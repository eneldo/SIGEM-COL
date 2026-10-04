import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useAuthStore } from '../../stores/authStore'
import { Layout } from './Layout'

vi.mock('../../lib/api', () => ({
  auth: {
    login: vi.fn(),
    logout: vi.fn(),
    getMe: vi.fn(),
    changePassword: vi.fn(),
  },
  default: {},
}))

function definirAncho(valor: number) {
  Object.defineProperty(window, 'innerWidth', {
    configurable: true,
    writable: true,
    value: valor,
  })
}

function montarLayout() {
  return render(
    <MemoryRouter
      initialEntries={['/']}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<div>contenido de salida</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  definirAncho(1024)
  useAuthStore.setState({
    user: null,
    token: null,
    isAuthenticated: false,
    mustChangePassword: false,
    loginTimestamp: null,
    passwordChangeDismissed: false,
  })
})

describe('Layout', () => {
  it('renderiza el sidebar, la cabecera y la salida de la ruta', () => {
    montarLayout()

    expect(screen.getByText('SIGEM')).toBeInTheDocument()
    expect(screen.getByRole('banner')).toBeInTheDocument()
    expect(screen.getByRole('main')).toBeInTheDocument()
    expect(screen.getByText('contenido de salida')).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Abrir menú de navegación' }),
    ).toBeInTheDocument()
  })

  it('arranca con el menú abierto en pantallas anchas', () => {
    definirAncho(1440)
    const { container } = montarLayout()

    expect(screen.getByRole('main').parentElement).toHaveClass('lg:ml-64')
    expect(container.querySelector('[class*="bg-black/50"]')).not.toBeNull()
  })

  it('arranca con el menú cerrado en pantallas estrechas', () => {
    definirAncho(800)
    const { container } = montarLayout()

    expect(screen.getByRole('main').parentElement).toHaveClass('lg:ml-0')
    expect(container.querySelector('[class*="bg-black/50"]')).toBeNull()
  })

  it('alterna el menú con el botón de la cabecera', async () => {
    const user = userEvent.setup()
    const { container } = montarLayout()

    expect(screen.getByRole('main').parentElement).toHaveClass('lg:ml-64')

    await user.click(screen.getByRole('button', { name: 'Abrir menú de navegación' }))

    expect(screen.getByRole('main').parentElement).toHaveClass('lg:ml-0')
    expect(container.querySelector('[class*="bg-black/50"]')).toBeNull()
  })

  it('cierra el menú al pulsar el fondo oscuro', async () => {
    const user = userEvent.setup()
    const { container } = montarLayout()

    await user.click(container.querySelector('[class*="bg-black/50"]') as Element)

    expect(screen.getByRole('main').parentElement).toHaveClass('lg:ml-0')
  })

  it('muestra el modal de cambio de contraseña cuando corresponde', () => {
    useAuthStore.setState({
      mustChangePassword: true,
      loginTimestamp: Date.now() - 11 * 60 * 1000,
      passwordChangeDismissed: false,
    })

    montarLayout()

    expect(
      screen.getByRole('heading', { name: 'Cambiar Contraseña' }),
    ).toBeInTheDocument()
    expect(
      screen.getByText('Es obligatorio cambiar su contraseña para continuar.'),
    ).toBeInTheDocument()
  })

  it('no muestra el modal de cambio de contraseña sin requisito', () => {
    montarLayout()

    expect(
      screen.queryByRole('heading', { name: 'Cambiar Contraseña' }),
    ).toBeNull()
  })
})
