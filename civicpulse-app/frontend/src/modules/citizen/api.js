const BASE = (import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || "").replace(/\/$/, "");
const TOKEN_KEY = import.meta.env.VITE_TOKEN_KEY || "civicpulse_token";
export class ApiError extends Error { constructor(status, msg) { super(msg); this.status = status; } }

async function req(path, opts = {}) {
  const token = localStorage.getItem(TOKEN_KEY) || localStorage.getItem("token");
  const res = await fetch(BASE + path, { ...opts, headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) } });
  if (res.status === 401) window.dispatchEvent(new Event("auth:expired"));
  if (!res.ok) throw new ApiError(res.status, (await res.json().catch(() => ({}))).detail || res.statusText);
  return res.status === 204 ? null : res.json();
}
export const mediaUrl = (u) => {
  if (!u) return null;
  if (/^(https?:|data:|blob:)/.test(u)) return u;
  let clean = u.startsWith("/") ? u : `/${u}`;
  if (!clean.startsWith("/uploads/") && !clean.startsWith("/media/")) {
    clean = `/uploads${clean}`;
  }
  return BASE + clean;
};
export const getMine = () => req("/complaints/mine");
export const getComplaint = (id) => req(`/complaints/${id}`);
export const getHistory = (id) => req(`/complaints/${id}/history`);
export const getUpdates = (id, lang) => req(`/complaints/${id}/updates?lang=${lang}`);
export const getNotifications = () => req("/notifications");
export const markRead = (id) => req(`/notifications/${id}/read`, { method: "POST" });
export const markAllRead = () => req("/notifications/read-all", { method: "POST" });
export const hasToken = () => !!localStorage.getItem(TOKEN_KEY);
