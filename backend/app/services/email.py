import asyncio
import logging
import smtplib
import ssl
from abc import ABC, abstractmethod
from email.message import EmailMessage
from email.utils import formataddr

from app.core.config import settings

logger = logging.getLogger("lexassist.email")
logger.setLevel(logging.INFO)
if not logger.handlers:
    # Own handler so dev-mode emails print regardless of the root/uvicorn
    # logging config (which defaults to WARNING for application loggers).
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(_handler)
    logger.propagate = False


# ======================================================================
# Transport
# ======================================================================
class EmailSender(ABC):
    @abstractmethod
    async def send(self, to: str, subject: str, html_body: str, text_body: str) -> bool:
        """Returns True on success. Implementations must NOT raise on a
        delivery failure — a failed transactional email must not turn into
        a 500 (and, for forgot-password, must not become an account-
        enumeration signal by failing only for real users)."""


class ConsoleEmailSender(EmailSender):
    """Development sender — prints the email (including the reset/verify
    link) to the backend log so the auth flows are fully testable without a
    real SMTP account."""

    async def send(self, to: str, subject: str, html_body: str, text_body: str) -> bool:
        banner = "=" * 70
        logger.info(
            "\n%s\n[DEV EMAIL] To: %s\nSubject: %s\n%s\n%s\n%s",
            banner, to, subject, "-" * 70, text_body, banner,
        )
        return True


class SmtpEmailSender(EmailSender):
    """Production sender over SMTP. Supports both STARTTLS (port 587, the
    Gmail default) and implicit SSL (port 465). Runs the blocking smtplib
    call in a thread so it never blocks the async event loop."""

    async def send(self, to: str, subject: str, html_body: str, text_body: str) -> bool:
        message = EmailMessage()
        message["From"] = formataddr((settings.smtp_from_name, settings.smtp_from))
        message["To"] = to
        message["Subject"] = subject
        message.set_content(text_body)  # plain-text fallback part
        message.add_alternative(html_body, subtype="html")  # preferred HTML part

        def _send_sync() -> None:
            context = ssl.create_default_context()
            timeout = settings.smtp_timeout_seconds
            if settings.smtp_use_ssl:
                with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=timeout, context=context) as server:
                    if settings.smtp_user:
                        server.login(settings.smtp_user, settings.smtp_password)
                    server.send_message(message)
            else:
                with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=timeout) as server:
                    server.ehlo()
                    if settings.smtp_use_tls:
                        server.starttls(context=context)
                        server.ehlo()
                    if settings.smtp_user:
                        server.login(settings.smtp_user, settings.smtp_password)
                    server.send_message(message)

        try:
            await asyncio.to_thread(_send_sync)
            logger.info("E-posta gönderildi (%s) -> %s", subject, to)
            return True
        except Exception:
            # Log server-side, swallow client-side. See EmailSender.send docstring.
            logger.exception("SMTP e-posta gönderimi başarısız (%s) -> %s", subject, to)
            return False


def get_email_sender() -> EmailSender:
    return SmtpEmailSender() if settings.use_smtp_email else ConsoleEmailSender()


# ======================================================================
# Branded HTML templates (email-client safe: table layout, inline CSS)
# ======================================================================
_BRAND_NAVY = "#0f172a"
_BRAND_NAVY_LIGHT = "#1e3a8a"
_BRAND_GOLD = "#d4af37"
_TEXT = "#334155"
_MUTED = "#94a3b8"
_BORDER = "#e2e8f0"


def _email_layout(*, heading: str, intro: str, button_label: str, button_url: str, footer_note: str) -> str:
    """Wraps per-email content in the shared LexAssist AI branded shell.

    Everything is table-based with inline styles because most email
    clients (Gmail, Outlook) strip <style> blocks and ignore flexbox/grid.
    """
    return f"""\
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<meta name="color-scheme" content="light" />
</head>
<body style="margin:0;padding:0;background-color:#f1f5f9;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f1f5f9;padding:32px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:520px;background-color:#ffffff;border:1px solid {_BORDER};border-radius:16px;overflow:hidden;">
          <!-- Header -->
          <tr>
            <td style="background-color:{_BRAND_NAVY};padding:24px 32px;">
              <table role="presentation" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="vertical-align:middle;">
                    <span style="display:inline-block;width:36px;height:36px;background-color:{_BRAND_GOLD};border-radius:9px;color:{_BRAND_NAVY};font-family:Arial,Helvetica,sans-serif;font-weight:bold;font-size:20px;line-height:36px;text-align:center;">L</span>
                  </td>
                  <td style="vertical-align:middle;padding-left:12px;">
                    <span style="font-family:Arial,Helvetica,sans-serif;font-size:18px;font-weight:600;color:#ffffff;">LexAssist <span style="color:{_BRAND_GOLD};">AI</span></span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <!-- Body -->
          <tr>
            <td style="padding:32px;font-family:Arial,Helvetica,sans-serif;color:{_TEXT};">
              <h1 style="margin:0 0 12px 0;font-size:20px;font-weight:700;color:{_BRAND_NAVY};">{heading}</h1>
              <p style="margin:0 0 24px 0;font-size:14px;line-height:22px;color:{_TEXT};">{intro}</p>
              <table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 auto;">
                <tr>
                  <td align="center" style="border-radius:10px;background-color:{_BRAND_NAVY};">
                    <a href="{button_url}" target="_blank"
                       style="display:inline-block;padding:13px 30px;font-family:Arial,Helvetica,sans-serif;font-size:14px;font-weight:600;color:{_BRAND_GOLD};text-decoration:none;border-radius:10px;">
                      {button_label}
                    </a>
                  </td>
                </tr>
              </table>
              <p style="margin:24px 0 6px 0;font-size:12px;color:{_MUTED};">Buton çalışmazsa aşağıdaki bağlantıyı tarayıcınıza yapıştırın:</p>
              <p style="margin:0;font-size:12px;word-break:break-all;"><a href="{button_url}" target="_blank" style="color:{_BRAND_NAVY_LIGHT};">{button_url}</a></p>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="padding:20px 32px 28px 32px;border-top:1px solid {_BORDER};font-family:Arial,Helvetica,sans-serif;">
              <p style="margin:0 0 6px 0;font-size:12px;line-height:18px;color:{_MUTED};">{footer_note}</p>
              <p style="margin:0;font-size:11px;color:{_MUTED};">© 2026 LexAssist AI · Türkiye'nin hukuk büroları için geliştirildi.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


async def send_password_reset_email(to: str, reset_url: str) -> bool:
    minutes = settings.reset_token_expire_minutes
    subject = "LexAssist AI — Şifre Sıfırlama"
    text_body = (
        "Şifre Sıfırlama\n\n"
        f"Hesabınızın şifresini sıfırlamak için aşağıdaki bağlantıya tıklayın. "
        f"Bağlantı {minutes} dakika boyunca geçerlidir.\n\n"
        f"{reset_url}\n\n"
        "Bu isteği siz yapmadıysanız bu e-postayı yok sayabilirsiniz; şifreniz değişmez."
    )
    html_body = _email_layout(
        heading="Şifre Sıfırlama",
        intro=(
            f"Hesabınızın şifresini sıfırlamak için aşağıdaki butona tıklayın. "
            f"Bu bağlantı <strong>{minutes} dakika</strong> boyunca geçerlidir."
        ),
        button_label="Şifremi Sıfırla",
        button_url=reset_url,
        footer_note="Bu isteği siz yapmadıysanız bu e-postayı yok sayabilirsiniz — hesabınızın şifresi değişmez.",
    )
    return await get_email_sender().send(to, subject, html_body, text_body)


async def send_verification_email(to: str, verify_url: str) -> bool:
    hours = settings.verification_token_expire_hours
    subject = "LexAssist AI — E-posta Doğrulama"
    text_body = (
        "E-posta Adresinizi Doğrulayın\n\n"
        "LexAssist AI'a hoş geldiniz. E-posta adresinizi doğrulamak için aşağıdaki bağlantıya tıklayın. "
        f"Bağlantı {hours} saat boyunca geçerlidir.\n\n"
        f"{verify_url}\n\n"
        "Bu hesabı siz oluşturmadıysanız bu e-postayı yok sayabilirsiniz."
    )
    html_body = _email_layout(
        heading="E-posta Adresinizi Doğrulayın",
        intro=(
            "LexAssist AI'a hoş geldiniz. Hesabınızı güvence altına almak için "
            f"e-posta adresinizi doğrulayın. Bu bağlantı <strong>{hours} saat</strong> boyunca geçerlidir."
        ),
        button_label="E-postamı Doğrula",
        button_url=verify_url,
        footer_note="Bu hesabı siz oluşturmadıysanız bu e-postayı yok sayabilirsiniz.",
    )
    return await get_email_sender().send(to, subject, html_body, text_body)
