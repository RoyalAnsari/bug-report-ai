import { lazy, Suspense } from 'react'
import type { ReactNode } from 'react'
import { Route, Routes } from 'react-router-dom'
import AppLayout from './layouts/AppLayout'
import NotFoundPage from './pages/NotFoundPage'

const BulkPredictPage = lazy(() => import('./pages/BulkPredictPage'))
const DashboardPage = lazy(() => import('./pages/DashboardPage'))
const DuplicatesPage = lazy(() => import('./pages/DuplicatesPage'))
const ModelsPage = lazy(() => import('./pages/ModelsPage'))
const OverviewPage = lazy(() => import('./pages/OverviewPage'))
const ReportDetailPage = lazy(() => import('./pages/ReportDetailPage'))
const ReportsPage = lazy(() => import('./pages/ReportsPage'))
const SettingsPage = lazy(() => import('./pages/SettingsPage'))
const UploadPage = lazy(() => import('./pages/UploadPage'))

// Har page apne hisse (chunk) mein load hota hai. Layout (menu) hamesha nazar aata hai,
// sirf page ki jagah "Loading" dikhta hai.
function Page({ children }: { children: ReactNode }) {
  return (
    <Suspense
      fallback={
        <p role="status" className="p-6 text-sm text-slate-600">
          Loading...
        </p>
      }
    >
      {children}
    </Suspense>
  )
}

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route
          index
          element={
            <Page>
              <DashboardPage />
            </Page>
          }
        />
        <Route
          path="reports"
          element={
            <Page>
              <ReportsPage />
            </Page>
          }
        />
        <Route
          path="reports/:reportId"
          element={
            <Page>
              <ReportDetailPage />
            </Page>
          }
        />
        <Route
          path="predict"
          element={
            <Page>
              <BulkPredictPage />
            </Page>
          }
        />
        <Route
          path="duplicates"
          element={
            <Page>
              <DuplicatesPage />
            </Page>
          }
        />
        <Route
          path="models"
          element={
            <Page>
              <ModelsPage />
            </Page>
          }
        />
        <Route
          path="upload"
          element={
            <Page>
              <UploadPage />
            </Page>
          }
        />
        <Route
          path="settings"
          element={
            <Page>
              <SettingsPage />
            </Page>
          }
        />
        <Route
          path="status"
          element={
            <Page>
              <OverviewPage />
            </Page>
          }
        />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}
