import { useEffect, useState } from 'react'
import { Icon } from '../../components/ui/icons'
import { Button } from '../../components/ui/Button'
import { selectClass } from '../../components/ui/icons'
import { personalizacion } from '../../lib/api'
import { DEFAULT_BRANDING, useBrandingStore } from '../../lib/branding'
import type { Personalizacion } from '../../lib/types'

export function PersonalizacionPage() {
  const [colorPrimario, setColorPrimario] = useState(DEFAULT_BRANDING.color_primario)
  const [colorSecundario, setColorSecundario] = useState(DEFAULT_BRANDING.color_secundario)
  const [nombreSistema, setNombreSistema] = useState(DEFAULT_BRANDING.nombre_sistema)
  const [logoDataUrl, setLogoDataUrl] = useState<string | null>(DEFAULT_BRANDING.logo_data_url)
  const [guardado, setGuardado] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [logoError, setLogoError] = useState<string | null>(null)
  const setBranding = useBrandingStore((state) => state.setBranding)

  useEffect(() => {
    let cancelled = false
    personalizacion
      .get()
      .then((response) => {
        if (cancelled) return
        const data = response.data
        setColorPrimario(data.color_primario)
        setColorSecundario(data.color_secundario)
        setNombreSistema(data.nombre_sistema)
        setLogoDataUrl(data.logo_data_url)
      })
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [])

  function leerLogo(file: File) {
    const esImagenValida =
      file.type === 'image/png' ||
      file.type === 'image/svg+xml' ||
      /\.(png|svg)$/i.test(file.name)
    if (!esImagenValida) {
      setLogoError('El logotipo debe ser una imagen PNG o SVG.')
      return
    }
    if (file.size > 2 * 1024 * 1024) {
      setLogoError('El logotipo supera el tamaño máximo de 2MB.')
      return
    }
    setLogoError(null)
    const reader = new FileReader()
    reader.onload = () => setLogoDataUrl(String(reader.result))
    reader.onerror = () => setLogoError('No se pudo leer el archivo seleccionado.')
    reader.readAsDataURL(file)
  }

  function handleLogo(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (file) leerLogo(file)
  }

  function handleLogoClick(event: React.MouseEvent<HTMLInputElement>) {
    event.currentTarget.value = ''
  }

  function handleDropLogo(event: React.DragEvent<HTMLLabelElement>) {
    event.preventDefault()
    const file = event.dataTransfer.files?.[0]
    if (file) leerLogo(file)
  }

  function handleQuitarLogo() {
    setLogoDataUrl(null)
  }

  async function handleGuardar() {
    const payload: Personalizacion = {
      color_primario: colorPrimario,
      color_secundario: colorSecundario,
      nombre_sistema: nombreSistema,
      logo_data_url: logoDataUrl,
    }
    try {
      const response = await personalizacion.update(payload)
      setBranding(response.data)
      setError(null)
      setGuardado(true)
      setTimeout(() => setGuardado(false), 3000)
    } catch {
      setGuardado(false)
      setError('No se pudieron guardar los cambios. Revise los datos e intente de nuevo.')
    }
  }

  return <div className="space-y-6 pb-8">
    <section className="flex flex-col gap-5 rounded-[28px] bg-pine px-6 py-7 text-white shadow-[0_18px_40px_rgba(10,43,41,.16)] sm:flex-row sm:items-end sm:justify-between sm:px-8">
      <div><p className="text-xs font-bold uppercase tracking-[.2em] text-ochre-soft">Configuración</p><h1 className="mt-2 text-3xl font-bold">Personalización</h1><p className="mt-2 max-w-2xl text-sm text-white/70">Configure la apariencia visual del sistema, colores, logotipo e información institucional.</p></div>
    </section>

    <div className="grid gap-6 lg:grid-cols-2">
      <div className="rounded-2xl border border-line bg-white p-6 shadow-sm">
        <h3 className="text-lg font-bold text-ink flex items-center gap-2"><Icon name="settings" /> Colores del sistema</h3>
        <p className="mt-1 text-sm text-ink-faint">Defina los colores principales que se usarán en toda la interfaz.</p>
        <div className="mt-6 space-y-4">
          <div>
            <label className="text-sm font-bold text-ink">Color primario</label>
            <div className="mt-2 flex items-center gap-3">
              <input type="color" value={colorPrimario} onChange={(e) => setColorPrimario(e.target.value)} className="h-10 w-10 cursor-pointer rounded-lg border border-line" />
              <input value={colorPrimario} onChange={(e) => setColorPrimario(e.target.value)} className={`${selectClass} flex-1`} />
            </div>
          </div>
          <div>
            <label className="text-sm font-bold text-ink">Color secundario</label>
            <div className="mt-2 flex items-center gap-3">
              <input type="color" value={colorSecundario} onChange={(e) => setColorSecundario(e.target.value)} className="h-10 w-10 cursor-pointer rounded-lg border border-line" />
              <input value={colorSecundario} onChange={(e) => setColorSecundario(e.target.value)} className={`${selectClass} flex-1`} />
            </div>
          </div>
        </div>
        <div className="mt-6">
          <p className="text-xs font-bold uppercase tracking-wider text-ink-faint mb-2">Vista previa</p>
          <div className="flex gap-2">
            <div className="h-12 flex-1 rounded-xl" style={{ backgroundColor: colorPrimario }} />
            <div className="h-12 flex-1 rounded-xl" style={{ backgroundColor: colorSecundario }} />
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-line bg-white p-6 shadow-sm">
        <h3 className="text-lg font-bold text-ink flex items-center gap-2"><Icon name="document" /> Información institucional</h3>
        <p className="mt-1 text-sm text-ink-faint">Configure el nombre y datos del municipio que se muestran en el sistema.</p>
        <div className="mt-6 space-y-4">
          <div>
            <label className="text-sm font-bold text-ink">Nombre del sistema</label>
            <input value={nombreSistema} onChange={(e) => setNombreSistema(e.target.value)} className={`${selectClass} mt-1`} />
          </div>
          <div>
            <label htmlFor="logo-input" className="text-sm font-bold text-ink">Logotipo</label>
            <input id="logo-input" type="file" accept="image/png,image/svg+xml" onChange={handleLogo} onClick={handleLogoClick} className="mt-2 block w-full text-xs text-ink-faint file:mr-3 file:cursor-pointer file:rounded-lg file:border-0 file:bg-paper file:px-3 file:py-2 file:text-xs file:font-bold file:text-ink" />
            <div className="mt-3 flex items-center gap-4">
              <label
                htmlFor="logo-input"
                onDragOver={(event) => event.preventDefault()}
                onDrop={handleDropLogo}
                className="flex h-20 w-20 shrink-0 cursor-pointer items-center justify-center overflow-hidden rounded-xl border-2 border-dashed border-line bg-paper/50 transition-colors hover:border-pine"
              >
                {logoDataUrl ? (
                  <img src={logoDataUrl} alt="Logotipo cargado" className="h-full w-full object-contain p-1" />
                ) : (
                  <Icon name="plus" />
                )}
              </label>
              <div>
                <p className="text-sm text-ink-faint">Formatos aceptados: PNG, SVG</p>
                <p className="text-xs text-ink-faint">Tamaño máximo: 2MB</p>
                <p className="text-xs text-ink-faint">Haga clic sobre el recuadro o arrastre el archivo</p>
                {logoDataUrl && (
                  <button type="button" onClick={handleQuitarLogo} className="mt-1 text-xs font-bold text-warn underline">
                    Quitar logotipo
                  </button>
                )}
              </div>
            </div>
            {logoError && <p role="alert" className="mt-2 text-xs font-bold text-warn">{logoError}</p>}
          </div>
        </div>
      </div>
    </div>

    <div className="flex justify-end items-center gap-3">
      {error && <p className="text-sm text-warn font-bold">{error}</p>}
      {guardado && <p className="text-sm text-forest font-bold">Cambios guardados exitosamente.</p>}
      <Button onClick={handleGuardar}>Guardar cambios</Button>
    </div>
  </div>
}
