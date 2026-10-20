import { create } from 'zustand'
import { auth, clearAccessToken, refreshAccessToken, setAccessToken } from '../lib/api'
import type { User } from '../lib/types'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  mustChangePassword: boolean
  loginTimestamp: number | null
  passwordChangeDismissed: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  setToken: (token: string) => void
  checkAuth: () => Promise<void>
  setUser: (user: User) => void
  dismissPasswordChange: () => void
  resetPasswordChange: () => void
}

export const useAuthStore = create<AuthState>()(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      mustChangePassword: false,
      loginTimestamp: null,
      passwordChangeDismissed: false,

      login: async (username: string, password: string) => {
        const payload: { username: string; password: string } = {
          username,
          password,
        }
        const response = await auth.login(payload)
        const { access_token, must_change_password, user } = response.data

        setAccessToken(access_token)
        localStorage.removeItem('token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
        localStorage.removeItem('sigem-auth')

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
          clearAccessToken()
        } finally {
          clearAccessToken()
          localStorage.removeItem('token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('user')
          localStorage.removeItem('sigem-auth')
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
        setAccessToken(token)
        set({ token })
      },

      setUser: (user: User) => {
        set({ user })
      },

      checkAuth: async () => {
        try {
          const token = get().token ?? (await refreshAccessToken())
          if (!token) {
            set({ isAuthenticated: false, user: null })
            clearAccessToken()
            return
          }
          set({ token })

          const response = await auth.getMe()
          const user = response.data
          set({
            user,
            isAuthenticated: true,
            mustChangePassword: user.must_change_password ?? false,
            loginTimestamp: get().loginTimestamp || Date.now(),
          })
        } catch {
          clearAccessToken()
          localStorage.removeItem('token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('user')
          localStorage.removeItem('sigem-auth')
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
)
