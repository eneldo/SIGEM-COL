import { useCallback, useEffect, useState } from 'react'
import { configUsuarios, catalogos } from '../../lib/api'
import type { ConfigUsuario, ConfigUsuarioCreatePayload } from '../../lib/types'
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

export function UsuariosPage() {
  const [items, setItems] = useState<ConfigUsuario[]>([])
  const [rolesList, setRolesList] = useState<{ id: string; codigo: string; nombre: string }[]>([])
  const [search, setSearch] = useState('')
  const [filtroEstado, setFiltroEstado] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [modal, setModal] = useState<'create' | 'edit' | null>(null)
  const [selected, setSelected] = useState<ConfigUsuario | null>(null)
  const [form, setForm] = useState<ConfigUsuarioCreatePayload>({ codigo: '', username: '', email: '', nombre_completo: '', telefono: '', cargo: '', password: '', rol_id: '', dependencia_id: '' })

  const loadCatalogos = useCallback(async () => {
    try {
      const rolesResp = await catalogos.roles()
      setRolesList(rolesResp.data as unknown as { id: string; codigo: string; nombre: string }[])
    } catch { /* silent */ }
  }, [])

  useEffect(() => { loadCatalogos() }, [loadCatalogos])

  async function load() {
    setLoading(true); setError('')
    try {
      const params: Record<string, unknown> = { page: 1, page_size: 100 }
      if (search) params.search = search
      if (filtroEstado) params.estado = filtroEstado
      setItems((await configUsuarios.list(params)).data.items)
    } catch { setError('No fue posible cargar los usuarios.') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [search, filtroEstado])

  function openCreate() {
    setSelected(null)
    setForm({ codigo: '', username: '', email: '', nombre_completo: '', telefono: '', cargo: '', password: '', rol_id: '', dependencia_id: '' })
    setModal('create')
  }

  function openEdit(u: ConfigUsuario) {
    setSelected(u)
    setForm({ codigo: u.codigo, username: u.username, email: u.email, nombre_completo: u.nombre_completo, telefono: u.telefono || '', cargo: u.cargo || '', password: '', rol_id: u.roles[0]?.id || '', dependencia_id: '' })
    setModal('edit')
  }

  async function save() {
    setSaving(true); setError('')
    try {
      if (selected) {
        const updateData: Record<string, unknown> = {}
        if (form.email) updateData.email = form.email
        if (form.nombre_completo) updateData.nombre_completo = form.nombre_completo
        if (form.telefono !== undefined) updateData.telefono = form.telefono
        if (form.cargo !== undefined) updateData.cargo = form.cargo
        if (form.rol_id) updateData.rol_id = form.rol_id
        await configUsuarios.update(selected.id, updateData)
      } else {
        await configUsuarios.create(form)
      }
      setModal(null)
      await load()
    } catch (e) { setError(getErrorDetail(e)) }
    finally { setSaving(false) }
  }

  async function remove(u: ConfigUsuario) {
    if (!window.confirm(`¿Eliminar el usuario "${u.nombre_completo}"? Esta acción quedará registrada en la auditoría.`)) return
    try { await configUsuarios.delete(u.id); await load() } catch { setError('No fue posible eliminar el usuario.') }
  }

  const activos = items.filter((u) => u.activo === 1).length

  return <div className="space-y-6 pb-8">
    <section className="flex flex-col gap-5 rounded-[28px] bg-pine px-6 py-7 text-white shadow-[0_18px_40px_rgba(10,43,41,.16)] sm:flex-row sm:items-end sm:justify-between sm:px-8">
      <div><p className="text-xs font-bold uppercase tracking-[.2em] text-ochre-soft">Configuración</p><h1 className="mt-2 text-3xl font-bold">Usuarios del sistema</h1><p className="mt-2 max-w-2xl text-sm text-white/70">Administre las cuentas de acceso al sistema, asigne roles y gestione credenciales.</p></div>
      <div className="flex gap-2"><Button variant="ghost" onClick={load} className="border border-white/20 text-white hover:bg-white/10"><Icon name="refresh" />Actualizar</Button><Button onClick={openCreate} className="bg-ochre hover:bg-ochre-deep"><Icon name="plus" />Nuevo usuario</Button></div>
    </section>

    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {[['Total de usuarios', items.length, 'text-pine'], ['Activos', activos, 'text-forest'], ['Inactivos', items.length - activos, 'text-ink-faint'], ['Con MFA', items.filter((u) => u.mfa_activo).length, 'text-ochre-deep']].map(([label, value, tone]) => <div key={label} className="rounded-2xl border border-line bg-white p-4 shadow-sm"><p className="text-xs font-bold uppercase tracking-wider text-ink-faint">{label}</p><p className={`mt-2 text-3xl font-bold ${tone}`}>{value}</p></div>)}
    </div>

    {error && <div role="alert" className="rounded-xl border border-warn/30 bg-warn-soft px-4 py-3 text-sm text-warn">{error}</div>}

    <section className="overflow-visible rounded-2xl border border-line bg-white shadow-sm">
      <div className="flex flex-col gap-3 border-b border-line p-4 lg:flex-row lg:items-center">
        <div className="relative flex-1"><span className="absolute left-3 top-3 text-ink-faint"><Icon name="search" /></span><input aria-label="Buscar usuarios" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Buscar por nombre, usuario o correo..." className={`${selectClass} pl-10`} /></div>
        <select aria-label="Filtrar por estado" className={`${selectClass} lg:w-40`} value={filtroEstado} onChange={(e) => setFiltroEstado(e.target.value)}><option value="">Todos los estados</option><option value="ACTIVO">Activos</option><option value="INACTIVO">Inactivos</option></select>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[900px] text-left text-sm">
          <thead className="bg-paper/70 text-xs uppercase tracking-wider text-ink-faint"><tr><th className="px-5 py-3">Código</th><th className="px-4 py-3">Nombre</th><th className="px-4 py-3">Usuario</th><th className="hidden lg:table-cell px-4 py-3">Email</th><th className="px-4 py-3">Rol</th><th className="px-4 py-3">Estado</th><th className="px-4 py-3">Último acceso</th><th className="px-5 py-3 text-right">Acciones</th></tr></thead>
          <tbody className="divide-y divide-line">
            {loading ? <tr><td colSpan={8} className="px-5 py-16 text-center text-ink-faint">Cargando usuarios...</td></tr> : items.length === 0 ? <tr><td colSpan={8} className="px-5 py-16 text-center text-ink-faint">No hay usuarios que coincidan con la búsqueda.</td></tr> : items.map((u) => <tr key={u.id} className="hover:bg-paper/45">
              <td className="px-5 py-4"><span className="font-mono text-xs font-bold text-pine">{u.codigo}</span></td>
              <td className="px-4 py-4"><p className="font-bold text-ink">{u.nombre_completo}</p>{u.cargo && <p className="mt-0.5 text-xs text-ink-faint">{u.cargo}</p>}</td>
              <td className="px-4 py-4"><span className="rounded-lg bg-forest-soft px-2.5 py-1 text-xs font-bold text-forest">@{u.username}</span></td>
              <td className="hidden lg:table-cell max-w-[200px] px-4 py-4 text-ink-soft truncate">{u.email}</td>
              <td className="px-4 py-4 text-xs text-ink-soft">{u.roles[0]?.nombre || '-'}</td>
              <td className="px-4 py-4"><EstadoBadge estado={u.activo === 1 ? 'ACTIVO' : 'INACTIVO'} /></td>
              <td className="px-4 py-4 text-xs text-ink-faint">{u.ultimo_acceso ? new Date(u.ultimo_acceso).toLocaleDateString('es-CO') : 'Nunca'}</td>
              <td className="px-5 py-4 text-right"><div className="inline-flex items-center justify-end gap-0.5" aria-label={`Acciones para ${u.nombre_completo}`}>
                <ActionButton label="Editar" onClick={() => openEdit(u)}><Icon name="edit" /></ActionButton>
                <ActionButton label="Eliminar" danger onClick={() => remove(u)}><Icon name="trash" /></ActionButton>
              </div></td>
            </tr>)}
          </tbody>
        </table>
      </div>
    </section>

    {(modal === 'create' || modal === 'edit') && <ModalShell title={modal === 'create' ? 'Nuevo usuario' : 'Editar usuario'} description={modal === 'create' ? 'Cree una cuenta de acceso al sistema.' : `Actualice la información de "${selected?.nombre_completo}".`} close={() => setModal(null)} wide>
      <div className="grid gap-4 p-6 sm:grid-cols-2">
        <div><label className="text-sm font-bold text-ink">Código <span className="text-warn">*</span></label><input value={form.codigo} onChange={(e) => setForm({ ...form, codigo: e.target.value })} placeholder="Ej: USR-001" className={`${selectClass} mt-1`} disabled={modal === 'edit'} /></div>
        <div><label className="text-sm font-bold text-ink">Username <span className="text-warn">*</span></label><input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} placeholder="Ej: jperez" className={`${selectClass} mt-1`} disabled={modal === 'edit'} /></div>
        <div className="sm:col-span-2"><label className="text-sm font-bold text-ink">Nombre completo <span className="text-warn">*</span></label><input value={form.nombre_completo} onChange={(e) => setForm({ ...form, nombre_completo: e.target.value })} className={`${selectClass} mt-1`} /></div>
        <div><label className="text-sm font-bold text-ink">Email <span className="text-warn">*</span></label><input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className={`${selectClass} mt-1`} /></div>
        <div><label className="text-sm font-bold text-ink">Teléfono</label><input value={form.telefono || ''} onChange={(e) => setForm({ ...form, telefono: e.target.value })} className={`${selectClass} mt-1`} /></div>
        <div><label className="text-sm font-bold text-ink">Cargo</label><input value={form.cargo || ''} onChange={(e) => setForm({ ...form, cargo: e.target.value })} className={`${selectClass} mt-1`} /></div>
        {modal === 'create' && <div><label className="text-sm font-bold text-ink">Contraseña <span className="text-warn">*</span></label><input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className={`${selectClass} mt-1`} /></div>}
        <div><label className="text-sm font-bold text-ink">Rol</label><select value={form.rol_id || ''} onChange={(e) => setForm({ ...form, rol_id: e.target.value })} className={`${selectClass} mt-1`}><option value="">Sin rol</option>{rolesList.map((r) => <option key={r.id} value={r.id}>{r.nombre}</option>)}</select></div>
      </div>
      <footer className="flex justify-end gap-3 border-t border-line px-6 py-4"><Button variant="ghost" onClick={() => setModal(null)}>Cancelar</Button><Button loading={saving} disabled={!form.codigo || !form.username || !form.email || !form.nombre_completo || (modal === 'create' && !form.password)} onClick={save}>{modal === 'create' ? 'Crear usuario' : 'Guardar cambios'}</Button></footer>
    </ModalShell>}
  </div>
}
