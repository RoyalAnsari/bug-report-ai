import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { peekFlash } from '../lib/flash'
import { AuthContext } from '../auth/context'
import { REVIEWER, makeAuthState } from '../auth/testState'
import { changePassword } from '../services/auth'
import AccountPage from './AccountPage'

vi.mock('../services/auth', () => ({
  changePassword: vi.fn(),
}))

function renderPage(logout: () => void = () => {}) {
  return render(
    <AuthContext.Provider value={makeAuthState({ user: REVIEWER, logout })}>
      <AccountPage />
    </AuthContext.Provider>,
  )
}

describe('AccountPage', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    window.sessionStorage.clear()
  })

  it('shows who is signed in', () => {
    renderPage()
    expect(screen.getByText(/rev@example.com/)).toBeInTheDocument()
  })

  it('refuses a new password that does not match the confirmation', async () => {
    const user = userEvent.setup()
    renderPage()
    await user.type(screen.getByLabelText('Current password'), 'old password value')
    await user.type(screen.getByLabelText('New password'), 'a brand new password')
    await user.type(screen.getByLabelText('Confirm new password'), 'a different password')
    await user.click(screen.getByRole('button', { name: 'Change password' }))

    expect(screen.getByRole('alert')).toHaveTextContent('do not match')
    expect(changePassword).not.toHaveBeenCalled()
  })

  it('refuses a short new password', async () => {
    const user = userEvent.setup()
    renderPage()
    await user.type(screen.getByLabelText('Current password'), 'old password value')
    await user.type(screen.getByLabelText('New password'), 'short')
    await user.type(screen.getByLabelText('Confirm new password'), 'short')
    await user.click(screen.getByRole('button', { name: 'Change password' }))

    expect(screen.getByRole('alert')).toHaveTextContent('at least 12')
    expect(changePassword).not.toHaveBeenCalled()
  })

  it('changes the password, signs the user out and leaves a message for the login page', async () => {
    vi.mocked(changePassword).mockResolvedValue(undefined)
    const logout = vi.fn()
    const user = userEvent.setup()
    renderPage(logout)
    await user.type(screen.getByLabelText('Current password'), 'old password value')
    await user.type(screen.getByLabelText('New password'), 'a brand new password')
    await user.type(screen.getByLabelText('Confirm new password'), 'a brand new password')
    await user.click(screen.getByRole('button', { name: 'Change password' }))

    expect(changePassword).toHaveBeenCalledWith('old password value', 'a brand new password')
    await vi.waitFor(() => expect(logout).toHaveBeenCalledTimes(1))
    expect(peekFlash()).toContain('password was changed')
  })

  it('shows the server error when the current password is wrong', async () => {
    vi.mocked(changePassword).mockRejectedValue(new Error('nope'))
    const user = userEvent.setup()
    renderPage()
    await user.type(screen.getByLabelText('Current password'), 'wrong password')
    await user.type(screen.getByLabelText('New password'), 'a brand new password')
    await user.type(screen.getByLabelText('Confirm new password'), 'a brand new password')
    await user.click(screen.getByRole('button', { name: 'Change password' }))

    expect(await screen.findByRole('alert')).toBeInTheDocument()
  })
})
