import { useState } from 'react'
import { Icon } from '../../components/ui/icons'
import { Button } from '../../components/ui/Button'
import { selectClass } from '../../components/ui/icons'

export function PersonalizacionPage() {
  const [colorPrimario, setColorPrimario] = useState('#0A2B29')
  const [colorSecundario, setColorSecundario] = useState('#D4A843')
  const [nombreMunicipio, setNombreMunicipio] = useState('SIGEM Colombia')
  const [guardado, setGuardado] = useState(false)

  function handleGuardar() {
    setGuardado(true)
    setTimeout(() => setGuardado(false), 3000)
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
            <input value={nombreMunicipio} onChange={(e) => setNombreMunicipio(e.target.value)} className={`${selectClass} mt-1`} />
          </div>
          <div>
            <label className="text-sm font-bold text-ink">Logotipo</label>
            <div className="mt-2 flex items-center gap-4">
              <div className="flex h-20 w-20 items-center justify-center rounded-xl border-2 border-dashed border-line bg-paper/50">
                <Icon name="plus" />
              </div>
              <div>
                <p className="text-sm text-ink-faint">Formatos aceptados: PNG, SVG</p>
                <p className="text-xs text-ink-faint">Tamaño máximo: 2MB</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div className="flex justify-end gap-3">
      {guardado && <p className="text-sm text-forest font-bold">Cambios guardados exitosamente.</p>}
      <Button onClick={handleGuardar}>Guardar cambios</Button>
    </div>
  </div>
}
