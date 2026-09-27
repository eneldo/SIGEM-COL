import { useCallback, useEffect, useRef, useState } from 'react'
import { gestorDashboard } from '../lib/api'
import type { Evidencia } from '../lib/types'
import { Button } from './ui/Button'
import { Icon, ModalShell, formatDate } from './ui/icons'
import { clsx } from 'clsx'

interface EvidenciasModalProps {
  avanceId: string
  avanceNombre: string
  subtitle?: string
  canEdit?: boolean
  onClose: () => void
}

function formatBytes(bytes: number | null | undefined): string {
  if (bytes == null) return '—'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

function tipoIcono(tipo: string) {
  if (tipo.includes('pdf')) return 'document'
  if (tipo.includes('image')) return 'eye'
  return 'document'
}

export default function EvidenciasModal({ avanceId, avanceNombre, subtitle, canEdit = false, onClose }: EvidenciasModalProps) {
  const [evidencias, setEvidencias] = useState<Evidencia[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [descargando, setDescargando] = useState<string | null>(null)
  const [editandoId, setEditandoId] = useState<string | null>(null)
  const [editDesc, setEditDesc] = useState('')
  const [guardandoDesc, setGuardandoDesc] = useState(false)
  const [eliminandoId, setEliminandoId] = useState<string | null>(null)
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)
  const [subiendo, setSubiendo] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const fetchEvidencias = useCallback(async () => {
    setLoading(true)
    try {
      const res = await gestorDashboard.listarEvidencias(avanceId)
      setEvidencias(res.data)
      setError('')
    } catch {
      setError('No fue posible cargar las evidencias.')
    } finally {
      setLoading(false)
    }
  }, [avanceId])

  useEffect(() => { fetchEvidencias() }, [fetchEvidencias])

  const handleDownload = async (ev: Evidencia) => {
    setDescargando(ev.id)
    try {
      const res = await gestorDashboard.descargarEvidenciaPorId(avanceId, ev.id)
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url
      a.download = ev.nombre
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch {
      setError('No fue posible descargar la evidencia.')
    } finally {
      setDescargando(null)
    }
  }

  const handleStartEdit = (ev: Evidencia) => {
    setEditandoId(ev.id)
    setEditDesc(ev.descripcion || '')
  }

  const handleSaveDesc = async () => {
    if (!editandoId) return
    setGuardandoDesc(true)
    try {
      await gestorDashboard.actualizarDescripcionEvidencia(avanceId, editandoId, editDesc.trim() || null)
      setEvidencias((prev) => prev.map((e) => (e.id === editandoId ? { ...e, descripcion: editDesc.trim() || null } : e)))
      setEditandoId(null)
    } catch {
      setError('No fue posible guardar la descripción.')
    } finally {
      setGuardandoDesc(false)
    }
  }

  const handleDelete = async (evId: string) => {
    setEliminandoId(evId)
    try {
      await gestorDashboard.eliminarEvidencia(avanceId, evId)
      setEvidencias((prev) => prev.filter((e) => e.id !== evId))
      setConfirmDelete(null)
    } catch {
      setError('No fue posible eliminar la evidencia.')
    } finally {
      setEliminandoId(null)
    }
  }

  const handleUpload = async (files: FileList) => {
    const disponibles = 4 - evidencias.length
    const arr = Array.from(files).slice(0, disponibles)
    if (!arr.length) {
      setError('Cada avance permite máximo 4 evidencias.')
      return
    }
    if (files.length > disponibles) {
      setError(`Solo puedes agregar ${disponibles} evidencia${disponibles === 1 ? '' : 's'} más.`)
      return
    }
    setSubiendo(true)
    setError('')
    try {
      await gestorDashboard.subirEvidencias(avanceId, arr)
      await fetchEvidencias()
    } catch {
      setError('No fue posible subir las evidencias.')
    } finally {
      setSubiendo(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  return (
    <ModalShell
      title="Evidencias del avance"
      description={subtitle || avanceNombre}
      close={onClose}
      wide
    >
      <div className="space-y-4 p-6">
        {error && (
          <div role="alert" className="rounded-xl border border-warn/30 bg-warn-soft px-4 py-3 text-sm text-warn">
            {error}
          </div>
        )}

        {loading ? (
          <div className="py-12 text-center text-ink-faint">Cargando evidencias...</div>
        ) : evidencias.length === 0 ? (
          <div className="py-12 text-center">
            <Icon name="document" className="mx-auto h-10 w-10 text-ink-faint" />
            <p className="mt-3 text-sm font-bold text-ink">Sin evidencias adjuntas</p>
            <p className="mt-1 text-xs text-ink-faint">Agrega fotos, actas o planillas en PDF como soporte del avance.</p>
          </div>
        ) : (
          <ul className="space-y-3">
            {evidencias.map((ev) => (
              <li key={ev.id} className="rounded-2xl border border-line bg-paper/50 p-4">
                <div className="flex items-start gap-3">
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-forest-soft text-forest">
                    <Icon name={tipoIcono(ev.tipo)} className="h-5 w-5" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-bold text-ink">{ev.nombre}</p>
                    <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-ink-faint">
                      <span>{ev.tipo}</span>
                      <span>{formatBytes(ev.tamano_almacenado)}</span>
                      {ev.optimizada && <span className="rounded bg-forest-soft px-1.5 py-0.5 font-bold text-forest">Comprimida</span>}
                      <span>{ev.created_at ? formatDate(ev.created_at) : '—'}</span>
                    </div>

                    {editandoId === ev.id ? (
                      <div className="mt-3 flex items-start gap-2">
                        <textarea
                          value={editDesc}
                          onChange={(e) => setEditDesc(e.target.value)}
                          rows={2}
                          maxLength={1000}
                          placeholder="Describe qué contiene esta evidencia..."
                          className="flex-1 rounded-xl border border-line bg-white px-3 py-2 text-sm text-ink outline-none focus:border-forest focus:ring-2 focus:ring-forest/20"
                        />
                        <div className="flex gap-1">
                          <button
                            type="button"
                            onClick={handleSaveDesc}
                            disabled={guardandoDesc}
                            className="flex h-8 w-8 items-center justify-center rounded-lg bg-forest text-white transition hover:bg-forest/90 disabled:opacity-50"
                            title="Guardar"
                          >
                            <Icon name="check" className="h-4 w-4" />
                          </button>
                          <button
                            type="button"
                            onClick={() => setEditandoId(null)}
                            className="flex h-8 w-8 items-center justify-center rounded-lg text-ink-faint transition hover:bg-line"
                            title="Cancelar"
                          >
                            <Icon name="close" className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <p className={clsx('mt-2 text-sm', ev.descripcion ? 'text-ink-soft' : 'italic text-ink-faint')}>
                        {ev.descripcion || 'Sin descripción'}
                      </p>
                    )}
                  </div>

                  <div className="flex shrink-0 flex-col gap-1">
                    <button
                      type="button"
                      onClick={() => handleDownload(ev)}
                      disabled={descargando === ev.id}
                      title="Descargar"
                      className="flex h-8 w-8 items-center justify-center rounded-lg border border-line text-pine transition hover:bg-forest-soft disabled:opacity-50"
                    >
                      <Icon name={descargando === ev.id ? 'refresh' : 'document'} className="h-4 w-4" />
                    </button>
                    {canEdit && editandoId !== ev.id && (
                      <button
                        type="button"
                        onClick={() => handleStartEdit(ev)}
                        title="Editar descripción"
                        className="flex h-8 w-8 items-center justify-center rounded-lg border border-line text-pine transition hover:bg-forest-soft"
                      >
                        <Icon name="edit" className="h-4 w-4" />
                      </button>
                    )}
                    {canEdit && (
                      confirmDelete === ev.id ? (
                        <div className="flex gap-1">
                          <button
                            type="button"
                            onClick={() => handleDelete(ev.id)}
                            disabled={eliminandoId === ev.id}
                            title="Confirmar eliminación"
                            className="flex h-8 w-8 items-center justify-center rounded-lg bg-warn text-white transition hover:bg-warn/90 disabled:opacity-50"
                          >
                            <Icon name="check" className="h-4 w-4" />
                          </button>
                          <button
                            type="button"
                            onClick={() => setConfirmDelete(null)}
                            title="Cancelar"
                            className="flex h-8 w-8 items-center justify-center rounded-lg text-ink-faint transition hover:bg-line"
                          >
                            <Icon name="close" className="h-4 w-4" />
                          </button>
                        </div>
                      ) : (
                        <button
                          type="button"
                          onClick={() => setConfirmDelete(ev.id)}
                          title="Eliminar evidencia"
                          className="flex h-8 w-8 items-center justify-center rounded-lg border border-line text-warn transition hover:bg-warn-soft"
                        >
                          <Icon name="trash" className="h-4 w-4" />
                        </button>
                      )
                    )}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      <footer className="flex items-center justify-between gap-3 border-t border-line px-6 py-4">
        <Button variant="ghost" onClick={onClose}>Cerrar</Button>
        {canEdit && (
          <>
            <input
              id="evidencia-modal-input"
              ref={fileInputRef}
              type="file"
              accept=".jpg,.jpeg,.png,.pdf"
              multiple
              disabled={evidencias.length >= 4 || subiendo}
              className="sr-only"
              onChange={(e) => { if (e.target.files) handleUpload(e.target.files) }}
            />
            <label
              htmlFor="evidencia-modal-input"
              aria-disabled={evidencias.length >= 4 || subiendo}
              className={clsx(
                'inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-pine/30',
                evidencias.length >= 4 || subiendo
                  ? 'cursor-not-allowed bg-line text-ink-faint'
                  : 'cursor-pointer bg-pine text-white shadow-sm hover:bg-pine-deep active:bg-pine-deep',
              )}
            >
              <Icon name="plus" />
              {subiendo ? 'Subiendo...' : evidencias.length >= 4 ? 'Máximo 4 evidencias' : `Agregar evidencias (${evidencias.length}/4)`}
            </label>
          </>
        )}
      </footer>
    </ModalShell>
  )
}
