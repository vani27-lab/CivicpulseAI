const env = import.meta.env

const parseCenter = (raw) => {
  const [lat, lng] = String(raw || '').split(',').map(Number)
  return Number.isFinite(lat) && Number.isFinite(lng) ? [lat, lng] : [22.9734, 78.6569]
}

export const config = {
  apiBase: (env.VITE_API_BASE_URL ?? '').replace(/\/$/, ''),
  mediaBase: (env.VITE_MEDIA_BASE_URL ?? env.VITE_API_BASE_URL ?? '').replace(/\/$/, ''),
  tokenKey: env.VITE_AUTH_TOKEN_KEY || 'civicpulse_token',
  loginPath: env.VITE_AUTH_LOGIN_PATH || '/api/auth/login',
  loginFormat: env.VITE_AUTH_LOGIN_FORMAT || 'json',
  mePath: env.VITE_AUTH_ME_PATH || '/api/auth/me',
  officerRoles: (env.VITE_OFFICER_ROLES || 'officer,admin').split(',').map((r) => r.trim().toLowerCase()),
  mapCenter: parseCenter(env.VITE_MAP_DEFAULT_CENTER),
  mapZoom: Number(env.VITE_MAP_DEFAULT_ZOOM) || 5,
  // Change a path here if Module 1/4 expose an equivalent route under another URL.
  paths: {
    stats: '/officer/dashboard/stats',
    filters: '/officer/filters',
    complaints: '/officer/complaints',
    complaintMap: '/officer/complaints/map',
    duplicates: '/officer/complaints/duplicates',
    confirmMerge: (id) => `/officer/duplicates/${id}/confirm`,
    rejectMerge: (id) => `/officer/duplicates/${id}/reject`,
    status: (id) => `/complaints/${id}/status`,
    classification: (id) => `/complaints/${id}/classification`,
    split: (id) => `/complaints/${id}/split`,
    heatmap: '/stats/heatmap',
  },
}

export const mediaUrl = (path) => {
  if (!path) return null
  if (/^(https?:|data:|blob:)/.test(path)) return path
  let clean = path.startsWith('/') ? path : `/${path}`
  if (!clean.startsWith('/uploads/') && !clean.startsWith('/media/')) {
    clean = `/uploads${clean}`
  }
  return `${config.mediaBase}${clean}`
}
