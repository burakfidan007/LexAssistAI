from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.validators import clean_optional, require_non_blank

TITLE_MAX_LENGTH = 300
SHORT_FIELD_MAX_LENGTH = 100


class CaseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=TITLE_MAX_LENGTH)
    client: str | None = Field(default=None, max_length=SHORT_FIELD_MAX_LENGTH)
    folder: str | None = Field(default=None, max_length=SHORT_FIELD_MAX_LENGTH)

    _clean_title = field_validator("title")(require_non_blank)
    _clean_client = field_validator("client")(clean_optional)
    _clean_folder = field_validator("folder")(clean_optional)


class CaseUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=TITLE_MAX_LENGTH)

    _clean_title = field_validator("title")(require_non_blank)


class CaseFolderUpdate(BaseModel):
    # None is a valid, explicit value here ("move to Klasörsüz"). The value
    # is a folder slug validated against the user's own folders in the
    # endpoint (folders are now per-user, not a fixed enum).
    folder: str | None = Field(default=None, max_length=SHORT_FIELD_MAX_LENGTH)


class CasePublic(BaseModel):
    id: str
    title: str
    client: str | None = None
    folder: str | None = None
    status: str = "devam"
    caseNumber: str
    pdfCount: int = 0
    pinned: bool = False
    createdAt: datetime
