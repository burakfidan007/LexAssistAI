import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, UploadFile, status
from pymongo.errors import DuplicateKeyError

from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.security import create_access_token, generate_secure_token, hash_password, hash_token, verify_password
from app.db.mongo import get_database
from app.deps import get_current_user
from app.models.user import (
    ForgotPasswordRequest,
    PasswordChange,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserLogin,
    UserPublic,
    UserRegister,
    UserUpdate,
    VerifyEmailRequest,
)
from app.services.cleanup import delete_account_data
from app.services.email import send_password_reset_email, send_verification_email
from app.services.notifications import create_notification
from app.services.storage import get_storage

router = APIRouter(prefix="/auth", tags=["auth"])


def _to_public(user: dict) -> UserPublic:
    return UserPublic(
        id=str(user["_id"]),
        fullName=user["full_name"],
        email=user["email"],
        lawFirm=user.get("law_firm"),
        phone=user.get("phone"),
        baroNumber=user.get("baro_number"),
        city=user.get("city"),
        plan=user.get("plan", "free"),
        emailVerified=user.get("email_verified", False),
        hasAvatar=bool(user.get("avatar_key") or user.get("avatar_path")),
    )


def _is_expired(expires_at: datetime | None) -> bool:
    if expires_at is None:
        return True
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at < datetime.now(timezone.utc)


async def _issue_verification_token(db, user_id, email: str) -> None:
    verification_token = generate_secure_token()
    await db.users.update_one(
        {"_id": user_id},
        {
            "$set": {
                "verification_token_hash": hash_token(verification_token),
                "verification_token_expires": datetime.now(timezone.utc)
                + timedelta(hours=settings.verification_token_expire_hours),
            }
        },
    )
    verify_url = f"{settings.frontend_base_url}/verify-email.html?token={verification_token}"
    await send_verification_email(email, verify_url)


@router.post("/register", response_model=TokenResponse)
@limiter.limit("5/minute")
async def register(request: Request, payload: UserRegister):
    db = get_database()

    email_taken = HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bu e-posta zaten kayıtlı.")

    # Fast-path check for the friendly common case...
    if await db.users.find_one({"email": payload.email}):
        raise email_taken

    user_doc = {
        "full_name": payload.fullName,
        "email": payload.email,
        "law_firm": payload.lawFirm,
        "password_hash": hash_password(payload.password),
        "plan": "free",
        "email_verified": False,
        "created_at": datetime.now(timezone.utc),
    }
    try:
        result = await db.users.insert_one(user_doc)
    except DuplicateKeyError:
        # ...and the unique index is the authoritative guard against the
        # find_one-then-insert race between two concurrent registrations.
        raise email_taken
    user_doc["_id"] = result.inserted_id

    # Verification is informational, not a login gate — registering still
    # signs the user in immediately, matching the existing flow.
    await _issue_verification_token(db, user_doc["_id"], payload.email)

    token = create_access_token(str(result.inserted_id))
    return TokenResponse(token=token, user=_to_public(user_doc))


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, payload: UserLogin):
    db = get_database()
    user = await db.users.find_one({"email": payload.email})

    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="E-posta veya şifre hatalı."
    )
    if user is None or not verify_password(payload.password, user["password_hash"]):
        raise invalid_credentials

    token = create_access_token(str(user["_id"]))
    return TokenResponse(token=token, user=_to_public(user))


@router.get("/me", response_model=UserPublic)
async def me(current_user: dict = Depends(get_current_user)):
    return _to_public(current_user)


@router.patch("/me", response_model=UserPublic)
async def update_me(payload: UserUpdate, current_user: dict = Depends(get_current_user)):
    db = get_database()
    updates = {
        "full_name": payload.fullName,
        "law_firm": payload.lawFirm,
        "phone": payload.phone,
        "baro_number": payload.baroNumber,
        "city": payload.city,
    }
    await db.users.update_one({"_id": current_user["_id"]}, {"$set": updates})
    current_user.update(updates)
    return _to_public(current_user)


_AVATAR_CONTENT_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


@router.post("/me/avatar", response_model=UserPublic)
async def upload_avatar(file: UploadFile, current_user: dict = Depends(get_current_user)):
    """Stores a profile photo (JPG/PNG/WebP, ≤2MB). Replaces any previous
    one on disk so avatars don't accumulate."""
    ext = _AVATAR_CONTENT_TYPES.get(file.content_type)
    if ext is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Yalnızca JPG, PNG veya WebP kabul edilir.")

    contents = await file.read()
    if len(contents) > settings.max_avatar_size_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fotoğraf boyutu 2MB sınırını aşıyor.")

    db = get_database()
    storage = get_storage()

    # Remove the previous avatar so they don't accumulate.
    old_key = current_user.get("avatar_key") or current_user.get("avatar_path")
    if old_key:
        await storage.delete(old_key)

    avatar_key = f"avatars/{current_user['_id']}_{uuid.uuid4().hex}{ext}"
    await storage.save(avatar_key, contents, file.content_type)

    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"avatar_key": avatar_key, "avatar_content_type": file.content_type},
         "$unset": {"avatar_path": ""}},
    )
    current_user["avatar_key"] = avatar_key
    current_user["avatar_content_type"] = file.content_type
    current_user.pop("avatar_path", None)
    return _to_public(current_user)


@router.get("/me/avatar")
async def get_avatar(current_user: dict = Depends(get_current_user)):
    key = current_user.get("avatar_key") or current_user.get("avatar_path")
    data = await get_storage().load(key) if key else None
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profil fotoğrafı bulunamadı.")
    return Response(content=data, media_type=current_user.get("avatar_content_type") or "image/jpeg")


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def change_password(request: Request, payload: PasswordChange, current_user: dict = Depends(get_current_user)):
    if not verify_password(payload.currentPassword, current_user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Mevcut şifre hatalı.")

    if verify_password(payload.newPassword, current_user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Yeni şifre mevcut şifreyle aynı olamaz."
        )

    db = get_database()
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"password_hash": hash_password(payload.newPassword)}},
    )
    await create_notification(
        db, current_user["_id"], "security", "Şifre Değiştirildi", "Hesap şifreniz başarıyla güncellendi."
    )
    return None


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(current_user: dict = Depends(get_current_user)):
    # JWTs are stateless and short-lived in this MVP; nothing to revoke
    # server-side yet. Client already clears its local session on logout.
    return None


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(current_user: dict = Depends(get_current_user)):
    """Danger Zone — permanently deletes the account and every piece of
    data belonging to it. The whole cascade lives in the cleanup service."""
    await delete_account_data(get_database(), current_user)
    return None


@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def forgot_password(request: Request, payload: ForgotPasswordRequest):
    db = get_database()
    user = await db.users.find_one({"email": payload.email})

    if user is not None:
        reset_token = generate_secure_token()
        await db.users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "reset_token_hash": hash_token(reset_token),
                    "reset_token_expires": datetime.now(timezone.utc)
                    + timedelta(minutes=settings.reset_token_expire_minutes),
                }
            },
        )
        reset_url = f"{settings.frontend_base_url}/reset-password.html?token={reset_token}"
        await send_password_reset_email(user["email"], reset_url)

    # Always 204 whether or not the email exists — prevents account
    # enumeration via response differences.
    return None


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def reset_password(request: Request, payload: ResetPasswordRequest):
    db = get_database()
    user = await db.users.find_one({"reset_token_hash": hash_token(payload.token)})

    if user is None or _is_expired(user.get("reset_token_expires")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Bağlantı geçersiz veya süresi dolmuş."
        )

    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {"password_hash": hash_password(payload.newPassword)},
            "$unset": {"reset_token_hash": "", "reset_token_expires": ""},
        },
    )
    await create_notification(
        db, user["_id"], "security", "Şifre Sıfırlandı", "Şifreniz sıfırlama bağlantısı ile güncellendi."
    )
    return None


@router.post("/verify-email", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def verify_email(request: Request, payload: VerifyEmailRequest):
    db = get_database()
    user = await db.users.find_one({"verification_token_hash": hash_token(payload.token)})

    if user is None or _is_expired(user.get("verification_token_expires")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Doğrulama bağlantısı geçersiz veya süresi dolmuş."
        )

    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {"email_verified": True},
            "$unset": {"verification_token_hash": "", "verification_token_expires": ""},
        },
    )
    return None


@router.post("/resend-verification", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def resend_verification(request: Request, payload: ResendVerificationRequest):
    db = get_database()
    user = await db.users.find_one({"email": payload.email})

    if user is not None and not user.get("email_verified", False):
        await _issue_verification_token(db, user["_id"], user["email"])

    # Same anti-enumeration reasoning as forgot-password.
    return None
