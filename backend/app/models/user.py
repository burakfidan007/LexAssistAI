from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.password_policy import validate_password_strength
from app.core.validators import clean_optional, require_non_blank

NAME_MAX_LENGTH = 200
SHORT_FIELD_MAX_LENGTH = 100


class UserRegister(BaseModel):
    fullName: str = Field(min_length=1, max_length=NAME_MAX_LENGTH)
    email: EmailStr
    password: str
    lawFirm: str | None = Field(default=None, max_length=NAME_MAX_LENGTH)

    _clean_full_name = field_validator("fullName")(require_non_blank)
    _clean_law_firm = field_validator("lawFirm")(clean_optional)
    _check_password = field_validator("password")(validate_password_strength)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class UserPublic(BaseModel):
    id: str
    fullName: str
    email: EmailStr
    lawFirm: str | None = None
    phone: str | None = None
    baroNumber: str | None = None
    city: str | None = None
    plan: str = "free"
    emailVerified: bool = False
    hasAvatar: bool = False


class UserUpdate(BaseModel):
    fullName: str = Field(min_length=1, max_length=NAME_MAX_LENGTH)
    lawFirm: str | None = Field(default=None, max_length=NAME_MAX_LENGTH)
    phone: str | None = Field(default=None, max_length=SHORT_FIELD_MAX_LENGTH)
    baroNumber: str | None = Field(default=None, max_length=SHORT_FIELD_MAX_LENGTH)
    city: str | None = Field(default=None, max_length=SHORT_FIELD_MAX_LENGTH)

    _clean_full_name = field_validator("fullName")(require_non_blank)
    _clean_law_firm = field_validator("lawFirm")(clean_optional)
    _clean_phone = field_validator("phone")(clean_optional)
    _clean_baro_number = field_validator("baroNumber")(clean_optional)
    _clean_city = field_validator("city")(clean_optional)


class PasswordChange(BaseModel):
    currentPassword: str = Field(min_length=1, max_length=200)
    newPassword: str

    _check_new_password = field_validator("newPassword")(validate_password_strength)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1, max_length=500)
    newPassword: str

    _check_new_password = field_validator("newPassword")(validate_password_strength)


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=1, max_length=500)


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class TokenResponse(BaseModel):
    token: str
    user: UserPublic
