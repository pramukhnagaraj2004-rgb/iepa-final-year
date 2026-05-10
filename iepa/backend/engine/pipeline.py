import os
import sys
from pathlib import Path

# Add project root to path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from iepa.backend.engine.decision_engine import DecisionEngine
from iepa.backend.engine.feedback_generator import FeedbackGenerator
from iepa.backend.ml.mapper.concept_mapper import ConceptMapper

# Singleton instances for pipeline
_MAPPER = ConceptMapper()
_FEEDBACK_GEN = FeedbackGenerator()

# Load models exactly once
if not _MAPPER.load_model():
    print("[!] Warning: ConceptMapper models not found. Did you run concept_mapper.py?")

def analyze(learner_id: str, error_string: str) -> dict:
    """
    End-to-end analysis pipeline.
    """
    project_root = Path(os.path.abspath(os.path.dirname(__file__))).parent.parent.parent
    learners_dir = project_root / "iepa" / "data" / "learners"
    learners_dir.mkdir(parents=True, exist_ok=True)
    
    state_path = learners_dir / f"{learner_id}.json"
    
    # 1. Load or create DecisionEngine
    engine = DecisionEngine(learner_id)
    engine.load(str(state_path))
    
    # 2. Call predict_concept
    pred = _MAPPER.predict_concept(error_string)
    concept = pred["concept"]
    confidence = pred["confidence"]
    
    # 3. Call record_error
    engine.record_error(concept, confidence)
    
    # 4. Call get_feedback_tier
    tier = engine.get_feedback_tier(concept)
    
    # 5. Call feedback_generator.generate
    feedback_payload = _FEEDBACK_GEN.generate(concept, tier, error_string)
    
    # 6. Save engine state
    engine.save(str(state_path))
    
    # 7. Return full response
    return {
        "learner_id": learner_id,
        "error_raw": error_string,
        "concept": concept,
        "confidence": round(confidence, 2),
        "tier": tier,
        "feedback": feedback_payload["feedback"],
        "follow_up_exercise": feedback_payload["follow_up_exercise"],
        "mastery_report": engine.get_mastery_report()
    }

if __name__ == "__main__":
    print("--- Testing Phase 4 Pipeline ---")
    
    test_learner = "test_student_001"
    
    # Clear state for testing
    test_path = Path(__file__).parent.parent.parent / "data" / "learners" / f"{test_learner}.json"
    if test_path.exists():
        test_path.unlink()
        
    errors_sequence = [
        # Same concept repeated 3 times (off_by_one)
        "IndexError: list index out of range",
        "IndexError: list index out of bounds",
        "IndexError: string index out of range",
        # Two different concepts
        "TypeError: 'NoneType' object is not subscriptable",
        "IndentationError: unexpected indent"
    ]
    
    for i, err in enumerate(errors_sequence, 1):
        print(f"\n--- Error {i} ---")
        print(f"Raw: {err}")
        res = analyze(test_learner, err)
        
        print(f"Concept: {res['concept']} (Confidence: {res['confidence']})")
        print(f"Tier:    {res['tier'].upper()}")
        print(f"Feedback: {res['feedback']}")
        if res['follow_up_exercise']:
            print(f"Exercise: {res['follow_up_exercise']}")
            
    print("\n--- Final Mastery Report ---")
    final_engine = DecisionEngine(test_learner)
    final_engine.load(str(test_path))
    print(final_engine.get_mastery_report())
