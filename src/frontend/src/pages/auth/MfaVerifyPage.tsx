import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'
import { auth } from '../../lib/api'
import { Button } from '../../components/ui/Button'

export function MfaVerifyPage() {
  const navigate = useNavigate()
  const { mfaToken, user, clearMfaChallenge } = useAuthStore()
  const [code, setCode] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (!mfaToken) {
    return <Navigate to="/login" replace />
  }

  const isAdmin = (user?.roles ?? []).some((role) =>
    ['SUPERADMIN_PLATAFORMA', 'ADMINISTRADOR_MUNICIPAL'].includes(role),
  )

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!/^\d{6}$/.test(code)) {
      setError('El código debe tener 6 dígitos.')
      return
    }

    setLoading(true)
    try {
      const response = await auth.mfaLogin({ mfa_token: mfaToken, code })
      const { access_token, must_change_password, user: userData } = response.data

      localStorage.setItem('token', access_token)
      localStorage.setItem('user', JSON.stringify(userData))

      useAuthStore.setState({
        token: access_token,
        user: userData,
        isAuthenticated: true,
        mustChangePassword: must_change_password,
        mfaRequired: false,
        mfaToken: null,
        loginTimestamp: Date.now(),
        passwordChangeDismissed: false,
      })

      if (must_change_password) {
        navigate('/change-password', { replace: true })
      } else {
        navigate(isAdmin ? '/admin/dashboard' : '/gestor/dashboard', { replace: true })
      }
    } catch (err: unknown) {
      const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } }
      const detail = axiosErr.response?.data?.detail
      if (axiosErr.response?.status === 401) {
        setError('Código incorrecto o expirado. Verifique la hora de su dispositivo.')
      } else {
        setError(detail || 'No se pudo validar el código. Intente de nuevo.')
      }
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
          <h1 className="text-2xl font-bold text-ink">Verificación en Dos Pasos</h1>
          <p className="text-ink-faint text-sm mt-1">
            Ingrese el código de su aplicación de autenticación.
          </p>
        </div>

        <div className="bg-paper-raised rounded-xl shadow-sm border border-line p-8">
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-warn/10 border border-warn/20 text-warn text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-ink mb-1">Código de Verificación</label>
              <input
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                maxLength={6}
                placeholder="123456"
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
                required
                autoFocus
                autoComplete="one-time-code"
                className="w-full px-3 py-2 border border-line rounded-lg bg-paper text-ink text-center text-xl tracking-[0.5em] font-mono placeholder:text-ink-faint placeholder:tracking-normal placeholder:font-sans focus:outline-none focus:ring-2 focus:ring-pine/30 focus:border-pine"
              />
            </div>

            <Button
              type="submit"
              loading={loading}
              disabled={code.length !== 6}
              className="w-full"
              size="lg"
            >
              Verificar
            </Button>

            <button
              type="button"
              onClick={() => {
                clearMfaChallenge()
                navigate('/login', { replace: true })
              }}
              className="w-full text-sm text-ink-faint hover:text-ink"
            >
              Volver al inicio de sesión
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
