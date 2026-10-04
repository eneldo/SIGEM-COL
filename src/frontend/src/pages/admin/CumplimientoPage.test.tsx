import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { cumplimiento } from '../../lib/api'
import CumplimientoPage from './CumplimientoPage'

vi.mock('../../lib/api', () => ({
  cumplimiento: {
    general: vi.fn(),
    porLinea: vi.fn(),
    porPrograma: vi.fn(),
    productos: vi.fn(),
  },
  default: {},
}))

const mockedCumplimiento = vi.mocked(cumplimiento)

const general = {
  total_productos: 48,
  con_meta_definida: 40,
  sin_meta_definida: 8,
  completados: 20,
  en_progreso: 15,
  sin_avance: 13,
  porcentaje_cumplimiento_general: 75,
}

const lineas = [
  {
    id: 'l1',
    codigo: 'L-01',
    nombre: 'Línea Uno',
    total_productos: 21,
    con_meta_definida: 20,
    completados: 12,
    en_progreso: 5,
    sin_avance: 4,
    porcentaje_cumplimiento: 100,
  },
  {
    id: 'l2',
    codigo: 'L-02',
    nombre: 'Línea Dos',
    total_productos: 16,
    con_meta_definida: 14,
    completados: 6,
    en_progreso: 6,
    sin_avance: 4,
    porcentaje_cumplimiento: 45,
  },
  {
    id: 'l3',
    codigo: 'L-03',
    nombre: 'Línea Tres',
    total_productos: 11,
    con_meta_definida: 6,
    completados: 2,
    en_progreso: 4,
    sin_avance: 5,
    porcentaje_cumplimiento: 0,
  },
]

const programas = [
  {
    id: 'pg1',
    codigo: 'PG-01',
    nombre: 'Programa Uno',
    linea_nombre: 'Línea Uno',
    total_productos: 10,
    con_meta_definida: 9,
    completados: 7,
    en_progreso: 2,
    sin_avance: 1,
    porcentaje_cumplimiento: 100,
  },
  {
    id: 'pg2',
    codigo: 'PG-02',
    nombre: 'Programa Dos',
    linea_nombre: 'Línea Dos',
    total_productos: 8,
    con_meta_definida: 6,
    completados: 2,
    en_progreso: 3,
    sin_avance: 3,
    porcentaje_cumplimiento: 30,
  },
]

const productos = [
  {
    id: 'pr1',
    codigo: 'PR-01',
    nombre: 'Producto Alfa',
    indicador: 'Indicador A',
    linea_base: 10,
    meta_cuatrienio: 100,
    programa_nombre: 'Programa Uno',
    linea_nombre: 'Línea Uno',
    porcentaje_avance: 100,
    estado_cumplimiento: 'COMPLETADO',
  },
  {
    id: 'pr2',
    codigo: 'PR-02',
    nombre: 'Producto Beta',
    indicador: null,
    linea_base: null,
    meta_cuatrienio: null,
    programa_nombre: 'Programa Dos',
    linea_nombre: 'Línea Dos',
    porcentaje_avance: 45,
    estado_cumplimiento: 'EN_PROGRESO',
  },
  {
    id: 'pr3',
    codigo: 'PR-03',
    nombre: 'Producto Gamma',
    indicador: 'Indicador C',
    linea_base: 5,
    meta_cuatrienio: 50,
    programa_nombre: 'Programa Uno',
    linea_nombre: 'Línea Uno',
    porcentaje_avance: 0,
    estado_cumplimiento: 'SIN_AVANCE',
  },
  {
    id: 'pr4',
    codigo: 'PR-04',
    nombre: 'Producto Delta',
    indicador: null,
    linea_base: null,
    meta_cuatrienio: null,
    programa_nombre: 'Programa Dos',
    linea_nombre: 'Línea Dos',
    porcentaje_avance: 0,
    estado_cumplimiento: 'SIN_META',
  },
  {
    id: 'pr5',
    codigo: 'PR-05',
    nombre: 'Producto Épsilon',
    indicador: 'Indicador E',
    linea_base: 2,
    meta_cuatrienio: 20,
    programa_nombre: 'Programa Uno',
    linea_nombre: 'Línea Uno',
    porcentaje_avance: 80,
    estado_cumplimiento: 'REVISAR',
  },
]

function prepararPendiente() {
  mockedCumplimiento.general.mockReturnValue(new Promise(() => {}) as never)
  mockedCumplimiento.porLinea.mockReturnValue(new Promise(() => {}) as never)
  mockedCumplimiento.porPrograma.mockReturnValue(new Promise(() => {}) as never)
  mockedCumplimiento.productos.mockReturnValue(new Promise(() => {}) as never)
}

function prepararExito(datos: {
  lineas: unknown
  programas: unknown
  productos: unknown
}) {
  mockedCumplimiento.general.mockResolvedValue({ data: general } as never)
  mockedCumplimiento.porLinea.mockResolvedValue({ data: datos.lineas } as never)
  mockedCumplimiento.porPrograma.mockResolvedValue({
    data: datos.programas,
  } as never)
  mockedCumplimiento.productos.mockResolvedValue({ data: datos.productos } as never)
}

function prepararFallo() {
  mockedCumplimiento.general.mockRejectedValue(new Error('fallo') as never)
  mockedCumplimiento.porLinea.mockRejectedValue(new Error('fallo') as never)
  mockedCumplimiento.porPrograma.mockRejectedValue(new Error('fallo') as never)
  mockedCumplimiento.productos.mockRejectedValue(new Error('fallo') as never)
}

const datosCompletos = { lineas, programas, productos }

beforeEach(() => {
  mockedCumplimiento.general.mockReset()
  mockedCumplimiento.porLinea.mockReset()
  mockedCumplimiento.porPrograma.mockReset()
  mockedCumplimiento.productos.mockReset()
})

describe('CumplimientoPage', () => {
  it('muestra el estado de carga al iniciar', () => {
    prepararPendiente()

    render(<CumplimientoPage />)

    expect(screen.getByText('Cargando cumplimiento...')).toBeInTheDocument()
  })

  it('muestra el error de carga y permite reintentar', async () => {
    const user = userEvent.setup()
    vi.spyOn(console, 'error').mockImplementation(() => {})
    prepararFallo()

    render(<CumplimientoPage />)

    expect(
      await screen.findByText('Error al cargar datos de cumplimiento'),
    ).toBeInTheDocument()

    prepararExito(datosCompletos)
    await user.click(screen.getByRole('button', { name: 'Reintentar' }))

    expect(await screen.findByText('Cumplimiento de Metas')).toBeInTheDocument()
    expect(screen.getByText('48')).toBeInTheDocument()
  })

  it('presenta las tarjetas de resumen y el cumplimiento general', async () => {
    prepararExito(datosCompletos)

    render(<CumplimientoPage />)

    expect(await screen.findByText('Cumplimiento de Metas')).toBeInTheDocument()
    expect(screen.getByText('Total Productos')).toBeInTheDocument()
    expect(screen.getByText('48')).toBeInTheDocument()
    expect(screen.getByText('75%')).toBeInTheDocument()
    expect(screen.getByText(/productos con meta definida/)).toBeInTheDocument()
    expect(screen.getByText(/productos sin meta/)).toBeInTheDocument()
    expect(screen.getAllByText('Completados')).toHaveLength(2)
    expect(screen.getAllByText('En Progreso')).toHaveLength(2)
    expect(screen.getAllByText('Sin Avance')).toHaveLength(2)

    const tabla = screen.getByRole('table')
    expect(within(tabla).getByText('L-01')).toBeInTheDocument()
    expect(within(tabla).getByText('Línea Uno')).toBeInTheDocument()
    expect(within(tabla).getByText('100%')).toBeInTheDocument()
    expect(within(tabla).getByText('45%')).toBeInTheDocument()
    expect(within(tabla).getByText('0%')).toBeInTheDocument()
  })

  it('cambia entre las pestañas de línea, programa y productos', async () => {
    const user = userEvent.setup()
    prepararExito(datosCompletos)

    render(<CumplimientoPage />)
    await screen.findByText('L-01')

    await user.click(screen.getByRole('button', { name: 'Por Programa' }))
    expect(await screen.findByText('PG-01')).toBeInTheDocument()
    expect(screen.getByText('Programa Dos')).toBeInTheDocument()
    expect(screen.getByText('Línea Dos')).toBeInTheDocument()
    expect(screen.getByText('30%')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Todos los Productos' }))
    expect(await screen.findByText('PR-01')).toBeInTheDocument()
    expect(screen.getByText('Producto Alfa')).toBeInTheDocument()
    expect(screen.getAllByText('Programa Uno')).toHaveLength(3)
    expect(screen.getByText('REVISAR')).toBeInTheDocument()
    expect(screen.getAllByText('-').length).toBeGreaterThan(0)
  })

  it('filtra los productos por estado de cumplimiento', async () => {
    const user = userEvent.setup()
    prepararExito(datosCompletos)

    render(<CumplimientoPage />)
    await screen.findByText('L-01')

    await user.click(screen.getByRole('button', { name: 'Todos los Productos' }))
    expect(await screen.findByText('Producto Épsilon')).toBeInTheDocument()
    expect(screen.getByText('Producto Alfa')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Completados' }))
    expect(screen.getByText('Producto Alfa')).toBeInTheDocument()
    expect(screen.queryByText('Producto Beta')).toBeNull()

    await user.click(screen.getByRole('button', { name: 'En Progreso' }))
    expect(screen.getByText('Producto Beta')).toBeInTheDocument()
    expect(screen.queryByText('Producto Alfa')).toBeNull()

    await user.click(screen.getByRole('button', { name: 'Sin Avance' }))
    expect(screen.getByText('Producto Gamma')).toBeInTheDocument()
    expect(screen.queryByText('Producto Beta')).toBeNull()

    await user.click(screen.getByRole('button', { name: 'Sin Meta' }))
    expect(screen.getByText('Producto Delta')).toBeInTheDocument()
    expect(screen.queryByText('Producto Gamma')).toBeNull()

    await user.click(screen.getByRole('button', { name: 'Todos' }))
    expect(screen.getByText('Producto Épsilon')).toBeInTheDocument()
    expect(screen.getByText('Producto Alfa')).toBeInTheDocument()
  })

  it('muestra los estados vacíos de las tablas y del filtro de productos', async () => {
    const user = userEvent.setup()
    prepararExito({ lineas: [], programas: [], productos: [productos[0]] })

    render(<CumplimientoPage />)

    expect(await screen.findByText('No hay datos disponibles')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Por Programa' }))
    expect(await screen.findByText('No hay datos disponibles')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Todos los Productos' }))
    expect(await screen.findByText('Producto Alfa')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Sin Meta' }))
    expect(
      screen.getByText('No hay productos con este filtro'),
    ).toBeInTheDocument()
  })
})
