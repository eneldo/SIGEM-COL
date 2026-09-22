import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import { Layout } from './components/layout/Layout'
import { LoginPage } from './pages/auth/LoginPage'
import { ChangePasswordPage } from './pages/auth/ChangePasswordPage'
import { DashboardAdmin } from './pages/admin/DashboardAdmin'
import { GestoresPage } from './pages/admin/GestoresPage'
import { LineasPage } from './pages/admin/LineasPage'
import { ProgramasPage } from './pages/admin/ProgramasPage'
import { ProductosPage } from './pages/admin/ProductosPage'
import { ConfiguracionPage } from './pages/admin/ConfiguracionPage'
import { UsuariosPage } from './pages/admin/UsuariosPage'
import { RolesPage } from './pages/admin/RolesPage'
import { AuditoriaPage } from './pages/admin/AuditoriaPage'
import { PersonalizacionPage } from './pages/admin/PersonalizacionPage'
import DependenciasPage from './pages/admin/DependenciasPage'
import ReportesPage from './pages/admin/ReportesPage'
import CumplimientoPage from './pages/admin/CumplimientoPage'
import { DashboardGestor } from './pages/gestor/DashboardGestor'
import { MisProductosPage } from './pages/gestor/MisProductosPage'
import { GestorDashboardPage } from './pages/gestor/GestorDashboardPage'
import GestorEquipoPage from './pages/gestor/GestorEquipoPage'
import GestorAsignarPage from './pages/gestor/GestorAsignarPage'
import RegistroAvancePage from './pages/gestor/RegistroAvancePage'
import RevisionAvancesPage from './pages/gestor/RevisionAvancesPage'

const adminRoles = ['SUPERADMIN_PLATAFORMA', 'ADMINISTRADOR_MUNICIPAL']
const isAdmin = (roles: string[]) => roles.some((role) => adminRoles.includes(role))

function ProtectedRoute({
  children,
  requiredRole,
  requirePasswordChange = false,
}: {
  children: React.ReactNode
  requiredRole?: string
  requirePasswordChange?: boolean
}) {
  const { isAuthenticated, user, mustChangePassword } = useAuthStore()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (mustChangePassword && !requirePasswordChange) {
    return <Navigate to="/change-password" replace />
  }

  if (requiredRole && user && !user.roles.includes(requiredRole)) {
    const fallback = isAdmin(user.roles) ? '/admin/dashboard' : '/gestor/dashboard'
    return <Navigate to={fallback} replace />
  }

  return <>{children}</>
}

function RootRedirect() {
  const { isAuthenticated, user, mustChangePassword } = useAuthStore()

  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (mustChangePassword) return <Navigate to="/change-password" replace />

  const role = user?.roles?.[0]
  if (role && adminRoles.includes(role)) return <Navigate to="/admin/dashboard" replace />
  return <Navigate to="/gestor/dashboard" replace />
}

export default function App() {
  return (
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route
          path="/change-password"
          element={
            <ProtectedRoute requirePasswordChange>
              <ChangePasswordPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route path="dashboard" element={<DashboardAdmin />} />
          <Route path="gestores" element={<GestoresPage />} />
          <Route path="lineas" element={<LineasPage />} />
          <Route path="programas" element={<ProgramasPage />} />
          <Route path="productos" element={<ProductosPage />} />
          <Route path="reportes" element={<ReportesPage />} />
          <Route path="cumplimiento" element={<CumplimientoPage />} />
          <Route path="revision-avances" element={<RevisionAvancesPage />} />
          <Route path="configuracion" element={<ConfiguracionPage />} />
          <Route path="configuracion/usuarios" element={<UsuariosPage />} />
          <Route path="configuracion/dependencias" element={<DependenciasPage />} />
          <Route path="configuracion/roles" element={<RolesPage />} />
          <Route path="configuracion/auditoria" element={<AuditoriaPage />} />
          <Route path="configuracion/personalizacion" element={<PersonalizacionPage />} />
        </Route>

        <Route
          path="/gestor"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route path="dashboard" element={<DashboardGestor />} />
          <Route path="equipo" element={<GestorEquipoPage />} />
          <Route path="asignar" element={<GestorAsignarPage />} />
          <Route path="productos" element={<MisProductosPage />} />
          <Route path="registro-avance" element={<RegistroAvancePage />} />
          <Route path="revision-avances" element={<RevisionAvancesPage />} />
          <Route path="mis-avances" element={<GestorDashboardPage />} />
        </Route>

        <Route path="/" element={<RootRedirect />} />
        <Route path="*" element={<RootRedirect />} />
      </Routes>
    </Router>
  )
}
