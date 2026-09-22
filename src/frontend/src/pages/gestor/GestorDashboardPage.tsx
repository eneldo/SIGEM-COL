import { useEffect, useState } from 'react'
import { gestorDashboard } from '../../lib/api'
import { useAuthStore } from '../../stores/authStore'
import { Icon } from '../../components/ui/icons'

interface ProductoAsignado {
  id: string
  codigo: string
  nombre: string
  indicador: string | null
  codigo_indicador: string | null
  meta_redactada: string | null
  linea_base: number | null
  meta_cuatrienio: number | null
  unidad_medida: string | null
  estado: string
}

interface Avance {
  id: string
  producto_id: string
  avance_porcentaje: number
  avance_valor: number | null
  observaciones: string | null
  evidencia_url: string | null
  estado: string
  created_at: string | null
}

interface ResumenAvances {
  total_productos: number
  productos_con_avance: number
  avance_promedio: number
  productos_completados: number
}

export function GestorDashboardPage() {
  const user = useAuthStore((s) => s.user)
  const [productos, setProductos] = useState<ProductoAsignado[]>([])
  const [resumen, setResumen] = useState<ResumenAvances | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedProducto, setSelectedProducto] = useState<ProductoAsignado | null>(null)
  const [avances, setAvances] = useState<Avance[]>([])
  const [_loadingAvances, setLoadingAvances] = useState(false)
  const [showModal, setShowModal] = useState(false)
  const [avanceForm, setAvanceForm] = useState({
    avance_porcentaje: 0,
    avance_valor: '',
    observaciones: '',
    evidencia_url: '',
  })
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    let active = true
    async function load() {
      try {
        const [productosRes, resumenRes] = await Promise.all([
          gestorDashboard.misProductos(),
          gestorDashboard.resumen(),
        ])
        if (!active) return
        setProductos(productosRes.data)
        setResumen(resumenRes.data)
      } catch {
        // Error handling
      } finally {
        setLoading(false)
      }
    }
    load()
    return () => { active = false }
  }, [])

  const handleSelectProducto = async (producto: ProductoAsignado) => {
    setSelectedProducto(producto)
    setLoadingAvances(true)
    setShowModal(true)
    try {
      const res = await gestorDashboard.avances(producto.id)
      setAvances(res.data)
    } catch {
      setAvances([])
    } finally {
      setLoadingAvances(false)
    }
  }

  const handleSubmitAvance = async () => {
    if (!selectedProducto) return
    setSubmitting(true)
    try {
      await gestorDashboard.registrarAvance(selectedProducto.id, {
        avance_porcentaje: avanceForm.avance_porcentaje,
        avance_valor: avanceForm.avance_valor ? parseInt(avanceForm.avance_valor) : undefined,
        observaciones: avanceForm.observaciones || undefined,
        evidencia_url: avanceForm.evidencia_url || undefined,
      })
      // Refresh avances
      const res = await gestorDashboard.avances(selectedProducto.id)
      setAvances(res.data)
      // Refresh resumen
      const resumenRes = await gestorDashboard.resumen()
      setResumen(resumenRes.data)
      // Reset form
      setAvanceForm({ avance_porcentaje: 0, avance_valor: '', observaciones: '', evidencia_url: '' })
      setShowModal(false)
    } catch {
      // Error handling
    } finally {
      setSubmitting(false)
    }
  }

  const kpiCards = resumen ? [
    { label: 'Productos asignados', value: resumen.total_productos, icon: 'box', tone: 'bg-forest-soft text-forest' },
    { label: 'Con avance registrado', value: resumen.productos_con_avance, icon: 'layers', tone: 'bg-ochre-soft text-ochre-deep' },
    { label: 'Avance promedio', value: `${resumen.avance_promedio}%`, icon: 'refresh', tone: 'bg-[#E9EEF5] text-[#3D5D7A]' },
    { label: 'Completados', value: resumen.productos_completados, icon: 'check', tone: 'bg-pine-soft text-pine' },
  ] : []

  return (
    <div className="space-y-6 pb-8">
      <section className="relative overflow-hidden rounded-[28px] bg-pine px-6 py-7 text-white shadow-[0_22px_50px_rgba(10,43,41,0.18)] sm:px-8 sm:py-9">
        <div className="absolute -right-20 -top-24 h-72 w-72 rounded-full border border-white/10" aria-hidden="true" />
        <div className="absolute -bottom-28 right-28 h-56 w-56 rounded-full bg-ochre/10 blur-2xl" aria-hidden="true" />
        <div className="relative grid gap-7 lg:grid-cols-[1fr_auto] lg:items-end">
          <div className="max-w-3xl">
            <p className="mb-3 text-xs font-bold uppercase tracking-[0.2em] text-ochre-soft">Panel del gestor líder</p>
            <h1 className="text-3xl font-bold leading-tight sm:text-4xl">Hola, {user?.nombre_completo || 'gestor'}</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-white/70 sm:text-base">
              Administre sus productos asignados y registre avances en cada uno de ellos.
            </p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/10 px-5 py-4 backdrop-blur-sm">
            <p className="text-xs font-bold uppercase tracking-wider text-white/55">Fecha actual</p>
            <p className="mt-1 capitalize text-sm font-bold text-white">
              {new Intl.DateTimeFormat('es-CO', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }).format(new Date())}
            </p>
          </div>
        </div>
      </section>

      {kpiCards.length > 0 && (
        <section aria-labelledby="resumen-title">
          <div className="mb-3 flex items-end justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-ink-faint">Resumen</p>
              <h2 id="resumen-title" className="mt-1 text-xl font-bold text-ink">Mis avances</h2>
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {kpiCards.map((card) => (
              <article key={card.label} className="group rounded-2xl border border-line bg-paper-raised p-5 shadow-[0_8px_22px_rgba(38,36,31,0.04)] transition-all hover:-translate-y-0.5 hover:border-pine/25 hover:shadow-[0_14px_30px_rgba(15,61,59,0.08)]">
                <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${card.tone}`}>
                  <Icon name={card.icon as any} className="h-5 w-5" />
                </div>
                <p className="mt-5 text-xs font-bold uppercase tracking-wider text-ink-faint">{card.label}</p>
                <p className="mt-1 text-3xl font-bold tabular-nums text-pine">{loading ? '—' : card.value}</p>
              </article>
            ))}
          </div>
        </section>
      )}

      <section className="overflow-hidden rounded-2xl border border-line bg-paper-raised shadow-sm" aria-labelledby="productos-title">
        <div className="flex items-center justify-between border-b border-line px-5 py-4 sm:px-6">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-ink-faint">Productos</p>
            <h2 id="productos-title" className="mt-1 text-xl font-bold text-ink">Metas del cuatrienio</h2>
          </div>
        </div>
        {loading ? (
          <div className="space-y-3 p-6" aria-label="Cargando productos">
            {[1, 2, 3].map((item) => (
              <div key={item} className="h-16 animate-pulse rounded-xl bg-line/40" />
            ))}
          </div>
        ) : productos.length ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-line bg-paper/60">
                  <th className="px-5 py-3.5 font-bold text-ink-faint sm:px-6">Código</th>
                  <th className="px-5 py-3.5 font-bold text-ink-faint">Nombre del producto</th>
                  <th className="hidden px-5 py-3.5 font-bold text-ink-faint lg:table-cell">Indicador</th>
                  <th className="hidden px-5 py-3.5 font-bold text-ink-faint md:table-cell">Meta cuatrienio</th>
                  <th className="px-5 py-3.5 font-bold text-ink-faint">Acción</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {productos.map((p) => (
                  <tr key={p.id} className="transition-colors hover:bg-paper/40">
                    <td className="px-5 py-4 sm:px-6">
                      <span className="font-mono text-xs font-bold text-pine">{p.codigo}</span>
                    </td>
                    <td className="px-5 py-4">
                      <p className="font-bold text-ink">{p.nombre}</p>
                      {p.meta_redactada && (
                        <p className="mt-0.5 text-xs text-ink-faint line-clamp-1">{p.meta_redactada}</p>
                      )}
                    </td>
                    <td className="hidden px-5 py-4 lg:table-cell">
                      <p className="text-sm text-ink-soft">{p.indicador || '—'}</p>
                    </td>
                    <td className="hidden px-5 py-4 md:table-cell">
                      <p className="text-sm font-bold text-ink">
                        {p.meta_cuatrienio !== null ? `${p.meta_cuatrienio} ${p.unidad_medida || ''}` : '—'}
                      </p>
                    </td>
                    <td className="px-5 py-4">
                      <button
                        onClick={() => handleSelectProducto(p)}
                        className="inline-flex items-center gap-2 rounded-xl bg-pine px-4 py-2 text-sm font-bold text-white transition-colors hover:bg-pine-deep"
                      >
                        Asignar <Icon name="layers" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="flex min-h-56 flex-col items-center justify-center px-6 py-10 text-center">
            <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-paper text-ink-faint">
              <Icon name="box" className="h-6 w-6" />
            </span>
            <h3 className="mt-4 text-lg font-bold text-ink">Sin productos asignados</h3>
            <p className="mt-1 max-w-sm text-sm leading-5 text-ink-faint">
              Cuando le asignen productos aparecerán aquí.
            </p>
          </div>
        )}
      </section>

      {showModal && selectedProducto && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-lg rounded-2xl bg-paper-raised shadow-2xl">
            <div className="flex items-center justify-between border-b border-line px-6 py-4">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.16em] text-ink-faint">Registrar avance</p>
                <h3 className="mt-1 text-lg font-bold text-ink">{selectedProducto.nombre}</h3>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="flex h-8 w-8 items-center justify-center rounded-lg text-ink-faint transition-colors hover:bg-line/60 hover:text-ink"
              >
                <Icon name="close" />
              </button>
            </div>
            <div className="px-6 py-5 space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-ink-faint">Código</p>
                  <p className="font-bold text-ink">{selectedProducto.codigo}</p>
                </div>
                <div>
                  <p className="text-ink-faint">Indicador</p>
                  <p className="font-bold text-ink">{selectedProducto.indicador || '—'}</p>
                </div>
                <div>
                  <p className="text-ink-faint">Línea base</p>
                  <p className="font-bold text-ink">{selectedProducto.linea_base ?? '—'}</p>
                </div>
                <div>
                  <p className="text-ink-faint">Meta cuatrienio</p>
                  <p className="font-bold text-ink">
                    {selectedProducto.meta_cuatrienio ?? '—'} {selectedProducto.unidad_medida || ''}
                  </p>
                </div>
              </div>

              <div className="border-t border-line pt-4">
                <label className="block text-sm font-bold text-ink">Porcentaje de avance (%)</label>
                <input
                  type="number"
                  min={0}
                  max={100}
                  value={avanceForm.avance_porcentaje}
                  onChange={(e) => setAvanceForm({ ...avanceForm, avance_porcentaje: parseFloat(e.target.value) || 0 })}
                  className="mt-1 w-full rounded-xl border border-line bg-paper px-4 py-2.5 text-sm text-ink outline-none transition-colors focus:border-pine focus:ring-2 focus:ring-pine/20"
                />
              </div>

              <div>
                <label className="block text-sm font-bold text-ink">Valor avance (opcional)</label>
                <input
                  type="number"
                  min={0}
                  value={avanceForm.avance_valor}
                  onChange={(e) => setAvanceForm({ ...avanceForm, avance_valor: e.target.value })}
                  className="mt-1 w-full rounded-xl border border-line bg-paper px-4 py-2.5 text-sm text-ink outline-none transition-colors focus:border-pine focus:ring-2 focus:ring-pine/20"
                  placeholder="Ej: 150"
                />
              </div>

              <div>
                <label className="block text-sm font-bold text-ink">Observaciones</label>
                <textarea
                  value={avanceForm.observaciones}
                  onChange={(e) => setAvanceForm({ ...avanceForm, observaciones: e.target.value })}
                  rows={3}
                  className="mt-1 w-full rounded-xl border border-line bg-paper px-4 py-2.5 text-sm text-ink outline-none transition-colors focus:border-pine focus:ring-2 focus:ring-pine/20 resize-none"
                  placeholder="Describe el avance realizado..."
                />
              </div>

              <div>
                <label className="block text-sm font-bold text-ink">URL de evidencia (opcional)</label>
                <input
                  type="url"
                  value={avanceForm.evidencia_url}
                  onChange={(e) => setAvanceForm({ ...avanceForm, evidencia_url: e.target.value })}
                  className="mt-1 w-full rounded-xl border border-line bg-paper px-4 py-2.5 text-sm text-ink outline-none transition-colors focus:border-pine focus:ring-2 focus:ring-pine/20"
                  placeholder="https://..."
                />
              </div>

              {avances.length > 0 && (
                <div className="border-t border-line pt-4">
                  <p className="text-xs font-bold uppercase tracking-[0.16em] text-ink-faint">Historial de avances</p>
                  <ul className="mt-2 space-y-2 max-h-40 overflow-y-auto">
                    {avances.map((a) => (
                      <li key={a.id} className="flex items-center justify-between rounded-xl bg-paper px-4 py-2 text-sm">
                        <div>
                          <span className="font-bold text-ink">{a.avance_porcentaje}%</span>
                          {a.avance_valor && <span className="ml-2 text-ink-faint">({a.avance_valor})</span>}
                        </div>
                        <span className="text-xs text-ink-faint">
                          {a.created_at ? new Date(a.created_at).toLocaleDateString('es-CO') : '—'}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
            <div className="flex items-center justify-end gap-3 border-t border-line px-6 py-4">
              <button
                onClick={() => setShowModal(false)}
                className="rounded-xl border border-line px-4 py-2.5 text-sm font-bold text-ink-soft transition-colors hover:bg-line/40"
              >
                Cancelar
              </button>
              <button
                onClick={handleSubmitAvance}
                disabled={submitting || avanceForm.avance_porcentaje < 0 || avanceForm.avance_porcentaje > 100}
                className="rounded-xl bg-pine px-5 py-2.5 text-sm font-bold text-white transition-colors hover:bg-pine-deep disabled:opacity-50"
              >
                {submitting ? 'Guardando...' : 'Registrar avance'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
