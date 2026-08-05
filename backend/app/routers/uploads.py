import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Response, UploadFile, status

from app.core.config import settings
from app.core.ids import parse_object_id
from app.db.mongo import get_database
from app.deps import get_current_user
from app.models.upload import UploadPublic, UsagePublic
from app.services.activity import log_activity
from app.services.cleanup import delete_all_uploads_for_user
from app.services.notifications import create_notification
from app.services.storage import get_storage

router = APIRouter(prefix="/uploads", tags=["uploads"])


def _to_public(upload: dict) -> UploadPublic:
    return UploadPublic(
        id=str(upload["_id"]),
        fileName=upload["file_name"],
        size=upload["size"],
        contentType=upload["content_type"],
        status=upload["status"],
        caseId=str(upload["case_id"]) if upload.get("case_id") else None,
        caseTitle=upload.get("case_title"),
        createdAt=upload["created_at"],
    )


@router.get("/usage", response_model=UsagePublic)
async def get_usage(current_user: dict = Depends(get_current_user)):
    db = get_database()
    used = await db.uploads.count_documents({"owner_id": current_user["_id"]})

    total_bytes = 0
    async for doc in db.uploads.aggregate([
        {"$match": {"owner_id": current_user["_id"]}},
        {"$group": {"_id": None, "total": {"$sum": "$size"}}},
    ]):
        total_bytes = doc["total"]

    return UsagePublic(used=used, limit=settings.free_tier_upload_limit, totalBytes=total_bytes)


@router.get("/history", response_model=list[UploadPublic])
async def get_history(current_user: dict = Depends(get_current_user)):
    db = get_database()
    uploads = await db.uploads.find({"owner_id": current_user["_id"]}).sort("created_at", -1).to_list(200)
    return [_to_public(u) for u in uploads]


@router.post("", response_model=UploadPublic, status_code=status.HTTP_201_CREATED)
async def create_upload(
    file: UploadFile,
    case_id: str | None = Form(None),
    current_user: dict = Depends(get_current_user),
):
    # Content-Type is client-supplied and spoofable; the magic-byte check
    # below on the actual bytes is the authoritative guard.
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Yalnızca PDF dosyaları kabul edilir.")

    db = get_database()

    if current_user.get("plan", "free") == "free":
        used = await db.uploads.count_documents({"owner_id": current_user["_id"]})
        if used >= settings.free_tier_upload_limit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ücretsiz plan yükleme limitine ulaştınız. Premium'a yükseltin.",
            )

    contents = await file.read()
    if len(contents) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dosya boyutu 25MB sınırını aşıyor.")
    # Magic-byte signature — real PDFs start with "%PDF-". Rejects files that
    # merely claim application/pdf but aren't (renamed/spoofed content).
    if not contents.startswith(b"%PDF-"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dosya geçerli bir PDF değil.")

    linked_case_id = None
    linked_case_title = None
    if case_id:
        case = await db.cases.find_one(
            {"_id": parse_object_id(case_id, detail="Dava bulunamadı."), "owner_id": current_user["_id"]}
        )
        if case is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dava bulunamadı.")
        linked_case_id = case["_id"]
        linked_case_title = case["title"]

    # Storage key uses a fresh uuid (never the client name), so nothing can
    # traverse the filesystem / bucket. The backend (disk or Firebase) is
    # chosen by config; the doc only ever stores this portable key.
    storage_key = f"uploads/{current_user['_id']}/{uuid.uuid4()}.pdf"
    await get_storage().save(storage_key, contents, "application/pdf")

    # Path(...).name strips any directory components from the display name
    # too, and it's length-capped.
    display_name = (Path(file.filename or "document.pdf").name or "document.pdf")[:200]

    upload_doc = {
        "owner_id": current_user["_id"],
        "case_id": linked_case_id,
        "case_title": linked_case_title,
        "file_name": display_name,
        "storage_key": storage_key,
        "size": len(contents),
        "content_type": file.content_type,
        "status": "tamamlandi",
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.uploads.insert_one(upload_doc)
    upload_doc["_id"] = result.inserted_id
    await log_activity(
        db, current_user["_id"], "upload_created", f'PDF yüklendi: "{upload_doc["file_name"]}"',
        case_id=linked_case_id,
    )
    await create_notification(
        db, current_user["_id"], "upload_completed", "Yükleme Tamamlandı",
        f'"{upload_doc["file_name"]}" başarıyla yüklendi.',
    )
    return _to_public(upload_doc)


@router.get("/{upload_id}/file")
async def get_upload_file(upload_id: str, current_user: dict = Depends(get_current_user)):
    db = get_database()
    upload = await db.uploads.find_one(
        {"_id": parse_object_id(upload_id, detail="Dosya bulunamadı."), "owner_id": current_user["_id"]}
    )
    if upload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dosya bulunamadı.")

    # storage_key for new uploads; stored_path (absolute) for legacy local docs.
    key = upload.get("storage_key") or upload.get("stored_path")
    data = await get_storage().load(key) if key else None
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dosya bulunamadı.")

    return Response(content=data, media_type="application/pdf")


@router.delete("")
async def delete_all_uploads(current_user: dict = Depends(get_current_user)):
    """Danger Zone — permanently removes every PDF the user has uploaded
    (documents + files on disk)."""
    db = get_database()
    deleted = await delete_all_uploads_for_user(db, current_user["_id"])
    return {"deleted": deleted}
