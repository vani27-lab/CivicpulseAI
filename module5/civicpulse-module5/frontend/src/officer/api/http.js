import { config } from '../config'

export class ApiError extends Error {
  constructor(message, { status, code, detail } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.detail = detail
  }
}

let unauthorizedHandler = null
export const onUnauthorized = (fn) => { unauthorizedHandler = fn }

export const getToken = () => {
  try { return localStorage.getItem(config.tokenKey) } catch { return null }
}
export const setToken = (token) => {
  try { token ? localStorage.setItem(config.tokenKey, token) : localStorage.removeItem(config.tokenKey) } catch { /* storage blocked */ }
}

const toQuery = (params) => {
  const qs = new URLSearchParams()
  Object.entries(params || {}).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') qs.append(k, v)
  })
  const s = qs.toString()
  return s ? `?${s}` : ''
}

const messageFor = (status, body) => {
  const detail = body?.detail
  if (detail?.message) return detail.message
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg // FastAPI validation errors
  if (status === 401) return 'Your session has expired. Sign in again.'
  if (status === 403) return 'You do not have permission to do that.'
  if (status === 404) return 'That item could not be found.'
  if (status >= 500) return 'The server had a problem. Try again in a moment.'
  return 'The request could not be completed.'
}

export async function request(path, { method = 'GET', params, json, form, signal, auth = true } = {}) {
  const headers = { Accept: 'application/json' }
  const token = auth ? getToken() : null
  if (token) headers.Authorization = `Bearer ${token}`
  let body
  if (form) body = form
  else if (json !== undefined) { headers['Content-Type'] = 'application/json'; body = JSON.stringify(json) }

  let response
  try {
    response = await fetch(`${config.apiBase}${path}${toQuery(params)}`, { method, headers, body, signal })
  } catch (err) {
    if (err?.name === 'AbortError') throw err
    throw new ApiError('Cannot reach the server. Check your connection and try again.', { status: 0 })
  }

  let data = null
  try { data = await response.json() } catch { /* empty or non-JSON body */ }

  if (!response.ok) {
    if (response.status === 401 && auth && unauthorizedHandler) unauthorizedHandler()
    throw new ApiError(messageFor(response.status, data), {
      status: response.status,
      code: data?.detail?.code,
      detail: data?.detail,
    })
  }
  return data
}
