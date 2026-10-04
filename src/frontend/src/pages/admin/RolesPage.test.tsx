import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { configRoles } from '../../lib/api'
import { RolesPage } from './RolesPage'

vi.mock('../../lib/api', () => ({
  configRoles: { list: vi.fn(), create: vi.fn(), update: vi.fn(), delete: vi.fn(), permisos: vi.fn() },
  default: {},
}))

const mockedConfigRoles = vi.mocked(configRoles)

function respuesta(data: unknown) {
  return { data } as never
}

const permisoVer = { id: 'p1', codigo: 'GESTOR_VER', nombre: 'Ver gestores', modulo: 'gestores', accion: 'ver' }
const permisoCrear = { id: 'p2', codigo: 'GESTOR_CREAR', nombre: 'Crear gestores', modulo: 'gestores', accion: 'crear' }
const permisoExportar = { id: 'p3', codigo: 'LINEA_EXPORT', nombre: 'Exportar líneas', modulo: 'lineas', accion: 'exportar' }

const rol1 = {
  id: 'r1',
  codigo: 'ADMIN',
  nombre: 'Administrador',
  descripcion: 'Acceso total',
  nivel: 5,
  estado: 'ACTIVO',
  permisos: [permisoVer],
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-02-01T00:00:00Z',
}

const rol2 = {
  id: 'r2',
  codigo: 'CONSULTA',
  nombre: 'Consulta',
  descripcion: '',
  nivel: 1,
  estado: 'INACTIVO',
  permisos: [],
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
  mockedConfigRoles.list.mockResolvedValue(respuesta({ items: [rol1, rol2], total: 2, page: 1, page_size: 100 }))
  mockedConfigRoles.permisos.mockResolvedValue(respuesta({ items: [permisoVer, permisoCrear, permisoExportar], total: 3 }))
  mockedConfigRoles.create.mockResolvedValue(respuesta(rol1))
  mockedConfigRoles.update.mockResolvedValue(respuesta(rol1))
  mockedConfigRoles.delete.mockResolvedValue(respuesta(null))
})

describe('RolesPage', () => {
  it('muestra el estado de carga inicial', () => {
    mockedConfigRoles.list.mockReturnValue(new Promise(() => {}) as never)

    render(<RolesPage />)

    expect(screen.getByText('Cargando roles...')).toBeInTheDocument()
  })

  it('renderiza los roles con sus tarjetas y la tabla', async () => {
    render(<RolesPage />)

    expect(await screen.findByText('Administrador')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Roles y permisos' })).toBeInTheDocument()
    expect(screen.getByText('Consulta')).toBeInTheDocument()
    expect(screen.getByText('Total de roles')).toBeInTheDocument()
    expect(screen.getByText('Activos')).toBeInTheDocument()
    expect(screen.getByText('Permisos disponibles')).toBeInTheDocument()
    expect(screen.getByLabelText('Buscar roles')).toBeInTheDocument()
    expect(filaDe('Administrador').getByText('ADMIN')).toBeInTheDocument()
    expect(filaDe('Administrador').getByText('Acceso total')).toBeInTheDocument()
    expect(filaDe('Administrador').getByText('5')).toBeInTheDocument()
    expect(filaDe('Administrador').getByText('1 permisos')).toBeInTheDocument()
    expect(filaDe('Administrador').getByText('ACTIVO')).toBeInTheDocument()
    expect(filaDe('Consulta').getByText('-')).toBeInTheDocument()
    expect(filaDe('Consulta').getByText('0 permisos')).toBeInTheDocument()
    expect(filaDe('Consulta').getByText('INACTIVO')).toBeInTheDocument()
  })

  it('muestra el mensaje de vacío cuando no hay roles', async () => {
    mockedConfigRoles.list.mockResolvedValue(respuesta({ items: [], total: 0, page: 1, page_size: 100 }))

    render(<RolesPage />)

    expect(await screen.findByText('No hay roles que coincidan con la búsqueda.')).toBeInTheDocument()
  })

  it('muestra un error cuando la carga de roles falla', async () => {
    mockedConfigRoles.list.mockRejectedValue(new Error('fallo') as never)

    render(<RolesPage />)

    expect(await screen.findByText('No fue posible cargar los roles.')).toBeInTheDocument()
  })

  it('funciona aunque el catálogo de permisos no pueda cargarse', async () => {
    mockedConfigRoles.permisos.mockRejectedValue(new Error('fallo') as never)

    render(<RolesPage />)

    expect(await screen.findByText('Administrador')).toBeInTheDocument()
  })

  it('permite buscar roles', async () => {
    const user = userEvent.setup()
    render(<RolesPage />)
    await screen.findByText('Administrador')

    await user.type(screen.getByLabelText('Buscar roles'), 'admin')

    await waitFor(() => {
      expect(mockedConfigRoles.list).toHaveBeenCalledWith(expect.objectContaining({ search: 'admin' }))
    })
  })

  it('recarga la lista con el botón Actualizar', async () => {
    const user = userEvent.setup()
    render(<RolesPage />)
    await screen.findByText('Administrador')

    await user.click(screen.getByRole('button', { name: 'Actualizar' }))

    await waitFor(() => {
      expect(mockedConfigRoles.list).toHaveBeenCalledTimes(2)
    })
  })

  it('crea un rol y asigna permisos por módulo', async () => {
    const user = userEvent.setup()
    render(<RolesPage />)
    await screen.findByText('Administrador')

    await user.click(screen.getByRole('button', { name: 'Nuevo rol' }))

    const modal = dialogo()
    expect(within(modal).getByRole('button', { name: 'Crear rol' })).toBeDisabled()

    const campos = within(modal).getAllByRole('textbox')
    await user.type(campos[0], 'COORD')
    await user.type(campos[1], 'Coordinador')
    await user.type(campos[2], 'Coordinación general')
    fireEvent.change(within(modal).getByRole('spinbutton'), { target: { value: '3' } })

    await user.click(within(modal).getByLabelText('gestores'))
    await user.click(within(modal).getByLabelText('ver'))
    await user.click(within(modal).getByLabelText('ver'))
    await user.click(within(modal).getByLabelText('gestores'))
    await user.click(within(modal).getByLabelText('gestores'))

    expect(within(modal).getByRole('button', { name: 'Crear rol' })).toBeEnabled()
    await user.click(within(modal).getByRole('button', { name: 'Crear rol' }))

    await waitFor(() => {
      expect(mockedConfigRoles.create).toHaveBeenCalledWith({
        codigo: 'COORD',
        nombre: 'Coordinador',
        descripcion: 'Coordinación general',
        nivel: 3,
        permisos_ids: ['p1', 'p2'],
      })
    })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('edita un rol con el código bloqueado', async () => {
    const user = userEvent.setup()
    render(<RolesPage />)
    await screen.findByText('Administrador')

    await user.click(filaDe('Administrador').getByRole('button', { name: 'Editar' }))

    const modal = dialogo()
    expect(within(modal).getByText('Actualice el rol "Administrador".')).toBeInTheDocument()
    const campos = within(modal).getAllByRole('textbox')
    expect(campos[0]).toBeDisabled()
    expect(campos[0]).toHaveValue('ADMIN')
    expect(within(modal).getByLabelText('ver')).toBeChecked()

    await user.clear(campos[1])
    await user.type(campos[1], 'Administrador General')
    fireEvent.change(within(modal).getByRole('spinbutton'), { target: { value: '4' } })

    await user.click(within(modal).getByRole('button', { name: 'Guardar cambios' }))

    await waitFor(() => {
      expect(mockedConfigRoles.update).toHaveBeenCalledWith('r1', {
        nombre: 'Administrador General',
        descripcion: 'Acceso total',
        nivel: 4,
        permisos_ids: ['p1'],
      })
    })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('muestra el detalle del error devuelto por el backend', async () => {
    const user = userEvent.setup()
    mockedConfigRoles.update.mockRejectedValue({ response: { data: { detail: 'El código ya existe' } } } as never)
    render(<RolesPage />)
    await screen.findByText('Administrador')

    await user.click(filaDe('Administrador').getByRole('button', { name: 'Editar' }))
    await user.click(within(dialogo()).getByRole('button', { name: 'Guardar cambios' }))

    expect(await screen.findByText('El código ya existe')).toBeInTheDocument()
  })

  it('muestra un mensaje de validación cuando el backend devuelve una lista de errores', async () => {
    const user = userEvent.setup()
    mockedConfigRoles.update.mockRejectedValue({ response: { data: { detail: [{ msg: 'inválido' }] } } } as never)
    render(<RolesPage />)
    await screen.findByText('Administrador')

    await user.click(filaDe('Administrador').getByRole('button', { name: 'Editar' }))
    await user.click(within(dialogo()).getByRole('button', { name: 'Guardar cambios' }))

    expect(await screen.findByText('Verifique los campos del formulario')).toBeInTheDocument()
  })

  it('muestra un error genérico cuando la falla no trae detalle', async () => {
    const user = userEvent.setup()
    mockedConfigRoles.update.mockRejectedValue(new Error('sin detalle') as never)
    render(<RolesPage />)
    await screen.findByText('Administrador')

    await user.click(filaDe('Administrador').getByRole('button', { name: 'Editar' }))
    await user.click(within(dialogo()).getByRole('button', { name: 'Guardar cambios' }))

    expect(await screen.findByText('No fue posible guardar los cambios.')).toBeInTheDocument()
  })

  it('elimina un rol tras confirmar', async () => {
    const user = userEvent.setup()
    const confirmar = vi.spyOn(window, 'confirm').mockReturnValue(true)
    render(<RolesPage />)
    await screen.findByText('Administrador')

    await user.click(filaDe('Administrador').getByRole('button', { name: 'Eliminar' }))

    await waitFor(() => {
      expect(confirmar).toHaveBeenCalledWith('¿Eliminar el rol "Administrador"? Esta acción quedará registrada en la auditoría.')
      expect(mockedConfigRoles.delete).toHaveBeenCalledWith('r1')
    })
  })

  it('no elimina el rol si el usuario cancela la confirmación', async () => {
    const user = userEvent.setup()
    vi.spyOn(window, 'confirm').mockReturnValue(false)
    render(<RolesPage />)
    await screen.findByText('Administrador')

    await user.click(filaDe('Administrador').getByRole('button', { name: 'Eliminar' }))

    expect(mockedConfigRoles.delete).not.toHaveBeenCalled()
  })

  it('muestra un error cuando la eliminación falla', async () => {
    const user = userEvent.setup()
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    mockedConfigRoles.delete.mockRejectedValue(new Error('fallo') as never)
    render(<RolesPage />)
    await screen.findByText('Administrador')

    await user.click(filaDe('Administrador').getByRole('button', { name: 'Eliminar' }))

    expect(await screen.findByText('No fue posible eliminar el rol.')).toBeInTheDocument()
  })

  it('cierra los modales con el botón Cancelar', async () => {
    const user = userEvent.setup()
    render(<RolesPage />)
    await screen.findByText('Administrador')

    await user.click(screen.getByRole('button', { name: 'Nuevo rol' }))
    await user.click(within(dialogo()).getByRole('button', { name: 'Cancelar' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()

    await user.click(filaDe('Administrador').getByRole('button', { name: 'Editar' }))
    await user.click(within(dialogo()).getByRole('button', { name: 'Cancelar' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('cierra el modal con el botón de cierre', async () => {
    const user = userEvent.setup()
    render(<RolesPage />)
    await screen.findByText('Administrador')

    await user.click(screen.getByRole('button', { name: 'Nuevo rol' }))
    await user.click(within(dialogo()).getByRole('button', { name: 'Cerrar' }))

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('cierra el modal al hacer clic en el fondo', async () => {
    const user = userEvent.setup()
    render(<RolesPage />)
    await screen.findByText('Administrador')

    await user.click(screen.getByRole('button', { name: 'Nuevo rol' }))
    const modal = dialogo()
    fireEvent.mouseDown(modal.parentElement as HTMLElement)

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
