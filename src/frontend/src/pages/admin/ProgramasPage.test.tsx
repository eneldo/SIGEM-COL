import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { lineas, programas } from '../../lib/api'
import { ProgramasPage } from './ProgramasPage'

vi.mock('../../lib/api', () => ({
  programas: { list: vi.fn(), create: vi.fn(), update: vi.fn(), delete: vi.fn() },
  lineas: { list: vi.fn() },
  default: {},
}))

const mockedProgramas = vi.mocked(programas)
const mockedLineas = vi.mocked(lineas)

function respuesta(data: unknown) {
  return { data } as never
}

const linea = {
  id: 'l1',
  codigo: 'LIN-01',
  numero: '001',
  nombre: 'Gobierno',
  orden: 1,
  estado: 'ACTIVA',
  municipio_id: 'm1',
  plan_desarrollo_id: 'pl1',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-02-01T00:00:00Z',
}

const programa1 = {
  id: 'pg1',
  codigo: '1903',
  nombre: 'Programa Salud',
  sector: 'Salud',
  descripcion: 'Atención primaria',
  estado: 'ACTIVO',
  municipio_id: 'm1',
  linea_estrategica_id: 'l1',
  linea_estrategica_nombre: 'Gobierno',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-02-01T00:00:00Z',
}

const programa2 = {
  id: 'pg2',
  codigo: '2001',
  nombre: 'Programa Educación',
  estado: 'INACTIVO',
  municipio_id: 'm1',
  linea_estrategica_id: 'l2',
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

beforeEach(() => {
  mockedProgramas.list.mockResolvedValue(respuesta({ items: [programa1, programa2], total: 2, page: 1, page_size: 100 }))
  mockedProgramas.create.mockResolvedValue(respuesta(programa1))
  mockedProgramas.update.mockResolvedValue(respuesta(programa1))
  mockedProgramas.delete.mockResolvedValue(respuesta(null))
  mockedLineas.list.mockResolvedValue(respuesta({ items: [linea], total: 1, page: 1, page_size: 100 }))
})

describe('ProgramasPage', () => {
  it('muestra el estado de carga inicial', () => {
    mockedProgramas.list.mockReturnValue(new Promise(() => {}) as never)

    render(<ProgramasPage />)

    expect(screen.getByText('Cargando programas...')).toBeInTheDocument()
  })

  it('renderiza los programas con sus tarjetas de resumen y filtros', async () => {
    render(<ProgramasPage />)

    expect(await screen.findByText('Programa Salud')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Programas' })).toBeInTheDocument()
    expect(screen.getByText('Programa Educación')).toBeInTheDocument()
    expect(screen.getByText('Total de programas')).toBeInTheDocument()
    expect(screen.getByText('Activos')).toBeInTheDocument()
    expect(screen.getByText('Inactivos')).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Gobierno' })).toBeInTheDocument()
    expect(filaDe('Programa Salud').getByText('1903')).toBeInTheDocument()
    expect(filaDe('Programa Salud').getByText('Salud')).toBeInTheDocument()
    expect(filaDe('Programa Salud').getByText('Atención primaria')).toBeInTheDocument()
    expect(filaDe('Programa Salud').getByText('Gobierno')).toBeInTheDocument()
    expect(filaDe('Programa Salud').getByText('ACTIVO')).toBeInTheDocument()
    expect(filaDe('Programa Educación').getAllByText('-')).toHaveLength(2)
    expect(filaDe('Programa Educación').getByText('Sin línea')).toBeInTheDocument()
    expect(filaDe('Programa Educación').getByText('INACTIVO')).toBeInTheDocument()
  })

  it('muestra el mensaje de vacío cuando no hay programas', async () => {
    mockedProgramas.list.mockResolvedValue(respuesta({ items: [], total: 0, page: 1, page_size: 100 }))

    render(<ProgramasPage />)

    expect(await screen.findByText('No hay programas que coincidan con la búsqueda.')).toBeInTheDocument()
  })

  it('muestra un error cuando la carga de programas falla', async () => {
    mockedProgramas.list.mockRejectedValue(new Error('fallo') as never)

    render(<ProgramasPage />)

    expect(await screen.findByText('No fue posible cargar los programas.')).toBeInTheDocument()
  })

  it('permite buscar y filtrar por línea estratégica', async () => {
    const user = userEvent.setup()
    render(<ProgramasPage />)
    await screen.findByText('Programa Salud')

    await user.type(screen.getByLabelText('Buscar programas'), 'salud')
    await waitFor(() => {
      expect(mockedProgramas.list).toHaveBeenCalledWith(expect.objectContaining({ search: 'salud' }))
    })

    await user.selectOptions(screen.getByLabelText('Filtrar por línea estratégica'), 'l1')
    await waitFor(() => {
      expect(mockedProgramas.list).toHaveBeenCalledWith(expect.objectContaining({ linea_estrategica_id: 'l1' }))
    })
  })

  it('recarga la lista con el botón Actualizar', async () => {
    const user = userEvent.setup()
    render(<ProgramasPage />)
    await screen.findByText('Programa Salud')

    await user.click(screen.getByRole('button', { name: 'Actualizar' }))

    await waitFor(() => {
      expect(mockedProgramas.list).toHaveBeenCalledTimes(2)
    })
  })

  it('crea un programa asociado a una línea estratégica', async () => {
    const user = userEvent.setup()
    render(<ProgramasPage />)
    await screen.findByText('Programa Salud')

    await user.click(screen.getByRole('button', { name: 'Nuevo programa' }))

    const modal = dialogo()
    expect(within(modal).getByText(/El programa se asociará a una línea estratégica/)).toBeInTheDocument()
    expect(within(modal).getByRole('button', { name: 'Crear programa' })).toBeDisabled()

    const campos = within(modal).getAllByRole('textbox')
    await user.type(campos[0], '2101')
    await user.type(campos[1], 'Nuevo Programa')
    await user.type(campos[2], 'Seguridad')
    await user.type(campos[3], 'Descripción del programa')
    await user.selectOptions(within(modal).getByRole('combobox'), 'l1')

    expect(within(modal).getByRole('button', { name: 'Crear programa' })).toBeEnabled()

    await user.click(within(modal).getByRole('button', { name: 'Crear programa' }))

    await waitFor(() => {
      expect(mockedProgramas.create).toHaveBeenCalledWith({
        codigo: '2101',
        nombre: 'Nuevo Programa',
        sector: 'Seguridad',
        descripcion: 'Descripción del programa',
        linea_estrategica_id: 'l1',
      })
    })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('edita un programa sin permitir cambiar la línea estratégica', async () => {
    const user = userEvent.setup()
    render(<ProgramasPage />)
    await screen.findByText('Programa Salud')

    await user.click(filaDe('Programa Salud').getByRole('button', { name: 'Editar' }))

    const modal = dialogo()
    expect(within(modal).getByText(/Actualice la información de "Programa Salud"/)).toBeInTheDocument()
    expect(within(modal).getByText(/no se puede modificar en esta versión/)).toBeInTheDocument()
    expect(within(modal).queryByRole('combobox')).not.toBeInTheDocument()

    const campos = within(modal).getAllByRole('textbox')
    await user.clear(campos[1])
    await user.type(campos[1], 'Programa Salud Nuevo')

    await user.click(within(modal).getByRole('button', { name: 'Guardar cambios' }))

    await waitFor(() => {
      expect(mockedProgramas.update).toHaveBeenCalledWith('pg1', {
        codigo: '1903',
        nombre: 'Programa Salud Nuevo',
        sector: 'Salud',
        descripcion: 'Atención primaria',
      })
    })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('edita un programa que no tiene línea estratégica asignada', async () => {
    const user = userEvent.setup()
    render(<ProgramasPage />)
    await screen.findByText('Programa Salud')

    await user.click(filaDe('Programa Educación').getByRole('button', { name: 'Editar' }))

    const modal = dialogo()
    expect(within(modal).queryByText(/no se puede modificar en esta versión/)).not.toBeInTheDocument()
    expect(within(modal).getByRole('button', { name: 'Guardar cambios' })).toBeEnabled()

    await user.click(within(modal).getByRole('button', { name: 'Guardar cambios' }))

    await waitFor(() => {
      expect(mockedProgramas.update).toHaveBeenCalledWith('pg2', {
        codigo: '2001',
        nombre: 'Programa Educación',
        sector: '',
        descripcion: '',
      })
    })
  })

  it('muestra el detalle del error devuelto por el backend', async () => {
    const user = userEvent.setup()
    mockedProgramas.create.mockRejectedValue({ response: { data: { detail: 'El código ya existe' } } } as never)
    render(<ProgramasPage />)
    await screen.findByText('Programa Salud')

    await user.click(screen.getByRole('button', { name: 'Nuevo programa' }))
    const modal = dialogo()
    const campos = within(modal).getAllByRole('textbox')
    await user.type(campos[0], '1903')
    await user.type(campos[1], 'Repetido')
    await user.selectOptions(within(modal).getByRole('combobox'), 'l1')
    await user.click(within(modal).getByRole('button', { name: 'Crear programa' }))

    expect(await screen.findByText('El código ya existe')).toBeInTheDocument()
  })

  it('muestra un mensaje de validación cuando el backend devuelve una lista de errores', async () => {
    const user = userEvent.setup()
    mockedProgramas.create.mockRejectedValue({ response: { data: { detail: [{ msg: 'inválido' }] } } } as never)
    render(<ProgramasPage />)
    await screen.findByText('Programa Salud')

    await user.click(screen.getByRole('button', { name: 'Nuevo programa' }))
    const modal = dialogo()
    const campos = within(modal).getAllByRole('textbox')
    await user.type(campos[0], '1903')
    await user.type(campos[1], 'Repetido')
    await user.selectOptions(within(modal).getByRole('combobox'), 'l1')
    await user.click(within(modal).getByRole('button', { name: 'Crear programa' }))

    expect(await screen.findByText('Verifique los campos del formulario')).toBeInTheDocument()
  })

  it('muestra un error genérico cuando la falla no trae detalle', async () => {
    const user = userEvent.setup()
    mockedProgramas.create.mockRejectedValue(new Error('sin detalle') as never)
    render(<ProgramasPage />)
    await screen.findByText('Programa Salud')

    await user.click(screen.getByRole('button', { name: 'Nuevo programa' }))
    const modal = dialogo()
    const campos = within(modal).getAllByRole('textbox')
    await user.type(campos[0], '1903')
    await user.type(campos[1], 'Repetido')
    await user.selectOptions(within(modal).getByRole('combobox'), 'l1')
    await user.click(within(modal).getByRole('button', { name: 'Crear programa' }))

    expect(await screen.findByText('No fue posible guardar los cambios.')).toBeInTheDocument()
  })

  it('elimina un programa tras confirmar', async () => {
    const user = userEvent.setup()
    const confirmar = vi.spyOn(window, 'confirm').mockReturnValue(true)
    render(<ProgramasPage />)
    await screen.findByText('Programa Salud')

    await user.click(filaDe('Programa Salud').getByRole('button', { name: 'Eliminar' }))

    await waitFor(() => {
      expect(confirmar).toHaveBeenCalled()
      expect(mockedProgramas.delete).toHaveBeenCalledWith('pg1')
    })
  })

  it('no elimina el programa si el usuario cancela la confirmación', async () => {
    const user = userEvent.setup()
    vi.spyOn(window, 'confirm').mockReturnValue(false)
    render(<ProgramasPage />)
    await screen.findByText('Programa Salud')

    await user.click(filaDe('Programa Salud').getByRole('button', { name: 'Eliminar' }))

    expect(mockedProgramas.delete).not.toHaveBeenCalled()
  })

  it('muestra un error cuando la eliminación falla', async () => {
    const user = userEvent.setup()
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    mockedProgramas.delete.mockRejectedValue(new Error('fallo') as never)
    render(<ProgramasPage />)
    await screen.findByText('Programa Salud')

    await user.click(filaDe('Programa Salud').getByRole('button', { name: 'Eliminar' }))

    expect(await screen.findByText('No fue posible eliminar el programa.')).toBeInTheDocument()
  })

  it('cierra los modales con el botón Cancelar', async () => {
    const user = userEvent.setup()
    render(<ProgramasPage />)
    await screen.findByText('Programa Salud')

    await user.click(screen.getByRole('button', { name: 'Nuevo programa' }))
    await user.click(within(dialogo()).getByRole('button', { name: 'Cancelar' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()

    await user.click(filaDe('Programa Salud').getByRole('button', { name: 'Editar' }))
    await user.click(within(dialogo()).getByRole('button', { name: 'Cancelar' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('cierra el modal con el botón de cierre', async () => {
    const user = userEvent.setup()
    render(<ProgramasPage />)
    await screen.findByText('Programa Salud')

    await user.click(screen.getByRole('button', { name: 'Nuevo programa' }))
    await user.click(within(dialogo()).getByRole('button', { name: 'Cerrar' }))

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('cierra el modal al hacer clic en el fondo', async () => {
    const user = userEvent.setup()
    render(<ProgramasPage />)
    await screen.findByText('Programa Salud')

    await user.click(screen.getByRole('button', { name: 'Nuevo programa' }))
    const modal = dialogo()
    fireEvent.mouseDown(modal.parentElement as HTMLElement)

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('funciona aunque el catálogo de líneas no pueda cargarse', async () => {
    mockedLineas.list.mockRejectedValue(new Error('fallo') as never)

    render(<ProgramasPage />)

    expect(await screen.findByText('Programa Salud')).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Todas las líneas' })).toBeInTheDocument()
  })
})
