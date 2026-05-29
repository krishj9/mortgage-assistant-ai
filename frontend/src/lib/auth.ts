const BORROWER_TOKEN_KEY = "lo_copilot_borrower_token";
const STAFF_TOKEN_KEY = "lo_copilot_staff_token";

/** @deprecated Use getBorrowerToken for borrower flows. */
export function getAccessToken(): string | null {
  return getBorrowerToken();
}

/** @deprecated Use setBorrowerToken for borrower flows. */
export function setAccessToken(token: string) {
  setBorrowerToken(token);
}

export function getBorrowerToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(BORROWER_TOKEN_KEY);
}

export function setBorrowerToken(token: string) {
  window.localStorage.setItem(BORROWER_TOKEN_KEY, token);
}

export function clearBorrowerToken() {
  window.localStorage.removeItem(BORROWER_TOKEN_KEY);
}

export function getStaffToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(STAFF_TOKEN_KEY);
}

export function setStaffToken(token: string) {
  window.localStorage.setItem(STAFF_TOKEN_KEY, token);
}

export function clearStaffToken() {
  window.localStorage.removeItem(STAFF_TOKEN_KEY);
}

export function getAuthHeader(token?: string | null): string | null {
  const t = token ?? getBorrowerToken();
  return t ? `Bearer ${t}` : null;
}
