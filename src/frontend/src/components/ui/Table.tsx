import { type ReactNode } from 'react'
import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export interface Column<T> {
  key: string
  header: string
  sortable?: boolean
  className?: string
  render?: (row: T, index: number) => ReactNode
}

interface TableProps<T> {
  columns: Column<T>[]
  data: T[]
  loading?: boolean
  emptyMessage?: string
  onRowClick?: (row: T) => void
  sortField?: string
  sortOrder?: 'asc' | 'desc'
  onSort?: (field: string) => void
  rowKey?: (row: T) => string | number
}

function SortIcon({ order }: { order?: 'asc' | 'desc' }) {
  return (
    <svg
      className={clsx('w-4 h-4 inline-block ml-1', order ? 'text-pine' : 'text-ink-faint')}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d={order === 'asc' ? 'M5 15l7-7 7 7' : order === 'desc' ? 'M19 9l-7 7-7-7' : 'M7 10l5 5 5-5'}
      />
    </svg>
  )
}

export function Table<T>({
  columns,
  data,
  loading = false,
  emptyMessage = 'No hay datos disponibles',
  onRowClick,
  sortField,
  sortOrder,
  onSort,
  rowKey,
}: TableProps<T>) {
  const getKey = (row: T, index: number) =>
    rowKey ? rowKey(row) : index

  if (loading) {
    return (
      <div className="bg-paper-raised rounded-xl border border-line overflow-hidden">
        <div className="animate-pulse">
          <div className="h-12 bg-line/50" />
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-14 border-t border-line bg-paper-raised" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="bg-paper-raised rounded-xl border border-line overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-paper">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={twMerge(
                    clsx(
                      'px-4 py-3 text-left font-semibold text-ink whitespace-nowrap',
                      col.sortable && 'cursor-pointer select-none hover:text-pine',
                      col.className,
                    ),
                  )}
                  onClick={() => col.sortable && onSort?.(col.key)}
                >
                  {col.header}
                  {col.sortable && (
                    <SortIcon
                      order={sortField === col.key ? sortOrder : undefined}
                    />
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-12 text-center text-ink-faint"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              data.map((row, index) => (
                <tr
                  key={getKey(row, index)}
                  className={twMerge(
                    'border-t border-line transition-colors',
                    onRowClick && 'cursor-pointer hover:bg-paper',
                  )}
                  onClick={() => onRowClick?.(row)}
                >
                  {columns.map((col) => (
                    <td key={col.key} className={clsx('px-4 py-3', col.className)}>
                      {col.render
                        ? col.render(row, index)
                        : String((row as Record<string, unknown>)[col.key] ?? '')}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
