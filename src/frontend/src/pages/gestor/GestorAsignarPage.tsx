import { useEffect, useState, useCallback } from 'react'
import { gestores, productos, programas } from '../../lib/api'
import type { Gestor, Programa, Producto } from '../../lib/types'
import { Button } from '../../components/ui/Button'
import { Icon, ModalShell } from '../../components/ui/icons'
import { clsx } from 'clsx'

export default function GestorAsignarPage() {
  const [gestoresList, setGestoresList] = useState<Gestor[]>([])
  const [productosList, setProductosList] = useState<Producto[]>([])
  const [programasList, setProgramasList] = useState<Programa[]>([])
  const [loading, setLoading] = useState(true)
  const [searchProducto, setSearchProducto] = useState('')
  const [selectedGestor, setSelectedGestor] = useState('')
  const [selectedPrograma, setSelectedPrograma] = useState('')
  const [assignModal, setAssignModal] = useState<Producto | null>(null)
  const [assignGestorId, setAssignGestorId] = useState('')
  const [assignLoading, setAssignLoading] = useState(false)
  const [success, setSuccess] = useState('')
  const [error, setError] = useState('')

  const openAssign = (p: Producto) => {
    setAssignModal(p)
    setAssignGestorId(p.gestor_lider_id || '')
    setError('')
  }

  const closeAssign = () => {
    setAssignModal(null)
    setAssignGestorId('')
  }

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [gRes, pRes, prRes] = await Promise.allSettled([
        gestores.list({ page: 1, page_size: 100, estado: 'ACTIVO' }),
        productos.list({ page: 1, page_size: 100 }),
        programas.list({ page: 1, page_size: 100, estado: 'ACTIVO' }),
      ])
      if (gRes.status === 'fulfilled') setGestoresList(gRes.value.data.items)
      if (pRes.status === 'fulfilled') setProductosList(pRes.value.data.items)
      if (prRes.status === 'fulfilled') setProgramasList(prRes.value.data.items)
      setError('')
    } catch {
      setError('No fue posible cargar el catálogo de productos y programas.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const handleAssign = async (productoId: string, gestorLiderId: string) => {
    setAssignLoading(true)
    setError('')
    try {
      await productos.update(productoId, { gestor_lider_id: gestorLiderId || null })
      closeAssign()
      setSuccess(
        gestorLiderId
          ? 'Producto asignado correctamente al gestor.'
          : 'Se quitó la asignación del producto.',
      )
      setTimeout(() => setSuccess(''), 4000)
      load()
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(typeof msg === 'string' ? msg : 'No fue posible guardar la asignación.')
    } finally {
      setAssignLoading(false)
    }
  }

  const filtered = productosList.filter((p) => {
    if (selectedPrograma && p.programa_id !== selectedPrograma) return false
    if (searchProducto) {
      const q = searchProducto.toLowerCase()
      if (!p.codigo.toLowerCase().includes(q) && !p.nombre.toLowerCase().includes(q)) return false
    }
    if (selectedGestor && p.gestor_lider_id !== selectedGestor) return false
    return true
  })

  const getGestorName = (id?: string) => {
    if (!id) return 'Sin asignar'
    const g = gestoresList.find((x) => x.id === id)
    return g ? g.nombre_completo : 'Desconocido'
  }

  const getProgramaNombre = (id: string) =>
    programasList.find((pr) => pr.id === id)?.nombre || 'Sin programa'

  const sinAsignar = productosList.filter((p) => !p.gestor_lider_id).length
  const asignados = productosList.length - sinAsignar

  return (
    <div className="space-y-6 pb-8">
      <section className="relative overflow-hidden rounded-[28px] bg-pine px-6 py-7 text-white shadow-lg sm:px-8 sm:py-9">
        <div className="absolute -right-20 -top-24 h-72 w-72 rounded-full border border-white/10" aria-hidden="true" />
        <div className="relative">
          <p className="mb-2 text-xs font-bold uppercase tracking-[0.2em] text-ochre-soft">Gestor Líder / Coordinador</p>
          <h1 className="text-3xl font-bold leading-tight sm:text-4xl">Asignar Responsables</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-white/70">
            Catálogo precargado de programas y productos de la administración. Aquí solo asigna o reasigna cada producto a un gestor de su equipo; no se crean productos ni programas.
          </p>
        </div>
      </section>

      {success && (
        <div className="flex items-center gap-3 rounded-2xl border border-forest/30 bg-forest-soft/60 px-4 py-3 text-sm text-forest">
          <Icon name="check" /> {success}
        </div>
      )}
      {error && (
        <div role="alert" className="flex items-center gap-3 rounded-2xl border border-warn/30 bg-warn-soft/60 px-4 py-3 text-sm text-warn">
          <Icon name="alert" /> {error}
        </div>
      )}

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {[
          ['Programas precargados', programasList.length, 'text-pine'],
          ['Productos en catálogo', productosList.length, 'text-forest'],
          ['Sin asignar', sinAsignar, 'text-ochre-deep'],
          ['Asignados', asignados, 'text-forest'],
        ].map(([label, value, tone]) => (
          <div key={String(label)} className="rounded-2xl border border-line bg-white p-4 shadow-sm">
            <p className="text-xs font-bold uppercase tracking-wider text-ink-faint">{label}</p>
            <p className={`mt-2 text-3xl font-bold ${tone}`}>{value}</p>
          </div>
        ))}
      </div>

      {programasList.length > 0 && (
        <section className="rounded-2xl border border-line bg-white p-5 shadow-sm">
          <div className="mb-3 flex items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-bold text-ink">Programas (solo consulta)</h2>
              <p className="mt-0.5 text-xs text-ink-faint">Cargados por la administración. El coordinador no crea ni edita programas.</p>
            </div>
            <span className="rounded-full bg-forest-soft px-2.5 py-1 text-[11px] font-bold text-forest">
              {programasList.length} activos
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {programasList.map((pr) => (
              <span
                key={pr.id}
                className="inline-flex items-center gap-2 rounded-xl border border-line bg-paper px-3 py-2 text-xs"
              >
                <span className="font-mono font-bold text-pine">{pr.codigo}</span>
                <span className="font-semibold text-ink">{pr.nombre}</span>
                {pr.sector && (
                  <span className="rounded-full bg-ochre-soft px-2 py-0.5 text-[10px] font-bold text-ochre">
                    {pr.sector}
                  </span>
                )}
              </span>
            ))}
          </div>
        </section>
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
          value={selectedPrograma}
          onChange={(e) => setSelectedPrograma(e.target.value)}
          aria-label="Filtrar por programa"
          className="rounded-xl border border-line bg-white px-3 py-2.5 text-sm text-ink outline-none focus:border-pine"
        >
          <option value="">Todos los programas</option>
          {programasList.map((pr) => (
            <option key={pr.id} value={pr.id}>{pr.codigo} — {pr.nombre}</option>
          ))}
        </select>
        <select
          value={selectedGestor}
          onChange={(e) => setSelectedGestor(e.target.value)}
          aria-label="Filtrar por gestor"
          className="rounded-xl border border-line bg-white px-3 py-2.5 text-sm text-ink outline-none focus:border-pine"
        >
          <option value="">Todos los gestores</option>
          {gestoresList.map((g) => (
            <option key={g.id} value={g.id}>{g.nombre_completo}</option>
          ))}
        </select>
      </div>

      {selectedGestor && (() => {
        const g = gestoresList.find((x) => x.id === selectedGestor)
        const misProductos = productosList.filter((p) => p.gestor_lider_id === selectedGestor)
        const misProgramas = Array.from(
          new Map(misProductos.map((p) => [p.programa_id, p.programa_nombre || 'Sin programa'])).entries(),
        )
        return (
          <section className="rounded-2xl border border-pine/20 bg-pine/5 p-5 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-pine text-sm font-bold text-white">
                  {(g?.nombre_completo || '?').split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()}
                </span>
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-wider text-ink-faint">Carga del gestor seleccionado</p>
                  <p className="text-lg font-bold text-ink">{g?.nombre_completo || 'Desconocido'}</p>
                  {g && (
                    <p className="text-xs text-ink-faint">
                      {[g.codigo, g.cargo, g.dependencia_principal].filter(Boolean).join(' · ')}
                    </p>
                  )}
                </div>
              </div>
              <div className="flex gap-2">
                <span className="rounded-full bg-ochre-soft px-3 py-1 text-xs font-bold text-ochre">
                  {misProgramas.length} programas
                </span>
                <span className="rounded-full bg-forest-soft px-3 py-1 text-xs font-bold text-forest">
                  {misProductos.length} productos
                </span>
              </div>
            </div>

            {misProgramas.length > 0 && (
              <div className="mt-4">
                <p className="text-[10px] font-bold uppercase tracking-wider text-ink-faint">Programas a desempeñar</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {misProgramas.map(([id, nombre]) => (
                    <span key={id} className="inline-flex items-center gap-2 rounded-xl border border-line bg-white px-3 py-1.5 text-xs">
                      <Icon name="layers" className="h-3.5 w-3.5 text-pine" />
                      <span className="font-semibold text-ink">{nombre}</span>
                    </span>
                  ))}
                </div>
              </div>
            )}

            {misProductos.length > 0 && (
              <div className="mt-4 overflow-hidden rounded-xl border border-line bg-white">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-line bg-paper text-[10px] font-bold uppercase tracking-wider text-ink-faint">
                      <th className="px-3 py-2">Producto</th>
                      <th className="hidden px-3 py-2 sm:table-cell">Programa</th>
                      <th className="px-3 py-2">Asignado</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line">
                    {misProductos.map((p) => (
                      <tr key={p.id}>
                        <td className="px-3 py-2.5">
                          <span className="font-mono font-bold text-pine">{p.codigo}</span>
                          <p className="mt-0.5 font-semibold text-ink">{p.nombre}</p>
                        </td>
                        <td className="hidden px-3 py-2.5 text-ink-soft sm:table-cell">
                          {p.programa_nombre || getProgramaNombre(p.programa_id)}
                        </td>
                        <td className="px-3 py-2.5 text-ink-soft">
                          {p.asignado_at
                            ? new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(p.asignado_at))
                            : 'Sin fecha'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {misProductos.length === 0 && (
              <p className="mt-3 text-sm text-ink-faint">Este gestor aún no tiene productos asignados.</p>
            )}
          </section>
        )
      })()}

      {loading ? (
        <div className="space-y-3">{[1, 2, 3, 4].map((i) => <div key={i} className="h-16 animate-pulse rounded-2xl bg-line/40" />)}</div>
      ) : filtered.length === 0 ? (
        <div className="flex min-h-48 flex-col items-center justify-center rounded-2xl border border-line bg-white text-center">
          <Icon name="box" className="h-10 w-10 text-ink-faint" />
          <h3 className="mt-4 text-lg font-bold text-ink">Sin productos</h3>
          <p className="mt-1 max-w-sm text-sm text-ink-faint">
            {searchProducto || selectedGestor || selectedPrograma
              ? 'No se encontraron resultados con los filtros aplicados.'
              : 'No hay productos precargados en el catálogo. Solicite a la administración cargar programas y productos.'}
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-line bg-white shadow-sm">
          <div className="border-b border-line bg-paper/70 px-5 py-3">
            <p className="text-xs font-bold uppercase tracking-wider text-ink-faint">
              Productos precargados — asigne un responsable por producto
            </p>
          </div>
          <div className="overflow-x-auto">
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
                    <td className="hidden px-5 py-4 md:table-cell">
                      <span className="text-xs text-ink-soft">{p.programa_nombre || getProgramaNombre(p.programa_id)}</span>
                    </td>
                    <td className="hidden px-5 py-4 lg:table-cell">
                      <span className="text-xs text-ink-soft">
                        {p.meta_cuatrienio != null ? `${p.meta_cuatrienio.toLocaleString()} ${p.unidad_medida || ''}` : '—'}
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className={clsx('text-xs font-bold', p.gestor_lider_id ? 'text-forest' : 'text-ink-faint')}>
                        {getGestorName(p.gestor_lider_id)}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-right">
                      <button
                        onClick={() => openAssign(p)}
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
        </div>
      )}

      {assignModal && (() => {
        const selectedGestor = gestoresList.find((g) => g.id === assignGestorId)
        const currentGestor = gestoresList.find((g) => g.id === assignModal.gestor_lider_id)
        const isChange = Boolean(assignModal.gestor_lider_id) && assignModal.gestor_lider_id !== assignGestorId
        const isUnassign = Boolean(assignModal.gestor_lider_id) && !assignGestorId
        const meta = assignModal.meta_cuatrienio != null
          ? `${assignModal.meta_cuatrienio.toLocaleString()}${assignModal.unidad_medida ? ` ${assignModal.unidad_medida}` : ''}`
          : '—'

        return (
          <ModalShell
            title={assignModal.gestor_lider_id ? 'Reasignar responsable' : 'Asignar responsable'}
            description="Confirme el gestor de su equipo que se hará cargo de este producto del catálogo."
            close={closeAssign}
            wide
          >
            <div className="space-y-5 p-6">
              {error && (
                <div role="alert" className="flex items-start gap-3 rounded-xl border border-warn/30 bg-warn-soft/60 px-4 py-3 text-sm text-warn">
                  <Icon name="alert" className="mt-0.5 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <section className="overflow-hidden rounded-2xl border border-line bg-white shadow-sm">
                <div className="flex items-start gap-4 border-b border-line bg-gradient-to-r from-paper to-white px-5 py-4">
                  <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-pine text-white shadow-sm">
                    <Icon name="box" className="h-6 w-6" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="rounded-md bg-pine/10 px-2 py-0.5 font-mono text-xs font-bold text-pine">
                        {assignModal.codigo}
                      </span>
                      <span className={clsx(
                        'inline-flex rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide',
                        assignModal.estado === 'ACTIVO' ? 'bg-forest-soft text-forest' : 'bg-line/60 text-ink-soft',
                      )}>
                        {assignModal.estado}
                      </span>
                      {!assignModal.gestor_lider_id && (
                        <span className="inline-flex rounded-full bg-ochre-soft px-2 py-0.5 text-[10px] font-bold uppercase text-ochre">
                          Sin asignar
                        </span>
                      )}
                    </div>
                    <h3 className="mt-1.5 text-lg font-bold leading-snug text-ink">
                      {assignModal.nombre}
                    </h3>
                    <p className="mt-1 flex items-center gap-1.5 text-xs text-ink-faint">
                      <Icon name="layers" className="h-3.5 w-3.5 shrink-0" />
                      {assignModal.programa_nombre || getProgramaNombre(assignModal.programa_id)}
                    </p>
                  </div>
                </div>

                <dl className="grid grid-cols-2 gap-px bg-line sm:grid-cols-3">
                  <div className="bg-white px-4 py-3">
                    <dt className="text-[10px] font-bold uppercase tracking-wider text-ink-faint">Meta cuatrienio</dt>
                    <dd className="mt-1 text-sm font-bold text-ink">{meta}</dd>
                  </div>
                  <div className="bg-white px-4 py-3">
                    <dt className="text-[10px] font-bold uppercase tracking-wider text-ink-faint">Indicador</dt>
                    <dd className="mt-1 truncate text-sm font-semibold text-ink" title={assignModal.indicador || '—'}>
                      {assignModal.indicador || '—'}
                    </dd>
                  </div>
                  <div className="col-span-2 bg-white px-4 py-3 sm:col-span-1">
                    <dt className="text-[10px] font-bold uppercase tracking-wider text-ink-faint">Dependencia</dt>
                    <dd className="mt-1 truncate text-sm font-semibold text-ink" title={assignModal.dependencia_nombre || '—'}>
                      {assignModal.dependencia_nombre || 'Sin dependencia'}
                    </dd>
                  </div>
                </dl>

                {currentGestor && (
                  <div className="flex items-center gap-3 border-t border-line bg-forest-soft/40 px-5 py-3">
                    <span className="flex h-8 w-8 items-center justify-center rounded-full bg-forest text-xs font-bold text-white">
                      {currentGestor.nombre_completo.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()}
                    </span>
                    <div className="min-w-0">
                      <p className="text-[10px] font-bold uppercase tracking-wider text-forest">Responsable actual</p>
                      <p className="truncate text-sm font-bold text-ink">
                        {currentGestor.nombre_completo}
                        <span className="ml-1.5 font-mono text-xs font-semibold text-ink-faint">{currentGestor.codigo}</span>
                      </p>
                    </div>
                  </div>
                )}
              </section>

              <section>
                <label htmlFor="gestor-select" className="mb-2 flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-ink-faint">
                  <Icon name="people" className="h-3.5 w-3.5" />
                  Gestor responsable <span className="text-warn">*</span>
                </label>
                <select
                  id="gestor-select"
                  value={assignGestorId}
                  onChange={(e) => setAssignGestorId(e.target.value)}
                  className="block min-h-12 w-full rounded-xl border border-line bg-white px-4 py-3 text-sm text-ink shadow-sm focus:border-pine focus:outline-none focus:ring-2 focus:ring-pine/20"
                >
                  <option value="">Sin asignar (quitar responsable)</option>
                  {gestoresList.map((g) => (
                    <option key={g.id} value={g.id}>
                      {g.nombre_completo} — {g.codigo}{g.dependencia_principal ? ` · ${g.dependencia_principal}` : ''}
                    </option>
                  ))}
                </select>

                <div className="mt-3 rounded-xl border border-line bg-paper/60 p-4">
                  {selectedGestor ? (
                    <div className="flex items-start gap-3">
                      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-pine text-sm font-bold text-white">
                        {selectedGestor.nombre_completo.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()}
                      </span>
                      <div className="min-w-0">
                        <p className="text-[10px] font-bold uppercase tracking-wider text-ink-faint">Vista previa</p>
                        <p className="mt-0.5 font-bold text-ink">{selectedGestor.nombre_completo}</p>
                        <p className="mt-0.5 text-xs text-ink-faint">
                          {selectedGestor.codigo}
                          {selectedGestor.cargo ? ` · ${selectedGestor.cargo}` : ''}
                          {selectedGestor.dependencia_principal ? ` · ${selectedGestor.dependencia_principal}` : ''}
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-start gap-3">
                      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-line text-ink-faint">
                        <Icon name="user" className="h-5 w-5" />
                      </span>
                      <div>
                        <p className="text-[10px] font-bold uppercase tracking-wider text-ink-faint">Vista previa</p>
                        <p className="mt-0.5 text-sm font-semibold text-ink-soft">Sin responsable</p>
                        <p className="mt-0.5 text-xs text-ink-faint">El producto quedará disponible para asignar después.</p>
                      </div>
                    </div>
                  )}
                </div>

                <p className="mt-3 flex items-start gap-2 text-xs leading-5 text-ink-faint">
                  <Icon name="alert" className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                  Cada producto tiene un solo responsable. Puede reasignarlo o quitarlo en cualquier momento.
                </p>
              </section>

              <footer className="flex flex-col-reverse gap-3 border-t border-line pt-4 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-xs text-ink-faint">
                  {isUnassign
                    ? 'Se quitará la asignación actual.'
                    : isChange
                      ? 'Se reemplazará el responsable actual.'
                      : assignModal.gestor_lider_id
                        ? 'Sin cambios en la asignación.'
                        : 'Se asignará el producto al gestor seleccionado.'}
                </p>
                <div className="flex justify-end gap-3">
                  <Button variant="ghost" onClick={closeAssign} disabled={assignLoading}>
                    Cancelar
                  </Button>
                  <Button
                    onClick={() => handleAssign(assignModal.id, assignGestorId)}
                    loading={assignLoading}
                    disabled={!isChange && !isUnassign && Boolean(assignModal.gestor_lider_id) === Boolean(assignGestorId)}
                  >
                    {!assignLoading && <Icon name={isUnassign ? 'ban' : 'check'} className="h-4 w-4" />}
                    {isUnassign ? 'Quitar asignación' : isChange ? 'Confirmar reasignación' : 'Guardar asignación'}
                  </Button>
                </div>
              </footer>
            </div>
          </ModalShell>
        )
      })()}
    </div>
  )
}
