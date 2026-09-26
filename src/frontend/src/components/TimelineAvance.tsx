import { useEffect, useState } from 'react'
import { gestorDashboard } from '../lib/api'
import type { Evidencia } from '../lib/types'
import { Icon, formatDate } from './ui/icons'
import { clsx } from 'clsx'

interface AvanceItem {
  id: string
  avance_porcentaje: number
  avance_valor: number | null
  observaciones: string | null
  periodo: string | null
  fecha_registro: string | null
  estado_revision: string
  observaciones_revision: string | null
  created_at: string | null
  evidencia_nombre: string | null
}

interface TimelineAvanceProps {
  avanceId: string
  avance: AvanceItem
}

interface TimelineEvent {
  id: string
  tipo: 'registro' | 'evidencia' | 'revision'
  titulo: string
  detalle?: string
  fecha: string | null
  icono: string
  tono: string
}

const estadoLabel: Record<string, string> = {
  PENDIENTE: 'Pendiente de revisión',
  BORRADOR: 'Borrador',
  EN_REVISION: 'En revisión',
  APROBADO: 'Aprobado',
  RECHAZADO: 'Devuelto',
  DEVUELTO: 'Devuelto',
}

const estadoTono: Record<string, string> = {
  APROBADO: 'bg-forest-soft text-forest border-forest/30',
  RECHAZADO: 'bg-warn-soft text-warn border-warn/30',
  DEVUELTO: 'bg-warn-soft text-warn border-warn/30',
  PENDIENTE: 'bg-ochre-soft text-ochre-deep border-ochre/30',
  BORRADOR: 'bg-line/60 text-ink-soft border-line',
  EN_REVISION: 'bg-[#E9EEF5] text-[#3D5D7A] border-[#3D5D7A]/30',
}

export default function TimelineAvance({ avanceId, avance }: TimelineAvanceProps) {
  const [evidencias, setEvidencias] = useState<Evidencia[]>([])

  useEffect(() => {
    gestorDashboard.listarEvidencias(avanceId)
      .then((r) => setEvidencias(r.data))
      .catch(() => {})
  }, [avanceId])

  const events: TimelineEvent[] = []

  events.push({
    id: `reg-${avance.id}`,
    tipo: 'registro',
    titulo: 'Avance registrado',
    detalle: `${avance.avance_porcentaje}% de cumplimiento${avance.avance_valor != null ? ` · Valor: ${avance.avance_valor}` : ''}${avance.periodo ? ` · Período: ${avance.periodo}` : ''}`,
    fecha: avance.created_at,
    icono: 'edit',
    tono: 'bg-pine text-white',
  })

  if (avance.observaciones) {
    events.push({
      id: `obs-${avance.id}`,
      tipo: 'registro',
      titulo: 'Observaciones del gestor',
      detalle: avance.observaciones,
      fecha: avance.created_at,
      icono: 'document',
      tono: 'bg-line text-ink-soft',
    })
  }

  evidencias.forEach((ev) => {
    events.push({
      id: `ev-${ev.id}`,
      tipo: 'evidencia',
      titulo: `Evidencia: ${ev.nombre}`,
      detalle: ev.descripcion || undefined,
      fecha: ev.created_at,
      icono: 'document',
      tono: 'bg-forest-soft text-forest',
    })
  })

  if (avance.estado_revision && avance.estado_revision !== 'PENDIENTE' && avance.estado_revision !== 'BORRADOR') {
    events.push({
      id: `rev-${avance.id}`,
      tipo: 'revision',
      titulo: `Revisión: ${estadoLabel[avance.estado_revision] || avance.estado_revision}`,
      detalle: avance.observaciones_revision || undefined,
      fecha: avance.fecha_registro,
      icono: avance.estado_revision === 'APROBADO' ? 'check' : 'alert',
      tono: avance.estado_revision === 'APROBADO' ? 'bg-forest text-white' : 'bg-warn text-white',
    })
  }

  events.sort((a, b) => {
    if (!a.fecha) return 1
    if (!b.fecha) return -1
    return new Date(a.fecha).getTime() - new Date(b.fecha).getTime()
  })

  return (
    <div className="space-y-0">
      <div className="mb-4 flex items-center gap-3">
        <span className={clsx('inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-bold border', estadoTono[avance.estado_revision] || 'bg-line/60 text-ink-soft border-line')}>
          <span className="h-1.5 w-1.5 rounded-full bg-current" />
          {estadoLabel[avance.estado_revision] || avance.estado_revision}
        </span>
        <span className="text-xs text-ink-faint">
          {evidencias.length} evidencia{evidencias.length !== 1 ? 's' : ''}
        </span>
      </div>

      <ol className="relative ml-4 space-y-6 border-l-2 border-line">
        {events.map((ev, idx) => (
          <li key={ev.id} className="relative pl-6">
            <span className={clsx('absolute -left-[11px] top-0 flex h-5 w-5 items-center justify-center rounded-full ring-2 ring-white', ev.tono)}>
              <Icon name={ev.icono as 'check'} className="h-3 w-3" />
            </span>
            <div className="rounded-xl border border-line bg-paper/50 p-3">
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm font-bold text-ink">{ev.titulo}</p>
                <span className="shrink-0 text-[11px] text-ink-faint">
                  {ev.fecha ? formatDate(ev.fecha) : '—'}
                </span>
              </div>
              {ev.detalle && <p className="mt-1 text-xs leading-5 text-ink-soft">{ev.detalle}</p>}
            </div>
            {idx < events.length - 1 && <span className="absolute -bottom-6 left-[-2px] h-6 w-0.5 bg-line" />}
          </li>
        ))}
      </ol>
    </div>
  )
}
