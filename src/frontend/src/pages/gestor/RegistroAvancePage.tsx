import { useEffect, useState, useRef } from 'react'
import { useAuthStore } from '../../stores/authStore'
import { gestorDashboard } from '../../lib/api'
import { Icon } from '../../components/ui/icons'
import { clsx } from 'clsx'

interface ProductoOption {
  id: string
  codigo: string
  nombre: string
  indicador: string | null
  codigo_indicador: string | null
  meta_redactada: string | null
  unidad_medida: string | null
}

const PERIODOS = [
  'Enero - Marzo 2026',
  'Abril - Junio 2026',
  'Julio - Septiembre 2026',
  'Octubre - Diciembre 2026',
  'Semestre 1 2026',
  'Semestre 2 2026',
  'Anual 2026',
]

export default function RegistroAvancePage() {
  const user = useAuthStore((s) => s.user)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [productos, setProductos] = useState<ProductoOption[]>([])
  const [saving, setSaving] = useState(false)
  const [success, setSuccess] = useState('')
  const [error, setError] = useState('')

  const [productoId, setProductoId] = useState('')
  const [indicador, setIndicador] = useState('')
  const [periodo, setPeriodo] = useState('')
  const [avanceValor, setAvanceValor] = useState('')
  const [porcentaje, setPorcentaje] = useState('')
  const [archivo, setArchivo] = useState<File | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const [estadoRevision, setEstadoRevision] = useState('PENDIENTE')

  useEffect(() => {
    gestorDashboard.misProductos()
      .then((r) => {
        setProductos(r.data)
        if (r.data.length > 0) {
          setProductoId(r.data[0].id)
          setIndicador(r.data[0].indicador || '')
        }
      })
      .catch(() => {})
  }, [])

  useEffect(() => {
    const p = productos.find((p) => p.id === productoId)
    if (p) setIndicador(p.indicador || '')
  }, [productoId, productos])

  const gestorCodigo = user?.username || ''
  const gestorNombre = user?.nombre_completo || ''
  const today = new Date().toLocaleDateString('es-CO', { day: '2-digit', month: '2-digit', year: '2-digit' })

  const handleFile = (file: File) => {
    const allowed = ['image/jpeg', 'image/png', 'application/pdf']
    if (!allowed.includes(file.type)) {
      setError('Solo se permiten archivos JPG, PNG o PDF.')
      return
    }
    if (file.size > 10 * 1024 * 1024) {
      setError('El archivo no puede superar 10 MB.')
      return
    }
    setArchivo(file)
    setError('')
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  const handleSubmit = async (estado: string) => {
    if (!productoId) { setError('Seleccione un producto.'); return }
    if (!periodo) { setError('Seleccione un período.'); return }
    if (!porcentaje) { setError('Ingrese el porcentaje de cumplimiento.'); return }

    setSaving(true)
    setError('')
    setSuccess('')

    try {
      const data = {
        avance_porcentaje: parseFloat(porcentaje),
        avance_valor: avanceValor ? parseInt(avanceValor) : undefined,
        indicador,
        periodo,
        estado_revision: estado === 'enviar' ? 'EN_REVISION' : 'BORRADOR',
        evidencia_nombre: archivo?.name || undefined,
        evidencia_tipo: archivo?.type || undefined,
      }
      await gestorDashboard.registrarAvance(productoId, data)
      setSuccess(estado === 'enviar' ? 'Avance enviado a revisión exitosamente.' : 'Borrador guardado.')
      setEstadoRevision(data.estado_revision)
      setTimeout(() => setSuccess(''), 4000)
    } catch {
      setError('Error al registrar el avance.')
    } finally {
      setSaving(false)
    }
  }

  const estadoTone: Record<string, string> = {
    PENDIENTE: 'bg-ochre-soft text-ochre-deep',
    BORRADOR: 'bg-line/60 text-ink-soft',
    EN_REVISION: 'bg-[#E9EEF5] text-[#3D5D7A]',
    APROBADO: 'bg-forest-soft text-forest',
    RECHAZADO: 'bg-warn-soft text-warn',
  }

  return (
    <div className="space-y-0 pb-8">
      <section className="relative overflow-hidden bg-pine px-6 py-7 text-white shadow-lg sm:px-8 sm:py-9">
        <div className="absolute -right-20 -top-24 h-72 w-72 rounded-full border border-white/10" aria-hidden="true" />
        <div className="relative flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white/15 backdrop-blur">
            <Icon name="document" className="h-6 w-6 text-white" />
          </div>
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-ochre-soft">Panel administrativo</p>
            <h1 className="text-2xl font-bold leading-tight sm:text-3xl">Registro de avance y carga de evidencia</h1>
          </div>
        </div>
        <p className="relative mt-3 max-w-2xl text-sm leading-6 text-white/70">
          Selecciona el indicador asignado, reporta el avance del período y adjunta la evidencia correspondiente para enviarla a revisión.
        </p>
      </section>

      <div className="mx-auto max-w-3xl px-4 -mt-4">
        <div className="rounded-2xl border border-line bg-white shadow-md">
          <div className="border-b border-line px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-ink">Datos del cumplimiento</h2>
              </div>
              <span className="rounded-full bg-forest-soft px-3 py-1 text-xs font-bold text-forest">
                Registrando nuevo avance
              </span>
            </div>
          </div>

          <div className="border-l-4 border-pine">
            <div className="px-6 py-5">
              {success && (
                <div className="mb-4 flex items-center gap-3 rounded-xl border border-forest/30 bg-forest-soft/60 px-4 py-3 text-sm text-forest">
                  <Icon name="check" /> {success}
                </div>
              )}
              {error && (
                <div className="mb-4 flex items-center gap-3 rounded-xl border border-warn/30 bg-warn-soft/60 px-4 py-3 text-sm text-warn">
                  <Icon name="alert" /> {error}
                </div>
              )}

              <fieldset className="mb-6">
                <legend className="mb-3 text-xs font-bold uppercase tracking-wider text-ink-faint">Identificación</legend>
                <div className="grid gap-4 sm:grid-cols-3">
                  <div>
                    <label className="text-xs font-bold text-ink">Gestor <span className="font-normal text-ink-faint">(se asigna automáticamente)</span></label>
                    <div className="mt-1 rounded-xl border border-line bg-paper px-4 py-2.5 text-sm text-ink-soft">
                      {gestorCodigo} — {gestorNombre}
                    </div>
                  </div>
                  <div>
                    <label className="text-xs font-bold text-ink">Indicador de producto</label>
                    <select
                      value={productoId}
                      onChange={(e) => setProductoId(e.target.value)}
                      className="mt-1 w-full rounded-xl border border-line bg-white px-4 py-2.5 text-sm text-ink outline-none focus:border-pine focus:ring-2 focus:ring-pine/10"
                    >
                      <option value="">Selecciona el indicador asignado</option>
                      {productos.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.codigo_indicador || p.codigo} — {p.nombre}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs font-bold text-ink">id_cumplimiento <span className="font-normal text-ink-faint">(automático)</span></label>
                      <div className="mt-1 rounded-xl border border-line bg-paper px-4 py-2.5 text-sm text-ink-faint">—</div>
                    </div>
                    <div>
                      <label className="text-xs font-bold text-ink">fecha_registro <span className="font-normal text-ink-faint">(hoy)</span></label>
                      <div className="mt-1 rounded-xl border border-line bg-paper px-4 py-2.5 text-sm text-ink-soft">{today}</div>
                    </div>
                  </div>
                </div>
                <div className="mt-4">
                  <label className="text-xs font-bold text-ink">Periodo</label>
                  <select
                    value={periodo}
                    onChange={(e) => setPeriodo(e.target.value)}
                    className="mt-1 w-full rounded-xl border border-line bg-white px-4 py-2.5 text-sm text-ink outline-none focus:border-pine focus:ring-2 focus:ring-pine/10 sm:max-w-xs"
                  >
                    <option value="">Selecciona el período</option>
                    {PERIODOS.map((p) => <option key={p} value={p}>{p}</option>)}
                  </select>
                </div>
              </fieldset>

              <fieldset className="mb-6">
                <legend className="mb-3 text-xs font-bold uppercase tracking-wider text-ink-faint">Avance reportado</legend>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label className="text-xs font-bold text-ink">Avance reportado</label>
                    <input
                      type="number"
                      min={0}
                      value={avanceValor}
                      onChange={(e) => setAvanceValor(e.target.value)}
                      placeholder="Ej. 1"
                      className="mt-1 w-full rounded-xl border border-line bg-white px-4 py-2.5 text-sm text-ink outline-none focus:border-pine focus:ring-2 focus:ring-pine/10"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-bold text-ink">Porcentaje de cumplimiento</label>
                    <div className="relative mt-1">
                      <input
                        type="number"
                        min={0}
                        max={100}
                        value={porcentaje}
                        onChange={(e) => setPorcentaje(e.target.value)}
                        placeholder="Ej. 30"
                        className="w-full rounded-xl border border-line bg-white px-4 py-2.5 pr-8 text-sm text-ink outline-none focus:border-pine focus:ring-2 focus:ring-pine/10"
                      />
                      <span className="absolute right-4 top-1/2 -translate-y-1/2 text-sm text-ink-faint">%</span>
                    </div>
                  </div>
                </div>
              </fieldset>

              <fieldset className="mb-6">
                <legend className="mb-3 text-xs font-bold uppercase tracking-wider text-ink-faint">Evidencia</legend>
                <label className="text-xs font-bold text-ink">Archivo de evidencia</label>
                <div
                  onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  className={clsx(
                    'mt-2 flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-8 text-center transition-colors',
                    dragOver ? 'border-pine bg-pine/5' : 'border-line hover:border-pine/40 hover:bg-paper',
                  )}
                >
                  <Icon name="document" className="h-8 w-8 text-ink-faint" />
                  <p className="mt-2 text-sm font-bold text-ink">Arrastra el archivo aquí o <span className="text-pine underline">seleccionarlo</span></p>
                  <p className="mt-1 text-xs text-ink-faint">JPG, PNG o PDF — máx. 10 MB</p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".jpg,.jpeg,.png,.pdf"
                    className="hidden"
                    onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f) }}
                  />
                </div>
                {archivo && (
                  <div className="mt-3 flex items-center gap-3 rounded-xl bg-paper p-3">
                    <Icon name="document" className="h-5 w-5 text-pine" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-bold text-ink">{archivo.name}</p>
                      <p className="text-xs text-ink-faint">{(archivo.size / 1024).toFixed(1)} KB</p>
                    </div>
                    <button onClick={() => setArchivo(null)} className="text-ink-faint hover:text-warn"><Icon name="close" /></button>
                  </div>
                )}
              </fieldset>

              <fieldset>
                <legend className="mb-3 text-xs font-bold uppercase tracking-wider text-ink-faint">Estado y seguimiento</legend>
                <label className="text-xs font-bold text-ink">estado_revision <span className="font-normal text-ink-faint">(al enviar queda en revisión)</span></label>
                <div className="mt-2">
                  <span className={clsx('inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-bold', estadoTone[estadoRevision] || 'bg-line/60 text-ink-soft')}>
                    <span className="h-1.5 w-1.5 rounded-full bg-current" />
                    {estadoRevision === 'PENDIENTE' ? 'Pendiente' :
                     estadoRevision === 'BORRADOR' ? 'Borrador' :
                     estadoRevision === 'EN_REVISION' ? 'En revisión' :
                     estadoRevision === 'APROBADO' ? 'Aprobado' :
                     estadoRevision === 'RECHAZADO' ? 'Rechazado' : estadoRevision}
                  </span>
                </div>
              </fieldset>
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 border-t border-line px-6 py-4">
            <button
              onClick={() => handleSubmit('borrador')}
              disabled={saving}
              className="rounded-xl border border-line px-5 py-2.5 text-sm font-bold text-ink transition-colors hover:bg-paper disabled:opacity-50"
            >
              Guardar borrador
            </button>
            <button
              onClick={() => handleSubmit('enviar')}
              disabled={saving}
              className="rounded-xl bg-pine px-5 py-2.5 text-sm font-bold text-white transition-colors hover:bg-pine-deep disabled:opacity-50"
            >
              {saving ? 'Guardando...' : 'Enviar a revisión'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
