from bson import ObjectId
from fastapi import HTTPException, status


def parse_object_id(value: str, *, detail: str = "Kayıt bulunamadı.") -> ObjectId:
    """Validates a path/query id and returns an ObjectId, raising a 404 with
    a domain-appropriate message on a malformed id. Replaces the
    `if not ObjectId.is_valid(x): raise HTTPException(404)` block that was
    repeated across every router."""
    if not ObjectId.is_valid(value):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
    return ObjectId(value)
