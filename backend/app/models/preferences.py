from typing import Literal

from pydantic import BaseModel


class NotificationPreferences(BaseModel):
    notifyMaster: bool = True
    notifyAnalysis: bool = True
    notifyUpload: bool = True
    notifySystem: bool = True
    notifyPromo: bool = False
    notifyWeekly: bool = True


class AIPreferences(BaseModel):
    aiModel: Literal["claude", "gpt", "gemini", "deepseek"] = "gemini"
    responseLengthGroup: Literal["kisa", "normal", "detayli"] = "kisa"
    autoSummary: bool = True
    autoRisk: bool = False
    autoDraft: bool = False


class AppearancePreferences(BaseModel):
    themeGroup: Literal["acik", "koyu", "sistem"] = "acik"
    sidebarWidthGroup: Literal["kompakt", "rahat"] = "kompakt"
    densityGroup: Literal["rahat", "sikisik"] = "rahat"
    animations: bool = True


class PdfPreferences(BaseModel):
    pdfFolder: Literal["", "is-hukuku", "ceza-hukuku", "aile-hukuku", "ticaret-hukuku", "icra-dosyalari"] = ""
    autoAnalyzeOnUpload: bool = True
    autoOcr: bool = False
    keepOriginal: bool = True


class UserPreferences(BaseModel):
    notifications: NotificationPreferences = NotificationPreferences()
    ai: AIPreferences = AIPreferences()
    appearance: AppearancePreferences = AppearancePreferences()
    pdf: PdfPreferences = PdfPreferences()


class UserPreferencesUpdate(BaseModel):
    notifications: dict[str, bool] | None = None
    ai: dict[str, str | bool] | None = None
    appearance: dict[str, str | bool] | None = None
    pdf: dict[str, str | bool] | None = None
