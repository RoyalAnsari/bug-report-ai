import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthContext } from '../auth/context'
import { ADMIN, makeAuthState } from '../auth/testState'
import { createUser, listUsers, resetUserPassword, updateUser } from '../services/users'
import type { ManagedUser } from '../types/users'
import UsersPage from './UsersPage'

vi.mock('../services/users', () => ({
  listUsers: vi.fn(),
  createUser: vi.fn(),
  updateUser: vi.fn(),
  resetUserPassword: vi.fn(),
}))

const admin: ManagedUser = {
  id: 'usr_admin',
  email: 'admin@example.com',
  name: 'Admin',
  role: 'admin',
  is_active: true,
  created_at: null,
  last_login_at: null,
}

const reviewer: ManagedUser = {
  id: 'usr_rev',
  email: 'reviewer@example.com',
  name: 'Reviewer',
  role: 'reviewer',
  is_active: true,
  created_at: null,
  last_login_at: null,
}

function renderPage() {
  return render(
    <AuthContext.Provider value={makeAuthState({ user: ADMIN })}>
      <UsersPage />
    </AuthContext.Provider>,
  )
}

describe('UsersPage', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    vi.mocked(listUsers).mockResolvedValue([admin, reviewer])
  })

  it('lists the users', async () => {
    renderPage()
    expect(await screen.findByText('reviewer@example.com')).toBeInTheDocument()
    expect(screen.getByText('admin@example.com')).toBeInTheDocument()
  })

  it('does not let an admin change their own role or deactivate themselves', async () => {
    renderPage()
    expect(await screen.findByRole('button', { name: 'Deactivate Admin' })).toBeDisabled()
    expect(screen.getByRole('combobox', { name: 'Role for Admin' })).toBeDisabled()
  })

  it('deactivates another user', async () => {
    vi.mocked(updateUser).mockResolvedValue({ ...reviewer, is_active: false })
    const user = userEvent.setup()
    renderPage()

    await user.click(await screen.findByRole('button', { name: 'Deactivate Reviewer' }))

    expect(updateUser).toHaveBeenCalledWith('usr_rev', { is_active: false })
    expect(await screen.findByText('Deactivated')).toBeInTheDocument()
  })

  it('creates a user', async () => {
    vi.mocked(createUser).mockResolvedValue({ ...reviewer, id: 'usr_new', email: 'new@example.com', name: 'New Person' })
    const user = userEvent.setup()
    renderPage()
    await screen.findByText('reviewer@example.com')

    await user.type(screen.getByLabelText('Name'), 'New Person')
    await user.type(screen.getByLabelText('Email'), 'new@example.com')
    await user.type(screen.getByLabelText('Temporary password'), 'a very long password')
    await user.click(screen.getByRole('button', { name: 'Create user' }))

    expect(createUser).toHaveBeenCalledWith({
      email: 'new@example.com',
      name: 'New Person',
      role: 'reviewer',
      password: 'a very long password',
    })
    expect(await screen.findByRole('status')).toHaveTextContent('new@example.com')
  })

  it('refuses a short password when creating a user', async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByText('reviewer@example.com')

    await user.type(screen.getByLabelText('Name'), 'New Person')
    await user.type(screen.getByLabelText('Email'), 'new@example.com')
    await user.type(screen.getByLabelText('Temporary password'), 'short')
    await user.click(screen.getByRole('button', { name: 'Create user' }))

    expect(screen.getByRole('alert')).toHaveTextContent('at least 12')
    expect(createUser).not.toHaveBeenCalled()
  })

  it('resets another user password', async () => {
    vi.mocked(resetUserPassword).mockResolvedValue(undefined)
    const user = userEvent.setup()
    renderPage()

    await user.click(await screen.findByRole('button', { name: 'Reset password for Reviewer' }))
    await user.type(screen.getByLabelText('New password for Reviewer'), 'a brand new password')
    await user.click(screen.getByRole('button', { name: 'Save new password for Reviewer' }))

    expect(resetUserPassword).toHaveBeenCalledWith('usr_rev', 'a brand new password')
    expect(await screen.findByRole('status')).toHaveTextContent('reviewer@example.com')
  })
})
