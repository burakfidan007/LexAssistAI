import { API_BASE_URL, TOKEN_KEY, USER_KEY } from '../config/env.js';

export class ApiError extends Error {
  constructor(message, status, fields) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.fields = fields;
  }
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setSession(token, user) {
  localStorage.setItem(TOKEN_KEY, token);
  if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

// Request timeouts. Without these a stalled request leaves the caller's
// spinner up forever, since fetch() has no timeout of its own. AI routes get
// a much longer budget: a draft legitimately takes ~40s, and a cold backend
// instance can add another ~50s before it even starts answering.
const DEFAULT_TIMEOUT_MS = 30000;
const AI_TIMEOUT_MS = 150000;
const UPLOAD_TIMEOUT_MS = 120000;

function timeoutFor(path) {
  if (path.startsWith('/ai/')) return AI_TIMEOUT_MS;
  if (path.startsWith('/uploads')) return UPLOAD_TIMEOUT_MS;
  return DEFAULT_TIMEOUT_MS;
}

/**
 * Tek merkezi fetch katmanı. auth:true (varsayılan) iken Authorization header'ı
 * ekler ve 401'de oturumu temizleyip login.html'e yönlendirir. Giriş/kayıt gibi
 * henüz oturum olmayan çağrılar auth:false geçmeli — 401 orada "geçersiz kimlik
 * bilgisi" anlamına gelir, "oturum sona erdi" değil.
 *
 * Her istek bir zaman aşımına bağlıdır ve ağ/zaman aşımı hataları da ApiError
 * olarak yükselir — böylece çağıran taraf tek bir catch bloğuyla hem HTTP
 * hatalarını hem de bağlantı sorunlarını kullanıcıya anlatabilir.
 */
export async function request(path, { method = 'GET', body, auth = true, timeoutMs } = {}) {
  const isFormData = body instanceof FormData;
  const headers = {};
  if (!isFormData && body !== undefined) headers['Content-Type'] = 'application/json';
  if (auth) {
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const controller = new AbortController();
  const limit = timeoutMs ?? timeoutFor(path);
  const timer = setTimeout(() => controller.abort(), limit);

  let res;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: isFormData ? body : body !== undefined ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
  } catch (err) {
    // AbortError = our own timeout fired; anything else here is a transport
    // failure (offline, DNS, TLS, backend unreachable) — fetch only rejects
    // for those, never for a 4xx/5xx.
    if (err.name === 'AbortError') {
      throw new ApiError(
        'İstek zaman aşımına uğradı. Sunucu yanıt vermiyor olabilir, lütfen tekrar deneyin.',
        0,
      );
    }
    throw new ApiError('Sunucuya ulaşılamadı. İnternet bağlantınızı kontrol edip tekrar deneyin.', 0);
  } finally {
    clearTimeout(timer);
  }

  if (res.status === 401 && auth) {
    clearSession();
    window.location.href = 'login.html';
    throw new ApiError('Oturum sona erdi.', 401);
  }

  if (!res.ok) {
    const payload = await res.json().catch(() => ({}));
    // FastAPI's default error shape is {"detail": "..."}; support a future
    // {"message": "..."} shape too so this doesn't need to change either way.
    const fallback = res.status >= 500
      ? 'Sunucu şu anda yanıt veremiyor. Lütfen birkaç saniye sonra tekrar deneyin.'
      : 'Bir hata oluştu.';
    throw new ApiError(payload.detail || payload.message || fallback, res.status, payload.fields);
  }

  const contentType = res.headers.get('content-type') || '';
  return contentType.includes('application/json') ? res.json() : res.text();
}
