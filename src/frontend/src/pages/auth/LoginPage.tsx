import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'
import { Input } from '../../components/ui/Input'
import { Button } from '../../components/ui/Button'

export function LoginPage() {
  const navigate = useNavigate()
  const { login, isAuthenticated, user, mustChangePassword } = useAuthStore()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  if (isAuthenticated) {
    if (mustChangePassword) {
      return <Navigate to="/change-password" replace />
    } else {
      const role = user?.roles?.[0]
      return (
        <Navigate
          to={role === 'SUPERADMIN_PLATAFORMA' || role === 'ADMINISTRADOR_MUNICIPAL' ? '/admin/dashboard' : '/gestor/dashboard'}
          replace
        />
      )
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await login(username, password)
      const store = useAuthStore.getState()
      if (store.mustChangePassword) {
        navigate('/change-password', { replace: true })
      } else {
        const role = store.user?.roles?.[0]
        navigate(role === 'SUPERADMIN_PLATAFORMA' || role === 'ADMINISTRADOR_MUNICIPAL' ? '/admin/dashboard' : '/gestor/dashboard', { replace: true })
      }
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setError(axiosErr.response?.data?.detail || 'Credenciales incorrectas. Intente de nuevo.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-paper flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-pine mb-4">
            <span className="text-white text-2xl font-bold">S</span>
          </div>
          <h1 className="text-2xl font-bold text-ink">SIGEM Colombia</h1>
          <p className="text-ink-faint text-sm mt-1">
            Sistema de Información para el Seguimiento al Plan de Desarrollo Municipal
          </p>
        </div>

        <div className="bg-paper-raised rounded-xl shadow-sm border border-line p-8">
          <h2 className="text-lg font-semibold text-ink mb-6">Iniciar Sesión</h2>

          {error && (
            <div className="mb-4 p-3 rounded-lg bg-warn/10 border border-warn/20 text-warn text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Usuario"
              placeholder="Ingrese su usuario"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoComplete="username"
            />

            <div>
              <label className="block text-sm font-medium text-ink mb-1">Contraseña</label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  placeholder="Ingrese su contraseña"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  className="w-full px-3 py-2 pr-10 border border-line rounded-lg bg-paper text-ink placeholder:text-ink-faint focus:outline-none focus:ring-2 focus:ring-pine/30 focus:border-pine"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-ink-faint hover:text-ink p-1"
                  aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                >
                  {showPassword ? (
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                      <line x1="1" y1="1" x2="23" y2="23"/>
                    </svg>
                  ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                      <circle cx="12" cy="12" r="3"/>
                    </svg>
                  )}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              loading={loading}
              className="w-full"
              size="lg"
            >
              Ingresar
            </Button>
          </form>
        </div>

        <p className="text-center text-xs text-ink-faint mt-6">
          SIGEM Colombia v1.0 — Plan de Desarrollo Municipal
        </p>
      </div>
    </div>
  )
}
