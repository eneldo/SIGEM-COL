import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { auth } from '../lib/api'
import type { User } from '../lib/types'
import { useAuthStore } from '../stores/authStore'
import { PasswordChangeModal } from './PasswordChangeModal'

vi.mock('../lib/api', () => ({
  auth: {
    login: vi.fn(),
    logout: vi.fn(),
    getMe: vi.fn(),
    changePassword: vi.fn(),
  },
  default: {},
}))

const mockedAuth = vi.mocked(auth)

const usuario: User = {
  id: 'u1',
  username: 'ana',
  email: 'ana@mun.co',
  nombre_completo: 'Ana Pérez',
  municipio_id: 'm1',
  roles: ['GESTOR'],
  must_change_password: false,
}

function prepararEstado(
  opciones: { exigido?: boolean; transcurrido?: number; descartado?: boolean } = {},
) {
  const { exigido = false, transcurrido = 0, descartado = false } = opciones
  useAuthStore.setState({
    isAuthenticated: true,
    mustChangePassword: exigido,
    loginTimestamp: transcurrido > 0 ? Date.now() - transcurrido : null,
    passwordChangeDismissed: descartado,
  })
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
  useAuthStore.setState({
    user: null,
    token: null,
    isAuthenticated: false,
    mustChangePassword: false,
    loginTimestamp: null,
    passwordChangeDismissed: false,
  })
})

describe('apertura del modal', () => {
  it('no se muestra sin requisito de cambio de contraseña', () => {
    const { container } = render(<PasswordChangeModal />)

    expect(container).toBeEmptyDOMElement()
  })

  it('permanece oculto antes del primer recordatorio', () => {
    prepararEstado({ exigido: true, transcurrido: 60_000 })

    const { container } = render(<PasswordChangeModal />)

    expect(container).toBeEmptyDOMElement()
  })

  it('se muestra como recomendación entre cinco y diez minutos', () => {
    prepararEstado({ exigido: true, transcurrido: 6 * 60 * 1000 })

    render(<PasswordChangeModal />)

    expect(
      screen.getByRole('heading', { name: 'Cambiar Contraseña' }),
    ).toBeInTheDocument()
    expect(
      screen.getByText('Se recomienda cambiar su contraseña por seguridad.'),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        'Su contraseña temporal debe ser actualizada. Puede hacerlo ahora o más tarde.',
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Cambiar después' }),
    ).toBeInTheDocument()
  })

  it('se vuelve obligatorio después de diez minutos', () => {
    prepararEstado({ exigido: true, transcurrido: 11 * 60 * 1000 })

    render(<PasswordChangeModal />)

    expect(
      screen.getByText('Es obligatorio cambiar su contraseña para continuar.'),
    ).toBeInTheDocument()
    expect(screen.queryByText('Se recomienda cambiar su contraseña por seguridad.')).toBeNull()
    expect(screen.queryByRole('button', { name: 'Cambiar después' })).toBeNull()
  })

  it('permanece oculto si la recomendación ya fue descartada', () => {
    prepararEstado({ exigido: true, transcurrido: 6 * 60 * 1000, descartado: true })

    const { container } = render(<PasswordChangeModal />)

    expect(container).toBeEmptyDOMElement()
  })

  it('permanece oculto si no hay marca de tiempo de inicio', () => {
    prepararEstado({ exigido: true })

    const { container } = render(<PasswordChangeModal />)

    expect(container).toBeEmptyDOMElement()
  })
})

describe('teclado y descarte', () => {
  it('impide cerrar la ventana con Escape cuando es obligatorio', () => {
    prepararEstado({ exigido: true, transcurrido: 11 * 60 * 1000 })
    render(<PasswordChangeModal />)

    const escape = new KeyboardEvent('keydown', { key: 'Escape', cancelable: true })
    document.dispatchEvent(escape)
    const letra = new KeyboardEvent('keydown', { key: 'a', cancelable: true })
    document.dispatchEvent(letra)

    expect(escape.defaultPrevented).toBe(true)
    expect(letra.defaultPrevented).toBe(false)
  })

  it('no intercepta Escape cuando solo es una recomendación', () => {
    prepararEstado({ exigido: true, transcurrido: 6 * 60 * 1000 })
    render(<PasswordChangeModal />)

    const escape = new KeyboardEvent('keydown', { key: 'Escape', cancelable: true })
    document.dispatchEvent(escape)

    expect(escape.defaultPrevented).toBe(false)
  })

  it('descarta el recordatorio para más tarde', async () => {
    const user = userEvent.setup()
    prepararEstado({ exigido: true, transcurrido: 6 * 60 * 1000 })
    const { container } = render(<PasswordChangeModal />)

    await user.click(screen.getByRole('button', { name: 'Cambiar después' }))

    expect(useAuthStore.getState().passwordChangeDismissed).toBe(true)
    expect(container).toBeEmptyDOMElement()
  })
})

describe('formulario de cambio', () => {
  it('evalúa la fortaleza y los requisitos de la nueva contraseña', async () => {
    const user = userEvent.setup()
    prepararEstado({ exigido: true, transcurrido: 11 * 60 * 1000 })
    render(<PasswordChangeModal />)

    const nueva = screen.getByLabelText('Nueva Contraseña')
    await user.type(nueva, 'abc')
    expect(screen.getByText('Débil')).toBeInTheDocument()
    expect(screen.getByText('Mínimo 8 caracteres')).toHaveClass('text-ink-faint')

    await user.clear(nueva)
    await user.type(nueva, 'Aaaaaaaa')
    expect(screen.getByText('Media')).toBeInTheDocument()

    await user.clear(nueva)
    await user.type(nueva, 'Aa1!aaaa')
    expect(screen.getByText('Fuerte')).toBeInTheDocument()
    expect(screen.getByText('Mínimo 8 caracteres')).toHaveClass('text-done')
    expect(screen.getByText('Una letra mayúscula')).toHaveClass('text-done')
    expect(screen.getByText('Una letra minúscula')).toHaveClass('text-done')
    expect(screen.getByText('Un número')).toHaveClass('text-done')
    expect(screen.getByText('Un carácter especial')).toHaveClass('text-done')
  })

  it('señala la confirmación que no coincide y bloquea el envío', async () => {
    const user = userEvent.setup()
    prepararEstado({ exigido: true, transcurrido: 11 * 60 * 1000 })
    render(<PasswordChangeModal />)

    await llenarFormulario(user, 'NuevaClave123*', 'OtraClave123*')

    expect(screen.getByText('Las contraseñas no coinciden')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cambiar Contraseña' })).toBeDisabled()
  })

  it('muestra el error de contraseñas distintas al enviar el formulario', async () => {
    const user = userEvent.setup()
    prepararEstado({ exigido: true, transcurrido: 11 * 60 * 1000 })
    render(<PasswordChangeModal />)

    await llenarFormulario(user, 'NuevaClave123*', 'OtraClave123*')
    const formulario = screen
      .getByRole('button', { name: 'Cambiar Contraseña' })
      .closest('form') as HTMLFormElement
    fireEvent.submit(formulario)

    expect(await screen.findByText('Las contraseñas no coinciden.')).toBeInTheDocument()
    expect(mockedAuth.changePassword).not.toHaveBeenCalled()
  })

  it('bloquea el botón mientras se procesa la petición', async () => {
    const user = userEvent.setup()
    mockedAuth.changePassword.mockReturnValue(new Promise<never>(() => {}))
    prepararEstado({ exigido: true, transcurrido: 11 * 60 * 1000 })
    render(<PasswordChangeModal />)

    await llenarFormulario(user, 'NuevaClave123*')
    await user.click(screen.getByRole('button', { name: 'Cambiar Contraseña' }))

    const boton = await screen.findByRole('button', { name: 'Cambiar Contraseña' })
    expect(boton).toBeDisabled()
    expect(boton).toHaveAttribute('aria-busy', 'true')
    expect(mockedAuth.changePassword).toHaveBeenCalledTimes(1)
  })

  it('cambia la contraseña y cierra el modal', async () => {
    const user = userEvent.setup()
    mockedAuth.changePassword.mockResolvedValue({} as never)
    mockedAuth.getMe.mockResolvedValue({ data: usuario } as never)
    prepararEstado({ exigido: true, transcurrido: 11 * 60 * 1000 })
    const { container } = render(<PasswordChangeModal />)

    await llenarFormulario(user, 'NuevaClave123*')
    await user.click(screen.getByRole('button', { name: 'Cambiar Contraseña' }))

    await waitFor(() => expect(container).toBeEmptyDOMElement())
    expect(mockedAuth.changePassword).toHaveBeenCalledWith({
      current_password: 'anterior',
      new_password: 'NuevaClave123*',
      confirm_password: 'NuevaClave123*',
    })
    expect(mockedAuth.getMe).toHaveBeenCalledTimes(1)
    expect(useAuthStore.getState().mustChangePassword).toBe(false)
    expect(useAuthStore.getState().user).toEqual(usuario)
    expect(localStorage.getItem('user')).toBe(JSON.stringify(usuario))
  })

  it('muestra el detalle del error devuelto por el API', async () => {
    const user = userEvent.setup()
    mockedAuth.changePassword.mockRejectedValue({
      response: { data: { detail: 'Contraseña actual incorrecta' } },
    } as never)
    prepararEstado({ exigido: true, transcurrido: 11 * 60 * 1000 })
    render(<PasswordChangeModal />)

    await llenarFormulario(user, 'NuevaClave123*')
    await user.click(screen.getByRole('button', { name: 'Cambiar Contraseña' }))

    expect(await screen.findByText('Contraseña actual incorrecta')).toBeInTheDocument()
    expect(
      screen.getByRole('heading', { name: 'Cambiar Contraseña' }),
    ).toBeInTheDocument()
  })

  it('muestra un error genérico cuando la petición falla sin detalle', async () => {
    const user = userEvent.setup()
    mockedAuth.changePassword.mockRejectedValue(new Error('Network Error') as never)
    prepararEstado({ exigido: true, transcurrido: 11 * 60 * 1000 })
    render(<PasswordChangeModal />)

    await llenarFormulario(user, 'NuevaClave123*')
    await user.click(screen.getByRole('button', { name: 'Cambiar Contraseña' }))

    expect(
      await screen.findByText('Error al cambiar la contraseña.'),
    ).toBeInTheDocument()
  })
})
