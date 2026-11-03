import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <section>
      <h1 className="text-2xl font-semibold">Page not found</h1>
      <p className="mt-2 text-sm text-slate-600">This page does not exist.</p>
      <Link to="/" className="mt-4 inline-block text-sm font-medium text-indigo-700 hover:underline">
        Back to Overview
      </Link>
    </section>
  )
}
