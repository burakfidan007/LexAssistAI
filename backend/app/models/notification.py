from datetime import datetime

from pydantic import BaseModel


class NotificationPublic(BaseModel):
    id: str
    type: str
    title: str
    message: str
    read: bool = False
    createdAt: datetime
