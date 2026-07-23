import { Navigate, Route, Routes } from "react-router-dom"
import { AuthProvider } from "./context/AuthContext"
import { ProtectedRoute } from "./components/ProtectedRoute"
import { Layout } from "./components/Layout"
import { LoginPage } from "./pages/LoginPage"
import { WorkersPage } from "./pages/WorkersPage"
import { AttendancePage } from "./pages/AttendancePage"
import { PayrollPage } from "./pages/PayrollPage"

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/workers"
          element={
            <ProtectedRoute>
              <Layout>
                <WorkersPage />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/attendance"
          element={
            <ProtectedRoute>
              <Layout>
                <AttendancePage />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/payroll"
          element={
            <ProtectedRoute>
              <Layout>
                <PayrollPage />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/workers" replace />} />
      </Routes>
    </AuthProvider>
  )
}
