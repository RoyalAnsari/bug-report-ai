import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { AuthContext } from '../auth/context'
import type { AuthState } from '../auth/context'
import { ADMIN, REVIEWER, makeAuthState } from '../auth/testState'
import AppLayout from './AppLayout'

function renderLayout(state: AuthState) {
  return render(
    <AuthContext.Provider value={state}>
      <MemoryRouter>
        <AppLayout />
      </MemoryRouter>
    </AuthContext.Provider>,
  )
}

describe('AppLayout with login', () => {
  it('hides admin-only pages from a reviewer', () => {
    renderLayout(makeAuthState({ user: REVIEWER }))
    expect(screen.getByRole('link', { name: 'Reports' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Account' })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Bulk predict' })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Upload' })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Settings' })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Users' })).not.toBeInTheDocument()
  })

  it('shows every page to an admin', () => {
    renderLayout(makeAuthState({ user: ADMIN }))
    expect(screen.getByRole('link', { name: 'Bulk predict' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Upload' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Settings' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Users' })).toHaveAttribute('href', '/users')
    expect(screen.getByRole('link', { name: 'Account' })).toHaveAttribute('href', '/account')
  })

  it('shows the user and a working Sign out button', async () => {
    const logout = vi.fn()
    const user = userEvent.setup()
    renderLayout(makeAuthState({ user: REVIEWER, logout }))

    expect(screen.getByText('Reviewer (reviewer)')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Sign out' }))
    expect(logout).toHaveBeenCalledTimes(1)
  })

  it('shows no Sign out, Users or Account when login is switched off', () => {
    renderLayout(makeAuthState({ authEnabled: false, user: ADMIN }))
    expect(screen.queryByRole('button', { name: 'Sign out' })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Users' })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Account' })).not.toBeInTheDocument()
  })
})
