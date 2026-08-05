// ---------------------------------------------------------------------------
// Where the API lives.
//
//  • Single-origin deploy (VPS/nginx, local docker):  leave API_ORIGIN = ''.
//    nginx reverse-proxies /api to the backend, so same-origin just works
//    and there is no CORS.
//
//  • Split deploy (frontend on Vercel, backend on Render): set API_ORIGIN to
//    your Render backend URL, e.g. 'https://lexassist-api.onrender.com'.
//    The backend must then list your Vercel URL in CORS_ORIGINS.
// ---------------------------------------------------------------------------
const API_ORIGIN = 'https://lexassist-api.onrender.com';

export const API_BASE_URL = `${API_ORIGIN || window.location.origin}/api`;
export const TOKEN_KEY = 'lexassist_token';
export const USER_KEY = 'lexassist_user';
export const MAX_FILE_SIZE = 25 * 1024 * 1024; // 25MB
export const FREE_TIER_UPLOAD_LIMIT = 3;
