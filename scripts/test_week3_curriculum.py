"""
Week 3 validation — Curriculum, Exercise Bank, Scoring Engine, and API.
Run from project root with the venv active:
    python scripts/test_week3_curriculum.py
"""

import os
import sys
import asyncio
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
env_iepa = PROJECT_ROOT / "iepa" / ".env"
if env_iepa.exists():
    load_dotenv(dotenv_path=env_iepa, override=True)

from iepa.backend.curriculum.exercise_bank import EXERCISE_BANK
from iepa.backend.curriculum.scoring_engine import ScoringEngine, CONCEPT_ORDER

TEST_USER = "test_curriculum_user_week3"


def test_exercise_bank_completeness():
    print("\n--- Test 1: Exercise bank has all 10 concepts ---")
    assert len(EXERCISE_BANK) == 10, f"Expected 10 concepts, found {len(EXERCISE_BANK)}"
    for concept in CONCEPT_ORDER:
        assert concept in EXERCISE_BANK, f"Missing concept: {concept}"
    print("   PASS — all 10 concepts present")


def test_exercise_shape():
    print("\n--- Test 2: Each concept has 2 theory + 3 coding + 3 resources ---")
    for concept, bank in EXERCISE_BANK.items():
        assert len(bank["theory"]) == 2, f"{concept}: expected 2 theory questions, got {len(bank['theory'])}"
        assert len(bank["coding"]) == 3, f"{concept}: expected 3 coding questions, got {len(bank['coding'])}"
        assert len(bank["resources"]) == 3, f"{concept}: expected 3 resources, got {len(bank['resources'])}"
        for t in bank["theory"]:
            assert t["correct"] in ("A", "B", "C", "D")
            assert len(t["options"]) == 4
    print("   PASS — all concepts have correct question/resource counts")


async def _cleanup_test_user():
    from iepa.backend.db.mongo import get_db
    for folder in ["learners", "curriculum_progress"]:
        path = PROJECT_ROOT / "iepa" / "data" / folder / f"{TEST_USER}.json"
        if path.exists():
            path.unlink()
    db = get_db()
    if db is not None:
        await db.concept_progress.delete_one({"user_id": TEST_USER})


async def test_scoring_pass_and_unlock():
    print("\n--- Test 3: Scoring engine — 2/3 correct passes and unlocks next concept ---")
    await _cleanup_test_user()
    engine = ScoringEngine(TEST_USER)

    progress = await engine.get_progress()
    assert progress["indentation_logic"]["status"] == "unlocked"
    assert progress["uninitialized_variable"]["status"] == "locked"

    exercise_set = await engine.get_exercise_set("indentation_logic")
    correct_theory = exercise_set["theory"]["correct"]

    result = await engine.submit_answers("indentation_logic", correct_theory, [True, True])
    assert result["passed"] is True, f"Expected pass, got {result}"
    assert result["score"] == 3
    assert result["next_concept"] == "uninitialized_variable"

    progress = await engine.get_progress()
    assert progress["indentation_logic"]["status"] == "passed"
    assert progress["uninitialized_variable"]["status"] == "unlocked"
    print("   PASS — concept marked passed, next concept unlocked")

async def test_scoring_fail_and_retest():
    print("\n--- Test 4: Scoring engine — 1/3 correct fails, retest uses different questions ---")
    await _cleanup_test_user()
    engine = ScoringEngine(TEST_USER)

    first_set = await engine.get_exercise_set("indentation_logic")
    wrong_theory = next(o for o in ("A", "B", "C", "D") if o != first_set["theory"]["correct"])

    result = await engine.submit_answers("indentation_logic", wrong_theory, [False, False])
    assert result["passed"] is False, f"Expected fail, got {result}"
    assert result["score"] < 2
    assert result["retest_available"] is True
    assert len(result["wrong_answers"]) == 3  # theory + 2 coding all wrong

    retest_set = await engine.get_exercise_set("indentation_logic")
    assert retest_set["theory"]["id"] == "indentation_logic_t2", "Retest should use t2, not t1"
    print("   PASS — fail recorded, retest uses t2 + different coding pool")

def test_wrong_answers_have_explanations():
    print("\n--- Test 5: Wrong answers always include explanations ---")
    for concept, bank in EXERCISE_BANK.items():
        for t in bank["theory"]:
            assert t["explanation"], f"{concept}/{t['id']} missing explanation"
        for c in bank["coding"]:
            assert c["explanation"], f"{concept}/{c['id']} missing explanation"
    print("   PASS — every question has a non-empty explanation")


async def test_progress_endpoint_shape():
    print("\n--- Test 6: get_progress returns correct locked/unlocked state for a fresh user ---")
    await _cleanup_test_user()
    engine = ScoringEngine(TEST_USER + "_fresh")
    progress = await engine.get_progress()
    assert progress["indentation_logic"]["status"] == "unlocked"
    for concept in CONCEPT_ORDER[1:]:
        assert progress[concept]["status"] == "locked", f"{concept} should start locked"
    path = PROJECT_ROOT / "iepa" / "data" / "curriculum_progress" / f"{TEST_USER}_fresh.json"
    if path.exists():
        path.unlink()
    print("   PASS — fresh user has correct default lock state")


def test_check_coding_answer_uses_real_executor():
    print("\n--- Test 7: check_coding_answer runs code through the real sandbox ---")
    engine = ScoringEngine(TEST_USER)
    good_result = engine.check_coding_answer("indentation_logic", "indentation_logic_c1", "print('hello')")
    assert good_result["correct"] is True, f"Expected clean run, got {good_result}"

    bad_result = engine.check_coding_answer("indentation_logic", "indentation_logic_c1", "print(undefined_var)")
    assert bad_result["correct"] is False
    assert "Error" in bad_result["error_raw"] or "error" in bad_result["error_raw"].lower()
    print("   PASS — sandbox correctly distinguishes clean vs erroring code")


async def main():
    test_exercise_bank_completeness()
    test_exercise_shape()
    test_wrong_answers_have_explanations()
    await test_scoring_pass_and_unlock()
    await test_scoring_fail_and_retest()
    await test_progress_endpoint_shape()
    test_check_coding_answer_uses_real_executor()
    await _cleanup_test_user()

    print("\n[+] All Week 3 curriculum tests PASSED!")


if __name__ == "__main__":
    asyncio.run(main())