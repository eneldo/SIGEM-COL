import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { dashboard } from '../../lib/api'
import type { DashboardKPIs, Alert } from '../../lib/types'

const initialKpis: DashboardKPIs = {
  total_gestores: 0,
  gestores_activos: 0,
  gestores_inactivos: 0,
  gestores_bloqueados: 0,
  total_lineas_estrategicas: 0,
  total_programas: 0,
  total_productos: 0,
  total_dependencias: 0,
}

function DashboardIcon({ type }: { type: 'people' | 'route' | 'folder' | 'box' | 'office' | 'check' | 'arrow' | 'alert' }) {
  const paths = {
    people: 'M18 18.72a9.1 9.1 0 0 0 3.74-.98 4.5 4.5 0 0 0-7.46-3.36m3.72 4.34v.12A12.3 12.3 0 0 1 11.25 21c-2.49 0-4.82-.73-6.75-1.98v-.15a6.75 6.75 0 0 1 12.6-3.39M14.25 6.75a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0Zm6.75 2.1a2.85 2.85 0 1 1-5.7 0 2.85 2.85 0 0 1 5.7 0Z',
    route: 'M3 17.25 9.75 10.5l4.13 4.13A12 12 0 0 1 21 9.75M16.5 6.75H21v4.5',
    folder: 'M3.75 6.75A2.25 2.25 0 0 1 6 4.5h3.38c.6 0 1.17.24 1.59.66l1.12 1.12c.42.42 1 .66 1.59.66H18A2.25 2.25 0 0 1 20.25 9v8.25A2.25 2.25 0 0 1 18 19.5H6a2.25 2.25 0 0 1-2.25-2.25V6.75Z',
    box: 'm4.5 7.5 7.5 4.35 7.5-4.35M12 11.85v8.4m8.25-12.32L12 3.15 3.75 7.93v8.14L12 20.85l8.25-4.78V7.93Z',
    office: 'M4.5 21V5.25A2.25 2.25 0 0 1 6.75 3h7.5a2.25 2.25 0 0 1 2.25 2.25V21m-12 0h15m-11.25-13.5h.01m3.74 0h.01m-3.76 3.75h.01m3.74 0h.01m-3.76 3.75h.01m3.74 0h.01M9.75 21v-3.75h1.5V21',
    check: 'm5.25 12.75 4.5 4.5 9-10.5',
    arrow: 'M5 12h14m-5-5 5 5-5 5',
    alert: 'M12 9v3.75m9.3 3.9L14.04 4.1a2.36 2.36 0 0 0-4.08 0L2.7 16.65A2.36 2.36 0 0 0 4.74 20.2h14.52a2.36 2.36 0 0 0 2.04-3.55ZM12 16.5h.01',
  }

  return (
    <svg aria-hidden="true" className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <path d={paths[type]} />
    </svg>
  )
}

function formatDate() {
  return new Intl.DateTimeFormat('es-CO', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
  }).format(new Date())
}

export function DashboardAdmin() {
  const [kpis, setKpis] = useState(initialKpis)
  const [alertas, setAlertas] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [hasError, setHasError] = useState(false)

  useEffect(() => {
    let active = true
    async function load() {
      const results = await Promise.allSettled([
        dashboard.adminKpis(),
        dashboard.adminAlertas(),
      ])
      if (!active) return

      if (results[0].status === 'fulfilled') setKpis(results[0].value.data)
      else setHasError(true)
      if (results[1].status === 'fulfilled') setAlertas(results[1].value.data.alertas)
      else setHasError(true)
      setLoading(false)
    }
    load()
    return () => { active = false }
  }, [])

  const activeRate = kpis.total_gestores
    ? Math.round((kpis.gestores_activos / kpis.total_gestores) * 100)
    : 0

  const cards = [
    { label: 'Gestores', value: kpis.total_gestores, helper: `${kpis.gestores_activos} activos`, icon: 'people' as const, tone: 'bg-forest-soft text-forest' },
    { label: 'Líneas estratégicas', value: kpis.total_lineas_estrategicas, helper: 'Ejes del plan', icon: 'route' as const, tone: 'bg-ochre-soft text-ochre-deep' },
    { label: 'Programas', value: kpis.total_programas, helper: 'En seguimiento', icon: 'folder' as const, tone: 'bg-[#E9EEF5] text-[#3D5D7A]' },
    { label: 'Productos', value: kpis.total_productos, helper: 'Entregables', icon: 'box' as const, tone: 'bg-[#EEE9F3] text-[#65527A]' },
    { label: 'Dependencias', value: kpis.total_dependencias, helper: 'Áreas vinculadas', icon: 'office' as const, tone: 'bg-warn-soft text-warn' },
  ]

  return (
    <div className="space-y-6 pb-8">
      <section className="relative overflow-hidden rounded-[28px] bg-pine px-6 py-7 text-white shadow-[0_22px_50px_rgba(10,43,41,0.18)] sm:px-8 sm:py-9">
        <div className="absolute -right-20 -top-24 h-72 w-72 rounded-full border border-white/10" aria-hidden="true" />
        <div className="absolute -bottom-28 right-28 h-56 w-56 rounded-full bg-ochre/10 blur-2xl" aria-hidden="true" />
        <div className="relative grid gap-7 lg:grid-cols-[1fr_auto] lg:items-end">
          <div className="max-w-3xl">
            <p className="mb-3 text-xs font-bold uppercase tracking-[0.2em] text-ochre-soft">Centro de control municipal</p>
            <h1 className="text-3xl font-bold leading-tight sm:text-4xl">Dashboard administrativo</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-white/70 sm:text-base">
              Monitoree la estructura del plan de desarrollo, el equipo gestor y las alertas operativas desde un único lugar.
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
          <DashboardIcon type="alert" />
          Algunos indicadores no pudieron actualizarse. Los datos disponibles siguen visibles.
        </div>
      )}

      <section aria-labelledby="resumen-title">
        <div className="mb-3 flex items-end justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-ink-faint">Resumen ejecutivo</p>
            <h2 id="resumen-title" className="mt-1 text-xl font-bold text-ink">Estructura del sistema</h2>
          </div>
          <span className="hidden text-xs text-ink-faint sm:block">Datos del municipio actual</span>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
          {cards.map((card) => (
            <article key={card.label} className="group rounded-2xl border border-line bg-paper-raised p-5 shadow-[0_8px_22px_rgba(38,36,31,0.04)] transition-all hover:-translate-y-0.5 hover:border-pine/25 hover:shadow-[0_14px_30px_rgba(15,61,59,0.08)]">
              <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${card.tone}`}>
                <DashboardIcon type={card.icon} />
              </div>
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
        <section className="overflow-hidden rounded-2xl border border-line bg-paper-raised shadow-sm" aria-labelledby="alertas-title">
          <div className="flex items-center justify-between border-b border-line px-5 py-4 sm:px-6">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-ink-faint">Seguimiento</p>
              <h2 id="alertas-title" className="mt-1 text-xl font-bold text-ink">Alertas recientes</h2>
            </div>
            <span className="rounded-full bg-warn-soft px-3 py-1 text-xs font-bold text-warn">{alertas.length} pendientes</span>
          </div>
          {loading ? (
            <div className="space-y-3 p-6" aria-label="Cargando alertas">
              {[1, 2, 3].map((item) => <div key={item} className="h-16 animate-pulse rounded-xl bg-line/40" />)}
            </div>
          ) : alertas.length ? (
            <ul className="divide-y divide-line">
              {alertas.slice(0, 5).map((alerta, i) => (
                <li key={`${alerta.tipo}-${i}`} className="flex gap-4 px-5 py-4 sm:px-6">
                  <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-warn-soft text-warn"><DashboardIcon type="alert" /></span>
                  <div className="min-w-0">
                    <p className="font-bold text-ink">{alerta.gestor_nombre || 'Alerta de seguridad'}</p>
                    <p className="mt-1 text-sm leading-5 text-ink-soft">{alerta.mensaje}</p>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="flex min-h-56 flex-col items-center justify-center px-6 py-10 text-center">
              <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-forest-soft text-forest"><DashboardIcon type="check" /></span>
              <h3 className="mt-4 text-lg font-bold text-ink">Todo está al día</h3>
              <p className="mt-1 max-w-sm text-sm leading-5 text-ink-faint">No hay alertas pendientes que requieran atención inmediata.</p>
            </div>
          )}
        </section>

        <aside className="space-y-5">
          <section className="rounded-2xl border border-line bg-paper-raised p-5 shadow-sm" aria-labelledby="equipo-title">
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-ink-faint">Equipo gestor</p>
            <h2 id="equipo-title" className="mt-1 text-xl font-bold text-ink">Capacidad operativa</h2>
            <div className="mt-5 flex items-center gap-5">
              <div className="relative flex h-24 w-24 shrink-0 items-center justify-center rounded-full" style={{ background: `conic-gradient(var(--forest) ${activeRate * 3.6}deg, var(--forest-soft) 0deg)` }}>
                <div className="flex h-[74px] w-[74px] flex-col items-center justify-center rounded-full bg-white">
                  <span className="text-2xl font-bold text-pine">{activeRate}%</span>
                  <span className="text-[10px] uppercase tracking-wider text-ink-faint">activos</span>
                </div>
              </div>
              <div className="space-y-2 text-sm">
                <p className="flex items-center gap-2 text-ink-soft"><span className="h-2 w-2 rounded-full bg-forest" />{kpis.gestores_activos} activos</p>
                <p className="flex items-center gap-2 text-ink-soft"><span className="h-2 w-2 rounded-full bg-line" />{kpis.gestores_inactivos} inactivos</p>
                <p className="flex items-center gap-2 text-ink-soft"><span className="h-2 w-2 rounded-full bg-warn" />{kpis.gestores_bloqueados} bloqueados</p>
              </div>
            </div>
            <Link to="/admin/gestores" className="mt-5 flex min-h-11 items-center justify-between rounded-xl bg-pine px-4 text-sm font-bold text-white transition-colors hover:bg-pine-deep">
              Administrar gestores <DashboardIcon type="arrow" />
            </Link>
          </section>

          <section className="rounded-2xl border border-line bg-[#EEE9DC] p-5" aria-labelledby="accesos-title">
            <h2 id="accesos-title" className="text-lg font-bold text-ink">Accesos rápidos</h2>
            <div className="mt-3 grid grid-cols-2 gap-2">
              {[
                ['/admin/lineas', 'Líneas'],
                ['/admin/programas', 'Programas'],
                ['/admin/productos', 'Productos'],
                ['/admin/gestores', 'Gestores'],
              ].map(([to, label]) => (
                <Link key={to} to={to} className="flex min-h-11 items-center justify-between rounded-xl border border-line bg-white/75 px-3 text-sm font-bold text-pine transition-colors hover:border-pine/30 hover:bg-white">
                  {label}<span aria-hidden="true">→</span>
                </Link>
              ))}
            </div>
          </section>
        </aside>
      </div>
    </div>
  )
}
