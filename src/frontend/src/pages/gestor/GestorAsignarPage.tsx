import { useEffect, useState, useCallback } from 'react'
import { gestores, productos } from '../../lib/api'
import type { Gestor, Producto } from '../../lib/types'
import { Icon, ModalShell } from '../../components/ui/icons'
import { clsx } from 'clsx'

export default function GestorAsignarPage() {
  const [gestoresList, setGestoresList] = useState<Gestor[]>([])
  const [productosList, setProductosList] = useState<Producto[]>([])
  const [loading, setLoading] = useState(true)
  const [searchProducto, setSearchProducto] = useState('')
  const [selectedGestor, setSelectedGestor] = useState<string>('')
  const [assignModal, setAssignModal] = useState<Producto | null>(null)
  const [assignLoading, setAssignLoading] = useState(false)
  const [success, setSuccess] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [gRes, pRes] = await Promise.allSettled([
        gestores.list({ page: 1, page_size: 100, estado: 'ACTIVO' }),
        productos.list({ page: 1, page_size: 100 }),
      ])
      if (gRes.status === 'fulfilled') setGestoresList(gRes.value.data.items)
      if (pRes.status === 'fulfilled') setProductosList(pRes.value.data.items)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const handleAssign = async (productoId: string, gestorLiderId: string) => {
    setAssignLoading(true)
    try {
      await productos.update(productoId, { gestor_lider_id: gestorLiderId || undefined })
      setAssignModal(null)
      setSuccess('Producto asignado correctamente.')
      setTimeout(() => setSuccess(''), 3000)
      load()
    } finally {
      setAssignLoading(false)
    }
  }

  const filtered = productosList.filter((p) => {
    if (searchProducto) {
      const q = searchProducto.toLowerCase()
      if (!p.codigo.toLowerCase().includes(q) && !p.nombre.toLowerCase().includes(q)) return false
    }
    if (selectedGestor && p.gestor_lider_id !== selectedGestor) return false
    return true
  })

  const getGestorName = (id?: string) => {
    if (!id) return 'Sin asignar'
    const g = gestoresList.find((g) => g.id === id)
    return g ? g.nombre_completo : 'Desconocido'
  }

  return (
    <div className="space-y-6 pb-8">
      <section className="relative overflow-hidden rounded-[28px] bg-pine px-6 py-7 text-white shadow-lg sm:px-8 sm:py-9">
        <div className="absolute -right-20 -top-24 h-72 w-72 rounded-full border border-white/10" aria-hidden="true" />
        <div className="relative">
          <p className="mb-2 text-xs font-bold uppercase tracking-[0.2em] text-ochre-soft">Gestor Líder</p>
          <h1 className="text-3xl font-bold leading-tight sm:text-4xl">Asignar Responsables</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-white/70">
            Asigne productos y defina responsables de metas para los miembros de su equipo.
          </p>
        </div>
      </section>

      {success && (
        <div className="flex items-center gap-3 rounded-2xl border border-forest/30 bg-forest-soft/60 px-4 py-3 text-sm text-forest">
          <Icon name="check" /> {success}
        </div>
      )}

      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 sm:max-w-xs">
          <Icon name="search" className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
          <input
            value={searchProducto}
            onChange={(e) => setSearchProducto(e.target.value)}
            placeholder="Buscar producto por código o nombre..."
            className="w-full rounded-xl border border-line bg-white py-2.5 pl-10 pr-4 text-sm text-ink outline-none focus:border-pine focus:ring-2 focus:ring-pine/10"
          />
        </div>
        <select
          value={selectedGestor}
          onChange={(e) => setSelectedGestor(e.target.value)}
          className="rounded-xl border border-line bg-white px-3 py-2.5 text-sm text-ink outline-none focus:border-pine"
        >
          <option value="">Todos los gestores</option>
          {gestoresList.map((g) => (
            <option key={g.id} value={g.id}>{g.nombre_completo}</option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="space-y-3">{[1, 2, 3, 4].map((i) => <div key={i} className="h-16 animate-pulse rounded-2xl bg-line/40" />)}</div>
      ) : filtered.length === 0 ? (
        <div className="flex min-h-48 flex-col items-center justify-center rounded-2xl border border-line bg-white text-center">
          <Icon name="box" className="h-10 w-10 text-ink-faint" />
          <h3 className="mt-4 text-lg font-bold text-ink">Sin productos</h3>
          <p className="mt-1 text-sm text-ink-faint">{searchProducto || selectedGestor ? 'No se encontraron resultados con los filtros aplicados.' : 'No hay productos disponibles para asignar.'}</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-line bg-white shadow-sm">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-line bg-paper text-[11px] font-bold uppercase tracking-wider text-ink-faint">
                <th className="px-5 py-3">Producto</th>
                <th className="hidden px-5 py-3 md:table-cell">Programa</th>
                <th className="hidden px-5 py-3 lg:table-cell">Meta</th>
                <th className="px-5 py-3">Responsable</th>
                <th className="px-5 py-3 text-right">Acción</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {filtered.map((p) => (
                <tr key={p.id} className="transition-colors hover:bg-paper">
                  <td className="px-5 py-4">
                    <div className="flex items-center gap-3">
                      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-forest-soft font-bold text-forest text-xs">
                        <Icon name="box" className="h-4 w-4" />
                      </span>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-pine">{p.codigo}</span>
                          <span className={clsx('inline-flex rounded-full px-2 py-0.5 text-[10px] font-bold', p.estado === 'ACTIVO' ? 'bg-forest-soft text-forest' : 'bg-line/60 text-ink-soft')}>{p.estado}</span>
                        </div>
                        <p className="mt-0.5 truncate font-bold text-ink">{p.nombre}</p>
                      </div>
                    </div>
                  </td>
                  <td className="hidden px-5 py-4 md:table-cell"><span className="text-xs text-ink-soft">{p.programa_nombre || '—'}</span></td>
                  <td className="hidden px-5 py-4 lg:table-cell"><span className="text-xs text-ink-soft">{p.meta_cuatrienio != null ? `${p.meta_cuatrienio.toLocaleString()} ${p.unidad_medida || ''}` : '—'}</span></td>
                  <td className="px-5 py-4">
                    <span className={clsx('text-xs font-bold', p.gestor_lider_id ? 'text-forest' : 'text-ink-faint')}>
                      {getGestorName(p.gestor_lider_id)}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-right">
                    <button
                      onClick={() => setAssignModal(p)}
                      className="rounded-xl bg-pine px-3 py-1.5 text-xs font-bold text-white transition-colors hover:bg-pine-deep"
                    >
                      <Icon name={p.gestor_lider_id ? 'edit' : 'plus'} className="mr-1 inline h-3 w-3" />
                      {p.gestor_lider_id ? 'Reasignar' : 'Asignar'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {assignModal && (
        <ModalShell title="Asignar responsable" close={() => setAssignModal(null)}>
          <div className="space-y-4">
            <div className="rounded-xl bg-paper p-4">
              <p className="text-[10px] font-bold uppercase text-ink-faint">Producto</p>
              <p className="mt-0.5 font-mono text-xs font-bold text-pine">{assignModal.codigo}</p>
              <p className="mt-0.5 font-bold text-ink">{assignModal.nombre}</p>
            </div>

            <div>
              <label className="text-xs font-bold uppercase text-ink-faint">Seleccionar gestor responsable</label>
              <select
                id="gestor-select"
                defaultValue={assignModal.gestor_lider_id || ''}
                className="mt-1 w-full rounded-xl border border-line px-4 py-2.5 text-sm outline-none focus:border-pine"
              >
                <option value="">Sin asignar</option>
                {gestoresList.map((g) => (
                  <option key={g.id} value={g.id}>{g.nombre_completo} ({g.codigo})</option>
                ))}
              </select>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button onClick={() => setAssignModal(null)} className="rounded-xl border border-line px-4 py-2 text-sm font-bold text-ink hover:bg-paper">Cancelar</button>
              <button
                onClick={() => {
                  const sel = document.getElementById('gestor-select') as HTMLSelectElement
                  handleAssign(assignModal.id, sel.value)
                }}
                disabled={assignLoading}
                className="rounded-xl bg-pine px-4 py-2 text-sm font-bold text-white hover:bg-pine-deep disabled:opacity-50"
              >
                {assignLoading ? 'Guardando...' : 'Guardar asignación'}
              </button>
            </div>
          </div>
        </ModalShell>
      )}
    </div>
  )
}
