import { useEffect, useMemo, useState } from 'react'
import { dashboard } from '../../lib/api'
import type { GestorProductoItem } from '../../lib/types'
import { EstadoBadge, Icon, formatDateOnly, selectClass } from '../../components/ui/icons'

export function MisProductosPage() {
  const [items, setItems] = useState<GestorProductoItem[]>([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [hasError, setHasError] = useState(false)

  useEffect(() => {
    let active = true
    dashboard.gestorMisProductos()
      .then((res) => { if (active) setItems(res.data.productos) })
      .catch(() => { if (active) setHasError(true) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return items
    return items.filter((p) => (p.codigo + ' ' + p.nombre + ' ' + p.programa.nombre + ' ' + (p.dependencia_responsable?.nombre || '')).toLowerCase().includes(q))
  }, [items, search])

  const activos = items.filter((p) => p.estado === 'ACTIVO').length
  const conDependencia = items.filter((p) => p.dependencia_responsable).length

  return <div className="space-y-6 pb-8">
    <section className="flex flex-col gap-5 rounded-[28px] bg-pine px-6 py-7 text-white shadow-[0_18px_40px_rgba(10,43,41,.16)] sm:flex-row sm:items-end sm:justify-between sm:px-8">
      <div><p className="text-xs font-bold uppercase tracking-[.2em] text-ochre-soft">Panel del gestor</p><h1 className="mt-2 text-3xl font-bold">Mis productos</h1><p className="mt-2 max-w-2xl text-sm text-white/70">Todos los productos asignados a su gestión, con su programa, dependencia responsable y estado.</p></div>
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
          <thead className="bg-paper/70 text-xs uppercase tracking-wider text-ink-faint"><tr><th className="px-5 py-3">Código</th><th className="px-4 py-3">Producto</th><th className="px-4 py-3">Programa</th><th className="hidden lg:table-cell px-4 py-3">Dependencia responsable</th><th className="px-4 py-3">Estado</th><th className="px-4 py-3">Última actualización</th></tr></thead>
          <tbody className="divide-y divide-line">
            {loading ? <tr><td colSpan={6} className="px-5 py-16 text-center text-ink-faint">Cargando productos...</td></tr> : filtered.length === 0 ? <tr><td colSpan={6} className="px-5 py-16 text-center text-ink-faint">No hay productos que coincidan con la búsqueda.</td></tr> : filtered.map((p) => <tr key={p.id} className="hover:bg-paper/45">
              <td className="px-5 py-4"><span className="font-mono text-xs font-bold text-pine">{p.codigo}</span></td>
              <td className="px-4 py-4"><p className="font-bold text-ink">{p.nombre}</p>{p.unidad_medida && <p className="mt-0.5 text-xs text-ink-faint">{p.unidad_medida}</p>}</td>
              <td className="max-w-[200px] px-4 py-4 text-ink-soft">{p.programa.nombre}</td>
              <td className="hidden lg:table-cell max-w-[190px] px-4 py-4 text-ink-soft">{p.dependencia_responsable?.nombre || 'Sin asignar'}</td>
              <td className="px-4 py-4"><EstadoBadge estado={p.estado} /></td>
              <td className="px-4 py-4 text-xs text-ink-faint">{formatDateOnly(p.updated_at)}</td>
            </tr>)}
          </tbody>
        </table>
      </div>
    </section>
  </div>
}