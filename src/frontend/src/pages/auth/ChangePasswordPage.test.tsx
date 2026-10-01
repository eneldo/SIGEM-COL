import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { auth } from '../../lib/api'
import { useAuthStore } from '../../stores/authStore'
import { ChangePasswordPage } from './ChangePasswordPage'

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

const usuario = {
  id: 'u1',
  username: 'ana',
  email: 'ana@mun.co',
  nombre_completo: 'Ana Pérez',
  municipio_id: 'm1',
  roles: ['GESTOR'],
}

function renderPage() {
  return render(
    <MemoryRouter
      initialEntries={['/change-password']}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <Routes>
        <Route path="/change-password" element={<ChangePasswordPage />} />
        <Route path="/gestor/dashboard" element={<div>panel gestor</div>} />
        <Route path="/admin/dashboard" element={<div>panel admin</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

async function llenarFormulario(
  user: ReturnType<typeof userEvent.setup>,
  nueva: string,
  confirmacion = nueva,
) {
  await user.type(screen.getByLabelText('Contraseña Actual'), 'anterior')
  await user.type(screen.getByLabelText('Nueva Contraseña'), nueva)
  await user.type(screen.getByLabelText('Confirmar Nueva Contraseña'), confirmacion)
}

beforeEach(() => {
  localStorage.clear()
  mockedAuth.changePassword.mockReset()
  mockedAuth.getMe.mockReset()
  useAuthStore.setState({
    user: null,
    token: null,
    isAuthenticated: false,
    mustChangePassword: true,
    loginTimestamp: null,
    passwordChangeDismissed: false,
  })
})

describe('ChangePasswordPage', () => {
  it('renderiza el formulario con los tres campos', () => {
    renderPage()

    expect(screen.getByRole('heading', { name: 'Cambiar Contraseña' })).toBeInTheDocument()
    expect(screen.getByLabelText('Contraseña Actual')).toBeInTheDocument()
    expect(screen.getByLabelText('Nueva Contraseña')).toBeInTheDocument()
    expect(screen.getByLabelText('Confirmar Nueva Contraseña')).toBeInTheDocument()
    expect(screen.queryByText('Requisitos:')).toBeNull()
  })

  it('muestra requisitos y nivel de seguridad según la contraseña', async () => {
    const user = userEvent.setup()
    renderPage()

    await user.type(screen.getByLabelText('Nueva Contraseña'), 'abc')
    expect(screen.getByText('Débil')).toBeInTheDocument()
    expect(screen.getByText('Requisitos:')).toBeInTheDocument()
    expect(screen.getByText('Mínimo 8 caracteres')).toHaveClass('text-ink-faint')

    await user.clear(screen.getByLabelText('Nueva Contraseña'))
    await user.type(screen.getByLabelText('Nueva Contraseña'), 'Aaaaaaaa')
    expect(screen.getByText('Media')).toBeInTheDocument()

    await user.clear(screen.getByLabelText('Nueva Contraseña'))
    await user.type(screen.getByLabelText('Nueva Contraseña'), 'Aa1!aaaa')
    expect(screen.getByText('Fuerte')).toBeInTheDocument()
    expect(screen.getByText('Mínimo 8 caracteres')).toHaveClass('text-done')
    expect(screen.getByText('Una letra mayúscula')).toHaveClass('text-done')
    expect(screen.getByText('Una letra minúscula')).toHaveClass('text-done')
    expect(screen.getByText('Un número')).toHaveClass('text-done')
    expect(screen.getByText('Un carácter especial')).toHaveClass('text-done')
  })

  it('bloquea el envío cuando las contraseñas no coinciden', async () => {
    const user = userEvent.setup()
    renderPage()

    await llenarFormulario(user, 'NuevaClave123*', 'OtraClave123*')

    expect(screen.getByText('Las contraseñas no coinciden')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cambiar Contraseña' })).toBeDisabled()
  })

  it('cambia la contraseña y redirige al panel del gestor', async () => {
    const user = userEvent.setup()
    mockedAuth.changePassword.mockResolvedValue({} as never)
    mockedAuth.getMe.mockResolvedValue({ data: usuario } as never)
    localStorage.setItem('token', 'tok-1')
    renderPage()

    await llenarFormulario(user, 'NuevaClave123*')
    await user.click(screen.getByRole('button', { name: 'Cambiar Contraseña' }))

    expect(await screen.findByText('panel gestor')).toBeInTheDocument()
    expect(mockedAuth.changePassword).toHaveBeenCalledWith({
      current_password: 'anterior',
      new_password: 'NuevaClave123*',
      confirm_password: 'NuevaClave123*',
    })
    expect(mockedAuth.getMe).toHaveBeenCalledTimes(1)
    const state = useAuthStore.getState()
    expect(state.token).toBe('tok-1')
    expect(state.mustChangePassword).toBe(false)
    expect(state.user).toEqual(usuario)
  })

  it('redirige al panel de administración para roles administrativos', async () => {
    const user = userEvent.setup()
    mockedAuth.changePassword.mockResolvedValue({} as never)
    mockedAuth.getMe.mockResolvedValue({
      data: { ...usuario, roles: ['SUPERADMIN_PLATAFORMA'] },
    } as never)
    renderPage()

    await llenarFormulario(user, 'NuevaClave123*')
    await user.click(screen.getByRole('button', { name: 'Cambiar Contraseña' }))

    expect(await screen.findByText('panel admin')).toBeInTheDocument()
  })

  it('muestra el detalle del error devuelto por el API', async () => {
    const user = userEvent.setup()
    mockedAuth.changePassword.mockRejectedValue({
      response: { data: { detail: 'Contraseña actual incorrecta' } },
    } as never)
    renderPage()

    await llenarFormulario(user, 'NuevaClave123*')
    await user.click(screen.getByRole('button', { name: 'Cambiar Contraseña' }))

    expect(await screen.findByText('Contraseña actual incorrecta')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Cambiar Contraseña' })).toBeInTheDocument()
  })

  it('muestra un error genérico cuando la petición falla sin detalle', async () => {
    const user = userEvent.setup()
    mockedAuth.changePassword.mockRejectedValue(new Error('Network Error') as never)
    renderPage()

    await llenarFormulario(user, 'NuevaClave123*')
    await user.click(screen.getByRole('button', { name: 'Cambiar Contraseña' }))

    expect(await screen.findByText('Error al cambiar la contraseña.')).toBeInTheDocument()
  })
})
