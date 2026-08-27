import os
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

env_root = PROJECT_ROOT / ".env"
env_iepa = PROJECT_ROOT / "iepa" / ".env"
if env_iepa.exists():
    load_dotenv(dotenv_path=env_iepa, override=True)
if env_root.exists():
    load_dotenv(dotenv_path=env_root, override=False)

from fastapi import FastAPI, Request, Depends, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
import httpx

try:
    from iepa.backend.api.models import (
        AnalyzeRequest,
        AnalyzeManualRequest,
        ClusterRequest,
        APIResponse,
        SubmitAnswerRequest,
        CheckCodeRequest
    )
    from iepa.backend.engine.pipeline import analyze
    from iepa.backend.engine.feedback_generator import FeedbackGenerator
    from iepa.backend.ml.clustering.error_clusterer import ErrorClusterer
    from iepa.backend.sandbox.executor import CodeExecutor
    from iepa.backend.auth.oauth import (
        oauth,
        create_access_token,
        get_current_user,
        get_optional_current_user,
        JWT_SECRET,
        FRONTEND_URL
    )
    from iepa.backend.db.mongo import (
        get_user,
        create_user,
        get_learner_state,
        save_learner_state,
        log_analysis,
        increment_analyses
    )
    from iepa.backend.curriculum.scoring_engine import ScoringEngine, CONCEPT_ORDER
    from iepa.backend.curriculum.exercise_bank import EXERCISE_BANK
    print("[main.py] All backend submodules imported successfully.")
except Exception as err:
    import traceback
    print(f"[main.py] ERROR during submodules import: {err}")
    traceback.print_exc()
    raise err

# Initialize singletons for clusterer and sandbox code executor
clusterer = ErrorClusterer()
executor = CodeExecutor()
_feedback_gen = FeedbackGenerator()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[*] Starting up IEPA API server...")
    print("[*] Initializing ErrorClusterer with KMeansScratch...")
    try:
        clusterer.load_data()
        clusterer.embed_corpus()
        clusterer.cluster()
        print("[+] ErrorClusterer initialized successfully.")
    except Exception as e:
        print(f"[!] Failed to initialize ErrorClusterer: {e}")
    
    yield
    print("[*] Shutting down IEPA API server...")

app = FastAPI(
    title="IEPA API — Intelligent Error Pattern Analyzer",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Session middleware required by Authlib for OAuth state handling
app.add_middleware(SessionMiddleware, secret_key=JWT_SECRET)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"Incoming: {request.method} {request.url.path}")
    response = await call_next(request)
    print(f"Completed: {request.method} {request.url.path} - Status: {response.status_code}")
    return response

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs", status_code=302)

@app.get("/health", response_model=APIResponse, tags=["System"])
async def health_check():
    return APIResponse(success=True, data={"status": "ok", "version": "2.0.0"})

# ═══════════════════════════════════════════════════════════
# AUTHENTICATION ENDPOINTS (Google OAuth + JWT)
# ═══════════════════════════════════════════════════════════

@app.get("/auth/google", tags=["Authentication"])
async def google_login(request: Request):
    """
    Redirects user to Google OAuth consent screen with HTTP 302.
    """
    forwarded_proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    redirect_uri = f"{forwarded_proto}://{request.url.netloc}/auth/google/callback"
    
    if hasattr(oauth, "google"):
        res = await oauth.google.authorize_redirect(request, redirect_uri)
        res.status_code = 302
        return res
    else:
        return RedirectResponse(url=f"{FRONTEND_URL}/auth/callback?token=mock_dev_token", status_code=302)

@app.get("/auth/google/callback", tags=["Authentication"])
async def google_callback(request: Request):
    """
    Handles Google OAuth callback, exchanges code for user profile,
    saves user in MongoDB, generates JWT, and redirects to frontend (HTTP 302).
    """
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")
        if not user_info:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://www.googleapis.com/oauth2/v3/userinfo",
                    headers={"Authorization": f"Bearer {token['access_token']}"}
                )
                user_info = resp.json()

        google_id = user_info.get("sub", "")
        email = user_info.get("email", "")
        name = user_info.get("name", "Student")
        picture = user_info.get("picture", "")

        # Upsert user record in MongoDB
        db_user = await create_user(google_id, email, name, picture)
        user_tier = db_user.get("tier", "free")

        # Create signed JWT
        jwt_token = create_access_token({
            "sub": google_id,
            "email": email,
            "name": name,
            "picture": picture,
            "tier": user_tier
        })

        return RedirectResponse(url=f"{FRONTEND_URL}/auth/callback?token={jwt_token}", status_code=302)

    except Exception as e:
        print(f"[!] Google OAuth callback error: {e}")
        return RedirectResponse(url=f"{FRONTEND_URL}/auth/callback?error={str(e)}", status_code=302)

@app.get("/auth/me", response_model=APIResponse, tags=["Authentication"])
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Returns current authenticated user profile and remaining monthly analysis quota.
    """
    tier = current_user.get("tier", "free")
    analyses_count = current_user.get("analyses_this_month", 0)
    remaining = max(0, 20 - analyses_count) if tier == "free" else 999999

    return APIResponse(
        success=True,
        data={
            "google_id": current_user.get("google_id", current_user.get("sub", "")),
            "email": current_user.get("email", ""),
            "name": current_user.get("name", "Student"),
            "picture": current_user.get("picture", ""),
            "tier": tier,
            "analyses_this_month": analyses_count,
            "analyses_remaining": remaining
        }
    )

# ═══════════════════════════════════════════════════════════
# ANALYSIS ENDPOINTS (With Freemium Quota Enforcement)
# ═══════════════════════════════════════════════════════════

@app.post("/analyze", response_model=APIResponse, tags=["Analysis"])
async def analyze_endpoint(
    req: AnalyzeRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    """
    Executes student code in isolated Docker/subprocess sandbox, extracts exceptions,
    and runs through ML pipeline with Freemium limit enforcement.
    """
    if not req.code or not req.code.strip():
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "code is required"}
        )

    user_id = req.learner_id
    if current_user:
        user_id = current_user.get("google_id") or current_user.get("email") or user_id or "user_default"
        tier = current_user.get("tier", "free")
        analyses_used = current_user.get("analyses_this_month", 0)

        # Freemium quota enforcement: 20 analyses per month for Free tier
        if tier == "free" and analyses_used >= 20:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": "Monthly limit reached (20/20 free analyses used). Please upgrade to Pro for unlimited access.",
                    "upgrade_url": "/pricing"
                }
            )
    else:
        user_id = user_id or "anonymous_student"

    try:
        # 1. Run in Sandbox
        exec_res = executor.execute(req.code, language=req.language or "python")

        # 2. If error detected, analyze concept gap
        if exec_res.get("error_raw"):
            result = analyze(user_id, exec_res["error_raw"])
            result["execution"] = exec_res

            # Log analysis and increment user counter in MongoDB
            if current_user:
                await increment_analyses(user_id)
                await log_analysis(user_id, result)
                if "mastery_report" in result:
                    state = await get_learner_state(user_id)
                    history = state.get("history", [])
                    history.append({
                        "concept": result["concept"],
                        "confidence": result["confidence"],
                        "tier": result["tier"],
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    await save_learner_state(user_id, result["mastery_report"], history)

            return APIResponse(success=True, data=result)

        # 3. Clean run with no errors
        return APIResponse(
            success=True,
            data={
                "message": "Code ran successfully, no errors detected",
                "stdout": exec_res.get("stdout", ""),
                "execution": exec_res
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/analyze/manual", response_model=APIResponse, tags=["Analysis"])
async def analyze_manual_endpoint(
    req: AnalyzeManualRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    """
    Accepts raw error strings directly. Backward compatible with optional authentication.
    """
    if not req.error_raw or not req.error_raw.strip():
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "error_raw is required"}
        )

    user_id = req.learner_id or "default"
    if current_user:
        user_id = current_user.get("google_id") or current_user.get("email") or user_id

    try:
        result = analyze(user_id, req.error_raw)
        return APIResponse(success=True, data=result)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# ═══════════════════════════════════════════════════════════
# LEARNER STATE & MASTERY
# ═══════════════════════════════════════════════════════════

@app.get("/learner/{learner_id}/mastery", response_model=APIResponse, tags=["Learner"])
async def get_mastery(learner_id: str):
    # Try Mongo first
    try:
        state = await get_learner_state(learner_id)
        if state and state.get("mastery"):
            return APIResponse(success=True, data={
                "learner_id": learner_id,
                "mastery": state["mastery"],
                "history_count": len(state.get("history", []))
            })
    except Exception as e:
        print(f"[!] Mongo fetch notice: {e}")

    # Fallback to local JSON files
    state_path = PROJECT_ROOT / "iepa" / "data" / "learners" / f"{learner_id}.json"
    if not state_path.exists():
        state_path = PROJECT_ROOT / "data" / "learners" / f"{learner_id}.json"
        
    if not state_path.exists():
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "Learner not found"}
        )
        
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        mastery = data.get("mastery", {})
        history_count = len(data.get("history", []))
        
        return APIResponse(success=True, data={
            "learner_id": learner_id,
            "mastery": mastery,
            "history_count": history_count
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/learner/{learner_id}/history", response_model=APIResponse, tags=["Learner"])
async def get_history(learner_id: str):
    # Try Mongo first
    try:
        state = await get_learner_state(learner_id)
        if state and state.get("history"):
            return APIResponse(success=True, data=state["history"])
    except Exception as e:
        print(f"[!] Mongo fetch notice: {e}")

    # Fallback to local JSON files
    state_path = PROJECT_ROOT / "iepa" / "data" / "learners" / f"{learner_id}.json"
    if not state_path.exists():
        state_path = PROJECT_ROOT / "data" / "learners" / f"{learner_id}.json"
        
    if not state_path.exists():
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "Learner not found"}
        )
        
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        history = data.get("history", [])
        return APIResponse(success=True, data=history)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/cluster", response_model=APIResponse, tags=["Clustering"])
async def cluster_endpoint(req: ClusterRequest):
    try:
        result = clusterer.get_cluster(req.error_raw)
        return APIResponse(success=True, data=result)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/concepts", response_model=APIResponse, tags=["Pedagogy"])
async def get_concepts():
    concepts = [
        {"label": "syntax_error", "description": "Basic syntax errors like missing colons or mismatched parentheses."},
        {"label": "name_error", "description": "Using a variable or function name that has not been defined."},
        {"label": "type_error", "description": "Performing an operation on inappropriate data types."},
        {"label": "index_error", "description": "Attempting to access an index that is out of bounds for a sequence."},
        {"label": "key_error", "description": "Accessing a dictionary with a key that does not exist."},
        {"label": "value_error", "description": "Passing an argument with the right type but inappropriate value."},
        {"label": "attribute_error", "description": "Attempting to access an attribute or method that does not exist on an object."},
        {"label": "indentation_error", "description": "Incorrect indentation levels in the code."},
        {"label": "import_error", "description": "Failing to import a module or a specific function from a module."},
        {"label": "logical_error", "description": "The code runs without crashing but produces incorrect results due to flawed logic."}
    ]
    return APIResponse(success=True, data=concepts)

# ═══════════════════════════════════════════════════════════
# CURRICULUM ENDPOINTS (Week 3)
# ═══════════════════════════════════════════════════════════

CONCEPT_DISPLAY_NAMES = {
    "indentation_logic": "Indentation & Block Structure",
    "uninitialized_variable": "Uninitialized Variables",
    "type_mismatch": "Type Mismatches",
    "logical_operator_confusion": "Logical Operator Confusion",
    "infinite_loop": "Infinite Loops",
    "off_by_one": "Off-by-One Errors",
    "array_out_of_bounds": "Array/List Out of Bounds",
    "missing_return": "Missing Return Statements",
    "wrong_return_type": "Wrong Return Type",
    "redundant_condition": "Redundant Conditions",
}

CONCEPT_DESCRIPTIONS = {
    "indentation_logic": "How Python uses indentation to define code blocks.",
    "uninitialized_variable": "Using a variable before it has ever been assigned.",
    "type_mismatch": "Mixing incompatible types like str and int.",
    "logical_operator_confusion": "Misusing and/or/not or = vs ==.",
    "infinite_loop": "Loops whose exit condition never becomes true.",
    "off_by_one": "Loop/index bounds that are one too many or too few.",
    "array_out_of_bounds": "Accessing a list index that doesn't exist.",
    "missing_return": "Functions that fall through without returning a value.",
    "wrong_return_type": "Functions that return inconsistent or unexpected types.",
    "redundant_condition": "Unnecessarily complex or duplicated conditionals.",
}


def _get_user_id(current_user: Dict[str, Any]) -> str:
    return current_user.get("google_id") or current_user.get("email") or "user_default"


@app.get("/curriculum/concepts", response_model=APIResponse, tags=["Curriculum"])
async def get_curriculum_concepts():
    """
    No auth required. Returns ordered list of all 10 concepts.
    """
    concepts = []
    for i, name in enumerate(CONCEPT_ORDER):
        concepts.append({
            "name": name,
            "display_name": CONCEPT_DISPLAY_NAMES.get(name, name),
            "level": i + 1,
            "description": CONCEPT_DESCRIPTIONS.get(name, ""),
            "prerequisites": [CONCEPT_ORDER[i - 1]] if i > 0 else [],
        })
    return APIResponse(success=True, data=concepts)


@app.get("/curriculum/progress", response_model=APIResponse, tags=["Curriculum"])
async def get_curriculum_progress(current_user: Dict[str, Any] = Depends(get_current_user)):
    user_id = _get_user_id(current_user)
    engine = ScoringEngine(user_id)
    progress = await engine.get_progress()

    completed_count = sum(1 for c in progress.values() if c["status"] == "passed")
    current_concept = next(
        (name for name in CONCEPT_ORDER if progress[name]["status"] in ("unlocked", "attempted")),
        None,
    )

    return APIResponse(success=True, data={
        "concepts": progress,
        "current_concept": current_concept,
        "completed_count": completed_count,
    })


@app.get("/curriculum/exercise/{concept}", response_model=APIResponse, tags=["Curriculum"])
async def get_curriculum_exercise(concept: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    if concept not in EXERCISE_BANK:
        return JSONResponse(status_code=404, content={"success": False, "error": f"Unknown concept: {concept}"})

    user_id = _get_user_id(current_user)
    engine = ScoringEngine(user_id)

    try:
        exercise_set = await engine.get_exercise_set(concept)
    except PermissionError as e:
        return JSONResponse(status_code=403, content={"success": False, "error": str(e)})

    theory_safe = {k: v for k, v in exercise_set["theory"].items() if k not in ("correct", "explanation")}
    coding_safe = [
        {k: v for k, v in q.items() if k not in ("solution_check", "explanation")}
        for q in exercise_set["coding"]
    ]

    return APIResponse(success=True, data={"theory": theory_safe, "coding": coding_safe})


@app.post("/curriculum/submit/{concept}", response_model=APIResponse, tags=["Curriculum"])
async def submit_curriculum_answers(
    concept: str,
    req: SubmitAnswerRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    if concept not in EXERCISE_BANK:
        return JSONResponse(status_code=404, content={"success": False, "error": f"Unknown concept: {concept}"})

    user_id = _get_user_id(current_user)
    engine = ScoringEngine(user_id)

    try:
        result = await engine.submit_answers(concept, req.theory_answer, req.coding_results)
    except PermissionError as e:
        return JSONResponse(status_code=403, content={"success": False, "error": str(e)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

    return APIResponse(success=True, data=result)


@app.post("/curriculum/check-code/{concept}/{question_id}", response_model=APIResponse, tags=["Curriculum"])
async def check_curriculum_code(
    concept: str,
    question_id: str,
    req: CheckCodeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    if concept not in EXERCISE_BANK:
        return JSONResponse(status_code=404, content={"success": False, "error": f"Unknown concept: {concept}"})

    user_id = _get_user_id(current_user)
    engine = ScoringEngine(user_id)

    try:
        result = engine.check_coding_answer(concept, question_id, req.code)
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

    return APIResponse(success=True, data=result)


@app.post("/curriculum/reveal-explanation/{concept}", response_model=APIResponse, tags=["Curriculum"])
async def reveal_explanation(concept: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    user_id = _get_user_id(current_user)
    result = _feedback_gen.generate(concept, "explain", "")
    engine = ScoringEngine(user_id)
    engine.apply_explanation_penalty(concept)
    return APIResponse(success=True, data={"explanation": result["feedback"]})