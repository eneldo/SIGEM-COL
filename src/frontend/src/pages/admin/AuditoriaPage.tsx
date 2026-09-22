import { useCallback, useEffect, useState } from 'react'
import { configAuditoria } from '../../lib/api'
import type { AuditoriaEvento, AuditoriaStats } from '../../lib/types'
import { selectClass } from '../../components/ui/icons'

export function AuditoriaPage() {
  const [items, setItems] = useState<AuditoriaEvento[]>([])
  const [stats, setStats] = useState<AuditoriaStats | null>(null)
  const [eventoTipo, setEventoTipo] = useState('')
  const [recursoTipo, setRecursoTipo] = useState('')
  const [resultado, setResultado] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadStats = useCallback(async () => {
    try {
      const resp = await configAuditoria.stats()
      setStats(resp.data)
    } catch { /* silent */ }
  }, [])

  useEffect(() => { loadStats() }, [loadStats])

  async function load() {
    setLoading(true); setError('')
    try {
      const params: Record<string, unknown> = { page: 1, page_size: 50 }
      if (eventoTipo) params.evento_tipo = eventoTipo
      if (recursoTipo) params.recurso_tipo = recursoTipo
      if (resultado) params.resultado = resultado
      setItems((await configAuditoria.list(params)).data.items)
    } catch { setError('No fue posible cargar los eventos de auditoría.') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [eventoTipo, recursoTipo, resultado])

  function getResultadoBadge(r: string) {
    if (r === 'EXITOSO') return 'bg-done-soft text-done'
    if (r === 'FALLIDO') return 'bg-warn-soft text-warn'
    return 'bg-ink-faint/10 text-ink-faint'
  }

  function getTipoLabel(t: string) {
    const map: Record<string, string> = {
      'LOGIN': 'Inicio de sesión',
      'LOGOUT': 'Cierre de sesión',
      'CREATE': 'Creación',
      'UPDATE': 'Actualización',
      'DELETE': 'Eliminación',
      'PASSWORD_CHANGE': 'Cambio de contraseña',
      'PASSWORD_RESET': 'Restablecimiento',
      'ACTIVATE': 'Activación',
      'DEACTIVATE': 'Desactivación',
      'BLOCK': 'Bloqueo',
      'UNBLOCK': 'Desbloqueo',
    }
    return map[t] || t
  }

  return <div className="space-y-6 pb-8">
    <section className="flex flex-col gap-5 rounded-[28px] bg-pine px-6 py-7 text-white shadow-[0_18px_40px_rgba(10,43,41,.16)] sm:flex-row sm:items-end sm:justify-between sm:px-8">
      <div><p className="text-xs font-bold uppercase tracking-[.2em] text-ochre-soft">Configuración</p><h1 className="mt-2 text-3xl font-bold">Auditoría del sistema</h1><p className="mt-2 max-w-2xl text-sm text-white/70">Consulte el registro de todos los eventos realizados en el sistema por los usuarios.</p></div>
    </section>

    {stats && <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {[['Total de eventos', stats.total_eventos, 'text-pine'], ['Exitosos', stats.exitosos, 'text-forest'], ['Fallidos', stats.fallidos, 'text-warn'], ['Hoy', stats.hoy, 'text-ochre-deep']].map(([label, value, tone]) => <div key={label} className="rounded-2xl border border-line bg-white p-4 shadow-sm"><p className="text-xs font-bold uppercase tracking-wider text-ink-faint">{label}</p><p className={`mt-2 text-3xl font-bold ${tone}`}>{value}</p></div>)}
    </div>}

    {stats && Object.keys(stats.por_tipo).length > 0 && <div className="rounded-2xl border border-line bg-white p-5 shadow-sm">
      <p className="text-xs font-bold uppercase tracking-wider text-ink-faint mb-3">Eventos por tipo</p>
      <div className="flex flex-wrap gap-2">
        {Object.entries(stats.por_tipo).map(([tipo, count]) => <div key={tipo} className="rounded-xl bg-forest-soft px-3 py-2 text-center">
          <p className="text-lg font-bold text-forest">{count}</p>
          <p className="text-xs text-ink-faint">{getTipoLabel(tipo)}</p>
        </div>)}
      </div>
    </div>}

    {error && <div role="alert" className="rounded-xl border border-warn/30 bg-warn-soft px-4 py-3 text-sm text-warn">{error}</div>}

    <section className="overflow-visible rounded-2xl border border-line bg-white shadow-sm">
      <div className="flex flex-col gap-3 border-b border-line p-4 lg:flex-row lg:items-center">
        <select aria-label="Filtrar por tipo de evento" className={`${selectClass} lg:w-48`} value={eventoTipo} onChange={(e) => setEventoTipo(e.target.value)}><option value="">Todos los eventos</option><option value="LOGIN">Inicio de sesión</option><option value="LOGOUT">Cierre de sesión</option><option value="CREATE">Creación</option><option value="UPDATE">Actualización</option><option value="DELETE">Eliminación</option><option value="PASSWORD_CHANGE">Cambio de contraseña</option><option value="ACTIVATE">Activación</option><option value="DEACTIVATE">Desactivación</option><option value="BLOCK">Bloqueo</option><option value="UNBLOCK">Desbloqueo</option></select>
        <select aria-label="Filtrar por recurso" className={`${selectClass} lg:w-40`} value={recursoTipo} onChange={(e) => setRecursoTipo(e.target.value)}><option value="">Todos los recursos</option><option value="USUARIO">Usuarios</option><option value="GESTOR">Gestores</option><option value="ROL">Roles</option><option value="LINEA">Líneas</option><option value="PROGRAMA">Programas</option><option value="PRODUCTO">Productos</option></select>
        <select aria-label="Filtrar por resultado" className={`${selectClass} lg:w-36`} value={resultado} onChange={(e) => setResultado(e.target.value)}><option value="">Todos</option><option value="EXITOSO">Exitosos</option><option value="FALLIDO">Fallidos</option></select>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[900px] text-left text-sm">
          <thead className="bg-paper/70 text-xs uppercase tracking-wider text-ink-faint"><tr><th className="px-5 py-3">Fecha</th><th className="px-4 py-3">Evento</th><th className="px-4 py-3">Recurso</th><th className="px-4 py-3">Actor</th><th className="px-4 py-3">Resultado</th><th className="hidden lg:table-cell px-4 py-3">IP</th></tr></thead>
          <tbody className="divide-y divide-line">
            {loading ? <tr><td colSpan={6} className="px-5 py-16 text-center text-ink-faint">Cargando eventos...</td></tr> : items.length === 0 ? <tr><td colSpan={6} className="px-5 py-16 text-center text-ink-faint">No hay eventos que coincidan con los filtros.</td></tr> : items.map((e) => <tr key={e.id} className="hover:bg-paper/45">
              <td className="px-5 py-4 text-xs text-ink-faint whitespace-nowrap">{new Date(e.fecha_evento).toLocaleString('es-CO')}</td>
              <td className="px-4 py-4"><span className="rounded-lg bg-forest-soft px-2.5 py-1 text-xs font-bold text-forest">{getTipoLabel(e.evento_tipo)}</span></td>
              <td className="px-4 py-4 text-xs text-ink-soft">{e.recurso_tipo || '-'}</td>
              <td className="px-4 py-4 text-xs text-ink-soft">{e.actor_nombre || 'Sistema'}</td>
              <td className="px-4 py-4"><span className={`rounded-lg px-2.5 py-1 text-xs font-bold ${getResultadoBadge(e.resultado)}`}>{e.resultado}</span></td>
              <td className="hidden lg:table-cell px-4 py-4 text-xs text-ink-faint">{e.ip_address || '-'}</td>
            </tr>)}
          </tbody>
        </table>
      </div>
    </section>
  </div>
}
