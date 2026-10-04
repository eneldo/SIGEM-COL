import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { configAuditoria } from '../../lib/api'
import { AuditoriaPage } from './AuditoriaPage'

vi.mock('../../lib/api', () => ({
  configAuditoria: {
    list: vi.fn(),
    stats: vi.fn(),
  },
  default: {},
}))

const mockedAuditoria = vi.mocked(configAuditoria)

const estadisticas = {
  total_eventos: 120,
  exitosos: 100,
  fallidos: 20,
  hoy: 5,
  por_tipo: { LOGIN: 40, CREATE: 30, TIPO_DESCONOCIDO: 10 },
}

const eventos = [
  {
    id: 'e1',
    evento_tipo: 'LOGIN',
    recurso_tipo: 'USUARIO',
    resultado: 'EXITOSO',
    ip_address: '192.168.0.10',
    actor_nombre: 'Ana Pérez',
    fecha_evento: '2026-03-01T08:30:00Z',
  },
  {
    id: 'e2',
    evento_tipo: 'CREATE',
    recurso_tipo: undefined,
    resultado: 'FALLIDO',
    ip_address: undefined,
    actor_nombre: undefined,
    fecha_evento: '2026-03-02T09:00:00Z',
  },
  {
    id: 'e3',
    evento_tipo: 'TIPO_DESCONOCIDO',
    recurso_tipo: 'GESTOR',
    resultado: 'PENDIENTE',
    ip_address: '10.0.0.4',
    actor_nombre: 'Carlos Ruiz',
    fecha_evento: '2026-03-03T10:15:00Z',
  },
]

beforeEach(() => {
  mockedAuditoria.list.mockReset()
  mockedAuditoria.stats.mockReset()
})

describe('AuditoriaPage', () => {
  it('muestra el estado de carga mientras consulta los eventos', () => {
    mockedAuditoria.list.mockReturnValue(new Promise(() => {}) as never)
    mockedAuditoria.stats.mockReturnValue(new Promise(() => {}) as never)

    render(<AuditoriaPage />)

    expect(screen.getByText('Cargando eventos...')).toBeInTheDocument()
  })

  it('lista los eventos con sus estadísticas y etiquetas de tipo', async () => {
    mockedAuditoria.stats.mockResolvedValue({ data: estadisticas } as never)
    mockedAuditoria.list.mockResolvedValue({ data: { items: eventos } } as never)

    render(<AuditoriaPage />)

    expect(await screen.findByText('Ana Pérez')).toBeInTheDocument()
    expect(screen.getByText('120')).toBeInTheDocument()
    expect(screen.getByText('100')).toBeInTheDocument()
    expect(screen.getByText('20')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
    expect(screen.getByText('Eventos por tipo')).toBeInTheDocument()
    expect(screen.getByText('10')).toBeInTheDocument()
    expect(screen.getAllByText('TIPO_DESCONOCIDO')).toHaveLength(2)

    const tabla = screen.getByRole('table')
    expect(within(tabla).getAllByRole('row')).toHaveLength(4)
    expect(within(tabla).getByText('Carlos Ruiz')).toBeInTheDocument()
    expect(within(tabla).getByText('Sistema')).toBeInTheDocument()
    expect(within(tabla).getByText('USUARIO')).toBeInTheDocument()
    expect(within(tabla).getByText('GESTOR')).toBeInTheDocument()
    expect(within(tabla).getByText('EXITOSO')).toBeInTheDocument()
    expect(within(tabla).getByText('FALLIDO')).toBeInTheDocument()
    expect(within(tabla).getByText('PENDIENTE')).toBeInTheDocument()
    expect(within(tabla).getAllByText('-')).toHaveLength(2)
  })

  it('muestra el mensaje de vacío cuando no hay eventos', async () => {
    mockedAuditoria.stats.mockResolvedValue({
      data: { ...estadisticas, por_tipo: {} },
    } as never)
    mockedAuditoria.list.mockResolvedValue({ data: { items: [] } } as never)

    render(<AuditoriaPage />)

    expect(
      await screen.findByText('No hay eventos que coincidan con los filtros.'),
    ).toBeInTheDocument()
    expect(screen.queryByText('Eventos por tipo')).toBeNull()
  })

  it('muestra el error cuando la lista de eventos falla', async () => {
    mockedAuditoria.stats.mockResolvedValue({ data: estadisticas } as never)
    mockedAuditoria.list.mockRejectedValue(new Error('fallo de red') as never)

    render(<AuditoriaPage />)

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'No fue posible cargar los eventos de auditoría.',
    )
  })

  it('omite las estadísticas cuando la consulta de resumen falla', async () => {
    mockedAuditoria.stats.mockRejectedValue(new Error('fallo') as never)
    mockedAuditoria.list.mockResolvedValue({ data: { items: eventos } } as never)

    render(<AuditoriaPage />)

    expect(await screen.findByText('Ana Pérez')).toBeInTheDocument()
    expect(screen.queryByText('Eventos por tipo')).toBeNull()
    expect(screen.queryByText('120')).toBeNull()
  })

  it('aplica los filtros de evento, recurso y resultado', async () => {
    const user = userEvent.setup()
    mockedAuditoria.stats.mockResolvedValue({ data: estadisticas } as never)
    mockedAuditoria.list.mockResolvedValue({ data: { items: eventos } } as never)

    render(<AuditoriaPage />)
    await screen.findByText('Ana Pérez')

    await user.selectOptions(
      screen.getByLabelText('Filtrar por tipo de evento'),
      'LOGIN',
    )
    await waitFor(() =>
      expect(mockedAuditoria.list).toHaveBeenCalledWith({
        page: 1,
        page_size: 50,
        evento_tipo: 'LOGIN',
      }),
    )

    await user.selectOptions(screen.getByLabelText('Filtrar por recurso'), 'USUARIO')
    await waitFor(() =>
      expect(mockedAuditoria.list).toHaveBeenCalledWith({
        page: 1,
        page_size: 50,
        evento_tipo: 'LOGIN',
        recurso_tipo: 'USUARIO',
      }),
    )

    await user.selectOptions(screen.getByLabelText('Filtrar por resultado'), 'FALLIDO')
    await waitFor(() =>
      expect(mockedAuditoria.list).toHaveBeenCalledWith({
        page: 1,
        page_size: 50,
        evento_tipo: 'LOGIN',
        recurso_tipo: 'USUARIO',
        resultado: 'FALLIDO',
      }),
    )
  })
})
