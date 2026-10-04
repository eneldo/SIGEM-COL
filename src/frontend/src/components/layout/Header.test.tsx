import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { auth } from '../../lib/api'
import type { User } from '../../lib/types'
import { useAuthStore } from '../../stores/authStore'
import { Header } from './Header'

vi.mock('../../lib/api', () => ({
  auth: {
    login: vi.fn(),
    logout: vi.fn(),
    getMe: vi.fn(),
    changePassword: vi.fn(),
  },
  default: {},
}))

const mockedAuth = vi.mocked(auth)

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

describe('Header', () => {
  it('muestra la identificación del usuario autenticado', () => {
    useAuthStore.setState({ user: crearUsuario(), isAuthenticated: true })

    render(<Header onMenuToggle={() => undefined} />)

    expect(screen.getByText('Ana Pérez')).toBeInTheDocument()
    expect(screen.getByText('ana@mun.co')).toBeInTheDocument()
    expect(screen.getByText('AP')).toBeInTheDocument()
  })

  it('muestra el título de administración para roles administrativos', () => {
    useAuthStore.setState({
      user: crearUsuario({ roles: ['ADMINISTRADOR_MUNICIPAL'] }),
      isAuthenticated: true,
    })

    render(<Header onMenuToggle={() => undefined} />)

    expect(screen.getByText('Administración municipal')).toBeInTheDocument()
    expect(screen.getByText('Sistema operativo')).toBeInTheDocument()
  })

  it('muestra el título de coordinación para gestores líderes', () => {
    useAuthStore.setState({
      user: crearUsuario({ roles: ['GESTOR_LIDER'] }),
      isAuthenticated: true,
    })

    render(<Header onMenuToggle={() => undefined} />)

    expect(screen.getByText('Coordinación de equipo')).toBeInTheDocument()
  })

  it('muestra el título de gestión para gestores sin liderazgo', () => {
    useAuthStore.setState({ user: crearUsuario(), isAuthenticated: true })

    render(<Header onMenuToggle={() => undefined} />)

    expect(screen.getByText('Gestión de productos')).toBeInTheDocument()
  })

  it('usa una inicial genérica cuando no hay usuario', () => {
    render(<Header onMenuToggle={() => undefined} />)

    expect(screen.getByText('U')).toBeInTheDocument()
    expect(screen.queryByText('Ana Pérez')).toBeNull()
    expect(screen.queryByText('ana@mun.co')).toBeNull()
  })

  it('notifica la apertura del menú de navegación', async () => {
    const user = userEvent.setup()
    const onMenuToggle = vi.fn()
    useAuthStore.setState({ user: crearUsuario(), isAuthenticated: true })

    render(<Header onMenuToggle={onMenuToggle} />)

    await user.click(screen.getByRole('button', { name: 'Abrir menú de navegación' }))

    expect(onMenuToggle).toHaveBeenCalledTimes(1)
  })

  it('cierra la sesión al pulsar el botón de salida', async () => {
    const user = userEvent.setup()
    mockedAuth.logout.mockResolvedValue({} as never)
    useAuthStore.setState({ user: crearUsuario(), isAuthenticated: true, token: 'tok-1' })

    render(<Header onMenuToggle={() => undefined} />)

    await user.click(screen.getByRole('button', { name: 'Cerrar sesión' }))

    await waitFor(() => expect(mockedAuth.logout).toHaveBeenCalledTimes(1))
    await waitFor(() => expect(useAuthStore.getState().isAuthenticated).toBe(false))
    expect(useAuthStore.getState().user).toBeNull()
  })
})
