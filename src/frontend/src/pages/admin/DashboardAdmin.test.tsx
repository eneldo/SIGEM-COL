import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { dashboard } from '../../lib/api'
import { DashboardAdmin } from './DashboardAdmin'

vi.mock('../../lib/api', () => ({
  dashboard: {
    adminKpis: vi.fn(),
    adminAlertas: vi.fn(),
  },
  default: {},
}))

const mockedDashboard = vi.mocked(dashboard)

const kpis = {
  total_gestores: 10,
  gestores_activos: 8,
  gestores_inactivos: 1,
  gestores_bloqueados: 1,
  total_lineas_estrategicas: 4,
  total_programas: 12,
  total_productos: 48,
  total_dependencias: 9,
}

const alertas = [
  {
    tipo: 'intentos_fallidos',
    severidad: 'ALTA',
    gestor_id: 'g1',
    gestor_codigo: 'GES-01',
    gestor_nombre: 'María López',
    mensaje: 'Cinco intentos fallidos de acceso',
    valor: 5,
    detectado_en: '2026-03-01T10:00:00Z',
  },
  {
    tipo: 'sin_acceso',
    severidad: 'MEDIA',
    mensaje: 'Sin acceso registrado en los últimos treinta días',
    detectado_en: '2026-03-02T10:00:00Z',
  },
]

function renderDashboard() {
  return render(
    <MemoryRouter
      initialEntries={['/admin']}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <Routes>
        <Route path="/admin" element={<DashboardAdmin />} />
        <Route path="/admin/gestores" element={<div>sección de gestores</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

function prepararExito(listaAlertas: unknown[]) {
  mockedDashboard.adminKpis.mockResolvedValue({ data: kpis } as never)
  mockedDashboard.adminAlertas.mockResolvedValue({
    data: { alertas: listaAlertas, total: listaAlertas.length },
  } as never)
}

function prepararFallo() {
  mockedDashboard.adminKpis.mockRejectedValue(new Error('fallo') as never)
  mockedDashboard.adminAlertas.mockRejectedValue(new Error('fallo') as never)
}

beforeEach(() => {
  mockedDashboard.adminKpis.mockReset()
  mockedDashboard.adminAlertas.mockReset()
})

describe('DashboardAdmin', () => {
  it('muestra los esqueletos mientras carga los datos', () => {
    mockedDashboard.adminKpis.mockReturnValue(new Promise(() => {}) as never)
    mockedDashboard.adminAlertas.mockReturnValue(new Promise(() => {}) as never)

    renderDashboard()

    expect(screen.getAllByText('—')).toHaveLength(5)
    expect(screen.getByLabelText('Cargando alertas')).toBeInTheDocument()
    expect(screen.getByText('0 pendientes')).toBeInTheDocument()
    expect(
      screen.getByRole('heading', { name: 'Dashboard administrativo' }),
    ).toBeInTheDocument()
  })

  it('presenta los KPIs, el listado de alertas y la capacidad operativa', async () => {
    prepararExito(alertas)

    renderDashboard()

    expect(await screen.findByText('María López')).toBeInTheDocument()
    expect(screen.getByText('10')).toBeInTheDocument()
    expect(screen.getByText('4')).toBeInTheDocument()
    expect(screen.getByText('12')).toBeInTheDocument()
    expect(screen.getByText('48')).toBeInTheDocument()
    expect(screen.getByText('9')).toBeInTheDocument()
    expect(screen.getByText('2 pendientes')).toBeInTheDocument()
    expect(screen.getByText('80%')).toBeInTheDocument()
    expect(screen.getAllByText('8 activos')).toHaveLength(2)
    expect(screen.getByText('1 inactivos')).toBeInTheDocument()
    expect(screen.getByText('1 bloqueados')).toBeInTheDocument()
    expect(
      screen.getByText('Alerta de seguridad'),
    ).toBeInTheDocument()
    expect(
      screen.getByText('Sin acceso registrado en los últimos treinta días'),
    ).toBeInTheDocument()
    expect(screen.queryByRole('status')).toBeNull()
  })

  it('muestra el estado vacío cuando no hay alertas pendientes', async () => {
    prepararExito([])

    renderDashboard()

    expect(await screen.findByText('Todo está al día')).toBeInTheDocument()
    expect(screen.getByText('0 pendientes')).toBeInTheDocument()
    expect(
      screen.getByText(
        'No hay alertas pendientes que requieran atención inmediata.',
      ),
    ).toBeInTheDocument()
    expect(screen.queryByText('María López')).toBeNull()
  })

  it('muestra el aviso cuando los indicadores no pudieron cargarse', async () => {
    prepararFallo()

    renderDashboard()

    const aviso = await screen.findByRole('status')
    expect(aviso).toHaveTextContent(
      'Algunos indicadores no pudieron actualizarse. Los datos disponibles siguen visibles.',
    )
    expect(screen.getByText('0%')).toBeInTheDocument()
    expect(screen.queryByText('María López')).toBeNull()
  })

  it('navega a la sección de gestores y muestra los accesos rápidos', async () => {
    const user = userEvent.setup()
    prepararExito(alertas)

    renderDashboard()
    await screen.findByText('María López')

    expect(
      screen.getByRole('link', { name: 'Líneas' }),
    ).toHaveAttribute('href', '/admin/lineas')
    expect(
      screen.getByRole('link', { name: 'Programas' }),
    ).toHaveAttribute('href', '/admin/programas')
    expect(
      screen.getByRole('link', { name: 'Productos' }),
    ).toHaveAttribute('href', '/admin/productos')
    expect(
      screen.getByRole('link', { name: 'Gestores' }),
    ).toHaveAttribute('href', '/admin/gestores')

    await user.click(screen.getByRole('link', { name: 'Administrar gestores' }))

    expect(await screen.findByText('sección de gestores')).toBeInTheDocument()
  })
})
