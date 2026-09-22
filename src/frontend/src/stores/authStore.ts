import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { auth } from '../lib/api'
import type { User } from '../lib/types'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  mustChangePassword: boolean
  loginTimestamp: number | null
  passwordChangeDismissed: boolean
  login: (username: string, password: string, municipioCodigo?: string) => Promise<void>
  logout: () => Promise<void>
  setToken: (token: string) => void
  checkAuth: () => Promise<void>
  setUser: (user: User) => void
  dismissPasswordChange: () => void
  resetPasswordChange: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      mustChangePassword: false,
      loginTimestamp: null,
      passwordChangeDismissed: false,

      login: async (username: string, password: string, municipioCodigo?: string) => {
        const payload: { username: string; password: string; municipio_codigo?: string } = {
          username,
          password,
        }
        if (municipioCodigo) {
          payload.municipio_codigo = municipioCodigo
        }
        const response = await auth.login(payload)
        const { access_token, must_change_password, user } = response.data

        localStorage.setItem('token', access_token)
        localStorage.setItem('user', JSON.stringify(user))

        set({
          token: access_token,
          user,
          isAuthenticated: true,
          mustChangePassword: must_change_password,
          loginTimestamp: Date.now(),
          passwordChangeDismissed: false,
        })
      },

      logout: async () => {
        try {
          await auth.logout()
        } catch {
          // ignore logout errors
        } finally {
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            mustChangePassword: false,
            loginTimestamp: null,
            passwordChangeDismissed: false,
          })
        }
      },

      setToken: (token: string) => {
        localStorage.setItem('token', token)
        set({ token })
      },

      setUser: (user: User) => {
        localStorage.setItem('user', JSON.stringify(user))
        set({ user })
      },

      checkAuth: async () => {
        const token = get().token
        if (!token) {
          set({ isAuthenticated: false, user: null })
          return
        }

        try {
          const response = await auth.getMe()
          const user = response.data
          localStorage.setItem('user', JSON.stringify(user))
          set({
            user,
            isAuthenticated: true,
            mustChangePassword: user.must_change_password ?? false,
            loginTimestamp: get().loginTimestamp || Date.now(),
          })
        } catch {
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            mustChangePassword: false,
            loginTimestamp: null,
            passwordChangeDismissed: false,
          })
        }
      },

      dismissPasswordChange: () => {
        set({ passwordChangeDismissed: true })
      },

      resetPasswordChange: () => {
        set({ passwordChangeDismissed: false, loginTimestamp: Date.now() })
      },
    }),
    {
      name: 'sigem-auth',
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        mustChangePassword: state.mustChangePassword,
        loginTimestamp: state.loginTimestamp,
        passwordChangeDismissed: state.passwordChangeDismissed,
      }),
    },
  ),
)
