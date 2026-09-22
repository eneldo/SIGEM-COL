import { Icon } from '../../components/ui/icons'

const modulos = [
  { title: 'Usuarios del sistema', description: 'Administre cuentas de acceso, credenciales y roles de los usuarios.', icon: 'people' as const, link: '/admin/configuracion/usuarios', color: 'bg-pine' },
  { title: 'Roles y permisos', description: 'Defina roles del sistema y asigne permisos de acceso por módulo.', icon: 'shield' as const, link: '/admin/configuracion/roles', color: 'bg-forest' },
  { title: 'Auditoría', description: 'Consulte el registro de eventos y acciones realizadas en el sistema.', icon: 'document' as const, link: '/admin/configuracion/auditoria', color: 'bg-ochre' },
  { title: 'Personalización', description: 'Configure colores, logotipo y información visual del sistema.', icon: 'settings' as const, link: '/admin/configuracion/personalizacion', color: 'bg-pine-deep' },
]

export function ConfiguracionPage() {
  return <div className="space-y-6 pb-8">
    <section className="flex flex-col gap-5 rounded-[28px] bg-pine px-6 py-7 text-white shadow-[0_18px_40px_rgba(10,43,41,.16)] sm:flex-row sm:items-end sm:justify-between sm:px-8">
      <div><p className="text-xs font-bold uppercase tracking-[.2em] text-ochre-soft">Configuración</p><h1 className="mt-2 text-3xl font-bold">Panel de configuración</h1><p className="mt-2 max-w-2xl text-sm text-white/70">Administre los módulos del sistema, usuarios, roles, permisos y la apariencia de la plataforma.</p></div>
    </section>

    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {modulos.map((m) => <a key={m.link} href={m.link} className="group rounded-2xl border border-line bg-white p-6 shadow-sm transition-all hover:shadow-md hover:border-pine/30">
        <div className={`inline-flex h-12 w-12 items-center justify-center rounded-xl ${m.color} text-white`}><Icon name={m.icon} /></div>
        <h3 className="mt-4 text-lg font-bold text-ink group-hover:text-pine">{m.title}</h3>
        <p className="mt-2 text-sm text-ink-faint">{m.description}</p>
        <p className="mt-4 text-sm font-bold text-pine opacity-0 transition-opacity group-hover:opacity-100">Ir al módulo →</p>
      </a>)}
    </div>
  </div>
}
