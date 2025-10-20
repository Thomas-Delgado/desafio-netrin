from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum

class StatusEnum(str, Enum):
    ENQUEUED = "enqueued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"

class ScrapingRequest(BaseModel):
    cnpj: str = Field(..., max_length=14)

class ScrapingResponse(BaseModel):
    task_id: str
    status: StatusEnum
    message: str

class TaskStatus(BaseModel):
    task_id: str
    status: StatusEnum
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# ===================== Custom Exceptions =====================
class NotFoundError(Exception):
    pass

class InternalServerError(Exception):
    pass

class InvalidRequestError(Exception):
    pass
