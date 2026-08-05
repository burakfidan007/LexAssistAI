"""Data-cleanup / cascade-delete operations.

Consolidated here so the Danger Zone endpoints and the account-delete
cascade share one implementation, and so auth.py no longer needs the
router-to-router lazy imports it used to reach these helpers."""

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.storage import get_storage


async def delete_all_uploads_for_user(db: AsyncIOMotorDatabase, owner_id: ObjectId) -> int:
    """Deletes every upload owned by the user — both the MongoDB documents
    and the corresponding stored files (disk or Firebase). Returns how many
    were removed, so stored files never get orphaned."""
    storage = get_storage()
    uploads = await db.uploads.find({"owner_id": owner_id}).to_list(1000)
    for upload in uploads:
        key = upload.get("storage_key") or upload.get("stored_path")
        if key:
            await storage.delete(key)
    result = await db.uploads.delete_many({"owner_id": owner_id})
    return result.deleted_count


async def delete_all_ai_history_for_user(db: AsyncIOMotorDatabase, owner_id: ObjectId) -> int:
    """Deletes all persisted AI conversations for the user — chat messages
    and stored summary/risk/draft results. Returns total removed."""
    chat_result = await db.chat_messages.delete_many({"owner_id": owner_id})
    results_result = await db.ai_results.delete_many({"owner_id": owner_id})
    return chat_result.deleted_count + results_result.deleted_count


async def delete_account_data(db: AsyncIOMotorDatabase, user: dict) -> None:
    """Full account cascade: removes every collection owned by the user
    (uploads + files, AI history, cases, folders, activity, notifications,
    preferences), the avatar file, and finally the user document."""
    owner_id = user["_id"]
    avatar_key = user.get("avatar_key") or user.get("avatar_path")
    if avatar_key:
        await get_storage().delete(avatar_key)
    await delete_all_uploads_for_user(db, owner_id)
    await delete_all_ai_history_for_user(db, owner_id)
    await db.cases.delete_many({"owner_id": owner_id})
    await db.folders.delete_many({"owner_id": owner_id})
    await db.activity.delete_many({"owner_id": owner_id})
    await db.notifications.delete_many({"owner_id": owner_id})
    await db.preferences.delete_one({"owner_id": owner_id})
    await db.users.delete_one({"_id": owner_id})
