import { useState, useEffect, useCallback } from 'react'
import { useAuthStore } from '../stores/authStore'
import { auth } from '../lib/api'
import { Input } from './ui/Input'
import { Button } from './ui/Button'
import { clsx } from 'clsx'

const FIRST_PROMPT_MS = 5 * 60 * 1000
const SECOND_PROMPT_MS = 10 * 60 * 1000

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

export function PasswordChangeModal() {
  const {
    mustChangePassword,
    loginTimestamp,
    passwordChangeDismissed,
    dismissPasswordChange,
    setUser,
  } = useAuthStore()

  const [visible, setVisible] = useState(false)
  const [mandatory, setMandatory] = useState(false)
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const strength = getPasswordStrength(newPassword)
  const passwordsMatch = newPassword === confirmPassword && confirmPassword.length > 0

  const checkTimer = useCallback(() => {
    if (!mustChangePassword || !loginTimestamp) {
      setVisible(false)
      return
    }

    const elapsed = Date.now() - loginTimestamp

    if (elapsed >= SECOND_PROMPT_MS) {
      setVisible(true)
      setMandatory(true)
    } else if (elapsed >= FIRST_PROMPT_MS && !passwordChangeDismissed) {
      setVisible(true)
      setMandatory(false)
    }
  }, [mustChangePassword, loginTimestamp, passwordChangeDismissed])

  useEffect(() => {
    checkTimer()
    const interval = setInterval(checkTimer, 10_000)
    return () => clearInterval(interval)
  }, [checkTimer])

  useEffect(() => {
    if (!visible || !mandatory) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') e.preventDefault()
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [visible, mandatory])

  const handleDismiss = () => {
    if (mandatory) return
    dismissPasswordChange()
    setVisible(false)
  }

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
      useAuthStore.setState({
        mustChangePassword: false,
        passwordChangeDismissed: false,
        loginTimestamp: null,
      })
      setVisible(false)
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setError(axiosErr.response?.data?.detail || 'Error al cambiar la contraseña.')
    } finally {
      setLoading(false)
    }
  }

  if (!visible) return null

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-ink/60 backdrop-blur-sm">
      <div className="bg-paper-raised rounded-2xl shadow-2xl border border-line w-full max-w-md mx-4 overflow-hidden">
        <div className="px-6 pt-6 pb-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-ochre/10 flex items-center justify-center">
              <svg className="w-5 h-5 text-ochre" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-bold text-ink">Cambiar Contraseña</h2>
              <p className="text-xs text-ink-faint">
                {mandatory
                  ? 'Es obligatorio cambiar su contraseña para continuar.'
                  : 'Se recomienda cambiar su contraseña por seguridad.'}
              </p>
            </div>
          </div>
          {!mandatory && (
            <p className="text-sm text-ink-faint">
              Su contraseña temporal debe ser actualizada. Puede hacerlo ahora o más tarde.
            </p>
          )}
        </div>

        <form onSubmit={handleSubmit} className="px-6 pb-6 space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-warn/10 border border-warn/20 text-warn text-sm">
              {error}
            </div>
          )}

          <Input
            label="Contraseña Actual"
            type="password"
            placeholder="Ingrese su contraseña actual"
            value={currentPassword}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setCurrentPassword(e.target.value)}
            required
            autoComplete="current-password"
          />

          <div>
            <Input
              label="Nueva Contraseña"
              type="password"
              placeholder="Ingrese su nueva contraseña"
              value={newPassword}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewPassword(e.target.value)}
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
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setConfirmPassword(e.target.value)}
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

          <div className="flex gap-3 pt-2">
            {!mandatory && (
              <Button
                type="button"
                variant="secondary"
                onClick={handleDismiss}
                className="flex-1"
              >
                Cambiar después
              </Button>
            )}
            <Button
              type="submit"
              loading={loading}
              disabled={!passwordsMatch}
              className={clsx(mandatory ? 'w-full' : 'flex-1')}
            >
              Cambiar Contraseña
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
