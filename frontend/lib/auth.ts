/**
 * Bare-bones client-side auth. Stores the JWT issued by POST /auth/login
 * in localStorage and attaches it to mutating API calls. This is not a
 * real session system (no refresh, no httpOnly cookie) -- appropriate
 * for a single-shared-password gate, not for a multi-user product.
 */

const TOKEN_KEY = "clauseiq_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
}

export function isAuthenticated(): boolean {
  return getToken() !== null;
}

export function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}
