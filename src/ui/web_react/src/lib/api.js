import axios from 'axios';

export const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';
export const TOKEN_STORAGE_KEY = 'poc07.access_token';

// Create configured axios instance
export const api = axios.create({
  baseURL: API_BASE,
});

/**
 * Attach the bearer token to every axios request.
 */
export function applyToken(token) {
  if (token) {
    api.defaults.headers.common.Authorization = `Bearer ${token}`;
    axios.defaults.headers.common.Authorization = `Bearer ${token}`;
    localStorage.setItem(TOKEN_STORAGE_KEY, token);
  } else {
    delete api.defaults.headers.common.Authorization;
    delete axios.defaults.headers.common.Authorization;
    localStorage.removeItem(TOKEN_STORAGE_KEY);
  }
}

// Initialise token from localStorage if present
const initialToken = localStorage.getItem(TOKEN_STORAGE_KEY);
if (initialToken) {
  applyToken(initialToken);
}

/**
 * Read the `sub` and `role` claims out of a token for display purposes only.
 */
export function identityFromToken(token) {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return { email: payload.sub, role: payload.role };
  } catch {
    return null;
  }
}

/**
 * Turn a FastAPI / Steward error response into a human-readable string.
 */
export function describeApiError(err) {
  if (!err) return 'Unknown error';
  
  // Custom Steward error envelope
  if (err.response?.data?.error) {
    const e = err.response.data.error;
    if (e.needed && e.have) {
      return `${e.message || 'Insufficient data'}\nNeeded: ${e.needed}\nHave: ${e.have}${e.citation ? ` (${e.citation})` : ''}`;
    }
    return e.message || JSON.stringify(e);
  }

  // Pydantic validation errors (array in detail)
  const detail = err.response?.data?.detail;
  if (Array.isArray(detail)) {
    return detail.map(d => d.msg?.replace(/^Value error,\s*/, '') || JSON.stringify(d)).join('\n');
  }
  if (typeof detail === 'string') return detail;
  if (typeof detail === 'object' && detail !== null) return JSON.stringify(detail);

  return err.message || 'Unknown error';
}

export default api;
