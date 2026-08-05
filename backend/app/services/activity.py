from datetime import datetime, timezone

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

# Scope is intentionally limited to case / upload / AI actions — not every
# request (logins, settings changes) is logged here.
ACTIVITY_TYPES = {
    "case_created",
    "case_deleted",
    "case_renamed",
    "upload_created",
    "ai_chat",
    "ai_summary",
    "ai_risks",
    "ai_draft",
    "plan_upgraded",
}


async def log_activity(
    db: AsyncIOMotorDatabase,
    owner_id: ObjectId,
    activity_type: str,
    description: str,
    case_id: ObjectId | None = None,
) -> None:
    assert activity_type in ACTIVITY_TYPES, f"Unknown activity type: {activity_type}"
    doc = {
        "owner_id": owner_id,
        "type": activity_type,
        "description": description,
        "created_at": datetime.now(timezone.utc),
    }
    if case_id is not None:
        doc["case_id"] = case_id
    await db.activity.insert_one(doc)
