from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_JWT_SECRET_DEFAULT = "dev_only_change_before_production"
MIN_JWT_SECRET_LENGTH_ANY_ENV = 16
MIN_JWT_SECRET_LENGTH_PRODUCTION = 32
_INSECURE_SECRET_MARKERS = ("dev_only", "change_this", "changeme", "insecure")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # "development" (default, permissive — used by docker-compose locally)
    # or "production" (triggers the fail-fast checks below). Deliberately
    # not validated as a strict enum so a typo here fails open to dev
    # behavior rather than accidentally disabling production hardening.
    environment: str = "development"

    jwt_secret: str = DEV_JWT_SECRET_DEFAULT
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "lexassist-ai"
    jwt_audience: str = "lexassist-ai-clients"
    access_token_expire_minutes: int = 60 * 24  # 24h — matches the "Beni Hatırla" localStorage session today

    mongo_uri: str = "mongodb://mongo:27017/lexassist"
    mongo_db_name: str = "lexassist"

    free_tier_upload_limit: int = 3
    max_upload_size_bytes: int = 25 * 1024 * 1024  # 25MB — matches frontend/js/config/env.js
    max_request_body_bytes: int = 30 * 1024 * 1024  # 30MB — general request cap, slightly above the upload limit

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash"

    cors_origins: list[str] = ["http://localhost:3000"]

    upload_storage_dir: str = "/app/storage/uploads"
    avatar_storage_dir: str = "/app/storage/avatars"
    max_avatar_size_bytes: int = 2 * 1024 * 1024  # 2MB — matches the "JPG/PNG, en fazla 2MB" UI hint

    # File storage backend for uploaded PDFs + avatars.
    #   "local"    -> disk under storage_root (VPS / local docker)
    #   "firebase" -> Firebase Storage bucket (needed on Render, whose disk
    #                 is ephemeral); requires firebase_bucket + credentials.
    storage_backend: str = "local"
    storage_root: str = "/app/storage"
    firebase_bucket: str = ""  # e.g. your-project-id.appspot.com
    firebase_credentials_json: str = ""  # raw service-account JSON (Render env var)

    # Used to build links inside password-reset / verification emails.
    frontend_base_url: str = "http://localhost:3000"
    reset_token_expire_minutes: int = 60
    verification_token_expire_hours: int = 24

    # Email delivery mode:
    #   "auto"    -> real SMTP when SMTP_HOST is set, else console dev-sender
    #   "console" -> always print emails to the backend log (development)
    #   "smtp"    -> always send over SMTP (fails loudly if misconfigured)
    email_mode: str = "auto"

    # SMTP transport. Gmail: host=smtp.gmail.com, port=587, use_tls=True
    # (STARTTLS) with an *App Password* (not your normal Google password).
    # For implicit SSL use port=465 with use_ssl=True instead.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "no-reply@lexassist.ai"
    smtp_from_name: str = "LexAssist AI"
    smtp_use_tls: bool = True  # STARTTLS on port 587
    smtp_use_ssl: bool = False  # implicit SSL on port 465 (mutually exclusive with STARTTLS)
    smtp_timeout_seconds: int = 15

    @property
    def is_production(self) -> bool:
        return self.environment.strip().lower() == "production"

    @property
    def use_smtp_email(self) -> bool:
        """Whether real SMTP sending is active (vs the console dev-sender)."""
        mode = self.email_mode.strip().lower()
        if mode == "smtp":
            return True
        if mode == "console":
            return False
        return bool(self.smtp_host)  # "auto"

    @field_validator("jwt_algorithm")
    @classmethod
    def _validate_jwt_algorithm(cls, v: str) -> str:
        # Only symmetric HMAC algorithms are supported by this codebase's
        # single-shared-secret setup. Rejecting "none" and asymmetric
        # algorithms here closes off the classic JWT "alg confusion" class
        # of vulnerabilities at the config layer, before a token is ever
        # decoded.
        allowed = {"HS256", "HS384", "HS512"}
        if v not in allowed:
            raise ValueError(f"jwt_algorithm 'none' veya desteklenmeyen bir değer olamaz. İzin verilenler: {sorted(allowed)}")
        return v

    @field_validator("jwt_secret")
    @classmethod
    def _validate_jwt_secret_length(cls, v: str) -> str:
        # A floor that applies in every environment, not just production —
        # catches trivially weak secrets ("secret", "123456") immediately
        # rather than only once someone remembers to set ENVIRONMENT=production.
        if len(v) < MIN_JWT_SECRET_LENGTH_ANY_ENV:
            raise ValueError(f"JWT_SECRET en az {MIN_JWT_SECRET_LENGTH_ANY_ENV} karakter olmalıdır.")
        return v

    @model_validator(mode="after")
    def _validate_production_configuration(self) -> "Settings":
        if not self.is_production:
            return self

        problems: list[str] = []

        if self.jwt_secret == DEV_JWT_SECRET_DEFAULT:
            problems.append("JWT_SECRET hâlâ geliştirme varsayılanı — gerçek, rastgele bir değer atayın.")
        if len(self.jwt_secret) < MIN_JWT_SECRET_LENGTH_PRODUCTION:
            problems.append(f"JWT_SECRET production'da en az {MIN_JWT_SECRET_LENGTH_PRODUCTION} karakter olmalıdır.")
        if any(marker in self.jwt_secret.lower() for marker in _INSECURE_SECRET_MARKERS):
            problems.append("JWT_SECRET bir yer tutucu (placeholder) gibi görünüyor — gerçek bir sır ile değiştirin.")

        if any(marker in self.mongo_uri.lower() for marker in _INSECURE_SECRET_MARKERS):
            problems.append("MONGO_URI bir geliştirme/yer tutucu parolası içeriyor gibi görünüyor.")

        if "*" in self.cors_origins:
            problems.append("CORS_ORIGINS production'da '*' (her origin) içeremez.")
        if not self.cors_origins:
            problems.append("CORS_ORIGINS production'da boş olamaz.")

        if not self.frontend_base_url.startswith("https://"):
            problems.append("FRONTEND_BASE_URL production'da https:// ile başlamalıdır.")

        # Firebase storage, when selected, needs its bucket + credentials.
        if self.storage_backend.strip().lower() == "firebase":
            if not self.firebase_bucket:
                problems.append("STORAGE_BACKEND=firebase ancak FIREBASE_BUCKET boş.")
            if not self.firebase_credentials_json:
                problems.append("STORAGE_BACKEND=firebase ancak FIREBASE_CREDENTIALS_JSON boş.")

        # Reset/verification links are useless if they only print to the
        # server console, so real SMTP delivery is mandatory in production.
        if not self.use_smtp_email:
            problems.append(
                "Production'da e-posta gönderimi SMTP ile yapılandırılmalıdır "
                "(EMAIL_MODE 'console' olamaz ve SMTP_HOST boş bırakılamaz)."
            )
        elif not self.smtp_host:
            problems.append("EMAIL_MODE=smtp ayarlandı ancak SMTP_HOST boş.")

        if problems:
            raise ValueError(
                "Güvensiz yapılandırmayla production'da başlatma reddedildi:\n- " + "\n- ".join(problems)
            )
        return self


settings = Settings()
