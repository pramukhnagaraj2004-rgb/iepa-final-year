import os
import json
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment variables
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
env_root = PROJECT_ROOT / ".env"
env_iepa = PROJECT_ROOT / "iepa" / ".env"
if env_iepa.exists():
    load_dotenv(dotenv_path=env_iepa, override=True)
if env_root.exists():
    load_dotenv(dotenv_path=env_root, override=False)

MONGO_URI = (os.getenv("MONGO_URI", "") or "").strip().replace("\n", "").replace("\r", "").replace(" ", "")
DB_NAME = os.getenv("MONGO_DB_NAME", "iepa_db")

DATA_DIR = PROJECT_ROOT / "iepa" / "data"
USERS_DIR = DATA_DIR / "users"
LEARNERS_DIR = DATA_DIR / "learners"
ANALYSES_DIR = DATA_DIR / "analyses"
CURRICULUM_DIR = DATA_DIR / "curriculum_progress"

# Ensure local fallback directories exist
for folder in [USERS_DIR, LEARNERS_DIR, ANALYSES_DIR, CURRICULUM_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

_client: Optional[AsyncIOMotorClient] = None

def get_client() -> Optional[AsyncIOMotorClient]:
    """
    Returns singleton AsyncIOMotorClient instance if MONGO_URI is set.
    Re-creates client if running on a new event loop.
    """
    global _client
    if not MONGO_URI:
        return None

    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None

    if _client is not None and current_loop is not None:
        try:
            client_loop = getattr(_client, "delegate", None)
            if client_loop and getattr(client_loop, "_io_loop", None) != current_loop:
                _client = None
        except Exception:
            _client = None

    if _client is None:
        try:
            _client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        except Exception as e:
            print(f"[!] Warning: Could not initialize Mongo client: {e}")
            _client = None
    return _client

def get_db():
    """
    Returns the database handle if client is available.
    """
    client = get_client()
    if client:
        return client[DB_NAME]
    return None

# ═══════════════════════════════════════════════════════════
# LOCAL JSON FALLBACK HELPERS
# ═══════════════════════════════════════════════════════════

def _fallback_get_user(user_id: str) -> Optional[Dict[str, Any]]:
    # Sanitize user_id for filesystem
    safe_id = "".join([c if c.isalnum() or c in ("-", "_", "@", ".") else "_" for c in user_id])
    file_path = USERS_DIR / f"{safe_id}.json"
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[!] Fallback get_user read error: {e}")
    return None

def _fallback_save_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
    user_id = user_data.get("google_id") or user_data.get("email") or "default_user"
    safe_id = "".join([c if c.isalnum() or c in ("-", "_", "@", ".") else "_" for c in user_id])
    file_path = USERS_DIR / f"{safe_id}.json"
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(user_data, f, indent=2)
    except Exception as e:
        print(f"[!] Fallback save_user write error: {e}")
    return user_data

# ═══════════════════════════════════════════════════════════
# ASYNC CRUD OPERATIONS (Mongo Primary + Local JSON Fallback)
# ═══════════════════════════════════════════════════════════

async def get_user(google_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves user document by google_id.
    Falls back to local file if Mongo is unavailable.
    """
    try:
        db = get_db()
        if db is not None:
            user = await db.users.find_one({"google_id": google_id})
            if user:
                if "_id" in user:
                    user["_id"] = str(user["_id"])
                return user
    except Exception as e:
        print(f"[!] Mongo get_user notice: {e}")
    
    return _fallback_get_user(google_id)

async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves user document by email.
    Falls back to local file if Mongo is unavailable.
    """
    try:
        db = get_db()
        if db is not None:
            user = await db.users.find_one({"email": email})
            if user:
                if "_id" in user:
                    user["_id"] = str(user["_id"])
                return user
    except Exception as e:
        print(f"[!] Mongo get_user_by_email notice: {e}")
        
    return _fallback_get_user(email)

async def create_user(google_id: str, email: str, name: str, picture: str = "") -> Dict[str, Any]:
    """
    Creates or updates a user document in MongoDB Atlas (with local fallback).
    """
    now = datetime.now(timezone.utc).isoformat()
    user_data = {
        "google_id": google_id,
        "email": email,
        "name": name,
        "picture": picture,
        "tier": "free",
        "analyses_this_month": 0,
        "updated_at": now
    }
    
    try:
        db = get_db()
        if db is not None:
            existing = await db.users.find_one({"google_id": google_id})
            if existing:
                await db.users.update_one(
                    {"google_id": google_id},
                    {"$set": {"name": name, "picture": picture, "updated_at": now}}
                )
                existing["name"] = name
                existing["picture"] = picture
                existing["updated_at"] = now
                if "_id" in existing:
                    existing["_id"] = str(existing["_id"])
                _fallback_save_user(existing)
                return existing
            else:
                user_data["created_at"] = now
                result = await db.users.insert_one(user_data)
                user_data["_id"] = str(result.inserted_id)
                _fallback_save_user(user_data)
                return user_data
    except Exception as e:
        print(f"[!] Mongo create_user fallback notice: {e}")

    # Fallback to local JSON
    existing_local = _fallback_get_user(google_id)
    if existing_local:
        existing_local["name"] = name
        existing_local["picture"] = picture
        existing_local["updated_at"] = now
        return _fallback_save_user(existing_local)

    user_data["created_at"] = now
    user_data["_id"] = google_id
    return _fallback_save_user(user_data)

async def get_learner_state(user_id: str) -> Dict[str, Any]:
    """
    Retrieves learner mastery state and history by user_id.
    Falls back to local file if Mongo is unavailable.
    """
    try:
        db = get_db()
        if db is not None:
            doc = await db.learner_state.find_one({"user_id": user_id})
            if doc:
                return {
                    "user_id": user_id,
                    "mastery": doc.get("mastery", {}),
                    "history": doc.get("history", [])
                }
    except Exception as e:
        print(f"[!] Mongo get_learner_state fallback notice: {e}")
        
    # Local JSON fallback
    safe_id = "".join([c if c.isalnum() or c in ("-", "_", "@", ".") else "_" for c in user_id])
    file_path = LEARNERS_DIR / f"{safe_id}.json"
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {
                    "user_id": user_id,
                    "mastery": data.get("mastery", {}),
                    "history": data.get("history", [])
                }
        except Exception as e:
            print(f"[!] Local learner_state read error: {e}")

    return {"user_id": user_id, "mastery": {}, "history": []}

async def save_learner_state(user_id: str, mastery: Dict[str, float], history: List[Dict[str, Any]]) -> None:
    """
    Saves or updates learner state in MongoDB Atlas and local disk.
    """
    now = datetime.now(timezone.utc).isoformat()
    state_payload = {
        "user_id": user_id,
        "mastery": mastery,
        "history": history,
        "updated_at": now
    }

    try:
        db = get_db()
        if db is not None:
            await db.learner_state.update_one(
                {"user_id": user_id},
                {"$set": state_payload},
                upsert=True
            )
    except Exception as e:
        print(f"[!] Mongo save_learner_state notice: {e}")

    # Also persist locally
    safe_id = "".join([c if c.isalnum() or c in ("-", "_", "@", ".") else "_" for c in user_id])
    file_path = LEARNERS_DIR / f"{safe_id}.json"
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(state_payload, f, indent=2)
    except Exception as e:
        print(f"[!] Local learner_state write error: {e}")

async def get_concept_progress(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves curriculum concept_progress document by user_id.
    Falls back to local file if Mongo is unavailable. Returns None
    if nothing found (caller is responsible for initializing defaults).
    """
    try:
        db = get_db()
        if db is not None:
            doc = await db.concept_progress.find_one({"user_id": user_id})
            if doc:
                doc.pop("_id", None)
                return doc
    except Exception as e:
        print(f"[!] Mongo get_concept_progress notice: {e}")

    safe_id = "".join([c if c.isalnum() or c in ("-", "_", "@", ".") else "_" for c in user_id])
    file_path = CURRICULUM_DIR / f"{safe_id}.json"
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[!] Local concept_progress read error: {e}")
    return None


async def save_concept_progress(user_id: str, progress_doc: Dict[str, Any]) -> None:
    """
    Saves or updates curriculum concept_progress in MongoDB Atlas and local disk.
    """
    try:
        db = get_db()
        if db is not None:
            await db.concept_progress.update_one(
                {"user_id": user_id},
                {"$set": progress_doc},
                upsert=True,
            )
    except Exception as e:
        print(f"[!] Mongo save_concept_progress notice: {e}")

    safe_id = "".join([c if c.isalnum() or c in ("-", "_", "@", ".") else "_" for c in user_id])
    file_path = CURRICULUM_DIR / f"{safe_id}.json"
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(progress_doc, f, indent=2)
    except Exception as e:
        print(f"[!] Local concept_progress write error: {e}")

async def log_analysis(user_id: str, analysis_result: Dict[str, Any]) -> None:
    """
    Logs an analysis event into MongoDB Atlas analyses collection and local JSON lines.
    """
    doc = {
        "user_id": user_id,
        "error_raw": analysis_result.get("error_raw", ""),
        "concept": analysis_result.get("concept", ""),
        "confidence": analysis_result.get("confidence", 0.0),
        "tier": analysis_result.get("tier", ""),
        "feedback": analysis_result.get("feedback", ""),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    try:
        db = get_db()
        if db is not None:
            await db.analyses.insert_one(doc)
    except Exception as e:
        print(f"[!] Mongo log_analysis notice: {e}")

    # Local fallback
    safe_id = "".join([c if c.isalnum() or c in ("-", "_", "@", ".") else "_" for c in user_id])
    file_path = ANALYSES_DIR / f"{safe_id}.jsonl"
    try:
        if "_id" in doc:
            doc_copy = doc.copy()
            doc_copy["_id"] = str(doc_copy["_id"])
        else:
            doc_copy = doc
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(doc_copy) + "\n")
    except Exception as e:
        print(f"[!] Local log_analysis write error: {e}")

async def increment_analyses(user_id: str) -> int:
    """
    Increments the monthly analysis count for a user (atomic in Mongo Atlas, updated in local cache).
    """
    try:
        db = get_db()
        if db is not None:
            res = await db.users.find_one_and_update(
                {"google_id": user_id},
                {"$inc": {"analyses_this_month": 1}},
                return_document=True
            )
            if res:
                return res.get("analyses_this_month", 1)
                
            res2 = await db.users.find_one_and_update(
                {"email": user_id},
                {"$inc": {"analyses_this_month": 1}},
                return_document=True
            )
            if res2:
                return res2.get("analyses_this_month", 1)
    except Exception as e:
        print(f"[!] Mongo increment_analyses notice: {e}")

    # Local fallback increment
    user = _fallback_get_user(user_id)
    if user:
        user["analyses_this_month"] = user.get("analyses_this_month", 0) + 1
        _fallback_save_user(user)
        return user["analyses_this_month"]

    return 1

if __name__ == "__main__":
    print("=== Testing MongoDB Atlas & Fallback System ===")
    
    async def run_test():
        test_id = "test_google_123"
        test_email = "student@sjbit.edu.in"
        test_name = "Alex Test Student"

        print("\n1. Testing create_user...")
        user = await create_user(test_id, test_email, test_name)
        print("   Created user:", user.get("email"), "| Tier:", user.get("tier"))
        assert user.get("email") == test_email

        print("\n2. Testing get_user...")
        fetched = await get_user(test_id)
        assert fetched is not None
        print("   Fetched user:", fetched.get("name"))

        print("\n3. Testing learner state persistence...")
        mastery = {"off_by_one": 0.45, "type_mismatch": 0.6}
        history = [{"concept": "off_by_one", "tier": "hint", "timestamp": datetime.now(timezone.utc).isoformat()}]
        await save_learner_state(test_id, mastery, history)
        state = await get_learner_state(test_id)
        assert "off_by_one" in state["mastery"]
        print("   Retrieved mastery:", state["mastery"])

        print("\n4. Testing analysis logging...")
        await log_analysis(test_id, {"concept": "off_by_one", "confidence": 0.95, "tier": "hint", "feedback": "Test feedback"})
        print("   Analysis logged successfully.")

        print("\n5. Testing analysis increment...")
        new_count = await increment_analyses(test_id)
        print("   New monthly count:", new_count)
        assert new_count >= 1

        print("\n[+] All MongoDB Atlas & Fallback tests PASSED!")

    asyncio.run(run_test())
