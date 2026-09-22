import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { dashboard } from '../../lib/api'
import { useAuthStore } from '../../stores/authStore'
import type { GestorAlert, GestorKpis, GestorPendienteItem, GestorProductoItem } from '../../lib/types'
import { EstadoBadge, Icon, formatDateOnly } from '../../components/ui/icons'

const emptyKpis: GestorKpis = { total_productos_asignados: 0, total_dependencias_asignadas: 0, total_lineas_estrategicas: 0 }

const severidadTone: Record<string, string> = {
  CRITICA: 'bg-warn-soft text-warn',
  ALTA: 'bg-warn-soft text-warn',
  MEDIA: 'bg-ochre-soft text-ochre-deep',
  BAJA: 'bg-line/60 text-ink-soft',
}

function formatDate() {
  return new Intl.DateTimeFormat('es-CO', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
  }).format(new Date())
}

export function DashboardGestor() {
  const user = useAuthStore((s) => s.user)
  const [kpis, setKpis] = useState<GestorKpis>(emptyKpis)
  const [productos, setProductos] = useState<GestorProductoItem[]>([])
  const [pendientes, setPendientes] = useState<GestorPendienteItem[]>([])
  const [alertas, setAlertas] = useState<GestorAlert[]>([])
  const [loading, setLoading] = useState(true)
  const [hasError, setHasError] = useState(false)

  useEffect(() => {
    let active = true
    async function load() {
      const results = await Promise.allSettled([
        dashboard.gestorKpis(),
        dashboard.gestorMisProductos(),
        dashboard.gestorMisPendientes(),
        dashboard.gestorMisAlertas(),
      ])
      if (!active) return

      if (results[0].status === 'fulfilled') setKpis(results[0].value.data)
      else setHasError(true)
      if (results[1].status === 'fulfilled') setProductos(results[1].value.data.productos)
      else setHasError(true)
      if (results[2].status === 'fulfilled') setPendientes(results[2].value.data.pendientes)
      else setHasError(true)
      if (results[3].status === 'fulfilled') setAlertas(results[3].value.data.alertas)
      else setHasError(true)
      setLoading(false)
    }
    load()
    return () => { active = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const cards = [
    { label: 'Productos asignados', value: kpis.total_productos_asignados, helper: 'Entregables a cargo', icon: 'box' as const, tone: 'bg-forest-soft text-forest' },
    { label: 'Dependencias', value: kpis.total_dependencias_asignadas, helper: 'Áreas vinculadas', icon: 'building' as const, tone: 'bg-ochre-soft text-ochre-deep' },
    { label: 'Líneas estratégicas', value: kpis.total_lineas_estrategicas, helper: 'Ejes del plan', icon: 'layers' as const, tone: 'bg-[#E9EEF5] text-[#3D5D7A]' },
  ]

  return (
    <div className="space-y-6 pb-8">
      <section className="relative overflow-hidden rounded-[28px] bg-pine px-6 py-7 text-white shadow-[0_22px_50px_rgba(10,43,41,0.18)] sm:px-8 sm:py-9">
        <div className="absolute -right-20 -top-24 h-72 w-72 rounded-full border border-white/10" aria-hidden="true" />
        <div className="absolute -bottom-28 right-28 h-56 w-56 rounded-full bg-ochre/10 blur-2xl" aria-hidden="true" />
        <div className="relative grid gap-7 lg:grid-cols-[1fr_auto] lg:items-end">
          <div className="max-w-3xl">
            <p className="mb-3 text-xs font-bold uppercase tracking-[0.2em] text-ochre-soft">Panel del gestor líder</p>
            <h1 className="text-3xl font-bold leading-tight sm:text-4xl">Hola, {user?.nombre_completo || 'gestor'}</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-white/70 sm:text-base">
              Consulte sus productos asignados, priorice los pendientes de actualización y revise sus alertas de seguridad.
            </p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/10 px-5 py-4 backdrop-blur-sm">
            <p className="text-xs font-bold uppercase tracking-wider text-white/55">Fecha de corte</p>
            <p className="mt-1 capitalize text-sm font-bold text-white">{formatDate()}</p>
            <div className="mt-3 flex items-center gap-2 text-xs text-white/65">
              <span className="h-2 w-2 rounded-full bg-[#7DD3A7] ring-4 ring-[#7DD3A7]/10" />
              Información actualizada
            </div>
          </div>
        </div>
      </section>

      {hasError && (
        <div role="status" className="flex items-start gap-3 rounded-2xl border border-ochre/30 bg-ochre-soft/60 px-4 py-3 text-sm text-ochre-deep">
          <Icon name="alert" />
          Algunos indicadores no pudieron actualizarse. Los datos disponibles siguen visibles.
        </div>
      )}

      <section aria-labelledby="resumen-title">
        <div className="mb-3 flex items-end justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-ink-faint">Resumen personal</p>
            <h2 id="resumen-title" className="mt-1 text-xl font-bold text-ink">Mi gestión</h2>
          </div>
          <span className="hidden text-xs text-ink-faint sm:block">Del municipio actual</span>
        </div>
        <div className="grid gap-3 sm:grid-cols-3">
          {cards.map((card) => (
            <article key={card.label} className="group rounded-2xl border border-line bg-paper-raised p-5 shadow-[0_8px_22px_rgba(38,36,31,0.04)] transition-all hover:-translate-y-0.5 hover:border-pine/25 hover:shadow-[0_14px_30px_rgba(15,61,59,0.08)]">
              <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${card.tone}`}><Icon name={card.icon} className="h-5 w-5" /></div>
              <p className="mt-5 text-xs font-bold uppercase tracking-wider text-ink-faint">{card.label}</p>
              <div className="mt-1 flex items-end justify-between gap-3">
                <p className="text-3xl font-bold tabular-nums text-pine">{loading ? '—' : card.value}</p>
                <p className="pb-1 text-xs text-ink-faint">{card.helper}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.55fr)_minmax(320px,.85fr)]">
        <section className="overflow-hidden rounded-2xl border border-line bg-paper-raised shadow-sm" aria-labelledby="productos-title">
          <div className="flex items-center justify-between border-b border-line px-5 py-4 sm:px-6">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-ink-faint">Productos</p>
              <h2 id="productos-title" className="mt-1 text-xl font-bold text-ink">Mis productos asignados</h2>
            </div>
            <Link to="/gestor/productos" className="hidden items-center gap-2 rounded-xl bg-pine px-4 py-2 text-sm font-bold text-white transition-colors hover:bg-pine-deep sm:inline-flex">
              Ver todos <Icon name="layers" />
            </Link>
          </div>
          {loading ? (
            <div className="space-y-3 p-6" aria-label="Cargando productos">
              {[1, 2, 3].map((item) => <div key={item} className="h-16 animate-pulse rounded-xl bg-line/40" />)}
            </div>
          ) : productos.length ? (
            <ul className="divide-y divide-line">
              {productos.slice(0, 5).map((p) => (
                <li key={p.id} className="flex items-center gap-4 px-5 py-4 sm:px-6">
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-forest-soft font-bold text-forest"><Icon name="box" /></span>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2"><span className="font-mono text-xs font-bold text-pine">{p.codigo}</span><EstadoBadge estado={p.estado} /></div>
                    <p className="mt-0.5 truncate font-bold text-ink">{p.nombre}</p>
                    <p className="mt-0.5 truncate text-xs text-ink-faint">{p.programa.nombre}{p.dependencia_responsable ? ` · ${p.dependencia_responsable.nombre}` : ''}</p>
                  </div>
                  <p className="hidden shrink-0 text-xs text-ink-faint sm:block">Actualizado {formatDateOnly(p.updated_at)}</p>
                </li>
              ))}
            </ul>
          ) : (
            <div className="flex min-h-56 flex-col items-center justify-center px-6 py-10 text-center">
              <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-paper text-ink-faint"><Icon name="box" className="h-6 w-6" /></span>
              <h3 className="mt-4 text-lg font-bold text-ink">Sin productos asignados</h3>
              <p className="mt-1 max-w-sm text-sm leading-5 text-ink-faint">Cuando le asignen productos aparecerán aquí.</p>
            </div>
          )}
        </section>

        <aside className="space-y-5">
          <section className="overflow-hidden rounded-2xl border border-line bg-paper-raised shadow-sm" aria-labelledby="pendientes-title">
            <div className="flex items-center justify-between border-b border-line px-5 py-4">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.16em] text-ink-faint">Prioridad</p>
                <h2 id="pendientes-title" className="mt-1 text-lg font-bold text-ink">Pendientes de actualización</h2>
              </div>
              <span className="rounded-full bg-ochre-soft px-3 py-1 text-xs font-bold text-ochre-deep">{pendientes.length}</span>
            </div>
            {loading ? (
              <div className="space-y-3 p-5">{[1, 2].map((i) => <div key={i} className="h-14 animate-pulse rounded-xl bg-line/40" />)}</div>
            ) : pendientes.length ? (
              <ul className="divide-y divide-line">
                {pendientes.slice(0, 4).map((p) => (
                  <li key={p.id} className="flex items-center gap-3 px-5 py-3.5">
                    <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-ochre-soft text-ochre-deep"><Icon name="calendar" /></span>
                    <div className="min-w-0 flex-1"><p className="truncate text-sm font-bold text-ink">{p.nombre}</p><p className="mt-0.5 text-xs text-ink-faint">{p.programa.nombre}</p></div>
                    <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-bold ${p.dias_sin_actualizacion === null ? 'bg-line/60 text-ink-soft' : (p.dias_sin_actualizacion ?? 0) > 30 ? 'bg-warn-soft text-warn' : 'bg-ochre-soft text-ochre-deep'}`}>{p.dias_sin_actualizacion === null ? 'Sin registro' : `${p.dias_sin_actualizacion} días`}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="flex min-h-40 flex-col items-center justify-center px-6 py-8 text-center">
                <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-forest-soft text-forest"><Icon name="check" /></span>
                <h3 className="mt-3 text-base font-bold text-ink">Al día</h3>
                <p className="mt-1 text-sm text-ink-faint">Sus productos están al día.</p>
              </div>
            )}
          </section>

          <section className="rounded-2xl border border-line bg-paper-raised p-5 shadow-sm" aria-labelledby="alertas-title">
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-ink-faint">Seguridad</p>
            <h2 id="alertas-title" className="mt-1 text-lg font-bold text-ink">Alertas personales</h2>
            <ul className="mt-4 space-y-3">
              {loading ? <li className="h-12 animate-pulse rounded-xl bg-line/40" /> : alertas.length ? alertas.map((a, i) => (
                <li key={`${a.tipo}-${i}`} className="rounded-xl border border-line p-3">
                  <span className={`inline-flex rounded-full px-2.5 py-0.5 text-[11px] font-bold ${severidadTone[a.severidad] || 'bg-line/60 text-ink-soft'}`}>{a.severidad}</span>
                  <p className="mt-2 text-sm leading-5 text-ink-soft">{a.mensaje}</p>
                  {a.motivo_bloqueo && <p className="mt-1 text-xs font-bold text-warn">Motivo: {a.motivo_bloqueo}</p>}
                </li>
              )) : (
                <li className="flex items-center gap-3 rounded-xl bg-forest-soft/60 p-3 text-sm font-bold text-forest"><span className="flex h-8 w-8 items-center justify-center rounded-full bg-white"><Icon name="check" /></span>Sin alertas de seguridad.</li>
              )}
            </ul>
          </section>
        </aside>
      </div>

      <div className="rounded-2xl border border-line bg-paper-raised p-5 shadow-sm sm:hidden">
        <Link to="/gestor/productos" className="flex min-h-11 items-center justify-between rounded-xl bg-pine px-4 text-sm font-bold text-white">
          Ver todos mis productos <Icon name="layers" />
        </Link>
      </div>
    </div>
  )
}