import { lazy, Suspense } from 'react'
import type { ReactNode } from 'react'
import { Route, Routes } from 'react-router-dom'
import AuthProvider from './auth/AuthProvider'
import RequireAuth from './auth/RequireAuth'
import RequireRole from './auth/RequireRole'
import AppLayout from './layouts/AppLayout'
import NotFoundPage from './pages/NotFoundPage'

const AccountPage = lazy(() => import('./pages/AccountPage'))
const BulkPredictPage = lazy(() => import('./pages/BulkPredictPage'))
const DashboardPage = lazy(() => import('./pages/DashboardPage'))
const DuplicatesPage = lazy(() => import('./pages/DuplicatesPage'))
const LoginPage = lazy(() => import('./pages/LoginPage'))
const ModelsPage = lazy(() => import('./pages/ModelsPage'))
const OverviewPage = lazy(() => import('./pages/OverviewPage'))
const ReportDetailPage = lazy(() => import('./pages/ReportDetailPage'))
const ReportsPage = lazy(() => import('./pages/ReportsPage'))
const SettingsPage = lazy(() => import('./pages/SettingsPage'))
const UploadPage = lazy(() => import('./pages/UploadPage'))
const TryItPage = lazy(() => import('./pages/TryItPage'))
const EvaluatePage = lazy(() => import('./pages/EvaluatePage'))
const UsersPage = lazy(() => import('./pages/UsersPage'))

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

// Sirf admin ke pages. (Server bhi inhein admin ke liye hi rokta hai.)
function AdminPage({ children }: { children: ReactNode }) {
  return (
    <RequireRole roles={['admin']}>
      <Page>{children}</Page>
    </RequireRole>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route
          path="login"
          element={
            <Page>
              <LoginPage />
            </Page>
          }
        />
        <Route
          element={
            <RequireAuth>
              <AppLayout />
            </RequireAuth>
          }
        >
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
              <AdminPage>
                <BulkPredictPage />
              </AdminPage>
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
              <AdminPage>
                <UploadPage />
              </AdminPage>
            }
          />
          <Route
            path="settings"
            element={
              <AdminPage>
                <SettingsPage />
              </AdminPage>
            }
          />
          <Route
            path="users"
            element={
              <AdminPage>
                <UsersPage />
              </AdminPage>
            }
          />
          <Route
            path="account"
            element={
              <Page>
                <AccountPage />
              </Page>
            }
          />
          <Route
            path="try"
            element={
              <Page>
                <TryItPage />
              </Page>
            }
          />
          <Route
            path="evaluate"
            element={
              <AdminPage>
                <EvaluatePage />
              </AdminPage>
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
    </AuthProvider>
  )
}
