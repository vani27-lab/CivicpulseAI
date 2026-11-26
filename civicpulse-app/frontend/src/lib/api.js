// All calls to the backend go through this file.
// In development, Vite forwards "/api/..." to the FastAPI server (see vite.config.js).

const API_BASE = "/api";
const TOKEN_KEY = "civicpulse_token";

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (token) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

function friendlyMessage(data, status) {
  if (data && typeof data.detail === "string") return data.detail;
  if (data && Array.isArray(data.detail)) {
    const text = data.detail
      .map((item) => (item.msg || "").replace(/^Value error, /, ""))
      .filter(Boolean)
      .join(" ");
    if (text) return text;
  }
  return `Something went wrong (error ${status}). Please try again.`;
}

async function request(path, { method = "GET", body, auth = true } = {}) {
  const headers = {};
  // A FormData body (photo upload) sets its own Content-Type, so only JSON needs the header.
  const isForm = body instanceof FormData;
  if (body !== undefined && !isForm) headers["Content-Type"] = "application/json";
  const token = tokenStore.get();
  if (auth && token) headers.Authorization = `Bearer ${token}`;

  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : isForm ? body : JSON.stringify(body),
    });
  } catch {
    throw new ApiError("Cannot reach the server. Please check that the backend is running.", 0);
  }

  let data = null;
  try {
    data = await response.json();
  } catch {
    // some responses have no body
  }

  if (!response.ok) throw new ApiError(friendlyMessage(data, response.status), response.status);
  return data;
}

export const api = {
  health: () => request("/health", { auth: false }),
  login: (email, password) => request("/auth/login", { method: "POST", body: { email, password }, auth: false }),
  register: (details) => request("/auth/register", { method: "POST", body: details, auth: false }),
  me: () => request("/auth/me"),
  users: () => request("/users"),
  submitReport: (formData) => request("/reports", { method: "POST", body: formData }),
  departments: () => request("/departments", { auth: false }),
};
