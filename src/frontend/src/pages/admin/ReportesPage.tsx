import { useEffect, useState } from 'react'
import { saveAs } from 'file-saver'
import { reportes } from '../../lib/api'
import type {
  ResumenGeneral,
  ResumenPorLinea,
  ResumenPorPrograma,
  ResumenPorDependencia,
  MetricasProductos,
} from '../../lib/types'
import {
  MIconTrendingUp,
  MIconCheck,
  MIconWarning,
  MIconUser,
  MIconSchool,
  MIconInfo,
} from '../../components/Icon'

export default function ReportesPage() {
  const [resumen, setResumen] = useState<ResumenGeneral | null>(null)
  const [lineas, setLineas] = useState<ResumenPorLinea[]>([])
  const [programas, setProgramas] = useState<ResumenPorPrograma[]>([])
  const [dependencias, setDependencias] = useState<ResumenPorDependencia[]>([])
  const [metricas, setMetricas] = useState<MetricasProductos | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [downloadingPdf, setDownloadingPdf] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [resumenRes, lineasRes, programasRes, depsRes, metricasRes] =
        await Promise.all([
          reportes.resumenGeneral(),
          reportes.porLinea(),
          reportes.porPrograma(),
          reportes.porDependencia(),
          reportes.metricasProductos(),
        ])
      setResumen(resumenRes.data)
      setLineas(lineasRes.data)
      setProgramas(programasRes.data)
      setDependencias(depsRes.data)
      setMetricas(metricasRes.data)
    } catch (e) {
      setError('Error al cargar datos de reportes')
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const downloadPdf = async () => {
    setDownloadingPdf(true)
    try {
      const authData = JSON.parse(localStorage.getItem('sigem-auth') || '{}')
      const token = authData?.state?.token
      if (!token) {
        setError('No hay sesión activa')
        return
      }
      const response = await fetch('http://localhost:8002/api/v1/reportes/informe-pdf', {
        headers: { 'Authorization': `Bearer ${token}` },
      })
      if (!response.ok) throw new Error('Error al descargar')
      const blob = await response.blob()
      saveAs(blob, 'informe_gestion_sigem.pdf')
    } catch (e) {
      console.error('Error downloading PDF:', e)
      setError('Error al descargar el PDF')
    } finally {
      setDownloadingPdf(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Cargando reportes...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700 text-sm">{error}</p>
          <button onClick={loadData} className="mt-2 text-sm text-red-600 underline">
            Reintentar
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Reportes y Rendición de Cuentas
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Resumen ejecutivo del Plan de Desarrollo Municipal
          </p>
        </div>
        <button
          onClick={downloadPdf}
          disabled={downloadingPdf}
          className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          {downloadingPdf ? 'Generando...' : 'Descargar PDF'}
        </button>
      </div>

      {resumen && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <KpiCard
            icon={<MIconTrendingUp className="w-5 h-5" />}
            label="Líneas"
            value={resumen.total_lineas}
            color="blue"
          />
          <KpiCard
            icon={<MIconSchool className="w-5 h-5" />}
            label="Programas"
            value={resumen.total_programas}
            color="indigo"
          />
          <KpiCard
            icon={<MIconInfo className="w-5 h-5" />}
            label="Productos"
            value={resumen.total_productos}
            color="purple"
          />
          <KpiCard
            icon={<MIconCheck className="w-5 h-5" />}
            label="Activos"
            value={resumen.productos_activos}
            color="green"
          />
          <KpiCard
            icon={<MIconWarning className="w-5 h-5" />}
            label="Inactivos"
            value={resumen.productos_inactivos}
            color="amber"
          />
          <KpiCard
            icon={<MIconUser className="w-5 h-5" />}
            label="Gestores"
            value={resumen.total_gestores}
            color="teal"
          />
        </div>
      )}

      {metricas && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Calidad de la Información
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricBar
              label="Con Indicador"
              value={metricas.con_indicador}
              total={metricas.total_productos}
              percentage={metricas.porcentaje_cumplimiento_indicador}
              color="green"
            />
            <MetricBar
              label="Con Meta Cuatrienio"
              value={metricas.con_meta_cuatrienio}
              total={metricas.total_productos}
              percentage={metricas.porcentaje_cumplimiento_meta}
              color="blue"
            />
            <MetricBar
              label="Con Gestor"
              value={metricas.con_gestor_asignado}
              total={metricas.total_productos}
              percentage={
                metricas.total_productos > 0
                  ? Math.round((metricas.con_gestor_asignado / metricas.total_productos) * 100)
                  : 0
              }
              color="indigo"
            />
            <MetricBar
              label="Prom. Avance"
              value={metricas.promedio_avance}
              total={100}
              percentage={metricas.promedio_avance}
              color="purple"
              suffix="%"
            />
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Resumen por Línea Estratégica
          </h2>
          {lineas.length === 0 ? (
            <p className="text-sm text-gray-400">No hay líneas registradas</p>
          ) : (
            <div className="space-y-3">
              {lineas.map((l) => (
                <div key={l.id} className="border border-gray-100 rounded-lg p-3">
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="text-xs font-mono text-gray-500">{l.codigo}</span>
                      <p className="text-sm font-medium text-gray-900">{l.nombre}</p>
                    </div>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full ${
                        l.estado === 'ACTIVA'
                          ? 'bg-green-50 text-green-700'
                          : 'bg-gray-100 text-gray-500'
                      }`}
                    >
                      {l.estado}
                    </span>
                  </div>
                  <div className="flex gap-4 mt-2 text-xs text-gray-500">
                    <span>{l.total_programas} programas</span>
                    <span>{l.total_productos} productos</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Resumen por Programa
          </h2>
          {programas.length === 0 ? (
            <p className="text-sm text-gray-400">No hay programas registrados</p>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {programas.map((p) => (
                <div key={p.id} className="border border-gray-100 rounded-lg p-3">
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="text-xs font-mono text-gray-500">{p.codigo}</span>
                      <p className="text-sm font-medium text-gray-900">{p.nombre}</p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        Línea: {p.linea_nombre}
                        {p.sector && ` · Sector: ${p.sector}`}
                      </p>
                    </div>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full ${
                        p.estado === 'ACTIVO'
                          ? 'bg-green-50 text-green-700'
                          : 'bg-gray-100 text-gray-500'
                      }`}
                    >
                      {p.estado}
                    </span>
                  </div>
                  <div className="flex gap-4 mt-2 text-xs text-gray-500">
                    <span>{p.total_productos} productos</span>
                    <span>{p.productos_activos} activos</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {dependencias.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Resumen por Dependencia
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 font-medium text-gray-600">Código</th>
                  <th className="text-left py-2 font-medium text-gray-600">Nombre</th>
                  <th className="text-center py-2 font-medium text-gray-600">Productos</th>
                  <th className="text-center py-2 font-medium text-gray-600">Gestores</th>
                </tr>
              </thead>
              <tbody>
                {dependencias.map((d) => (
                  <tr key={d.id} className="border-b border-gray-50">
                    <td className="py-2 font-mono text-gray-500">{d.codigo}</td>
                    <td className="py-2 text-gray-900">{d.nombre}</td>
                    <td className="py-2 text-center">{d.total_productos}</td>
                    <td className="py-2 text-center">{d.total_gestores}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

function KpiCard({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode
  label: string
  value: number
  color: string
}) {
  const colors: Record<string, string> = {
    blue: 'bg-blue-50 text-blue-600',
    indigo: 'bg-indigo-50 text-indigo-600',
    purple: 'bg-purple-50 text-purple-600',
    green: 'bg-green-50 text-green-600',
    amber: 'bg-amber-50 text-amber-600',
    teal: 'bg-teal-50 text-teal-600',
  }
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${colors[color]}`}>
        {icon}
      </div>
      <p className="text-2xl font-bold text-gray-900 mt-2">{value}</p>
      <p className="text-xs text-gray-500">{label}</p>
    </div>
  )
}

function MetricBar({
  label,
  value,
  total,
  percentage,
  color,
  suffix,
}: {
  label: string
  value: number
  total: number
  percentage: number
  color: string
  suffix?: string
}) {
  const barColors: Record<string, string> = {
    green: 'bg-green-500',
    blue: 'bg-blue-500',
    indigo: 'bg-indigo-500',
    purple: 'bg-purple-500',
  }
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-gray-600">{label}</span>
        <span className="font-medium text-gray-900">
          {suffix ? `${value}${suffix}` : `${value}/${total}`}
        </span>
      </div>
      <div className="w-full bg-gray-100 rounded-full h-2">
        <div
          className={`h-2 rounded-full ${barColors[color]}`}
          style={{ width: `${Math.min(100, percentage)}%` }}
        />
      </div>
      <p className="text-xs text-gray-400 mt-0.5">{percentage}%</p>
    </div>
  )
}
