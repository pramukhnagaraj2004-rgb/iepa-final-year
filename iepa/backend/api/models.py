from pydantic import BaseModel
from typing import Any, Dict, List, Optional

class AnalyzeRequest(BaseModel):
    learner_id: str
    code: str
    language: Optional[str] = "python"

class AnalyzeManualRequest(BaseModel):
    learner_id: str
    error_raw: str
    code: Optional[str] = ""

class ClusterRequest(BaseModel):
    error_raw: str

class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
