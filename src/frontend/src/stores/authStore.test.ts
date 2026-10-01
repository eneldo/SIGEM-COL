import { beforeEach, describe, expect, it, vi } from 'vitest'
import { auth } from '../lib/api'
import { useAuthStore } from './authStore'
import type { User } from '../lib/types'

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

const user: User = {
  id: 'u1',
  username: 'ana',
  email: 'ana@mun.co',
  nombre_completo: 'Ana Pérez',
  municipio_id: 'm1',
  roles: ['GESTOR'],
}

const loginResponse = {
  data: {
    access_token: 'tok-1',
    token_type: 'bearer',
    must_change_password: false,
    user,
  },
}

function resetState() {
  useAuthStore.setState({
    user: null,
    token: null,
    isAuthenticated: false,
    mustChangePassword: false,
    loginTimestamp: null,
    passwordChangeDismissed: false,
  })
}

beforeEach(() => {
  localStorage.clear()
  resetState()
})

describe('login', () => {
  it('envía credenciales y persiste la sesión', async () => {
    mockedAuth.login.mockResolvedValue(loginResponse as never)

    await useAuthStore.getState().login('ana', 'secreta')

    expect(mockedAuth.login).toHaveBeenCalledWith({ username: 'ana', password: 'secreta' })
    const state = useAuthStore.getState()
    expect(state.isAuthenticated).toBe(true)
    expect(state.token).toBe('tok-1')
    expect(state.user).toEqual(user)
    expect(state.mustChangePassword).toBe(false)
    expect(state.loginTimestamp).toEqual(expect.any(Number))
    expect(localStorage.getItem('token')).toBe('tok-1')
    expect(localStorage.getItem('user')).toBe(JSON.stringify(user))
  })

  it('marca mustChangePassword cuando el backend lo solicita', async () => {
    mockedAuth.login.mockResolvedValue({
      data: { ...loginResponse.data, must_change_password: true },
    } as never)

    await useAuthStore.getState().login('ana', 'secreta')

    expect(useAuthStore.getState().mustChangePassword).toBe(true)
  })

  it('propaga el error y no altera el estado cuando falla', async () => {
    mockedAuth.login.mockRejectedValue(new Error('bad credentials') as never)

    await expect(useAuthStore.getState().login('ana', 'mala')).rejects.toThrow('bad credentials')

    const state = useAuthStore.getState()
    expect(state.isAuthenticated).toBe(false)
    expect(state.token).toBeNull()
    expect(localStorage.getItem('token')).toBeNull()
  })
})

describe('logout', () => {
  it('limpia storage y estado', async () => {
    localStorage.setItem('token', 'tok-1')
    localStorage.setItem('user', JSON.stringify(user))
    useAuthStore.setState({ token: 'tok-1', user, isAuthenticated: true })
    mockedAuth.logout.mockResolvedValue({} as never)

    await useAuthStore.getState().logout()

    expect(mockedAuth.logout).toHaveBeenCalledTimes(1)
    expect(localStorage.getItem('token')).toBeNull()
    expect(localStorage.getItem('user')).toBeNull()
    const state = useAuthStore.getState()
    expect(state.isAuthenticated).toBe(false)
    expect(state.token).toBeNull()
    expect(state.user).toBeNull()
    expect(state.mustChangePassword).toBe(false)
    expect(state.loginTimestamp).toBeNull()
  })

  it('limpia la sesión aunque el API falle', async () => {
    localStorage.setItem('token', 'tok-1')
    useAuthStore.setState({ token: 'tok-1', isAuthenticated: true })
    mockedAuth.logout.mockRejectedValue(new Error('network') as never)

    await useAuthStore.getState().logout()

    expect(localStorage.getItem('token')).toBeNull()
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
  })
})

describe('setToken y setUser', () => {
  it('setToken guarda en estado y localStorage', () => {
    useAuthStore.getState().setToken('tok-nuevo')

    expect(useAuthStore.getState().token).toBe('tok-nuevo')
    expect(localStorage.getItem('token')).toBe('tok-nuevo')
  })

  it('setUser guarda en estado y localStorage', () => {
    useAuthStore.getState().setUser(user)

    expect(useAuthStore.getState().user).toEqual(user)
    expect(localStorage.getItem('user')).toBe(JSON.stringify(user))
  })
})

describe('checkAuth', () => {
  it('sin token marca la sesión como inválida sin llamar al API', async () => {
    await useAuthStore.getState().checkAuth()

    expect(mockedAuth.getMe).not.toHaveBeenCalled()
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
    expect(useAuthStore.getState().user).toBeNull()
  })

  it('con token refresca el usuario desde el backend', async () => {
    useAuthStore.setState({ token: 'tok-1' })
    mockedAuth.getMe.mockResolvedValue({
      data: { ...user, must_change_password: true },
    } as never)

    await useAuthStore.getState().checkAuth()

    expect(mockedAuth.getMe).toHaveBeenCalledTimes(1)
    const state = useAuthStore.getState()
    expect(state.isAuthenticated).toBe(true)
    expect(state.user?.username).toBe('ana')
    expect(state.mustChangePassword).toBe(true)
    expect(localStorage.getItem('user')).toContain('ana')
  })

  it('conserva el timestamp de login existente', async () => {
    useAuthStore.setState({ token: 'tok-1', loginTimestamp: 12345 })
    mockedAuth.getMe.mockResolvedValue({ data: user } as never)

    await useAuthStore.getState().checkAuth()

    expect(useAuthStore.getState().loginTimestamp).toBe(12345)
  })

  it('borra la sesión cuando el backend rechaza el token', async () => {
    localStorage.setItem('token', 'tok-vencido')
    localStorage.setItem('user', JSON.stringify(user))
    useAuthStore.setState({ token: 'tok-vencido', user, isAuthenticated: true })
    mockedAuth.getMe.mockRejectedValue(new Error('401') as never)

    await useAuthStore.getState().checkAuth()

    expect(localStorage.getItem('token')).toBeNull()
    expect(localStorage.getItem('user')).toBeNull()
    const state = useAuthStore.getState()
    expect(state.isAuthenticated).toBe(false)
    expect(state.token).toBeNull()
    expect(state.user).toBeNull()
  })
})

describe('aviso de cambio de contraseña', () => {
  it('dismissPasswordChange y resetPasswordChange alternan el estado', () => {
    useAuthStore.getState().dismissPasswordChange()
    expect(useAuthStore.getState().passwordChangeDismissed).toBe(true)

    useAuthStore.getState().resetPasswordChange()
    expect(useAuthStore.getState().passwordChangeDismissed).toBe(false)
    expect(useAuthStore.getState().loginTimestamp).toEqual(expect.any(Number))
  })
})

describe('persistencia', () => {
  it('serializa la sesión bajo la clave sigem-auth', async () => {
    mockedAuth.login.mockResolvedValue(loginResponse as never)

    await useAuthStore.getState().login('ana', 'secreta')

    const raw = localStorage.getItem('sigem-auth')
    expect(raw).toBeTruthy()
    const persisted = JSON.parse(raw ?? '{}') as { state: { token: string } }
    expect(persisted.state.token).toBe('tok-1')
  })
})
