export type IconName =
  | 'plus'
  | 'refresh'
  | 'search'
  | 'edit'
  | 'shield'
  | 'key'
  | 'audit'
  | 'trash'
  | 'dots'
  | 'close'
  | 'copy'
  | 'columns'
  | 'box'
  | 'layers'
  | 'calendar'
  | 'user'
  | 'home'
  | 'bell'
  | 'spark'
  | 'alert'
  | 'check'
  | 'building'
  | 'document'
  | 'people'
  | 'settings'

const paths: Record<IconName, string> = {
  plus: 'M12 4.5v15m7.5-7.5h-15',
  refresh: 'M16.02 9.35h5V4.36m-.01 4.99-3.18-3.18a8.25 8.25 0 1 0 1.94 8.57',
  search: 'm21 21-4.35-4.35m2.1-5.4a7.5 7.5 0 1 1-15 0 7.5 7.5 0 0 1 15 0Z',
  edit: 'm16.86 4.49 1.69-1.69a1.88 1.88 0 1 1 2.65 2.65L10.58 16.07a4.5 4.5 0 0 1-1.9 1.13L6 18l.8-2.69a4.5 4.5 0 0 1 1.13-1.89l8.93-8.93ZM18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10',
  shield: 'M12 3c2.12 1.43 4.57 2.25 7.13 2.38v5.37c0 4.8-2.91 8.34-7.13 10.25-4.22-1.91-7.13-5.45-7.13-10.25V5.38A14.95 14.95 0 0 0 12 3Zm-2.25 9 1.5 1.5 3.5-4',
  key: 'M15.75 5.25a6 6 0 1 1-6.16 4.03l-7.34 7.34v5.13H7.5V19.5h2.25v-2.25h2.25l1.16-1.16a6 6 0 0 1 2.59-10.84Z',
  audit: 'M9 12.75 11.25 15 15 9.75M12 3.75a8.25 8.25 0 1 0 8.25 8.25A8.25 8.25 0 0 0 12 3.75Z',
  trash: 'm9.75 9 .38 9m3.74 0 .38-9M4.5 6.75h15m-12 0V4.5h9v2.25m1.5 0-.75 14.25H6.75L6 6.75',
  dots: 'M12 6.75h.01M12 12h.01M12 17.25h.01',
  close: 'm6 6 12 12M18 6 6 18',
  copy: 'M8.25 7.5V5.25A2.25 2.25 0 0 1 10.5 3h8.25A2.25 2.25 0 0 1 21 5.25v8.25a2.25 2.25 0 0 1-2.25 2.25H16.5m-11.25-7.5h8.25a2.25 2.25 0 0 1 2.25 2.25v8.25A2.25 2.25 0 0 1 13.5 21H5.25A2.25 2.25 0 0 1 3 18.75V10.5a2.25 2.25 0 0 1 2.25-2.25Z',
  columns: 'M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25A2.25 2.25 0 0 1 8.25 10.5H6a2.25 2.25 0 0 1-2.25-2.25V6Zm3.75 0v2.25M6 13.5h2.25A2.25 2.25 0 0 1 10.5 15.75V18a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 18v-2.25A2.25 2.25 0 0 1 6 13.5Zm0 2.25V18M13.5 6A2.25 2.25 0 0 1 15.75 3.75H18A2.25 2.25 0 0 1 20.25 6v2.25A2.25 2.25 0 0 1 18 10.5h-2.25a2.25 2.25 0 0 1-2.25-2.25V6Zm3.75 0v2.25M15.75 13.5H18a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25h-2.25a2.25 2.25 0 0 1-2.25-2.25v-2.25a2.25 2.25 0 0 1 2.25-2.25Zm0 2.25V18',
  box: 'M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12Z',
  layers: 'M21 7.5-12 3.75 3 7.5l9 3.75 9-3.75ZM3.75 12l9 3.75L21.75 12M3.75 16.5l9 3.75 9-3.75',
  calendar: 'M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5',
  user: 'M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.5 20.25a7.5 7.5 0 0 1 15 0',
  home: 'M2.25 12 11.6 3.9a1.13 1.13 0 0 1 1.8 0L21.75 12m-18 0v8.25a1.5 1.5 0 0 0 1.5 1.5h13.5a1.5 1.5 0 0 0 1.5-1.5V12',
  bell: 'M14.857 17.082a23.85 23.85 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.97 8.97 0 0 1-2.312 6.022c.435.181.894.339 1.454.433 1.172.198 2.386.317 3.608.317m5.107 0a23.85 23.85 0 0 1-5.107 0m5.107 0a3.72 3.72 0 0 1-3.72 3.75 3.72 3.72 0 0 1-3.72-3.75',
  spark: 'M9.813 3.157 12 6.5l2.187-3.343a.75.75 0 0 1 1.332.223l.873 3.824 3.647-2.14a.75.75 0 0 1 .994.901l-.193 3.937 4.477-1.095a.75.75 0 0 1 .861.567',
  alert: 'M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.01',
  building: 'M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375a1.125 1.125 0 0 1 1.125-1.125h3.75A1.125 1.125 0 0 1 15 17.625V21',
  check: 'm5.25 12.75 4.5 4.5 9-10.5',
  document: 'M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z',
  people: 'M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z',
  settings: 'M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z',
}

export function Icon({ name, className = 'h-4 w-4' }: { name: IconName; className?: string }) {
  return (
    <svg aria-hidden="true" className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <path d={paths[name]} />
    </svg>
  )
}

export function formatDate(value?: string | null) {
  if (!value) return 'Sin registro'
  return new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

export function formatDateOnly(value?: string | null) {
  if (!value) return 'Sin registro'
  const dateOnly = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value)
  const date = dateOnly
    ? new Date(Number(dateOnly[1]), Number(dateOnly[2]) - 1, Number(dateOnly[3]))
    : new Date(value)
  return new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium' }).format(date)
}

export function ModalShell({ title, description, close, children, wide = false }: { title: string; description?: string; close: () => void; children: React.ReactNode; wide?: boolean }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-pine-deep/70 p-4 backdrop-blur-sm" onMouseDown={(e) => e.target === e.currentTarget && close()}>
      <section role="dialog" aria-modal="true" aria-labelledby="modal-title" className={`max-h-[92vh] w-full overflow-hidden rounded-3xl bg-white shadow-2xl ${wide ? 'max-w-3xl' : 'max-w-xl'}`}>
        <header className="flex items-start justify-between border-b border-line px-6 py-5">
          <div>
            <h2 id="modal-title" className="text-2xl font-bold text-ink">{title}</h2>
            {description && <p className="mt-1 text-sm text-ink-faint">{description}</p>}
          </div>
          <button onClick={close} aria-label="Cerrar" className="flex h-10 w-10 items-center justify-center rounded-xl text-ink-faint hover:bg-line/50"><Icon name="close" /></button>
        </header>
        <div className="max-h-[calc(92vh-89px)] overflow-y-auto">{children}</div>
      </section>
    </div>
  )
}

export const selectClass = 'block min-h-10 w-full rounded-xl border border-line bg-white px-3 py-2 text-sm text-ink focus:border-pine focus:outline-none focus:ring-2 focus:ring-pine/20'

export function EstadoBadge({ estado }: { estado: string }) {
  const activa = estado === 'ACTIVA'
  const activo = estado === 'ACTIVO'
  const ok = activa || activo
  return (
    <span className={`inline-flex items-center gap-2 rounded-full px-2.5 py-1 text-xs font-bold ${ok ? 'bg-forest-soft text-forest' : 'bg-line/60 text-ink-soft'}`}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {estado}
    </span>
  )
}
