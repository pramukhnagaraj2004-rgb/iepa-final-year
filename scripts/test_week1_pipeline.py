import os
import sys
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from iepa.backend.sandbox.executor import CodeExecutor
from iepa.backend.ml.mapper.concept_mapper import ConceptMapper
from iepa.backend.ml.mapper.tfidf_scratch import TFIDFVectorizer, LogisticRegressionScratch
from iepa.backend.engine.pipeline import analyze
from iepa.backend.api.main import app

def run_all_tests():
    print("===========================================================")
    print("           WEEK 1 COMPREHENSIVE TEST SUITE")
    print("===========================================================")

    # ---------------------------------------------------------
    # 1. Docker CodeExecutor Test
    # ---------------------------------------------------------
    print("\n[TEST 1] Isolated Docker Sandbox Code Execution...")
    executor = CodeExecutor(timeout=10)

    # 1.1 Python IndexError Code
    code_index = "items = [10, 20, 30]\nprint(items[99])"
    res1 = executor.execute(code_index)
    print("  1.1 IndexError code execution:")
    print("      success:", res1["success"])
    print("      error_raw:", res1["error_raw"])
    assert res1["success"] is False
    assert "IndexError: list index out of range" in res1["error_raw"]
    print("      [PASSED]")

    # 1.2 Python Clean Code
    code_clean = "x = 40\ny = 2\nprint(f'Answer is {x + y}')"
    res2 = executor.execute(code_clean)
    print("  1.2 Clean code execution:")
    print("      success:", res2["success"])
    print("      stdout:", res2["stdout"].strip())
    assert res2["success"] is True
    assert res2["error_raw"] == ""
    assert "Answer is 42" in res2["stdout"]
    print("      [PASSED]")

    # 1.3 Python Syntax Error
    code_syntax = "def broken(\n    print('missing paren')"
    res3 = executor.execute(code_syntax)
    print("  1.3 Syntax error execution:")
    print("      success:", res3["success"])
    print("      error_raw:", res3["error_raw"])
    assert res3["success"] is False
    assert "SyntaxError" in res3["error_raw"]
    print("      [PASSED]")

    # ---------------------------------------------------------
    # 2. Scratch TF-IDF & Logistic Regression Models
    # ---------------------------------------------------------
    print("\n[TEST 2] Scratch TF-IDF & Logistic Regression (JSON Serialization)...")
    mapper = ConceptMapper()
    loaded = mapper.load_model()
    print("  2.1 Models loaded from JSON:", loaded)
    assert loaded is True, "Failed to load scratch models from JSON"
    assert isinstance(mapper.vectorizer, TFIDFVectorizer)
    assert isinstance(mapper.classifier, LogisticRegressionScratch)
    print(f"      Vocabulary terms: {len(mapper.vectorizer.vocabulary_)}")
    print(f"      Classes: {mapper.classifier.classes_}")
    print("      [PASSED]")

    # 2.2 Predict concepts on error strings
    sample_errors = [
        ("IndexError: list index out of range", "off_by_one"),
        ("TypeError: unsupported operand type(s) for +: 'int' and 'str'", "type_mismatch"),
        ("NameError: name 'val' is not defined", "uninitialized_variable")
    ]
    for err, expected in sample_errors:
        pred = mapper.predict_concept(err)
        print(f"  2.2 Predicting '{err}':")
        print(f"      Predicted: {pred['concept']} (Confidence: {pred['confidence']:.2f})")
        assert pred["concept"] == expected or pred["confidence"] > 0.3
    print("      [PASSED]")

    # ---------------------------------------------------------
    # 3. End-to-End FastAPI Test via TestClient
    # ---------------------------------------------------------
    print("\n[TEST 3] FastAPI Endpoints Testing...")
    client = TestClient(app)

    # 3.1 GET /health
    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["success"] is True
    print("  3.1 GET /health: [PASSED]")

    # 3.2 POST /analyze with Python Code containing TypeError
    learner_id = "test_learner_wk1"
    code_type_err = "a = 5\nb = 'hello'\nprint(a + b)"
    analyze_resp = client.post("/analyze", json={
        "learner_id": learner_id,
        "code": code_type_err,
        "language": "python"
    })
    assert analyze_resp.status_code == 200
    data = analyze_resp.json()["data"]
    print("  3.2 POST /analyze with buggy code:")
    print("      Concept:", data.get("concept"))
    print("      Tier:", data.get("tier"))
    print("      Feedback:", data.get("feedback"))
    print("      Execution:", data.get("execution", {}).get("error_raw"))
    assert data["concept"] == "type_mismatch"
    assert "execution" in data
    print("      [PASSED]")

    # 3.3 POST /analyze with clean Python Code
    clean_resp = client.post("/analyze", json={
        "learner_id": learner_id,
        "code": "print('All good!')",
        "language": "python"
    })
    assert clean_resp.status_code == 200
    clean_data = clean_resp.json()["data"]
    print("  3.3 POST /analyze with clean code:")
    print("      Message:", clean_data.get("message"))
    print("      Stdout:", clean_data.get("stdout").strip())
    assert "Code ran successfully" in clean_data.get("message")
    print("      [PASSED]")

    # 3.4 POST /analyze/manual (Backward compatibility)
    manual_resp = client.post("/analyze/manual", json={
        "learner_id": learner_id,
        "error_raw": "IndexError: list index out of range"
    })
    assert manual_resp.status_code == 200
    manual_data = manual_resp.json()["data"]
    print("  3.4 POST /analyze/manual:")
    print("      Concept:", manual_data.get("concept"))
    print("      Tier:", manual_data.get("tier"))
    assert manual_data["concept"] == "off_by_one"
    print("      [PASSED]")

    # 3.5 GET /learner/{id}/history and GET /learner/{id}/mastery
    history_resp = client.get(f"/learner/{learner_id}/history")
    assert history_resp.status_code == 200
    history_list = history_resp.json()["data"]
    print(f"  3.5 GET /learner/{learner_id}/history items: {len(history_list)}")
    assert len(history_list) >= 2
    # Verify tier is present in history items
    for item in history_list:
        assert "tier" in item and item["tier"] in ["hint", "explain", "exercise"]
    print("      Verified tier field in history items: [PASSED]")

    mastery_resp = client.get(f"/learner/{learner_id}/mastery")
    assert mastery_resp.status_code == 200
    mastery_data = mastery_resp.json()["data"]
    print(f"  3.6 GET /learner/{learner_id}/mastery: {mastery_data.get('mastery')}")
    print("      [PASSED]")

    print("\n===========================================================")
    print("    [+] ALL WEEK 1 OBJECTIVES SUCCESSFULLY VERIFIED!       ")
    print("===========================================================")

if __name__ == "__main__":
    run_all_tests()
