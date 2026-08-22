import os
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any
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
        APIResponse
    )
    from iepa.backend.engine.pipeline import analyze
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
    print("[main.py] All backend submodules imported successfully.")
except Exception as err:
    import traceback
    print(f"[main.py] ERROR during submodules import: {err}")
    traceback.print_exc()
    raise err

# Initialize singletons for clusterer and sandbox code executor
clusterer = ErrorClusterer()
executor = CodeExecutor()

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
                        "timestamp": result.get("timestamp", "")
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