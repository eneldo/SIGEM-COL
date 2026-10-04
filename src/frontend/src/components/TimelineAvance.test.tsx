import { render, screen, waitFor, within } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { gestorDashboard } from '../lib/api'
import type { Evidencia } from '../lib/types'
import TimelineAvance from './TimelineAvance'

vi.mock('../lib/api', () => ({
  gestorDashboard: {
    listarEvidencias: vi.fn(),
  },
  default: {},
}))

const listar = vi.mocked(gestorDashboard.listarEvidencias)

type Avance = Parameters<typeof TimelineAvance>[0]['avance']

function crearAvance(overrides: Partial<Avance> = {}): Avance {
  return {
    id: 'av-1',
    avance_porcentaje: 50,
    avance_valor: null,
    observaciones: null,
    periodo: null,
    fecha_registro: null,
    estado_revision: 'PENDIENTE',
    observaciones_revision: null,
    created_at: '2026-03-01T10:00:00.000Z',
    evidencia_nombre: null,
    ...overrides,
  }
}

function crearEvidencia(overrides: Partial<Evidencia> = {}): Evidencia {
  return {
    id: 'ev-1',
    avance_id: 'av-1',
    nombre: 'acta.pdf',
    tipo: 'application/pdf',
    url: '/media/acta.pdf',
    descripcion: null,
    tamano_original: 1024,
    tamano_almacenado: 512,
    optimizada: false,
    created_at: '2026-03-02T09:00:00.000Z',
    ...overrides,
  }
}

function montarTimeline(avance: Avance) {
  return render(<TimelineAvance avanceId="av-1" avance={avance} />)
}

beforeEach(() => {
  listar.mockReset()
  listar.mockResolvedValue({ data: [] } as never)
})

describe('TimelineAvance', () => {
  it('registra el avance con su porcentaje de cumplimiento', async () => {
    montarTimeline(crearAvance())

    expect(await screen.findByText('Avance registrado')).toBeInTheDocument()
    expect(screen.getByText(/50% de cumplimiento/)).toBeInTheDocument()
    expect(screen.getByText('Pendiente de revisión')).toBeInTheDocument()
    expect(screen.getByText('0 evidencias')).toBeInTheDocument()
    expect(listar).toHaveBeenCalledWith('av-1')
  })

  it('incluye valor y período cuando el avance los tiene', async () => {
    montarTimeline(
      crearAvance({ avance_valor: 12.5, periodo: '2026-T1', avance_porcentaje: 80 }),
    )

    const detalle = await screen.findByText(/80% de cumplimiento/)
    expect(detalle).toHaveTextContent('80% de cumplimiento · Valor: 12.5 · Período: 2026-T1')
  })

  it('agrega el evento de observaciones del gestor', async () => {
    montarTimeline(crearAvance({ observaciones: 'Falta soporte firmado' }))

    expect(await screen.findByText('Observaciones del gestor')).toBeInTheDocument()
    expect(screen.getByText('Falta soporte firmado')).toBeInTheDocument()
  })

  it('muestra la evidencia en singular', async () => {
    listar.mockResolvedValue({
      data: [crearEvidencia({ id: 'ev-unica', nombre: 'informe.pdf' })],
    } as never)

    montarTimeline(crearAvance())

    expect(await screen.findByText('1 evidencia')).toBeInTheDocument()
    expect(screen.getByText('Evidencia: informe.pdf')).toBeInTheDocument()
  })

  it('lista varias evidencias con y sin descripción', async () => {
    listar.mockResolvedValue({
      data: [
        crearEvidencia({ id: 'ev-1', nombre: 'acta.pdf', descripcion: 'Acta del comité' }),
        crearEvidencia({ id: 'ev-2', nombre: 'foto.png', descripcion: null }),
      ],
    } as never)

    montarTimeline(crearAvance())

    expect(await screen.findByText('2 evidencias')).toBeInTheDocument()
    expect(screen.getByText('Evidencia: acta.pdf')).toBeInTheDocument()
    expect(screen.getByText('Acta del comité')).toBeInTheDocument()
    expect(screen.getByText('Evidencia: foto.png')).toBeInTheDocument()
  })

  it('muestra la revisión aprobada con su observación', async () => {
    montarTimeline(
      crearAvance({
        estado_revision: 'APROBADO',
        observaciones_revision: 'Sin observaciones',
        fecha_registro: '2026-03-05T12:00:00.000Z',
      }),
    )

    expect(await screen.findByText('Revisión: Aprobado')).toBeInTheDocument()
    expect(screen.getByText('Sin observaciones')).toBeInTheDocument()
    expect(screen.getByText('Aprobado')).toBeInTheDocument()
  })

  it('muestra la revisión devuelta al gestor', async () => {
    montarTimeline(
      crearAvance({
        estado_revision: 'DEVUELTO',
        observaciones_revision: 'Corregir el indicador',
        fecha_registro: '2026-03-06T12:00:00.000Z',
      }),
    )

    expect(await screen.findByText('Revisión: Devuelto')).toBeInTheDocument()
    expect(screen.getByText('Corregir el indicador')).toBeInTheDocument()
    expect(screen.getByText('Devuelto')).toBeInTheDocument()
  })

  it('usa el estado crudo cuando no está en el catálogo', async () => {
    montarTimeline(
      crearAvance({
        estado_revision: 'EN_VIAJE',
        fecha_registro: '2026-03-07T12:00:00.000Z',
      }),
    )

    expect(await screen.findByText('Revisión: EN_VIAJE')).toBeInTheDocument()
    expect(screen.getByText('EN_VIAJE')).toBeInTheDocument()
  })

  it('omite la revisión mientras el avance no fue revisado', async () => {
    montarTimeline(crearAvance({ estado_revision: 'BORRADOR' }))

    expect(await screen.findByText('Borrador')).toBeInTheDocument()
    expect(screen.queryByText(/Revisión:/)).toBeNull()
  })

  it('ordena los eventos por fecha y marca los que no tienen fecha', async () => {
    listar.mockResolvedValue({
      data: [
        crearEvidencia({ id: 'ev-null', nombre: 'sin-fecha.pdf', created_at: null }),
        crearEvidencia({
          id: 'ev-date',
          nombre: 'con-fecha.pdf',
          created_at: '2026-02-01T08:00:00.000Z',
        }),
      ],
    } as never)

    montarTimeline(crearAvance({ created_at: '2026-03-01T10:00:00.000Z' }))

    expect(await screen.findByText('Evidencia: con-fecha.pdf')).toBeInTheDocument()
    const eventos = screen.getAllByRole('listitem')
    expect(eventos).toHaveLength(3)
    expect(within(eventos[0]).getByText('Evidencia: con-fecha.pdf')).toBeInTheDocument()
    expect(within(eventos[1]).getByText('Avance registrado')).toBeInTheDocument()
    expect(within(eventos[2]).getByText('Evidencia: sin-fecha.pdf')).toBeInTheDocument()
    expect(within(eventos[2]).getByText('—')).toBeInTheDocument()
  })

  it('mantiene el listado vacío cuando la consulta falla', async () => {
    listar.mockRejectedValue(new Error('network') as never)

    montarTimeline(crearAvance())

    await waitFor(() => expect(listar).toHaveBeenCalledTimes(1))
    expect(await screen.findByText('Avance registrado')).toBeInTheDocument()
    expect(screen.getByText('0 evidencias')).toBeInTheDocument()
    expect(screen.queryByText(/^Evidencia:/)).toBeNull()
  })
})
