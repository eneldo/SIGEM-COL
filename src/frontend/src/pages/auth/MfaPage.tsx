import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'
import { auth } from '../../lib/api'
import type { MfaSetupResponse, MfaStatusResponse } from '../../lib/types'
import { Input } from '../../components/ui/Input'
import { Button } from '../../components/ui/Button'

export function MfaPage() {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()

  const [status, setStatus] = useState<MfaStatusResponse | null>(null)
  const [setupData, setSetupData] = useState<MfaSetupResponse | null>(null)
  const [code, setCode] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [copied, setCopied] = useState(false)

  const [disablePassword, setDisablePassword] = useState('')
  const [disableCode, setDisableCode] = useState('')

  const isAdmin = (user?.roles ?? []).some((role) =>
    ['SUPERADMIN_PLATAFORMA', 'ADMINISTRADOR_MUNICIPAL'].includes(role),
  )

  const loadStatus = useCallback(async () => {
    try {
      const response = await auth.mfaStatus()
      setStatus(response.data)
      if (!response.data.pending) {
        setSetupData(null)
      }
    } catch (err: unknown) {
      const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } }
      if (axiosErr.response?.status !== 403) {
        setError('No se pudo consultar el estado de MFA.')
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadStatus()
  }, [loadStatus])

  const pendingSecret = setupData?.secret ?? (status?.pending ? status.secret ?? null : null)
  const pendingQr = setupData?.qr_code_url ?? (status?.pending ? status.qr_code_url ?? null : null)

  const handleSetup = async () => {
    setError('')
    setSuccess('')
    setSubmitting(true)
    try {
      const response = await auth.mfaSetup()
      setSetupData(response.data)
    } catch (err: unknown) {
      const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } }
      setError(axiosErr.response?.data?.detail || 'No se pudo iniciar la configuración.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    if (!/^\d{6}$/.test(code)) {
      setError('El código debe tener 6 dígitos.')
      return
    }

    setSubmitting(true)
    try {
      await auth.mfaVerify(code)
      setSuccess('MFA activado exitosamente. Su cuenta ahora requiere un código en cada inicio de sesión.')
      setCode('')
      setSetupData(null)
      await loadStatus()
    } catch (err: unknown) {
      const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } }
      if (axiosErr.response?.status === 401) {
        setError('Código incorrecto o expirado. Verifique la hora de su dispositivo.')
      } else {
        setError(axiosErr.response?.data?.detail || 'No se pudo verificar el código.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  const handleDisable = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    if (!/^\d{6}$/.test(disableCode)) {
      setError('El código debe tener 6 dígitos.')
      return
    }

    setSubmitting(true)
    try {
      await auth.mfaDisable({ password: disablePassword, code: disableCode })
      setSuccess('MFA desactivado. Vuelva a activarlo cuanto antes.')
      setDisablePassword('')
      setDisableCode('')
      await loadStatus()
    } catch (err: unknown) {
      const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } }
      if (axiosErr.response?.status === 401) {
        setError('Contraseña o código incorrectos.')
      } else {
        setError(axiosErr.response?.data?.detail || 'No se pudo desactivar MFA.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  const copySecret = async () => {
    if (!pendingSecret) return
    try {
      await navigator.clipboard.writeText(pendingSecret)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      setError('No se pudo copiar; seleccione el texto manualmente.')
    }
  }

  return (
    <div className="min-h-screen bg-paper flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-lg">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-pine mb-4">
            <span className="text-white text-2xl font-bold">S</span>
          </div>
          <h1 className="text-2xl font-bold text-ink">Verificación en Dos Pasos (MFA)</h1>
          <p className="text-ink-faint text-sm mt-1">
            Proteja su cuenta con una aplicación de autenticación (TOTP).
          </p>
        </div>

        <div className="bg-paper-raised rounded-xl shadow-sm border border-line p-8 space-y-5">
          {error && (
            <div className="p-3 rounded-lg bg-warn/10 border border-warn/20 text-warn text-sm">
              {error}
            </div>
          )}
          {success && (
            <div className="p-3 rounded-lg bg-done/10 border border-done/20 text-done text-sm">
              {success}
            </div>
          )}

          {loading ? (
            <p className="text-ink-faint text-sm text-center py-6">Cargando…</p>
          ) : status?.mfa_activo ? (
            <>
              <div className="flex items-center gap-3 p-4 rounded-lg bg-done/10 border border-done/20">
                <div className="w-8 h-8 rounded-full bg-done text-white flex items-center justify-center flex-shrink-0">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                  </svg>
                </div>
                <div>
                  <p className="font-medium text-ink text-sm">MFA está activo</p>
                  <p className="text-ink-faint text-xs">Cada inicio de sesión requiere un código de 6 dígitos.</p>
                </div>
              </div>

              <form onSubmit={handleDisable} className="space-y-4 pt-2 border-t border-line">
                <h2 className="text-sm font-semibold text-ink pt-4">Desactivar MFA</h2>
                <Input
                  label="Contraseña actual"
                  type="password"
                  placeholder="Ingrese su contraseña"
                  value={disablePassword}
                  onChange={(e) => setDisablePassword(e.target.value)}
                  required
                  autoComplete="current-password"
                />
                <Input
                  label="Código de verificación"
                  type="text"
                  inputMode="numeric"
                  maxLength={6}
                  placeholder="123456"
                  value={disableCode}
                  onChange={(e) => setDisableCode(e.target.value.replace(/\D/g, ''))}
                  required
                  autoComplete="one-time-code"
                />
                <Button type="submit" loading={submitting} variant="danger" className="w-full">
                  Desactivar MFA
                </Button>
              </form>
            </>
          ) : pendingSecret ? (
            <form onSubmit={handleVerify} className="space-y-4">
              <div>
                <h2 className="text-sm font-semibold text-ink">1. Agregue la cuenta a su app</h2>
                <p className="text-ink-faint text-xs mt-1">
                  Use Google Authenticator, Aegis, 1Password o cualquier app compatible con TOTP.
                  Escanee el código o ingrese la clave manualmente.
                </p>
              </div>

              {pendingQr && (
                <div className="p-4 bg-white border border-line rounded-lg text-center">
                  <p className="text-xs text-ink-faint mb-2">
                    Escanee con su aplicación de autenticación
                  </p>
                  <a href={pendingQr} target="_blank" rel="noreferrer" className="text-xs text-pine underline break-all">
                    {pendingQr}
                  </a>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-ink mb-1">Clave secreta</label>
                <div className="flex gap-2">
                  <code className="flex-1 px-3 py-2 border border-line rounded-lg bg-paper text-ink text-sm font-mono break-all">
                    {pendingSecret}
                  </code>
                  <Button type="button" variant="secondary" onClick={() => void copySecret()}>
                    {copied ? 'Copiado' : 'Copiar'}
                  </Button>
                </div>
              </div>

              <div className="pt-2 border-t border-line space-y-4">
                <h2 className="text-sm font-semibold text-ink">2. Confirme con un código</h2>
                <Input
                  label="Código de verificación"
                  type="text"
                  inputMode="numeric"
                  maxLength={6}
                  placeholder="123456"
                  value={code}
                  onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
                  required
                  autoComplete="one-time-code"
                />
                <Button type="submit" loading={submitting} className="w-full" size="lg">
                  Activar MFA
                </Button>
                <button
                  type="button"
                  onClick={() => setSetupData(null)}
                  className="w-full text-sm text-ink-faint hover:text-ink"
                >
                  Cancelar
                </button>
              </div>
            </form>
          ) : (
            <div className="space-y-4">
              <div className="p-4 rounded-lg bg-ochre/10 border border-ochre/20">
                <p className="text-sm text-ink">
                  {isAdmin
                    ? 'Su rol administrador requiere MFA. Debe activarlo para continuar usando el sistema.'
                    : 'Recomendamos activar MFA para proteger su cuenta.'}
                </p>
              </div>
              <Button
                type="button"
                loading={submitting}
                onClick={() => void handleSetup()}
                className="w-full"
                size="lg"
              >
                Configurar MFA
              </Button>
              <button
                type="button"
                onClick={() => navigate(isAdmin ? '/admin/dashboard' : '/gestor/dashboard', { replace: true })}
                className="w-full text-sm text-ink-faint hover:text-ink"
              >
                Volver al inicio
              </button>
              <button
                type="button"
                onClick={() => void logout()}
                className="w-full text-sm text-ink-faint hover:text-ink"
              >
                Cerrar sesión
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
