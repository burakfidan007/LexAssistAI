from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.ids import parse_object_id
from app.db.mongo import get_database
from app.deps import get_current_user
from app.models.folder import FolderCreate, FolderPublic
from app.services.folders import ensure_defaults, slugify, unique_slug

router = APIRouter(prefix="/folders", tags=["folders"])

_FOLDER_NOT_FOUND = "Klasör bulunamadı."


def _to_public(folder: dict) -> FolderPublic:
    return FolderPublic(
        id=str(folder["_id"]),
        name=folder["name"],
        slug=folder["slug"],
        icon=folder.get("icon", "folder"),
        isDefault=folder.get("is_default", False),
    )


@router.get("", response_model=list[FolderPublic])
async def list_folders(current_user: dict = Depends(get_current_user)):
    db = get_database()
    await ensure_defaults(db, current_user["_id"])
    # Defaults first, then custom folders by creation order.
    folders = (
        await db.folders.find({"owner_id": current_user["_id"]})
        .sort([("is_default", -1), ("created_at", 1)])
        .to_list(200)
    )
    return [_to_public(f) for f in folders]


@router.post("", response_model=FolderPublic, status_code=status.HTTP_201_CREATED)
async def create_folder(payload: FolderCreate, current_user: dict = Depends(get_current_user)):
    db = get_database()
    await ensure_defaults(db, current_user["_id"])

    slug = await unique_slug(db, current_user["_id"], slugify(payload.name))
    folder_doc = {
        "owner_id": current_user["_id"],
        "slug": slug,
        "name": payload.name,
        "icon": "folder",
        "is_default": False,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.folders.insert_one(folder_doc)
    folder_doc["_id"] = result.inserted_id
    return _to_public(folder_doc)


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(folder_id: str, current_user: dict = Depends(get_current_user)):
    db = get_database()
    folder = await db.folders.find_one(
        {"_id": parse_object_id(folder_id, detail=_FOLDER_NOT_FOUND), "owner_id": current_user["_id"]}
    )
    if folder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_FOLDER_NOT_FOUND)
    if folder.get("is_default", False):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Varsayılan klasörler silinemez.")

    # Unfile any cases that were in this folder rather than orphaning them.
    await db.cases.update_many(
        {"owner_id": current_user["_id"], "folder": folder["slug"]},
        {"$set": {"folder": None}},
    )
    await db.folders.delete_one({"_id": folder["_id"]})
    return None
