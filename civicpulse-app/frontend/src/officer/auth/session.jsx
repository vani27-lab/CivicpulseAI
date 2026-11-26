import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { config } from '../config'
import { ApiError, getToken, onUnauthorized, request, setToken } from '../api/http'

/**
 * Thin adapter over Module 1's authentication. It never issues or validates tokens
 * itself: it calls the existing login and "me" endpoints and keeps the JWT where
 * Module 1's frontend keeps it (VITE_AUTH_TOKEN_KEY). The server enforces roles on
 * every request; the role check here only decides which screens to show.
 */
const SessionContext = createContext(null)

export const isOfficerRole = (role) => config.officerRoles.includes(String(role || '').toLowerCase())

export function SessionProvider({ children }) {
  const [state, setState] = useState({ status: getToken() ? 'loading' : 'anonymous', user: null })

  const signOut = useCallback(() => {
    setToken(null)
    setState({ status: 'anonymous', user: null })
  }, [])

  useEffect(() => { onUnauthorized(signOut) }, [signOut])

  useEffect(() => {
    if (!getToken()) return
    let cancelled = false
    request(config.mePath)
      .then((user) => { if (!cancelled) setState({ status: 'authenticated', user }) })
      .catch(() => { if (!cancelled) signOut() })
    return () => { cancelled = true }
  }, [signOut])

  const signIn = useCallback(async (email, password) => {
    let tokenResponse
    if (config.loginFormat === 'form') {
      const form = new URLSearchParams({ username: email, password })
      const res = await fetch(`${config.apiBase}${config.loginPath}`, { method: 'POST', body: form })
      tokenResponse = await res.json().catch(() => null)
      if (!res.ok) throw new ApiError('Email or password is incorrect.', { status: res.status })
    } else {
      tokenResponse = await request(config.loginPath, { method: 'POST', json: { email, password }, auth: false })
    }
    const token = tokenResponse?.access_token
    if (!token) throw new ApiError('Sign-in succeeded but no access token was returned.')
    setToken(token)
    const user = await request(config.mePath)
    if (!isOfficerRole(user?.role)) {
      setToken(null)
      setState({ status: 'anonymous', user: null })
      throw new ApiError('This account does not have officer access.', { status: 403 })
    }
    setState({ status: 'authenticated', user })
    return user
  }, [])

  const value = useMemo(() => ({ ...state, signIn, signOut }), [state, signIn, signOut])
  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
}

export const useSession = () => {
  const ctx = useContext(SessionContext)
  if (!ctx) throw new Error('useSession must be used inside <SessionProvider>')
  return ctx
}
