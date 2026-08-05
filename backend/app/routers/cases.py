import random
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pymongo import ReturnDocument

from app.core.ids import parse_object_id
from app.db.mongo import get_database
from app.deps import get_current_user
from app.models.case import CaseCreate, CaseFolderUpdate, CasePublic, CaseUpdate
from app.models.case_content import AIResultPublic, ChatMessagePublic
from app.models.upload import UploadPublic
from app.routers.uploads import _to_public as _upload_to_public
from app.services.activity import log_activity
from app.services.folders import user_folder_slugs

router = APIRouter(prefix="/cases", tags=["cases"])

_CASE_NOT_FOUND = "Dava bulunamadı."


def _generate_case_number() -> str:
    return f"{datetime.now(timezone.utc).year}/{random.randint(100, 999)}"


async def _to_public(case: dict) -> CasePublic:
    db = get_database()
    pdf_count = await db.uploads.count_documents({"case_id": case["_id"]})
    return CasePublic(
        id=str(case["_id"]),
        title=case["title"],
        client=case.get("client"),
        folder=case.get("folder"),
        status=case.get("status", "devam"),
        caseNumber=case.get("case_number") or _generate_case_number(),
        pdfCount=pdf_count,
        pinned=case.get("pinned", False),
        createdAt=case["created_at"],
    )


async def _get_owned_case(case_id: str, owner_id) -> dict:
    db = get_database()
    case = await db.cases.find_one({"_id": parse_object_id(case_id, detail=_CASE_NOT_FOUND), "owner_id": owner_id})
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_CASE_NOT_FOUND)
    return case


@router.get("", response_model=list[CasePublic])
async def list_cases(current_user: dict = Depends(get_current_user)):
    db = get_database()
    cases = await db.cases.find({"owner_id": current_user["_id"]}).sort("created_at", -1).to_list(200)
    return [await _to_public(c) for c in cases]


@router.get("/{case_id}", response_model=CasePublic)
async def get_case(case_id: str, current_user: dict = Depends(get_current_user)):
    case = await _get_owned_case(case_id, current_user["_id"])
    return await _to_public(case)


@router.get("/{case_id}/primary-upload", response_model=UploadPublic)
async def get_primary_upload(case_id: str, current_user: dict = Depends(get_current_user)):
    """The PDF this case's Dashboard should show — the most recently
    uploaded file linked to this case, not the user's most recent upload
    overall (that was the bug: switching cases showed the wrong PDF)."""
    case = await _get_owned_case(case_id, current_user["_id"])
    db = get_database()
    upload = await db.uploads.find_one(
        {"case_id": case["_id"], "owner_id": current_user["_id"]},
        sort=[("created_at", -1)],
    )
    if upload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bu davaya ait PDF bulunamadı.")
    return _upload_to_public(upload)


@router.get("/{case_id}/chat", response_model=list[ChatMessagePublic])
async def get_case_chat(case_id: str, current_user: dict = Depends(get_current_user)):
    case = await _get_owned_case(case_id, current_user["_id"])
    db = get_database()
    messages = (
        await db.chat_messages.find({"case_id": case["_id"], "owner_id": current_user["_id"]})
        .sort("created_at", 1)
        .to_list(500)
    )
    return [
        ChatMessagePublic(id=str(m["_id"]), role=m["role"], content=m["content"], createdAt=m["created_at"])
        for m in messages
    ]


@router.get("/{case_id}/ai-results", response_model=dict[str, AIResultPublic])
async def get_case_ai_results(case_id: str, current_user: dict = Depends(get_current_user)):
    case = await _get_owned_case(case_id, current_user["_id"])
    db = get_database()
    results = await db.ai_results.find({"case_id": case["_id"], "owner_id": current_user["_id"]}).to_list(10)
    return {
        r["type"]: AIResultPublic(
            type=r["type"], result=r["result"], uploadId=str(r["upload_id"]), generatedAt=r["generated_at"]
        )
        for r in results
    }


@router.post("", response_model=CasePublic, status_code=status.HTTP_201_CREATED)
async def create_case(payload: CaseCreate, current_user: dict = Depends(get_current_user)):
    db = get_database()
    case_doc = {
        "owner_id": current_user["_id"],
        "title": payload.title,
        "client": payload.client,
        "folder": payload.folder,
        "status": "devam",
        "case_number": _generate_case_number(),
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.cases.insert_one(case_doc)
    case_doc["_id"] = result.inserted_id
    await log_activity(
        db, current_user["_id"], "case_created", f'Dava oluşturuldu: "{payload.title}"', case_id=case_doc["_id"]
    )
    return await _to_public(case_doc)


@router.patch("/{case_id}", response_model=CasePublic)
async def update_case(case_id: str, payload: CaseUpdate, current_user: dict = Depends(get_current_user)):
    db = get_database()
    result = await db.cases.find_one_and_update(
        {"_id": parse_object_id(case_id, detail=_CASE_NOT_FOUND), "owner_id": current_user["_id"]},
        {"$set": {"title": payload.title}},
        return_document=ReturnDocument.AFTER,
    )
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_CASE_NOT_FOUND)
    await log_activity(
        db, current_user["_id"], "case_renamed", f'Dava yeniden adlandırıldı: "{payload.title}"',
        case_id=result["_id"],
    )
    return await _to_public(result)


@router.patch("/{case_id}/folder", response_model=CasePublic)
async def move_case(case_id: str, payload: CaseFolderUpdate, current_user: dict = Depends(get_current_user)):
    case_object_id = parse_object_id(case_id, detail=_CASE_NOT_FOUND)
    db = get_database()

    # A non-null target must be one of the user's own folders.
    if payload.folder is not None and payload.folder not in await user_folder_slugs(db, current_user["_id"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Klasör bulunamadı.")

    result = await db.cases.find_one_and_update(
        {"_id": case_object_id, "owner_id": current_user["_id"]},
        {"$set": {"folder": payload.folder}},
        return_document=ReturnDocument.AFTER,
    )
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_CASE_NOT_FOUND)
    return await _to_public(result)


@router.patch("/{case_id}/pin", response_model=CasePublic)
async def toggle_pin(case_id: str, current_user: dict = Depends(get_current_user)):
    db = get_database()
    case = await db.cases.find_one(
        {"_id": parse_object_id(case_id, detail=_CASE_NOT_FOUND), "owner_id": current_user["_id"]}
    )
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_CASE_NOT_FOUND)

    result = await db.cases.find_one_and_update(
        {"_id": case["_id"]},
        {"$set": {"pinned": not case.get("pinned", False)}},
        return_document=ReturnDocument.AFTER,
    )
    return await _to_public(result)


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case(case_id: str, current_user: dict = Depends(get_current_user)):
    db = get_database()
    deleted = await db.cases.find_one_and_delete(
        {"_id": parse_object_id(case_id, detail=_CASE_NOT_FOUND), "owner_id": current_user["_id"]}
    )
    if deleted is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_CASE_NOT_FOUND)
    await log_activity(
        db, current_user["_id"], "case_deleted", f'Dava silindi: "{deleted["title"]}"', case_id=deleted["_id"]
    )
    return None
