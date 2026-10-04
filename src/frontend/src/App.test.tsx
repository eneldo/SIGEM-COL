import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import type { User } from './lib/types'
import { useAuthStore } from './stores/authStore'

vi.mock('./lib/api', () => ({
  auth: {
    login: vi.fn(),
    logout: vi.fn(),
    getMe: vi.fn(),
    changePassword: vi.fn(),
  },
  default: {},
}))

vi.mock('./pages/auth/LoginPage', () => ({ LoginPage: () => <div>pagina login</div> }))
vi.mock('./pages/auth/ChangePasswordPage', () => ({
  ChangePasswordPage: () => <div>pagina cambio clave</div>,
}))
vi.mock('./pages/admin/DashboardAdmin', () => ({
  DashboardAdmin: () => <div>pagina dashboard admin</div>,
}))
vi.mock('./pages/admin/GestoresPage', () => ({ GestoresPage: () => <div>pagina gestores</div> }))
vi.mock('./pages/admin/LineasPage', () => ({ LineasPage: () => <div>pagina lineas</div> }))
vi.mock('./pages/admin/ProgramasPage', () => ({ ProgramasPage: () => <div>pagina programas</div> }))
vi.mock('./pages/admin/ProductosPage', () => ({ ProductosPage: () => <div>pagina productos</div> }))
vi.mock('./pages/admin/ConfiguracionPage', () => ({
  ConfiguracionPage: () => <div>pagina configuracion</div>,
}))
vi.mock('./pages/admin/UsuariosPage', () => ({ UsuariosPage: () => <div>pagina usuarios</div> }))
vi.mock('./pages/admin/RolesPage', () => ({ RolesPage: () => <div>pagina roles</div> }))
vi.mock('./pages/admin/AuditoriaPage', () => ({ AuditoriaPage: () => <div>pagina auditoria</div> }))
vi.mock('./pages/admin/PersonalizacionPage', () => ({
  PersonalizacionPage: () => <div>pagina personalizacion</div>,
}))
vi.mock('./pages/admin/DependenciasPage', () => ({
  default: () => <div>pagina dependencias</div>,
}))
vi.mock('./pages/admin/ReportesPage', () => ({ default: () => <div>pagina reportes</div> }))
vi.mock('./pages/admin/CumplimientoPage', () => ({
  default: () => <div>pagina cumplimiento</div>,
}))
vi.mock('./pages/gestor/DashboardGestor', () => ({
  DashboardGestor: () => <div>pagina dashboard gestor</div>,
}))
vi.mock('./pages/gestor/MisProductosPage', () => ({
  MisProductosPage: () => <div>pagina mis productos</div>,
}))
vi.mock('./pages/gestor/GestorDashboardPage', () => ({
  GestorDashboardPage: () => <div>pagina gestor dashboard</div>,
}))
vi.mock('./pages/gestor/GestorEquipoPage', () => ({ default: () => <div>pagina equipo</div> }))
vi.mock('./pages/gestor/GestorAsignarPage', () => ({ default: () => <div>pagina asignar</div> }))
vi.mock('./pages/gestor/RegistroAvancePage', () => ({
  default: () => <div>pagina registro avance</div>,
}))
vi.mock('./pages/gestor/RevisionAvancesPage', () => ({
  default: () => <div>pagina revision avances</div>,
}))

const usuarioGestor: User = {
  id: 'u1',
  username: 'ana',
  email: 'ana@mun.co',
  nombre_completo: 'Ana Pérez',
  municipio_id: 'm1',
  roles: ['GESTOR'],
}

const usuarioAdmin: User = { ...usuarioGestor, roles: ['ADMINISTRADOR_MUNICIPAL'] }
const usuarioGestorLider: User = { ...usuarioGestor, roles: ['GESTOR_LIDER'] }

function iniciarSesion(user: User | null, mustChangePassword = false) {
  useAuthStore.setState({
    user,
    token: user ? 'tok-1' : null,
    isAuthenticated: user !== null,
    mustChangePassword,
    loginTimestamp: user ? Date.now() : null,
    passwordChangeDismissed: false,
  })
}

function montarApp(ruta: string) {
  window.history.replaceState({}, '', ruta)
  return render(<App />)
}

const rutasAdministrador: Array<[string, string]> = [
  ['/admin/dashboard', 'pagina dashboard admin'],
  ['/admin/gestores', 'pagina gestores'],
  ['/admin/lineas', 'pagina lineas'],
  ['/admin/programas', 'pagina programas'],
  ['/admin/productos', 'pagina productos'],
  ['/admin/reportes', 'pagina reportes'],
  ['/admin/cumplimiento', 'pagina cumplimiento'],
  ['/admin/revision-avances', 'pagina revision avances'],
  ['/admin/configuracion', 'pagina configuracion'],
  ['/admin/configuracion/usuarios', 'pagina usuarios'],
  ['/admin/configuracion/dependencias', 'pagina dependencias'],
  ['/admin/configuracion/roles', 'pagina roles'],
  ['/admin/configuracion/auditoria', 'pagina auditoria'],
  ['/admin/configuracion/personalizacion', 'pagina personalizacion'],
]

const rutasGestor: Array<[string, string]> = [
  ['/gestor/dashboard', 'pagina dashboard gestor'],
  ['/gestor/equipo', 'pagina equipo'],
  ['/gestor/asignar', 'pagina asignar'],
  ['/gestor/productos', 'pagina mis productos'],
  ['/gestor/registro-avance', 'pagina registro avance'],
  ['/gestor/mis-avances', 'pagina gestor dashboard'],
  ['/gestor/mis-pendientes', 'pagina gestor dashboard'],
  ['/gestor/mis-alertas', 'pagina gestor dashboard'],
  ['/gestor/cumplimiento', 'pagina cumplimiento'],
  ['/gestor/reportes', 'pagina reportes'],
]

beforeEach(() => {
  window.history.replaceState({}, '', '/')
  localStorage.clear()
  useAuthStore.setState({
    user: null,
    token: null,
    isAuthenticated: false,
    mustChangePassword: false,
    loginTimestamp: null,
    passwordChangeDismissed: false,
  })
})

describe('ProtectedRoute', () => {
  it('redirige al login cuando no hay sesión', async () => {
    iniciarSesion(null)
    montarApp('/admin/dashboard')

    expect(await screen.findByText('pagina login')).toBeInTheDocument()
    expect(window.location.pathname).toBe('/login')
  })

  it('redirige al cambio de contraseña cuando debe renovarla', async () => {
    iniciarSesion(usuarioAdmin, true)
    montarApp('/admin/dashboard')

    expect(await screen.findByText('pagina cambio clave')).toBeInTheDocument()
    expect(window.location.pathname).toBe('/change-password')
  })

  it('permite el acceso con el rol requerido', async () => {
    iniciarSesion(usuarioAdmin)
    montarApp('/gestor/configuracion')

    expect(await screen.findByText('pagina configuracion')).toBeInTheDocument()
    expect(window.location.pathname).toBe('/gestor/configuracion')
  })

  it('permite al gestor líder revisar avances', async () => {
    iniciarSesion(usuarioGestorLider)
    montarApp('/gestor/revision-avances')

    expect(await screen.findByText('pagina revision avances')).toBeInTheDocument()
    expect(window.location.pathname).toBe('/gestor/revision-avances')
  })

  it('impide al gestor revisar avances', async () => {
    iniciarSesion(usuarioGestor)
    montarApp('/gestor/revision-avances')

    expect(await screen.findByText('pagina dashboard gestor')).toBeInTheDocument()
    expect(window.location.pathname).toBe('/gestor/dashboard')
  })

  it('redirige al panel del gestor cuando el rol no alcanza', async () => {
    iniciarSesion(usuarioGestor)
    montarApp('/gestor/configuracion')

    expect(await screen.findByText('pagina dashboard gestor')).toBeInTheDocument()
    expect(window.location.pathname).toBe('/gestor/dashboard')
  })

  it('protege también las dependencias de configuración del gestor', async () => {
    iniciarSesion(usuarioGestor)
    montarApp('/gestor/configuracion/dependencias')

    expect(await screen.findByText('pagina dashboard gestor')).toBeInTheDocument()
    expect(window.location.pathname).toBe('/gestor/dashboard')
  })

  it('permite a un administrador gestionar las dependencias del gestor', async () => {
    iniciarSesion(usuarioAdmin)
    montarApp('/gestor/configuracion/dependencias')

    expect(await screen.findByText('pagina dependencias')).toBeInTheDocument()
    expect(window.location.pathname).toBe('/gestor/configuracion/dependencias')
  })
})

describe('RootRedirect', () => {
  it('envía al login desde la raíz sin sesión', async () => {
    iniciarSesion(null)
    montarApp('/')

    expect(await screen.findByText('pagina login')).toBeInTheDocument()
    expect(window.location.pathname).toBe('/login')
  })

  it('envía al cambio de contraseña desde la raíz', async () => {
    iniciarSesion(usuarioGestor, true)
    montarApp('/')

    expect(await screen.findByText('pagina cambio clave')).toBeInTheDocument()
    expect(window.location.pathname).toBe('/change-password')
  })

  it('envía a un administrador a su panel', async () => {
    iniciarSesion(usuarioAdmin)
    montarApp('/')

    expect(await screen.findByText('pagina dashboard admin')).toBeInTheDocument()
    expect(window.location.pathname).toBe('/admin/dashboard')
  })

  it('envía a un gestor a su panel', async () => {
    iniciarSesion(usuarioGestor)
    montarApp('/')

    expect(await screen.findByText('pagina dashboard gestor')).toBeInTheDocument()
    expect(window.location.pathname).toBe('/gestor/dashboard')
  })

  it('aplica el redirect a rutas desconocidas', async () => {
    iniciarSesion(usuarioAdmin)
    montarApp('/ruta-inexistente')

    expect(await screen.findByText('pagina dashboard admin')).toBeInTheDocument()
    expect(window.location.pathname).toBe('/admin/dashboard')
  })
})

describe('rutas públicas', () => {
  it('renderiza la página de acceso', async () => {
    iniciarSesion(null)
    montarApp('/login')

    expect(await screen.findByText('pagina login')).toBeInTheDocument()
    expect(window.location.pathname).toBe('/login')
  })

  it('renderiza el cambio de contraseña con la sesión exigida', async () => {
    iniciarSesion(usuarioGestor, true)
    montarApp('/change-password')

    expect(await screen.findByText('pagina cambio clave')).toBeInTheDocument()
    expect(window.location.pathname).toBe('/change-password')
  })

  it('redirige al login si se entra al cambio de contraseña sin sesión', async () => {
    iniciarSesion(null)
    montarApp('/change-password')

    expect(await screen.findByText('pagina login')).toBeInTheDocument()
    expect(window.location.pathname).toBe('/login')
  })
})

describe('rutas del administrador', () => {
  it.each(rutasAdministrador)('renderiza %s con sesión de administrador', async (ruta, texto) => {
    iniciarSesion(usuarioAdmin)
    montarApp(ruta)

    expect(await screen.findByText(texto)).toBeInTheDocument()
    expect(window.location.pathname).toBe(ruta)
    expect(screen.getByText('Administración municipal')).toBeInTheDocument()
  })
})

describe('rutas del gestor', () => {
  it.each(rutasGestor)('renderiza %s con sesión de gestor', async (ruta, texto) => {
    iniciarSesion(usuarioGestor)
    montarApp(ruta)

    expect(await screen.findByText(texto)).toBeInTheDocument()
    expect(window.location.pathname).toBe(ruta)
    expect(screen.getByText('Gestión de productos')).toBeInTheDocument()
  })
})
