import { useEffect, useState, useCallback } from 'react'
import { gestores, catalogos } from '../../lib/api'
import type { Gestor, Dependencia, GestorCreatePayload, CredencialTemporal } from '../../lib/types'
import { Icon, formatDate, ModalShell } from '../../components/ui/icons'
import { clsx } from 'clsx'

type Tab = 'lista' | 'crear'

export default function GestorEquipoPage() {
  const [tab, setTab] = useState<Tab>('lista')
  const [items, setItems] = useState<Gestor[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [estadoFilter, setEstadoFilter] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [detailGestor, setDetailGestor] = useState<Gestor | null>(null)
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const [deleteLoading, setDeleteLoading] = useState(false)
  const [credencial, setCredencial] = useState<CredencialTemporal | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params: Record<string, unknown> = { page, page_size: 10 }
      if (search) params.search = search
      if (estadoFilter) params.estado = estadoFilter
      const res = await gestores.list(params)
      setItems(res.data.items)
      setTotal(res.data.total)
    } catch {
      // silently fail
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
    if (!deleteId) return
    setDeleteLoading(true)
    try {
      await gestores.delete(deleteId)
      setDeleteId(null)
      load()
    } finally {
      setDeleteLoading(false)
    }
  }

  const handleToggleEstado = async (g: Gestor) => {
    if (g.estado === 'ACTIVO') {
      await gestores.deactivate(g.id)
    } else {
      await gestores.activate(g.id)
    }
    load()
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
          <p className="mb-2 text-xs font-bold uppercase tracking-[0.2em] text-ochre-soft">Gestor Líder</p>
          <h1 className="text-3xl font-bold leading-tight sm:text-4xl">Mi Equipo de Gestores</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-white/70">
            Cree, gestione y asigne responsables a los miembros de su equipo.
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
            <div className="rounded-xl bg-white p-3 sm:col-span-2"><p className="text-[10px] font-bold uppercase text-ink-faint">Contraseña temporal</p><p className="mt-0.5 font-mono text-sm font-bold text-warn break-all">{credencial.nueva_password_temporal}</p></div>
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
                      <th className="hidden px-5 py-3 lg:table-cell">Dependencia</th>
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
                              <p className="text-xs text-ink-faint truncate">{g.email}</p>
                              {g.cargo && <p className="text-xs text-ink-faint truncate">{g.cargo}</p>}
                            </div>
                          </div>
                        </td>
                        <td className="hidden px-5 py-4 md:table-cell"><span className="font-mono text-xs font-bold text-pine">{g.codigo}</span></td>
                        <td className="hidden px-5 py-4 lg:table-cell"><span className="text-xs text-ink-soft">{g.dependencia_principal || '—'}</span></td>
                        <td className="px-5 py-4"><span className={clsx('inline-flex rounded-full px-2.5 py-1 text-[11px] font-bold', estadoTone[g.estado] || 'bg-line/60 text-ink-soft')}>{g.estado}</span></td>
                        <td className="hidden px-5 py-4 sm:table-cell"><span className="text-xs text-ink-faint">{formatDate(g.ultimo_acceso)}</span></td>
                        <td className="px-5 py-4">
                          <div className="flex items-center justify-end gap-1">
                            <button onClick={() => setDetailGestor(g)} className="rounded-lg p-2 text-ink-faint transition-colors hover:bg-pine/10 hover:text-pine" title="Ver detalle"><Icon name="document" /></button>
                            <button onClick={() => handleToggleEstado(g)} className={clsx('rounded-lg p-2 transition-colors', g.estado === 'ACTIVO' ? 'text-ink-faint hover:bg-warn-soft hover:text-warn' : 'text-ink-faint hover:bg-forest-soft hover:text-forest')} title={g.estado === 'ACTIVO' ? 'Desactivar' : 'Activar'}>
                              <Icon name={g.estado === 'ACTIVO' ? 'close' : 'check'} />
                            </button>
                            <button onClick={() => setDeleteId(g.id)} className="rounded-lg p-2 text-ink-faint transition-colors hover:bg-warn-soft hover:text-warn" title="Eliminar"><Icon name="trash" /></button>
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

      {detailGestor && <DetalleGestorModal gestor={detailGestor} onClose={() => setDetailGestor(null)} onRefresh={load} />}

      {deleteId && (
        <ModalShell title="Confirmar eliminación" close={() => setDeleteId(null)}>
          <p className="text-sm text-ink-soft">¿Está seguro de eliminar este gestor? Esta acción es irreversible.</p>
          <div className="mt-5 flex justify-end gap-3">
            <button onClick={() => setDeleteId(null)} className="rounded-xl border border-line px-4 py-2 text-sm font-bold text-ink hover:bg-paper">Cancelar</button>
            <button onClick={handleDelete} disabled={deleteLoading} className="rounded-xl bg-warn px-4 py-2 text-sm font-bold text-white hover:bg-warn-deep disabled:opacity-50">
              {deleteLoading ? 'Eliminando...' : 'Eliminar'}
            </button>
          </div>
        </ModalShell>
      )}
    </div>
  )
}

function CrearGestorForm({ onSubmit, onCancel }: { onSubmit: (d: GestorCreatePayload) => Promise<void>; onCancel: () => void }) {
  const [form, setForm] = useState<GestorCreatePayload>({ nombre_completo: '', email: '', telefono: '', cargo: '', dependencias_adicionales: [] })
  const [dependencias, setDependencias] = useState<Dependencia[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    catalogos.dependencias().then((r) => setDependencias(r.data)).catch(() => {})
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.nombre_completo || !form.email) { setError('Nombre y email son obligatorios.'); return }
    setLoading(true)
    setError('')
    try {
      await onSubmit(form)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Error al crear gestor'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-2xl border border-line bg-white p-6 shadow-sm">
      <h3 className="text-lg font-bold text-ink">Nuevo Gestor</h3>
      <p className="mt-1 text-sm text-ink-faint">Complete los datos para crear un nuevo gestor en su equipo.</p>

      {error && <div className="mt-4 rounded-xl border border-warn/30 bg-warn-soft/60 px-4 py-3 text-sm text-warn">{error}</div>}

      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        <div>
          <label className="text-xs font-bold uppercase text-ink-faint">Nombre completo *</label>
          <input value={form.nombre_completo} onChange={(e) => setForm({ ...form, nombre_completo: e.target.value })} className="mt-1 w-full rounded-xl border border-line px-4 py-2.5 text-sm outline-none focus:border-pine focus:ring-2 focus:ring-pine/10" placeholder="Ej: Juan Pérez" />
        </div>
        <div>
          <label className="text-xs font-bold uppercase text-ink-faint">Email *</label>
          <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="mt-1 w-full rounded-xl border border-line px-4 py-2.5 text-sm outline-none focus:border-pine focus:ring-2 focus:ring-pine/10" placeholder="juan@ejemplo.com" />
        </div>
        <div>
          <label className="text-xs font-bold uppercase text-ink-faint">Teléfono</label>
          <input value={form.telefono || ''} onChange={(e) => setForm({ ...form, telefono: e.target.value })} className="mt-1 w-full rounded-xl border border-line px-4 py-2.5 text-sm outline-none focus:border-pine focus:ring-2 focus:ring-pine/10" placeholder="300 123 4567" />
        </div>
        <div>
          <label className="text-xs font-bold uppercase text-ink-faint">Cargo</label>
          <input value={form.cargo || ''} onChange={(e) => setForm({ ...form, cargo: e.target.value })} className="mt-1 w-full rounded-xl border border-line px-4 py-2.5 text-sm outline-none focus:border-pine focus:ring-2 focus:ring-pine/10" placeholder="Ej: Coordinador" />
        </div>
        <div className="sm:col-span-2">
          <label className="text-xs font-bold uppercase text-ink-faint">Dependencia principal</label>
          <select value={form.dependencia_principal_id || ''} onChange={(e) => setForm({ ...form, dependencia_principal_id: e.target.value || undefined })} className="mt-1 w-full rounded-xl border border-line px-4 py-2.5 text-sm outline-none focus:border-pine">
            <option value="">Sin dependencia</option>
            {dependencias.map((d) => <option key={d.id} value={d.id}>{d.nombre}</option>)}
          </select>
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

function DetalleGestorModal({ gestor, onClose, onRefresh }: { gestor: Gestor; onClose: () => void; onRefresh: () => void }) {
  const [resetLoading, setResetLoading] = useState(false)
  const [newPass, setNewPass] = useState<string | null>(null)

  const handleReset = async () => {
    setResetLoading(true)
    try {
      const res = await gestores.resetPassword(gestor.id)
      setNewPass(res.data.nueva_password_temporal)
      onRefresh()
    } finally {
      setResetLoading(false)
    }
  }

  return (
    <ModalShell title={`Gestor: ${gestor.nombre_completo}`} close={onClose} wide>
      <div className="grid gap-4 sm:grid-cols-2 text-sm">
        <div><span className="text-[10px] font-bold uppercase text-ink-faint">Código</span><p className="mt-0.5 font-mono font-bold text-pine">{gestor.codigo}</p></div>
        <div><span className="text-[10px] font-bold uppercase text-ink-faint">Usuario</span><p className="mt-0.5 font-mono font-bold text-pine">{gestor.username}</p></div>
        <div><span className="text-[10px] font-bold uppercase text-ink-faint">Email</span><p className="mt-0.5 text-ink">{gestor.email}</p></div>
        <div><span className="text-[10px] font-bold uppercase text-ink-faint">Estado</span><p className="mt-0.5 text-ink">{gestor.estado}</p></div>
        <div><span className="text-[10px] font-bold uppercase text-ink-faint">Cargo</span><p className="mt-0.5 text-ink">{gestor.cargo || '—'}</p></div>
        <div><span className="text-[10px] font-bold uppercase text-ink-faint">Teléfono</span><p className="mt-0.5 text-ink">{gestor.telefono || '—'}</p></div>
        <div><span className="text-[10px] font-bold uppercase text-ink-faint">Dependencia principal</span><p className="mt-0.5 text-ink">{gestor.dependencia_principal || '—'}</p></div>
        <div><span className="text-[10px] font-bold uppercase text-ink-faint">Último acceso</span><p className="mt-0.5 text-ink">{formatDate(gestor.ultimo_acceso)}</p></div>
      </div>

      <div className="mt-5 border-t border-line pt-4">
        <button onClick={handleReset} disabled={resetLoading} className="rounded-xl border border-warn/30 bg-warn-soft/40 px-4 py-2 text-sm font-bold text-warn hover:bg-warn-soft disabled:opacity-50">
          <Icon name="key" className="mr-1 inline h-4 w-4" />
          {resetLoading ? 'Generando...' : 'Restablecer contraseña'}
        </button>
        {newPass && (
          <div className="mt-3 rounded-xl bg-forest-soft/60 p-3">
            <p className="text-xs font-bold text-forest">Nueva contraseña temporal:</p>
            <p className="mt-1 font-mono text-sm font-bold text-warn break-all">{newPass}</p>
          </div>
        )}
      </div>
    </ModalShell>
  )
}
