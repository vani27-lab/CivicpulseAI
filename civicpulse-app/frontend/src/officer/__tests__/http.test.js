import { vi } from 'vitest'
import { ApiError, onUnauthorized, request, setToken } from '../api/http'

const respond = (status, body) =>
  vi.fn().mockResolvedValue({ ok: status >= 200 && status < 300, status, json: async () => body })

beforeEach(() => { localStorage.clear(); onUnauthorized(null) })

describe('request', () => {
  it('sends the bearer token and drops empty query params', async () => {
    setToken('jwt-123')
    global.fetch = respond(200, { ok: true })
    await request('/officer/complaints', { params: { q: '', status: 'assigned', page: 2 } })
    const [url, init] = global.fetch.mock.calls[0]
    expect(url).toContain('/officer/complaints?status=assigned&page=2')
    expect(init.headers.Authorization).toBe('Bearer jwt-123')
  })

  it('turns API errors into readable messages', async () => {
    global.fetch = respond(409, { detail: { code: 'invalid_transition', message: 'Cannot move from Submitted to Resolved.' } })
    await expect(request('/x')).rejects.toMatchObject({ message: 'Cannot move from Submitted to Resolved.', code: 'invalid_transition', status: 409 })
  })

  it('reads FastAPI validation errors', async () => {
    global.fetch = respond(422, { detail: [{ msg: 'Field required' }] })
    await expect(request('/x')).rejects.toThrow('Field required')
  })

  it('signs the officer out on 401', async () => {
    const handler = vi.fn()
    onUnauthorized(handler)
    global.fetch = respond(401, { detail: 'Not authenticated' })
    await expect(request('/x')).rejects.toBeInstanceOf(ApiError)
    expect(handler).toHaveBeenCalledTimes(1)
  })

  it('reports an unreachable server clearly', async () => {
    global.fetch = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'))
    await expect(request('/x')).rejects.toMatchObject({ status: 0, message: expect.stringMatching(/cannot reach the server/i) })
  })

  it('does not wrap an aborted request', async () => {
    const abort = Object.assign(new Error('aborted'), { name: 'AbortError' })
    global.fetch = vi.fn().mockRejectedValue(abort)
    await expect(request('/x')).rejects.toMatchObject({ name: 'AbortError' })
  })
})
