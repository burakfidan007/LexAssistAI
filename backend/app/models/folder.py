from pydantic import BaseModel, Field, field_validator

FOLDER_NAME_MAX_LENGTH = 60


class FolderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=FOLDER_NAME_MAX_LENGTH)

    @field_validator("name")
    @classmethod
    def _clean_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Klasör adı boş olamaz.")
        return v


class FolderPublic(BaseModel):
    id: str
    name: str
    slug: str
    icon: str
    isDefault: bool
