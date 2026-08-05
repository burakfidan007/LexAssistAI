from fastapi import APIRouter, Depends, HTTPException, status
from pymongo import ReturnDocument

from app.core.ids import parse_object_id
from app.db.mongo import get_database
from app.deps import get_current_user
from app.models.notification import NotificationPublic

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _to_public(entry: dict) -> NotificationPublic:
    return NotificationPublic(
        id=str(entry["_id"]),
        type=entry["type"],
        title=entry["title"],
        message=entry["message"],
        read=entry.get("read", False),
        createdAt=entry["created_at"],
    )


@router.get("", response_model=list[NotificationPublic])
async def list_notifications(limit: int = 20, current_user: dict = Depends(get_current_user)):
    db = get_database()
    entries = (
        await db.notifications.find({"owner_id": current_user["_id"]})
        .sort("created_at", -1)
        .to_list(min(limit, 100))
    )
    return [_to_public(e) for e in entries]


@router.get("/unread-count")
async def unread_count(current_user: dict = Depends(get_current_user)):
    db = get_database()
    count = await db.notifications.count_documents({"owner_id": current_user["_id"], "read": False})
    return {"count": count}


@router.post("/{notification_id}/read", response_model=NotificationPublic)
async def mark_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    db = get_database()
    result = await db.notifications.find_one_and_update(
        {"_id": parse_object_id(notification_id, detail="Bildirim bulunamadı."), "owner_id": current_user["_id"]},
        {"$set": {"read": True}},
        return_document=ReturnDocument.AFTER,
    )
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bildirim bulunamadı.")
    return _to_public(result)


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_read(current_user: dict = Depends(get_current_user)):
    db = get_database()
    await db.notifications.update_many(
        {"owner_id": current_user["_id"], "read": False},
        {"$set": {"read": True}},
    )
    return None
