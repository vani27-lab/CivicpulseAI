import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { vi } from 'vitest'

const session = vi.hoisted(() => ({ value: { status: 'anonymous', user: null } }))
vi.mock('../auth/session', () => ({
  useSession: () => session.value,
  isOfficerRole: (r) => ['officer', 'admin'].includes(String(r).toLowerCase()),
}))
import { RequireOfficer } from '../auth/RequireOfficer'

const renderGuarded = () =>
  render(
    <MemoryRouter initialEntries={['/officer']}>
      <Routes>
        <Route path="/officer/login" element={<p>Login page</p>} />
        <Route path="/officer" element={<RequireOfficer><p>Secret dashboard</p></RequireOfficer>} />
      </Routes>
    </MemoryRouter>,
  )

describe('RequireOfficer', () => {
  it('sends anonymous visitors to the login page', () => {
    session.value = { status: 'anonymous', user: null }
    renderGuarded()
    expect(screen.getByText('Login page')).toBeInTheDocument()
    expect(screen.queryByText('Secret dashboard')).not.toBeInTheDocument()
  })

  it('blocks citizens even though they are signed in', () => {
    session.value = { status: 'authenticated', user: { role: 'citizen' } }
    renderGuarded()
    expect(screen.getByText(/officer access only/i)).toBeInTheDocument()
    expect(screen.queryByText('Secret dashboard')).not.toBeInTheDocument()
  })

  it.each(['officer', 'admin'])('lets a %s in', (role) => {
    session.value = { status: 'authenticated', user: { role } }
    renderGuarded()
    expect(screen.getByText('Secret dashboard')).toBeInTheDocument()
  })

  it('waits while the session is being verified', () => {
    session.value = { status: 'loading', user: null }
    renderGuarded()
    expect(screen.getByRole('status')).toHaveTextContent(/checking your session/i)
  })
})
