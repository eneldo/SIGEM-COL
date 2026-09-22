import { useCallback, useEffect, useState } from 'react'
import { configDependencias } from '../../lib/api'
import type { Dependencia, DependenciaCreatePayload } from '../../lib/types'
import { Button } from '../../components/ui/Button'
import { EstadoBadge, Icon, ModalShell, selectClass } from '../../components/ui/icons'

function ActionButton({ label, onClick, danger = false, children }: { label: string; onClick: () => void; danger?: boolean; children: React.ReactNode }) {
  return <button type="button" title={label} aria-label={label} onClick={onClick} className={`inline-flex h-8 w-8 items-center justify-center rounded-lg border transition-colors ${danger ? 'border-warn/20 text-warn hover:bg-warn-soft' : 'border-line text-pine hover:border-pine/30 hover:bg-forest-soft'}`}><span className="sr-only">{label}</span>{children}</button>
}

function getErrorDetail(e: unknown): string {
  const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return 'Verifique los campos del formulario'
  return 'No fue posible guardar los cambios.'
}

export default function DependenciasPage() {
  const [items, setItems] = useState<Dependencia[]>([])
  const [dependenciasList, setDependenciasList] = useState<Dependencia[]>([])
  const [search, setSearch] = useState('')
  const [filtroEstado, setFiltroEstado] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [modal, setModal] = useState<'create' | 'edit' | null>(null)
  const [selected, setSelected] = useState<Dependencia | null>(null)
  const [form, setForm] = useState<DependenciaCreatePayload>({
    codigo: '', nombre: '', descripcion: '', dependencia_padre_id: '', nivel: 1, estado: 'ACTIVA',
  })

  const loadDependencias = useCallback(async () => {
    try {
      const resp = await configDependencias.list({ page: 1, page_size: 200 })
      setDependenciasList(resp.data.items)
    } catch { /* silent */ }
  }, [])

  useEffect(() => { loadDependencias() }, [loadDependencias])

  async function load() {
    setLoading(true); setError('')
    try {
      const params: Record<string, unknown> = { page: 1, page_size: 100 }
      if (search) params.search = search
      if (filtroEstado) params.estado = filtroEstado
      setItems((await configDependencias.list(params)).data.items)
    } catch { setError('No fue posible cargar las dependencias.') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [search, filtroEstado])

  function openCreate() {
    setSelected(null)
    setForm({ codigo: '', nombre: '', descripcion: '', dependencia_padre_id: '', nivel: 1, estado: 'ACTIVA' })
    setModal('create')
  }

  function openEdit(d: Dependencia) {
    setSelected(d)
    setForm({
      codigo: d.codigo,
      nombre: d.nombre,
      descripcion: d.descripcion || '',
      dependencia_padre_id: d.dependencia_padre_id || '',
      nivel: d.nivel || 1,
      estado: d.estado,
    })
    setModal('edit')
  }

  async function save() {
    setSaving(true); setError('')
    try {
      if (selected) {
        const updateData: Record<string, unknown> = {}
        if (form.nombre) updateData.nombre = form.nombre
        if (form.descripcion !== undefined) updateData.descripcion = form.descripcion
        if (form.nivel) updateData.nivel = form.nivel
        if (form.estado) updateData.estado = form.estado
        if (form.dependencia_padre_id !== undefined) updateData.dependencia_padre_id = form.dependencia_padre_id || null
        await configDependencias.update(selected.id, updateData)
      } else {
        await configDependencias.create(form)
      }
      setModal(null)
      await load()
      await loadDependencias()
    } catch (e) { setError(getErrorDetail(e)) }
    finally { setSaving(false) }
  }

  async function remove(d: Dependencia) {
    if (!window.confirm(`¿Eliminar la dependencia "${d.nombre}"? Esta acción quedará registrada en la auditoría.`)) return
    try { await configDependencias.delete(d.id); await load(); await loadDependencias() }
    catch { setError('No fue posible eliminar la dependencia.') }
  }

  const activas = items.filter((d) => d.estado === 'ACTIVA').length

  return <div className="space-y-6 pb-8">
    <section className="flex flex-col gap-5 rounded-[28px] bg-pine px-6 py-7 text-white shadow-[0_18px_40px_rgba(10,43,41,.16)] sm:flex-row sm:items-end sm:justify-between sm:px-8">
      <div><p className="text-xs font-bold uppercase tracking-[.2em] text-ochre-soft">Configuración</p><h1 className="mt-2 text-3xl font-bold">Dependencias del municipio</h1><p className="mt-2 max-w-2xl text-sm text-white/70">Administre las dependencias organizacionales, asigne jerarquías y gestione la estructura institucional.</p></div>
      <div className="flex gap-2"><Button variant="ghost" onClick={load} className="border border-white/20 text-white hover:bg-white/10"><Icon name="refresh" />Actualizar</Button><Button onClick={openCreate} className="bg-ochre hover:bg-ochre-deep"><Icon name="plus" />Nueva dependencia</Button></div>
    </section>

    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {[['Total dependencias', items.length, 'text-pine'], ['Activas', activas, 'text-forest'], ['Inactivas', items.length - activas, 'text-ink-faint'], ['Con padre', items.filter((d) => d.dependencia_padre_id).length, 'text-ochre-deep']].map(([label, value, tone]) => <div key={label} className="rounded-2xl border border-line bg-white p-4 shadow-sm"><p className="text-xs font-bold uppercase tracking-wider text-ink-faint">{label}</p><p className={`mt-2 text-3xl font-bold ${tone}`}>{value}</p></div>)}
    </div>

    {error && <div role="alert" className="rounded-xl border border-warn/30 bg-warn-soft px-4 py-3 text-sm text-warn">{error}</div>}

    <section className="overflow-visible rounded-2xl border border-line bg-white shadow-sm">
      <div className="flex flex-col gap-3 border-b border-line p-4 lg:flex-row lg:items-center">
        <div className="relative flex-1"><span className="absolute left-3 top-3 text-ink-faint"><Icon name="search" /></span><input aria-label="Buscar dependencias" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Buscar por nombre o código..." className={`${selectClass} pl-10`} /></div>
        <select aria-label="Filtrar por estado" className={`${selectClass} lg:w-40`} value={filtroEstado} onChange={(e) => setFiltroEstado(e.target.value)}><option value="">Todos los estados</option><option value="ACTIVO">Activas</option><option value="INACTIVO">Inactivas</option></select>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[800px] text-left text-sm">
          <thead className="bg-paper/70 text-xs uppercase tracking-wider text-ink-faint"><tr><th className="px-5 py-3">Código</th><th className="px-4 py-3">Nombre</th><th className="hidden lg:table-cell px-4 py-3">Descripción</th><th className="px-4 py-3">Nivel</th><th className="px-4 py-3">Estado</th><th className="px-5 py-3 text-right">Acciones</th></tr></thead>
          <tbody className="divide-y divide-line">
            {loading ? <tr><td colSpan={6} className="px-5 py-16 text-center text-ink-faint">Cargando dependencias...</td></tr> : items.length === 0 ? <tr><td colSpan={6} className="px-5 py-16 text-center text-ink-faint">No hay dependencias que coincidan con la búsqueda.</td></tr> : items.map((d) => <tr key={d.id} className="hover:bg-paper/45">
              <td className="px-5 py-4"><span className="font-mono text-xs font-bold text-pine">{d.codigo}</span></td>
              <td className="px-4 py-4"><p className="font-bold text-ink">{d.nombre}</p>{d.dependencia_padre_id && <p className="mt-0.5 text-xs text-ink-faint">Padre: {dependenciasList.find((p) => p.id === d.dependencia_padre_id)?.nombre || 'N/A'}</p>}</td>
              <td className="hidden lg:table-cell max-w-[200px] px-4 py-4 text-ink-soft truncate">{d.descripcion || '-'}</td>
              <td className="px-4 py-4 text-center"><span className="rounded-lg bg-forest-soft px-2.5 py-1 text-xs font-bold text-forest">Nv. {d.nivel}</span></td>
              <td className="px-4 py-4"><EstadoBadge estado={d.estado} /></td>
              <td className="px-5 py-4 text-right"><div className="inline-flex items-center justify-end gap-0.5" aria-label={`Acciones para ${d.nombre}`}>
                <ActionButton label="Editar" onClick={() => openEdit(d)}><Icon name="edit" /></ActionButton>
                <ActionButton label="Eliminar" danger onClick={() => remove(d)}><Icon name="trash" /></ActionButton>
              </div></td>
            </tr>)}
          </tbody>
        </table>
      </div>
    </section>

    {(modal === 'create' || modal === 'edit') && <ModalShell title={modal === 'create' ? 'Nueva dependencia' : 'Editar dependencia'} description={modal === 'create' ? 'Registre una nueva dependencia en el municipio.' : `Actualice la información de "${selected?.nombre}".`} close={() => setModal(null)} wide>
      <div className="grid gap-4 p-6 sm:grid-cols-2">
        <div><label className="text-sm font-bold text-ink">Código <span className="text-warn">*</span></label><input value={form.codigo} onChange={(e) => setForm({ ...form, codigo: e.target.value })} placeholder="Ej: DEP-001" className={`${selectClass} mt-1`} disabled={modal === 'edit'} /></div>
        <div><label className="text-sm font-bold text-ink">Nivel jerárquico <span className="text-warn">*</span></label><select value={form.nivel} onChange={(e) => setForm({ ...form, nivel: Number(e.target.value) })} className={`${selectClass} mt-1`}><option value={1}>1 - Secretaría / Dirección</option><option value={2}>2 - Subdirección / Coordinación</option><option value={3}>3 - Oficina / Grupo</option><option value={4}>4 - Sección</option><option value={5}>5 - Subsección</option></select></div>
        <div className="sm:col-span-2"><label className="text-sm font-bold text-ink">Nombre <span className="text-warn">*</span></label><input value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} placeholder="Ej: Secretaría de Planeación" className={`${selectClass} mt-1`} /></div>
        <div className="sm:col-span-2"><label className="text-sm font-bold text-ink">Descripción</label><textarea value={form.descripcion || ''} onChange={(e) => setForm({ ...form, descripcion: e.target.value })} rows={3} className={`${selectClass} mt-1`} placeholder="Descripción opcional de la dependencia..." /></div>
        <div><label className="text-sm font-bold text-ink">Dependencia padre</label><select value={form.dependencia_padre_id || ''} onChange={(e) => setForm({ ...form, dependencia_padre_id: e.target.value })} className={`${selectClass} mt-1`}><option value="">Sin padre (raíz)</option>{dependenciasList.filter((d) => d.id !== selected?.id).map((d) => <option key={d.id} value={d.id}>{d.codigo} - {d.nombre}</option>)}</select></div>
        <div><label className="text-sm font-bold text-ink">Estado</label><select value={form.estado} onChange={(e) => setForm({ ...form, estado: e.target.value })} className={`${selectClass} mt-1`}><option value="ACTIVA">Activa</option><option value="INACTIVA">Inactiva</option></select></div>
      </div>
      <footer className="flex justify-end gap-3 border-t border-line px-6 py-4"><Button variant="ghost" onClick={() => setModal(null)}>Cancelar</Button><Button loading={saving} disabled={!form.codigo || !form.nombre} onClick={save}>{modal === 'create' ? 'Crear dependencia' : 'Guardar cambios'}</Button></footer>
    </ModalShell>}
  </div>
}
