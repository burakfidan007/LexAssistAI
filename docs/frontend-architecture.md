# LexAssist AI — Frontend Architecture & Backend Integration Plan

**Amaç:** Mevcut 4 ekranın (login, my-cases, upload, dashboard) görsel tasarımını **değiştirmeden**, gerçek bir REST API + JWT + MongoDB + Docker backend'ine bağlanabilecek, kurumsal ölçekte sürdürülebilir bir frontend mimarisine geçiş planı. Kod üretimi değil, mimari kararlar ve gerekçeleridir.

**Mevcut durumun dürüst tespiti (bu plan buradan başlıyor):** Bugün 4 sayfanın her biri (`login.html`, `my-cases.html`, `upload.html`, `index.html`) tamamen kendi kendine yeten, sıfır paylaşılan modül içeren tek dosyalar. Her dosyada ayrı ayrı tanımlanmış aynı `API_BASE_URL` sabiti, aynı toast/modal sistemi, aynı sidebar markup'ı var. Bu, prompt-bazlı üretim aşaması için doğru bir seçimdi — ama gerçek backend entegrasyonu ve "enterprise" sürdürülebilirlik için artık bir mimari katman gerekiyor.

---

## 0. Temel Mimari Karar: Build Adımı Olmadan Modülerlik

Proje "framework yok, saf HTML5 + Tailwind CDN + Vanilla JS" kısıtını koruyor — bu doğru bir kısıt, değiştirilmiyor. Ama "framework yok" ile "hiç modül yok" aynı şey değil.

**Öneri:** Native ES Modules (`<script type="module">`). Modern tarayıcılar `import`/`export`'u derleme aracı olmadan destekler. Bu, Tailwind CDN'i koruyarak, npm/webpack/vite eklemeden, `api/`, `state/`, `utils/` gibi gerçekten paylaşılan dosyalar yazmamızı sağlar.

```html
<!-- her sayfanın en altında -->
<script type="module" src="js/pages/myCases.page.js"></script>
```

Bu tek karar, aşağıdaki tüm bölümlerin önkoşulu.

---

## 1. Klasör Yapısı

```
frontend/
├── login.html
├── my-cases.html
├── upload.html
├── index.html
├── css/
│   └── theme.css              # 4 dosyada tekrar eden <style> bloğu (navy/gold tema, keyframe'ler) buraya taşınır
├── assets/
│   └── favicon.svg            # şu an inline data-URI olan favicon dosyaya alınır
└── js/
    ├── config/
    │   └── env.js              # API_BASE_URL, FREE_TIER_LIMIT, MAX_FILE_SIZE — tek kaynak
    ├── api/                    # Sunucuyla konuşan TEK katman. DOM'a dokunmaz, sadece Promise döner.
    │   ├── http.js              # fetch wrapper: Authorization header, hata normalizasyonu, 401 yakalama
    │   ├── auth.js               # login, register, refreshToken, logout, me()
    │   ├── cases.js               # CRUD + arama/sıralama/sayfalama
    │   ├── folders.js              # CRUD + istatistik
    │   ├── upload.js                # dosya yükleme, ilerleme, geçmiş
    │   ├── chat.js                    # mesaj gönderme, konuşma geçmişi, streaming
    │   ├── analysis.js                 # özet, risk, taslak, güven skoru
    │   └── user.js                      # profil, abonelik, kullanım limitleri
    ├── state/
    │   └── store.js              # küçük pub-sub store (bkz. Bölüm 4)
    ├── services/
    │   ├── session.js             # token yaşam döngüsü, guardPage(), otomatik çıkış
    │   └── notifications.js        # toast sistemi (şu an 3 dosyada ayrı ayrı tanımlı)
    ├── components/                 # Sayfalar arası paylaşılan, yeniden kullanılabilir UI parçaları
    │   ├── sidebar.js
    │   ├── topbar.js
    │   ├── commandPalette.js
    │   ├── modal.js                # openModal/closeModal/focus-trap (my-cases.html'de zaten var, jenerikleştirilir)
    │   └── toast.js
    ├── pages/                       # Sayfaya özel orkestrasyon — sadece "hangi API çağrılır, hangi component render edilir"
    │   ├── login.page.js
    │   ├── myCases.page.js
    │   ├── upload.page.js
    │   └── dashboard.page.js
    └── utils/
        ├── format.js              # formatFileSize, formatTime, formatCurrency
        ├── validate.js             # e-posta/şifre kuralları (login.html'de inline olan mantık)
        ├── sanitize.js              # kullanıcı girdisini innerHTML'e koymadan önce escape eder (bkz. Bölüm 5)
        └── dom.js                    # küçük yardımcılar (qs, qsa, createElement)
```

**Katman kuralı:** `api/` ve `state/` hiçbir zaman `document.querySelector` çağırmaz. `components/` ve `pages/` hiçbir zaman doğrudan `fetch` çağırmaz. Bu ayrım, Bölüm 9'daki (Ölçeklenebilirlik) React/Vue geçişinin maliyetini düşüren asıl karardır.

---

## 2. API Katmanı

Her modülün tek sorumluluğu var; hepsi `http.js` üzerinden geçer.

| Dosya | Sorumluluk | Örnek fonksiyonlar |
|---|---|---|
| `http.js` | Tüm isteklerin geçtiği tek nokta: `Authorization: Bearer <token>` ekler, JSON parse eder, hata şeklini normalize eder (`ApiError`), 401'de `session.js`'e haber verir | `request(path, options)` |
| `auth.js` | Kimlik doğrulama uç noktaları | `login()`, `register()`, `refreshToken()`, `logout()`, `me()` |
| `cases.js` | Dava CRUD + liste sorguları | `listCases({ search, status, folder, sort, page })`, `getCase(id)`, `createCase()`, `updateCase()`, `deleteCase()`, `moveCase(id, folderId)` |
| `folders.js` | Klasör CRUD + istatistik | `listFolders()`, `createFolder()`, `renameFolder()`, `deleteFolder()`, `getFolderStats(id)` |
| `upload.js` | PDF yükleme + geçmiş | `uploadFile(file, { onProgress })`, `listHistory()`, `retryUpload(id)`, `deleteHistoryItem(id)` |
| `chat.js` | AI sohbet | `sendMessage(caseId, text)`, `getConversation(caseId)`, `streamMessage(caseId, text, onToken)` |
| `analysis.js` | AI analiz aksiyonları | `generateSummary(caseId)`, `analyzeRisks(caseId)`, `generateDraft(caseId)`, `getConfidence(caseId)`, `getRecentActions(caseId)` |
| `user.js` | Profil ve abonelik | `getProfile()`, `updateProfile()`, `getSubscription()`, `getStorageUsage()`, `getUsageLimits()` |

`http.js` bugünkü `apiRequest()`/inline `fetch()` kalıbının (4 dosyada ayrı ayrı yazılmış hâli) tekilleştirilmiş, jenerik versiyonu:

```js
// api/http.js — kavramsal iskelet, tam kod değil
export async function request(path, { method = 'GET', body, auth = true } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (auth) headers.Authorization = `Bearer ${session.getAccessToken()}`;

  const res = await fetch(`${env.API_BASE_URL}${path}`, { method, headers, body });

  if (res.status === 401) {
    const refreshed = await session.tryRefresh();
    if (refreshed) return request(path, { method, body, auth });
    session.logout();
    throw new ApiError('UNAUTHORIZED', 401);
  }
  if (!res.ok) throw await ApiError.fromResponse(res);
  return res.json();
}
```

Sayfa kodu (`pages/myCases.page.js`) artık şöyle görünür — `fetch` yok, sadece veri + render:

```js
import { listCases } from '../api/cases.js';
const cases = await listCases({ status: state.get('statusFilter') });
renderCaseGrid(cases);
```

---

## 3. Kimlik Doğrulama Akışı

Mevcut kodda zaten doğru yönde atılmış adımlar var — bunlar korunuyor, genelleştiriliyor:

- **Register / Login:** `POST /api/auth/register`, `POST /api/auth/login` → `{ accessToken, refreshToken, user }`. `login.html`'deki demo-mode fallback (backend'e ulaşılamazsa `TypeError` yakalanıp demo token'la devam edilmesi) **geliştirme/demo modunda korunur**, `env.js`'deki `MOCK_AUTH_ON_NETWORK_ERROR` bayrağıyla üretimde kapatılabilir hale getirilir.
- **JWT saklama stratejisi:** İki aşamalı öneri —
  - **Bugün (prototip):** `localStorage`'da tek bir access token (`lexassist_token`) — zaten uygulanmış durumda, basit ve demo için yeterli.
  - **Üretim sertleştirmesi:** Access token kısa ömürlü (15 dk) ve `localStorage`'da kalabilir; refresh token backend tarafından `httpOnly`, `Secure`, `SameSite=Strict` cookie olarak set edilir — JavaScript'in refresh token'a hiç erişememesi XSS'e karşı asıl korumadır.
- **Token süresi dolumu:** JWT payload'ı (imza doğrulanmadan) decode edilip `exp` okunur; süresine 60 saniye kalınca arka planda sessizce `refreshToken()` çağrılır — kullanıcı hiç fark etmez.
- **Otomatik çıkış:** `refreshToken()` başarısız olursa veya `http.js` bir isteğe 401 alıp refresh de başarısız olursa → `session.logout()` → state temizlenir → `login.html`'e yönlendirilir.
- **Authorization header:** `http.js` içinde merkezi olarak eklenir; hiçbir sayfa kodu bunu elle yazmaz (bugün her `fetch` çağrısında elle yazılıyor).
- **Korumalı rotalar:** Router olmadığı için "route guard" kavramı = her korumalı sayfanın en üstünde `session.guardPage()` çağrısı. Bu zaten `my-cases.html`/`upload.html`/`index.html`'e eklendi (`requireAuth()` deseni); `session.js`'e taşınıp tekilleştirilir.
- **Oturum doğrulama:** Bugün yalnızca token'ın *varlığı* kontrol ediliyor, *geçerliliği* değil. Öneri: sayfa yüklenirken `GET /api/auth/me` çağrılır; 401 dönerse token var ama geçersiz demektir → çıkış yapılır. Bu, "token localStorage'da duruyor ama backend'de zaten geçersiz" durumunu yakalar.
- **Beni Hatırla:** Şu an işlevsiz bir checkbox. Öneri: işaretliyse token `localStorage`'a (tarayıcı kapansa da kalıcı), işaretli değilse `sessionStorage`'a (sekme kapanınca silinir) yazılır. `session.js` iki storage'ı da soyutlayan tek bir `getToken()/setToken()` API'si sunar, çağıran kod hangisini kullandığını bilmek zorunda kalmaz.

---

## 4. State Yönetimi (React'sız)

Bugün her sayfa kendi `let CASES = [...]`, `let state = {...}`, `let draftUsed = false` gibi sayfa-local değişkenlerini tutuyor — sayfa yenilenince ya da başka sayfaya geçilince kayboluyor (upload sayacı, seçili filtre gibi). Önerilen çözüm, Redux değil, ~30 satırlık bir pub-sub store:

```js
// state/store.js — kavramsal
const state = {
  currentUser: null,
  currentFolder: null,
  selectedCase: null,
  selectedPdf: null,
  chatHistory: [],
  notifications: [],
  theme: 'light',
  premiumStatus: 'free',
};
const listeners = new Set();

export const store = {
  get: (key) => state[key],
  set(patch) {
    Object.assign(state, patch);
    listeners.forEach((fn) => fn(state));
  },
  subscribe: (fn) => (listeners.add(fn), () => listeners.delete(fn)),
};
```

Bu, üç şeyi çözer:
1. **Sayfalar arası tutarlılık:** `currentUser` bir kez `auth.js` tarafından set edilir, sidebar/topbar/profil menüsü hepsi aynı kaynaktan okur (bugün her sayfa "Av. Ayşe Yılmaz" metnini kendi HTML'ine hardcode etmiş durumda).
2. **`localStorage` ile karışıklığı önler:** `localStorage` yalnızca *sayfalar arası kalıcılık gereken* şeyler için (token, son görüntülenen davalar) — geri kalan her şey bellek-içi `store`'da.
3. **Component'lerin store'a abone olması:** Örn. `sidebar.js` kullanıcı adı değiştiğinde otomatik yeniden render olur, sayfa kodu bunu elle tetiklemez.

---

## 5. Güvenlik

**Kod üzerinde doğrulanmış gerçek bir bulgu:** `my-cases.html` ve `upload.html`'de dava başlığı (`c.title`) ve dosya adı (`item.fileName`) — ikisi de kullanıcı girdisi — doğrudan `innerHTML` template string'lerine ekleniyor, escape edilmeden:

```js
// my-cases.html — bugünkü hâli
`<p class="text-sm font-semibold text-navy truncate">${c.title}</p>`
```

Demo verisiyle risk yok, ama gerçek backend'e bağlanınca bir kullanıcı dava adını `<img src=x onerror=alert(document.cookie)>` yaparsa bu **çalışan bir XSS**'tir. **Zorunlu düzeltme:** `utils/sanitize.js` içinde bir `escapeHtml()` fonksiyonu, tüm kullanıcı-kaynaklı string'lerin `innerHTML`'e girmeden önce buradan geçmesi, ya da mümkün olan yerlerde `textContent` kullanımına dönülmesi (login.html'in kendi form hata mesajlarında zaten doğru yapılıyor — `textContent` kullanılıyor, tutarlılık sağlanmalı).

Diğer güvenlik kararları:

- **CSRF:** JWT bearer-token modeli (Authorization header, cookie değil) kullanıldığı sürece CSRF riski düşük — CSRF esasen "tarayıcı cookie'yi otomatik gönderir" senaryosunda oluşur. Refresh token için `httpOnly` cookie'ye geçilirse (Bölüm 3), backend `SameSite=Strict` + CSRF token deseni eklemeli.
- **Girdi sanitizasyonu:** Sadece render değil, form gönderiminde de (dava adı, klasör adı, sohbet mesajı) whitespace-trim + uzunluk sınırı frontend'de, **gerçek doğrulama her zaman backend'de** — frontend doğrulaması yalnızca UX içindir, güvenlik sınırı değildir.
- **Güvenli localStorage stratejisi:** Token dışında hassas veri (şifre, tam kimlik bilgisi) asla localStorage'a yazılmaz. Bugün `lexassist_user`'a yalnızca ad/e-posta yazılıyor — bu kabul edilebilir, ama backend entegrasyonunda buraya asla token dışı hassas alan eklenmemeli.
- **Çıkış stratejisi:** `session.logout()` yalnızca `localStorage` temizlemekle kalmaz, backend'e `POST /api/auth/logout` çağırıp refresh token'ı sunucu tarafında da geçersiz kılmalı (bugün sadece client-side temizlik yapılıyor).

---

## 6. Hata Yönetimi

`http.js` tüm hataları tek bir `ApiError { code, status, message, fields? }` şekline normalize eder; UI katmanı sadece bu şekli bilir, ham `fetch` hatalarını hiç görmez.

| Durum | Kaynak | UI Davranışı |
|---|---|---|
| 401 Unauthorized | Token yok/süresi dolmuş | Sessiz refresh dene → başarısızsa `session.logout()` + login'e yönlendir |
| 403 Forbidden | Yetki yok (örn. free tier limit backend'de de kontrol ediliyor) | Toast: "Bu işlem için yetkiniz yok." — upload.html'deki free-tier UI kalıbıyla aynı dil |
| 422 Validation | Form hatası | Alan bazlı hata (`fields: { email: "..." }`) → `login.html`'deki `setFieldError()` deseni her formda tekrar kullanılır |
| Network / Timeout | Backend ayakta değil | `err instanceof TypeError` yakalanır (bugün `login.html`'de zaten bu desen var) → demo-mode fallback veya "Bağlantı kurulamadı, tekrar deneyin" banner'ı |
| Upload hatası | Dosya reddedildi / bağlantı koptu | `upload.html`'de zaten var olan "Başarısız" durum + "Tekrar Dene" butonu deseni |
| AI hatası | LLM servisi yanıt vermedi | `index.html`'de zaten var olan canned-response fallback deseni korunur, ama artık gerçek hata olduğu ayrıca loglanır (sessizce yutulmaz) |
| 500 Server Error | Backend çöktü | Genel toast + "Destek ile iletişime geçin" linki |

**Kural:** Her hata kategorisi zaten var olan bir UI bileşenine (toast, inline form hatası, "tekrar dene" butonu) eşlenir — yeni bir hata UI dili icat edilmiyor, mevcut olan yeniden kullanılıyor.

---

## 7. Backend Entegrasyon Stratejisi

1. **Ortam konfigürasyonu:** `js/config/env.js` tek bir `API_BASE_URL` export eder. Docker Compose'da nginx üzerinden `envsubst` ile derleme-zamanı olmadan ortam değiştirmek mümkün (`docker-compose.yml`'de zaten `backend` servisi taslağı var).
2. **Mock'tan gerçeğe kademeli geçiş:** Bugün her sayfa "gerçek `fetch` dene, başarısız olursa demo veriyle devam et" deseninde. Bu desen **kaldırılmaz**, tersine çevrilir: `env.js`'de `USE_MOCK_DATA = true/false` bayrağı ile kontrol edilir. Backend endpoint'leri tek tek hazır oldukça (`/api/auth` → `/api/cases` → `/api/folders` → `/api/uploads` → `/api/ai/*`), ilgili `api/*.js` modülü gerçek çağrıya geçer, diğerleri mock kalmaya devam eder — sayfa kodunda hiçbir değişiklik gerekmez.
3. **CORS:** Backend, frontend'in origin'ini (geliştirmede `http://localhost:3000`, üretimde gerçek domain) `Access-Control-Allow-Origin`'e eklemeli; `Authorization` header'ı `Access-Control-Allow-Headers`'da olmalı.
4. **Uç nokta sözleşmesi:** Her `api/*.js` modülü, backend ekibiyle paylaşılabilecek bir sözleşme dosyası gibi davranır — fonksiyon imzaları zaten beklenen request/response şeklini tanımlıyor (Bölüm 2'deki tablo).
5. **Entegrasyon test sırası (önerilen):** auth → user (profil/limitler, çünkü sidebar'daki her şey buna bağlı) → folders → cases → upload → analysis → chat (en karmaşık, streaming gerektirebilir).

---

## 8. Performans

- **Debounce:** `my-cases.html`'deki arama input'u her tuş vuruşunda tüm listeyi yeniden render ediyor; 200-300ms debounce eklenmeli (özellikle arama backend'e gidince, her tuş vuruşunda istek atılmaması için kritik).
- **API retry:** Ağ hatalarında (5xx, timeout) `http.js` içinde üstel geri çekilmeli (exponential backoff) otomatik retry (maks. 2 deneme) — kullanıcı aksiyonlarında değil, yalnızca GET/idempotent isteklerde.
- **İstek kuyruğu:** Sohbet gibi sıralı önemli olan akışlarda (kullanıcı hızlıca birden fazla mesaj gönderirse) basit bir FIFO kuyruk, isteklerin yanıt sırasının karışmasını önler.
- **Lazy loading:** `commandPalette.js`, `modal.js` gibi yalnızca kullanıcı etkileşimiyle açılan component'ler dinamik `import()` ile ilk kullanımda yüklenebilir — ES modules bunu build aracı olmadan da destekler.
- **Lucide `createIcons()` kapsamı:** Bölüm 2'deki `design-review.md`'de belirtildiği gibi, her render'da tüm dokümanı taramak yerine yalnızca değişen alt ağaca (`lucide.createIcons({ nodes: [container] })`) scope edilmeli.
- **Caching:** `folders.js`/`user.js` gibi sık değişmeyen veriler için basit bir bellek-içi TTL cache (`store` üzerinde `lastFetchedAt` alanı) — her sayfa geçişinde aynı klasör listesini tekrar çekmek gereksiz.

---

## 9. Ölçeklenebilirlik — React/Vue/Angular'a Geçiş

Bölüm 1'deki katman ayrımı (`api/` ve `state/` DOM'a dokunmaz) bu geçişin maliyetini önceden düşürüyor:

| Katman | Framework geçişinde ne olur? |
|---|---|
| `api/*.js`, `state/store.js`, `utils/*.js` | **Neredeyse değişmeden taşınır.** Bunlar zaten saf JS/Promise/state — React'te bir hook'un içinden, Vue'da bir composable'ın içinden aynen çağrılabilir. |
| `components/*.js` | Yeniden yazılır, ama her component'in *ne yaptığı* (props, state, olaylar) zaten net tanımlı olduğu için 1:1 çeviri kolaydır. |
| `pages/*.js` | Framework'ün route/component sistemine göre yeniden yazılır — bu, en çok değişecek katman. |
| `*.html` + Tailwind class'ları | Tailwind zaten framework-agnostik; JSX/Vue template'e class isimleri neredeyse aynen taşınır. |

**Önerilen strateji (strangler pattern):** Tüm uygulamayı bir günde React'e taşımaya çalışmak yerine, en küçük yüzeyli sayfadan (`login.html`) başlanır; `api/auth.js` aynen kullanılır, yalnızca `login.page.js` bir React component'ine dönüşür. Diğer 3 sayfa vanilla kalmaya devam edebilir — ikisi aynı `api/` ve `state/` katmanını paylaştığı için birlikte çalışabilirler.

---

## 10. Uygulama Sırası (Özet)

Bu doküman bir tasarım değil, bir plandır — kod değişikliği içermez. Uygulamaya geçilecekse önerilen sıra:

1. `config/env.js` + `api/http.js` — tek merkezi fetch katmanı (4 dosyadaki tekrar eden `API_BASE_URL`'i birleştirir)
2. `services/session.js` — `requireAuth()`'un jenerikleştirilmiş hâli + refresh mantığı
3. `utils/sanitize.js` — Bölüm 5'teki XSS bulgusunun düzeltmesi (en yüksek öncelik, çünkü gerçek bir güvenlik açığı)
4. `state/store.js` — sayfalar arası kullanıcı/oturum tutarlılığı
5. Kalan `api/*.js` modülleri, backend endpoint'leri hazır oldukça tek tek

---

*Bu doküman `docs/design-system.md` ve `docs/design-review.md` ile birlikte okunmalıdır — biri görsel dili, biri mevcut tutarlılık durumunu, bu üçüncüsü ise backend'e bağlanma yolunu tanımlar.*
