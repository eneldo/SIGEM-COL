import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { productos, programas } from '../../lib/api'
import { ProductosPage } from './ProductosPage'

vi.mock('../../lib/api', () => ({
  productos: { list: vi.fn(), create: vi.fn(), update: vi.fn(), delete: vi.fn() },
  programas: { list: vi.fn() },
  default: {},
}))

const mockedProductos = vi.mocked(productos)
const mockedProgramas = vi.mocked(programas)

function respuesta(data: unknown) {
  return { data } as never
}

const programa = {
  id: 'pg1',
  codigo: '1903',
  nombre: 'Programa Salud',
  sector: 'Salud',
  estado: 'ACTIVO',
  municipio_id: 'm1',
  linea_estrategica_id: 'l1',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-02-01T00:00:00Z',
}

const producto1 = {
  id: 'pr1',
  codigo: '1903031',
  nombre: 'Producto Uno',
  codigo_indicador: '190500400',
  indicador: '% de cumplimiento',
  meta_redactada: 'Meta cuatrienal',
  linea_base: 10,
  meta_cuatrienio: 50,
  descripcion: 'Desc',
  unidad_medida: 'UND',
  estado: 'ACTIVO',
  municipio_id: 'm1',
  programa_id: 'pg1',
  programa_nombre: 'Programa Salud',
  dependencia_responsable_id: 'dep1',
  gestor_lider_id: 'g1',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-06-01T00:00:00Z',
}

const producto2 = {
  id: 'pr2',
  codigo: '2001001',
  nombre: 'Producto Dos',
  estado: 'INACTIVO',
  municipio_id: 'm1',
  programa_id: 'pg2',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-06-02T00:00:00Z',
}

function filaDe(nombre: string) {
  const fila = screen.getByText(nombre).closest('tr')
  return within(fila as HTMLElement)
}

function dialogo() {
  return screen.getByRole('dialog')
}

async function abrirCreacion(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole('button', { name: 'Nuevo producto' }))
  return dialogo()
}

async function llenarProductoNuevo(user: ReturnType<typeof userEvent.setup>) {
  const modal = dialogo()
  const campos = within(modal).getAllByRole('textbox')
  await user.type(within(modal).getByPlaceholderText('Ej: 1903031'), '1909999')
  await user.type(campos[1], 'Producto Nuevo')
  await user.type(within(modal).getByPlaceholderText('Ej: 190500400'), '190500999')
  await user.type(within(modal).getByPlaceholderText('Ej: % de cumplimiento...'), 'Indicador nuevo')
  await user.type(within(modal).getByPlaceholderText('Descripción de la meta cuatrienal...'), 'Meta nueva')
  await user.selectOptions(within(modal).getByRole('combobox'), 'pg1')
  const numeros = modal.querySelectorAll('input[type="number"]')
  fireEvent.change(numeros[0], { target: { value: '25' } })
  fireEvent.change(numeros[1], { target: { value: '75' } })
}

beforeEach(() => {
  mockedProductos.list.mockResolvedValue(respuesta({ items: [producto1, producto2], total: 2, page: 1, page_size: 100 }))
  mockedProductos.create.mockResolvedValue(respuesta(producto1))
  mockedProductos.update.mockResolvedValue(respuesta(producto1))
  mockedProductos.delete.mockResolvedValue(respuesta(null))
  mockedProgramas.list.mockResolvedValue(respuesta({ items: [programa], total: 1, page: 1, page_size: 100 }))
})

describe('ProductosPage', () => {
  it('muestra el estado de carga inicial', () => {
    mockedProductos.list.mockReturnValue(new Promise(() => {}) as never)

    render(<ProductosPage />)

    expect(screen.getByText('Cargando productos...')).toBeInTheDocument()
  })

  it('renderiza los productos con sus tarjetas y filtros', async () => {
    render(<ProductosPage />)

    expect(await screen.findByText('Producto Uno')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Productos' })).toBeInTheDocument()
    expect(screen.getByText('Producto Dos')).toBeInTheDocument()
    expect(screen.getByText('Total de productos')).toBeInTheDocument()
    expect(screen.getAllByText('Activos')).toHaveLength(2)
    expect(screen.getAllByText('Inactivos')).toHaveLength(2)
    expect(screen.getByText('Con gestor asignado')).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Programa Salud' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Todos los estados' })).toBeInTheDocument()
    expect(filaDe('Producto Uno').getByText('1903031')).toBeInTheDocument()
    expect(filaDe('Producto Uno').getByText('% de cumplimiento')).toBeInTheDocument()
    expect(filaDe('Producto Uno').getByText('Programa Salud')).toBeInTheDocument()
    expect(filaDe('Producto Uno').getByText('190500400')).toBeInTheDocument()
    expect(filaDe('Producto Uno').getByText('50')).toBeInTheDocument()
    expect(filaDe('Producto Uno').getByText('ACTIVO')).toBeInTheDocument()
    expect(filaDe('Producto Dos').getAllByText('-')).toHaveLength(2)
    expect(filaDe('Producto Dos').getByText('0')).toBeInTheDocument()
    expect(filaDe('Producto Dos').getByText('INACTIVO')).toBeInTheDocument()
  })

  it('muestra el mensaje de vacío cuando no hay productos', async () => {
    mockedProductos.list.mockResolvedValue(respuesta({ items: [], total: 0, page: 1, page_size: 100 }))

    render(<ProductosPage />)

    expect(await screen.findByText('No hay productos que coincidan con la búsqueda.')).toBeInTheDocument()
  })

  it('muestra un error cuando la carga de productos falla', async () => {
    mockedProductos.list.mockRejectedValue(new Error('fallo') as never)

    render(<ProductosPage />)

    expect(await screen.findByText('No fue posible cargar los productos.')).toBeInTheDocument()
  })

  it('permite buscar y filtrar por programa y estado', async () => {
    const user = userEvent.setup()
    render(<ProductosPage />)
    await screen.findByText('Producto Uno')

    await user.type(screen.getByLabelText('Buscar productos'), 'uno')
    await waitFor(() => {
      expect(mockedProductos.list).toHaveBeenCalledWith(expect.objectContaining({ search: 'uno' }))
    })

    await user.selectOptions(screen.getByLabelText('Filtrar por programa'), 'pg1')
    await waitFor(() => {
      expect(mockedProductos.list).toHaveBeenCalledWith(expect.objectContaining({ programa_id: 'pg1' }))
    })

    await user.selectOptions(screen.getByLabelText('Filtrar por estado'), 'ACTIVO')
    await waitFor(() => {
      expect(mockedProductos.list).toHaveBeenCalledWith(
        expect.objectContaining({ search: 'uno', programa_id: 'pg1', estado: 'ACTIVO' }),
      )
    })
  })

  it('recarga la lista con el botón Actualizar', async () => {
    const user = userEvent.setup()
    render(<ProductosPage />)
    await screen.findByText('Producto Uno')

    await user.click(screen.getByRole('button', { name: 'Actualizar' }))

    await waitFor(() => {
      expect(mockedProductos.list).toHaveBeenCalledTimes(2)
    })
  })

  it('crea un producto completo', async () => {
    const user = userEvent.setup()
    render(<ProductosPage />)
    await screen.findByText('Producto Uno')

    const modal = await abrirCreacion(user)
    expect(within(modal).getByText(/Asocie el producto a un programa/)).toBeInTheDocument()
    expect(within(modal).getByRole('button', { name: 'Crear producto' })).toBeDisabled()

    await llenarProductoNuevo(user)

    expect(within(dialogo()).getByRole('button', { name: 'Crear producto' })).toBeEnabled()

    await user.click(within(dialogo()).getByRole('button', { name: 'Crear producto' }))

    await waitFor(() => {
      expect(mockedProductos.create).toHaveBeenCalledWith({
        codigo: '1909999',
        nombre: 'Producto Nuevo',
        codigo_indicador: '190500999',
        indicador: 'Indicador nuevo',
        meta_redactada: 'Meta nueva',
        linea_base: 25,
        meta_cuatrienio: 75,
        descripcion: '',
        unidad_medida: '',
        programa_id: 'pg1',
        dependencia_responsable_id: undefined,
        gestor_lider_id: undefined,
      })
    })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('edita un producto existente', async () => {
    const user = userEvent.setup()
    render(<ProductosPage />)
    await screen.findByText('Producto Uno')

    await user.click(filaDe('Producto Uno').getByRole('button', { name: 'Editar' }))

    const modal = dialogo()
    expect(within(modal).getByText(/Actualice la información de "Producto Uno"/)).toBeInTheDocument()

    const campos = within(modal).getAllByRole('textbox')
    await user.clear(campos[1])
    await user.type(campos[1], 'Producto Editado')

    await user.click(within(modal).getByRole('button', { name: 'Guardar cambios' }))

    await waitFor(() => {
      expect(mockedProductos.update).toHaveBeenCalledWith('pr1', {
        codigo: '1903031',
        nombre: 'Producto Editado',
        codigo_indicador: '190500400',
        indicador: '% de cumplimiento',
        meta_redactada: 'Meta cuatrienal',
        linea_base: 10,
        meta_cuatrienio: 50,
        dependencia_responsable_id: 'dep1',
        gestor_lider_id: 'g1',
      })
    })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('muestra el detalle del error devuelto por el backend', async () => {
    const user = userEvent.setup()
    mockedProductos.create.mockRejectedValue({ response: { data: { detail: 'El código ya existe' } } } as never)
    render(<ProductosPage />)
    await screen.findByText('Producto Uno')

    await abrirCreacion(user)
    await llenarProductoNuevo(user)
    await user.click(within(dialogo()).getByRole('button', { name: 'Crear producto' }))

    expect(await screen.findByText('El código ya existe')).toBeInTheDocument()
  })

  it('muestra un mensaje de validación cuando el backend devuelve una lista de errores', async () => {
    const user = userEvent.setup()
    mockedProductos.create.mockRejectedValue({ response: { data: { detail: [{ msg: 'inválido' }] } } } as never)
    render(<ProductosPage />)
    await screen.findByText('Producto Uno')

    await abrirCreacion(user)
    await llenarProductoNuevo(user)
    await user.click(within(dialogo()).getByRole('button', { name: 'Crear producto' }))

    expect(await screen.findByText('Verifique los campos del formulario')).toBeInTheDocument()
  })

  it('muestra un error genérico cuando la falla no trae detalle', async () => {
    const user = userEvent.setup()
    mockedProductos.create.mockRejectedValue(new Error('sin detalle') as never)
    render(<ProductosPage />)
    await screen.findByText('Producto Uno')

    await abrirCreacion(user)
    await llenarProductoNuevo(user)
    await user.click(within(dialogo()).getByRole('button', { name: 'Crear producto' }))

    expect(await screen.findByText('No fue posible guardar los cambios.')).toBeInTheDocument()
  })

  it('elimina un producto tras confirmar', async () => {
    const user = userEvent.setup()
    const confirmar = vi.spyOn(window, 'confirm').mockReturnValue(true)
    render(<ProductosPage />)
    await screen.findByText('Producto Uno')

    await user.click(filaDe('Producto Uno').getByRole('button', { name: 'Eliminar' }))

    await waitFor(() => {
      expect(confirmar).toHaveBeenCalled()
      expect(mockedProductos.delete).toHaveBeenCalledWith('pr1')
    })
  })

  it('no elimina el producto si el usuario cancela la confirmación', async () => {
    const user = userEvent.setup()
    vi.spyOn(window, 'confirm').mockReturnValue(false)
    render(<ProductosPage />)
    await screen.findByText('Producto Uno')

    await user.click(filaDe('Producto Uno').getByRole('button', { name: 'Eliminar' }))

    expect(mockedProductos.delete).not.toHaveBeenCalled()
  })

  it('muestra un error cuando la eliminación falla', async () => {
    const user = userEvent.setup()
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    mockedProductos.delete.mockRejectedValue(new Error('fallo') as never)
    render(<ProductosPage />)
    await screen.findByText('Producto Uno')

    await user.click(filaDe('Producto Uno').getByRole('button', { name: 'Eliminar' }))

    expect(await screen.findByText('No fue posible eliminar el producto.')).toBeInTheDocument()
  })

  it('cierra los modales con el botón Cancelar', async () => {
    const user = userEvent.setup()
    render(<ProductosPage />)
    await screen.findByText('Producto Uno')

    const creacion = await abrirCreacion(user)
    await user.click(within(creacion).getByRole('button', { name: 'Cancelar' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()

    await user.click(filaDe('Producto Uno').getByRole('button', { name: 'Editar' }))
    await user.click(within(dialogo()).getByRole('button', { name: 'Cancelar' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('cierra el modal con el botón de cierre', async () => {
    const user = userEvent.setup()
    render(<ProductosPage />)
    await screen.findByText('Producto Uno')

    const modal = await abrirCreacion(user)
    await user.click(within(modal).getByRole('button', { name: 'Cerrar' }))

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('cierra el modal al hacer clic en el fondo', async () => {
    const user = userEvent.setup()
    render(<ProductosPage />)
    await screen.findByText('Producto Uno')

    const modal = await abrirCreacion(user)
    fireEvent.mouseDown(modal.parentElement as HTMLElement)

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('funciona aunque el catálogo de programas no pueda cargarse', async () => {
    mockedProgramas.list.mockRejectedValue(new Error('fallo') as never)

    render(<ProductosPage />)

    expect(await screen.findByText('Producto Uno')).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Todos los programas' })).toBeInTheDocument()
  })
})
