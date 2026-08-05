# AI Sağlayıcı Geçişi: Anthropic Claude → Google Gemini

Bu doküman, LexAssist AI'nın yapay zeka katmanının Anthropic Claude'dan Google Gemini'ye taşınmasını açıklar. Geçiş yalnızca backend'i ve AI servis katmanını etkiler — hiçbir sayfa tasarımı, endpoint yolu veya frontend davranışı değişmedi.

## Neden bu geçiş

Anthropic API'nin sürekli ücretsiz bir katmanı yok. Google Gemini ise [Google AI Studio](https://aistudio.google.com/apikey) üzerinden ücretsiz kotalı bir API anahtarı sunuyor — geliştirme ve test için kredi kartı gerektirmiyor.

## Eklenen / kaldırılan paketler

**Kaldırıldı** (`backend/requirements.txt`):
- `anthropic==0.40.0`

**Eklendi**:
- `google-genai==2.8.0` — Google'ın güncel, birleşik (unified) Gen AI SDK'sı. Eski `google-generativeai` paketi yerine bunu kullandık çünkü Google'ın şu anki resmi olarak önerdiği paket bu.

Yükleme:
```bash
docker compose build backend
```
(Bağımlılıklar `requirements.txt`'ten Docker build sırasında otomatik kurulur; yerel bir venv kullanıyorsanız `pip install -r backend/requirements.txt`.)

## Gemini API anahtarı nasıl alınır

1. [aistudio.google.com/apikey](https://aistudio.google.com/apikey) adresine gidin.
2. Google hesabınızla giriş yapın.
3. "Create API key" butonuna tıklayın.
4. Oluşturulan anahtarı kopyalayın (`AIza...` ile başlar).

Ücretsiz kota, dakika/gün başına istek sınırlarıyla gelir — production'a geçerken faturalandırmalı bir proje bağlamanız gerekebilir.

## Anahtarı nereye koymalısınız

Proje kök dizinindeki `.env` dosyasında:
```
GEMINI_API_KEY=AIza...buraya_kendi_anahtariniz...
```
`.env.example` bu değişkeni zaten örnekliyor. `ANTHROPIC_API_KEY` artık kullanılmıyor ve backend tarafından okunmuyor — dosyanızda kalmışsa silebilirsiniz, zararı olmaz.

## Uygulamayı çalıştırma

Değişiklik yok — aynı komutlar:
```bash
docker compose build backend
docker compose up -d
```
Anahtar eksikse AI uçları (`/api/ai/chat`, `/summary`, `/risks`, `/draft`) 503 ile "AI servisi yapılandırılmamış (GEMINI_API_KEY eksik)." mesajı döner; sunucu çökmez, diğer tüm özellikler (auth, davalar, yüklemeler, geçmiş, bildirimler vb.) normal çalışmaya devam eder.

## Mimari değişiklikler

- **Yeni servis katmanı**: `backend/app/services/ai/gemini_service.py` — tüm Gemini çağrıları tek bir yerden geçiyor. `chat()`, `generate_summary()`, `analyze_risks()`, `generate_draft()`, `generate_title()` fonksiyonlarını dışa açıyor. Router'lar SDK'ya doğrudan dokunmuyor; ileride başka bir sağlayıcıya geçilirse (veya model değişirse) yalnızca bu dosya değişir.
- **`backend/app/routers/ai.py`**: Endpoint yolları, request/response şemaları (`ChatRequest`, `DocumentActionRequest`, `AnalysisResponse`, `ChatResponse`) birebir aynı kaldı — frontend hiçbir değişiklik yapmadan çalışmaya devam ediyor. PDF dosyaları artık Gemini'nin `Part.from_bytes(mime_type="application/pdf")` ile native belge girişi olarak gönderiliyor (Claude'daki native PDF desteğiyle aynı yaklaşım).
- **`backend/app/core/config.py`**: `anthropic_api_key`/`anthropic_model` → `gemini_api_key`/`gemini_model` (varsayılan: `gemini-3.5-flash` — bkz. aşağıdaki "Model: neden gemini-3.5-flash" bölümü).
- **Hata yönetimi**: `AIServiceError` özel exception sınıfı — eksik anahtar (503), kota/rate limit (429), geçersiz istek (400), sunucu hatası (502), zaman aşımı (504, 90 saniye) durumlarını ayrı ayrı yakalayıp anlamlı Türkçe JSON mesajına çeviriyor. Hiçbir durumda sunucu çökmüyor.
- **Girdi doğrulama**: Sohbet sorusu artık 1-4000 karakterle sınırlı (`Field(min_length=1, max_length=4000)`); boş veya aşırı uzun istekler 422 ile reddediliyor.
- **Prompt injection önlemi**: Sistem talimatı, belge içeriğinde veya kullanıcı mesajında gömülü olabilecek "rolünü değiştir" tarzı talimatları görmezden gelmesi için modele açıkça yönlendiriyor.
- **Basit önbellek**: Aynı kullanıcı aynı dosya için özet/risk/taslak butonuna art arda basarsa, 10 dakika içinde aynı sonuç tekrar Gemini'ye sorulmadan döner (`_result_cache`, işlem-içi/in-memory — birden fazla worker veya restart arasında paylaşılmaz, tek instance için yeterli).
- **`backend/app/models/preferences.py`**: `AIPreferences.aiModel` varsayılanı `"claude"` → `"gemini"` (bu alan yalnızca Ayarlar sayfasındaki bir arayüz önizlemesi, gerçek sağlayıcı seçimini etkilemiyor).
- **`frontend/settings.html`**: Yapay Zeka sekmesindeki açıklama metni ve model seçim listesindeki varsayılan artık Gemini'yi yansıtıyor — bu, gerçekte hangi modelin çalıştığına dair yanlış bilgi vermemek için yapılan tek metin düzeltmesi; sayfa tasarımı/düzeni değişmedi.

## MongoDB

Şema değişikliği yapılmadı. AI aksiyonları hâlâ mevcut `activity` koleksiyonuna zaman damgasıyla loglanıyor (`ai_chat`, `ai_summary`, `ai_risks`, `ai_draft`), tıpkı Claude entegrasyonunda olduğu gibi. AI yanıtlarının, güven skorunun veya sohbet geçmişinin ayrıca kalıcı olarak saklanması bu geçiş için gerekli değildi ve kapsamı büyütmemek adına eklenmedi — ihtiyaç olursa ayrı bir görev olarak ele alınabilir.

## Model: neden gemini-3.5-flash

İlk geçişte varsayılan `gemini-2.5-flash` olarak ayarlanmıştı. Gerçek bir `GEMINI_API_KEY` eklenip canlı test edildiğinde, Google API'si bu modelin **yeni hesaplar için artık kullanılamadığını** döndürdü:
```
404 NOT_FOUND: This model models/gemini-2.5-flash is no longer available to new users.
```
`client.models.list()` ile hesabın erişebildiği güncel model listesi doğrudan API'den sorgulandı (tahmin edilmedi). Kullanıcıyla birlikte, Pro olmayan ve deprecated olmayan seçenekler arasından **`gemini-3.5-flash`** seçildi — `backend/app/core/config.py`'deki `gemini_model` varsayılanı bu şekilde güncellendi.

Not: Google'ın model kataloğu zamanla değişebilir. Aynı hata tekrar alınırsa (`... no longer available ...` veya `404 NOT_FOUND`), hesabınızın gerçekte erişebildiği modelleri şu şekilde sorgulayabilirsiniz:
```python
from google import genai
client = genai.Client(api_key="...")
for m in client.models.list():
    if "generateContent" in (m.supported_actions or []):
        print(m.name)
```
Ardından `GEMINI_MODEL` ortam değişkeniyle (veya `config.py`'deki varsayılanla) Pro/preview olmayan, stabil bir flash modeli seçin.

## Doğrulama

Backend yeniden derlendi ve gerçek bir `GEMINI_API_KEY` ile canlı olarak test edildi (mock/varsayım değil):
- Temiz başlangıç (import/circular-dependency hatası yok)
- `GEMINI_API_KEY` eksikken `/api/ai/chat` → 503 + anlamlı Türkçe mesaj
- Var olmayan `uploadId` → 404 (öncekiyle birebir aynı davranış)
- Boş soru → 422, 4000 karakteri aşan soru → 422
- Bozuk/geçersiz PDF → Gemini'nin gerçek 400 hatası doğru şekilde yakalanıp Türkçe mesaja çevrildi
- **Gerçek çağrılar**: `/ai/chat` (belgesiz, gerçek Gemini yanıtı, "belge yoksa uydurma" talimatına uyduğu doğrulandı), `/ai/summary`, `/ai/risks` (Düşük/Orta/Yüksek seviyelendirmesi ve gerekçesiyle), `/ai/draft` — hepsi geçerli bir PDF ile gerçek ve tutarlı Türkçe çıktı üretti
- **Önbellek doğrulandı**: Aynı dosya için `/ai/draft` ilk çağrısı ~17.6 saniye (gerçek Gemini isteği), aynı isteğin tekrarı ~0.01 saniye (önbellekten, ikinci bir API çağrısı yapılmadan)
- Tüm diğer uçlar (auth, cases, uploads, activity, notifications, billing, preferences) etkilenmeden çalışmaya devam ediyor
