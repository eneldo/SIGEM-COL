import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { configDependencias } from '../../lib/api'
import DependenciasPage from './DependenciasPage'

vi.mock('../../lib/api', () => ({
  configDependencias: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
  default: {},
}))

const mockedDependencias = vi.mocked(configDependencias)

const dependencias = [
  {
    id: 'd1',
    municipio_id: 'm1',
    codigo: 'DEP-001',
    nombre: 'Secretaría de Planeación',
    descripcion: 'Planeación y desarrollo municipal',
    dependencia_padre_id: '',
    nivel: 1,
    estado: 'ACTIVA',
  },
  {
    id: 'd2',
    municipio_id: 'm1',
    codigo: 'DEP-002',
    nombre: 'Oficina de Talento Humano',
    dependencia_padre_id: 'd1',
    nivel: 2,
    estado: 'INACTIVA',
  },
  {
    id: 'd3',
    municipio_id: 'm1',
    codigo: 'DEP-003',
    nombre: 'Grupo de Sistemas',
    descripcion: 'Soporte tecnológico interno',
    dependencia_padre_id: 'no-existe',
    nivel: 3,
    estado: 'ACTIVA',
  },
]

function prepararListado(items: unknown[]) {
  mockedDependencias.list.mockResolvedValue({ data: { items } } as never)
}

async function guardarConFallo(
  user: ReturnType<typeof userEvent.setup>,
  fallo: unknown,
) {
  prepararListado(dependencias)
  mockedDependencias.create.mockRejectedValue(fallo as never)

  render(<DependenciasPage />)

  await user.click(await screen.findByRole('button', { name: 'Nueva dependencia' }))
  const dialogo = await screen.findByRole('dialog')
  await user.type(within(dialogo).getByPlaceholderText('Ej: DEP-001'), 'DEP-099')
  await user.type(
    within(dialogo).getByPlaceholderText('Ej: Secretaría de Planeación'),
    'Oficina de Pruebas',
  )
  await user.click(within(dialogo).getByRole('button', { name: 'Crear dependencia' }))
}

beforeEach(() => {
  mockedDependencias.list.mockReset()
  mockedDependencias.create.mockReset()
  mockedDependencias.update.mockReset()
  mockedDependencias.delete.mockReset()
})

describe('DependenciasPage', () => {
  it('muestra el estado de carga al iniciar', () => {
    mockedDependencias.list.mockReturnValue(new Promise(() => {}) as never)

    render(<DependenciasPage />)

    expect(screen.getByText('Cargando dependencias...')).toBeInTheDocument()
  })

  it('lista las dependencias con sus estadísticas y jerarquías', async () => {
    prepararListado(dependencias)

    render(<DependenciasPage />)

    expect(await screen.findByText('DEP-001')).toBeInTheDocument()
    expect(screen.getByText('DEP-002')).toBeInTheDocument()
    expect(screen.getByText('DEP-003')).toBeInTheDocument()
    expect(screen.getByText('Total dependencias')).toBeInTheDocument()
    expect(screen.getByText('Con padre')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getAllByText('2')).toHaveLength(2)
    expect(screen.getByText('1')).toBeInTheDocument()
    expect(screen.getByText('Padre: Secretaría de Planeación')).toBeInTheDocument()
    expect(screen.getByText('Padre: N/A')).toBeInTheDocument()
    expect(screen.getAllByText('ACTIVA')).toHaveLength(2)
    expect(screen.getAllByText('INACTIVA')).toHaveLength(1)
    expect(screen.getByText('-')).toBeInTheDocument()
    expect(
      screen.getByText('Planeación y desarrollo municipal'),
    ).toBeInTheDocument()
  })

  it('recarga la lista con el botón de actualizar', async () => {
    const user = userEvent.setup()
    prepararListado(dependencias)

    render(<DependenciasPage />)
    await screen.findByText('DEP-001')

    const llamadasPrevias = mockedDependencias.list.mock.calls.length
    await user.click(screen.getByRole('button', { name: 'Actualizar' }))

    await waitFor(() =>
      expect(mockedDependencias.list.mock.calls.length).toBeGreaterThan(
        llamadasPrevias,
      ),
    )
    expect(await screen.findByText('DEP-001')).toBeInTheDocument()
  })

  it('filtra por búsqueda y por estado', async () => {
    const user = userEvent.setup()
    prepararListado(dependencias)

    render(<DependenciasPage />)
    await screen.findByText('DEP-001')

    await user.type(screen.getByLabelText('Buscar dependencias'), 'plane')
    await waitFor(() =>
      expect(mockedDependencias.list).toHaveBeenLastCalledWith({
        page: 1,
        page_size: 100,
        search: 'plane',
      }),
    )

    await user.selectOptions(screen.getByLabelText('Filtrar por estado'), 'ACTIVO')
    await waitFor(() =>
      expect(mockedDependencias.list).toHaveBeenLastCalledWith({
        page: 1,
        page_size: 100,
        search: 'plane',
        estado: 'ACTIVO',
      }),
    )
  })

  it('muestra el estado vacío cuando no hay resultados', async () => {
    prepararListado([])

    render(<DependenciasPage />)

    expect(
      await screen.findByText('No hay dependencias que coincidan con la búsqueda.'),
    ).toBeInTheDocument()
  })

  it('muestra el error cuando la carga de dependencias falla', async () => {
    mockedDependencias.list.mockRejectedValue(new Error('fallo') as never)

    render(<DependenciasPage />)

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'No fue posible cargar las dependencias.',
    )
  })

  it('crea una dependencia con todos los campos del formulario', async () => {
    const user = userEvent.setup()
    prepararListado(dependencias)
    mockedDependencias.create.mockResolvedValue({ data: {} } as never)

    render(<DependenciasPage />)
    await screen.findByText('DEP-001')

    await user.click(screen.getByRole('button', { name: 'Nueva dependencia' }))
    const dialogo = await screen.findByRole('dialog')
    expect(
      screen.getByRole('heading', { name: 'Nueva dependencia' }),
    ).toBeInTheDocument()

    const botonGuardar = within(dialogo).getByRole('button', {
      name: 'Crear dependencia',
    })
    expect(botonGuardar).toBeDisabled()

    await user.type(within(dialogo).getByPlaceholderText('Ej: DEP-001'), 'DEP-010')
    await user.type(
      within(dialogo).getByPlaceholderText('Ej: Secretaría de Planeación'),
      'Nueva Oficina',
    )
    await user.type(
      within(dialogo).getByPlaceholderText(
        'Descripción opcional de la dependencia...',
      ),
      'Dependencia creada en la prueba',
    )

    const [nivel, padre, estado] = within(dialogo).getAllByRole('combobox')
    await user.selectOptions(nivel, '2')
    await user.selectOptions(padre, 'd1')
    await user.selectOptions(estado, 'INACTIVA')

    expect(botonGuardar).toBeEnabled()
    await user.click(botonGuardar)

    expect(mockedDependencias.create).toHaveBeenCalledWith({
      codigo: 'DEP-010',
      nombre: 'Nueva Oficina',
      descripcion: 'Dependencia creada en la prueba',
      dependencia_padre_id: 'd1',
      nivel: 2,
      estado: 'INACTIVA',
    })
    await waitFor(() =>
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument(),
    )
  })

  it('edita una dependencia existente', async () => {
    const user = userEvent.setup()
    prepararListado(dependencias)
    mockedDependencias.update.mockResolvedValue({ data: {} } as never)

    render(<DependenciasPage />)
    await screen.findByText('DEP-001')

    const fila = screen.getByText('DEP-001').closest('tr') as HTMLElement
    await user.click(within(fila).getByRole('button', { name: 'Editar' }))

    const dialogo = await screen.findByRole('dialog')
    expect(
      screen.getByRole('heading', { name: 'Editar dependencia' }),
    ).toBeInTheDocument()
    expect(
      screen.getByText('Actualice la información de "Secretaría de Planeación".'),
    ).toBeInTheDocument()
    expect(within(dialogo).getByPlaceholderText('Ej: DEP-001')).toBeDisabled()
    expect(
      within(dialogo).queryByRole('option', {
        name: 'DEP-001 - Secretaría de Planeación',
      }),
    ).toBeNull()

    const nombre = within(dialogo).getByPlaceholderText(
      'Ej: Secretaría de Planeación',
    )
    await user.clear(nombre)
    await user.type(nombre, 'Secretaría Renombrada')

    const descripcion = within(dialogo).getByPlaceholderText(
      'Descripción opcional de la dependencia...',
    )
    await user.clear(descripcion)
    await user.type(descripcion, 'Descripción actualizada')

    const [nivel, padre, estado] = within(dialogo).getAllByRole('combobox')
    await user.selectOptions(nivel, '3')
    await user.selectOptions(padre, 'd2')
    await user.selectOptions(estado, 'INACTIVA')

    await user.click(
      within(dialogo).getByRole('button', { name: 'Guardar cambios' }),
    )

    expect(mockedDependencias.update).toHaveBeenCalledWith('d1', {
      nombre: 'Secretaría Renombrada',
      descripcion: 'Descripción actualizada',
      nivel: 3,
      estado: 'INACTIVA',
      dependencia_padre_id: 'd2',
    })
    await waitFor(() =>
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument(),
    )
  })

  it('muestra el detalle de error devuelto por el API al guardar', async () => {
    const user = userEvent.setup()

    await guardarConFallo(user, {
      response: { data: { detail: 'El código ya existe' } },
    })

    expect(await screen.findByRole('alert')).toHaveTextContent('El código ya existe')
  })

  it('muestra el mensaje de validación cuando el error es una lista', async () => {
    const user = userEvent.setup()

    await guardarConFallo(user, {
      response: {
        data: { detail: [{ loc: ['body', 'nombre'], msg: 'campo requerido' }] },
      },
    })

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Verifique los campos del formulario',
    )
  })

  it('muestra el mensaje genérico cuando el error no trae detalle', async () => {
    const user = userEvent.setup()

    await guardarConFallo(user, new Error('sin detalle'))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'No fue posible guardar los cambios.',
    )
  })

  it('cierra el modal de creación con el botón cancelar', async () => {
    const user = userEvent.setup()
    prepararListado(dependencias)

    render(<DependenciasPage />)
    await screen.findByText('DEP-001')

    await user.click(screen.getByRole('button', { name: 'Nueva dependencia' }))
    expect(await screen.findByRole('dialog')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Cancelar' }))

    expect(screen.queryByRole('dialog')).toBeNull()
    expect(mockedDependencias.create).not.toHaveBeenCalled()
  })

  it('cierra el modal con el botón de cerrar', async () => {
    const user = userEvent.setup()
    prepararListado(dependencias)

    render(<DependenciasPage />)
    await screen.findByText('DEP-001')

    await user.click(screen.getByRole('button', { name: 'Nueva dependencia' }))
    expect(await screen.findByRole('dialog')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Cerrar' }))

    expect(screen.queryByRole('dialog')).toBeNull()
  })

  it('elimina la dependencia cuando se confirma la acción', async () => {
    const user = userEvent.setup()
    const confirmar = vi.spyOn(window, 'confirm').mockReturnValue(true)
    prepararListado(dependencias)
    mockedDependencias.delete.mockResolvedValue({ data: null } as never)

    render(<DependenciasPage />)
    await screen.findByText('DEP-001')

    const fila = screen.getByText('DEP-001').closest('tr') as HTMLElement
    await user.click(within(fila).getByRole('button', { name: 'Eliminar' }))

    expect(confirmar).toHaveBeenCalledWith(
      '¿Eliminar la dependencia "Secretaría de Planeación"? Esta acción quedará registrada en la auditoría.',
    )
    expect(mockedDependencias.delete).toHaveBeenCalledWith('d1')
    await waitFor(() =>
      expect(mockedDependencias.delete).toHaveBeenCalledTimes(1),
    )
  })

  it('no elimina la dependencia cuando se cancela la confirmación', async () => {
    const user = userEvent.setup()
    const confirmar = vi.spyOn(window, 'confirm').mockReturnValue(false)
    prepararListado(dependencias)

    render(<DependenciasPage />)
    await screen.findByText('DEP-001')

    const fila = screen.getByText('DEP-001').closest('tr') as HTMLElement
    await user.click(within(fila).getByRole('button', { name: 'Eliminar' }))

    expect(confirmar).toHaveBeenCalled()
    expect(mockedDependencias.delete).not.toHaveBeenCalled()
    expect(screen.getByText('DEP-001')).toBeInTheDocument()
  })

  it('muestra el error cuando la eliminación falla', async () => {
    const user = userEvent.setup()
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    prepararListado(dependencias)
    mockedDependencias.delete.mockRejectedValue(new Error('fallo') as never)

    render(<DependenciasPage />)
    await screen.findByText('DEP-001')

    const fila = screen.getByText('DEP-001').closest('tr') as HTMLElement
    await user.click(within(fila).getByRole('button', { name: 'Eliminar' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'No fue posible eliminar la dependencia.',
    )
  })
})
