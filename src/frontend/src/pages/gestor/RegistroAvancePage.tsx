import { useEffect, useState, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'
import { gestorDashboard } from '../../lib/api'
import { Icon } from '../../components/ui/icons'
import EvidenciasModal from '../../components/EvidenciasModal'
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

interface Avance {
  id: string
  producto_id: string
  avance_porcentaje: number
  avance_valor: number | null
  observaciones: string | null
  indicador: string | null
  periodo: string | null
  fecha_registro: string | null
  estado_revision: string
  evidencia_nombre: string | null
  evidencia_tipo: string | null
  observaciones_revision: string | null
  estado: string
  created_at: string | null
}

const EDITABLE_STATES = new Set(['BORRADOR', 'PENDIENTE', 'RECHAZADO', 'DEVUELTO', 'EN_REVISION'])

function canEditAvance(a: Avance) {
  return EDITABLE_STATES.has(a.estado_revision || '')
}

const ESTADO_LISTA: Record<string, { label: string; tone: string }> = {
  APROBADO: { label: 'Aprobado', tone: 'bg-forest-soft text-forest' },
  RECHAZADO: { label: 'Devuelto', tone: 'bg-warn-soft text-warn' },
  BORRADOR: { label: 'Borrador', tone: 'bg-line/60 text-ink-soft' },
  EN_REVISION: { label: 'En revisión', tone: 'bg-[#E9EEF5] text-[#3D5D7A]' },
  PENDIENTE: { label: 'Pendiente', tone: 'bg-ochre-soft text-ochre-deep' },
  DEVUELTO: { label: 'Devuelto', tone: 'bg-warn-soft text-warn' },
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
  const formRef = useRef<HTMLFormElement>(null)
  const avancesRef = useRef<HTMLElement>(null)
  const [searchParams] = useSearchParams()
  const productoParam = searchParams.get('producto_id') || ''

  const [productos, setProductos] = useState<ProductoOption[]>([])
  const [saving, setSaving] = useState(false)
  const [success, setSuccess] = useState('')
  const [error, setError] = useState('')

  const [productoId, setProductoId] = useState(productoParam)
  const [indicador, setIndicador] = useState('')
  const [periodo, setPeriodo] = useState('')
  const [avanceValor, setAvanceValor] = useState('')
  const [porcentaje, setPorcentaje] = useState('')
  const [observaciones, setObservaciones] = useState('')
  const [archivos, setArchivos] = useState<{ file: File; descripcion: string }[]>([])
  const [dragOver, setDragOver] = useState(false)
  const [estadoRevision, setEstadoRevision] = useState('PENDIENTE')

  const [avances, setAvances] = useState<Avance[]>([])
  const [loadingAvances, setLoadingAvances] = useState(true)
  const [detailAvance, setDetailAvance] = useState<Avance | null>(null)
  const [evidenciasAvance, setEvidenciasAvance] = useState<Avance | null>(null)
  const [editAvance, setEditAvance] = useState<Avance | null>(null)
  const [editForm, setEditForm] = useState({ avance_porcentaje: 0, avance_valor: '', observaciones: '', periodo: '', indicador: '' })
  const [editSaving, setEditSaving] = useState(false)
  const [editError, setEditError] = useState('')
  const [deleteTarget, setDeleteTarget] = useState<Avance | null>(null)
  const [deleteSaving, setDeleteSaving] = useState(false)
  const [deleteError, setDeleteError] = useState('')

  const loadAvances = async (prods: ProductoOption[]) => {
    setLoadingAvances(true)
    try {
      const listas = await Promise.all(prods.map((p) => gestorDashboard.avances(p.id).catch(() => null)))
      const todas: Avance[] = []
      for (const res of listas) {
        if (res?.data) todas.push(...res.data)
      }
      todas.sort((a, b) => (b.created_at || '').localeCompare(a.created_at || ''))
      setAvances(todas)
    } catch {
      setAvances([])
    } finally {
      setLoadingAvances(false)
    }
  }

  const openEditAvance = (a: Avance) => {
    setEditError('')
    setEditForm({
      avance_porcentaje: a.avance_porcentaje,
      avance_valor: a.avance_valor != null ? String(a.avance_valor) : '',
      observaciones: a.observaciones || '',
      periodo: a.periodo || '',
      indicador: a.indicador || '',
    })
    setEditAvance(a)
  }

  const saveEditAvance = async () => {
    if (!editAvance) return
    setEditSaving(true)
    setEditError('')
    try {
      await gestorDashboard.actualizarAvance(editAvance.id, {
        avance_porcentaje: editForm.avance_porcentaje,
        avance_valor: editForm.avance_valor ? parseInt(editForm.avance_valor, 10) : null,
        observaciones: editForm.observaciones || null,
        periodo: editForm.periodo || null,
        indicador: editForm.indicador || null,
      })
      setEditAvance(null)
      await loadAvances(productos)
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setEditError(axiosErr.response?.data?.detail || 'No fue posible guardar los cambios.')
    } finally {
      setEditSaving(false)
    }
  }

  const confirmDeleteAvance = async () => {
    if (!deleteTarget) return
    setDeleteSaving(true)
    setDeleteError('')
    try {
      await gestorDashboard.eliminarAvance(deleteTarget.id)
      setDeleteTarget(null)
      await loadAvances(productos)
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setDeleteError(axiosErr.response?.data?.detail || 'No fue posible eliminar el avance.')
    } finally {
      setDeleteSaving(false)
    }
  }

  useEffect(() => {
    gestorDashboard.misProductos()
      .then((r) => {
        setProductos(r.data)
        const preferred = productoParam
          ? r.data.find((p) => p.id === productoParam)
          : r.data[0]
        if (preferred) {
          setProductoId(preferred.id)
          setIndicador(preferred.indicador || '')
        }
        void loadAvances(r.data)
      })
      .catch(() => setLoadingAvances(false))
  }, [productoParam])

  useEffect(() => {
    const p = productos.find((p) => p.id === productoId)
    if (p) setIndicador(p.indicador || '')
  }, [productoId, productos])

  const gestorCodigo = user?.username || ''
  const gestorNombre = user?.nombre_completo || ''
  const today = new Date().toLocaleDateString('es-CO', { day: '2-digit', month: 'long', year: 'numeric' })
  const productoSeleccionado = productos.find((producto) => producto.id === productoId)
  const porcentajeNumero = Math.min(100, Math.max(0, Number(porcentaje) || 0))
  const camposCompletos = [productoId, periodo, porcentaje].filter(Boolean).length
  const progresoFormulario = Math.round((camposCompletos / 3) * 100)

  const handleFiles = (fileList: FileList | File[]) => {
    const allowed = ['image/jpeg', 'image/png', 'application/pdf']
    const arr = Array.from(fileList)
    const valid: { file: File; descripcion: string }[] = []
    let validationError = ''
    let duplicados = 0
    for (const f of arr) {
      if (!allowed.includes(f.type)) { validationError = `"${f.name}": solo se permiten JPG, PNG o PDF.`; continue }
      if (f.size > 10 * 1024 * 1024) { validationError = `"${f.name}": no puede superar 10 MB.`; continue }
      const duplicado = [...archivos, ...valid].some((a) =>
        a.file.name === f.name && a.file.size === f.size && a.file.lastModified === f.lastModified,
      )
      if (duplicado) { duplicados += 1; continue }
      valid.push({ file: f, descripcion: '' })
    }

    const disponibles = 4 - archivos.length
    const accepted = valid.slice(0, disponibles)
    if (accepted.length) setArchivos((prev) => [...prev, ...accepted])

    if (valid.length > disponibles) {
      setError('Cada avance permite máximo 4 evidencias.')
    } else if (validationError) {
      setError(validationError)
    } else if (duplicados && !accepted.length) {
      setError('Esos archivos ya están seleccionados.')
    } else if (duplicados) {
      setError(`Se omitieron ${duplicados} archivo${duplicados !== 1 ? 's' : ''} ya seleccionados.`)
    } else {
      setError('')
    }
  }

  const handleRemoveFile = (index: number) => {
    setArchivos((prev) => prev.filter((_, i) => i !== index))
  }

  const handleFileDesc = (index: number, desc: string) => {
    setArchivos((prev) => prev.map((a, i) => (i === index ? { ...a, descripcion: desc } : a)))
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    if (e.dataTransfer.files.length) handleFiles(e.dataTransfer.files)
  }

  const handleSubmit = async (modo: 'borrador' | 'enviar') => {
    if (!productoId) { setError('Seleccione un producto.'); return }
    if (!periodo) { setError('Seleccione un período.'); return }
    if (!porcentaje) { setError('Ingrese el porcentaje de cumplimiento.'); return }
    if (Number(porcentaje) < 0 || Number(porcentaje) > 100) {
      setError('El porcentaje de cumplimiento debe estar entre 0% y 100%.')
      return
    }

    setSaving(true)
    setError('')
    setSuccess('')

    try {
      const data = {
        avance_porcentaje: parseFloat(porcentaje),
        avance_valor: avanceValor ? parseInt(avanceValor) : undefined,
        observaciones: observaciones || undefined,
        indicador,
        periodo,
        estado_revision: modo === 'enviar' ? 'PENDIENTE' : 'BORRADOR',
        evidencia_nombre: archivos[0]?.file.name || undefined,
        evidencia_tipo: archivos[0]?.file.type || undefined,
      }
      const res = await gestorDashboard.registrarAvance(productoId, data) as { data?: { id?: string } }
      const avanceId = res?.data?.id

      if (archivos.length && avanceId) {
        for (const a of archivos) {
          await gestorDashboard.subirEvidencias(avanceId, [a.file], a.descripcion || undefined)
        }
      }

      setSuccess(
        modo === 'enviar'
          ? `Avance enviado a revisión${archivos.length ? ` con ${archivos.length} evidencia${archivos.length !== 1 ? 's' : ''}` : ''}.`
          : `Borrador guardado${archivos.length ? ` con ${archivos.length} evidencia${archivos.length !== 1 ? 's' : ''}` : ''}.`,
      )
      setEstadoRevision(data.estado_revision)
      setArchivos([])
      if (fileInputRef.current) fileInputRef.current.value = ''
      await loadAvances(productos)
      avancesRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      setTimeout(() => setSuccess(''), 4000)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(typeof msg === 'string' ? msg : 'Error al registrar el avance.')
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

  const inputClass = 'mt-2 min-h-12 w-full rounded-xl border border-line bg-white px-4 text-sm text-ink shadow-[0_1px_0_rgba(15,61,59,.03)] outline-none transition focus:border-forest focus:ring-4 focus:ring-forest/10'
  const estadoLabel = estadoRevision === 'PENDIENTE' ? 'Pendiente de revisión' : estadoRevision === 'BORRADOR' ? 'Borrador' : estadoRevision === 'EN_REVISION' ? 'En revisión' : estadoRevision === 'APROBADO' ? 'Aprobado' : estadoRevision === 'RECHAZADO' ? 'Devuelto' : estadoRevision

  return (
    <div className="mx-auto max-w-[1440px] space-y-6 pb-10">
      <section className="relative overflow-hidden rounded-[28px] bg-pine px-6 py-7 text-white shadow-[0_18px_50px_rgba(10,43,41,.18)] sm:px-8 lg:px-10 lg:py-9">
        <div className="absolute -right-16 -top-28 h-80 w-80 rounded-full border border-white/10" aria-hidden="true" />
        <div className="absolute right-32 top-4 h-24 w-24 rounded-full bg-ochre/10 blur-2xl" aria-hidden="true" />
        <div className="relative flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-3 py-1.5 text-[11px] font-bold uppercase tracking-[.18em] text-ochre-soft backdrop-blur-sm">
              <span className="h-2 w-2 rounded-full bg-ochre" /> Gestión de cumplimiento
            </div>
            <h1 className="text-3xl font-bold leading-tight sm:text-4xl">Registrar avance</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-white/70 sm:text-base">
              Reporta el resultado del período, documenta el contexto y adjunta evidencias verificables para revisión.
            </p>
          </div>
          <div className="grid grid-cols-3 gap-2 sm:min-w-[390px]">
            {[
              ['1', 'Producto', Boolean(productoId)],
              ['2', 'Avance', Boolean(periodo && porcentaje)],
              ['3', 'Evidencia', archivos.length > 0],
            ].map(([step, label, done]) => (
              <div key={label as string} className={clsx('rounded-2xl border px-3 py-3 transition', done ? 'border-white/20 bg-white/15' : 'border-white/10 bg-pine-deep/35')}>
                <span className={clsx('flex h-6 w-6 items-center justify-center rounded-full text-[11px] font-bold', done ? 'bg-ochre text-white' : 'bg-white/10 text-white/60')}>{done ? <Icon name="check" className="h-3.5 w-3.5" /> : step}</span>
                <p className="mt-2 text-xs font-bold text-white">{label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <nav aria-label="Navegación de avances" className="grid gap-3 rounded-2xl border border-line bg-white p-2 shadow-sm sm:grid-cols-2">
        <button
          type="button"
          onClick={() => formRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
          className="flex min-h-16 items-center gap-3 rounded-xl bg-pine px-4 text-left text-white transition hover:bg-pine-deep"
        >
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/10"><Icon name="plus" /></span>
          <span><strong className="block text-sm">Registrar nuevo avance</strong><small className="text-white/65">Crear y enviar un reporte</small></span>
        </button>
        <button
          type="button"
          onClick={() => avancesRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
          className="flex min-h-16 items-center gap-3 rounded-xl px-4 text-left text-ink transition hover:bg-paper"
        >
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-forest-soft text-forest"><Icon name="document" /></span>
          <span className="min-w-0 flex-1"><strong className="block text-sm">Ver mis avances registrados</strong><small className="text-ink-faint">Consultar, corregir, eliminar y administrar evidencias</small></span>
          <span className="rounded-full bg-ochre-soft px-2.5 py-1 text-xs font-bold text-ochre-deep">{loadingAvances ? '…' : avances.length}</span>
        </button>
      </nav>

      {(success || error) && (
        <div role={error ? 'alert' : 'status'} className={clsx('flex items-start gap-3 rounded-2xl border px-5 py-4 shadow-sm', error ? 'border-warn/25 bg-warn-soft text-warn' : 'border-forest/20 bg-forest-soft text-forest')}>
          <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-white/70"><Icon name={error ? 'alert' : 'check'} /></span>
          <div><p className="font-bold">{error ? 'Revisa la información' : 'Registro actualizado'}</p><p className="mt-0.5 text-sm opacity-80">{error || success}</p></div>
        </div>
      )}

      <div className="grid items-start gap-6 xl:grid-cols-[minmax(0,1fr)_330px]">
        <form ref={formRef} onSubmit={(event) => event.preventDefault()} className="scroll-mt-6 overflow-hidden rounded-[24px] border border-line bg-white shadow-[0_16px_50px_rgba(38,36,31,.07)]">
          <header className="flex flex-col gap-3 border-b border-line bg-gradient-to-r from-white to-paper/60 px-5 py-5 sm:flex-row sm:items-center sm:justify-between sm:px-7">
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[.16em] text-forest">Nuevo reporte</p>
              <h2 className="mt-1 text-2xl font-bold text-ink">Datos del cumplimiento</h2>
            </div>
            <span className={clsx('inline-flex w-fit items-center gap-2 rounded-full px-3 py-1.5 text-xs font-bold', estadoTone[estadoRevision] || 'bg-line/60 text-ink-soft')}>
              <span className="h-2 w-2 rounded-full bg-current" /> {estadoLabel}
            </span>
          </header>

          <div className="space-y-8 p-5 sm:p-7">
            <fieldset>
              <legend className="mb-5 flex items-center gap-3">
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-pine text-sm font-bold text-white">1</span>
                <span><strong className="block text-sm text-ink">Identificación del reporte</strong><small className="text-xs text-ink-faint">Selecciona el producto y período que vas a informar.</small></span>
              </legend>
              <div className="grid gap-5 lg:grid-cols-2">
                <label className="text-xs font-bold text-ink">Indicador de producto <span className="text-warn">*</span>
                  <select value={productoId} onChange={(e) => setProductoId(e.target.value)} className={inputClass}>
                    <option value="">Selecciona un indicador asignado</option>
                    {productos.map((p) => <option key={p.id} value={p.id}>{p.codigo_indicador || p.codigo} — {p.nombre}</option>)}
                  </select>
                </label>
                <label className="text-xs font-bold text-ink">Período de reporte <span className="text-warn">*</span>
                  <select value={periodo} onChange={(e) => setPeriodo(e.target.value)} className={inputClass}>
                    <option value="">Selecciona el período</option>
                    {PERIODOS.map((p) => <option key={p} value={p}>{p}</option>)}
                  </select>
                </label>
              </div>
              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                <div className="flex items-center gap-3 rounded-xl border border-line/80 bg-paper/65 px-4 py-3">
                  <Icon name="user" className="h-5 w-5 text-forest" />
                  <div className="min-w-0"><p className="text-[10px] font-bold uppercase tracking-wider text-ink-faint">Gestor responsable</p><p className="truncate text-sm font-bold text-ink">{gestorCodigo} · {gestorNombre}</p></div>
                </div>
                <div className="flex items-center gap-3 rounded-xl border border-line/80 bg-paper/65 px-4 py-3">
                  <Icon name="calendar" className="h-5 w-5 text-forest" />
                  <div><p className="text-[10px] font-bold uppercase tracking-wider text-ink-faint">Fecha de registro</p><p className="text-sm font-bold capitalize text-ink">{today}</p></div>
                </div>
              </div>
            </fieldset>

            <div className="h-px bg-line" />

            <fieldset>
              <legend className="mb-5 flex items-center gap-3">
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-pine text-sm font-bold text-white">2</span>
                <span><strong className="block text-sm text-ink">Resultado alcanzado</strong><small className="text-xs text-ink-faint">Registra el valor ejecutado y el nivel de cumplimiento.</small></span>
              </legend>
              <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]">
                <label className="text-xs font-bold text-ink">Valor reportado
                  <div className="relative"><input type="number" min={0} value={avanceValor} onChange={(e) => setAvanceValor(e.target.value)} placeholder="Ej. 125" className={`${inputClass} pr-20`} /><span className="absolute bottom-3.5 right-4 text-xs font-bold text-ink-faint">{productoSeleccionado?.unidad_medida || 'Unidades'}</span></div>
                </label>
                <div>
                  <div className="flex items-center justify-between"><label htmlFor="porcentaje" className="text-xs font-bold text-ink">Porcentaje de cumplimiento <span className="text-warn">*</span></label><strong className="text-xl text-pine">{porcentajeNumero}%</strong></div>
                  <input id="porcentaje" type="range" min={0} max={100} step={1} value={porcentajeNumero} onChange={(e) => setPorcentaje(e.target.value)} className="mt-4 h-2 w-full cursor-pointer accent-forest" />
                  <div className="mt-3 flex flex-wrap gap-2">
                    {[25, 50, 75, 100].map((valor) => <button key={valor} type="button" onClick={() => setPorcentaje(String(valor))} className={clsx('rounded-lg border px-3 py-1.5 text-xs font-bold transition', porcentajeNumero === valor ? 'border-pine bg-pine text-white' : 'border-line bg-white text-ink-soft hover:border-forest hover:text-forest')}>{valor}%</button>)}
                    <input aria-label="Porcentaje exacto" type="number" min={0} max={100} value={porcentaje} onChange={(e) => setPorcentaje(e.target.value)} placeholder="Otro" className="h-8 w-20 rounded-lg border border-line px-2 text-xs outline-none focus:border-forest" />
                  </div>
                </div>
              </div>
              <label className="mt-5 block text-xs font-bold text-ink">Observaciones del período <span className="font-normal text-ink-faint">(opcional)</span>
                <textarea value={observaciones} onChange={(e) => setObservaciones(e.target.value)} rows={3} maxLength={1000} placeholder="Describe logros, novedades o condiciones que expliquen el resultado reportado..." className={`${inputClass} resize-none py-3`} />
                <span className="mt-1 block text-right text-[11px] font-normal text-ink-faint">{observaciones.length}/1000</span>
              </label>
            </fieldset>

            <div className="h-px bg-line" />

            <fieldset>
              <legend className="mb-5 flex items-center gap-3">
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-pine text-sm font-bold text-white">3</span>
                <span><strong className="block text-sm text-ink">Evidencia de soporte</strong><small className="text-xs text-ink-faint">Adjunta uno o más documentos legibles que respalden el avance.</small></span>
              </legend>
              <label
                htmlFor="evidencia-input"
                onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                className={clsx('group flex min-h-44 w-full flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-8 text-center transition-all', archivos.length >= 4 ? 'cursor-not-allowed border-forest/30 bg-forest-soft/40 opacity-70' : dragOver ? 'scale-[1.01] cursor-pointer border-forest bg-forest-soft shadow-inner' : archivos.length ? 'cursor-pointer border-forest/40 bg-forest-soft/50' : 'cursor-pointer border-line bg-paper/35 hover:border-forest/50 hover:bg-forest-soft/30')}
              >
                <span className={clsx('flex h-12 w-12 items-center justify-center rounded-2xl transition', archivos.length ? 'bg-forest text-white' : 'bg-white text-pine shadow-sm group-hover:-translate-y-0.5')}><Icon name={archivos.length ? 'check' : 'document'} className="h-6 w-6" /></span>
                <span className="mt-4 block text-sm font-bold text-ink">{archivos.length ? `${archivos.length} archivo${archivos.length !== 1 ? 's' : ''} listo${archivos.length !== 1 ? 's' : ''} para cargar` : 'Arrastra tus archivos aquí'}</span>
                <span className="mt-1 block text-xs text-ink-faint">{archivos.length >= 4 ? 'Alcanzaste el máximo de 4 evidencias' : archivos.length ? 'Haz clic para agregar más' : 'o haz clic para seleccionar desde tu equipo'}</span>
                {!archivos.length && <span className="mt-4 rounded-full border border-line bg-white px-3 py-1 text-[11px] font-bold text-ink-soft">JPG, PNG o PDF · máximo 4 archivos de 10 MB c/u</span>}
              </label>
              <input id="evidencia-input" ref={fileInputRef} type="file" accept=".jpg,.jpeg,.png,.pdf" multiple disabled={archivos.length >= 4} className="sr-only" onChange={(e) => { if (e.target.files?.length) handleFiles(e.target.files); e.currentTarget.value = '' }} />
              {archivos.length > 0 && (
                <div className="mt-4">
                  <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <p className="text-xs text-ink-faint"><strong className="text-ink">{archivos.length} evidencia{archivos.length !== 1 ? 's' : ''}</strong> seleccionada{archivos.length !== 1 ? 's' : ''}. Puedes agregar fotos, actas o planillas en PDF.</p>
                    <label htmlFor="evidencia-input" className={clsx('inline-flex min-h-10 w-fit items-center gap-2 rounded-xl border px-4 text-xs font-bold transition', archivos.length >= 4 ? 'cursor-not-allowed border-line bg-paper text-ink-faint' : 'cursor-pointer border-forest/25 bg-forest-soft text-forest hover:border-forest/40 hover:bg-forest/10')}>
                      <Icon name="plus" className="h-4 w-4" /> {archivos.length >= 4 ? 'Máximo 4 evidencias' : 'Agregar otra evidencia'}
                    </label>
                  </div>
                  <ul className="space-y-3">
                  {archivos.map((a, i) => (
                    <li key={`${a.file.name}-${a.file.lastModified}`} className="rounded-xl border border-forest/20 bg-white p-3">
                      <div className="flex items-center gap-3">
                        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-forest-soft text-forest"><Icon name="document" className="h-4 w-4" /></span>
                        <div className="min-w-0 flex-1">
                          <p className="text-[10px] font-bold uppercase tracking-wider text-forest">Evidencia {i + 1}</p>
                          <p className="truncate text-sm font-bold text-ink">{a.file.name}</p>
                          <p className="text-xs text-ink-faint">{(a.file.size / 1024).toFixed(1)} KB · {a.file.type}</p>
                        </div>
                        <button type="button" aria-label={`Quitar ${a.file.name}`} onClick={(event) => { event.stopPropagation(); handleRemoveFile(i) }} className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-ink-faint transition hover:bg-warn-soft hover:text-warn"><Icon name="close" /></button>
                      </div>
                      <input
                        type="text"
                        value={a.descripcion}
                        onChange={(e) => handleFileDesc(i, e.target.value)}
                        onClick={(e) => e.stopPropagation()}
                        placeholder="Descripción de la evidencia (opcional)"
                        maxLength={1000}
                        className="mt-2 w-full rounded-lg border border-line bg-paper/50 px-3 py-2 text-xs text-ink outline-none transition focus:border-forest focus:ring-2 focus:ring-forest/10"
                      />
                    </li>
                  ))}
                  </ul>
                </div>
              )}
            </fieldset>
          </div>

          <footer className="sticky bottom-0 z-10 flex flex-col gap-3 border-t border-line bg-white/95 px-5 py-4 backdrop-blur sm:flex-row sm:items-center sm:justify-between sm:px-7">
            <p className="text-xs text-ink-faint"><strong className="text-ink">{camposCompletos}/3 campos clave</strong> completados</p>
            <div className="flex flex-col-reverse gap-2 sm:flex-row">
              <button type="button" onClick={() => handleSubmit('borrador')} disabled={saving} className="min-h-11 rounded-xl border border-line bg-white px-5 text-sm font-bold text-ink transition hover:border-pine/30 hover:bg-paper disabled:cursor-not-allowed disabled:opacity-50">Guardar borrador</button>
              <button type="button" onClick={() => handleSubmit('enviar')} disabled={saving || camposCompletos < 3} className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-pine px-6 text-sm font-bold text-white shadow-[0_8px_20px_rgba(15,61,59,.18)] transition hover:bg-pine-deep disabled:cursor-not-allowed disabled:bg-ink-faint disabled:shadow-none">{saving ? <><span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" /> Guardando...</> : <>Enviar a revisión <Icon name="check" /></>}</button>
            </div>
          </footer>
        </form>

        <aside className="space-y-4 xl:sticky xl:top-6">
          <section className="overflow-hidden rounded-[24px] bg-pine text-white shadow-[0_16px_40px_rgba(10,43,41,.14)]">
            <div className="p-6">
              <div className="flex items-center justify-between gap-4">
                <div><p className="text-[10px] font-bold uppercase tracking-[.18em] text-white/55">Progreso del formulario</p><p className="mt-1 text-2xl font-bold">{progresoFormulario}% listo</p></div>
                <div className="grid h-16 w-16 place-items-center rounded-full" style={{ background: `conic-gradient(var(--ochre) ${progresoFormulario}%, rgba(255,255,255,.12) 0)` }}><div className="grid h-12 w-12 place-items-center rounded-full bg-pine text-xs font-bold">{camposCompletos}/3</div></div>
              </div>
              <div className="mt-5 h-1.5 overflow-hidden rounded-full bg-white/10"><div className="h-full rounded-full bg-ochre transition-all duration-500" style={{ width: `${progresoFormulario}%` }} /></div>
            </div>
            <div className="border-t border-white/10 bg-pine-deep/35 p-5">
              <p className="text-[10px] font-bold uppercase tracking-[.18em] text-white/50">Producto seleccionado</p>
              {productoSeleccionado ? <><p className="mt-2 font-mono text-xs font-bold text-ochre-soft">{productoSeleccionado.codigo_indicador || productoSeleccionado.codigo}</p><h3 className="mt-1 text-lg font-bold leading-snug">{productoSeleccionado.nombre}</h3>{productoSeleccionado.meta_redactada && <p className="mt-2 line-clamp-3 text-xs leading-5 text-white/60">{productoSeleccionado.meta_redactada}</p>}</> : <p className="mt-2 text-sm text-white/60">Selecciona un producto para ver su ficha.</p>}
            </div>
          </section>

          <section className="rounded-[20px] border border-line bg-white p-5 shadow-sm">
            <p className="text-[10px] font-bold uppercase tracking-[.16em] text-ink-faint">Antes de enviar</p>
            <ul className="mt-4 space-y-3">
              {[
                ['Producto y período definidos', Boolean(productoId && periodo)],
                ['Porcentaje entre 0% y 100%', Boolean(porcentaje)],
                ['Evidencia de soporte adjunta', archivos.length > 0],
              ].map(([label, done]) => <li key={label as string} className="flex items-center gap-3 text-xs"><span className={clsx('flex h-6 w-6 shrink-0 items-center justify-center rounded-full', done ? 'bg-forest-soft text-forest' : 'bg-paper text-ink-faint')}><Icon name={done ? 'check' : 'dots'} className="h-3.5 w-3.5" /></span><span className={done ? 'font-bold text-ink' : 'text-ink-faint'}>{label}</span></li>)}
            </ul>
            <div className="mt-5 rounded-xl bg-ochre-soft/70 p-3 text-xs leading-5 text-ochre-deep"><strong>Nota:</strong> puedes guardar el formulario como borrador y completarlo antes de enviarlo a revisión.</div>
          </section>
        </aside>
      </div>

      <section ref={avancesRef} className="scroll-mt-6 overflow-hidden rounded-[24px] border border-line bg-white shadow-[0_16px_50px_rgba(38,36,31,.07)]" aria-labelledby="lista-avances-title">
        <div className="flex flex-col gap-3 border-b border-line bg-gradient-to-r from-white to-paper/60 px-5 py-5 sm:flex-row sm:items-center sm:justify-between sm:px-7">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[.16em] text-forest">Historial</p>
            <h2 id="lista-avances-title" className="mt-1 text-2xl font-bold text-ink">Avances registrados</h2>
            <p className="mt-1 text-sm text-ink-faint">Aquí puedes ver el detalle, corregir datos, agregar evidencias o eliminar registros que aún no estén aprobados.</p>
          </div>
          <button
            type="button"
            onClick={() => void loadAvances(productos)}
            disabled={loadingAvances}
            className="inline-flex min-h-10 w-fit items-center gap-2 rounded-xl border border-line bg-white px-4 text-sm font-bold text-ink transition hover:border-pine/30 hover:bg-paper disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Icon name="refresh" className={clsx('h-4 w-4', loadingAvances && 'animate-spin')} /> Actualizar
          </button>
        </div>

        {loadingAvances ? (
          <div className="space-y-3 p-6" aria-label="Cargando avances">
            {[1, 2, 3].map((i) => <div key={i} className="h-16 animate-pulse rounded-xl bg-line/40" />)}
          </div>
        ) : avances.length === 0 ? (
          <div className="flex min-h-56 flex-col items-center justify-center px-6 py-10 text-center">
            <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-paper text-ink-faint"><Icon name="document" className="h-6 w-6" /></span>
            <h3 className="mt-4 text-lg font-bold text-ink">Sin avances registrados</h3>
            <p className="mt-1 max-w-sm text-sm leading-5 text-ink-faint">Usa el formulario para crear el primer reporte de cumplimiento.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-line bg-paper/60">
                  <th className="px-5 py-3.5 font-bold text-ink-faint sm:px-7">Producto</th>
                  <th className="px-5 py-3.5 font-bold text-ink-faint">Período</th>
                  <th className="px-5 py-3.5 font-bold text-ink-faint">Avance</th>
                  <th className="hidden px-5 py-3.5 font-bold text-ink-faint md:table-cell">Valor</th>
                  <th className="px-5 py-3.5 font-bold text-ink-faint">Estado</th>
                  <th className="hidden px-5 py-3.5 font-bold text-ink-faint lg:table-cell">Fecha</th>
                  <th className="px-5 py-3.5 font-bold text-ink-faint sm:px-7">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {avances.map((a) => {
                  const producto = productos.find((p) => p.id === a.producto_id)
                  const estado = ESTADO_LISTA[a.estado_revision] || { label: a.estado_revision, tone: 'bg-line/60 text-ink-soft' }
                  return (
                    <tr key={a.id} className="transition-colors hover:bg-paper/40">
                      <td className="px-5 py-4 sm:px-7">
                        <p className="font-bold text-ink">{producto ? (producto.codigo_indicador || producto.codigo) : '—'}</p>
                        <p className="mt-0.5 max-w-[220px] truncate text-xs text-ink-faint">{producto?.nombre || a.producto_id}</p>
                      </td>
                      <td className="px-5 py-4 text-ink-soft">{a.periodo || '—'}</td>
                      <td className="px-5 py-4"><strong className="text-pine">{a.avance_porcentaje}%</strong></td>
                      <td className="hidden px-5 py-4 text-ink-soft md:table-cell">{a.avance_valor ?? '—'}</td>
                      <td className="px-5 py-4">
                        <span className={clsx('inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-bold', estado.tone)}>
                          <span className="h-1.5 w-1.5 rounded-full bg-current" /> {estado.label}
                        </span>
                      </td>
                      <td className="hidden px-5 py-4 text-xs text-ink-faint lg:table-cell">
                        {a.created_at ? new Date(a.created_at).toLocaleDateString('es-CO') : '—'}
                      </td>
                      <td className="px-5 py-4 sm:px-7">
                        <div className="flex flex-wrap items-center gap-1.5">
                          <button type="button" onClick={() => setDetailAvance(a)} title="Ver detalle" className="inline-flex h-8 items-center justify-center gap-1.5 rounded-lg border border-line px-2 text-pine transition hover:bg-forest-soft"><Icon name="eye" className="h-4 w-4" /><span className="hidden xl:inline">Ver</span></button>
                          <button type="button" onClick={() => setEvidenciasAvance(a)} title="Administrar evidencias" className="inline-flex h-8 items-center justify-center gap-1.5 rounded-lg border border-line px-2 text-pine transition hover:bg-forest-soft"><Icon name="document" className="h-4 w-4" /><span className="hidden xl:inline">Evidencias</span></button>
                          {canEditAvance(a) && (
                            <button type="button" onClick={() => openEditAvance(a)} title="Corregir avance" className="inline-flex h-8 items-center justify-center gap-1.5 rounded-lg border border-line px-2 text-pine transition hover:bg-forest-soft"><Icon name="edit" className="h-4 w-4" /><span className="hidden xl:inline">Corregir</span></button>
                          )}
                          {canEditAvance(a) && (
                            deleteTarget?.id === a.id ? (
                              <div className="flex gap-1">
                                <button type="button" onClick={() => void confirmDeleteAvance()} disabled={deleteSaving} title="Confirmar eliminación" className="flex h-8 w-8 items-center justify-center rounded-lg bg-warn text-white transition hover:bg-warn/90 disabled:opacity-50"><Icon name="check" className="h-4 w-4" /></button>
                                <button type="button" onClick={() => { setDeleteTarget(null); setDeleteError('') }} title="Cancelar" className="flex h-8 w-8 items-center justify-center rounded-lg text-ink-faint transition hover:bg-line"><Icon name="close" className="h-4 w-4" /></button>
                              </div>
                            ) : (
                              <button type="button" onClick={() => { setDeleteError(''); setDeleteTarget(a) }} title="Eliminar avance" className="inline-flex h-8 items-center justify-center gap-1.5 rounded-lg border border-line px-2 text-warn transition hover:bg-warn-soft"><Icon name="trash" className="h-4 w-4" /><span className="hidden xl:inline">Eliminar</span></button>
                            )
                          )}
                        </div>
                        {deleteTarget?.id === a.id && deleteError && (
                          <p role="alert" className="mt-1.5 max-w-[200px] text-[11px] font-bold text-warn">{deleteError}</p>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {detailAvance && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" role="dialog" aria-modal="true">
          <div className="w-full max-w-lg rounded-2xl bg-paper-raised shadow-2xl">
            <div className="flex items-center justify-between border-b border-line px-6 py-4">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.16em] text-ink-faint">Detalle del avance</p>
                <h3 className="mt-1 text-lg font-bold text-ink">{productos.find((p) => p.id === detailAvance.producto_id)?.nombre || 'Avance'}</h3>
              </div>
              <button type="button" onClick={() => setDetailAvance(null)} className="flex h-8 w-8 items-center justify-center rounded-lg text-ink-faint transition hover:bg-line/60 hover:text-ink"><Icon name="close" /></button>
            </div>
            <div className="space-y-4 px-6 py-5 text-sm">
              <div className="grid grid-cols-2 gap-4">
                <div><p className="text-ink-faint">Período</p><p className="font-bold text-ink">{detailAvance.periodo || '—'}</p></div>
                <div><p className="text-ink-faint">Estado</p><span className={clsx('mt-1 inline-flex rounded-full px-2.5 py-1 text-[11px] font-bold', (ESTADO_LISTA[detailAvance.estado_revision] || ESTADO_LISTA.PENDIENTE).tone)}>{(ESTADO_LISTA[detailAvance.estado_revision] || ESTADO_LISTA.PENDIENTE).label}</span></div>
                <div><p className="text-ink-faint">Porcentaje</p><p className="font-bold text-pine">{detailAvance.avance_porcentaje}%</p></div>
                <div><p className="text-ink-faint">Valor reportado</p><p className="font-bold text-ink">{detailAvance.avance_valor ?? '—'}</p></div>
                <div className="col-span-2"><p className="text-ink-faint">Indicador</p><p className="font-bold text-ink">{detailAvance.indicador || '—'}</p></div>
                <div className="col-span-2"><p className="text-ink-faint">Observaciones</p><p className="mt-0.5 leading-5 text-ink-soft">{detailAvance.observaciones || 'Sin observaciones.'}</p></div>
                {detailAvance.evidencia_nombre && (
                  <div className="col-span-2"><p className="text-ink-faint">Evidencia asociada</p><p className="font-bold text-ink">{detailAvance.evidencia_nombre}</p></div>
                )}
                {detailAvance.estado_revision === 'RECHAZADO' && detailAvance.observaciones_revision && (
                  <div className="col-span-2 rounded-xl border border-warn/30 bg-warn-soft px-4 py-3 text-warn"><p className="text-[11px] font-bold uppercase tracking-wider">Observación de revisión</p><p className="mt-1 text-sm">{detailAvance.observaciones_revision}</p></div>
                )}
                <div className="col-span-2 border-t border-line pt-3 text-xs text-ink-faint">
                  Registrado: {detailAvance.created_at ? new Date(detailAvance.created_at).toLocaleString('es-CO') : '—'}
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-3 border-t border-line px-6 py-4">
              <button type="button" onClick={() => setDetailAvance(null)} className="rounded-xl border border-line px-4 py-2.5 text-sm font-bold text-ink-soft transition hover:bg-line/40">Cerrar</button>
              <button type="button" onClick={() => { setEvidenciasAvance(detailAvance); setDetailAvance(null) }} className="rounded-xl bg-pine px-5 py-2.5 text-sm font-bold text-white transition hover:bg-pine-deep">Ver evidencias</button>
            </div>
          </div>
        </div>
      )}

      {evidenciasAvance && (
        <EvidenciasModal
          avanceId={evidenciasAvance.id}
          avanceNombre={`${evidenciasAvance.avance_porcentaje}% · ${evidenciasAvance.periodo || 'Sin período'}`}
          subtitle={productos.find((p) => p.id === evidenciasAvance.producto_id)?.nombre}
          canEdit={canEditAvance(evidenciasAvance)}
          onClose={() => setEvidenciasAvance(null)}
        />
      )}

      {editAvance && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" role="dialog" aria-modal="true">
          <div className="w-full max-w-lg rounded-2xl bg-paper-raised shadow-2xl">
            <div className="flex items-center justify-between border-b border-line px-6 py-4">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.16em] text-ink-faint">Editar avance</p>
                <h3 className="mt-1 text-lg font-bold text-ink">{productos.find((p) => p.id === editAvance.producto_id)?.nombre || 'Avance'}</h3>
              </div>
              <button type="button" onClick={() => setEditAvance(null)} className="flex h-8 w-8 items-center justify-center rounded-lg text-ink-faint transition hover:bg-line/60 hover:text-ink"><Icon name="close" /></button>
            </div>
            <div className="space-y-4 px-6 py-5">
              {editError && <div role="alert" className="rounded-xl border border-warn/30 bg-warn-soft px-4 py-3 text-sm text-warn">{editError}</div>}
              <div>
                <label className="block text-sm font-bold text-ink">Porcentaje de avance (%)</label>
                <input type="number" min={0} max={100} value={editForm.avance_porcentaje} onChange={(e) => setEditForm({ ...editForm, avance_porcentaje: parseFloat(e.target.value) || 0 })} className="mt-1 w-full rounded-xl border border-line bg-paper px-4 py-2.5 text-sm text-ink outline-none focus:border-pine focus:ring-2 focus:ring-pine/20" />
              </div>
              <div>
                <label className="block text-sm font-bold text-ink">Valor (opcional)</label>
                <input type="number" min={0} value={editForm.avance_valor} onChange={(e) => setEditForm({ ...editForm, avance_valor: e.target.value })} className="mt-1 w-full rounded-xl border border-line bg-paper px-4 py-2.5 text-sm text-ink outline-none focus:border-pine focus:ring-2 focus:ring-pine/20" placeholder="Ej: 125" />
              </div>
              <div>
                <label className="block text-sm font-bold text-ink">Período</label>
                <input type="text" value={editForm.periodo} onChange={(e) => setEditForm({ ...editForm, periodo: e.target.value })} className="mt-1 w-full rounded-xl border border-line bg-paper px-4 py-2.5 text-sm text-ink outline-none focus:border-pine focus:ring-2 focus:ring-pine/20" placeholder="Ej: Julio - Septiembre 2026" maxLength={50} />
              </div>
              <div>
                <label className="block text-sm font-bold text-ink">Observaciones</label>
                <textarea value={editForm.observaciones} onChange={(e) => setEditForm({ ...editForm, observaciones: e.target.value })} rows={3} maxLength={1000} className="mt-1 w-full resize-none rounded-xl border border-line bg-paper px-4 py-2.5 text-sm text-ink outline-none focus:border-pine focus:ring-2 focus:ring-pine/20" placeholder="Describe el avance..." />
              </div>
            </div>
            <div className="flex items-center justify-end gap-3 border-t border-line px-6 py-4">
              <button type="button" onClick={() => setEditAvance(null)} className="rounded-xl border border-line px-4 py-2.5 text-sm font-bold text-ink-soft transition hover:bg-line/40">Cancelar</button>
              <button type="button" onClick={() => void saveEditAvance()} disabled={editSaving || editForm.avance_porcentaje < 0 || editForm.avance_porcentaje > 100} className="rounded-xl bg-pine px-5 py-2.5 text-sm font-bold text-white transition hover:bg-pine-deep disabled:opacity-50">{editSaving ? 'Guardando...' : 'Guardar cambios'}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
