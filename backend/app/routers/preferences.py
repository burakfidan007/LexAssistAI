from fastapi import APIRouter, Depends, HTTPException, status

from app.db.mongo import get_database
from app.deps import get_current_user
from app.models.preferences import (
    AIPreferences,
    AppearancePreferences,
    NotificationPreferences,
    PdfPreferences,
    UserPreferences,
    UserPreferencesUpdate,
)

router = APIRouter(prefix="/preferences", tags=["preferences"])

SECTION_MODELS = {
    "notifications": NotificationPreferences,
    "ai": AIPreferences,
    "appearance": AppearancePreferences,
    "pdf": PdfPreferences,
}


async def _load_preferences(owner_id) -> dict:
    db = get_database()
    doc = await db.preferences.find_one({"owner_id": owner_id}) or {}
    doc.pop("_id", None)
    doc.pop("owner_id", None)
    return UserPreferences(**doc).model_dump()


@router.get("", response_model=UserPreferences)
async def get_preferences(current_user: dict = Depends(get_current_user)):
    return await _load_preferences(current_user["_id"])


@router.put("", response_model=UserPreferences)
async def update_preferences(payload: UserPreferencesUpdate, current_user: dict = Depends(get_current_user)):
    merged = await _load_preferences(current_user["_id"])

    updates = payload.model_dump(exclude_unset=True)
    for section, values in updates.items():
        if values is None:
            continue
        model = SECTION_MODELS[section]
        unknown = set(values) - set(model.model_fields.keys())
        if unknown:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Geçersiz alan(lar): {', '.join(sorted(unknown))}",
            )
        merged[section].update(values)
        try:
            merged[section] = model(**merged[section]).model_dump()
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    db = get_database()
    await db.preferences.update_one(
        {"owner_id": current_user["_id"]},
        {"$set": merged},
        upsert=True,
    )
    return UserPreferences(**merged)
