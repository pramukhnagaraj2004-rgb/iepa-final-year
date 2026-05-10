import os
import json
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from contextlib import asynccontextmanager

from iepa.backend.api.models import AnalyzeRequest, ClusterRequest, APIResponse
from iepa.backend.engine.pipeline import analyze
from iepa.backend.ml.clustering.error_clusterer import ErrorClusterer

# Initialize singleton for clusterer
clusterer = ErrorClusterer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[*] Starting up API server...")
    print("[*] Initializing ErrorClusterer...")
    try:
        clusterer.load_data()
        clusterer.embed_corpus()
        clusterer.cluster()
        print("[+] ErrorClusterer initialized successfully.")
    except Exception as e:
        print(f"[!] Failed to initialize ErrorClusterer: {e}")
    
    yield
    print("[*] Shutting down API server...")

app = FastAPI(title="IEPA API", version="1.0.0", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"Incoming: {request.method} {request.url.path}")
    response = await call_next(request)
    print(f"Completed: {request.method} {request.url.path} - Status: {response.status_code}")
    return response

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

@app.get("/health", response_model=APIResponse)
async def health_check():
    return APIResponse(success=True, data={"status": "ok", "version": "1.0.0"})

@app.post("/analyze", response_model=APIResponse)
async def analyze_endpoint(req: AnalyzeRequest):
    if not req.error_raw.strip():
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "error_raw is required"}
        )
    try:
        result = analyze(req.learner_id, req.error_raw)
        return APIResponse(success=True, data=result)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/learner/{learner_id}/mastery", response_model=APIResponse)
async def get_mastery(learner_id: str):
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    state_path = project_root / "iepa" / "data" / "learners" / f"{learner_id}.json"
    
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

@app.get("/learner/{learner_id}/history", response_model=APIResponse)
async def get_history(learner_id: str):
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    state_path = project_root / "iepa" / "data" / "learners" / f"{learner_id}.json"
    
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

@app.post("/cluster", response_model=APIResponse)
async def cluster_endpoint(req: ClusterRequest):
    try:
        result = clusterer.get_cluster(req.error_raw)
        return APIResponse(success=True, data=result)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/concepts", response_model=APIResponse)
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
