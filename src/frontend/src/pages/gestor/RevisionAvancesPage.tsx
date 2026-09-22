import { useEffect, useState } from 'react'
import { Icon } from '../../components/ui/icons'
import { gestorDashboard } from '../../lib/api'
import { clsx } from 'clsx'

interface AvanceRevision {
  id: string
  producto_id: string
  producto_codigo: string
  producto_nombre: string
  codigo_indicador: string | null
  indicador: string | null
  gestor_id: string
  gestor_codigo: string
  gestor_nombre: string
  avance_porcentaje: number
  avance_valor: number | null
  periodo: string | null
  fecha_registro: string | null
  estado_revision: string
  evidencia_nombre: string | null
  evidencia_tipo: string | null
  evidencia_url: string | null
  observaciones: string | null
  created_at: string | null
}

const PERIODOS = [
  'Enero - Marzo 2026',
  'Abril - Junio 2026',
  'Julio - Septiembre 2026',
  'Octubre - Diciembre 2026',
  'Semestre 1 2026',
  'Semestre 2 2026',
  'Anual 2026',
]

const estadoTone: Record<string, string> = {
  PENDIENTE: 'bg-ochre-soft text-ochre-deep',
  BORRADOR: 'bg-line/60 text-ink-soft',
  EN_REVISION: 'bg-[#E9EEF5] text-[#3D5D7A]',
  APROBADO: 'bg-forest-soft text-forest',
  RECHAZADO: 'bg-warn-soft text-warn',
}

export default function RevisionAvancesPage() {
  const [avances, setAvances] = useState<AvanceRevision[]>([])
  const [stats, setStats] = useState({ pendientes: 0, aprobados_semana: 0, devueltos: 0 })
  const [loading, setLoading] = useState(true)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [observaciones, setObservaciones] = useState<Record<string, string>>({})
  const [saving, setSaving] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [filtroEstado, setFiltroEstado] = useState('')
  const [filtroPeriodo, setFiltroPeriodo] = useState('')

  const fetchData = async () => {
    setLoading(true)
    try {
      const [avancesRes, statsRes] = await Promise.all([
        gestorDashboard.revisionAvances(filtroEstado || undefined, search || undefined, filtroPeriodo || undefined),
        gestorDashboard.revisionEstadisticas(),
      ])
      setAvances(avancesRes.data)
      setStats(statsRes.data)
    } catch {
      // silent
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [filtroEstado, filtroPeriodo])

  const handleSearch = () => { fetchData() }

  const handleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id)
  }

  const handleObservacion = (id: string, value: string) => {
    setObservaciones((prev) => ({ ...prev, [id]: value }))
  }

  const handleAprobar = async (avance: AvanceRevision) => {
    setSaving(avance.id)
    try {
      await gestorDashboard.revisarAvance(avance.id, { nuevo_estado: 'APROBADO' })
      await fetchData()
    } catch {
      // silent
    } finally {
      setSaving(null)
    }
  }

  const handleDevolver = async (avance: AvanceRevision) => {
    const obs = observaciones[avance.id]
    if (!obs || obs.trim().length < 5) {
      alert('La observación es obligatoria al devolver un avance (mínimo 5 caracteres).')
      return
    }
    setSaving(avance.id)
    try {
      await gestorDashboard.revisarAvance(avance.id, { nuevo_estado: 'RECHAZADO', observacion: obs })
      setExpandedId(null)
      await fetchData()
    } catch {
      // silent
    } finally {
      setSaving(null)
    }
  }

  return (
    <div className="space-y-0 pb-8">
      <section className="relative overflow-hidden bg-pine px-6 py-7 text-white shadow-lg sm:px-8 sm:py-9">
        <div className="absolute -right-20 -top-24 h-72 w-72 rounded-full border border-white/10" aria-hidden="true" />
        <div className="relative flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white/15 backdrop-blur">
            <Icon name="check" className="h-6 w-6 text-white" />
          </div>
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-ochre-soft">Panel administrativo</p>
            <h1 className="text-2xl font-bold leading-tight sm:text-3xl">Revisión y aprobación de avances</h1>
          </div>
        </div>
        <p className="relative mt-3 max-w-2xl text-sm leading-6 text-white/70">
          Revisa los avances reportados por los gestores de tu sector, verifica la evidencia adjunta y aprueba o devuelve cada registro con una observación.
        </p>
      </section>

      <div className="mx-auto max-w-5xl px-4 -mt-4">
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="rounded-2xl border border-line bg-white p-5 shadow-sm">
            <p className="text-3xl font-black text-ochre-deep">{stats.pendientes}</p>
            <p className="mt-1 text-sm font-bold text-ink-soft">Pendientes de revisión</p>
          </div>
          <div className="rounded-2xl border border-line bg-white p-5 shadow-sm">
            <p className="text-3xl font-black text-forest">{stats.aprobados_semana}</p>
            <p className="mt-1 text-sm font-bold text-ink-soft">Aprobados esta semana</p>
          </div>
          <div className="rounded-2xl border border-line bg-white p-5 shadow-sm">
            <p className="text-3xl font-black text-warn">{stats.devueltos}</p>
            <p className="mt-1 text-sm font-bold text-ink-soft">Devueltos al gestor</p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 mb-5">
          <div className="relative flex-1 min-w-[240px]">
            <Icon name="search" className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Buscar por gestor o código de indicador"
              className="w-full rounded-xl border border-line bg-white py-2.5 pl-10 pr-4 text-sm text-ink outline-none focus:border-pine focus:ring-2 focus:ring-pine/10"
            />
          </div>
          <select
            value={filtroEstado}
            onChange={(e) => setFiltroEstado(e.target.value)}
            className="rounded-xl border border-line bg-white px-4 py-2.5 text-sm text-ink outline-none focus:border-pine"
          >
            <option value="">Estado: Todos</option>
            <option value="PENDIENTE">Pendiente</option>
            <option value="APROBADO">Aprobado</option>
            <option value="RECHAZADO">Devuelto</option>
          </select>
          <select
            value={filtroPeriodo}
            onChange={(e) => setFiltroPeriodo(e.target.value)}
            className="rounded-xl border border-line bg-white px-4 py-2.5 text-sm text-ink outline-none focus:border-pine"
          >
            <option value="">Periodo: Todos</option>
            {PERIODOS.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>

        <div className="mb-3 flex items-center gap-2">
          <h2 className="text-sm font-bold text-ink">Avances pendientes</h2>
          <span className="rounded-full bg-ochre-soft px-2.5 py-0.5 text-xs font-bold text-ochre-deep">{avances.length}</span>
        </div>

        {loading ? (
          <div className="rounded-2xl border border-line bg-white p-12 text-center text-sm text-ink-faint">
            Cargando avances...
          </div>
        ) : avances.length === 0 ? (
          <div className="rounded-2xl border border-line bg-white p-12 text-center text-sm text-ink-faint">
            No hay avances para mostrar.
          </div>
        ) : (
          <div className="space-y-3">
            {avances.map((avance) => {
              const isExpanded = expandedId === avance.id
              const isDevuelto = avance.estado_revision === 'RECHAZADO'
              const isAprobado = avance.estado_revision === 'APROBADO'

              return (
                <div
                  key={avance.id}
                  className={clsx(
                    'rounded-2xl border bg-white shadow-sm transition-shadow',
                    isExpanded ? 'border-pine shadow-md' : 'border-line',
                  )}
                >
                  <div
                    className="flex flex-wrap items-center gap-4 px-5 py-4 cursor-pointer"
                    onClick={() => handleExpand(avance.id)}
                  >
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-bold text-ink">
                        {avance.gestor_codigo} · {avance.gestor_nombre}
                      </p>
                      <p className="mt-0.5 text-xs text-ink-faint">
                        Indicador {avance.codigo_indicador || '—'} — {avance.periodo || 'Sin período'} · id_cumplimiento {avance.id.slice(0, 8)}
                      </p>
                    </div>
                    <div className="flex items-center gap-6 text-center text-xs">
                      <div>
                        <p className="font-bold text-ink">{avance.avance_valor ?? '—'}</p>
                        <p className="text-ink-faint">Avance</p>
                      </div>
                      <div>
                        <p className="font-bold text-ink">{avance.avance_porcentaje}%</p>
                        <p className="text-ink-faint">Cumplimiento</p>
                      </div>
                      <div>
                        <p className="font-bold text-ink">{avance.fecha_registro ? new Date(avance.fecha_registro).toLocaleDateString('es-CO') : '—'}</p>
                        <p className="text-ink-faint">Registrado</p>
                      </div>
                    </div>
                    <span className={clsx('inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-bold', estadoTone[avance.estado_revision] || 'bg-line/60 text-ink-soft')}>
                      <span className="h-1.5 w-1.5 rounded-full bg-current" />
                      {avance.estado_revision === 'PENDIENTE' ? 'Pendiente' :
                       avance.estado_revision === 'APROBADO' ? 'Aprobado' :
                       avance.estado_revision === 'RECHAZADO' ? 'Devuelto' : avance.estado_revision}
                    </span>
                    {!isExpanded && (isDevuelto || isAprobado) && (
                      <button className="rounded-lg border border-line px-3 py-1.5 text-xs font-bold text-ink-soft hover:bg-paper">
                        Ver evidencia
                      </button>
                    )}
                  </div>

                  {isExpanded && (
                    <div className="border-t border-line px-5 py-4 space-y-4">
                      {avance.evidencia_nombre && (
                        <div className="flex items-center gap-3 rounded-xl bg-paper p-3">
                          <Icon name="document" className="h-5 w-5 text-pine" />
                          <div className="min-w-0 flex-1">
                            <p className="truncate text-sm font-bold text-ink">{avance.evidencia_nombre}</p>
                            <p className="text-xs text-ink-faint">
                              Adjuntado {avance.fecha_registro ? new Date(avance.fecha_registro).toLocaleDateString('es-CO') : '—'}
                              {avance.evidencia_tipo?.startsWith('image/') ? ' · Ver archivo completo' : ''}
                            </p>
                          </div>
                          {avance.evidencia_nombre.match(/\.(jpg|jpeg|png)$/i) && (
                            <div className="h-10 w-10 rounded-lg bg-forest-soft flex items-center justify-center">
                              <Icon name="document" className="h-5 w-5 text-forest" />
                            </div>
                          )}
                        </div>
                      )}

                      <div>
                        <label className="text-xs font-bold text-ink">
                          Observación <span className="font-normal text-ink-faint">(obligatoria si se devuelve)</span>
                        </label>
                        <textarea
                          value={observaciones[avance.id] || ''}
                          onChange={(e) => handleObservacion(avance.id, e.target.value)}
                          placeholder="Ej: La evidencia no corresponde al período reportado..."
                          rows={2}
                          className="mt-1 w-full rounded-xl border border-line bg-white px-4 py-2.5 text-sm text-ink outline-none focus:border-pine focus:ring-2 focus:ring-pine/10 resize-none"
                        />
                      </div>

                      <div className="flex items-center justify-end gap-3">
                        {avance.estado_revision === 'PENDIENTE' && (
                          <>
                            <button
                              onClick={() => handleDevolver(avance)}
                              disabled={saving === avance.id}
                              className="rounded-xl border border-warn/40 px-5 py-2.5 text-sm font-bold text-warn transition-colors hover:bg-warn-soft disabled:opacity-50"
                            >
                              Devolver al gestor
                            </button>
                            <button
                              onClick={() => handleAprobar(avance)}
                              disabled={saving === avance.id}
                              className="rounded-xl bg-pine px-5 py-2.5 text-sm font-bold text-white transition-colors hover:bg-pine-deep disabled:opacity-50"
                            >
                              {saving === avance.id ? 'Procesando...' : 'Aprobar avance'}
                            </button>
                          </>
                        )}
                        {avance.estado_revision === 'RECHAZADO' && (
                          <>
                            <button className="rounded-xl border border-line px-5 py-2.5 text-sm font-bold text-ink-soft hover:bg-paper">
                              Devolver
                            </button>
                            <button className="rounded-xl bg-pine px-5 py-2.5 text-sm font-bold text-white hover:bg-pine-deep">
                              Aprobar
                            </button>
                          </>
                        )}
                        {avance.estado_revision === 'APROBADO' && (
                          <span className="text-sm font-bold text-forest">✓ Avance aprobado</span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
