import { useAuthStore } from '../../stores/authStore'

interface HeaderProps {
  onMenuToggle: () => void
}

export function Header({ onMenuToggle }: HeaderProps) {
  const { user, logout } = useAuthStore()
  const isAdmin = user?.roles?.some((role) =>
    ['SUPERADMIN_PLATAFORMA', 'ADMINISTRADOR_MUNICIPAL'].includes(role),
  )
  const isGestorLider = user?.roles?.includes('GESTOR_LIDER')

  return (
    <header className="sticky top-0 z-30 flex min-h-16 w-full items-center justify-between border-b border-line/80 bg-paper-raised/95 px-4 shadow-[0_1px_0_rgba(15,61,59,0.03)] backdrop-blur sm:px-6 xl:px-10">
      <button
        onClick={onMenuToggle}
        aria-label="Abrir menú de navegación"
        className="flex h-11 w-11 items-center justify-center rounded-xl text-ink transition-colors hover:bg-forest-soft"
      >
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
        </svg>
      </button>

      <div className="hidden lg:flex items-center gap-3">
        <span className="h-2 w-2 rounded-full bg-done ring-4 ring-done/10" aria-hidden="true" />
        <div>
          <p className="text-sm font-bold text-pine">
            {isAdmin ? 'Administración municipal' : isGestorLider ? 'Gestión de equipo' : 'Gestión de productos'}
          </p>
          <p className="text-xs text-ink-faint">Sistema operativo</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="hidden sm:block text-right">
          <p className="text-sm font-medium text-ink">{user?.nombre_completo}</p>
          <p className="text-xs text-ink-faint">{user?.email}</p>
        </div>

        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-pine shadow-sm ring-1 ring-pine-deep/20">
          <span className="text-white text-sm font-semibold">
            {user?.nombre_completo?.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase() || 'U'}
          </span>
        </div>

        <button
          onClick={logout}
          aria-label="Cerrar sesión"
          className="flex h-11 w-11 items-center justify-center rounded-xl text-ink-faint transition-colors hover:bg-warn/10 hover:text-warn"
          title="Cerrar sesión"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
          </svg>
        </button>
      </div>
    </header>
  )
}
