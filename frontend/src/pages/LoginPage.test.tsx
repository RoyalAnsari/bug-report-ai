import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { peekFlash, setFlash } from '../lib/flash'
import { AuthContext } from '../auth/context'
import type { AuthState } from '../auth/context'
import { ADMIN, makeAuthState } from '../auth/testState'
import LoginPage from './LoginPage'

function renderLogin(state: AuthState) {
  return render(
    <AuthContext.Provider value={state}>
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<p>Home page</p>} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  )
}

describe('LoginPage', () => {
  beforeEach(() => {
    window.sessionStorage.clear()
  })

  it('shows a waiting message (for example after a password change) and then clears it', () => {
    setFlash('Your password was changed.')
    renderLogin(makeAuthState())
    expect(screen.getByRole('status')).toHaveTextContent('Your password was changed.')
    expect(peekFlash()).toBeNull()
  })

  it('signs in with the typed email and password, then opens the home page', async () => {
    const login = vi.fn().mockResolvedValue(undefined)
    const user = userEvent.setup()
    renderLogin(makeAuthState({ login }))

    await user.type(screen.getByLabelText('Email'), '  admin@example.com ')
    await user.type(screen.getByLabelText('Password'), 'correct horse battery')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(login).toHaveBeenCalledWith('admin@example.com', 'correct horse battery')
    expect(await screen.findByText('Home page')).toBeInTheDocument()
  })

  it('shows an error and stays on the page when login fails', async () => {
    const login = vi.fn().mockRejectedValue(new Error('nope'))
    const user = userEvent.setup()
    renderLogin(makeAuthState({ login }))

    await user.type(screen.getByLabelText('Email'), 'admin@example.com')
    await user.type(screen.getByLabelText('Password'), 'wrong password')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(screen.queryByText('Home page')).not.toBeInTheDocument()
  })

  it('tells people who forgot their password to ask an admin', () => {
    renderLogin(makeAuthState())
    expect(screen.getByText(/Ask an admin to reset it/)).toBeInTheDocument()
  })

  it('skips the login page when the user is already signed in', () => {
    renderLogin(makeAuthState({ user: ADMIN }))
    expect(screen.getByText('Home page')).toBeInTheDocument()
  })

  it('skips the login page when login is switched off', () => {
    renderLogin(makeAuthState({ authEnabled: false }))
    expect(screen.getByText('Home page')).toBeInTheDocument()
  })
})
