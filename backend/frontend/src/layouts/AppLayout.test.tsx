import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import AppLayout from './AppLayout'

function renderLayout() {
  return render(
    <MemoryRouter>
      <AppLayout />
    </MemoryRouter>,
  )
}

describe('AppLayout', () => {
  it('opens and closes the menu with the menu button', async () => {
    const user = userEvent.setup()
    renderLayout()

    const openButton = screen.getByRole('button', { name: 'Open menu' })
    expect(openButton).toHaveAttribute('aria-expanded', 'false')

    await user.click(openButton)
    const closeButton = screen.getByRole('button', { name: 'Close menu' })
    expect(closeButton).toHaveAttribute('aria-expanded', 'true')

    await user.click(closeButton)
    expect(screen.getByRole('button', { name: 'Open menu' })).toHaveAttribute('aria-expanded', 'false')
  })

  it('links to every page in the sidebar', () => {
    renderLayout()
    expect(screen.getByRole('link', { name: 'Dashboard' })).toHaveAttribute('href', '/')
    expect(screen.getByRole('link', { name: 'Reports' })).toHaveAttribute('href', '/reports')
    expect(screen.getByRole('link', { name: 'Duplicates' })).toHaveAttribute('href', '/duplicates')
    expect(screen.getByRole('link', { name: 'Model performance' })).toHaveAttribute('href', '/models')
    expect(screen.getByRole('link', { name: 'Upload' })).toHaveAttribute('href', '/upload')
    expect(screen.getByRole('link', { name: 'Settings' })).toHaveAttribute('href', '/settings')
    expect(screen.getByRole('link', { name: 'System status' })).toHaveAttribute('href', '/status')
  })
})
