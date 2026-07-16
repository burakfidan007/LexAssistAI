# LexAssist AI

Avukatların dava dosyalarını (PDF) yükleyerek yapay zeka ile analiz edebildiği, riskli maddeleri tespit edebildiği, dosya hakkında soru sorabildiği ve otomatik dilekçe taslakları üretebildiği web tabanlı bir LegalTech SaaS uygulaması.

## Klasör Yapısı

```
lexassist-ai/
├── frontend/                saf HTML5 + Tailwind CSS (CDN) + Vanilla JS (ES Modules)
│   ├── login.html            giriş / kayıt ekranı
│   ├── my-cases.html          "Davalarım" - dava/klasör yönetimi
│   ├── upload.html             PDF yükleme (sürükle-bırak, free tier limit göstergesi)
│   ├── index.html                ana dashboard (3 sütun: navigasyon, sohbet/PDF, AI analiz)
│   ├── assets/
│   └── js/
│       ├── config/env.js          API_BASE_URL, token anahtarları, limitler
│       ├── api/http.js             merkezi fetch katmanı (Authorization header, hata normalizasyonu)
│       └── utils/sanitize.js        kullanıcı girdisini innerHTML'e yazmadan önce escape eder
├── backend/                 FastAPI + MongoDB (henüz oluşturulmadı)
├── docs/
│   ├── design-system.md      görsel dil ve UX kuralları
│   ├── design-review.md       tutarlılık/erişilebilirlik denetimi
│   └── frontend-architecture.md  backend entegrasyon mimarisi
├── docker-compose.yml
├── .env.example
└── .gitignore
```

## Tasarım

- **Palet:** Koyu lacivert (`#0f172a`), beyaz, açık gri arka planlar, altın sarısı (`#d4af37`) vurgular.
- **Stil:** Kurumsal, güven veren, modern SaaS (Harvey AI / Casetext CoCounsel esinli).
- **Platform:** Framework'süz, saf HTML5 + Tailwind CDN + Vanilla JS (native ES Modules). Backend API'leri ile `js/api/http.js` üzerinden haberleşir.

Detaylar için `docs/design-system.md`, `docs/design-review.md` ve `docs/frontend-architecture.md`'ye bakın.

## Veritabanı

**MongoDB** — dava/dosya metadata, kullanıcı hesapları ve free tier limit takibi için. Bağlantı bilgileri `.env`'de (`MONGO_URI`), servis tanımı `docker-compose.yml`'de.

## Çalıştırma

Sayfalar ES Modules kullandığı için **`file://` üzerinden doğrudan açılamaz** (tarayıcılar bunu güvenlik nedeniyle engeller). Docker ile çalıştırın:

```
docker compose up -d frontend
```

sonra `http://localhost:3000/login.html` adresine gidin. `frontend/` klasörü container'a bind-mount edildiği için dosya değişiklikleri anında yansır — yeniden başlatmaya gerek yok, sadece tarayıcıyı yenileyin.

Backend henüz yok; `login.html` backend'e ulaşamadığında otomatik olarak demo oturumuyla devam eder, böylece diğer 3 ekran da önizlenebilir.

Durdurmak için:

```
docker compose down
```

## Backend (Yapılacak)

- FastAPI + JWT auth
- MongoDB (dava/dosya metadata, free tier limit takibi)
- PDF analiz, sohbet ve dilekçe taslağı üretimi için LLM entegrasyonu
- `docker-compose.yml` içindeki `backend` servisi backend kodu eklendiğinde etkinleştirilecek

## Git Commit Kuralları

Tüm commit mesajları **scope'lu Conventional Commits** formatında yazılır:

```
<tip>(<scope>): <kısa açıklama>
```

**Tipler:** `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `build`

**Scope'lar** (proje klasör yapısına karşılık gelir): `frontend`, `backend`, `docs`, `docker`, `config`

Örnekler:

```
feat(frontend): add command palette to my-cases and upload pages
fix(frontend): escape user input before rendering to prevent XSS
docs(docs): add frontend architecture and backend integration plan
chore(docker): add mongo service and dev .env defaults
```
