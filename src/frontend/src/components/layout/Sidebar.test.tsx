import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { User } from '../../lib/types'
import { useAuthStore } from '../../stores/authStore'
import { Sidebar } from './Sidebar'

function RutaActual() {
  const location = useLocation()
  return <div>{location.pathname}</div>
}

function crearUsuario(overrides: Partial<User> = {}): User {
  return {
    id: 'u1',
    username: 'ana',
    email: 'ana@mun.co',
    nombre_completo: 'Ana Pérez',
    municipio_id: 'm1',
    roles: ['GESTOR'],
    ...overrides,
  }
}

function montarSidebar(user: User | null, entrada = '/admin/dashboard', open = true) {
  const onClose = vi.fn()
  useAuthStore.setState({ user })
  const utils = render(
    <MemoryRouter
      initialEntries={[entrada]}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <Sidebar open={open} onClose={onClose} />
      <RutaActual />
    </MemoryRouter>,
  )
  return { onClose, ...utils }
}

beforeEach(() => {
  useAuthStore.setState({
    user: null,
    token: null,
    isAuthenticated: false,
    mustChangePassword: false,
    loginTimestamp: null,
    passwordChangeDismissed: false,
  })
})

describe('Sidebar', () => {
  it('lista los enlaces del panel de administración', () => {
    montarSidebar(crearUsuario({ roles: ['ADMINISTRADOR_MUNICIPAL'] }))

    const nav = screen.getByRole('navigation', { name: 'Navegación principal' })
    const etiquetas = [
      'Dashboard',
      'Gestores Líderes / Coordinadores',
      'Líneas',
      'Programas',
      'Productos',
      'Reportes',
      'Cumplimiento',
      'Revisión de Avances',
      'Dependencias',
      'Configuración',
    ]
    for (const etiqueta of etiquetas) {
      expect(within(nav).getByRole('link', { name: etiqueta })).toBeInTheDocument()
    }
    expect(within(nav).queryByRole('link', { name: 'Mis Productos' })).toBeNull()
  })

  it('lista los enlaces de coordinación para un gestor líder', () => {
    montarSidebar(crearUsuario({ roles: ['GESTOR_LIDER'] }))

    const nav = screen.getByRole('navigation', { name: 'Navegación principal' })
    expect(within(nav).getByRole('link', { name: 'Coordinación de Equipo' })).toBeInTheDocument()
    expect(within(nav).getByRole('link', { name: 'Asignar Responsables' })).toBeInTheDocument()
    expect(within(nav).getByRole('link', { name: 'Mis Avances' })).toBeInTheDocument()
    expect(within(nav).getByRole('link', { name: 'Revisión de Avances' })).toHaveAttribute(
      'href',
      '/gestor/revision-avances',
    )
    expect(within(nav).queryByRole('link', { name: 'Mis Productos' })).toBeNull()
    expect(within(nav).queryByRole('link', { name: 'Configuración' })).toBeNull()
  })

  it('lista los enlaces propios de un gestor', () => {
    montarSidebar(crearUsuario())

    const nav = screen.getByRole('navigation', { name: 'Navegación principal' })
    expect(within(nav).getByRole('link', { name: 'Mis Productos' })).toBeInTheDocument()
    expect(within(nav).getByRole('link', { name: 'Registro de Avance' })).toBeInTheDocument()
    expect(within(nav).getByRole('link', { name: 'Mis Pendientes' })).toBeInTheDocument()
    expect(within(nav).getByRole('link', { name: 'Mis Alertas' })).toBeInTheDocument()
    expect(within(nav).queryByRole('link', { name: 'Coordinación de Equipo' })).toBeNull()
  })

  it('marca el enlace activo de la ruta actual', () => {
    montarSidebar(crearUsuario({ roles: ['ADMINISTRADOR_MUNICIPAL'] }), '/admin/dashboard')

    const activo = screen.getByRole('link', { name: 'Dashboard' })
    const inactivo = screen.getByRole('link', { name: 'Líneas' })
    expect(activo).toHaveAttribute('aria-current', 'page')
    expect(activo).toHaveClass('bg-white')
    expect(inactivo).not.toHaveAttribute('aria-current')
    expect(inactivo).toHaveClass('text-white/70')
  })

  it('oculta el fondo y desplaza el panel cuando está cerrado', () => {
    const { container } = montarSidebar(crearUsuario(), '/admin/dashboard', false)

    expect(container.querySelector('aside')).toHaveClass('-translate-x-full')
    expect(container.querySelector('[class*="bg-black/50"]')).toBeNull()
  })

  it('muestra el panel a ras y el fondo cuando está abierto', () => {
    const { container } = montarSidebar(crearUsuario(), '/admin/dashboard', true)

    expect(container.querySelector('aside')).toHaveClass('translate-x-0')
    expect(container.querySelector('[class*="bg-black/50"]')).not.toBeNull()
  })

  it('cierra el menú al pulsar el fondo oscuro', async () => {
    const user = userEvent.setup()
    const { onClose, container } = montarSidebar(crearUsuario(), '/admin/dashboard', true)

    await user.click(container.querySelector('[class*="bg-black/50"]') as Element)

    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('cierra el menú y navega al pulsar un enlace', async () => {
    const user = userEvent.setup()
    const { onClose } = montarSidebar(
      crearUsuario({ roles: ['ADMINISTRADOR_MUNICIPAL'] }),
      '/admin/dashboard',
    )

    await user.click(screen.getByRole('link', { name: 'Líneas' }))

    expect(onClose).toHaveBeenCalledTimes(1)
    expect(await screen.findByText('/admin/lineas')).toBeInTheDocument()
  })

  it('muestra los datos del usuario en el pie del panel', () => {
    montarSidebar(crearUsuario({ roles: ['ADMINISTRADOR_MUNICIPAL'] }))

    expect(screen.getByText('Ana Pérez')).toBeInTheDocument()
    expect(screen.getByText('AP')).toBeInTheDocument()
    expect(screen.getByText('Administrador')).toBeInTheDocument()
  })

  it('describe al gestor líder como coordinador', () => {
    montarSidebar(crearUsuario({ roles: ['GESTOR_LIDER'] }))

    expect(screen.getByText('Coordinador')).toBeInTheDocument()
  })

  it('describe al gestor sin rol de coordinación', () => {
    montarSidebar(crearUsuario())

    expect(screen.getByText('Gestor')).toBeInTheDocument()
  })

  it('usa valores por defecto cuando no hay usuario en sesión', () => {
    montarSidebar(null)

    expect(screen.getByText('Usuario')).toBeInTheDocument()
    expect(screen.getByText('U')).toBeInTheDocument()
    expect(screen.getByText('Gestor')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Mis Productos' })).toBeInTheDocument()
  })
})
