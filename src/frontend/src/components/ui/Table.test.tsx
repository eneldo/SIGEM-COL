import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { Table, type Column } from './Table'

interface Fila {
  id: string
  nombre: string
  estado: string
}

const columnas: Column<Fila>[] = [
  { key: 'nombre', header: 'Nombre' },
  { key: 'estado', header: 'Estado' },
]

const filas: Fila[] = [
  { id: '1', nombre: 'Ana', estado: 'ACTIVO' },
  { id: '2', nombre: 'Luis', estado: 'INACTIVO' },
]

describe('Table', () => {
  it('renderiza encabezados y filas con valores por defecto', () => {
    render(<Table columns={columnas} data={filas} />)

    expect(screen.getByRole('table')).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Nombre' })).toBeInTheDocument()
    expect(screen.getByRole('cell', { name: 'Ana' })).toBeInTheDocument()
    expect(screen.getByRole('cell', { name: 'INACTIVO' })).toBeInTheDocument()
    expect(screen.getAllByRole('row')).toHaveLength(3)
  })

  it('muestra el esqueleto de carga sin filas', () => {
    const { container } = render(<Table columns={columnas} data={filas} loading />)

    expect(screen.queryByRole('table')).toBeNull()
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument()
  })

  it('muestra el mensaje vacío por defecto', () => {
    render(<Table columns={columnas} data={[]} />)

    expect(screen.getByText('No hay datos disponibles')).toBeInTheDocument()
  })

  it('muestra un mensaje vacío personalizado', () => {
    render(<Table columns={columnas} data={[]} emptyMessage="Sin gestores" />)

    expect(screen.getByText('Sin gestores')).toBeInTheDocument()
  })

  it('usa la función render de la columna', () => {
    render(
      <Table
        columns={[
          { key: 'nombre', header: 'Nombre', render: (fila) => <strong>{fila.nombre}</strong> },
        ]}
        data={filas}
      />,
    )

    expect(screen.getByRole('cell', { name: 'Ana' }).querySelector('strong')).toHaveTextContent(
      'Ana',
    )
  })

  it('notifica el clic en una fila', async () => {
    const user = userEvent.setup()
    const onRowClick = vi.fn()
    render(<Table columns={columnas} data={filas} onRowClick={onRowClick} />)

    await user.click(screen.getByRole('cell', { name: 'Ana' }))

    expect(onRowClick).toHaveBeenCalledTimes(1)
    expect(onRowClick).toHaveBeenCalledWith(filas[0])
  })

  it('no marca cursor puntero sin onRowClick', () => {
    render(<Table columns={columnas} data={filas} />)

    expect(screen.getByRole('cell', { name: 'Ana' }).parentElement).not.toHaveClass(
      'cursor-pointer',
    )
  })

  it('dispara onSort solo en columnas ordenables', async () => {
    const user = userEvent.setup()
    const onSort = vi.fn()
    render(
      <Table
        columns={[
          { key: 'nombre', header: 'Nombre', sortable: true },
          { key: 'estado', header: 'Estado' },
        ]}
        data={filas}
        onSort={onSort}
      />,
    )

    await user.click(screen.getByRole('columnheader', { name: /Nombre/ }))
    expect(onSort).toHaveBeenCalledWith('nombre')

    await user.click(screen.getByRole('columnheader', { name: 'Estado' }))
    expect(onSort).toHaveBeenCalledTimes(1)
  })

  it('resalta la columna ordenada activa', () => {
    render(
      <Table
        columns={[{ key: 'nombre', header: 'Nombre', sortable: true }]}
        data={filas}
        sortField="nombre"
        sortOrder="asc"
        onSort={vi.fn()}
      />,
    )

    const header = screen.getByRole('columnheader', { name: /Nombre/ })
    expect(header.querySelector('svg')).toHaveClass('text-pine')
  })

  it('usa rowKey para identificar las filas', () => {
    const rowKey = vi.fn((fila: Fila) => fila.id)
    render(<Table columns={columnas} data={filas} rowKey={rowKey} />)

    expect(rowKey).toHaveBeenCalledTimes(2)
    expect(screen.getAllByRole('row')).toHaveLength(3)
  })
})
