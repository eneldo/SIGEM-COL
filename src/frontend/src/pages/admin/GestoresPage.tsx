import { useDeferredValue, useEffect, useState } from 'react'
import { catalogos, gestores } from '../../lib/api'
import type { CredencialTemporal, Dependencia, Gestor, GestorAcceso, GestorCreatePayload, Rol } from '../../lib/types'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'

type Modal = 'create' | 'edit' | 'details' | 'permissions' | 'audit' | 'credentials' | null

const emptyForm: GestorCreatePayload = {
  nombre_completo: '', email: '', telefono: '', cargo: '', rol_id: '',
  dependencia_principal_id: '', dependencias_adicionales: [],
}

function Icon({ name }: { name: 'plus' | 'refresh' | 'search' | 'edit' | 'shield' | 'key' | 'audit' | 'trash' | 'dots' | 'close' | 'copy' }) {
  const paths = {
    plus: 'M12 4.5v15m7.5-7.5h-15', refresh: 'M16.02 9.35h5V4.36m-.01 4.99-3.18-3.18a8.25 8.25 0 1 0 1.94 8.57',
    search: 'm21 21-4.35-4.35m2.1-5.4a7.5 7.5 0 1 1-15 0 7.5 7.5 0 0 1 15 0Z',
    edit: 'm16.86 4.49 1.69-1.69a1.88 1.88 0 1 1 2.65 2.65L10.58 16.07a4.5 4.5 0 0 1-1.9 1.13L6 18l.8-2.69a4.5 4.5 0 0 1 1.13-1.89l8.93-8.93ZM18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10',
    shield: 'M12 3c2.12 1.43 4.57 2.25 7.13 2.38v5.37c0 4.8-2.91 8.34-7.13 10.25-4.22-1.91-7.13-5.45-7.13-10.25V5.38A14.95 14.95 0 0 0 12 3Zm-2.25 9 1.5 1.5 3.5-4',
    key: 'M15.75 5.25a6 6 0 1 1-6.16 4.03l-7.34 7.34v5.13H7.5V19.5h2.25v-2.25h2.25l1.16-1.16a6 6 0 0 1 2.59-10.84Z',
    audit: 'M9 12.75 11.25 15 15 9.75M12 3.75a8.25 8.25 0 1 0 8.25 8.25A8.25 8.25 0 0 0 12 3.75Z',
    trash: 'm9.75 9 .38 9m3.74 0 .38-9M4.5 6.75h15m-12 0V4.5h9v2.25m1.5 0-.75 14.25H6.75L6 6.75',
    dots: 'M12 6.75h.01M12 12h.01M12 17.25h.01', close: 'm6 6 12 12M18 6 6 18',
    copy: 'M8.25 7.5V5.25A2.25 2.25 0 0 1 10.5 3h8.25A2.25 2.25 0 0 1 21 5.25v8.25a2.25 2.25 0 0 1-2.25 2.25H16.5m-11.25-7.5h8.25a2.25 2.25 0 0 1 2.25 2.25v8.25A2.25 2.25 0 0 1 13.5 21H5.25A2.25 2.25 0 0 1 3 18.75V10.5a2.25 2.25 0 0 1 2.25-2.25Z',
  }
  return <svg aria-hidden="true" className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><path d={paths[name]} /></svg>
}

function formatDate(value?: string) {
  if (!value) return 'Sin registro'
  return new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

function ModalShell({ title, description, close, children, wide = false }: { title: string; description?: string; close: () => void; children: React.ReactNode; wide?: boolean }) {
  return <div className="fixed inset-0 z-50 flex items-center justify-center bg-pine-deep/70 p-4 backdrop-blur-sm" onMouseDown={(e) => e.target === e.currentTarget && close()}>
    <section role="dialog" aria-modal="true" aria-labelledby="modal-title" className={`max-h-[92vh] w-full overflow-hidden rounded-3xl bg-white shadow-2xl ${wide ? 'max-w-3xl' : 'max-w-xl'}`}>
      <header className="flex items-start justify-between border-b border-line px-6 py-5">
        <div><h2 id="modal-title" className="text-2xl font-bold text-ink">{title}</h2>{description && <p className="mt-1 text-sm text-ink-faint">{description}</p>}</div>
        <button onClick={close} aria-label="Cerrar" className="flex h-10 w-10 items-center justify-center rounded-xl text-ink-faint hover:bg-line/50"><Icon name="close" /></button>
      </header>
      <div className="max-h-[calc(92vh-89px)] overflow-y-auto">{children}</div>
    </section>
  </div>
}

export function GestoresPage() {
  const [items, setItems] = useState<Gestor[]>([])
  const [roles, setRoles] = useState<Rol[]>([])
  const [dependencies, setDependencies] = useState<Dependencia[]>([])
  const [accesses, setAccesses] = useState<GestorAcceso[]>([])
  const [selected, setSelected] = useState<Gestor | null>(null)
  const [credentials, setCredentials] = useState<CredencialTemporal | null>(null)
  const [modal, setModal] = useState<Modal>(null)
  const [form, setForm] = useState<GestorCreatePayload>(emptyForm)
  const [search, setSearch] = useState('')
  const deferredSearch = useDeferredValue(search)
  const [status, setStatus] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  async function load() {
    setLoading(true); setError('')
    try {
      const res = await gestores.list({ page: 1, page_size: 100, search: deferredSearch || undefined, estado: status || undefined })
      setItems(res.data.items)
    } catch { setError('No fue posible cargar los gestores.') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [deferredSearch, status])
  useEffect(() => {
    Promise.all([catalogos.roles(), catalogos.dependencias()]).then(([r, d]) => { setRoles(r.data); setDependencies(d.data) }).catch(() => setError('No fue posible cargar los catálogos.'))
  }, [])

  function openCreate() {
    const defaultRole = roles.find((r) => r.codigo === 'GESTOR_LIDER')
    setForm({ ...emptyForm, rol_id: defaultRole?.id || '' }); setSelected(null); setModal('create')
  }

  function openEdit(g: Gestor) {
    setSelected(g); setForm({ nombre_completo: g.nombre_completo, email: g.email, telefono: g.telefono || '', cargo: g.cargo || '', rol_id: g.rol_id || '', dependencia_principal_id: g.dependencia_principal_id || '', dependencias_adicionales: [] }); setModal('edit')
  }

  function openDetails(g: Gestor) {
    setSelected(g); setModal('details')
  }

  function openPermissions(g: Gestor) {
    setSelected(g); setForm({ ...emptyForm, rol_id: g.rol_id || '', dependencia_principal_id: g.dependencia_principal_id || '', dependencias_adicionales: g.dependencias.filter((d) => !d.es_principal).map((d) => d.id) }); setModal('permissions')
  }

  async function save() {
    setSaving(true); setError('')
    try {
      if (modal === 'create') {
        const res = await gestores.create(form); setCredentials(res.data); setModal('credentials')
      } else if (modal === 'edit' && selected) {
        await gestores.update(selected.id, { nombre_completo: form.nombre_completo, email: form.email, telefono: form.telefono, cargo: form.cargo, dependencia_principal_id: form.dependencia_principal_id || undefined }); setModal(null)
      } else if (modal === 'permissions' && selected) {
        await gestores.updatePermissions(selected.id, { rol_id: form.rol_id || undefined, dependencia_principal_id: form.dependencia_principal_id || undefined, dependencias_adicionales: form.dependencias_adicionales }); setModal(null)
      }
      await load()
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: string } } }).response?.data?.detail
      setError(typeof detail === 'string' ? detail : 'No fue posible guardar los cambios.')
    } finally { setSaving(false) }
  }

  async function openAudit(g: Gestor) {
    setSelected(g); setModal('audit'); setAccesses([])
    try { setAccesses((await gestores.accesos(g.id)).data) } catch { setError('No fue posible cargar los accesos.') }
  }

  async function resetPassword(g: Gestor) {
    if (!window.confirm(`¿Generar una nueva contraseña temporal para ${g.nombre_completo}?`)) return
    try { setCredentials((await gestores.resetPassword(g.id)).data); setModal('credentials') } catch { setError('No fue posible restablecer la contraseña.') }
  }

  async function toggleStatus(g: Gestor) {
    try {
      if (g.estado === 'BLOQUEADO') await gestores.unblock(g.id)
      else if (g.estado === 'ACTIVO') await gestores.deactivate(g.id)
      else await gestores.activate(g.id)
      await load()
    } catch { setError('No fue posible cambiar el estado.') }
  }

  async function remove(g: Gestor) {
    if (!window.confirm(`¿Eliminar a ${g.nombre_completo}? Esta acción dejará un registro auditable.`)) return
    try { await gestores.delete(g.id); await load() } catch { setError('No fue posible eliminar el gestor.') }
  }

  const active = items.filter((g) => g.estado === 'ACTIVO').length
  const blocked = items.filter((g) => g.estado === 'BLOQUEADO').length
  const selectClass = 'block min-h-10 w-full rounded-xl border border-line bg-white px-3 py-2 text-sm text-ink focus:border-pine focus:outline-none focus:ring-2 focus:ring-pine/20'

  return <div className="space-y-6 pb-8">
    <section className="flex flex-col gap-5 rounded-[28px] bg-pine px-6 py-7 text-white shadow-[0_18px_40px_rgba(10,43,41,.16)] sm:flex-row sm:items-end sm:justify-between sm:px-8">
      <div><p className="text-xs font-bold uppercase tracking-[.2em] text-ochre-soft">Administración de usuarios</p><h1 className="mt-2 text-3xl font-bold">Gestores líderes</h1><p className="mt-2 max-w-2xl text-sm text-white/70">Cree cuentas, asigne roles y dependencias, gestione credenciales y consulte la trazabilidad de acceso.</p></div>
      <div className="flex gap-2"><Button variant="ghost" onClick={load} className="border border-white/20 text-white hover:bg-white/10"><Icon name="refresh" />Actualizar</Button><Button onClick={openCreate} className="bg-ochre hover:bg-ochre-deep"><Icon name="plus" />Añadir gestor</Button></div>
    </section>

    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {[['Total', items.length, 'text-pine'], ['Activos', active, 'text-forest'], ['Inactivos', items.length - active - blocked, 'text-ink-faint'], ['Bloqueados', blocked, 'text-warn']].map(([label, value, tone]) => <div key={label} className="rounded-2xl border border-line bg-white p-4 shadow-sm"><p className="text-xs font-bold uppercase tracking-wider text-ink-faint">{label}</p><p className={`mt-2 text-3xl font-bold ${tone}`}>{value}</p></div>)}
    </div>

    {error && <div role="alert" className="rounded-xl border border-warn/30 bg-warn-soft px-4 py-3 text-sm text-warn">{error}</div>}

    <section className="overflow-visible rounded-2xl border border-line bg-white shadow-sm">
      <div className="flex flex-col gap-3 border-b border-line p-4 sm:flex-row sm:items-center">
        <div className="relative flex-1"><span className="absolute left-3 top-3 text-ink-faint"><Icon name="search" /></span><input aria-label="Buscar gestores" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Buscar por nombre, usuario, correo o ID..." className={`${selectClass} pl-10`} /></div>
        <select aria-label="Filtrar por estado" className={`${selectClass} sm:w-48`} value={status} onChange={(e) => setStatus(e.target.value)}><option value="">Todos los estados</option><option value="ACTIVO">Activos</option><option value="INACTIVO">Inactivos</option><option value="BLOQUEADO">Bloqueados</option></select>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[1280px] text-left text-sm">
          <thead className="bg-paper/70 text-xs uppercase tracking-wider text-ink-faint"><tr><th className="px-5 py-3">Gestor</th><th className="px-4 py-3">ID / Usuario</th><th className="px-4 py-3">Rol</th><th className="px-4 py-3">Dependencia</th><th className="px-4 py-3">Estado</th><th className="px-4 py-3">Último acceso</th><th className="px-4 py-3 text-center">Fallidos</th><th className="px-5 py-3 text-right">Acciones</th></tr></thead>
          <tbody className="divide-y divide-line">
            {loading ? <tr><td colSpan={8} className="px-5 py-16 text-center text-ink-faint">Cargando gestores...</td></tr> : items.length === 0 ? <tr><td colSpan={8} className="px-5 py-16 text-center text-ink-faint">No hay gestores que coincidan con la búsqueda.</td></tr> : items.map((g) => <tr key={g.id} className="hover:bg-paper/45">
              <td className="px-5 py-4"><p className="font-bold text-ink">{g.nombre_completo}</p><p className="mt-0.5 text-xs text-ink-faint">{g.cargo || 'Sin cargo asignado'}</p></td>
              <td className="px-4 py-4"><p className="font-mono text-xs font-bold text-pine">{g.codigo}</p><p className="mt-1 text-xs text-ink-faint">@{g.username}</p></td>
              <td className="px-4 py-4"><span className="rounded-lg bg-forest-soft px-2.5 py-1 text-xs font-bold text-forest">{g.rol || 'Sin rol'}</span></td>
              <td className="max-w-[190px] px-4 py-4 text-ink-soft">{g.dependencia_principal || 'Sin asignar'}</td>
              <td className="px-4 py-4"><span className={`inline-flex items-center gap-2 rounded-full px-2.5 py-1 text-xs font-bold ${g.estado === 'ACTIVO' ? 'bg-forest-soft text-forest' : g.estado === 'BLOQUEADO' ? 'bg-warn-soft text-warn' : 'bg-line/60 text-ink-soft'}`}><span className="h-1.5 w-1.5 rounded-full bg-current" />{g.estado}</span></td>
              <td className="px-4 py-4"><p className="text-xs text-ink-soft">{formatDate(g.ultimo_acceso)}</p><p className="mt-1 font-mono text-[11px] text-ink-faint">{g.ip_ultimo_acceso || 'IP no registrada'}</p></td>
              <td className="px-4 py-4 text-center font-bold text-ink">{g.intentos_fallidos}</td>
              <td className="px-5 py-4 text-right"><div className="inline-flex items-center justify-end gap-0.5" aria-label={`Acciones para ${g.nombre_completo}`}>
                <ActionButton label="Editar" onClick={() => openEdit(g)}><Icon name="edit" /></ActionButton>
                <ActionButton label="Eliminar" danger onClick={() => remove(g)}><Icon name="trash" /></ActionButton>
                <ActionButton label="Ver detalles" onClick={() => openDetails(g)}><Icon name="audit" /></ActionButton>
                <ActionButton label={g.estado === 'ACTIVO' ? 'Desactivar' : g.estado === 'BLOQUEADO' ? 'Desbloquear' : 'Activar'} onClick={() => toggleStatus(g)}><Icon name="refresh" /></ActionButton>
                <ActionButton label="Permisos" onClick={() => openPermissions(g)}><Icon name="shield" /></ActionButton>
                <ActionButton label="Cambiar contraseña" onClick={() => resetPassword(g)}><Icon name="key" /></ActionButton>
              </div></td>
            </tr>)}
          </tbody>
        </table>
      </div>
    </section>

    {(modal === 'create' || modal === 'edit') && <ModalShell title={modal === 'create' ? 'Añadir gestor líder' : 'Editar gestor'} description={modal === 'create' ? 'El ID, usuario y contraseña serán generados automáticamente.' : `Actualice la información de ${selected?.nombre_completo}.`} close={() => setModal(null)}>
      <div className="grid gap-4 p-6 sm:grid-cols-2"><div className="sm:col-span-2"><Input label="Nombre completo" required value={form.nombre_completo} onChange={(e) => setForm({ ...form, nombre_completo: e.target.value })} /></div><Input label="Cargo" value={form.cargo} onChange={(e) => setForm({ ...form, cargo: e.target.value })} /><Input label="Teléfono" value={form.telefono} onChange={(e) => setForm({ ...form, telefono: e.target.value })} /><div className="sm:col-span-2"><Input label="Correo electrónico" type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></div>{modal === 'create' && <><label className="text-sm font-bold text-ink">Rol<select className={`${selectClass} mt-1`} value={form.rol_id} onChange={(e) => setForm({ ...form, rol_id: e.target.value })}>{roles.map((r) => <option key={r.id} value={r.id}>{r.nombre.replace(/_/g, ' ')}</option>)}</select></label><label className="text-sm font-bold text-ink">Dependencia principal<select className={`${selectClass} mt-1`} value={form.dependencia_principal_id} onChange={(e) => setForm({ ...form, dependencia_principal_id: e.target.value })}><option value="">Sin asignar</option>{dependencies.map((d) => <option key={d.id} value={d.id}>{d.nombre}</option>)}</select></label></>}</div>
      <footer className="flex justify-end gap-3 border-t border-line px-6 py-4"><Button variant="ghost" onClick={() => setModal(null)}>Cancelar</Button><Button loading={saving} disabled={!form.nombre_completo || !form.email} onClick={save}>{modal === 'create' ? 'Crear gestor' : 'Guardar cambios'}</Button></footer>
    </ModalShell>}

    {modal === 'permissions' && selected && <ModalShell title="Roles y permisos" description={`Configure el alcance de ${selected.nombre_completo}.`} close={() => setModal(null)}>
      <div className="space-y-5 p-6"><label className="block text-sm font-bold text-ink">Rol asignado<select className={`${selectClass} mt-1`} value={form.rol_id} onChange={(e) => setForm({ ...form, rol_id: e.target.value })}>{roles.map((r) => <option key={r.id} value={r.id}>{r.nombre.replace(/_/g, ' ')}</option>)}</select></label><label className="block text-sm font-bold text-ink">Dependencia principal<select className={`${selectClass} mt-1`} value={form.dependencia_principal_id} onChange={(e) => setForm({ ...form, dependencia_principal_id: e.target.value })}><option value="">Sin asignar</option>{dependencies.map((d) => <option key={d.id} value={d.id}>{d.nombre}</option>)}</select></label><fieldset><legend className="text-sm font-bold text-ink">Dependencias adicionales</legend><div className="mt-2 grid gap-2 sm:grid-cols-2">{dependencies.filter((d) => d.id !== form.dependencia_principal_id).map((d) => <label key={d.id} className="flex min-h-11 items-center gap-3 rounded-xl border border-line px-3 text-sm"><input type="checkbox" checked={form.dependencias_adicionales.includes(d.id)} onChange={(e) => setForm({ ...form, dependencias_adicionales: e.target.checked ? [...form.dependencias_adicionales, d.id] : form.dependencias_adicionales.filter((id) => id !== d.id) })} />{d.nombre}</label>)}</div></fieldset></div><footer className="flex justify-end gap-3 border-t border-line px-6 py-4"><Button variant="ghost" onClick={() => setModal(null)}>Cancelar</Button><Button loading={saving} onClick={save}>Guardar permisos</Button></footer>
    </ModalShell>}

    {modal === 'details' && selected && <ModalShell title="Detalle del gestor" description={`${selected.codigo} · @${selected.username}`} close={() => setModal(null)} wide>
      <div className="grid gap-3 p-6 sm:grid-cols-2 lg:grid-cols-3">
        <Detail label="Nombre completo" value={selected.nombre_completo} />
        <Detail label="Cargo" value={selected.cargo || 'Sin asignar'} />
        <Detail label="Estado" value={selected.estado} />
        <Detail label="Correo" value={selected.email} />
        <Detail label="Teléfono" value={selected.telefono || 'Sin registro'} />
        <Detail label="Rol" value={selected.rol || 'Sin asignar'} />
        <Detail label="Dependencia principal" value={selected.dependencia_principal || 'Sin asignar'} />
        <Detail label="Último acceso" value={formatDate(selected.ultimo_acceso)} />
        <Detail label="Creado" value={formatDate(selected.created_at)} />
      </div>
      <footer className="flex flex-wrap justify-end gap-3 border-t border-line px-6 py-4"><Button variant="ghost" onClick={() => setModal(null)}>Cerrar</Button><Button onClick={() => openAudit(selected)}><Icon name="audit" />Ver auditoría</Button></footer>
    </ModalShell>}

    {modal === 'credentials' && credentials && <ModalShell title="Credenciales temporales" description="Guarde esta información ahora. La contraseña no volverá a mostrarse." close={() => { setModal(null); setCredentials(null) }}>
      <div className="space-y-3 p-6">{credentials.codigo && <Credential label="ID del gestor" value={credentials.codigo} />}{credentials.username && <Credential label="Usuario" value={credentials.username} />}<Credential label="Contraseña temporal" value={credentials.nueva_password_temporal} /><div className="rounded-xl bg-ochre-soft p-4 text-sm text-ochre-deep">El gestor deberá cambiar esta contraseña en su primer ingreso.</div></div><footer className="flex justify-end border-t border-line px-6 py-4"><Button onClick={() => { setModal(null); setCredentials(null) }}>Entendido</Button></footer>
    </ModalShell>}

    {modal === 'audit' && selected && <ModalShell wide title="Auditoría de acceso" description={`${selected.codigo} · ${selected.nombre_completo}`} close={() => setModal(null)}>
      <div className="grid gap-3 border-b border-line p-6 sm:grid-cols-3"><AuditStat label="Último acceso" value={formatDate(selected.ultimo_acceso)} /><AuditStat label="IP del último acceso" value={selected.ip_ultimo_acceso || 'Sin registro'} /><AuditStat label="Intentos fallidos actuales" value={String(selected.intentos_fallidos)} /></div><div className="p-6"><h3 className="text-lg font-bold text-ink">Historial reciente</h3><div className="mt-3 overflow-hidden rounded-xl border border-line"><table className="w-full text-sm"><thead className="bg-paper text-xs uppercase text-ink-faint"><tr><th className="px-4 py-3 text-left">Resultado</th><th className="px-4 py-3 text-left">Fecha y hora</th><th className="px-4 py-3 text-left">IP</th><th className="px-4 py-3 text-left">Detalle</th></tr></thead><tbody className="divide-y divide-line">{accesses.length ? accesses.map((a) => <tr key={a.id}><td className="px-4 py-3"><span className={a.exitoso ? 'font-bold text-forest' : 'font-bold text-warn'}>{a.exitoso ? 'Exitoso' : 'Fallido'}</span></td><td className="px-4 py-3">{formatDate(a.fecha_intento)}</td><td className="px-4 py-3 font-mono text-xs">{a.ip_address || '-'}</td><td className="px-4 py-3 text-ink-faint">{a.razon_fallo || 'Acceso autorizado'}</td></tr>) : <tr><td colSpan={4} className="px-4 py-10 text-center text-ink-faint">Sin accesos registrados</td></tr>}</tbody></table></div></div>
    </ModalShell>}
  </div>
}

function Credential({ label, value }: { label: string; value: string }) {
  return <div className="rounded-xl border border-line bg-paper/60 p-4"><p className="text-xs font-bold uppercase tracking-wider text-ink-faint">{label}</p><div className="mt-1 flex items-center justify-between gap-3"><code className="break-all text-base font-bold text-pine">{value}</code><button aria-label={`Copiar ${label}`} onClick={() => navigator.clipboard.writeText(value)} className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-pine hover:bg-forest-soft"><Icon name="copy" /></button></div></div>
}

function AuditStat({ label, value }: { label: string; value: string }) {
  return <div className="rounded-xl bg-paper p-4"><p className="text-xs font-bold uppercase tracking-wider text-ink-faint">{label}</p><p className="mt-2 font-bold text-ink">{value}</p></div>
}

function Detail({ label, value }: { label: string; value: string }) {
  return <div className="rounded-xl border border-line bg-paper/60 p-4"><p className="text-xs font-bold uppercase tracking-wider text-ink-faint">{label}</p><p className="mt-2 break-words font-bold text-ink">{value}</p></div>
}

function ActionButton({ label, onClick, danger = false, children }: { label: string; onClick: () => void; danger?: boolean; children: React.ReactNode }) {
  return <button type="button" title={label} aria-label={label} onClick={onClick} className={`inline-flex h-9 w-9 items-center justify-center rounded-lg border transition-colors ${danger ? 'border-warn/20 text-warn hover:bg-warn-soft' : 'border-line text-pine hover:border-pine/30 hover:bg-forest-soft'}`}><span className="sr-only">{label}</span>{children}</button>
}
