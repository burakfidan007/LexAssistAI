from datetime import datetime

from pydantic import BaseModel


class ActivityPublic(BaseModel):
    id: str
    type: str
    description: str
    createdAt: datetime
