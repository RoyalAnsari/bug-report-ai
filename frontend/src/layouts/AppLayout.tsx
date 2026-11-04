import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'
import { docsUrl } from '../services/api'

const navItems = [
  { to: '/', label: 'Dashboard', end: true, adminOnly: false, needsLogin: false },
  { to: '/reports', label: 'Reports', end: false, adminOnly: false, needsLogin: false },
  { to: '/predict', label: 'Bulk predict', end: false, adminOnly: true, needsLogin: false },
  { to: '/duplicates', label: 'Duplicates', end: false, adminOnly: false, needsLogin: false },
  { to: '/models', label: 'Model performance', end: false, adminOnly: false, needsLogin: false },
  { to: '/upload', label: 'Upload', end: false, adminOnly: true, needsLogin: false },
  { to: '/settings', label: 'Settings', end: false, adminOnly: true, needsLogin: false },
  { to: '/users', label: 'Users', end: false, adminOnly: true, needsLogin: true },
  { to: '/status', label: 'System status', end: false, adminOnly: false, needsLogin: false },
  { to: '/account', label: 'Account', end: false, adminOnly: false, needsLogin: true },
]

// Production mein /docs band ho to VITE_SHOW_API_DOCS=false rakhein, taake link na dikhe.
const showDocsLink = import.meta.env.VITE_SHOW_API_DOCS !== 'false'

function linkClass({ isActive }: { isActive: boolean }) {
  const tone = isActive ? 'bg-indigo-50 text-indigo-700' : 'text-slate-700 hover:bg-slate-100'
  return `block rounded-md px-3 py-2 text-sm font-medium ${tone}`
}

export default function AppLayout() {
  const [open, setOpen] = useState(false)
  const auth = useAuth()
  const isAdmin = auth.user?.role === 'admin'
  const visibleItems = navItems.filter(
    (item) => (!item.adminOnly || isAdmin) && (!item.needsLogin || auth.authEnabled),
  )

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <aside
        id="sidebar"
        className={`fixed inset-y-0 left-0 z-30 w-64 transform border-r border-slate-200 bg-white p-4 transition-transform md:translate-x-0 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="mb-6 px-3 text-lg font-semibold">Bug Report AI</div>
        <nav aria-label="Main">
          <ul className="space-y-1">
            {visibleItems.map((item) => (
              <li key={item.to}>
                <NavLink to={item.to} end={item.end} className={linkClass} onClick={() => setOpen(false)}>
                  {item.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
      </aside>

      {open && (
        <div className="fixed inset-0 z-20 bg-black/30 md:hidden" onClick={() => setOpen(false)} aria-hidden="true" />
      )}

      <div className="md:pl-64">
        <header className="sticky top-0 z-10 flex h-14 items-center gap-3 border-b border-slate-200 bg-white px-4">
          <button
            type="button"
            className="rounded-md px-2 py-1 text-xl text-slate-700 hover:bg-slate-100 md:hidden"
            aria-label={open ? 'Close menu' : 'Open menu'}
            aria-expanded={open}
            aria-controls="sidebar"
            onClick={() => setOpen((value) => !value)}
          >
            ☰
          </button>
          <span className="font-medium md:hidden">Bug Report AI</span>
          <div className="ml-auto flex items-center gap-2">
            {auth.authEnabled && auth.user && (
              <>
                <span className="hidden text-sm text-slate-600 sm:inline">
                  {auth.user.name} ({auth.user.role})
                </span>
                <button
                  type="button"
                  onClick={auth.logout}
                  className="rounded-md px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100"
                >
                  Sign out
                </button>
              </>
            )}
            {showDocsLink && (
              <a
                href={docsUrl}
                target="_blank"
                rel="noreferrer"
                className="rounded-md px-3 py-1.5 text-sm font-medium text-indigo-700 hover:bg-indigo-50"
              >
                API docs
              </a>
            )}
          </div>
        </header>
        <main className="mx-auto max-w-6xl p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
