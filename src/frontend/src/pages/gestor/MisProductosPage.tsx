import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { dashboard, gestorDashboard } from '../../lib/api'
import type { GestorProductoItem } from '../../lib/types'
import { EstadoBadge, Icon, ModalShell, formatDate, formatDateOnly, selectClass } from '../../components/ui/icons'
import { Button } from '../../components/ui/Button'
import EvidenciasModal from '../../components/EvidenciasModal'
import TimelineAvance from '../../components/TimelineAvance'
import { clsx } from 'clsx'

interface AvanceItem {
  id: string
  producto_id: string
  avance_porcentaje: number
  avance_valor: number | null
  observaciones: string | null
  evidencia_url: string | null
  indicador: string | null
  periodo: string | null
  fecha_registro: string | null
  estado_revision: string
  evidencia_nombre: string | null
  evidencia_tipo: string | null
  observaciones_revision: string | null
  estado: string
  created_at: string | null
}

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

function AvanceBadge({ estado }: { estado: string }) {
  return (
    <span className={clsx('inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-bold', estadoTone[estado] || 'bg-line/60 text-ink-soft')}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {estadoLabel[estado] || estado}
    </span>
  )
}

const EDITABLE_STATES = new Set(['BORRADOR', 'PENDIENTE', 'RECHAZADO', 'DEVUELTO', 'EN_REVISION'])

function canEditAvance(a: AvanceItem) {
  return EDITABLE_STATES.has(a.estado_revision)
}

export function MisProductosPage() {
  const navigate = useNavigate()
  const [items, setItems] = useState<GestorProductoItem[]>([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [hasError, setHasError] = useState(false)

  const [detail, setDetail] = useState<GestorProductoItem | null>(null)
  const [avances, setAvances] = useState<AvanceItem[]>([])
  const [avancesLoading, setAvancesLoading] = useState(false)

  const [evidenciasAvance, setEvidenciasAvance] = useState<AvanceItem | null>(null)
  const [timelineAvance, setTimelineAvance] = useState<AvanceItem | null>(null)
  const [editAvance, setEditAvance] = useState<AvanceItem | null>(null)
  const [editForm, setEditForm] = useState({ avance_porcentaje: 0, avance_valor: '', observaciones: '', periodo: '' })
  const [editSaving, setEditSaving] = useState(false)
  const [editError, setEditError] = useState('')

  const reloadAvances = useCallback(async (productoId: string) => {
    try {
      const res = await gestorDashboard.avances(productoId)
      setAvances(res.data)
    } catch {
      setAvances([])
    }
  }, [])

  const load = useCallback(() => {
    setLoading(true)
    dashboard.gestorMisProductos()
      .then((res) => setItems(res.data.productos))
      .catch(() => setHasError(true))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { load() }, [load])

  const openDetail = async (p: GestorProductoItem) => {
    setDetail(p)
    setAvances([])
    setAvancesLoading(true)
    try {
      const res = await gestorDashboard.avances(p.id)
      setAvances(res.data)
    } catch {
      setAvances([])
    } finally {
      setAvancesLoading(false)
    }
  }

  const openEdit = (a: AvanceItem) => {
    setEditError('')
    setEditForm({
      avance_porcentaje: a.avance_porcentaje,
      avance_valor: a.avance_valor != null ? String(a.avance_valor) : '',
      observaciones: a.observaciones || '',
      periodo: a.periodo || '',
    })
    setEditAvance(a)
  }

  const saveEdit = async () => {
    if (!editAvance) return
    setEditSaving(true)
    setEditError('')
    try {
      await gestorDashboard.actualizarAvance(editAvance.id, {
        avance_porcentaje: editForm.avance_porcentaje,
        avance_valor: editForm.avance_valor ? parseInt(editForm.avance_valor, 10) : null,
        observaciones: editForm.observaciones || null,
        periodo: editForm.periodo || null,
      })
      setEditAvance(null)
      if (detail) await reloadAvances(detail.id)
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setEditError(axiosErr.response?.data?.detail || 'No fue posible guardar los cambios.')
    } finally {
      setEditSaving(false)
    }
  }

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return items
    return items.filter((p) => (p.codigo + ' ' + p.nombre + ' ' + p.programa.nombre + ' ' + (p.dependencia_responsable?.nombre || '')).toLowerCase().includes(q))
  }, [items, search])

  const activos = items.filter((p) => p.estado === 'ACTIVO').length
  const conDependencia = items.filter((p) => p.dependencia_responsable).length

  return <div className="space-y-6 pb-8">
    <section className="flex flex-col gap-5 rounded-[28px] bg-pine px-6 py-7 text-white shadow-[0_18px_40px_rgba(10,43,41,.16)] sm:flex-row sm:items-end sm:justify-between sm:px-8">
      <div>
        <p className="text-xs font-bold uppercase tracking-[.2em] text-ochre-soft">Panel del gestor</p>
        <h1 className="mt-2 text-3xl font-bold">Mis productos</h1>
        <p className="mt-2 max-w-2xl text-sm text-white/70">Todos los productos asignados a su gestión. Haga clic en un producto para ver el detalle, el historial de avances y registrar nuevo avance con evidencia.</p>
      </div>
    </section>

    {hasError && <div role="alert" className="rounded-xl border border-warn/30 bg-warn-soft px-4 py-3 text-sm text-warn">No fue posible cargar los productos asignados.</div>}

    <div className="grid grid-cols-2 gap-3 lg:grid-cols-3">
      {[['Productos asignados', items.length, 'text-pine'], ['Activos', activos, 'text-forest'], ['Con dependencia responsable', conDependencia, 'text-ochre-deep']].map(([label, value, tone]) => <div key={label} className="rounded-2xl border border-line bg-white p-4 shadow-sm"><p className="text-xs font-bold uppercase tracking-wider text-ink-faint">{label}</p><p className={`mt-2 text-3xl font-bold ${tone}`}>{value}</p></div>)}
    </div>

    <section className="overflow-hidden rounded-2xl border border-line bg-white shadow-sm">
      <div className="flex flex-col gap-3 border-b border-line p-4 sm:flex-row sm:items-center">
        <div className="relative flex-1"><span className="absolute left-3 top-3 text-ink-faint"><Icon name="search" /></span><input aria-label="Buscar productos" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Buscar por código, nombre, programa o dependencia..." className={`${selectClass} pl-10`} /></div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[980px] text-left text-sm">
          <thead className="bg-paper/70 text-xs uppercase tracking-wider text-ink-faint"><tr><th className="px-5 py-3">Código</th><th className="px-4 py-3">Producto</th><th className="px-4 py-3">Programa</th><th className="hidden lg:table-cell px-4 py-3">Dependencia responsable</th><th className="px-4 py-3">Estado</th><th className="px-4 py-3">Última actualización</th><th className="px-4 py-3 text-right">Acción</th></tr></thead>
          <tbody className="divide-y divide-line">
            {loading ? <tr><td colSpan={7} className="px-5 py-16 text-center text-ink-faint">Cargando productos...</td></tr> : filtered.length === 0 ? <tr><td colSpan={7} className="px-5 py-16 text-center text-ink-faint">No hay productos que coincidan con la búsqueda.</td></tr> : filtered.map((p) => (
              <tr
                key={p.id}
                onClick={() => openDetail(p)}
                className="cursor-pointer transition-colors hover:bg-paper/45"
                title="Ver detalle y avances"
              >
                <td className="px-5 py-4"><span className="font-mono text-xs font-bold text-pine">{p.codigo}</span></td>
                <td className="px-4 py-4"><p className="font-bold text-ink">{p.nombre}</p>{p.unidad_medida && <p className="mt-0.5 text-xs text-ink-faint">{p.unidad_medida}</p>}</td>
                <td className="max-w-[200px] px-4 py-4 text-ink-soft">{p.programa.nombre}</td>
                <td className="hidden lg:table-cell max-w-[190px] px-4 py-4 text-ink-soft">{p.dependencia_responsable?.nombre || 'Sin asignar'}</td>
                <td className="px-4 py-4"><EstadoBadge estado={p.estado} /></td>
                <td className="px-4 py-4 text-xs text-ink-faint">{formatDateOnly(p.updated_at)}</td>
                <td className="px-4 py-4 text-right">
                  <span className="inline-flex items-center gap-1.5 rounded-xl border border-line px-3 py-1.5 text-xs font-bold text-pine transition-colors hover:border-pine/40 hover:bg-forest-soft">
                    <Icon name="eye" className="h-3.5 w-3.5" /> Ver
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>

    {detail && (
      <ModalShell
        title="Detalle del producto"
        description="Ficha, historial de avances y registro de nuevo avance."
        close={() => setDetail(null)}
        wide
      >
        <div className="space-y-5 p-6">
          <div className="rounded-2xl border border-line bg-paper/60 p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold text-pine">{detail.codigo}</span>
                  <EstadoBadge estado={detail.estado} />
                </div>
                <p className="mt-1 text-lg font-bold text-ink">{detail.nombre}</p>
                <p className="mt-1 text-sm text-ink-soft">{detail.programa.nombre}</p>
                {detail.dependencia_responsable && (
                  <p className="mt-0.5 text-xs text-ink-faint">{detail.dependencia_responsable.nombre}</p>
                )}
              </div>
              <Button
                onClick={() => navigate(`/gestor/registro-avance?producto_id=${detail.id}`)}
              >
                <Icon name="plus" /> Registrar avance
              </Button>
            </div>
            {detail.descripcion && (
              <p className="mt-3 text-sm text-ink-soft">{detail.descripcion}</p>
            )}
          </div>

          <section>
            <div className="flex items-center justify-between">
              <p className="text-[10px] font-bold uppercase tracking-wider text-ink-faint">Historial de avances</p>
              <span className="rounded-full bg-forest-soft px-2.5 py-1 text-[11px] font-bold text-forest">{avances.length}</span>
            </div>

            {avancesLoading ? (
              <div className="mt-3 space-y-2">{[1, 2].map((i) => <div key={i} className="h-16 animate-pulse rounded-xl bg-line/40" />)}</div>
            ) : avances.length === 0 ? (
              <div className="mt-3 rounded-xl border border-dashed border-line bg-white p-6 text-center">
                <Icon name="document" className="mx-auto h-8 w-8 text-ink-faint" />
                <p className="mt-2 text-sm font-bold text-ink">Sin avances registrados</p>
                <p className="mt-1 text-xs text-ink-faint">Use "Registrar avance" para reportar el primer período.</p>
              </div>
            ) : (
              <ul className="mt-3 space-y-3">
                {avances.map((a) => (
                  <li key={a.id} className="rounded-xl border border-line bg-white p-4">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-lg font-bold text-pine">{a.avance_porcentaje}%</span>
                          {a.avance_valor != null && <span className="text-xs text-ink-faint">valor {a.avance_valor}</span>}
                          <AvanceBadge estado={a.estado_revision} />
                        </div>
                        <p className="mt-1 text-xs text-ink-faint">
                          {a.periodo || 'Sin período'} · {formatDate(a.fecha_registro || a.created_at)}
                        </p>
                      </div>
                      <div className="flex flex-wrap items-center gap-1.5">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setEvidenciasAvance(a)}
                          title="Ver, agregar o eliminar evidencias"
                        >
                          <Icon name="document" /> Evidencias
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setTimelineAvance(a)}
                          title="Ver línea de tiempo"
                        >
                          <Icon name="refresh" /> Historial
                        </Button>
                        {canEditAvance(a) && (
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => openEdit(a)}
                            title="Editar avance"
                          >
                            <Icon name="edit" /> Editar
                          </Button>
                        )}
                      </div>
                    </div>
                    {a.observaciones && (
                      <p className="mt-2 rounded-lg bg-paper px-3 py-2 text-xs text-ink-soft">
                        <span className="font-bold text-ink">Observaciones:</span> {a.observaciones}
                      </p>
                    )}
                    {a.estado_revision === 'RECHAZADO' && a.observaciones_revision && (
                      <p className="mt-2 rounded-lg bg-warn-soft px-3 py-2 text-xs text-warn">
                        <span className="font-bold">Devolución del revisor:</span> {a.observaciones_revision}
                      </p>
                    )}
                    {a.estado_revision === 'APROBADO' && a.observaciones_revision && (
                      <p className="mt-2 rounded-lg bg-forest-soft px-3 py-2 text-xs text-forest">
                        <span className="font-bold">Comentario del revisor:</span> {a.observaciones_revision}
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>

        <div className="flex justify-end border-t border-line px-6 py-4">
          <button
            onClick={() => setDetail(null)}
            className="rounded-xl border border-line px-5 py-2.5 text-sm font-bold text-ink transition-colors hover:bg-paper"
          >
            Cerrar
          </button>
        </div>
      </ModalShell>
    )}

    {evidenciasAvance && (
      <EvidenciasModal
        avanceId={evidenciasAvance.id}
        avanceNombre={`${evidenciasAvance.avance_porcentaje}% · ${evidenciasAvance.periodo || 'Sin período'}`}
        subtitle={detail?.nombre}
        canEdit={canEditAvance(evidenciasAvance)}
        onClose={() => setEvidenciasAvance(null)}
      />
    )}

    {timelineAvance && (
      <ModalShell
        title="Línea de tiempo del avance"
        description={`${timelineAvance.avance_porcentaje}% · ${timelineAvance.periodo || 'Sin período'}`}
        close={() => setTimelineAvance(null)}
        wide
      >
        <div className="p-6">
          <TimelineAvance avanceId={timelineAvance.id} avance={timelineAvance} />
        </div>
      </ModalShell>
    )}

    {editAvance && (
      <ModalShell
        title="Editar avance"
        description={detail?.nombre}
        close={() => setEditAvance(null)}
      >
        <div className="space-y-4 p-6">
          {editError && (
            <div role="alert" className="rounded-xl border border-warn/30 bg-warn-soft px-4 py-3 text-sm text-warn">
              {editError}
            </div>
          )}
          <div>
            <label className="block text-sm font-bold text-ink">Porcentaje de avance (%)</label>
            <input
              type="number"
              min={0}
              max={100}
              value={editForm.avance_porcentaje}
              onChange={(e) => setEditForm({ ...editForm, avance_porcentaje: parseFloat(e.target.value) || 0 })}
              className="mt-1 w-full rounded-xl border border-line bg-paper px-4 py-2.5 text-sm text-ink outline-none focus:border-pine focus:ring-2 focus:ring-pine/20"
            />
          </div>
          <div>
            <label className="block text-sm font-bold text-ink">Valor (opcional)</label>
            <input
              type="number"
              min={0}
              value={editForm.avance_valor}
              onChange={(e) => setEditForm({ ...editForm, avance_valor: e.target.value })}
              className="mt-1 w-full rounded-xl border border-line bg-paper px-4 py-2.5 text-sm text-ink outline-none focus:border-pine focus:ring-2 focus:ring-pine/20"
              placeholder="Ej: 1500000"
            />
          </div>
          <div>
            <label className="block text-sm font-bold text-ink">Período</label>
            <input
              type="text"
              value={editForm.periodo}
              onChange={(e) => setEditForm({ ...editForm, periodo: e.target.value })}
              className="mt-1 w-full rounded-xl border border-line bg-paper px-4 py-2.5 text-sm text-ink outline-none focus:border-pine focus:ring-2 focus:ring-pine/20"
              placeholder="Ej: Julio - Septiembre 2026"
              maxLength={50}
            />
          </div>
          <div>
            <label className="block text-sm font-bold text-ink">Observaciones</label>
            <textarea
              value={editForm.observaciones}
              onChange={(e) => { setEditForm({ ...editForm, observaciones: e.target.value }); }}
              rows={3}
              maxLength={1000}
              className="mt-1 w-full resize-none rounded-xl border border-line bg-paper px-4 py-2.5 text-sm text-ink outline-none focus:border-pine focus:ring-2 focus:ring-pine/20"
              placeholder="Describe el avance..."
            />
          </div>
          <p className="text-xs text-ink-faint">Estado: {estadoLabel[editAvance.estado_revision] || editAvance.estado_revision}</p>
        </div>
        <div className="flex items-center justify-end gap-3 border-t border-line px-6 py-4">
          <button
            onClick={() => setEditAvance(null)}
            className="rounded-xl border border-line px-4 py-2.5 text-sm font-bold text-ink-soft transition-colors hover:bg-line/40"
          >
            Cancelar
          </button>
          <button
            onClick={saveEdit}
            disabled={editSaving || editForm.avance_porcentaje < 0 || editForm.avance_porcentaje > 100}
            className="rounded-xl bg-pine px-5 py-2.5 text-sm font-bold text-white transition-colors hover:bg-pine-deep disabled:opacity-50"
          >
            {editSaving ? 'Guardando...' : 'Guardar cambios'}
          </button>
        </div>
      </ModalShell>
    )}
  </div>
}
