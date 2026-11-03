import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { docsUrl } from '../services/api'

const navItems = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/reports', label: 'Reports', end: false },
  { to: '/duplicates', label: 'Duplicates', end: false },
  { to: '/models', label: 'Model performance', end: false },
  { to: '/upload', label: 'Upload', end: false },
  { to: '/settings', label: 'Settings', end: false },
  { to: '/status', label: 'System status', end: false },
]

function linkClass({ isActive }: { isActive: boolean }) {
  const tone = isActive ? 'bg-indigo-50 text-indigo-700' : 'text-slate-700 hover:bg-slate-100'
  return `block rounded-md px-3 py-2 text-sm font-medium ${tone}`
}

export default function AppLayout() {
  const [open, setOpen] = useState(false)

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
            {navItems.map((item) => (
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
          <a
            href={docsUrl}
            target="_blank"
            rel="noreferrer"
            className="ml-auto rounded-md px-3 py-1.5 text-sm font-medium text-indigo-700 hover:bg-indigo-50"
          >
            API docs
          </a>
        </header>
        <main className="mx-auto max-w-6xl p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
