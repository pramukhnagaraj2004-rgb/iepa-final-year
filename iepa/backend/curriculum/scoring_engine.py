"""
Scoring Engine — tracks per-user concept progress, generates the right
exercise set for normal attempts vs retests, and grades submissions.

Storage: MongoDB Atlas (collection: concept_progress) via db/mongo.py,
with the same local-JSON-fallback pattern used everywhere else in IEPA.

Mastery updates reuse the existing DecisionEngine, loading/saving the
same iepa/data/learners/{user_id}.json file that pipeline.py already
reads and writes: passing a concept boosts mastery, failing decrements it.
"""

from pathlib import Path
from datetime import datetime, timezone

from iepa.backend.curriculum.exercise_bank import EXERCISE_BANK
from iepa.backend.sandbox.executor import CodeExecutor
from iepa.backend.engine.decision_engine import DecisionEngine
from iepa.backend.db.mongo import get_concept_progress, save_concept_progress

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
LEARNERS_DIR = PROJECT_ROOT / "iepa" / "data" / "learners"
LEARNERS_DIR.mkdir(parents=True, exist_ok=True)

CONCEPT_ORDER = [
    "indentation_logic",
    "uninitialized_variable",
    "type_mismatch",
    "logical_operator_confusion",
    "infinite_loop",
    "off_by_one",
    "array_out_of_bounds",
    "missing_return",
    "wrong_return_type",
    "redundant_condition",
]


class ScoringEngine:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self._executor = CodeExecutor()

    # ------------------------------------------------------------------
    # Progress loading/saving (async — Mongo + local JSON fallback)
    # ------------------------------------------------------------------
    def _default_progress(self) -> dict:
        concept_progress = {}
        for i, concept in enumerate(CONCEPT_ORDER):
            concept_progress[concept] = {
                "status": "unlocked" if i == 0 else "locked",
                "attempts": 0,
                "last_score": 0,
                "questions_used": [],
                "passed_at": None,
            }
        return {"user_id": self.user_id, "concept_progress": concept_progress}

    async def _load_progress(self) -> dict:
        doc = await get_concept_progress(self.user_id)
        if doc:
            return doc
        fresh = self._default_progress()
        await save_concept_progress(self.user_id, fresh)
        return fresh

    async def _save_progress(self, progress: dict) -> None:
        await save_concept_progress(self.user_id, progress)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def get_progress(self) -> dict:
        progress = await self._load_progress()
        return progress["concept_progress"]

    async def get_exercise_set(self, concept: str) -> dict:
        if concept not in EXERCISE_BANK:
            raise ValueError(f"Unknown concept: {concept}")

        progress = await self._load_progress()
        state = progress["concept_progress"][concept]
        if state["status"] == "locked":
            raise PermissionError(f"Concept '{concept}' is locked")

        bank = EXERCISE_BANK[concept]

        if state["attempts"] == 0:
            theory = bank["theory"][0]
            coding = [bank["coding"][0], bank["coding"][1]]
        else:
            theory = bank["theory"][1]
            wrong_ids = state.get("questions_used", [])
            all_coding = {q["id"]: q for q in bank["coding"]}
            wrong_coding = [all_coding[qid] for qid in wrong_ids if qid in all_coding and "_c" in qid]

            remaining_pool = [q for q in bank["coding"] if q["id"] not in wrong_ids]
            coding = (wrong_coding + remaining_pool)[:2]
            if len(coding) < 2:
                coding = [bank["coding"][0], bank["coding"][2]]

        return {"theory": theory, "coding": coding}

    async def submit_answers(self, concept: str, theory_answer: str,
                              coding_results: list) -> dict:
        if concept not in EXERCISE_BANK:
            raise ValueError(f"Unknown concept: {concept}")

        bank = EXERCISE_BANK[concept]
        progress = await self._load_progress()
        state = progress["concept_progress"][concept]

        exercise_set = await self.get_exercise_set(concept)
        theory_q = exercise_set["theory"]
        coding_qs = exercise_set["coding"]

        theory_correct = (theory_answer == theory_q["correct"])
        score = int(theory_correct) + sum(1 for r in coding_results if r)

        state["questions_used"] = [theory_q["id"]] + [q["id"] for q in coding_qs]

        wrong_answers = []
        if not theory_correct:
            wrong_answers.append({
                "question_id": theory_q["id"],
                "question": theory_q["question"],
                "your_answer": theory_answer,
                "correct_answer": theory_q["correct"],
                "explanation": theory_q["explanation"],
            })
        for q, was_correct in zip(coding_qs, coding_results):
            if not was_correct:
                wrong_answers.append({
                    "question_id": q["id"],
                    "question": q["description"],
                    "your_answer": "(submitted code did not pass)",
                    "correct_answer": "(see explanation)",
                    "explanation": q["explanation"],
                })

        if score >= 2:
            state["status"] = "passed"
            state["last_score"] = score
            state["passed_at"] = datetime.now(timezone.utc).isoformat()

            current_index = CONCEPT_ORDER.index(concept)
            next_concept = None
            if current_index + 1 < len(CONCEPT_ORDER):
                next_concept = CONCEPT_ORDER[current_index + 1]
                next_state = progress["concept_progress"][next_concept]
                if next_state["status"] == "locked":
                    next_state["status"] = "unlocked"

            await self._save_progress(progress)
            self._boost_mastery(concept, 0.3)

            return {
                "passed": True,
                "score": score,
                "next_concept": next_concept,
                "show_resources": True,
                "resources": bank["resources"],
                "wrong_answers": wrong_answers,
            }
        else:
            state["status"] = "attempted"
            state["attempts"] += 1
            state["last_score"] = score
            await self._save_progress(progress)
            self._decrement_mastery(concept, 0.15)

            return {
                "passed": False,
                "score": score,
                "show_resources": False,
                "wrong_answers": wrong_answers,
                "retest_available": True,
            }

    def check_coding_answer(self, concept: str, question_id: str,
                             submitted_code: str) -> dict:
        run_result = self._executor.execute(submitted_code, language="python")
        error_raw = run_result.get("error_raw", "")
        correct = not bool(error_raw)

        return {
            "correct": correct,
            "stdout": run_result.get("stdout", ""),
            "error_raw": error_raw,
            "passed": correct,
        }

    # ------------------------------------------------------------------
    # Internal — reuses the real DecisionEngine + its own state file,
    # same one pipeline.py's analyze() reads/writes.
    # ------------------------------------------------------------------
    def _decrement_mastery(self, concept: str, amount: float):
        state_path = LEARNERS_DIR / f"{self.user_id}.json"
        engine = DecisionEngine(self.user_id)
        engine.load(str(state_path))

        current = engine.mastery.get(concept, 0.5)
        engine.mastery[concept] = max(0.0, min(1.0, current - amount))

        engine.save(str(state_path))

    def _boost_mastery(self, concept: str, amount: float):
        state_path = LEARNERS_DIR / f"{self.user_id}.json"
        engine = DecisionEngine(self.user_id)
        engine.load(str(state_path))

        current = engine.mastery.get(concept, 0.4)
        engine.mastery[concept] = max(0.0, min(1.0, current + amount))

        engine.save(str(state_path))

    def apply_explanation_penalty(self, concept: str):
        """
        Called when a learner reveals the full explanation on a HINT-tier
        result instead of working it out. Costs 0.10 mastery — smaller than
        a failed exercise (0.15) since it's a self-reported 'I gave up',
        not a wrong-answer submission.
        """
        self._decrement_mastery(concept, 0.10)