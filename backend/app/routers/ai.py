from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from app.core.rate_limit import limiter
from app.db.mongo import get_database
from app.deps import get_current_user
from app.services.ai import gemini_service as ai_service
from app.services.activity import log_activity
from app.services.cleanup import delete_all_ai_history_for_user
from app.services.notifications import create_notification
from app.services.storage import get_storage

router = APIRouter(prefix="/ai", tags=["ai"])


def _valid_object_id(value: str | None) -> ObjectId | None:
    if value and ObjectId.is_valid(value):
        return ObjectId(value)
    return None


async def _load_document_bytes(upload_id: str, owner_id: ObjectId) -> bytes | None:
    if not ObjectId.is_valid(upload_id):
        return None

    db = get_database()
    upload = await db.uploads.find_one({"_id": ObjectId(upload_id), "owner_id": owner_id})
    if upload is None:
        return None

    # storage_key for new uploads; stored_path (absolute) for legacy local docs.
    key = upload.get("storage_key") or upload.get("stored_path")
    return await get_storage().load(key) if key else None


async def _persist_chat_message(db, owner_id: ObjectId, case_id: ObjectId, role: str, content: str) -> None:
    await db.chat_messages.insert_one({
        "owner_id": owner_id,
        "case_id": case_id,
        "role": role,
        "content": content,
        "created_at": datetime.now(timezone.utc),
    })


async def _persist_ai_result(
    db, owner_id: ObjectId, case_id: ObjectId, upload_id: ObjectId, result_type: str, result: str
) -> None:
    await db.ai_results.update_one(
        {"owner_id": owner_id, "case_id": case_id, "type": result_type},
        {"$set": {
            "upload_id": upload_id,
            "result": result,
            "generated_at": datetime.now(timezone.utc),
        }},
        upsert=True,
    )


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=ai_service.MAX_QUESTION_LENGTH)
    uploadId: str | None = None
    caseId: str | None = None

    @field_validator("question")
    @classmethod
    def _clean_question(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Soru boş olamaz.")
        return v


class ChatResponse(BaseModel):
    answer: str


class DocumentActionRequest(BaseModel):
    uploadId: str = Field(min_length=1)
    caseId: str | None = None


class AnalysisResponse(BaseModel):
    result: str


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("20/minute")
async def chat(request: Request, payload: ChatRequest, current_user: dict = Depends(get_current_user)):
    document_bytes = None
    if payload.uploadId:
        document_bytes = await _load_document_bytes(payload.uploadId, current_user["_id"])

    try:
        answer = await ai_service.chat(payload.question, document_bytes)
    except ai_service.AIServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    db = get_database()
    case_object_id = _valid_object_id(payload.caseId)
    if case_object_id is not None:
        await _persist_chat_message(db, current_user["_id"], case_object_id, "user", payload.question)
        await _persist_chat_message(db, current_user["_id"], case_object_id, "ai", answer)

    await log_activity(
        db, current_user["_id"], "ai_chat", f'AI sohbet: "{payload.question[:60]}"', case_id=case_object_id
    )
    return ChatResponse(answer=answer)


@router.post("/summary", response_model=AnalysisResponse)
@limiter.limit("20/minute")
async def summary(request: Request, payload: DocumentActionRequest, current_user: dict = Depends(get_current_user)):
    document_bytes = await _load_document_bytes(payload.uploadId, current_user["_id"])
    if document_bytes is None:
        raise HTTPException(status_code=404, detail="Dosya bulunamadı.")

    try:
        result = await ai_service.generate_summary(
            document_bytes, cache_key=(str(current_user["_id"]), f"summary:{payload.uploadId}")
        )
    except ai_service.AIServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    db = get_database()
    case_object_id = _valid_object_id(payload.caseId)
    if case_object_id is not None:
        await _persist_ai_result(
            db, current_user["_id"], case_object_id, ObjectId(payload.uploadId), "summary", result
        )

    await log_activity(db, current_user["_id"], "ai_summary", "Dava özeti oluşturuldu", case_id=case_object_id)
    await create_notification(db, current_user["_id"], "analysis_completed", "Analiz Tamamlandı", "Dava özeti hazır.")
    return AnalysisResponse(result=result)


@router.post("/risks", response_model=AnalysisResponse)
@limiter.limit("20/minute")
async def risks(request: Request, payload: DocumentActionRequest, current_user: dict = Depends(get_current_user)):
    document_bytes = await _load_document_bytes(payload.uploadId, current_user["_id"])
    if document_bytes is None:
        raise HTTPException(status_code=404, detail="Dosya bulunamadı.")

    try:
        result = await ai_service.analyze_risks(
            document_bytes, cache_key=(str(current_user["_id"]), f"risks:{payload.uploadId}")
        )
    except ai_service.AIServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    db = get_database()
    case_object_id = _valid_object_id(payload.caseId)
    if case_object_id is not None:
        await _persist_ai_result(
            db, current_user["_id"], case_object_id, ObjectId(payload.uploadId), "risks", result
        )

    await log_activity(db, current_user["_id"], "ai_risks", "Risk analizi tamamlandı", case_id=case_object_id)
    await create_notification(db, current_user["_id"], "analysis_completed", "Analiz Tamamlandı", "Risk analizi hazır.")
    return AnalysisResponse(result=result)


@router.post("/draft", response_model=AnalysisResponse)
@limiter.limit("20/minute")
async def draft(request: Request, payload: DocumentActionRequest, current_user: dict = Depends(get_current_user)):
    document_bytes = await _load_document_bytes(payload.uploadId, current_user["_id"])
    if document_bytes is None:
        raise HTTPException(status_code=404, detail="Dosya bulunamadı.")

    try:
        result = await ai_service.generate_draft(
            document_bytes, cache_key=(str(current_user["_id"]), f"draft:{payload.uploadId}")
        )
    except ai_service.AIServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    db = get_database()
    case_object_id = _valid_object_id(payload.caseId)
    if case_object_id is not None:
        await _persist_ai_result(
            db, current_user["_id"], case_object_id, ObjectId(payload.uploadId), "draft", result
        )

    await log_activity(db, current_user["_id"], "ai_draft", "Dilekçe taslağı oluşturuldu", case_id=case_object_id)
    await create_notification(db, current_user["_id"], "analysis_completed", "Analiz Tamamlandı", "Dilekçe taslağı hazır.")
    return AnalysisResponse(result=result)


@router.delete("/history")
async def delete_ai_history(current_user: dict = Depends(get_current_user)):
    """Danger Zone — permanently removes all of the user's AI chat history
    and stored analysis results across every case."""
    db = get_database()
    deleted = await delete_all_ai_history_for_user(db, current_user["_id"])
    return {"deleted": deleted}
