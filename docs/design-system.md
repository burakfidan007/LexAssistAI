# LexAssist AI — Design System & UX Foundation

Bu doküman, LexAssist AI platformunun tüm gelecek ekranlarının üzerine inşa edileceği görsel dil ve UX kurallarını tanımlar. Referans alınan ürünler: **Harvey AI, CoCounsel, Stripe Dashboard, Notion, Vercel, Linear.**

Hedef kullanıcı: zamanı kısıtlı, güvenlik ve prestije önem veren profesyonel avukatlar ve hukuk büroları. Arayüz dili Türkçe; bu doküman İngilizce prompt'a yanıt olarak Türkçe hazırlanmıştır.

---

## 1. Tasarım İlkeleri

Arayüz şunları iletmelidir: **Güven, Profesyonellik, Prestij, Sadelik, Kurumsal Kalite, Güvenlik, Sakinlik, Zeka.**

Kurallar:
- Startup/renkli/eğlenceli SaaS estetiğinden kaçın (canlı mor-turkuaz gradyanlar, emoji, playful illüstrasyon yok).
- Renk sadece anlam taşımak için kullanılır (durum, önem, marka vurgusu) — dekorasyon için değil.
- Her ekran "sakin" hissettirmeli: az renk, çok beyaz alan, net hiyerarşi.
- Altın/gold rengi **nadir ve kasıtlı** kullanılır; bollaşırsa "premium" hissi yerine "gösterişli" hisse döner.
- Bir avukatın her gün 6-8 saat baktığı yazılım gibi tasarlanmalı: göz yormayan kontrast, gereksiz animasyon yok.

---

## 2. Renk Sistemi

| Token | Hex | Kullanım Alanı |
|---|---|---|
| `navy-900` (Primary Navy) | `#0F172A` | Sidebar arka planı, birincil buton arka planı, başlık metinleri, logo zemini |
| `navy-800` (Alternative Blue) | `#1E3A8A` | Primary buton hover/active, linkler, seçili sekme alt çizgisi, gradyan geçişleri |
| `bg-canvas` | `#F8FAFC` | Sayfa/uygulama arka planı (kartların altındaki zemin) |
| `white` | `#FFFFFF` | Kart yüzeyleri, modal, sidebar dışındaki paneller |
| `border` | `#E5E7EB` | Kart kenarlıkları, input kenarlıkları, ayırıcı çizgiler |
| `gold` (Premium) | `#D4AF37` | **Sadece**: premium rozet/CTA, aktif odak halkası (focus ring), premium kart aksanı, AI'nin "öne çıkan" önerisi. Büyük yüzeylerde asla kullanılmaz. |
| `success` | `#059669` (metin) / `#ECFDF5` (zemin) | Başarılı işlem, "Aktif" durum, tamamlanan yükleme |
| `warning` | `#D97706` (metin) / `#FFFBEB` (zemin) | Free tier limiti yaklaşıyor, dikkat gerektiren ama kritik olmayan durum |
| `error / risk` | `#DC2626` (metin) / `#FEF2F2` (zemin) | Riskli madde, silme işlemi, kritik hata |
| `info` | `#2563EB` (metin) / `#EFF6FF` (zemin) | Bilgilendirme banner'ı, AI ipucu kutuları |
| `muted-600` | `#64748B` | İkincil metin (açıklama, meta bilgi) |
| `muted-400` | `#94A3B8` | Placeholder, üçüncül metin, ikon rengi (pasif) |
| `hover-overlay` | `navy-900 üzerinde beyaz %8` / `beyaz yüzeyde navy %4` | Tüm hover durumları için tutarlı overlay mantığı — her bileşen için ayrı hover rengi tanımlamak yerine opaklık katmanı kullan |
| `disabled-bg` | `#F1F5F9` | Devre dışı input/buton zemini |
| `disabled-text` | `#CBD5E1` | Devre dışı metin/ikon |
| `disabled-border` | `#E2E8F0` | Devre dışı kenarlık |

**Kural:** Bir ekranda gold rengi aynı anda en fazla 1-2 öğede görünmeli. Navy, arayüzün "sesi"; gold, arayüzün "fısıltısı"dır.

---

## 3. Tipografi

**Font ailesi: Inter.** Gerekçe: değişken ağırlık ekseni sayesinde tutarlı bir aile içinde tüm ihtiyaçları karşılar, Türkçe karakterlerde (ı, ğ, ş, ç, ö, ü) mükemmel okunabilirlik sunar, küçük punto boyutlarında (12-13px) bile netliğini korur — yoğun metin/sözleşme okuyan avukatlar için kritik. Linear, Vercel ve Stripe'ın da tercih ettiği, "kurumsal ama soğuk değil" bir karakteri var.

| Seviye | Boyut / Satır Yüksekliği | Ağırlık | Kullanım |
|---|---|---|---|
| H1 | 32px / 40px | 700 | Sayfa başlığı (ör. "Davalarım") |
| H2 | 24px / 32px | 700 | Bölüm başlığı, modal başlığı |
| H3 | 20px / 28px | 600 | Kart grubu başlığı |
| H4 | 16px / 24px | 600 | Kart içi başlık (ör. dava adı) |
| Body-lg | 16px / 24px | 400 | Sohbet mesajları, önemli açıklamalar |
| Body | 14px / 20px | 400 | Standart arayüz metni |
| Body-sm | 13px / 18px | 400 | Meta bilgi, tarih, sayaç |
| Button | 14px / 20px | 600 | Tüm buton metinleri |
| Label | 13px / 16px | 500 | Form etiketleri; eyebrow etiketlerde uppercase + letter-spacing 0.04em |
| Caption | 12px / 16px | 400 | Yardım metni, hata mesajı altyazısı, timestamp |

**Kurallar:**
- Ağırlık paleti sadece 400 / 500 / 600 / 700 — 800/900 kullanılmaz (aşırı kalın başlıklar "startup" hissi verir).
- Satır yüksekliği: gövde metinde 1.4-1.5, başlıklarda 1.25-1.3.
- Bir satırda maksimum ~75 karakter (okunabilirlik için body metinlerde `max-width` sınırı).

---

## 4. Boşluk (Spacing) Sistemi

**Temel birim: 4px.** Ölçek: `4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96`.

| Bağlam | Değer |
|---|---|
| Kart iç boşluğu (padding) | 20-24px |
| Kart/öğe arası boşluk (grid gap) | 16-20px |
| Bölümler arası boşluk | 32-48px |
| Sayfa kenar boşluğu — Desktop (≥1280px) | 32px |
| Sayfa kenar boşluğu — Tablet (768-1279px) | 24px |
| Sayfa kenar boşluğu — Mobile (<768px) | 16px |
| İçerik maksimum genişliği (form/okuma alanı) | 640-720px |
| Dashboard içerik konteyneri | full-bleed (sidebar sabit 260-280px, kalan alan akışkan) |
| Sidebar genişliği | 260-280px (daraltılmış: 72px ikon-rail) |
| AI Analiz paneli genişliği | 360-400px |

**Kural:** İç içe geçen bileşenlerde boşluk her zaman 4'ün katı olmalı; 4px'in altına asla inilmez (ör. 3px, 5px yasak).

---

## 5. Border Radius

| Bileşen | Radius | Gerekçe |
|---|---|---|
| Button | 8px | Küçük öğe, hafif yumuşama yeterli |
| Input / Select / Textarea | 8px | Butonla tutarlılık — form ile buton aynı "hizada" hissetmeli |
| Card | 12-16px | Büyük yüzey, daha belirgin yumuşama premium his verir |
| Badge / Pill / Tag | 999px (full) | Durum göstergeleri her zaman tam yuvarlak |
| Dropdown / Popover | 10px | Buton ile kart arası ara değer |
| Modal / Dialog | 16-20px | En büyük yüzey, en yumuşak köşe — "kaldırılmış" bir yüzey hissi |
| Avatar | 999px (full) veya 8px (kare-yuvarlak kurumsal logo için) | Kullanıcıya göre |

**Tutarlılık kuralı:** Radius, öğe boyutuyla orantılı büyür. Küçük öğe + büyük radius = "oyuncak" görünüm; bundan kaçının. Aynı bileşen ailesinde (örn. tüm butonlar) tek bir radius değeri kullanılır, istisna yok.

---

## 6. Gölge (Shadow) Sistemi

| Token | Değer (öneri) | Kullanım |
|---|---|---|
| `shadow-sm` | `0 1px 2px rgba(15,23,42,0.04)` | Liste satırı hover, input focus öncesi zemin ayrımı |
| `shadow-md` | `0 4px 12px rgba(15,23,42,0.06)` | Kartların dinlenme (resting) durumu |
| `shadow-lg` | `0 12px 24px -8px rgba(15,23,42,0.12)` | Kart hover, dropdown/popover |
| `shadow-floating` | `0 16px 32px -12px rgba(15,23,42,0.18)` | Tooltip, kısa ömürlü yüzen öğeler |
| `shadow-modal` | `0 24px 48px -16px rgba(15,23,42,0.28)` + arka plan `backdrop-blur` | Modal, dialog |

**Kural:** Gölgeler her zaman soğuk/lacivert tonlu (`rgba(15,23,42,...)`), asla saf siyah değil — bu, paletle uyumlu ve daha "premium" bir derinlik hissi verir. Bir öğe aynı anda hem kalın border hem güçlü gölge taşımaz; ikisinden biri tercih edilir (kart: ince border + shadow-md; modal: border yok + shadow-modal).

---

## 7. Bileşen Kütüphanesi (Kavramsal)

### Butonlar
- **Primary:** Navy zemin, beyaz metin. Ana sayfa aksiyonu (Yeni Dava, Giriş Yap). Bir ekranda **en fazla 1 primary buton**.
- **Secondary:** Beyaz zemin, navy border + metin. İkincil aksiyonlar (İptal, Filtrele).
- **Ghost:** Zeminsiz, sadece metin/ikon; hover'da hafif gri zemin. Düşük öncelikli aksiyonlar (Detaylar, Daha Fazla).
- **Danger:** Kırmızı metin/border, zeminsiz (dolu kırmızı zemin yalnızca onay adımından sonra/dialog içinde). Silme, iptal etme.
- **Premium Upgrade:** Gold gradyan zemin, navy metin. Yalnızca sidebar alt kısmı ve upgrade dialog'da kullanılır — arayüzde en fazla 1-2 yerde tekrar eder, aşırı kullanılmaz.

Durum kuralları: `default / hover / active / focus (gold ring) / disabled / loading (spinner + disabled metin opaklığı)`.

### Girdiler (Inputs)
- **Text/Search/Password:** Beyaz zemin, `border` rengi kenarlık, focus'ta gold ring (2-3px, %35 opaklık) + border navy. Search input'ta sol ikon, sağda temizle (x) ikonu (dolulukta).
- **Textarea:** Aynı stil, otomatik yükseklik artışı, min 3 satır.
- **Select/Dropdown:** Text input ile aynı zemin/border, sağda chevron ikonu.
- **Checkbox/Radio:** 16px, navy dolgu (seçili), gold değil — gold sadece "premium/vurgu" anlamına geldiği için form kontrollerinde kullanılmaz.
- **Switch:** Kapalı: gri zemin. Açık: navy zemin (kritik/tehlikeli switch'lerde açık = kırmızı, bağlama göre).

### Kartlar
- **Case Card:** İkon + durum rozeti (sağ üst) + başlık + müvekkil + alt bilgi satırı (dosya sayısı, güncelleme tarihi). Hover: `shadow-lg` + 2px yukarı kayma.
- **AI Result Card:** Sol üstte küçük "AI Üretimi" etiketi (gold, uppercase, 10-11px), içerik metni, alt kısımda "Kopyala / Dilekçeye Ekle" gibi ikincil aksiyonlar.
- **Upload Card:** Dosya ikonu + ad + ilerleme çubuğu + durum etiketi (Yükleniyor/Tamamlandı/Hata).
- **Statistics Card:** Büyük sayı (H2 ağırlığında) + küçük label + opsiyonel trend ok/yüzde (success/error rengiyle).
- **Premium Card:** Gold ince border (1px) veya üst kenarda gold şerit; içerik navy zemin üzerinde beyaz metin olabilir (tek istisna — kontrast yaratmak için).

### Rozetler / Etiketler
- **JWT Secure / Docker Isolated:** Küçük pill, ince border, ikon + metin, nötr renk (navy/10 zemin) — güvenlik rozetleri "başarı yeşili" değil, nötr/güvenilir gri-navy tonda olmalı.
- **Premium:** Gold pill.
- **Risk Level:** Üç kademe — Düşük (success), Orta (warning), Kritik (error) — renk + ikon birlikte (yalnızca renkle anlam taşıma, erişilebilirlik için).
- **AI Confidence:** Yüzde + ince progress pill, info rengi tonlarında.
- **Folder / Completed / Pending / Critical (tags):** Nötr gri zemin varsayılan; durum bazlı renk yalnızca anlam değiştiğinde devreye girer.

### Navigasyon
- **Sidebar:** Sabit sol, navy zemin, ikon+etiket, aktif öğe beyaz/10 zemin + gold ikon rengi.
- **Topbar:** Yalnızca ana sidebar olmayan yardımcı sayfalarda (varsayılan: yok, dashboard sidebar yeterli).
- **Breadcrumb:** Sadece 2+ seviye derinlikte gösterilir (ör. Davalarım > Yılmaz vs. ABC > Belge), gereksiz yerde kullanılmaz.
- **Tabs:** Pill-container içinde segment control (login ekranındaki Giriş/Kayıt gibi) — max 4 sekme, fazlası dropdown'a alınır.
- **Pagination:** Sayı yerine "Önceki/Sonraki" + sayfa göstergesi tercih edilir (avukat için "kaçıncı sayfa" değil "ne kadar kaldı" önemli).
- **Dropdown (menü):** `shadow-floating`, 10px radius, öğe yüksekliği min 36px (tıklanabilirlik).

### Modallar
- **Confirmation Dialog:** Nötr, tek primary aksiyon.
- **Delete Dialog:** Başlıkta net uyarı ("Bu davayı silmek üzeresiniz"), danger buton sağda, iptal solda — **danger buton asla sol/varsayılan odakta değildir.**
- **Upgrade Dialog:** Gold aksan, fayda listesi (checkmark'lı), tek net CTA.

### Bildirimler
- **Toast:** Sağ alt/üst köşe, 4-5 sn otomatik kaybolur, ikon + kısa metin, kritik olmayan onaylar için (ör. "Dava oluşturuldu").
- **Banner:** Sayfa üstünde tam genişlik, kalıcı/kapatılabilir, sistem geneli bilgilendirme (ör. "Free tier limitine yaklaştınız").
- **Alert (inline):** Form/bölüm içinde, ilgili bağlamda hata/uyarı.

### Boş Durumlar (Empty States)
İkon/illüstrasyon (sade çizgi, renkli değil) + 1 cümle açıklama + net CTA buton. Asla sadece "Kayıt yok" yazıp bırakılmaz — her zaman bir sonraki adımı gösterir.

### Yükleme Durumları
- **Skeleton Loader:** İçerik yüklenirken kart/liste yapısını taklit eden gri bloklar (spinner değil) — algılanan hızı artırır, tercih edilen yöntem.
- **Progress Indicator (belirlenmiş süre):** Upload gibi ölçülebilir işlemler için çubuk.
- **Spinner:** Yalnızca süresi öngörülemeyen kısa işlemlerde (buton içi loading).

### Kullanım Göstergeleri
- **Upload Progress:** İnce çubuk + yüzde, dosya adının hemen altında.
- **Usage/Free Tier Indicator:** Çubuk + "X hakkın Y'si kullanıldı" metni; %100'e yaklaşınca renk warning'e, dolunca error'a döner.

### Diğer
- **Chart Placeholder:** Kurumsal, tek renkli (navy tonları) çizgi/bar grafik — canlı renkli "consumer" grafik paletleri kullanılmaz.
- **PDF Viewer Placeholder:** Kağıt benzeri beyaz yüzey, ince gölge, üstte sayfa/zoom kontrolleri.
- **Chat Bubble:** Kullanıcı: navy zemin sağda. AI: açık gri zemin solda, sol üst köşe sivri (konuşma yönü). AI baloncuğunda küçük "AI" rozeti opsiyonel.
- **Action Cards (AI Analiz butonları):** İkon + başlık + 1 satır açıklama, hover'da gold border — mevcut `index.html` implementasyonuyla birebir uyumlu.

---

## 8. İkonografi

- **Kütüphane:** Lucide (Heroicons ile aynı outline felsefesine sahip, daha geniş set).
- **Boyutlar:** 16px (inline/etiket içi), 20px (varsayılan buton/nav ikonu), 24px (boş durum/başlık yanı vurgu ikonu).
- **Stroke width:** Sabit 1.75-2px — kalınlık değişkenliği tutarsızlık yaratır.
- **Outline vs Filled:** Varsayılan her zaman **outline**. Filled/dolu ikon yalnızca: (a) aktif nav öğesinde, (b) durum noktası (status dot) gibi çok küçük vurgularda kullanılır. Filled ikonlar "seçili/aktif" anlamına gelir, dekorasyon için kullanılmaz.
- **Renk:** İkonlar varsayılan `muted-400`; aktif/vurgulu bağlamda `navy-900` veya `gold`.

---

## 9. Hareket (Motion) Tasarımı

| Etkileşim | Süre | Easing |
|---|---|---|
| Buton hover/active | 120-150ms | `ease-out` |
| Kart hover (gölge+translate) | 180-200ms | `ease-out` |
| Dropdown/popover açılış | 150ms | `ease-out`, 4px'lik yukarıdan gelme + fade |
| Modal açılış | 220-250ms | `ease-out`, hafif scale (0.98→1) + fade |
| Modal kapanış | 150ms | `ease-in` |
| Sayfa/görünüm geçişi (tab switch) | 200ms | `ease-in-out`, fade + 4-6px kayma |
| Yükleme/skeleton pulse | 1.2-1.5s loop | `ease-in-out` |
| Toast giriş/çıkış | 200ms giriş / 150ms çıkış | `ease-out` / `ease-in` |

**Kurallar:**
- Zıplayan (bounce/elastic) easing **kullanılmaz** — "sakin/kurumsal" ilkesiyle çelişir.
- Hiçbir animasyon 400ms'yi geçmez (dava dosyası açan bir avukat bekletilmemeli).
- `prefers-reduced-motion: reduce` sistem ayarına saygı gösterilir; bu durumda geçişler fade-only'e düşer, transform kaldırılır.

---

## 10. Erişilebilirlik

- **Kontrast:** Gövde metni min. **4.5:1** (WCAG AA), büyük başlık/ikon min. **3:1**. `muted-400` (#94A3B8) yalnızca büyük/ikincil metinde kullanılır, küçük gövde metninde kullanılmaz.
- **Klavye navigasyonu:** Tüm interaktif öğeler `Tab` ile ulaşılabilir olmalı; mantıksal sekme sırası (sol→sağ, yukarı→aşağı).
- **Focus ring:** Her interaktif öğede görünür gold focus ring (`box-shadow: 0 0 0 3px rgba(212,175,55,0.35)`), `outline: none` yalnızca bu ring ile birlikte kullanılır — asla focus tamamen gizlenmez.
- **ARIA:** İkon-only butonlarda `aria-label` zorunlu; modallarda `role="dialog"` + `aria-modal="true"` + açılışta odak modala taşınır; form hatalarında `aria-live="polite"` ile ekran okuyucuya anons edilir.
- **Tıklanabilir alan:** Minimum 40x40px (mobilde 44x44px) — küçük ikon butonlar bile bu görünmez alanla sarılır.
- **Renk bağımsızlığı:** Durum bilgisi asla sadece renkle verilmez (Risk Level'da ikon+renk+metin birlikte).

---

## 11. Responsive Strateji

Basit "her şeyi alt alta yığma" yaklaşımı **kullanılmaz** — her kırılım noktasında bilinçli bir yeniden düzenleme yapılır.

| Kırılım | Genişlik | Strateji |
|---|---|---|
| **Desktop** | ≥1280px | Tam 3 sütun (sidebar + sohbet/PDF + AI panel) yan yana. Sidebar genişletilmiş (etiketli). |
| **Laptop** | 1024-1279px | Sidebar ikon-rail'e daralır (72px, tooltip ile etiket). 3 sütun korunur ama AI paneli 320px'e daralır. |
| **Tablet** | 768-1023px | Sidebar off-canvas drawer'a döner (hamburger ile açılır). AI Analiz paneli ayrı sütun olmaktan çıkar; sağ üstte "Analiz" butonuyla açılan bir **slide-over panel** olur. Ana alan: sohbet/PDF tam genişlik. |
| **Mobile** | <768px | Sidebar tamamen kaldırılır, yerine alt **tab bar** (Dashboard / Davalarım / Yükle / Ayarlar) gelir. AI Analiz butonları, sohbet ekranının üstünde yatay kaydırmalı bir çubuk veya alttan açılan bottom-sheet olur. Chat, birincil ve tek odak; PDF görünümü ayrı bir tam ekran görünüme geçer (tab yerine buton). |

**UX prensibi:** Küçülen ekranda önce **ikincil bilgi yoğunluğu** azaltılır (AI panel, breadcrumb, meta bilgiler), **birincil aksiyon** (sohbet/analiz) her zaman en görünür ve en az tıklamayla ulaşılabilir kalır.

---

## 12. Design Token Referansı

```json
{
  "color": {
    "navy": { "900": "#0F172A", "800": "#1E3A8A" },
    "surface": { "canvas": "#F8FAFC", "white": "#FFFFFF" },
    "border": { "default": "#E5E7EB" },
    "gold": { "DEFAULT": "#D4AF37", "light": "#F4E5B2" },
    "success": { "text": "#059669", "bg": "#ECFDF5" },
    "warning": { "text": "#D97706", "bg": "#FFFBEB" },
    "error":   { "text": "#DC2626", "bg": "#FEF2F2" },
    "info":    { "text": "#2563EB", "bg": "#EFF6FF" },
    "muted":   { "600": "#64748B", "400": "#94A3B8" },
    "disabled":{ "bg": "#F1F5F9", "text": "#CBD5E1", "border": "#E2E8F0" }
  },
  "spacing": [4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96],
  "radius": {
    "button": 8, "input": 8, "card": 14, "dropdown": 10,
    "modal": 18, "pill": 999
  },
  "shadow": {
    "sm": "0 1px 2px rgba(15,23,42,0.04)",
    "md": "0 4px 12px rgba(15,23,42,0.06)",
    "lg": "0 12px 24px -8px rgba(15,23,42,0.12)",
    "floating": "0 16px 32px -12px rgba(15,23,42,0.18)",
    "modal": "0 24px 48px -16px rgba(15,23,42,0.28)"
  },
  "typography": {
    "fontFamily": "Inter, sans-serif",
    "h1": { "size": 32, "lineHeight": 40, "weight": 700 },
    "h2": { "size": 24, "lineHeight": 32, "weight": 700 },
    "h3": { "size": 20, "lineHeight": 28, "weight": 600 },
    "h4": { "size": 16, "lineHeight": 24, "weight": 600 },
    "bodyLg": { "size": 16, "lineHeight": 24, "weight": 400 },
    "body": { "size": 14, "lineHeight": 20, "weight": 400 },
    "bodySm": { "size": 13, "lineHeight": 18, "weight": 400 },
    "caption": { "size": 12, "lineHeight": 16, "weight": 400 }
  },
  "motion": {
    "fast": "150ms ease-out",
    "base": "200ms ease-out",
    "modal": "250ms ease-out",
    "exit": "150ms ease-in"
  }
}
```

---

## 13. UX Kuralları (Her Ekran İçin Geçerli)

- **Birincil aksiyon sayısı:** Bir ekranda en fazla **1 primary buton** bulunur. Diğer tüm aksiyonlar secondary/ghost'tur. Bu, avukatın "ne yapmam gerekiyor" sorusuna her zaman net bir cevap vermesini sağlar.
- **AI aksiyonlarının vurgusu:** AI aksiyonları (özet çıkar, risk bul, taslak üret) renkle değil, **konumla ve ikonla** öne çıkar (sağ panel, sabit konum, tutarlı ikon dili). Gold rengi yalnızca sonuç kartındaki "AI Üretimi" etiketinde kullanılır — buton zemininde değil (aksi halde her AI butonu "premium" gibi görünür ve gold'un anlamı sulanır).
- **Yıkıcı (destructive) aksiyonlar:** Her zaman ikinci bir onay adımı gerektirir (dialog); dialog içinde danger buton sağda, iptal solda/varsayılan odakta. Liste görünümünde silme ikonu asla birincil aksiyonla aynı görsel ağırlıkta olmaz (küçük, ghost, hover'da belirir).
- **Premium tanıtımı:** Rahatsız edici modal/popup ile değil, **sürekli ama sessiz** bir sidebar CTA'sı ve ilgili anlarda (limit dolduğunda) bağlamsal banner ile yapılır. Kullanıcı akışını asla kesmez (ör. yükleme sırasında zorla upgrade ekranına yönlendirilmez, sadece uyarılır).
- **Dava/klasör navigasyonu:** Avukat her zaman "hangi davadayım" sorusuna tek bakışta cevap bulmalı — aktif dava adı üst kısımda sabit, davalar arası geçiş tek tıkla (dropdown veya breadcrumb), asla iç içe çok seviyeli menü gerektirmez.
- **Boş durumlar:** İlk kullanım anını bir engel değil, bir davet olarak tasarla — "Henüz dava yok" yerine "İlk davanızı oluşturun, PDF'inizi 30 saniyede analiz edin" tonunda, net CTA ile.
- **Güven sinyalleri:** Güvenlik rozetleri (JWT, Docker Isolated) yalnızca giriş ekranında değil, dosya yükleme gibi "hassas" anlarda da (küçük, sessiz biçimde) tekrarlanabilir — ama asla her ekranda tekrar edilerek "aşırı ikna etmeye çalışan" bir ton yaratmaz.
- **Tutarlılık kuralı:** Yeni bir ekran tasarlanırken önce bu dokümandaki token'lar ve bileşen kuralları kontrol edilir; özel/tek seferlik stil (ad-hoc renk, ad-hoc radius) oluşturulmaz.

---

*Bu doküman, `frontend/` altında halihazırda uygulanmış olan login/cases/upload/dashboard ekranlarının tasarım mantığını formalize eder ve bundan sonraki tüm ekran/bileşen kararları için referans kaynaktır.*
