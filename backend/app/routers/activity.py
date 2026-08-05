from fastapi import APIRouter, Depends

from app.core.ids import parse_object_id
from app.db.mongo import get_database
from app.deps import get_current_user
from app.models.activity import ActivityPublic

router = APIRouter(prefix="/activity", tags=["activity"])


def _to_public(entry: dict) -> ActivityPublic:
    return ActivityPublic(
        id=str(entry["_id"]),
        type=entry["type"],
        description=entry["description"],
        createdAt=entry["created_at"],
    )


@router.get("", response_model=list[ActivityPublic])
async def list_activity(
    limit: int = 50, caseId: str | None = None, current_user: dict = Depends(get_current_user)
):
    db = get_database()
    query: dict = {"owner_id": current_user["_id"]}
    if caseId is not None:
        query["case_id"] = parse_object_id(caseId, detail="Dava bulunamadı.")

    entries = await db.activity.find(query).sort("created_at", -1).to_list(min(limit, 200))
    return [_to_public(e) for e in entries]
