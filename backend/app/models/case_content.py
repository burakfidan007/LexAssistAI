from datetime import datetime

from pydantic import BaseModel


class ChatMessagePublic(BaseModel):
    id: str
    role: str  # "user" | "ai"
    content: str
    createdAt: datetime


class AIResultPublic(BaseModel):
    type: str  # "summary" | "risks" | "draft"
    result: str
    uploadId: str
    generatedAt: datetime
