import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { AuthContext } from './context'
import type { AuthState } from './context'
import RequireAuth from './RequireAuth'
import RequireRole from './RequireRole'
import { ADMIN, REVIEWER, makeAuthState } from './testState'

function renderGuarded(state: AuthState, roles?: Array<'admin' | 'reviewer'>) {
  const content = roles ? (
    <RequireRole roles={roles}>
      <p>Private page</p>
    </RequireRole>
  ) : (
    <p>Private page</p>
  )
  return render(
    <AuthContext.Provider value={state}>
      <MemoryRouter initialEntries={['/private']}>
        <Routes>
          <Route path="/login" element={<p>Login page</p>} />
          <Route path="/private" element={<RequireAuth>{content}</RequireAuth>} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  )
}

describe('RequireAuth', () => {
  it('sends a signed-out visitor to the login page', () => {
    renderGuarded(makeAuthState({ authEnabled: true, user: null }))
    expect(screen.getByText('Login page')).toBeInTheDocument()
    expect(screen.queryByText('Private page')).not.toBeInTheDocument()
  })

  it('shows the page to a signed-in user', () => {
    renderGuarded(makeAuthState({ authEnabled: true, user: ADMIN }))
    expect(screen.getByText('Private page')).toBeInTheDocument()
  })

  it('shows the page when login is switched off on the server', () => {
    renderGuarded(makeAuthState({ authEnabled: false, user: null }))
    expect(screen.getByText('Private page')).toBeInTheDocument()
  })

  it('shows a loading message while it checks', () => {
    renderGuarded(makeAuthState({ status: 'loading' }))
    expect(screen.getByRole('status')).toHaveTextContent('Loading')
  })

  it('shows an error with a retry button when the server cannot be reached', () => {
    renderGuarded(makeAuthState({ status: 'error', error: 'Cannot reach the server.' }))
    expect(screen.getByRole('alert')).toHaveTextContent('Cannot reach the server.')
    expect(screen.getByRole('button', { name: 'Try again' })).toBeInTheDocument()
  })
})

describe('RequireRole', () => {
  it('lets an admin open an admin-only page', () => {
    renderGuarded(makeAuthState({ user: ADMIN }), ['admin'])
    expect(screen.getByText('Private page')).toBeInTheDocument()
  })

  it('blocks a reviewer from an admin-only page', () => {
    renderGuarded(makeAuthState({ user: REVIEWER }), ['admin'])
    expect(screen.queryByText('Private page')).not.toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('permission')
  })
})
