import { useEffect, useState } from 'react'
import { dashboard, lineas } from '../../lib/api'
import type { LineaCreatePayload, LineaEstrategica, PlanResumen } from '../../lib/types'
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

export function LineasPage() {
  const [items, setItems] = useState<LineaEstrategica[]>([])
  const [plan, setPlan] = useState<PlanResumen | null>(null)
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [modal, setModal] = useState<'create' | 'edit' | null>(null)
  const [selected, setSelected] = useState<LineaEstrategica | null>(null)
  const [form, setForm] = useState<LineaCreatePayload>({ numero: '', nombre: '', descripcion: '', plan_desarrollo_id: '' })

  async function load() {
    setLoading(true); setError('')
    try {
      const res = await lineas.list({ page: 1, page_size: 100, search: search || undefined })
      setItems(res.data.items)
    } catch { setError('No fue posible cargar las líneas estratégicas.') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [search])

  useEffect(() => {
    dashboard.adminResumenPlan().then((res) => setPlan(res.data)).catch(() => setPlan(null))
  }, [])

  function openCreate() {
    if (!plan) return
    setSelected(null)
    setForm({ numero: '', nombre: '', descripcion: '', plan_desarrollo_id: plan.plan.id })
    setModal('create')
  }

  function openEdit(linea: LineaEstrategica) {
    setSelected(linea)
    setForm({ numero: linea.numero || '', nombre: linea.nombre, descripcion: linea.descripcion || '', plan_desarrollo_id: linea.plan_desarrollo_id })
    setModal('edit')
  }

  async function save() {
    if (!selected && !form.plan_desarrollo_id) return
    setSaving(true); setError('')
    try {
      if (selected) await lineas.update(selected.id, { numero: form.numero, nombre: form.nombre, descripcion: form.descripcion })
      else await lineas.create(form)
      setModal(null)
      await load(); await refreshPlan()
    } catch (e) { setError(getErrorDetail(e)) }
    finally { setSaving(false) }
  }

  async function refreshPlan() {
    try { setPlan((await dashboard.adminResumenPlan()).data) } catch { /* sin plan */ }
  }

  async function remove(linea: LineaEstrategica) {
    if (!window.confirm(`¿Eliminar la línea estratégica "${linea.nombre}"? Esta acción quedará registrada en la auditoría.`)) return
    try { await lineas.delete(linea.id); await load(); await refreshPlan() } catch { setError('No fue posible eliminar la línea estratégica.') }
  }

  const activas = items.filter((l) => l.estado === 'ACTIVA').length

  return <div className="space-y-6 pb-8">
    <section className="flex flex-col gap-5 rounded-[28px] bg-pine px-6 py-7 text-white shadow-[0_18px_40px_rgba(10,43,41,.16)] sm:flex-row sm:items-end sm:justify-between sm:px-8">
      <div><p className="text-xs font-bold uppercase tracking-[.2em] text-ochre-soft">Plan de desarrollo</p><h1 className="mt-2 text-3xl font-bold">Líneas estratégicas</h1><p className="mt-2 max-w-2xl text-sm text-white/70">Organice los ejes del plan de desarrollo municipal. Cada línea agrupa los programas y productos de la gestión.</p></div>
      <div className="flex gap-2"><Button variant="ghost" onClick={load} className="border border-white/20 text-white hover:bg-white/10"><Icon name="refresh" />Actualizar</Button><Button onClick={openCreate} disabled={!plan} className="bg-ochre hover:bg-ochre-deep"><Icon name="plus" />Nueva línea</Button></div>
    </section>

    {plan && (
      <div className="flex flex-col gap-3 rounded-2xl border border-line bg-white p-4 shadow-sm sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-forest-soft text-forest"><Icon name="layers" /></div>
          <div><p className="text-sm font-bold text-ink">{plan.plan.nombre}</p><p className="text-xs text-ink-faint">{plan.plan.codigo} · {formatDateOnly(plan.plan.fecha_inicio)} — {formatDateOnly(plan.plan.fecha_fin)} · {plan.plan.vigencias} vigencias</p></div>
        </div>
        <p className="text-xs text-ink-faint">Las líneas nuevas se asocian automáticamente a este plan.</p>
      </div>
    )}

    <div className="grid grid-cols-2 gap-3 lg:grid-cols-3">
      {[['Total de líneas', items.length, 'text-pine'], ['Activas', activas, 'text-forest'], ['Inactivas', items.length - activas, 'text-ink-faint']].map(([label, value, tone]) => <div key={label} className="rounded-2xl border border-line bg-white p-4 shadow-sm"><p className="text-xs font-bold uppercase tracking-wider text-ink-faint">{label}</p><p className={`mt-2 text-3xl font-bold ${tone}`}>{value}</p></div>)}
    </div>

    {error && <div role="alert" className="rounded-xl border border-warn/30 bg-warn-soft px-4 py-3 text-sm text-warn">{error}</div>}

    <section className="overflow-visible rounded-2xl border border-line bg-white shadow-sm">
      <div className="flex flex-col gap-3 border-b border-line p-4 sm:flex-row sm:items-center">
        <div className="relative flex-1"><span className="absolute left-3 top-3 text-ink-faint"><Icon name="search" /></span><input aria-label="Buscar líneas" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Buscar por código o nombre..." className={`${selectClass} pl-10`} /></div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[980px] text-left text-sm">
          <thead className="bg-paper/70 text-xs uppercase tracking-wider text-ink-faint"><tr><th className="px-5 py-3">Código</th><th className="px-4 py-3">Número</th><th className="px-4 py-3">Línea estratégica</th><th className="hidden md:table-cell px-4 py-3">Plan de desarrollo</th><th className="px-4 py-3">Estado</th><th className="px-5 py-3 text-right">Acciones</th></tr></thead>
          <tbody className="divide-y divide-line">
            {loading ? <tr><td colSpan={6} className="px-5 py-16 text-center text-ink-faint">Cargando líneas estratégicas...</td></tr> : items.length === 0 ? <tr><td colSpan={6} className="px-5 py-16 text-center text-ink-faint">No hay líneas que coincidan con la búsqueda.</td></tr> : items.map((l) => <tr key={l.id} className="hover:bg-paper/45">
              <td className="px-5 py-4"><span className="font-mono text-xs font-bold text-pine">{l.codigo}</span></td>
              <td className="px-4 py-4 font-mono text-xs text-ink-soft">{l.numero || '-'}</td>
              <td className="px-4 py-4"><p className="font-bold text-ink">{l.nombre}</p>{l.descripcion && <p className="mt-0.5 max-w-md truncate text-xs text-ink-faint">{l.descripcion}</p>}</td>
              <td className="hidden md:table-cell px-4 py-4 text-ink-soft">{l.plan_desarrollo_nombre || plan?.plan.nombre || '-'}</td>
              <td className="px-4 py-4"><EstadoBadge estado={l.estado} /></td>
              <td className="px-5 py-4 text-right"><div className="inline-flex items-center justify-end gap-0.5" aria-label={`Acciones para ${l.nombre}`}>
                <ActionButton label="Editar" onClick={() => openEdit(l)}><Icon name="edit" /></ActionButton>
                <ActionButton label="Eliminar" danger onClick={() => remove(l)}><Icon name="trash" /></ActionButton>
              </div></td>
            </tr>)}
          </tbody>
        </table>
      </div>
    </section>

    {modal === 'create' && <ModalShell title="Nueva línea estratégica" description={`Se asociará al plan ${plan?.plan.nombre}. El código se generará automáticamente.`} close={() => setModal(null)}>
      <div className="grid gap-4 p-6"><InputField label="Número de la línea" value={form.numero || ''} onChange={(v) => setForm({ ...form, numero: v })} placeholder="Ej: 001" /><InputField label="Nombre" required value={form.nombre} onChange={(v) => setForm({ ...form, nombre: v })} placeholder="Nombre de la línea estratégica" /><div><label className="text-sm font-bold text-ink">Descripción</label><textarea value={form.descripcion || ''} onChange={(e) => setForm({ ...form, descripcion: e.target.value })} rows={3} placeholder="Objetivo del eje estratégico" className={`${selectClass} mt-1 resize-none`} /></div></div>
      <footer className="flex justify-end gap-3 border-t border-line px-6 py-4"><Button variant="ghost" onClick={() => setModal(null)}>Cancelar</Button><Button loading={saving} disabled={!form.nombre} onClick={save}>Crear línea</Button></footer>
    </ModalShell>}

    {modal === 'edit' && selected && <ModalShell title="Editar línea estratégica" description={`Actualice la información de "${selected.nombre}".`} close={() => setModal(null)}>
      <div className="grid gap-4 p-6"><div><label className="text-sm font-bold text-ink">Código</label><p className="mt-1 font-mono text-sm text-ink-faint">{selected.codigo}</p></div><InputField label="Número de la línea" value={form.numero || ''} onChange={(v) => setForm({ ...form, numero: v })} placeholder="Ej: 001" /><InputField label="Nombre" required value={form.nombre} onChange={(v) => setForm({ ...form, nombre: v })} /><div><label className="text-sm font-bold text-ink">Descripción</label><textarea value={form.descripcion || ''} onChange={(e) => setForm({ ...form, descripcion: e.target.value })} rows={3} className={`${selectClass} mt-1 resize-none`} /></div></div>
      <footer className="flex justify-end gap-3 border-t border-line px-6 py-4"><Button variant="ghost" onClick={() => setModal(null)}>Cancelar</Button><Button loading={saving} disabled={!form.nombre} onClick={save}>Guardar cambios</Button></footer>
    </ModalShell>}
  </div>
}

function InputField({ label, required, type = 'text', value, onChange, placeholder }: { label: string; required?: boolean; type?: string; value: string; onChange: (v: string) => void; placeholder?: string }) {
  return <div><label className="text-sm font-bold text-ink">{label}{required && <span className="text-warn"> *</span>}</label><input type={type} value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} className={`${selectClass} mt-1`} /></div>
}