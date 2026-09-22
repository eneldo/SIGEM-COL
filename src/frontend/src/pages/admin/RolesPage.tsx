import { useCallback, useEffect, useState } from 'react'
import { configRoles } from '../../lib/api'
import type { ConfigRol, ConfigPermiso, ConfigRolCreatePayload } from '../../lib/types'
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

export function RolesPage() {
  const [items, setItems] = useState<ConfigRol[]>([])
  const [permisos, setPermisos] = useState<ConfigPermiso[]>([])
  const [permisosSeleccionados, setPermisosSeleccionados] = useState<string[]>([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [modal, setModal] = useState<'create' | 'edit' | null>(null)
  const [selected, setSelected] = useState<ConfigRol | null>(null)
  const [form, setForm] = useState<ConfigRolCreatePayload>({ codigo: '', nombre: '', descripcion: '', nivel: 1, permisos_ids: [] })

  const loadPermisos = useCallback(async () => {
    try {
      const resp = await configRoles.permisos()
      setPermisos(resp.data.items)
    } catch { /* silent */ }
  }, [])

  useEffect(() => { loadPermisos() }, [loadPermisos])

  async function load() {
    setLoading(true); setError('')
    try {
      const params: Record<string, unknown> = { page: 1, page_size: 100 }
      if (search) params.search = search
      setItems((await configRoles.list(params)).data.items)
    } catch { setError('No fue posible cargar los roles.') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [search])

  function openCreate() {
    setSelected(null)
    setForm({ codigo: '', nombre: '', descripcion: '', nivel: 1, permisos_ids: [] })
    setPermisosSeleccionados([])
    setModal('create')
  }

  function openEdit(r: ConfigRol) {
    setSelected(r)
    setForm({ codigo: r.codigo, nombre: r.nombre, descripcion: r.descripcion || '', nivel: r.nivel, permisos_ids: r.permisos.map((p) => p.id) })
    setPermisosSeleccionados(r.permisos.map((p) => p.id))
    setModal('edit')
  }

  function togglePermiso(permisoId: string) {
    setPermisosSeleccionados((prev) => {
      const next = prev.includes(permisoId) ? prev.filter((id) => id !== permisoId) : [...prev, permisoId]
      setForm((f) => ({ ...f, permisos_ids: next }))
      return next
    })
  }

  function toggleAllPermisos(modulo: string) {
    const moduloPermisos = permisos.filter((p) => p.modulo === modulo).map((p) => p.id)
    const allSelected = moduloPermisos.every((id) => permisosSeleccionados.includes(id))
    setPermisosSeleccionados((prev) => {
      const next = allSelected ? prev.filter((id) => !moduloPermisos.includes(id)) : [...new Set([...prev, ...moduloPermisos])]
      setForm((f) => ({ ...f, permisos_ids: next }))
      return next
    })
  }

  async function save() {
    setSaving(true); setError('')
    try {
      if (selected) {
        await configRoles.update(selected.id, { nombre: form.nombre, descripcion: form.descripcion, nivel: form.nivel, permisos_ids: form.permisos_ids })
      } else {
        await configRoles.create(form)
      }
      setModal(null)
      await load()
    } catch (e) { setError(getErrorDetail(e)) }
    finally { setSaving(false) }
  }

  async function remove(r: ConfigRol) {
    if (!window.confirm(`¿Eliminar el rol "${r.nombre}"? Esta acción quedará registrada en la auditoría.`)) return
    try { await configRoles.delete(r.id); await load() } catch { setError('No fue posible eliminar el rol.') }
  }

  const modulos = [...new Set(permisos.map((p) => p.modulo))].sort()

  return <div className="space-y-6 pb-8">
    <section className="flex flex-col gap-5 rounded-[28px] bg-pine px-6 py-7 text-white shadow-[0_18px_40px_rgba(10,43,41,.16)] sm:flex-row sm:items-end sm:justify-between sm:px-8">
      <div><p className="text-xs font-bold uppercase tracking-[.2em] text-ochre-soft">Configuración</p><h1 className="mt-2 text-3xl font-bold">Roles y permisos</h1><p className="mt-2 max-w-2xl text-sm text-white/70">Defina los roles del sistema y asigne permisos de acceso por módulo y acción.</p></div>
      <div className="flex gap-2"><Button variant="ghost" onClick={load} className="border border-white/20 text-white hover:bg-white/10"><Icon name="refresh" />Actualizar</Button><Button onClick={openCreate} className="bg-ochre hover:bg-ochre-deep"><Icon name="plus" />Nuevo rol</Button></div>
    </section>

    <div className="grid grid-cols-2 gap-3 lg:grid-cols-3">
      {[['Total de roles', items.length, 'text-pine'], ['Activos', items.filter((r) => r.estado === 'ACTIVO').length, 'text-forest'], ['Permisos disponibles', permisos.length, 'text-ochre-deep']].map(([label, value, tone]) => <div key={label} className="rounded-2xl border border-line bg-white p-4 shadow-sm"><p className="text-xs font-bold uppercase tracking-wider text-ink-faint">{label}</p><p className={`mt-2 text-3xl font-bold ${tone}`}>{value}</p></div>)}
    </div>

    {error && <div role="alert" className="rounded-xl border border-warn/30 bg-warn-soft px-4 py-3 text-sm text-warn">{error}</div>}

    <section className="overflow-visible rounded-2xl border border-line bg-white shadow-sm">
      <div className="flex flex-col gap-3 border-b border-line p-4 lg:flex-row lg:items-center">
        <div className="relative flex-1"><span className="absolute left-3 top-3 text-ink-faint"><Icon name="search" /></span><input aria-label="Buscar roles" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Buscar por código o nombre..." className={`${selectClass} pl-10`} /></div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[800px] text-left text-sm">
          <thead className="bg-paper/70 text-xs uppercase tracking-wider text-ink-faint"><tr><th className="px-5 py-3">Código</th><th className="px-4 py-3">Nombre</th><th className="hidden lg:table-cell px-4 py-3">Descripción</th><th className="px-4 py-3">Nivel</th><th className="px-4 py-3">Permisos</th><th className="px-4 py-3">Estado</th><th className="px-5 py-3 text-right">Acciones</th></tr></thead>
          <tbody className="divide-y divide-line">
            {loading ? <tr><td colSpan={7} className="px-5 py-16 text-center text-ink-faint">Cargando roles...</td></tr> : items.length === 0 ? <tr><td colSpan={7} className="px-5 py-16 text-center text-ink-faint">No hay roles que coincidan con la búsqueda.</td></tr> : items.map((r) => <tr key={r.id} className="hover:bg-paper/45">
              <td className="px-5 py-4"><span className="font-mono text-xs font-bold text-pine">{r.codigo}</span></td>
              <td className="px-4 py-4"><p className="font-bold text-ink">{r.nombre}</p></td>
              <td className="hidden lg:table-cell max-w-[200px] px-4 py-4 text-ink-soft truncate">{r.descripcion || '-'}</td>
              <td className="px-4 py-4"><span className="rounded-lg bg-forest-soft px-2.5 py-1 text-xs font-bold text-forest">{r.nivel}</span></td>
              <td className="px-4 py-4 text-xs text-ink-soft">{r.permisos.length} permisos</td>
              <td className="px-4 py-4"><EstadoBadge estado={r.estado} /></td>
              <td className="px-5 py-4 text-right"><div className="inline-flex items-center justify-end gap-0.5" aria-label={`Acciones para ${r.nombre}`}>
                <ActionButton label="Editar" onClick={() => openEdit(r)}><Icon name="edit" /></ActionButton>
                <ActionButton label="Eliminar" danger onClick={() => remove(r)}><Icon name="trash" /></ActionButton>
              </div></td>
            </tr>)}
          </tbody>
        </table>
      </div>
    </section>

    {(modal === 'create' || modal === 'edit') && <ModalShell title={modal === 'create' ? 'Nuevo rol' : 'Editar rol'} description={modal === 'create' ? 'Defina el código, nombre y permisos del rol.' : `Actualice el rol "${selected?.nombre}".`} close={() => setModal(null)} wide>
      <div className="grid gap-4 p-6 sm:grid-cols-2">
        <div><label className="text-sm font-bold text-ink">Código <span className="text-warn">*</span></label><input value={form.codigo} onChange={(e) => setForm({ ...form, codigo: e.target.value })} placeholder="Ej: ADMIN_MUNICIPAL" className={`${selectClass} mt-1`} disabled={modal === 'edit'} /></div>
        <div><label className="text-sm font-bold text-ink">Nombre <span className="text-warn">*</span></label><input value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} className={`${selectClass} mt-1`} /></div>
        <div className="sm:col-span-2"><label className="text-sm font-bold text-ink">Descripción</label><input value={form.descripcion || ''} onChange={(e) => setForm({ ...form, descripcion: e.target.value })} className={`${selectClass} mt-1`} /></div>
        <div><label className="text-sm font-bold text-ink">Nivel de acceso</label><input type="number" value={form.nivel || 1} onChange={(e) => setForm({ ...form, nivel: parseInt(e.target.value) || 1 })} className={`${selectClass} mt-1`} /></div>
        <div className="sm:col-span-2">
          <label className="text-sm font-bold text-ink">Permisos</label>
          <div className="mt-2 max-h-64 overflow-y-auto rounded-xl border border-line p-3">
            {modulos.map((mod) => {
              const moduloPermisos = permisos.filter((p) => p.modulo === mod)
              const allSelected = moduloPermisos.every((p) => permisosSeleccionados.includes(p.id))
              return <div key={mod} className="mb-3">
                <label className="flex items-center gap-2 cursor-pointer rounded-lg px-2 py-1 hover:bg-paper/60">
                  <input type="checkbox" checked={allSelected} onChange={() => toggleAllPermisos(mod)} className="h-4 w-4 rounded border-line text-pine focus:ring-pine" />
                  <span className="text-xs font-bold uppercase tracking-wider text-ink-faint">{mod}</span>
                </label>
                <div className="ml-6 mt-1 flex flex-wrap gap-1">
                  {moduloPermisos.map((p) => <label key={p.id} className={`inline-flex items-center gap-1.5 cursor-pointer rounded-lg px-2.5 py-1 text-xs transition-colors ${permisosSeleccionados.includes(p.id) ? 'bg-pine text-white' : 'bg-paper/60 text-ink-soft hover:bg-paper'}`}>
                    <input type="checkbox" checked={permisosSeleccionados.includes(p.id)} onChange={() => togglePermiso(p.id)} className="sr-only" />
                    {p.accion}
                  </label>)}
                </div>
              </div>
            })}
          </div>
        </div>
      </div>
      <footer className="flex justify-end gap-3 border-t border-line px-6 py-4"><Button variant="ghost" onClick={() => setModal(null)}>Cancelar</Button><Button loading={saving} disabled={!form.codigo || !form.nombre} onClick={save}>{modal === 'create' ? 'Crear rol' : 'Guardar cambios'}</Button></footer>
    </ModalShell>}
  </div>
}
