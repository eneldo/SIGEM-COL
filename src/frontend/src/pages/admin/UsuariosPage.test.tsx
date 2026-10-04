import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { catalogos, configUsuarios } from '../../lib/api'
import { UsuariosPage } from './UsuariosPage'

vi.mock('../../lib/api', () => ({
  configUsuarios: { list: vi.fn(), create: vi.fn(), update: vi.fn(), delete: vi.fn() },
  catalogos: { roles: vi.fn() },
  default: {},
}))

const mockedConfigUsuarios = vi.mocked(configUsuarios)
const mockedCatalogos = vi.mocked(catalogos)

function respuesta(data: unknown) {
  return { data } as never
}

const rolU = { id: 'ur1', codigo: 'ADMIN', nombre: 'Administrador' }

const usuario1 = {
  id: 'u1',
  municipio_id: 'm1',
  codigo: 'USR-001',
  username: 'jperez',
  email: 'jorge@correo.gov.co',
  nombre_completo: 'Jorge Pérez',
  telefono: '3001234567',
  cargo: 'Secretario',
  activo: 1,
  roles: [rolU],
  must_change_password: false,
  mfa_activo: true,
  ultimo_acceso: '2024-06-01T10:00:00Z',
  intentos_fallidos: 0,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

const usuario2 = {
  id: 'u2',
  municipio_id: 'm1',
  codigo: 'USR-002',
  username: 'mgomez',
  email: 'maria@correo.gov.co',
  nombre_completo: 'María Gómez',
  telefono: '',
  cargo: '',
  activo: 0,
  roles: [],
  must_change_password: false,
  mfa_activo: false,
  intentos_fallidos: 3,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

function filaDe(nombre: string) {
  const fila = screen.getByText(nombre).closest('tr')
  return within(fila as HTMLElement)
}

function dialogo() {
  return screen.getByRole('dialog')
}

beforeEach(() => {
  mockedConfigUsuarios.list.mockResolvedValue(respuesta({ items: [usuario1, usuario2], total: 2, page: 1, page_size: 100 }))
  mockedConfigUsuarios.create.mockResolvedValue(respuesta(usuario1))
  mockedConfigUsuarios.update.mockResolvedValue(respuesta(usuario1))
  mockedConfigUsuarios.delete.mockResolvedValue(respuesta(null))
  mockedCatalogos.roles.mockResolvedValue(respuesta([rolU]))
})

describe('UsuariosPage', () => {
  it('muestra el estado de carga inicial', () => {
    mockedConfigUsuarios.list.mockReturnValue(new Promise(() => {}) as never)

    render(<UsuariosPage />)

    expect(screen.getByText('Cargando usuarios...')).toBeInTheDocument()
  })

  it('renderiza los usuarios con sus tarjetas y filtros', async () => {
    render(<UsuariosPage />)

    expect(await screen.findByText('Jorge Pérez')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Usuarios del sistema' })).toBeInTheDocument()
    expect(screen.getByText('María Gómez')).toBeInTheDocument()
    expect(screen.getByText('Total de usuarios')).toBeInTheDocument()
    expect(screen.getByText('Con MFA')).toBeInTheDocument()
    expect(screen.getAllByText('Activos')).toHaveLength(2)
    expect(screen.getAllByText('Inactivos')).toHaveLength(2)
    expect(screen.getByLabelText('Buscar usuarios')).toBeInTheDocument()
    expect(screen.getByLabelText('Filtrar por estado')).toBeInTheDocument()
    expect(filaDe('Jorge Pérez').getByText('USR-001')).toBeInTheDocument()
    expect(filaDe('Jorge Pérez').getByText('@jperez')).toBeInTheDocument()
    expect(filaDe('Jorge Pérez').getByText('jorge@correo.gov.co')).toBeInTheDocument()
    expect(filaDe('Jorge Pérez').getByText('Administrador')).toBeInTheDocument()
    expect(filaDe('Jorge Pérez').getByText('ACTIVO')).toBeInTheDocument()
    expect(filaDe('María Gómez').getByText('@mgomez')).toBeInTheDocument()
    expect(filaDe('María Gómez').getByText('-')).toBeInTheDocument()
    expect(filaDe('María Gómez').getByText('INACTIVO')).toBeInTheDocument()
    expect(filaDe('María Gómez').getByText('Nunca')).toBeInTheDocument()
  })

  it('muestra el mensaje de vacío cuando no hay usuarios', async () => {
    mockedConfigUsuarios.list.mockResolvedValue(respuesta({ items: [], total: 0, page: 1, page_size: 100 }))

    render(<UsuariosPage />)

    expect(await screen.findByText('No hay usuarios que coincidan con la búsqueda.')).toBeInTheDocument()
  })

  it('muestra un error cuando la carga de usuarios falla', async () => {
    mockedConfigUsuarios.list.mockRejectedValue(new Error('fallo') as never)

    render(<UsuariosPage />)

    expect(await screen.findByText('No fue posible cargar los usuarios.')).toBeInTheDocument()
  })

  it('funciona aunque el catálogo de roles no pueda cargarse', async () => {
    mockedCatalogos.roles.mockRejectedValue(new Error('fallo') as never)

    render(<UsuariosPage />)

    expect(await screen.findByText('Jorge Pérez')).toBeInTheDocument()
  })

  it('permite buscar y filtrar por estado', async () => {
    const user = userEvent.setup()
    render(<UsuariosPage />)
    await screen.findByText('Jorge Pérez')

    await user.type(screen.getByLabelText('Buscar usuarios'), 'jorge')
    await waitFor(() => {
      expect(mockedConfigUsuarios.list).toHaveBeenCalledWith(expect.objectContaining({ search: 'jorge' }))
    })

    await user.selectOptions(screen.getByLabelText('Filtrar por estado'), 'ACTIVO')
    await waitFor(() => {
      expect(mockedConfigUsuarios.list).toHaveBeenCalledWith(expect.objectContaining({ estado: 'ACTIVO' }))
    })
  })

  it('recarga la lista con el botón Actualizar', async () => {
    const user = userEvent.setup()
    render(<UsuariosPage />)
    await screen.findByText('Jorge Pérez')

    await user.click(screen.getByRole('button', { name: 'Actualizar' }))

    await waitFor(() => {
      expect(mockedConfigUsuarios.list).toHaveBeenCalledTimes(2)
    })
  })

  it('crea un usuario con rol y contraseña', async () => {
    const user = userEvent.setup()
    render(<UsuariosPage />)
    await screen.findByText('Jorge Pérez')

    await user.click(screen.getByRole('button', { name: 'Nuevo usuario' }))

    const modal = dialogo()
    expect(within(modal).getByRole('button', { name: 'Crear usuario' })).toBeDisabled()

    const campos = within(modal).getAllByRole('textbox')
    expect(campos).toHaveLength(6)
    await user.type(campos[0], 'USR-010')
    await user.type(campos[1], 'ana.lopez')
    await user.type(campos[2], 'Ana López')
    await user.type(campos[3], 'ana@correo.gov.co')
    await user.type(campos[4], '3009876543')
    await user.type(campos[5], 'Analista')
    const password = modal.querySelector('input[type="password"]') as HTMLInputElement
    expect(password).not.toBeNull()
    await user.type(password, 'ClaveSegura123')
    await user.selectOptions(within(modal).getByRole('combobox'), 'ur1')

    expect(within(modal).getByRole('button', { name: 'Crear usuario' })).toBeEnabled()
    await user.click(within(modal).getByRole('button', { name: 'Crear usuario' }))

    await waitFor(() => {
      expect(mockedConfigUsuarios.create).toHaveBeenCalledWith({
        codigo: 'USR-010',
        username: 'ana.lopez',
        email: 'ana@correo.gov.co',
        nombre_completo: 'Ana López',
        telefono: '3009876543',
        cargo: 'Analista',
        password: 'ClaveSegura123',
        rol_id: 'ur1',
        dependencia_id: '',
      })
    })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('edita un usuario sin permitir cambiar código ni usuario', async () => {
    const user = userEvent.setup()
    render(<UsuariosPage />)
    await screen.findByText('Jorge Pérez')

    await user.click(filaDe('Jorge Pérez').getByRole('button', { name: 'Editar' }))

    const modal = dialogo()
    expect(within(modal).getByText(/Actualice la información de "Jorge Pérez"/)).toBeInTheDocument()
    const campos = within(modal).getAllByRole('textbox')
    expect(campos[0]).toBeDisabled()
    expect(campos[1]).toBeDisabled()
    expect(modal.querySelector('input[type="password"]')).toBeNull()

    await user.clear(campos[2])
    await user.type(campos[2], 'Jorge Pérez Actualizado')
    await user.click(within(modal).getByRole('button', { name: 'Guardar cambios' }))

    await waitFor(() => {
      expect(mockedConfigUsuarios.update).toHaveBeenCalledWith('u1', {
        email: 'jorge@correo.gov.co',
        nombre_completo: 'Jorge Pérez Actualizado',
        telefono: '3001234567',
        cargo: 'Secretario',
        rol_id: 'ur1',
      })
    })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('muestra el detalle del error devuelto por el backend', async () => {
    const user = userEvent.setup()
    mockedConfigUsuarios.update.mockRejectedValue({ response: { data: { detail: 'El correo ya está en uso' } } } as never)
    render(<UsuariosPage />)
    await screen.findByText('Jorge Pérez')

    await user.click(filaDe('Jorge Pérez').getByRole('button', { name: 'Editar' }))
    await user.click(within(dialogo()).getByRole('button', { name: 'Guardar cambios' }))

    expect(await screen.findByText('El correo ya está en uso')).toBeInTheDocument()
  })

  it('muestra un mensaje de validación cuando el backend devuelve una lista de errores', async () => {
    const user = userEvent.setup()
    mockedConfigUsuarios.update.mockRejectedValue({ response: { data: { detail: [{ msg: 'inválido' }] } } } as never)
    render(<UsuariosPage />)
    await screen.findByText('Jorge Pérez')

    await user.click(filaDe('Jorge Pérez').getByRole('button', { name: 'Editar' }))
    await user.click(within(dialogo()).getByRole('button', { name: 'Guardar cambios' }))

    expect(await screen.findByText('Verifique los campos del formulario')).toBeInTheDocument()
  })

  it('muestra un error genérico cuando la falla no trae detalle', async () => {
    const user = userEvent.setup()
    mockedConfigUsuarios.update.mockRejectedValue(new Error('sin detalle') as never)
    render(<UsuariosPage />)
    await screen.findByText('Jorge Pérez')

    await user.click(filaDe('Jorge Pérez').getByRole('button', { name: 'Editar' }))
    await user.click(within(dialogo()).getByRole('button', { name: 'Guardar cambios' }))

    expect(await screen.findByText('No fue posible guardar los cambios.')).toBeInTheDocument()
  })

  it('elimina un usuario tras confirmar', async () => {
    const user = userEvent.setup()
    const confirmar = vi.spyOn(window, 'confirm').mockReturnValue(true)
    render(<UsuariosPage />)
    await screen.findByText('Jorge Pérez')

    await user.click(filaDe('Jorge Pérez').getByRole('button', { name: 'Eliminar' }))

    await waitFor(() => {
      expect(confirmar).toHaveBeenCalledWith('¿Eliminar el usuario "Jorge Pérez"? Esta acción quedará registrada en la auditoría.')
      expect(mockedConfigUsuarios.delete).toHaveBeenCalledWith('u1')
    })
  })

  it('no elimina el usuario si el usuario cancela la confirmación', async () => {
    const user = userEvent.setup()
    vi.spyOn(window, 'confirm').mockReturnValue(false)
    render(<UsuariosPage />)
    await screen.findByText('Jorge Pérez')

    await user.click(filaDe('Jorge Pérez').getByRole('button', { name: 'Eliminar' }))

    expect(mockedConfigUsuarios.delete).not.toHaveBeenCalled()
  })

  it('muestra un error cuando la eliminación falla', async () => {
    const user = userEvent.setup()
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    mockedConfigUsuarios.delete.mockRejectedValue(new Error('fallo') as never)
    render(<UsuariosPage />)
    await screen.findByText('Jorge Pérez')

    await user.click(filaDe('Jorge Pérez').getByRole('button', { name: 'Eliminar' }))

    expect(await screen.findByText('No fue posible eliminar el usuario.')).toBeInTheDocument()
  })

  it('cierra los modales con el botón Cancelar', async () => {
    const user = userEvent.setup()
    render(<UsuariosPage />)
    await screen.findByText('Jorge Pérez')

    await user.click(screen.getByRole('button', { name: 'Nuevo usuario' }))
    await user.click(within(dialogo()).getByRole('button', { name: 'Cancelar' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()

    await user.click(filaDe('Jorge Pérez').getByRole('button', { name: 'Editar' }))
    await user.click(within(dialogo()).getByRole('button', { name: 'Cancelar' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('cierra el modal con el botón de cierre', async () => {
    const user = userEvent.setup()
    render(<UsuariosPage />)
    await screen.findByText('Jorge Pérez')

    await user.click(screen.getByRole('button', { name: 'Nuevo usuario' }))
    await user.click(within(dialogo()).getByRole('button', { name: 'Cerrar' }))

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('cierra el modal al hacer clic en el fondo', async () => {
    const user = userEvent.setup()
    render(<UsuariosPage />)
    await screen.findByText('Jorge Pérez')

    await user.click(screen.getByRole('button', { name: 'Nuevo usuario' }))
    const modal = dialogo()
    fireEvent.mouseDown(modal.parentElement as HTMLElement)

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
