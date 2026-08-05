import re

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

# Not exhaustive by design — a full breach-corpus check (e.g. HaveIBeenPwned's
# k-anonymity API) is the real long-term answer; this is a cheap first line
# of defense against the most common throwaway passwords, in Turkish and
# English, so it lives entirely offline with zero external dependencies.
_COMMON_PASSWORDS = {
    "password", "password1", "password123", "12345678", "123456789",
    "qwerty123", "letmein11", "iloveyou1", "admin1234", "welcome123",
    "sifre1234", "sifre123456", "parola123", "parola1234", "istanbul1",
    "turkiye123", "12345678910",
}


def validate_password_strength(password: str) -> str:
    """Raises ValueError with a Turkish, user-facing message on failure;
    returns the password unchanged on success (Pydantic field_validator
    convention)."""
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Şifre en az {MIN_PASSWORD_LENGTH} karakter olmalıdır.")
    if len(password) > MAX_PASSWORD_LENGTH:
        raise ValueError(f"Şifre en fazla {MAX_PASSWORD_LENGTH} karakter olabilir.")
    if not re.search(r"[a-z]", password):
        raise ValueError("Şifre en az bir küçük harf içermelidir.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Şifre en az bir büyük harf içermelidir.")
    if not re.search(r"[0-9]", password):
        raise ValueError("Şifre en az bir rakam içermelidir.")
    if not re.search(r"[^A-Za-z0-9]", password):
        raise ValueError("Şifre en az bir özel karakter içermelidir (örn. ! ? # @ %).")
    if password.lower() in _COMMON_PASSWORDS:
        raise ValueError("Bu şifre çok yaygın kullanılıyor. Lütfen daha güvenli bir şifre seçin.")
    return password
