import { useCallback, useEffect, useState } from 'react'
import { lineas, programas } from '../../lib/api'
import type { LineaEstrategica, Programa, ProgramaCreatePayload } from '../../lib/types'
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

export function ProgramasPage() {
  const [items, setItems] = useState<Programa[]>([])
  const [lineasList, setLineasList] = useState<LineaEstrategica[]>([])
  const [search, setSearch] = useState('')
  const [filtroLinea, setFiltroLinea] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [modal, setModal] = useState<'create' | 'edit' | null>(null)
  const [selected, setSelected] = useState<Programa | null>(null)
  const [form, setForm] = useState<ProgramaCreatePayload>({ codigo: '', nombre: '', sector: '', descripcion: '', linea_estrategica_id: '' })

  const loadLineas = useCallback(async () => {
    try { setLineasList((await lineas.list({ page: 1, page_size: 100 })).data.items) } catch { /* silent */ }
  }, [])

  useEffect(() => { loadLineas() }, [loadLineas])

  async function load() {
    setLoading(true); setError('')
    try {
      const params: Record<string, unknown> = { page: 1, page_size: 100 }
      if (search) params.search = search
      if (filtroLinea) params.linea_estrategica_id = filtroLinea
      setItems((await programas.list(params)).data.items)
    } catch { setError('No fue posible cargar los programas.') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [search, filtroLinea])

  function openCreate() {
    setSelected(null)
    setForm({ codigo: '', nombre: '', sector: '', descripcion: '', linea_estrategica_id: '' })
    setModal('create')
  }

  function openEdit(p: Programa) {
    setSelected(p)
    setForm({ codigo: p.codigo, nombre: p.nombre, sector: p.sector || '', descripcion: p.descripcion || '', linea_estrategica_id: p.linea_estrategica_id })
    setModal('edit')
  }

  async function save() {
    setSaving(true); setError('')
    try {
      if (selected) await programas.update(selected.id, { codigo: form.codigo, nombre: form.nombre, sector: form.sector, descripcion: form.descripcion })
      else await programas.create(form)
      setModal(null)
      await load()
    } catch (e) { setError(getErrorDetail(e)) }
    finally { setSaving(false) }
  }

  async function remove(p: Programa) {
    if (!window.confirm(`¿Eliminar el programa "${p.nombre}"? Esta acción quedará registrada en la auditoría.`)) return
    try { await programas.delete(p.id); await load() } catch { setError('No fue posible eliminar el programa.') }
  }

  const activos = items.filter((p) => p.estado === 'ACTIVO').length

  return <div className="space-y-6 pb-8">
    <section className="flex flex-col gap-5 rounded-[28px] bg-pine px-6 py-7 text-white shadow-[0_18px_40px_rgba(10,43,41,.16)] sm:flex-row sm:items-end sm:justify-between sm:px-8">
      <div><p className="text-xs font-bold uppercase tracking-[.2em] text-ochre-soft">Plan de desarrollo</p><h1 className="mt-2 text-3xl font-bold">Programas</h1><p className="mt-2 max-w-2xl text-sm text-white/70">Defina los programas que se ejecutarán dentro de cada línea estratégica del plan de desarrollo.</p></div>
      <div className="flex gap-2"><Button variant="ghost" onClick={load} className="border border-white/20 text-white hover:bg-white/10"><Icon name="refresh" />Actualizar</Button><Button onClick={openCreate} className="bg-ochre hover:bg-ochre-deep"><Icon name="plus" />Nuevo programa</Button></div>
    </section>

    <div className="grid grid-cols-2 gap-3 lg:grid-cols-3">
      {[['Total de programas', items.length, 'text-pine'], ['Activos', activos, 'text-forest'], ['Inactivos', items.length - activos, 'text-ink-faint']].map(([label, value, tone]) => <div key={label} className="rounded-2xl border border-line bg-white p-4 shadow-sm"><p className="text-xs font-bold uppercase tracking-wider text-ink-faint">{label}</p><p className={`mt-2 text-3xl font-bold ${tone}`}>{value}</p></div>)}
    </div>

    {error && <div role="alert" className="rounded-xl border border-warn/30 bg-warn-soft px-4 py-3 text-sm text-warn">{error}</div>}

    <section className="overflow-visible rounded-2xl border border-line bg-white shadow-sm">
      <div className="flex flex-col gap-3 border-b border-line p-4 sm:flex-row sm:items-center">
        <div className="relative flex-1"><span className="absolute left-3 top-3 text-ink-faint"><Icon name="search" /></span><input aria-label="Buscar programas" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Buscar por código o nombre..." className={`${selectClass} pl-10`} /></div>
        <select aria-label="Filtrar por línea estratégica" className={`${selectClass} sm:w-56`} value={filtroLinea} onChange={(e) => setFiltroLinea(e.target.value)}><option value="">Todas las líneas</option>{lineasList.map((l) => <option key={l.id} value={l.id}>{l.nombre}</option>)}</select>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[980px] text-left text-sm">
          <thead className="bg-paper/70 text-xs uppercase tracking-wider text-ink-faint"><tr><th className="px-5 py-3">Código</th><th className="px-4 py-3">Programa</th><th className="px-4 py-3">Sector</th><th className="hidden lg:table-cell px-4 py-3">Descripción</th><th className="px-4 py-3">Línea estratégica</th><th className="px-4 py-3">Estado</th><th className="px-5 py-3 text-right">Acciones</th></tr></thead>
          <tbody className="divide-y divide-line">
            {loading ? <tr><td colSpan={7} className="px-5 py-16 text-center text-ink-faint">Cargando programas...</td></tr> : items.length === 0 ? <tr><td colSpan={7} className="px-5 py-16 text-center text-ink-faint">No hay programas que coincidan con la búsqueda.</td></tr> : items.map((p) => <tr key={p.id} className="hover:bg-paper/45">
              <td className="px-5 py-4"><span className="font-mono text-xs font-bold text-pine">{p.codigo}</span></td>
              <td className="px-4 py-4"><p className="font-bold text-ink">{p.nombre}</p></td>
              <td className="px-4 py-4"><span className="rounded-lg bg-ochre-soft px-2.5 py-1 text-xs font-bold text-ochre">{p.sector || '-'}</span></td>
              <td className="hidden lg:table-cell max-w-sm px-4 py-4 text-xs text-ink-faint">{p.descripcion || '-'}</td>
              <td className="px-4 py-4"><span className="rounded-lg bg-forest-soft px-2.5 py-1 text-xs font-bold text-forest">{p.linea_estrategica_nombre || 'Sin línea'}</span></td>
              <td className="px-4 py-4"><EstadoBadge estado={p.estado} /></td>
              <td className="px-5 py-4 text-right"><div className="inline-flex items-center justify-end gap-0.5" aria-label={`Acciones para ${p.nombre}`}>
                <ActionButton label="Editar" onClick={() => openEdit(p)}><Icon name="edit" /></ActionButton>
                <ActionButton label="Eliminar" danger onClick={() => remove(p)}><Icon name="trash" /></ActionButton>
              </div></td>
            </tr>)}
          </tbody>
        </table>
      </div>
    </section>

    {modal === 'create' && <ModalShell title="Nuevo programa" description="El programa se asociará a una línea estratégica." close={() => setModal(null)}>
      <div className="grid gap-4 p-6">
        <ProgramaFields form={form} setForm={setForm} lineas={lineasList} editing={false} />
      </div>
      <footer className="flex justify-end gap-3 border-t border-line px-6 py-4"><Button variant="ghost" onClick={() => setModal(null)}>Cancelar</Button><Button loading={saving} disabled={!form.codigo || !form.nombre || !form.linea_estrategica_id} onClick={save}>Crear programa</Button></footer>
    </ModalShell>}

    {modal === 'edit' && selected && <ModalShell title="Editar programa" description={`Actualice la información de "${selected.nombre}".`} close={() => setModal(null)}>
      <div className="grid gap-4 p-6">
        <ProgramaFields form={form} setForm={setForm} lineas={lineasList} editing />
        {selected.linea_estrategica_nombre && <div className="rounded-xl bg-paper p-3 text-xs text-ink-soft">La línea estratégica «{selected.linea_estrategica_nombre}» no se puede modificar en esta versión.</div>}
      </div>
      <footer className="flex justify-end gap-3 border-t border-line px-6 py-4"><Button variant="ghost" onClick={() => setModal(null)}>Cancelar</Button><Button loading={saving} disabled={!form.codigo || !form.nombre} onClick={save}>Guardar cambios</Button></footer>
    </ModalShell>}
  </div>
}

function ProgramaFields({ form, setForm, lineas, editing }: { form: ProgramaCreatePayload; setForm: (f: ProgramaCreatePayload) => void; lineas: LineaEstrategica[]; editing: boolean }) {
  const field = 'text-sm font-bold text-ink'
  return <><div><label className={field}>Código <span className="text-warn">*</span></label><input value={form.codigo} onChange={(e) => setForm({ ...form, codigo: e.target.value })} placeholder="Ej: 1903" className={`${selectClass} mt-1`} /></div><div><label className={field}>Nombre <span className="text-warn">*</span></label><input value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} placeholder="Nombre del programa" className={`${selectClass} mt-1`} /></div><div><label className={field}>Sector</label><input value={form.sector || ''} onChange={(e) => setForm({ ...form, sector: e.target.value })} placeholder="Ej: Salud" className={`${selectClass} mt-1`} /></div><div><label className={field}>Descripción</label><textarea value={form.descripcion || ''} onChange={(e) => setForm({ ...form, descripcion: e.target.value })} rows={3} className={`${selectClass} mt-1 resize-none`} /></div>{!editing && <div><label className={field}>Línea estratégica <span className="text-warn">*</span></label><select value={form.linea_estrategica_id} onChange={(e) => setForm({ ...form, linea_estrategica_id: e.target.value })} className={`${selectClass} mt-1`}><option value="">Seleccionar línea</option>{lineas.map((l) => <option key={l.id} value={l.id}>{l.codigo} - {l.nombre}</option>)}</select></div>}</>
}