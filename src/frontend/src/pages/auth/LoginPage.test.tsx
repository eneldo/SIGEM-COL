import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { auth } from '../../lib/api'
import { useAuthStore } from '../../stores/authStore'
import { LoginPage } from './LoginPage'

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

const usuarioGestor = {
  id: 'u1',
  username: 'ana',
  email: 'ana@mun.co',
  nombre_completo: 'Ana Pérez',
  municipio_id: 'm1',
  roles: ['GESTOR'],
}

const usuarioAdmin = { ...usuarioGestor, roles: ['ADMINISTRADOR_MUNICIPAL'] }

function renderLogin() {
  return render(
    <MemoryRouter
      initialEntries={['/login']}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/gestor/dashboard" element={<div>panel gestor</div>} />
        <Route path="/admin/dashboard" element={<div>panel admin</div>} />
        <Route path="/change-password" element={<div>cambio de clave</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

async function completarLogin(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText('Usuario'), 'ana')
  await user.type(screen.getByPlaceholderText('Ingrese su contraseña'), 'secreta')
  await user.click(screen.getByRole('button', { name: 'Ingresar' }))
}

beforeEach(() => {
  localStorage.clear()
  mockedAuth.login.mockReset()
  useAuthStore.setState({
    user: null,
    token: null,
    isAuthenticated: false,
    mustChangePassword: false,
    loginTimestamp: null,
    passwordChangeDismissed: false,
  })
})

describe('LoginPage', () => {
  it('renderiza el formulario de acceso', () => {
    renderLogin()

    expect(screen.getByRole('heading', { name: 'Iniciar Sesión' })).toBeInTheDocument()
    expect(screen.getByLabelText('Usuario')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Ingrese su contraseña')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Ingresar' })).toBeInTheDocument()
  })

  it('envía las credenciales y redirige al panel del gestor', async () => {
    const user = userEvent.setup()
    mockedAuth.login.mockResolvedValue({
      data: {
        access_token: 'tok-1',
        token_type: 'bearer',
        must_change_password: false,
        user: usuarioGestor,
      },
    } as never)
    renderLogin()

    await completarLogin(user)

    expect(await screen.findByText('panel gestor')).toBeInTheDocument()
    expect(mockedAuth.login).toHaveBeenCalledWith({ username: 'ana', password: 'secreta' })
    expect(localStorage.getItem('token')).toBe('tok-1')
  })

  it('redirige al panel de administración según el rol', async () => {
    const user = userEvent.setup()
    mockedAuth.login.mockResolvedValue({
      data: {
        access_token: 'tok-1',
        token_type: 'bearer',
        must_change_password: false,
        user: usuarioAdmin,
      },
    } as never)
    renderLogin()

    await completarLogin(user)

    expect(await screen.findByText('panel admin')).toBeInTheDocument()
  })

  it('redirige al cambio de contraseña cuando el backend lo exige', async () => {
    const user = userEvent.setup()
    mockedAuth.login.mockResolvedValue({
      data: {
        access_token: 'tok-1',
        token_type: 'bearer',
        must_change_password: true,
        user: usuarioGestor,
      },
    } as never)
    renderLogin()

    await completarLogin(user)

    expect(await screen.findByText('cambio de clave')).toBeInTheDocument()
  })

  it('muestra el detalle del error devuelto por el API', async () => {
    const user = userEvent.setup()
    mockedAuth.login.mockRejectedValue({
      response: { data: { detail: 'Usuario o contraseña inválidos' } },
    } as never)
    renderLogin()

    await completarLogin(user)

    expect(await screen.findByText('Usuario o contraseña inválidos')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Iniciar Sesión' })).toBeInTheDocument()
    expect(localStorage.getItem('token')).toBeNull()
  })

  it('muestra un error genérico cuando la petición falla sin detalle', async () => {
    const user = userEvent.setup()
    mockedAuth.login.mockRejectedValue(new Error('Network Error') as never)
    renderLogin()

    await completarLogin(user)

    expect(
      await screen.findByText('Credenciales incorrectas. Intente de nuevo.'),
    ).toBeInTheDocument()
  })

  it('alterna la visibilidad de la contraseña', async () => {
    const user = userEvent.setup()
    renderLogin()

    const campo = screen.getByPlaceholderText('Ingrese su contraseña')
    expect(campo).toHaveAttribute('type', 'password')

    await user.click(screen.getByRole('button', { name: 'Mostrar contraseña' }))
    expect(campo).toHaveAttribute('type', 'text')

    await user.click(screen.getByRole('button', { name: 'Ocultar contraseña' }))
    expect(campo).toHaveAttribute('type', 'password')
  })

  it('redirige directamente si ya hay sesión activa', () => {
    useAuthStore.setState({ isAuthenticated: true, user: usuarioGestor, token: 'tok-1' })

    renderLogin()

    expect(screen.getByText('panel gestor')).toBeInTheDocument()
  })

  it('redirige al cambio de contraseña si la sesión exige renovarla', () => {
    useAuthStore.setState({
      isAuthenticated: true,
      user: usuarioGestor,
      token: 'tok-1',
      mustChangePassword: true,
    })

    renderLogin()

    expect(screen.getByText('cambio de clave')).toBeInTheDocument()
  })
})
