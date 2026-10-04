import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { dashboard, lineas } from '../../lib/api'
import { LineasPage } from './LineasPage'

vi.mock('../../lib/api', () => ({
  lineas: { list: vi.fn(), create: vi.fn(), update: vi.fn(), delete: vi.fn() },
  dashboard: { adminResumenPlan: vi.fn() },
  default: {},
}))

const mockedLineas = vi.mocked(lineas)
const mockedDashboard = vi.mocked(dashboard)

function respuesta(data: unknown) {
  return { data } as never
}

const plan = {
  plan: {
    id: 'pl1',
    codigo: 'PD-2024',
    nombre: 'Plan Municipal 2024',
    fecha_inicio: '2024-01-01',
    fecha_fin: '2027-12-31',
    vigencias: 4,
    estado: 'ACTIVO',
  },
  total_lineas_estrategicas: 2,
  total_programas: 3,
  total_productos: 4,
  lineas_desglose: [],
}

const linea1 = {
  id: 'l1',
  codigo: 'LIN-01',
  numero: '001',
  nombre: 'Gobierno',
  descripcion: 'Eje de gobierno',
  orden: 1,
  estado: 'ACTIVA',
  municipio_id: 'm1',
  plan_desarrollo_id: 'pl1',
  plan_desarrollo_nombre: 'Plan Municipal 2024',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-02-01T00:00:00Z',
}

const linea2 = {
  id: 'l2',
  codigo: 'LIN-02',
  nombre: 'Salud',
  orden: 2,
  estado: 'INACTIVA',
  municipio_id: 'm1',
  plan_desarrollo_id: 'pl1',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-02-01T00:00:00Z',
}

function filaDe(nombre: string) {
  const fila = screen.getByText(nombre).closest('tr')
  return within(fila as HTMLElement)
}

function dialogo() {
  return screen.getByRole('dialog')
}

async function abrirCreacion(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole('button', { name: 'Nueva línea' }))
  return dialogo()
}

beforeEach(() => {
  mockedLineas.list.mockResolvedValue(respuesta({ items: [linea1, linea2], total: 2, page: 1, page_size: 100 }))
  mockedLineas.create.mockResolvedValue(respuesta(linea1))
  mockedLineas.update.mockResolvedValue(respuesta(linea1))
  mockedLineas.delete.mockResolvedValue(respuesta(null))
  mockedDashboard.adminResumenPlan.mockResolvedValue(respuesta(plan))
})

describe('LineasPage', () => {
  it('muestra el estado de carga inicial', () => {
    mockedLineas.list.mockReturnValue(new Promise(() => {}) as never)

    render(<LineasPage />)

    expect(screen.getByText('Cargando líneas estratégicas...')).toBeInTheDocument()
  })

  it('renderiza las líneas estratégicas con el plan y las tarjetas de resumen', async () => {
    render(<LineasPage />)

    expect(await screen.findByText('Gobierno')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Líneas estratégicas' })).toBeInTheDocument()
    expect(screen.getByText('Salud')).toBeInTheDocument()
    expect(screen.getByText(/PD-2024/)).toBeInTheDocument()
    expect(screen.getByText(/4 vigencias/)).toBeInTheDocument()
    expect(screen.getByText('Las líneas nuevas se asocian automáticamente a este plan.')).toBeInTheDocument()
    expect(screen.getByText('Total de líneas')).toBeInTheDocument()
    expect(screen.getByText('Activas')).toBeInTheDocument()
    expect(screen.getByText('Inactivas')).toBeInTheDocument()
    expect(filaDe('Gobierno').getByText('LIN-01')).toBeInTheDocument()
    expect(filaDe('Gobierno').getByText('001')).toBeInTheDocument()
    expect(filaDe('Gobierno').getByText('Eje de gobierno')).toBeInTheDocument()
    expect(filaDe('Gobierno').getByText('ACTIVA')).toBeInTheDocument()
    expect(filaDe('Salud').getByText('-')).toBeInTheDocument()
    expect(filaDe('Salud').getByText('INACTIVA')).toBeInTheDocument()
    expect(filaDe('Salud').getByText('Plan Municipal 2024')).toBeInTheDocument()
  })

  it('muestra el mensaje de vacío cuando no hay líneas', async () => {
    mockedLineas.list.mockResolvedValue(respuesta({ items: [], total: 0, page: 1, page_size: 100 }))

    render(<LineasPage />)

    expect(await screen.findByText('No hay líneas que coincidan con la búsqueda.')).toBeInTheDocument()
  })

  it('muestra un error cuando la carga de líneas falla', async () => {
    mockedLineas.list.mockRejectedValue(new Error('fallo') as never)

    render(<LineasPage />)

    expect(await screen.findByText('No fue posible cargar las líneas estratégicas.')).toBeInTheDocument()
  })

  it('permite buscar líneas por código o nombre', async () => {
    const user = userEvent.setup()
    render(<LineasPage />)
    await screen.findByText('Gobierno')

    await user.type(screen.getByLabelText('Buscar líneas'), 'gob')

    await waitFor(() => {
      expect(mockedLineas.list).toHaveBeenCalledWith(expect.objectContaining({ search: 'gob' }))
    })
  })

  it('recarga la lista con el botón Actualizar', async () => {
    const user = userEvent.setup()
    render(<LineasPage />)
    await screen.findByText('Gobierno')

    await user.click(screen.getByRole('button', { name: 'Actualizar' }))

    await waitFor(() => {
      expect(mockedLineas.list).toHaveBeenCalledTimes(2)
    })
  })

  it('deshabilita la creación cuando no hay plan de desarrollo', async () => {
    mockedDashboard.adminResumenPlan.mockRejectedValue(new Error('sin plan') as never)

    render(<LineasPage />)

    expect(await screen.findByText('Gobierno')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Nueva línea' })).toBeDisabled()
    expect(screen.queryByText('Las líneas nuevas se asocian automáticamente a este plan.')).not.toBeInTheDocument()
  })

  it('crea una línea estratégica asociada al plan', async () => {
    const user = userEvent.setup()
    render(<LineasPage />)
    await screen.findByText('Gobierno')

    const modal = await abrirCreacion(user)

    expect(within(modal).getByText(/Se asociará al plan Plan Municipal 2024/)).toBeInTheDocument()
    expect(within(modal).getByRole('button', { name: 'Crear línea' })).toBeDisabled()

    await user.type(within(modal).getByPlaceholderText('Ej: 001'), '002')
    await user.type(within(modal).getByPlaceholderText('Nombre de la línea estratégica'), 'Nueva línea')
    await user.type(within(modal).getByPlaceholderText('Objetivo del eje estratégico'), 'Descripción nueva')

    expect(within(modal).getByRole('button', { name: 'Crear línea' })).toBeEnabled()

    await user.click(within(modal).getByRole('button', { name: 'Crear línea' }))

    await waitFor(() => {
      expect(mockedLineas.create).toHaveBeenCalledWith({
        numero: '002',
        nombre: 'Nueva línea',
        descripcion: 'Descripción nueva',
        plan_desarrollo_id: 'pl1',
      })
    })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('edita una línea estratégica existente', async () => {
    const user = userEvent.setup()
    render(<LineasPage />)
    await screen.findByText('Gobierno')

    await user.click(filaDe('Gobierno').getByRole('button', { name: 'Editar' }))

    const modal = dialogo()
    expect(within(modal).getByText(/Actualice la información de "Gobierno"/)).toBeInTheDocument()
    expect(within(modal).getByText('LIN-01')).toBeInTheDocument()

    const campos = within(modal).getAllByRole('textbox')
    await user.clear(campos[1])
    await user.type(campos[1], 'Gobierno Local')

    await user.click(within(modal).getByRole('button', { name: 'Guardar cambios' }))

    await waitFor(() => {
      expect(mockedLineas.update).toHaveBeenCalledWith('l1', {
        numero: '001',
        nombre: 'Gobierno Local',
        descripcion: 'Eje de gobierno',
      })
    })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('muestra el detalle del error devuelto por el backend', async () => {
    const user = userEvent.setup()
    mockedLineas.create.mockRejectedValue({ response: { data: { detail: 'La línea ya existe' } } } as never)
    render(<LineasPage />)
    await screen.findByText('Gobierno')

    const modal = await abrirCreacion(user)
    await user.type(within(modal).getByPlaceholderText('Nombre de la línea estratégica'), 'Repetida')
    await user.click(within(modal).getByRole('button', { name: 'Crear línea' }))

    expect(await screen.findByText('La línea ya existe')).toBeInTheDocument()
  })

  it('muestra un mensaje de validación cuando el backend devuelve una lista de errores', async () => {
    const user = userEvent.setup()
    mockedLineas.create.mockRejectedValue({ response: { data: { detail: [{ msg: 'inválido' }] } } } as never)
    render(<LineasPage />)
    await screen.findByText('Gobierno')

    const modal = await abrirCreacion(user)
    await user.type(within(modal).getByPlaceholderText('Nombre de la línea estratégica'), 'Repetida')
    await user.click(within(modal).getByRole('button', { name: 'Crear línea' }))

    expect(await screen.findByText('Verifique los campos del formulario')).toBeInTheDocument()
  })

  it('muestra un error genérico cuando la falla no trae detalle', async () => {
    const user = userEvent.setup()
    mockedLineas.create.mockRejectedValue(new Error('sin detalle') as never)
    render(<LineasPage />)
    await screen.findByText('Gobierno')

    const modal = await abrirCreacion(user)
    await user.type(within(modal).getByPlaceholderText('Nombre de la línea estratégica'), 'Repetida')
    await user.click(within(modal).getByRole('button', { name: 'Crear línea' }))

    expect(await screen.findByText('No fue posible guardar los cambios.')).toBeInTheDocument()
  })

  it('elimina una línea estratégica tras confirmar', async () => {
    const user = userEvent.setup()
    const confirmar = vi.spyOn(window, 'confirm').mockReturnValue(true)
    render(<LineasPage />)
    await screen.findByText('Gobierno')

    await user.click(filaDe('Gobierno').getByRole('button', { name: 'Eliminar' }))

    await waitFor(() => {
      expect(confirmar).toHaveBeenCalled()
      expect(mockedLineas.delete).toHaveBeenCalledWith('l1')
    })
    await waitFor(() => {
      expect(mockedLineas.list).toHaveBeenCalledTimes(2)
    })
  })

  it('no elimina la línea si el usuario cancela la confirmación', async () => {
    const user = userEvent.setup()
    vi.spyOn(window, 'confirm').mockReturnValue(false)
    render(<LineasPage />)
    await screen.findByText('Gobierno')

    await user.click(filaDe('Gobierno').getByRole('button', { name: 'Eliminar' }))

    expect(mockedLineas.delete).not.toHaveBeenCalled()
  })

  it('muestra un error cuando la eliminación falla', async () => {
    const user = userEvent.setup()
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    mockedLineas.delete.mockRejectedValue(new Error('fallo') as never)
    render(<LineasPage />)
    await screen.findByText('Gobierno')

    await user.click(filaDe('Gobierno').getByRole('button', { name: 'Eliminar' }))

    expect(await screen.findByText('No fue posible eliminar la línea estratégica.')).toBeInTheDocument()
  })

  it('cierra los modales con el botón Cancelar', async () => {
    const user = userEvent.setup()
    render(<LineasPage />)
    await screen.findByText('Gobierno')

    const creacion = await abrirCreacion(user)
    await user.click(within(creacion).getByRole('button', { name: 'Cancelar' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()

    await user.click(filaDe('Gobierno').getByRole('button', { name: 'Editar' }))
    const edicion = dialogo()
    await user.click(within(edicion).getByRole('button', { name: 'Cancelar' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('cierra el modal con el botón de cierre', async () => {
    const user = userEvent.setup()
    render(<LineasPage />)
    await screen.findByText('Gobierno')

    const modal = await abrirCreacion(user)
    await user.click(within(modal).getByRole('button', { name: 'Cerrar' }))

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('cierra el modal al hacer clic en el fondo', async () => {
    const user = userEvent.setup()
    render(<LineasPage />)
    await screen.findByText('Gobierno')

    const modal = await abrirCreacion(user)
    fireEvent.mouseDown(modal.parentElement as HTMLElement)

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
