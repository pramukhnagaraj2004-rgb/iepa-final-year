from pydantic import BaseModel
from typing import Any, Dict, List, Optional

class AnalyzeRequest(BaseModel):
    code: str
    learner_id: Optional[str] = None
    language: Optional[str] = "python"

class AnalyzeManualRequest(BaseModel):
    error_raw: str
    learner_id: Optional[str] = "default"
    code: Optional[str] = ""

class ClusterRequest(BaseModel):
    error_raw: str

class SubmitAnswersRequest(BaseModel):
    theory_answer: str
    coding_results: List[bool]
    theory_question_id: Optional[str] = None

class CheckCodeRequest(BaseModel):
    code: str

class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    upgrade_url: Optional[str] = None

class SubmitAnswerRequest(BaseModel):
    theory_answer: str
    coding_results: List[bool]

class CheckCodeRequest(BaseModel):
    code: str