import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient

from iepa.backend.auth.oauth import create_access_token, decode_access_token
from iepa.backend.db.mongo import create_user, get_user, save_learner_state, get_learner_state, increment_analyses, MONGO_URI
from iepa.backend.api.main import app

def run_week2_final_tests():
    print("===========================================================")
    print("         IEPA WEEK 2 FINAL COMPREHENSIVE TEST SUITE        ")
    print("===========================================================")

    # ---------------------------------------------------------
    # TEST 1: MongoDB Atlas Ping & CRUD Verification
    # ---------------------------------------------------------
    print("\n[TEST 1] MongoDB Atlas Ping & CRUD Verification...")
    async def test_mongo_live():
        if MONGO_URI:
            client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            ping_res = await client.admin.command('ping')
            assert ping_res.get('ok') == 1, "MongoDB Atlas ping failed"
            print("  1.1 MongoDB Atlas ping: {'ok': 1} [PASSED]")
        else:
            print("  1.1 MongoDB URI not set, using local fallback [PASSED]")

        test_google_id = "test_google_student_99"
        test_email = "student99@sjbit.edu.in"
        test_name = "Alex Student"

        # Create/Upsert User
        user = await create_user(test_google_id, test_email, test_name)
        assert user is not None
        assert user.get("email") == test_email
        print(f"  1.2 User Saved ({user.get('email')}): [PASSED]")

        # Fetch User
        fetched = await get_user(test_google_id)
        assert fetched is not None
        assert fetched.get("name") == test_name
        print("  1.3 User Retrieved from DB: [PASSED]")

        # Learner State Persistence
        mastery = {"off_by_one": 0.45, "syntax_error": 0.8}
        history = [{"concept": "off_by_one", "tier": "hint", "timestamp": datetime.now(timezone.utc).isoformat()}]
        await save_learner_state(test_google_id, mastery, history)
        state = await get_learner_state(test_google_id)
        assert "off_by_one" in state.get("mastery", {})
        print("  1.4 Learner State & History Persistence: [PASSED]")

        # Atomic Counter Increment
        new_analyses_count = await increment_analyses(test_google_id)
        assert new_analyses_count >= 1
        print(f"  1.5 Analysis Quota Increment (Count: {new_analyses_count}): [PASSED]")

    asyncio.run(test_mongo_live())

    # ---------------------------------------------------------
    # TEST 2: JWT Creation & Decoding
    # ---------------------------------------------------------
    print("\n[TEST 2] JWT Creation, Signing & Verification...")
    test_payload = {
        "sub": "google_test_12345",
        "email": "learner@university.edu",
        "name": "Alex Learner",
        "tier": "free",
        "analyses_this_month": 5
    }
    jwt_token = create_access_token(test_payload)
    assert jwt_token and len(jwt_token) > 20
    print("  2.1 JWT Token Generated successfully: [PASSED]")

    decoded = decode_access_token(jwt_token)
    assert decoded is not None
    assert decoded.get("sub") == test_payload["sub"]
    assert decoded.get("email") == test_payload["email"]
    print(f"  2.2 JWT Token Decoded & Verified ({decoded.get('email')}): [PASSED]")

    invalid_token_res = decode_access_token("malformed.jwt.signature")
    assert invalid_token_res is None
    print("  2.3 Malformed Token Rejection: [PASSED]")

    # ---------------------------------------------------------
    # TEST 3: FastAPI Client & Authenticated /auth/me Endpoint
    # ---------------------------------------------------------
    print("\n[TEST 3] FastAPI /auth/me Endpoint Verification...")
    client = TestClient(app)

    # 3.1 Unauthenticated Request -> 401
    unauth_resp = client.get("/auth/me")
    assert unauth_resp.status_code == 401
    print("  3.1 Unauthenticated /auth/me blocked with 401: [PASSED]")

    # 3.2 Authenticated Request -> 200 OK
    auth_resp = client.get("/auth/me", headers={"Authorization": f"Bearer {jwt_token}"})
    assert auth_resp.status_code == 200
    user_data = auth_resp.json()["data"]
    assert user_data["email"] == "learner@university.edu"
    assert user_data["analyses_remaining"] == 15
    print(f"  3.2 Authenticated /auth/me returned profile & quota (Remaining: {user_data['analyses_remaining']}): [PASSED]")

    # ---------------------------------------------------------
    # TEST 4: End-to-End Authenticated Code Analysis (/analyze)
    # ---------------------------------------------------------
    print("\n[TEST 4] End-to-End Authenticated /analyze Sandbox Pipeline...")
    python_code = "scores = [90, 85, 95]\nprint(scores[10])"
    analyze_resp = client.post(
        "/analyze",
        json={"code": python_code, "language": "python"},
        headers={"Authorization": f"Bearer {jwt_token}"}
    )
    assert analyze_resp.status_code == 200
    res_data = analyze_resp.json()
    assert res_data["success"] is True
    analysis_payload = res_data["data"]
    assert "concept" in analysis_payload
    assert analysis_payload["concept"] in ["off_by_one", "array_out_of_bounds"]
    assert "execution" in analysis_payload
    assert "IndexError" in analysis_payload["execution"]["error_raw"]
    print(f"  4.1 Code Sandbox & ML Diagnostic ({analysis_payload['concept']}, Tier: {analysis_payload['tier']}): [PASSED]")

    # ---------------------------------------------------------
    # TEST 5: Freemium Gating (HTTP 429 at 21st Analysis)
    # ---------------------------------------------------------
    print("\n[TEST 5] Freemium Rate Limiting (20 Free Analyses/Month)...")
    capped_token = create_access_token({
        "sub": "user_exhausted_quota",
        "email": "exhausted@learner.com",
        "name": "Exhausted Learner",
        "tier": "free",
        "analyses_this_month": 20
    })
    capped_resp = client.post(
        "/analyze",
        json={"code": "x = 10 / 0", "language": "python"},
        headers={"Authorization": f"Bearer {capped_token}"}
    )
    assert capped_resp.status_code == 429
    assert capped_resp.json()["upgrade_url"] == "/pricing"
    print(f"  5.1 21st Analysis blocked with HTTP 429 & Upgrade URL: [PASSED]")

    print("\n===========================================================")
    print("    [+] ALL WEEK 2 FINAL PIPELINE TESTS PASSED 100%!       ")
    print("===========================================================")

if __name__ == "__main__":
    run_week2_final_tests()
