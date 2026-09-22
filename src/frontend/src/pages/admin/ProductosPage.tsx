import { useCallback, useEffect, useState } from 'react'
import { programas, productos } from '../../lib/api'
import type { Producto, ProductoCreatePayload, Programa } from '../../lib/types'
import { Button } from '../../components/ui/Button'
import { EstadoBadge, Icon, ModalShell, formatDateOnly, selectClass } from '../../components/ui/icons'

function ActionButton({ label, onClick, danger = false, children }: { label: string; onClick: () => void; danger?: boolean; children: React.ReactNode }) {
  return <button type="button" title={label} aria-label={label} onClick={onClick} className={`inline-flex h-8 w-8 items-center justify-center rounded-lg border transition-colors ${danger ? 'border-warn/20 text-warn hover:bg-warn-soft' : 'border-line text-pine hover:border-pine/30 hover:bg-forest-soft'}`}><span className="sr-only">{label}</span>{children}</button>
}

function getErrorDetail(e: unknown): string {
  const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return 'Verifique los campos del formulario'
  return 'No fue posible guardar los cambios.'
}

export function ProductosPage() {
  const [items, setItems] = useState<Producto[]>([])
  const [programasList, setProgramasList] = useState<Programa[]>([])
  const [search, setSearch] = useState('')
  const [filtroPrograma, setFiltroPrograma] = useState('')
  const [filtroEstado, setFiltroEstado] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [modal, setModal] = useState<'create' | 'edit' | null>(null)
  const [selected, setSelected] = useState<Producto | null>(null)
  const [form, setForm] = useState<ProductoCreatePayload>({ codigo: '', nombre: '', descripcion: '', unidad_medida: '', programa_id: '', dependencia_responsable_id: '', gestor_lider_id: '' })

  const loadCatalogos = useCallback(async () => {
    try {
      const progs = await programas.list({ page: 1, page_size: 100 })
      setProgramasList(progs.data.items)
    } catch { /* silent */ }
  }, [])

  useEffect(() => { loadCatalogos() }, [loadCatalogos])

  async function load() {
    setLoading(true); setError('')
    try {
      const params: Record<string, unknown> = { page: 1, page_size: 100 }
      if (search) params.search = search
      if (filtroPrograma) params.programa_id = filtroPrograma
      if (filtroEstado) params.estado = filtroEstado
      setItems((await productos.list(params)).data.items)
    } catch { setError('No fue posible cargar los productos.') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [search, filtroPrograma, filtroEstado])

  function openCreate() {
    setSelected(null)
    setForm({ codigo: '', nombre: '', codigo_indicador: '', indicador: '', meta_redactada: '', linea_base: 0, meta_cuatrienio: 0, descripcion: '', unidad_medida: '', programa_id: '', dependencia_responsable_id: '', gestor_lider_id: '' })
    setModal('create')
  }

  function openEdit(p: Producto) {
    setSelected(p)
    setForm({ codigo: p.codigo, nombre: p.nombre, codigo_indicador: p.codigo_indicador || '', indicador: p.indicador || '', meta_redactada: p.meta_redactada || '', linea_base: p.linea_base || 0, meta_cuatrienio: p.meta_cuatrienio || 0, descripcion: p.descripcion || '', unidad_medida: p.unidad_medida || '', programa_id: p.programa_id, dependencia_responsable_id: p.dependencia_responsable_id || '', gestor_lider_id: p.gestor_lider_id || '' })
    setModal('edit')
  }

  async function save() {
    setSaving(true); setError('')
    try {
      if (selected) await productos.update(selected.id, { codigo: form.codigo, nombre: form.nombre, codigo_indicador: form.codigo_indicador, indicador: form.indicador, meta_redactada: form.meta_redactada, linea_base: form.linea_base, meta_cuatrienio: form.meta_cuatrienio, dependencia_responsable_id: form.dependencia_responsable_id || undefined, gestor_lider_id: form.gestor_lider_id || undefined })
      else await productos.create({ ...form, dependencia_responsable_id: form.dependencia_responsable_id || undefined, gestor_lider_id: form.gestor_lider_id || undefined })
      setModal(null)
      await load()
    } catch (e) { setError(getErrorDetail(e)) }
    finally { setSaving(false) }
  }

  async function remove(p: Producto) {
    if (!window.confirm(`¿Eliminar el producto "${p.nombre}"? Esta acción quedará registrada en la auditoría.`)) return
    try { await productos.delete(p.id); await load() } catch { setError('No fue posible eliminar el producto.') }
  }

  const activos = items.filter((p) => p.estado === 'ACTIVO').length

  return <div className="space-y-6 pb-8">
    <section className="flex flex-col gap-5 rounded-[28px] bg-pine px-6 py-7 text-white shadow-[0_18px_40px_rgba(10,43,41,.16)] sm:flex-row sm:items-end sm:justify-between sm:px-8">
      <div><p className="text-xs font-bold uppercase tracking-[.2em] text-ochre-soft">Plan de desarrollo</p><h1 className="mt-2 text-3xl font-bold">Productos</h1><p className="mt-2 max-w-2xl text-sm text-white/70">Registre los productos y entregables de cada programa, con su dependencia responsable y gestor líder asignado.</p></div>
      <div className="flex gap-2"><Button variant="ghost" onClick={load} className="border border-white/20 text-white hover:bg-white/10"><Icon name="refresh" />Actualizar</Button><Button onClick={openCreate} className="bg-ochre hover:bg-ochre-deep"><Icon name="plus" />Nuevo producto</Button></div>
    </section>

    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {[['Total de productos', items.length, 'text-pine'], ['Activos', activos, 'text-forest'], ['Inactivos', items.length - activos, 'text-ink-faint'], ['Con gestor asignado', items.filter((p) => p.gestor_lider_id).length, 'text-ochre-deep']].map(([label, value, tone]) => <div key={label} className="rounded-2xl border border-line bg-white p-4 shadow-sm"><p className="text-xs font-bold uppercase tracking-wider text-ink-faint">{label}</p><p className={`mt-2 text-3xl font-bold ${tone}`}>{value}</p></div>)}
    </div>

    {error && <div role="alert" className="rounded-xl border border-warn/30 bg-warn-soft px-4 py-3 text-sm text-warn">{error}</div>}

    <section className="overflow-visible rounded-2xl border border-line bg-white shadow-sm">
      <div className="flex flex-col gap-3 border-b border-line p-4 lg:flex-row lg:items-center">
        <div className="relative flex-1"><span className="absolute left-3 top-3 text-ink-faint"><Icon name="search" /></span><input aria-label="Buscar productos" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Buscar por código o nombre..." className={`${selectClass} pl-10`} /></div>
        <select aria-label="Filtrar por programa" className={`${selectClass} lg:w-56`} value={filtroPrograma} onChange={(e) => setFiltroPrograma(e.target.value)}><option value="">Todos los programas</option>{programasList.map((p) => <option key={p.id} value={p.id}>{p.nombre}</option>)}</select>
        <select aria-label="Filtrar por estado" className={`${selectClass} lg:w-40`} value={filtroEstado} onChange={(e) => setFiltroEstado(e.target.value)}><option value="">Todos los estados</option><option value="ACTIVO">Activos</option><option value="INACTIVO">Inactivos</option></select>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[1100px] text-left text-sm">
          <thead className="bg-paper/70 text-xs uppercase tracking-wider text-ink-faint"><tr><th className="px-5 py-3">Código</th><th className="px-4 py-3">Producto</th><th className="px-4 py-3">Programa</th><th className="hidden lg:table-cell px-4 py-3">Indicador</th><th className="hidden lg:table-cell px-4 py-3">Meta cuatrienio</th><th className="px-4 py-3">Estado</th><th className="px-4 py-3">Actualizado</th><th className="px-5 py-3 text-right">Acciones</th></tr></thead>
          <tbody className="divide-y divide-line">
            {loading ? <tr><td colSpan={8} className="px-5 py-16 text-center text-ink-faint">Cargando productos...</td></tr> : items.length === 0 ? <tr><td colSpan={8} className="px-5 py-16 text-center text-ink-faint">No hay productos que coincidan con la búsqueda.</td></tr> : items.map((p) => <tr key={p.id} className="hover:bg-paper/45">
              <td className="px-5 py-4"><span className="font-mono text-xs font-bold text-pine">{p.codigo}</span></td>
              <td className="px-4 py-4"><p className="font-bold text-ink">{p.nombre}</p>{p.indicador && <p className="mt-0.5 text-xs text-ink-faint">{p.indicador}</p>}</td>
              <td className="max-w-[180px] px-4 py-4 text-ink-soft">{p.programa_nombre || '-'}</td>
              <td className="hidden lg:table-cell max-w-[170px] px-4 py-4 text-ink-soft">{p.codigo_indicador || '-'}</td>
              <td className="hidden lg:table-cell px-4 py-4"><span className="rounded-lg bg-forest-soft px-2.5 py-1 text-xs font-bold text-forest">{p.meta_cuatrienio || 0}</span></td>
              <td className="px-4 py-4"><EstadoBadge estado={p.estado} /></td>
              <td className="px-4 py-4 text-xs text-ink-faint">{formatDateOnly(p.updated_at)}</td>
              <td className="px-5 py-4 text-right"><div className="inline-flex items-center justify-end gap-0.5" aria-label={`Acciones para ${p.nombre}`}>
                <ActionButton label="Editar" onClick={() => openEdit(p)}><Icon name="edit" /></ActionButton>
                <ActionButton label="Eliminar" danger onClick={() => remove(p)}><Icon name="trash" /></ActionButton>
              </div></td>
            </tr>)}
          </tbody>
        </table>
      </div>
    </section>

    {(modal === 'create' || modal === 'edit') && <ModalShell title={modal === 'create' ? 'Nuevo producto' : 'Editar producto'} description={modal === 'create' ? 'Asocie el producto a un programa y defina su indicador.' : `Actualice la información de "${selected?.nombre}".`} close={() => setModal(null)} wide>
      <div className="grid gap-4 p-6 sm:grid-cols-2">
        <div><label className="text-sm font-bold text-ink">Programa <span className="text-warn">*</span></label><select value={form.programa_id} onChange={(e) => setForm({ ...form, programa_id: e.target.value })} className={`${selectClass} mt-1`}><option value="">Seleccionar programa</option>{programasList.map((p) => <option key={p.id} value={p.id}>{p.nombre}</option>)}</select></div>
        <div><label className="text-sm font-bold text-ink">Código producto <span className="text-warn">*</span></label><input value={form.codigo} onChange={(e) => setForm({ ...form, codigo: e.target.value })} placeholder="Ej: 1903031" className={`${selectClass} mt-1`} /></div>
        <div className="sm:col-span-2"><label className="text-sm font-bold text-ink">Nombre producto <span className="text-warn">*</span></label><input value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} className={`${selectClass} mt-1`} /></div>
        <div><label className="text-sm font-bold text-ink">Código indicador</label><input value={form.codigo_indicador || ''} onChange={(e) => setForm({ ...form, codigo_indicador: e.target.value })} placeholder="Ej: 190500400" className={`${selectClass} mt-1`} /></div>
        <div><label className="text-sm font-bold text-ink">Indicador</label><input value={form.indicador || ''} onChange={(e) => setForm({ ...form, indicador: e.target.value })} placeholder="Ej: % de cumplimiento..." className={`${selectClass} mt-1`} /></div>
        <div className="sm:col-span-2"><label className="text-sm font-bold text-ink">Meta redactada</label><textarea value={form.meta_redactada || ''} onChange={(e) => setForm({ ...form, meta_redactada: e.target.value })} rows={2} placeholder="Descripción de la meta cuatrienal..." className={`${selectClass} mt-1 resize-none`} /></div>
        <div><label className="text-sm font-bold text-ink">Línea base</label><input type="number" value={form.linea_base || 0} onChange={(e) => setForm({ ...form, linea_base: parseInt(e.target.value) || 0 })} className={`${selectClass} mt-1`} /></div>
        <div><label className="text-sm font-bold text-ink">Meta cuatrienio</label><input type="number" value={form.meta_cuatrienio || 0} onChange={(e) => setForm({ ...form, meta_cuatrienio: parseInt(e.target.value) || 0 })} className={`${selectClass} mt-1`} /></div>
      </div>
      <footer className="flex justify-end gap-3 border-t border-line px-6 py-4"><Button variant="ghost" onClick={() => setModal(null)}>Cancelar</Button><Button loading={saving} disabled={!form.codigo || !form.nombre || !form.programa_id} onClick={save}>{modal === 'create' ? 'Crear producto' : 'Guardar cambios'}</Button></footer>
    </ModalShell>}
  </div>
}