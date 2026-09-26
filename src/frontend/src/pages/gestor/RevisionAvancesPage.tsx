import { Fragment, useEffect, useState } from 'react'
import { gestorDashboard } from '../../lib/api'
import { Button } from '../../components/ui/Button'
import { Icon, ModalShell, formatDateOnly, selectClass } from '../../components/ui/icons'
import EvidenciasModal from '../../components/EvidenciasModal'
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
  observaciones_revision?: string | null
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
  DEVUELTO: 'bg-warn-soft text-warn',
}

const estadoLabel: Record<string, string> = {
  PENDIENTE: 'Pendiente',
  BORRADOR: 'Borrador',
  EN_REVISION: 'En revisión',
  APROBADO: 'Aprobado',
  RECHAZADO: 'Devuelto',
  DEVUELTO: 'Devuelto',
}

function EstadoBadge({ estado }: { estado: string }) {
  return (
    <span className={clsx('inline-flex items-center gap-2 rounded-full px-2.5 py-1 text-xs font-bold', estadoTone[estado] || 'bg-line/60 text-ink-soft')}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {estadoLabel[estado] || estado}
    </span>
  )
}

export default function RevisionAvancesPage() {
  const [avances, setAvances] = useState<AvanceRevision[]>([])
  const [stats, setStats] = useState({ pendientes: 0, aprobados_semana: 0, devueltos: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [observaciones, setObservaciones] = useState<Record<string, string>>({})
  const [saving, setSaving] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [filtroEstado, setFiltroEstado] = useState('')
  const [filtroPeriodo, setFiltroPeriodo] = useState('')
  const [modalEvidencia, setModalEvidencia] = useState<AvanceRevision | null>(null)
  const [showEvidenciasModal, setShowEvidenciasModal] = useState<AvanceRevision | null>(null)
  const [downloadLoading, setDownloadLoading] = useState(false)

  const downloadEvidencia = async (avance: AvanceRevision) => {
    setDownloadLoading(true)
    try {
      const res = await gestorDashboard.descargarEvidencia(avance.id)
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url
      a.download = avance.evidencia_nombre || 'evidencia'
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch {
      setError('No fue posible descargar la evidencia.')
    } finally {
      setDownloadLoading(false)
    }
  }

  const fetchData = async () => {
    setLoading(true)
    setError('')
    try {
      const [avancesRes, statsRes] = await Promise.all([
        gestorDashboard.revisionAvances(filtroEstado || undefined, search || undefined, filtroPeriodo || undefined),
        gestorDashboard.revisionEstadisticas(),
      ])
      setAvances(avancesRes.data)
      setStats(statsRes.data)
    } catch {
      setError('No fue posible cargar los avances pendientes de revisión.')
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
      setExpandedId(null)
      await fetchData()
    } catch {
      setError('No fue posible aprobar el avance.')
    } finally {
      setSaving(null)
    }
  }

  const handleDevolver = async (avance: AvanceRevision) => {
    const obs = observaciones[avance.id]
    if (!obs || obs.trim().length < 5) {
      setError('La observación es obligatoria al devolver un avance (mínimo 5 caracteres).')
      return
    }
    setSaving(avance.id)
    try {
      await gestorDashboard.revisarAvance(avance.id, { nuevo_estado: 'RECHAZADO', observacion: obs })
      setExpandedId(null)
      await fetchData()
    } catch {
      setError('No fue posible devolver el avance.')
    } finally {
      setSaving(null)
    }
  }

  const total = avances.length

  return (
    <div className="space-y-6 pb-8">
      <section className="flex flex-col gap-5 rounded-[28px] bg-pine px-6 py-7 text-white shadow-[0_18px_40px_rgba(10,43,41,.16)] sm:flex-row sm:items-end sm:justify-between sm:px-8">
        <div>
          <p className="text-xs font-bold uppercase tracking-[.2em] text-ochre-soft">Panel administrativo</p>
          <h1 className="mt-2 text-3xl font-bold">Revisión y aprobación de avances</h1>
          <p className="mt-2 max-w-2xl text-sm text-white/70">
            Revisa los avances reportados por los gestores de tu sector, verifica la evidencia adjunta y aprueba o devuelve cada registro con una observación.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" onClick={fetchData} className="border border-white/20 text-white hover:bg-white/10">
            <Icon name="refresh" />
            Actualizar
          </Button>
        </div>
      </section>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {[
          ['Total avances', total, 'text-pine'],
          ['Pendientes', stats.pendientes, 'text-ochre-deep'],
          ['Aprobados esta semana', stats.aprobados_semana, 'text-forest'],
          ['Devueltos al gestor', stats.devueltos, 'text-warn'],
        ].map(([label, value, tone]) => (
          <div key={String(label)} className="rounded-2xl border border-line bg-white p-4 shadow-sm">
            <p className="text-xs font-bold uppercase tracking-wider text-ink-faint">{label}</p>
            <p className={`mt-2 text-3xl font-bold ${tone}`}>{value}</p>
          </div>
        ))}
      </div>

      {error && (
        <div role="alert" className="rounded-xl border border-warn/30 bg-warn-soft px-4 py-3 text-sm text-warn">
          {error}
        </div>
      )}

      <section className="overflow-visible rounded-2xl border border-line bg-white shadow-sm">
        <div className="flex flex-col gap-3 border-b border-line p-4 lg:flex-row lg:items-center">
          <div className="relative flex-1">
            <span className="absolute left-3 top-3 text-ink-faint">
              <Icon name="search" />
            </span>
            <input
              aria-label="Buscar avances"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Buscar por gestor o código de indicador..."
              className={`${selectClass} pl-10`}
            />
          </div>
          <select
            aria-label="Filtrar por estado"
            className={`${selectClass} lg:w-44`}
            value={filtroEstado}
            onChange={(e) => setFiltroEstado(e.target.value)}
          >
            <option value="">Todos los estados</option>
            <option value="PENDIENTE">Pendiente</option>
            <option value="APROBADO">Aprobado</option>
            <option value="RECHAZADO">Devuelto</option>
          </select>
          <select
            aria-label="Filtrar por período"
            className={`${selectClass} lg:w-56`}
            value={filtroPeriodo}
            onChange={(e) => setFiltroPeriodo(e.target.value)}
          >
            <option value="">Todos los períodos</option>
            {PERIODOS.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[1100px] text-left text-sm">
            <thead className="bg-paper/70 text-xs uppercase tracking-wider text-ink-faint">
              <tr>
                <th className="px-5 py-3">Gestor</th>
                <th className="px-4 py-3">Producto / Indicador</th>
                <th className="hidden md:table-cell px-4 py-3">Período</th>
                <th className="px-4 py-3 text-right">Avance</th>
                <th className="px-4 py-3 text-right">Cumplimiento</th>
                <th className="hidden lg:table-cell px-4 py-3">Registrado</th>
                <th className="px-4 py-3">Estado</th>
                <th className="px-5 py-3 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {loading ? (
                <tr>
                  <td colSpan={8} className="px-5 py-16 text-center text-ink-faint">
                    Cargando avances...
                  </td>
                </tr>
              ) : avances.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-5 py-16 text-center text-ink-faint">
                    No hay avances que coincidan con la búsqueda.
                  </td>
                </tr>
              ) : (
                avances.map((avance) => {
                  const isExpanded = expandedId === avance.id
                  return (
                    <Fragment key={avance.id}>
                      <tr className={clsx('hover:bg-paper/45', isExpanded && 'bg-paper/60')}>
                        <td className="px-5 py-4">
                          <p className="font-bold text-ink">{avance.gestor_nombre}</p>
                          <p className="mt-0.5 font-mono text-xs text-ink-faint">{avance.gestor_codigo}</p>
                        </td>
                        <td className="px-4 py-4">
                          <p className="font-bold text-ink">{avance.producto_nombre}</p>
                          <p className="mt-0.5 max-w-[240px] truncate text-xs text-ink-faint">
                            {avance.codigo_indicador || '—'} · {avance.indicador || 'Sin indicador'}
                          </p>
                        </td>
                        <td className="hidden md:table-cell px-4 py-4 text-ink-soft">{avance.periodo || '—'}</td>
                        <td className="px-4 py-4 text-right font-bold text-ink">{avance.avance_valor ?? '—'}</td>
                        <td className="px-4 py-4 text-right">
                          <span className="rounded-lg bg-forest-soft px-2.5 py-1 text-xs font-bold text-forest">
                            {avance.avance_porcentaje}%
                          </span>
                        </td>
                        <td className="hidden lg:table-cell px-4 py-4 text-xs text-ink-faint">
                          {avance.fecha_registro ? formatDateOnly(avance.fecha_registro) : '—'}
                        </td>
                        <td className="px-4 py-4">
                          <EstadoBadge estado={avance.estado_revision} />
                        </td>
                        <td className="px-5 py-4 text-right">
                          <div className="inline-flex items-center justify-end gap-0.5" aria-label={`Acciones para ${avance.gestor_nombre}`}>
                            <button
                              type="button"
                              title="Revisar avance"
                              aria-label="Revisar avance"
                              onClick={() => handleExpand(avance.id)}
                              className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-line text-pine transition-colors hover:border-pine/30 hover:bg-forest-soft"
                            >
                              <span className="sr-only">Revisar avance</span>
                              <Icon name={isExpanded ? 'close' : 'edit'} />
                            </button>
                            {avance.evidencia_nombre && (
                              <button
                                type="button"
                                title="Ver evidencias"
                                aria-label="Ver evidencias"
                                onClick={() => setShowEvidenciasModal(avance)}
                                className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-line text-pine transition-colors hover:border-pine/30 hover:bg-forest-soft"
                              >
                                <span className="sr-only">Ver evidencias</span>
                                <Icon name="document" />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr key={`${avance.id}-detail`}>
                          <td colSpan={8} className="bg-paper/40 px-5 py-5">
                            <div className="space-y-4">
                              {avance.evidencia_nombre && (
                                <div className="flex items-center gap-3 rounded-xl border border-line bg-white p-3">
                                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-forest-soft">
                                    <Icon name="document" className="h-5 w-5 text-forest" />
                                  </div>
                                  <div className="min-w-0 flex-1">
                                    <p className="truncate text-sm font-bold text-ink">{avance.evidencia_nombre}</p>
                                    <p className="text-xs text-ink-faint">
                                      Adjuntado {avance.fecha_registro ? formatDateOnly(avance.fecha_registro) : '—'}
                                    </p>
                                  </div>
                                  <Button variant="ghost" size="sm" onClick={() => setShowEvidenciasModal(avance)}>
                                    Ver evidencias
                                  </Button>
                                </div>
                              )}

                              <div>
                                <label className="text-sm font-bold text-ink" htmlFor={`obs-${avance.id}`}>
                                  Observación <span className="font-normal text-ink-faint">(obligatoria si se devuelve)</span>
                                </label>
                                <textarea
                                  id={`obs-${avance.id}`}
                                  value={observaciones[avance.id] || ''}
                                  onChange={(e) => handleObservacion(avance.id, e.target.value)}
                                  placeholder="Ej: La evidencia no corresponde al período reportado..."
                                  rows={2}
                                  className={`${selectClass} mt-1 resize-none`}
                                />
                              </div>

                              <div className="flex flex-wrap items-center justify-end gap-3">
                                {avance.estado_revision === 'PENDIENTE' && (
                                  <>
                                    <Button
                                      variant="ghost"
                                      onClick={() => handleDevolver(avance)}
                                      disabled={saving === avance.id}
                                      className="border border-warn/40 text-warn hover:bg-warn-soft"
                                    >
                                      Devolver al gestor
                                    </Button>
                                    <Button
                                      onClick={() => handleAprobar(avance)}
                                      loading={saving === avance.id}
                                    >
                                      Aprobar avance
                                    </Button>
                                  </>
                                )}
                                {(avance.estado_revision === 'RECHAZADO' || avance.estado_revision === 'DEVUELTO') && (
                                  <span className="text-sm font-bold text-warn">Devuelto al gestor</span>
                                )}
                                {avance.estado_revision === 'APROBADO' && (
                                  <span className="text-sm font-bold text-forest">Avance aprobado</span>
                                )}
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </section>

      {showEvidenciasModal && (
        <EvidenciasModal
          avanceId={showEvidenciasModal.id}
          avanceNombre={showEvidenciasModal.producto_nombre}
          subtitle={`${showEvidenciasModal.gestor_nombre} · ${showEvidenciasModal.producto_nombre}`}
          canEdit={false}
          onClose={() => setShowEvidenciasModal(null)}
        />
      )}

      {modalEvidencia && (
        <ModalShell
          title="Evidencia adjunta"
          description={`${modalEvidencia.producto_nombre} · ${modalEvidencia.gestor_nombre}`}
          close={() => setModalEvidencia(null)}
        >
          <div className="space-y-3 p-6">
            <div className="rounded-xl border border-line bg-paper/60 p-4">
              <p className="text-xs font-bold uppercase tracking-wider text-ink-faint">Archivo</p>
              <p className="mt-1 break-all font-bold text-pine">{modalEvidencia.evidencia_nombre || 'Sin archivo'}</p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-xl border border-line bg-paper/60 p-4">
                <p className="text-xs font-bold uppercase tracking-wider text-ink-faint">Tipo</p>
                <p className="mt-1 font-bold text-ink">{modalEvidencia.evidencia_tipo || '—'}</p>
              </div>
              <div className="rounded-xl border border-line bg-paper/60 p-4">
                <p className="text-xs font-bold uppercase tracking-wider text-ink-faint">Fecha</p>
                <p className="mt-1 font-bold text-ink">
                  {modalEvidencia.fecha_registro ? formatDateOnly(modalEvidencia.fecha_registro) : '—'}
                </p>
              </div>
            </div>
            <div className="rounded-xl border border-line bg-paper/60 p-4">
              <p className="text-xs font-bold uppercase tracking-wider text-ink-faint">Observaciones del gestor</p>
              <p className="mt-1 text-sm text-ink">{modalEvidencia.observaciones || 'Sin observaciones'}</p>
            </div>
            {modalEvidencia.observaciones_revision && (
              <div className="rounded-xl border border-line bg-forest-soft/40 p-4">
                <p className="text-xs font-bold uppercase tracking-wider text-forest">Comentario del revisor</p>
                <p className="mt-1 text-sm text-ink">{modalEvidencia.observaciones_revision}</p>
              </div>
            )}
          </div>
          <footer className="flex justify-end gap-3 border-t border-line px-6 py-4">
            <Button variant="ghost" onClick={() => setModalEvidencia(null)}>Cerrar</Button>
            <Button
              loading={downloadLoading}
              onClick={() => downloadEvidencia(modalEvidencia)}
              disabled={!modalEvidencia.evidencia_nombre}
            >
              <Icon name="document" /> Descargar evidencia
            </Button>
          </footer>
        </ModalShell>
      )}
    </div>
  )
}
