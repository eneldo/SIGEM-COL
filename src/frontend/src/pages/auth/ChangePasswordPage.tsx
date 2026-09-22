import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'
import { auth } from '../../lib/api'
import { Input } from '../../components/ui/Input'
import { Button } from '../../components/ui/Button'
import { clsx } from 'clsx'

function getPasswordStrength(pw: string): { score: number; label: string; color: string } {
  let score = 0
  if (pw.length >= 8) score++
  if (pw.length >= 12) score++
  if (/[A-Z]/.test(pw)) score++
  if (/[a-z]/.test(pw)) score++
  if (/[0-9]/.test(pw)) score++
  if (/[^A-Za-z0-9]/.test(pw)) score++

  if (score <= 2) return { score, label: 'Débil', color: 'bg-warn' }
  if (score <= 4) return { score, label: 'Media', color: 'bg-ochre' }
  return { score, label: 'Fuerte', color: 'bg-done' }
}

const requirements = [
  { test: (pw: string) => pw.length >= 8, label: 'Mínimo 8 caracteres' },
  { test: (pw: string) => /[A-Z]/.test(pw), label: 'Una letra mayúscula' },
  { test: (pw: string) => /[a-z]/.test(pw), label: 'Una letra minúscula' },
  { test: (pw: string) => /[0-9]/.test(pw), label: 'Un número' },
  { test: (pw: string) => /[^A-Za-z0-9]/.test(pw), label: 'Un carácter especial' },
]

export function ChangePasswordPage() {
  const navigate = useNavigate()
  const { setUser, setToken } = useAuthStore()

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const strength = getPasswordStrength(newPassword)
  const passwordsMatch = newPassword === confirmPassword && confirmPassword.length > 0

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!passwordsMatch) {
      setError('Las contraseñas no coinciden.')
      return
    }

    setLoading(true)
    try {
      await auth.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword,
      })

      const meRes = await auth.getMe()
      const user = meRes.data
      setUser(user)
      setToken(localStorage.getItem('token') || '')
      useAuthStore.setState({ mustChangePassword: false })

      const isAdmin = user.roles.some((role) =>
        ['SUPERADMIN_PLATAFORMA', 'ADMINISTRADOR_MUNICIPAL'].includes(role),
      )
      navigate(isAdmin ? '/admin/dashboard' : '/gestor/dashboard', { replace: true })
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setError(axiosErr.response?.data?.detail || 'Error al cambiar la contraseña.')
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
          <h1 className="text-2xl font-bold text-ink">Cambiar Contraseña</h1>
          <p className="text-ink-faint text-sm mt-1">
            Es obligatorio cambiar su contraseña en el primer inicio de sesión.
          </p>
        </div>

        <div className="bg-paper-raised rounded-xl shadow-sm border border-line p-8">
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-warn/10 border border-warn/20 text-warn text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Contraseña Actual"
              type="password"
              placeholder="Ingrese su contraseña actual"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
              autoComplete="current-password"
            />

            <div>
              <Input
                label="Nueva Contraseña"
                type="password"
                placeholder="Ingrese su nueva contraseña"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                autoComplete="new-password"
              />

              {newPassword.length > 0 && (
                <div className="mt-2">
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-ink-faint">Seguridad:</span>
                    <span className="font-medium text-ink">{strength.label}</span>
                  </div>
                  <div className="h-1.5 bg-line rounded-full overflow-hidden">
                    <div
                      className={clsx('h-full rounded-full transition-all', strength.color)}
                      style={{ width: `${(strength.score / 6) * 100}%` }}
                    />
                  </div>
                </div>
              )}
            </div>

            <Input
              label="Confirmar Nueva Contraseña"
              type="password"
              placeholder="Repita su nueva contraseña"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              error={confirmPassword.length > 0 && !passwordsMatch ? 'Las contraseñas no coinciden' : undefined}
              autoComplete="new-password"
            />

            {newPassword.length > 0 && (
              <div className="space-y-1.5">
                <p className="text-xs font-medium text-ink-faint">Requisitos:</p>
                {requirements.map((req) => (
                  <div key={req.label} className="flex items-center gap-2 text-xs">
                    <div
                      className={clsx(
                        'w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0',
                        req.test(newPassword) ? 'bg-done text-white' : 'bg-line text-ink-faint',
                      )}
                    >
                      {req.test(newPassword) && (
                        <svg className="w-2.5 h-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                        </svg>
                      )}
                    </div>
                    <span className={req.test(newPassword) ? 'text-done' : 'text-ink-faint'}>
                      {req.label}
                    </span>
                  </div>
                ))}
              </div>
            )}

            <Button
              type="submit"
              loading={loading}
              disabled={!passwordsMatch}
              className="w-full"
              size="lg"
            >
              Cambiar Contraseña
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}
