from datetime import datetime

from pydantic import BaseModel


class UploadPublic(BaseModel):
    id: str
    fileName: str
    size: int
    contentType: str
    status: str
    caseId: str | None = None
    caseTitle: str | None = None
    createdAt: datetime


class UsagePublic(BaseModel):
    used: int
    limit: int
    totalBytes: int = 0
