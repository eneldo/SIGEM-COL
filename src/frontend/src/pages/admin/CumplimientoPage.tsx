import { useEffect, useState } from 'react'
import { cumplimiento } from '../../lib/api'
import type {
  CumplimientoGeneral,
  CumplimientoPorLinea,
  CumplimientoPorPrograma,
  ItemCumplimientoProducto,
} from '../../lib/types'
import {
  MIconCheck,
  MIconWarning,
  MIconInfo,
  MIconTrendingUp,
} from '../../components/Icon'

export default function CumplimientoPage() {
  const [general, setGeneral] = useState<CumplimientoGeneral | null>(null)
  const [porLinea, setPorLinea] = useState<CumplimientoPorLinea[]>([])
  const [porPrograma, setPorPrograma] = useState<CumplimientoPorPrograma[]>([])
  const [productos, setProductos] = useState<ItemCumplimientoProducto[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [tab, setTab] = useState<'general' | 'lineas' | 'programas' | 'productos'>('general')

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [genRes, lineaRes, progRes, prodRes] = await Promise.all([
        cumplimiento.general(),
        cumplimiento.porLinea(),
        cumplimiento.porPrograma(),
        cumplimiento.productos(),
      ])
      setGeneral(genRes.data)
      setPorLinea(lineaRes.data)
      setPorPrograma(progRes.data)
      setProductos(prodRes.data)
    } catch (e) {
      setError('Error al cargar datos de cumplimiento')
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Cargando cumplimiento...</div>
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
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Cumplimiento de Metas</h1>
        <p className="text-sm text-gray-500 mt-1">
          Seguimiento al avance de metas cuatrienales del Plan de Desarrollo
        </p>
      </div>

      {general && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-blue-50 text-blue-600">
              <MIconInfo className="w-5 h-5" />
            </div>
            <p className="text-2xl font-bold text-gray-900 mt-2">{general.total_productos}</p>
            <p className="text-xs text-gray-500">Total Productos</p>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-green-50 text-green-600">
              <MIconCheck className="w-5 h-5" />
            </div>
            <p className="text-2xl font-bold text-green-600 mt-2">{general.completados}</p>
            <p className="text-xs text-gray-500">Completados</p>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-amber-50 text-amber-600">
              <MIconTrendingUp className="w-5 h-5" />
            </div>
            <p className="text-2xl font-bold text-amber-600 mt-2">{general.en_progreso}</p>
            <p className="text-xs text-gray-500">En Progreso</p>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-red-50 text-red-600">
              <MIconWarning className="w-5 h-5" />
            </div>
            <p className="text-2xl font-bold text-red-600 mt-2">{general.sin_avance}</p>
            <p className="text-xs text-gray-500">Sin Avance</p>
          </div>
        </div>
      )}

      {general && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Cumplimiento General</h2>
            <span className="text-2xl font-bold text-blue-600">
              {general.porcentaje_cumplimiento_general}%
            </span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-4">
            <div
              className="h-4 rounded-full bg-gradient-to-r from-blue-500 to-indigo-500"
              style={{ width: `${Math.min(100, general.porcentaje_cumplimiento_general)}%` }}
            />
          </div>
          <div className="flex justify-between mt-2 text-xs text-gray-500">
            <span>{general.con_meta_definida} productos con meta definida</span>
            <span>{general.sin_meta_definida} productos sin meta</span>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg border border-gray-200">
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setTab('general')}
            className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              tab === 'general'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Por Línea
          </button>
          <button
            onClick={() => setTab('lineas')}
            className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              tab === 'lineas'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Por Programa
          </button>
          <button
            onClick={() => setTab('programas')}
            className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              tab === 'programas'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Todos los Productos
          </button>
        </div>

        <div className="p-6">
          {tab === 'general' && (
            <CumplimientoPorLineaTable data={porLinea} />
          )}
          {tab === 'lineas' && (
            <CumplimientoPorProgramaTable data={porPrograma} />
          )}
          {tab === 'programas' && (
            <ProductosTable data={productos} />
          )}
        </div>
      </div>
    </div>
  )
}

function CumplimientoPorLineaTable({ data }: { data: CumplimientoPorLinea[] }) {
  if (data.length === 0) {
    return <p className="text-sm text-gray-400">No hay datos disponibles</p>
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="text-left py-2 font-medium text-gray-600">Código</th>
            <th className="text-left py-2 font-medium text-gray-600">Línea Estratégica</th>
            <th className="text-center py-2 font-medium text-gray-600">Productos</th>
            <th className="text-center py-2 font-medium text-gray-600">Completados</th>
            <th className="text-center py-2 font-medium text-gray-600">En Progreso</th>
            <th className="text-center py-2 font-medium text-gray-600">Sin Avance</th>
            <th className="text-center py-2 font-medium text-gray-600">Avance</th>
          </tr>
        </thead>
        <tbody>
          {data.map((item) => (
            <tr key={item.id} className="border-b border-gray-50">
              <td className="py-3 font-mono text-gray-500">{item.codigo}</td>
              <td className="py-3 text-gray-900">{item.nombre}</td>
              <td className="py-3 text-center">{item.total_productos}</td>
              <td className="py-3 text-center">
                <span className="text-green-600 font-medium">{item.completados}</span>
              </td>
              <td className="py-3 text-center">
                <span className="text-amber-600 font-medium">{item.en_progreso}</span>
              </td>
              <td className="py-3 text-center">
                <span className="text-red-600 font-medium">{item.sin_avance}</span>
              </td>
              <td className="py-3">
                <div className="flex items-center gap-2">
                  <div className="w-20 bg-gray-100 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        item.porcentaje_cumplimiento >= 100
                          ? 'bg-green-500'
                          : item.porcentaje_cumplimiento > 0
                          ? 'bg-amber-500'
                          : 'bg-red-500'
                      }`}
                      style={{ width: `${Math.min(100, item.porcentaje_cumplimiento)}%` }}
                    />
                  </div>
                  <span className="text-xs font-medium text-gray-700 w-10 text-right">
                    {item.porcentaje_cumplimiento}%
                  </span>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function CumplimientoPorProgramaTable({ data }: { data: CumplimientoPorPrograma[] }) {
  if (data.length === 0) {
    return <p className="text-sm text-gray-400">No hay datos disponibles</p>
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="text-left py-2 font-medium text-gray-600">Código</th>
            <th className="text-left py-2 font-medium text-gray-600">Programa</th>
            <th className="text-left py-2 font-medium text-gray-600">Línea</th>
            <th className="text-center py-2 font-medium text-gray-600">Productos</th>
            <th className="text-center py-2 font-medium text-gray-600">Completados</th>
            <th className="text-center py-2 font-medium text-gray-600">En Progreso</th>
            <th className="text-center py-2 font-medium text-gray-600">Sin Avance</th>
            <th className="text-center py-2 font-medium text-gray-600">Avance</th>
          </tr>
        </thead>
        <tbody>
          {data.map((item) => (
            <tr key={item.id} className="border-b border-gray-50">
              <td className="py-3 font-mono text-gray-500">{item.codigo}</td>
              <td className="py-3 text-gray-900">{item.nombre}</td>
              <td className="py-3 text-gray-500 text-xs">{item.linea_nombre}</td>
              <td className="py-3 text-center">{item.total_productos}</td>
              <td className="py-3 text-center">
                <span className="text-green-600 font-medium">{item.completados}</span>
              </td>
              <td className="py-3 text-center">
                <span className="text-amber-600 font-medium">{item.en_progreso}</span>
              </td>
              <td className="py-3 text-center">
                <span className="text-red-600 font-medium">{item.sin_avance}</span>
              </td>
              <td className="py-3">
                <div className="flex items-center gap-2">
                  <div className="w-20 bg-gray-100 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        item.porcentaje_cumplimiento >= 100
                          ? 'bg-green-500'
                          : item.porcentaje_cumplimiento > 0
                          ? 'bg-amber-500'
                          : 'bg-red-500'
                      }`}
                      style={{ width: `${Math.min(100, item.porcentaje_cumplimiento)}%` }}
                    />
                  </div>
                  <span className="text-xs font-medium text-gray-700 w-10 text-right">
                    {item.porcentaje_cumplimiento}%
                  </span>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function ProductosTable({ data }: { data: ItemCumplimientoProducto[] }) {
  const [filtro, setFiltro] = useState<string>('TODOS')

  const filtered = data.filter((p) => {
    if (filtro === 'TODOS') return true
    return p.estado_cumplimiento === filtro
  })

  const estadoBadge = (estado: string) => {
    const styles: Record<string, string> = {
      COMPLETADO: 'bg-green-50 text-green-700',
      EN_PROGRESO: 'bg-amber-50 text-amber-700',
      SIN_AVANCE: 'bg-red-50 text-red-700',
      SIN_META: 'bg-gray-100 text-gray-500',
    }
    const labels: Record<string, string> = {
      COMPLETADO: 'Completado',
      EN_PROGRESO: 'En Progreso',
      SIN_AVANCE: 'Sin Avance',
      SIN_META: 'Sin Meta',
    }
    return (
      <span className={`text-xs px-2 py-0.5 rounded-full ${styles[estado] || styles.SIN_META}`}>
        {labels[estado] || estado}
      </span>
    )
  }

  return (
    <div>
      <div className="flex gap-2 mb-4">
        {['TODOS', 'COMPLETADO', 'EN_PROGRESO', 'SIN_AVANCE', 'SIN_META'].map((f) => (
          <button
            key={f}
            onClick={() => setFiltro(f)}
            className={`px-3 py-1.5 text-xs rounded-lg border transition-colors ${
              filtro === f
                ? 'bg-blue-50 border-blue-200 text-blue-700'
                : 'border-gray-200 text-gray-600 hover:bg-gray-50'
            }`}
          >
            {f === 'TODOS'
              ? 'Todos'
              : f === 'COMPLETADO'
              ? 'Completados'
              : f === 'EN_PROGRESO'
              ? 'En Progreso'
              : f === 'SIN_AVANCE'
              ? 'Sin Avance'
              : 'Sin Meta'}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <p className="text-sm text-gray-400">No hay productos con este filtro</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-2 font-medium text-gray-600">Código</th>
                <th className="text-left py-2 font-medium text-gray-600">Producto</th>
                <th className="text-left py-2 font-medium text-gray-600">Indicador</th>
                <th className="text-center py-2 font-medium text-gray-600">Línea Base</th>
                <th className="text-center py-2 font-medium text-gray-600">Meta</th>
                <th className="text-center py-2 font-medium text-gray-600">Avance</th>
                <th className="text-center py-2 font-medium text-gray-600">Estado</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((p) => (
                <tr key={p.id} className="border-b border-gray-50">
                  <td className="py-3 font-mono text-gray-500">{p.codigo}</td>
                  <td className="py-3">
                    <p className="text-gray-900">{p.nombre}</p>
                    <p className="text-xs text-gray-400">{p.programa_nombre}</p>
                  </td>
                  <td className="py-3 text-gray-600 text-xs max-w-48 truncate">
                    {p.indicador || '-'}
                  </td>
                  <td className="py-3 text-center">{p.linea_base ?? '-'}</td>
                  <td className="py-3 text-center">{p.meta_cuatrienio ?? '-'}</td>
                  <td className="py-3">
                    <div className="flex items-center gap-2 justify-center">
                      <div className="w-16 bg-gray-100 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${
                            p.porcentaje_avance >= 100
                              ? 'bg-green-500'
                              : p.porcentaje_avance > 0
                              ? 'bg-amber-500'
                              : 'bg-red-500'
                          }`}
                          style={{ width: `${Math.min(100, p.porcentaje_avance)}%` }}
                        />
                      </div>
                      <span className="text-xs font-medium w-10 text-right">
                        {p.porcentaje_avance}%
                      </span>
                    </div>
                  </td>
                  <td className="py-3 text-center">{estadoBadge(p.estado_cumplimiento)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
