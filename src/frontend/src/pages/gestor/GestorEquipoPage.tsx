import { useEffect, useState, useCallback } from 'react'
import { gestores, catalogos, productos } from '../../lib/api'
import { useAuthStore } from '../../stores/authStore'
import type { Gestor, Dependencia, Rol, GestorCreatePayload, CredencialTemporal, Producto } from '../../lib/types'
import { Icon, formatDate, ModalShell } from '../../components/ui/icons'
import { clsx } from 'clsx'

type Tab = 'lista' | 'crear'
const PASSWORD_MIN = 15
const ADMIN_ROLES = ['SUPERADMIN_PLATAFORMA', 'ADMINISTRADOR_MUNICIPAL']
const COORDINATOR_CREATE_ROLES = ['GESTOR']

export default function GestorEquipoPage() {
  const [tab, setTab] = useState<Tab>('lista')
  const [items, setItems] = useState<Gestor[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [estadoFilter, setEstadoFilter] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [detailGestor, setDetailGestor] = useState<Gestor | null>(null)
  const [deleteGestor, setDeleteGestor] = useState<Gestor | null>(null)
  const [deleteLoading, setDeleteLoading] = useState(false)
  const [credencial, setCredencial] = useState<CredencialTemporal | null>(null)
  const [passwordGestor, setPasswordGestor] = useState<Gestor | null>(null)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params: Record<string, unknown> = { page, page_size: 10 }
      if (search) params.search = search
      if (estadoFilter) params.estado = estadoFilter
      const res = await gestores.list(params)
      setItems(res.data.items)
      setTotal(res.data.total)
      setError('')
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(typeof msg === 'string' ? msg : 'No fue posible cargar el equipo.')
    } finally {
      setLoading(false)
    }
  }, [page, search, estadoFilter])

  useEffect(() => { load() }, [load])

  const handleCreate = async (data: GestorCreatePayload) => {
    const res = await gestores.create(data)
    setCredencial(res.data)
    setTab('lista')
    load()
  }

  const handleDelete = async () => {
    if (!deleteGestor) return
    setDeleteLoading(true)
    setError('')
    try {
      await gestores.delete(deleteGestor.id)
      setDeleteGestor(null)
      load()
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(typeof msg === 'string' ? msg : 'No fue posible eliminar el gestor.')
      setDeleteGestor(null)
    } finally {
      setDeleteLoading(false)
    }
  }

  const handleToggleEstado = async (g: Gestor) => {
    try {
      if (g.estado === 'ACTIVO') {
        await gestores.deactivate(g.id)
      } else {
        await gestores.activate(g.id)
      }
      load()
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(typeof msg === 'string' ? msg : 'No fue posible cambiar el estado.')
    }
  }

  const estadoTone: Record<string, string> = {
    ACTIVO: 'bg-forest-soft text-forest',
    INACTIVO: 'bg-line/60 text-ink-soft',
    BLOQUEADO: 'bg-warn-soft text-warn',
  }

  const totalPages = Math.ceil(total / 10)

  return (
    <div className="space-y-6 pb-8">
      <section className="relative overflow-hidden rounded-[28px] bg-pine px-6 py-7 text-white shadow-lg sm:px-8 sm:py-9">
        <div className="absolute -right-20 -top-24 h-72 w-72 rounded-full border border-white/10" aria-hidden="true" />
        <div className="relative">
          <p className="mb-2 text-xs font-bold uppercase tracking-[0.2em] text-ochre-soft">Gestor Líder / Coordinador</p>
          <h1 className="text-3xl font-bold leading-tight sm:text-4xl">Mi Equipo de Gestores</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-white/70">
            Cree gestores con usuario y contraseña, actívelos o inactívelos, cambie contraseñas y asigne responsables.
          </p>
        </div>
      </section>

      <div className="flex gap-2 border-b border-line pb-0">
        <button
          onClick={() => setTab('lista')}
          className={clsx('rounded-t-xl px-5 py-3 text-sm font-bold transition-colors', tab === 'lista' ? 'bg-white text-pine shadow-sm' : 'text-ink-faint hover:text-ink')}
        >
          <Icon name="people" className="mr-2 inline h-4 w-4" />
          Mi Equipo ({total})
        </button>
        <button
          onClick={() => setTab('crear')}
          className={clsx('rounded-t-xl px-5 py-3 text-sm font-bold transition-colors', tab === 'crear' ? 'bg-white text-pine shadow-sm' : 'text-ink-faint hover:text-ink')}
        >
          <Icon name="plus" className="mr-2 inline h-4 w-4" />
          Crear Gestor
        </button>
      </div>

      {error && (
        <div role="alert" className="rounded-xl border border-warn/30 bg-warn-soft/60 px-4 py-3 text-sm text-warn">{error}</div>
      )}

      {credencial && (
        <div className="rounded-2xl border border-forest/30 bg-forest-soft/60 p-5">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="text-sm font-bold text-forest">Gestor creado exitosamente</h3>
              <p className="mt-1 text-xs text-ink-faint">Guarde estas credenciales, solo se muestran una vez.</p>
            </div>
            <button onClick={() => setCredencial(null)} className="text-ink-faint hover:text-ink"><Icon name="close" /></button>
          </div>
          <div className="mt-3 grid gap-3 sm:grid-cols-4">
            <div className="rounded-xl bg-white p-3"><p className="text-[10px] font-bold uppercase text-ink-faint">Código</p><p className="mt-0.5 font-mono text-sm font-bold text-pine">{credencial.codigo}</p></div>
            <div className="rounded-xl bg-white p-3"><p className="text-[10px] font-bold uppercase text-ink-faint">Usuario</p><p className="mt-0.5 font-mono text-sm font-bold text-pine">{credencial.username}</p></div>
            <div className="rounded-xl bg-white p-3 sm:col-span-2"><p className="text-[10px] font-bold uppercase text-ink-faint">Contraseña</p><p className="mt-0.5 font-mono text-sm font-bold text-warn break-all">{credencial.nueva_password_temporal}</p></div>
          </div>
        </div>
      )}

      {tab === 'lista' && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative flex-1 sm:max-w-xs">
              <Icon name="search" className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
              <input
                value={search}
                onChange={(e) => { setSearch(e.target.value); setPage(1) }}
                placeholder="Buscar por nombre, usuario, email..."
                className="w-full rounded-xl border border-line bg-white py-2.5 pl-10 pr-4 text-sm text-ink outline-none focus:border-pine focus:ring-2 focus:ring-pine/10"
              />
            </div>
            <select
              value={estadoFilter}
              onChange={(e) => { setEstadoFilter(e.target.value); setPage(1) }}
              className="rounded-xl border border-line bg-white px-3 py-2.5 text-sm text-ink outline-none focus:border-pine"
            >
              <option value="">Todos los estados</option>
              <option value="ACTIVO">Activos</option>
              <option value="INACTIVO">Inactivos</option>
              <option value="BLOQUEADO">Bloqueados</option>
            </select>
          </div>

          {loading ? (
            <div className="space-y-3">{[1, 2, 3].map((i) => <div key={i} className="h-20 animate-pulse rounded-2xl bg-line/40" />)}</div>
          ) : items.length === 0 ? (
            <div className="flex min-h-48 flex-col items-center justify-center rounded-2xl border border-line bg-white text-center">
              <Icon name="people" className="h-10 w-10 text-ink-faint" />
              <h3 className="mt-4 text-lg font-bold text-ink">Sin gestores</h3>
              <p className="mt-1 text-sm text-ink-faint">Cree un nuevo gestor para comenzar.</p>
              <button onClick={() => setTab('crear')} className="mt-4 rounded-xl bg-pine px-5 py-2.5 text-sm font-bold text-white hover:bg-pine-deep">
                <Icon name="plus" className="mr-1 inline h-4 w-4" /> Crear gestor
              </button>
            </div>
          ) : (
            <>
              <div className="overflow-hidden rounded-2xl border border-line bg-white shadow-sm">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-line bg-paper text-[11px] font-bold uppercase tracking-wider text-ink-faint">
                      <th className="px-5 py-3">Gestor</th>
                      <th className="hidden px-5 py-3 md:table-cell">Código</th>
                      <th className="hidden px-5 py-3 lg:table-cell">Rol</th>
                      <th className="hidden px-5 py-3 xl:table-cell">Dependencia</th>
                      <th className="px-5 py-3">Estado</th>
                      <th className="hidden px-5 py-3 sm:table-cell">Último acceso</th>
                      <th className="px-5 py-3 text-right">Acciones</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line">
                    {items.map((g) => (
                      <tr key={g.id} className="transition-colors hover:bg-paper">
                        <td className="px-5 py-4">
                          <div className="flex items-center gap-3">
                            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-pine/10 font-bold text-pine text-xs">
                              {g.nombre_completo.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()}
                            </div>
                            <div className="min-w-0">
                              <p className="font-bold text-ink truncate">{g.nombre_completo}</p>
                              <p className="text-xs text-ink-faint truncate">@{g.username} · {g.email}</p>
                              {g.cargo && <p className="text-xs text-ink-faint truncate">{g.cargo}</p>}
                            </div>
                          </div>
                        </td>
                        <td className="hidden px-5 py-4 md:table-cell"><span className="font-mono text-xs font-bold text-pine">{g.codigo}</span></td>
                        <td className="hidden px-5 py-4 lg:table-cell"><span className="rounded-lg bg-forest-soft px-2 py-1 text-[11px] font-bold text-forest">{g.rol || 'Sin rol'}</span></td>
                        <td className="hidden px-5 py-4 xl:table-cell"><span className="text-xs text-ink-soft">{g.dependencia_principal || '—'}</span></td>
                        <td className="px-5 py-4"><span className={clsx('inline-flex rounded-full px-2.5 py-1 text-[11px] font-bold', estadoTone[g.estado] || 'bg-line/60 text-ink-soft')}>{g.estado}</span></td>
                        <td className="hidden px-5 py-4 sm:table-cell"><span className="text-xs text-ink-faint">{formatDate(g.ultimo_acceso)}</span></td>
                        <td className="px-5 py-4">
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              onClick={() => setDetailGestor(g)}
                              className="rounded-lg bg-pine/8 p-2 text-pine transition-colors hover:bg-pine hover:text-white"
                              title="Ver detalle"
                              aria-label="Ver detalle"
                            >
                              <Icon name="eye" />
                            </button>
                            <button
                              onClick={() => setPasswordGestor(g)}
                              className="rounded-lg bg-ochre/10 p-2 text-ochre-deep transition-colors hover:bg-ochre hover:text-white"
                              title="Cambiar contraseña"
                              aria-label="Cambiar contraseña"
                            >
                              <Icon name="key" />
                            </button>
                            <button
                              onClick={() => handleToggleEstado(g)}
                              className={clsx(
                                'rounded-lg p-2 transition-colors',
                                g.estado === 'ACTIVO'
                                  ? 'bg-warn/10 text-warn hover:bg-warn hover:text-white'
                                  : 'bg-forest/10 text-forest hover:bg-forest hover:text-white',
                              )}
                              title={g.estado === 'ACTIVO' ? 'Desactivar' : 'Activar'}
                              aria-label={g.estado === 'ACTIVO' ? 'Desactivar' : 'Activar'}
                            >
                              <Icon name={g.estado === 'ACTIVO' ? 'pause' : 'play'} />
                            </button>
                            <button
                              onClick={() => setDeleteGestor(g)}
                              className="rounded-lg bg-warn/15 p-2 text-warn ring-1 ring-warn/20 transition-colors hover:bg-warn hover:text-white"
                              title="Eliminar gestor"
                              aria-label="Eliminar gestor"
                            >
                              <Icon name="trash" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {totalPages > 1 && (
                <div className="flex items-center justify-between text-sm text-ink-faint">
                  <p>Página {page} de {totalPages} ({total} registros)</p>
                  <div className="flex gap-2">
                    <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)} className="rounded-lg border border-line px-3 py-1.5 text-xs font-bold disabled:opacity-40">Anterior</button>
                    <button disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)} className="rounded-lg border border-line px-3 py-1.5 text-xs font-bold disabled:opacity-40">Siguiente</button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {tab === 'crear' && <CrearGestorForm onSubmit={handleCreate} onCancel={() => setTab('lista')} />}

      {detailGestor && <DetalleGestorModal gestor={detailGestor} onClose={() => setDetailGestor(null)} onRefresh={load} onChangePassword={(g) => { setDetailGestor(null); setPasswordGestor(g) }} />}

      {passwordGestor && (
        <CambiarPasswordModal
          gestor={passwordGestor}
          onClose={() => setPasswordGestor(null)}
          onDone={(cred) => { setCredencial(cred); setPasswordGestor(null); load() }}
        />
      )}

      {deleteGestor && (
        <ModalShell title="¿Eliminar gestor?" description="Confirme la eliminación permanente de esta cuenta." close={() => !deleteLoading && setDeleteGestor(null)}>
          <div className="space-y-5 p-6">
            <div className="flex items-start gap-4 rounded-2xl border border-warn/25 bg-warn-soft/50 p-4">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-warn text-white shadow-sm">
                <Icon name="trash" className="h-5 w-5" />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-bold text-ink">Esta acción es irreversible.</p>
                <p className="mt-0.5 text-sm leading-5 text-ink-soft">
                  Se eliminará la cuenta y el acceso de este gestor al sistema. El registro quedará en auditoría.
                </p>
              </div>
            </div>

            <div className="rounded-2xl border border-line bg-paper/70 p-4">
              <div className="flex items-center gap-3">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-pine text-xs font-bold text-white">
                  {deleteGestor.nombre_completo.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()}
                </div>
                <div className="min-w-0">
                  <p className="truncate text-sm font-bold text-ink">{deleteGestor.nombre_completo}</p>
                  <p className="truncate text-xs text-ink-faint">
                    @{deleteGestor.username} · {deleteGestor.codigo}
                    {deleteGestor.rol ? ` · ${deleteGestor.rol}` : ''}
                  </p>
                </div>
              </div>
              {deleteGestor.dependencia_principal && (
                <p className="mt-3 border-t border-line/80 pt-3 text-xs text-ink-faint">
                  Dependencia: <span className="font-bold text-ink-soft">{deleteGestor.dependencia_principal}</span>
                </p>
              )}
            </div>

            <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <button
                onClick={() => setDeleteGestor(null)}
                disabled={deleteLoading}
                className="rounded-xl border border-line bg-white px-5 py-2.5 text-sm font-bold text-ink transition-colors hover:bg-paper disabled:opacity-50"
              >
                Cancelar
              </button>
              <button
                onClick={handleDelete}
                disabled={deleteLoading}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-warn px-5 py-2.5 text-sm font-bold text-white shadow-sm transition-colors hover:bg-warn/90 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {deleteLoading ? (
                  <>
                    <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Eliminando...
                  </>
                ) : (
                  <>
                    <Icon name="trash" className="h-4 w-4" />
                    Eliminar gestor
                  </>
                )}
              </button>
            </div>
          </div>
        </ModalShell>
      )}
    </div>
  )
}

function CrearGestorForm({ onSubmit, onCancel }: { onSubmit: (d: GestorCreatePayload) => Promise<void>; onCancel: () => void }) {
  const { user } = useAuthStore()
  const isAdmin = user?.roles?.some((r) => ADMIN_ROLES.includes(r)) ?? false
  const [form, setForm] = useState<GestorCreatePayload>({
    nombre_completo: '', email: '', telefono: '', cargo: '',
    dependencias_adicionales: [], username: '', password: '', rol_id: '',
  })
  const [dependencias, setDependencias] = useState<Dependencia[]>([])
  const [roles, setRoles] = useState<Rol[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    catalogos.dependencias().then((r) => setDependencias(r.data)).catch(() => {})
    catalogos.roles().then((r) => {
      const visible = isAdmin ? r.data : r.data.filter((rol) => COORDINATOR_CREATE_ROLES.includes(rol.codigo))
      setRoles(visible)
      const preferred = visible.find((rol) => rol.codigo === 'GESTOR') || visible[0]
      if (preferred) setForm((f) => ({ ...f, rol_id: f.rol_id || preferred.id }))
    }).catch(() => {})
  }, [isAdmin])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.nombre_completo || !form.email) { setError('Nombre y email son obligatorios.'); return }
    if (!form.dependencia_principal_id) {
      setError('La dependencia principal es obligatoria. El gestor solo debe estar asociado a su dependencia.')
      return
    }
    if (form.password && form.password.length < PASSWORD_MIN) {
      setError(`La contraseña debe tener al menos ${PASSWORD_MIN} caracteres.`)
      return
    }
    if (form.username && form.username.length < 3) {
      setError('El usuario debe tener al menos 3 caracteres.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const payload: GestorCreatePayload = {
        ...form,
        dependencias_adicionales: [],
        username: form.username?.trim() || undefined,
        password: form.password || undefined,
        rol_id: form.rol_id || undefined,
      }
      await onSubmit(payload)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
      setError(typeof msg === 'string' ? msg : 'Error al crear gestor')
    } finally {
      setLoading(false)
    }
  }

  const inputClass = 'mt-1 w-full rounded-xl border border-line px-4 py-2.5 text-sm outline-none focus:border-pine focus:ring-2 focus:ring-pine/10'

  return (
    <form onSubmit={handleSubmit} className="rounded-2xl border border-line bg-white p-6 shadow-sm">
      <h3 className="text-lg font-bold text-ink">Nuevo Gestor</h3>
      <p className="mt-1 text-sm text-ink-faint">Defina el rol, usuario y contraseña. Si deja usuario o contraseña vacíos, se autogenerarán.</p>

      {error && <div className="mt-4 rounded-xl border border-warn/30 bg-warn-soft/60 px-4 py-3 text-sm text-warn">{error}</div>}

      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        <div>
          <label className="text-xs font-bold uppercase text-ink-faint">Nombre completo *</label>
          <input value={form.nombre_completo} onChange={(e) => setForm({ ...form, nombre_completo: e.target.value })} className={inputClass} placeholder="Ej: Juan Pérez" />
        </div>
        <div>
          <label className="text-xs font-bold uppercase text-ink-faint">Email *</label>
          <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className={inputClass} placeholder="juan@ejemplo.com" />
        </div>
        <div>
          <label className="text-xs font-bold uppercase text-ink-faint">Teléfono</label>
          <input value={form.telefono || ''} onChange={(e) => setForm({ ...form, telefono: e.target.value })} className={inputClass} placeholder="300 123 4567" />
        </div>
        <div>
          <label className="text-xs font-bold uppercase text-ink-faint">Cargo</label>
          <input value={form.cargo || ''} onChange={(e) => setForm({ ...form, cargo: e.target.value })} className={inputClass} placeholder="Ej: Gestor" />
        </div>
        <div>
          <label className="text-xs font-bold uppercase text-ink-faint">Rol</label>
          <select value={form.rol_id || ''} onChange={(e) => setForm({ ...form, rol_id: e.target.value })} className={inputClass}>
            {roles.map((r) => <option key={r.id} value={r.id}>{r.nombre}</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs font-bold uppercase text-ink-faint">Dependencia principal *</label>
          <select value={form.dependencia_principal_id || ''} onChange={(e) => setForm({ ...form, dependencia_principal_id: e.target.value || undefined })} className={inputClass}>
            <option value="">Seleccione su dependencia</option>
            {dependencias.map((d) => <option key={d.id} value={d.id}>{d.nombre}</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs font-bold uppercase text-ink-faint">Usuario (opcional)</label>
          <input
            value={form.username || ''}
            onChange={(e) => setForm({ ...form, username: e.target.value })}
            className={inputClass}
            placeholder="Autogenerado si se deja vacío"
            autoComplete="off"
          />
        </div>
        <div>
          <label className="text-xs font-bold uppercase text-ink-faint">Contraseña (opcional)</label>
          <input
            type="text"
            value={form.password || ''}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            className={inputClass}
            placeholder={`Mínimo ${PASSWORD_MIN} caracteres o autogenerar`}
            autoComplete="new-password"
          />
          <p className="mt-1 text-[11px] text-ink-faint">Si se vacía, se genera una contraseña temporal de 24 caracteres.</p>
        </div>
      </div>

      <div className="mt-6 flex justify-end gap-3">
        <button type="button" onClick={onCancel} className="rounded-xl border border-line px-5 py-2.5 text-sm font-bold text-ink hover:bg-paper">Cancelar</button>
        <button type="submit" disabled={loading} className="rounded-xl bg-pine px-5 py-2.5 text-sm font-bold text-white hover:bg-pine-deep disabled:opacity-50">
          {loading ? 'Creando...' : 'Crear Gestor'}
        </button>
      </div>
    </form>
  )
}

function DetalleGestorModal({ gestor, onClose, onRefresh, onChangePassword }: {
  gestor: Gestor
  onClose: () => void
  onRefresh: () => void
  onChangePassword: (g: Gestor) => void
}) {
  const [carga, setCarga] = useState<Producto[]>([])
  const [cargaLoading, setCargaLoading] = useState(true)

  useEffect(() => {
    let cancel = false
    setCargaLoading(true)
    productos
      .list({ page: 1, page_size: 100, gestor_id: gestor.id })
      .then((res) => {
        if (!cancel) setCarga(res.data.items)
      })
      .catch(() => {
        if (!cancel) setCarga([])
      })
      .finally(() => {
        if (!cancel) setCargaLoading(false)
      })
    return () => {
      cancel = true
    }
  }, [gestor.id])

  const programasUnicos = Array.from(
    new Map(carga.map((p) => [p.programa_id, p.programa_nombre || 'Sin programa'])).entries(),
  )
  const estadoTone: Record<string, string> = {
    ACTIVO: 'bg-forest-soft text-forest',
    INACTIVO: 'bg-line/60 text-ink-soft',
    BLOQUEADO: 'bg-warn-soft text-warn',
  }
  const initials = gestor.nombre_completo
    .split(' ')
    .map((n) => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()

  const fields: Array<{ label: string; value: string; mono?: boolean }> = [
    { label: 'Código', value: gestor.codigo, mono: true },
    { label: 'Usuario', value: `@${gestor.username}`, mono: true },
    { label: 'Correo', value: gestor.email },
    { label: 'Teléfono', value: gestor.telefono || 'Sin registro' },
    { label: 'Cargo', value: gestor.cargo || 'Sin asignar' },
    { label: 'Dependencia', value: gestor.dependencia_principal || 'Sin asignar' },
  ]

  return (
    <ModalShell
      title="Detalle del gestor"
      description="Cuenta, acceso y carga de trabajo asignada."
      close={onClose}
      wide
    >
      <div className="space-y-5 p-6">
        <div className="flex flex-col gap-4 rounded-2xl border border-line bg-paper/60 p-4 sm:flex-row sm:items-center">
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-pine text-base font-bold text-white shadow-sm">
            {initials}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-lg font-bold text-ink">{gestor.nombre_completo}</p>
            <p className="mt-0.5 truncate text-sm text-ink-faint">
              {gestor.email}
              {gestor.dependencia_principal ? ` · ${gestor.dependencia_principal}` : ''}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-2 rounded-full bg-forest-soft px-3 py-1 text-xs font-bold text-forest">
              {gestor.rol || 'Sin rol'}
            </span>
            <span className={clsx('inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold', estadoTone[gestor.estado] || 'bg-line/60 text-ink-soft')}>
              <span className="h-1.5 w-1.5 rounded-full bg-current" />
              {gestor.estado}
            </span>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {fields.map((f) => (
            <div key={f.label} className="rounded-xl border border-line bg-white p-3.5">
              <p className="text-[10px] font-bold uppercase tracking-wider text-ink-faint">{f.label}</p>
              <p className={clsx('mt-1 break-words text-sm text-ink', f.mono && 'font-mono font-bold text-pine')}>
                {f.value}
              </p>
            </div>
          ))}
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-xl border border-line bg-white p-3.5">
            <p className="text-[10px] font-bold uppercase tracking-wider text-ink-faint">Último acceso</p>
            <p className="mt-1 text-sm text-ink">{formatDate(gestor.ultimo_acceso)}</p>
          </div>
          <div className="rounded-xl border border-line bg-white p-3.5">
            <p className="text-[10px] font-bold uppercase tracking-wider text-ink-faint">Cuenta creada</p>
            <p className="mt-1 text-sm text-ink">{formatDate(gestor.created_at)}</p>
          </div>
        </div>

        {gestor.dependencias?.length > 0 && (
          <div>
            <p className="text-[10px] font-bold uppercase tracking-wider text-ink-faint">Dependencias asociadas</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {gestor.dependencias.map((d) => (
                <span
                  key={d.id}
                  className={clsx(
                    'inline-flex items-center rounded-full px-3 py-1 text-xs font-bold',
                    d.es_principal ? 'bg-pine text-white' : 'bg-line/50 text-ink-soft',
                  )}
                >
                  {d.nombre}
                  {d.es_principal ? ' · Principal' : ''}
                </span>
              ))}
            </div>
          </div>
        )}

        <section className="rounded-2xl border border-line bg-white p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-ink-faint">Carga de trabajo</p>
              <p className="mt-0.5 text-sm font-bold text-ink">Programas y productos que debe desempeñar</p>
            </div>
            {cargaLoading ? (
              <span className="text-xs font-bold text-ink-faint">Cargando…</span>
            ) : (
              <div className="flex gap-2">
                <span className="rounded-full bg-ochre-soft px-3 py-1 text-xs font-bold text-ochre">
                  {programasUnicos.length} programas
                </span>
                <span className="rounded-full bg-forest-soft px-3 py-1 text-xs font-bold text-forest">
                  {carga.length} productos
                </span>
              </div>
            )}
          </div>

          {!cargaLoading && programasUnicos.length > 0 && (
            <div className="mt-3">
              <p className="text-[10px] font-bold uppercase tracking-wider text-ink-faint">Programas</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {programasUnicos.map(([id, nombre]) => (
                  <span key={id} className="inline-flex items-center gap-2 rounded-xl border border-line bg-paper px-3 py-1.5 text-xs">
                    <Icon name="layers" className="h-3.5 w-3.5 text-pine" />
                    <span className="font-semibold text-ink">{nombre}</span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {!cargaLoading && carga.length > 0 && (
            <div className="mt-4 overflow-hidden rounded-xl border border-line">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-line bg-paper text-[10px] font-bold uppercase tracking-wider text-ink-faint">
                    <th className="px-3 py-2">Producto</th>
                    <th className="hidden px-3 py-2 sm:table-cell">Programa</th>
                    <th className="px-3 py-2">Asignado</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {carga.map((p) => (
                    <tr key={p.id}>
                      <td className="px-3 py-2.5">
                        <span className="font-mono font-bold text-pine">{p.codigo}</span>
                        <p className="mt-0.5 font-semibold text-ink">{p.nombre}</p>
                      </td>
                      <td className="hidden px-3 py-2.5 text-ink-soft sm:table-cell">
                        {p.programa_nombre || '—'}
                      </td>
                      <td className="px-3 py-2.5 text-ink-soft">{formatDate(p.asignado_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {!cargaLoading && carga.length === 0 && (
            <p className="mt-3 text-sm text-ink-faint">Este gestor aún no tiene productos asignados.</p>
          )}
        </section>
      </div>

      <div className="flex flex-col-reverse gap-2 border-t border-line px-6 py-4 sm:flex-row sm:justify-end">
        <button
          onClick={() => { onRefresh(); onClose() }}
          className="rounded-xl border border-line px-5 py-2.5 text-sm font-bold text-ink transition-colors hover:bg-paper"
        >
          Cerrar
        </button>
        <button
          onClick={() => onChangePassword(gestor)}
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-forest px-5 py-2.5 text-sm font-bold text-white shadow-sm transition-colors hover:bg-forest/90"
        >
          <Icon name="key" className="h-4 w-4" />
          Cambiar contraseña
        </button>
      </div>
    </ModalShell>
  )
}

function CambiarPasswordModal({ gestor, onClose, onDone }: {
  gestor: Gestor
  onClose: () => void
  onDone: (cred: CredencialTemporal) => void
}) {
  const [mode, setMode] = useState<'auto' | 'custom'>('auto')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (mode === 'custom') {
      if (password.length < PASSWORD_MIN) {
        setError(`La contraseña debe tener al menos ${PASSWORD_MIN} caracteres.`)
        return
      }
      if (password !== confirm) {
        setError('Las contraseñas no coinciden.')
        return
      }
    }
    setLoading(true)
    try {
      const res = await gestores.resetPassword(gestor.id, mode === 'custom' ? password : undefined)
      onDone(res.data)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
      setError(typeof msg === 'string' ? msg : 'No fue posible cambiar la contraseña.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <ModalShell title="Cambiar contraseña" close={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4 p-6">
        <div className="rounded-xl bg-paper p-4">
          <p className="text-[10px] font-bold uppercase text-ink-faint">Gestor</p>
          <p className="mt-0.5 font-bold text-ink">{gestor.nombre_completo}</p>
          <p className="font-mono text-xs text-ink-faint">@{gestor.username} · {gestor.codigo}</p>
        </div>

        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setMode('auto')}
            className={clsx('flex-1 rounded-xl border px-4 py-2.5 text-sm font-bold', mode === 'auto' ? 'border-pine bg-forest-soft text-pine' : 'border-line text-ink-faint hover:bg-paper')}
          >
            Generar automática
          </button>
          <button
            type="button"
            onClick={() => setMode('custom')}
            className={clsx('flex-1 rounded-xl border px-4 py-2.5 text-sm font-bold', mode === 'custom' ? 'border-pine bg-forest-soft text-pine' : 'border-line text-ink-faint hover:bg-paper')}
          >
            Contraseña personalizada
          </button>
        </div>

        {mode === 'custom' ? (
          <div className="space-y-3">
            <div>
              <label className="text-xs font-bold uppercase text-ink-faint">Nueva contraseña</label>
              <input
                type="text"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 w-full rounded-xl border border-line px-4 py-2.5 text-sm outline-none focus:border-pine focus:ring-2 focus:ring-pine/10"
                placeholder={`Mínimo ${PASSWORD_MIN} caracteres`}
                autoComplete="new-password"
              />
            </div>
            <div>
              <label className="text-xs font-bold uppercase text-ink-faint">Confirmar contraseña</label>
              <input
                type="text"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                className="mt-1 w-full rounded-xl border border-line px-4 py-2.5 text-sm outline-none focus:border-pine focus:ring-2 focus:ring-pine/10"
                placeholder="Repita la contraseña"
                autoComplete="new-password"
              />
            </div>
          </div>
        ) : (
          <p className="rounded-xl bg-ochre-soft/50 px-4 py-3 text-xs text-ochre-deep">
            Se generará una contraseña temporal de 24 caracteres. El gestor deberá cambiarla en su primer ingreso.
          </p>
        )}

        {error && <div className="rounded-xl border border-warn/30 bg-warn-soft/60 px-4 py-3 text-sm text-warn">{error}</div>}

        <div className="flex justify-end gap-3 border-t border-line pt-4">
          <button type="button" onClick={onClose} className="rounded-xl border border-line px-4 py-2 text-sm font-bold text-ink hover:bg-paper">Cancelar</button>
          <button type="submit" disabled={loading} className="rounded-xl bg-pine px-4 py-2 text-sm font-bold text-white hover:bg-pine-deep disabled:opacity-50">
            {loading ? 'Guardando...' : 'Cambiar contraseña'}
          </button>
        </div>
      </form>
    </ModalShell>
  )
}
