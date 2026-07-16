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

/**
 * Tek merkezi fetch katmanı. auth:true (varsayılan) iken Authorization header'ı
 * ekler ve 401'de oturumu temizleyip login.html'e yönlendirir. Giriş/kayıt gibi
 * henüz oturum olmayan çağrılar auth:false geçmeli — 401 orada "geçersiz kimlik
 * bilgisi" anlamına gelir, "oturum sona erdi" değil.
 */
export async function request(path, { method = 'GET', body, auth = true } = {}) {
  const isFormData = body instanceof FormData;
  const headers = {};
  if (!isFormData && body !== undefined) headers['Content-Type'] = 'application/json';
  if (auth) {
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: isFormData ? body : body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401 && auth) {
    clearSession();
    window.location.href = 'login.html';
    throw new ApiError('Oturum sona erdi.', 401);
  }

  if (!res.ok) {
    const payload = await res.json().catch(() => ({}));
    throw new ApiError(payload.message || 'Bir hata oluştu.', res.status, payload.fields);
  }

  const contentType = res.headers.get('content-type') || '';
  return contentType.includes('application/json') ? res.json() : res.text();
}
