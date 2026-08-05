from datetime import datetime, timezone

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.routers.preferences import _load_preferences

# Maps a notification's type to the NotificationPreferences flag that must
# be on for it to actually be created — ties this feature into the
# notification-preferences the user already controls in Ayarlar.
PREF_GATE = {
    "upload_completed": "notifyUpload",
    "analysis_completed": "notifyAnalysis",
    "system": "notifySystem",
    "security": "notifySecurity",
}


async def create_notification(
    db: AsyncIOMotorDatabase, owner_id: ObjectId, notif_type: str, title: str, message: str
) -> None:
    # Security notifications are never gated — settings.html tells the user
    # these "always stay on" regardless of the master toggle.
    pref_key = PREF_GATE.get(notif_type)
    if pref_key and notif_type != "security":
        prefs = (await _load_preferences(owner_id))["notifications"]
        if not (prefs.get("notifyMaster", True) and prefs.get(pref_key, True)):
            return

    await db.notifications.insert_one(
        {
            "owner_id": owner_id,
            "type": notif_type,
            "title": title,
            "message": message,
            "read": False,
            "created_at": datetime.now(timezone.utc),
        }
    )
