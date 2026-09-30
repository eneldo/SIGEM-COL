import { useEffect, useState } from 'react'
import { gestorDashboard } from '../lib/api'
import type { Evidencia } from '../lib/types'
import { Icon } from './ui/icons'

export type EvidencePreviewKind = 'image' | 'pdf' | 'unsupported'

export function getEvidencePreviewKind(tipo: string): EvidencePreviewKind {
  const normalizedType = tipo.toLowerCase()
  if (normalizedType.startsWith('image/')) return 'image'
  if (normalizedType === 'application/pdf' || normalizedType.includes('pdf')) return 'pdf'
  return 'unsupported'
}

interface EvidencePreviewProps {
  avanceId: string
  evidencia: Evidencia
}

export function EvidencePreview({ avanceId, evidencia }: EvidencePreviewProps) {
  const kind = getEvidencePreviewKind(evidencia.tipo)
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(kind !== 'unsupported')
  const [error, setError] = useState(false)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    if (kind === 'unsupported') return
    let active = true
    let objectUrl = ''

    gestorDashboard.descargarEvidenciaPorId(avanceId, evidencia.id)
      .then((response) => {
        const blob = response.data
        if (!active) return
        objectUrl = URL.createObjectURL(blob)
        setUrl(objectUrl)
      })
      .catch(() => {
        if (active) setError(true)
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [avanceId, evidencia.id, kind])

  useEffect(() => {
    if (!open) return
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false)
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [open])

  if (kind === 'unsupported') {
    return (
      <span className="flex h-16 w-20 shrink-0 items-center justify-center rounded-xl bg-forest-soft text-forest">
        <Icon name="document" className="h-6 w-6" />
      </span>
    )
  }

  return (
    <>
      <button
        type="button"
        onClick={() => url && setOpen(true)}
        disabled={!url}
        aria-label={`Ver vista previa de ${evidencia.nombre}`}
        className="group relative flex h-16 w-20 shrink-0 items-center justify-center overflow-hidden rounded-xl border border-line bg-forest-soft text-forest transition hover:border-forest/40 focus:outline-none focus:ring-2 focus:ring-forest/30 disabled:cursor-default"
      >
        {kind === 'image' && url ? (
          <img src={url} alt="" className="h-full w-full object-cover" />
        ) : (
          <Icon name={loading ? 'refresh' : 'document'} className="h-6 w-6" />
        )}
        {!loading && !error && (
          <span className="absolute inset-0 flex items-center justify-center bg-pine-deep/0 text-white opacity-0 transition group-hover:bg-pine-deep/60 group-hover:opacity-100 group-focus-visible:bg-pine-deep/60 group-focus-visible:opacity-100">
            <Icon name="eye" className="h-5 w-5" />
          </span>
        )}
      </button>

      {open && url && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-pine-deep/80 p-4 backdrop-blur-sm" onMouseDown={(event) => event.target === event.currentTarget && setOpen(false)}>
          <section role="dialog" aria-modal="true" aria-label={`Vista previa de ${evidencia.nombre}`} className="flex max-h-[94vh] w-full max-w-5xl flex-col overflow-hidden rounded-3xl bg-white shadow-2xl">
            <header className="flex items-center justify-between gap-4 border-b border-line px-5 py-4">
              <div className="min-w-0">
                <h3 className="truncate text-lg font-bold text-ink">{evidencia.nombre}</h3>
                <p className="text-xs text-ink-faint">Vista previa de la evidencia</p>
              </div>
              <button type="button" onClick={() => setOpen(false)} aria-label="Cerrar vista previa" className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-ink-faint transition hover:bg-line/50 focus:outline-none focus:ring-2 focus:ring-forest/30">
                <Icon name="close" />
              </button>
            </header>
            <div className="flex min-h-0 flex-1 items-center justify-center overflow-auto bg-paper p-4 sm:p-6">
              {kind === 'image' ? (
                <img src={url} alt={`Vista previa de ${evidencia.nombre}`} className="max-h-[78vh] max-w-full rounded-xl object-contain shadow-sm" />
              ) : (
                <iframe src={url} title={`Vista previa de ${evidencia.nombre}`} className="h-[78vh] w-full rounded-xl border border-line bg-white" />
              )}
            </div>
          </section>
        </div>
      )}
    </>
  )
}
