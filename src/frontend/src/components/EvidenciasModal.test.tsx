import { act, fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { gestorDashboard } from '../lib/api'
import type { Evidencia } from '../lib/types'
import EvidenciasModal from './EvidenciasModal'

vi.mock('../lib/api', () => ({
  gestorDashboard: {
    listarEvidencias: vi.fn(),
    descargarEvidenciaPorId: vi.fn(),
    subirEvidencias: vi.fn(),
    actualizarDescripcionEvidencia: vi.fn(),
    eliminarEvidencia: vi.fn(),
  },
  default: {},
}))

const listar = vi.mocked(gestorDashboard.listarEvidencias)
const descargar = vi.mocked(gestorDashboard.descargarEvidenciaPorId)
const subir = vi.mocked(gestorDashboard.subirEvidencias)
const actualizarDescripcion = vi.mocked(gestorDashboard.actualizarDescripcionEvidencia)
const eliminar = vi.mocked(gestorDashboard.eliminarEvidencia)

function evidencia(overrides: Partial<Evidencia> = {}): Evidencia {
  return {
    id: 'ev-1',
    avance_id: 'av-1',
    nombre: 'foto-avance.png',
    tipo: 'image/png',
    url: '/media/foto-avance.png',
    descripcion: null,
    tamano_original: 4096,
    tamano_almacenado: 2048,
    optimizada: false,
    created_at: null,
    ...overrides,
  }
}

function renderModal(props: Partial<Parameters<typeof EvidenciasModal>[0]> = {}) {
  const onClose = vi.fn()
  render(
    <EvidenciasModal avanceId="av-1" avanceNombre="Producto 1" canEdit onClose={onClose} {...props} />,
  )
  return { onClose }
}

function selectFiles(files: File[]) {
  const input = document.getElementById('evidencia-modal-input') as HTMLInputElement
  Object.defineProperty(input, 'files', { configurable: true, writable: true, value: files })
  fireEvent.change(input)
}

beforeEach(() => {
  listar.mockReset()
  descargar.mockReset()
  subir.mockReset()
  actualizarDescripcion.mockReset()
  eliminar.mockReset()
  listar.mockResolvedValue({ data: [] } as never)
  descargar.mockResolvedValue({ data: new Blob(['contenido']) } as never)
  subir.mockResolvedValue({ data: [] } as never)
  actualizarDescripcion.mockResolvedValue({ data: { id: 'ev-1', descripcion: null } } as never)
  eliminar.mockResolvedValue({ data: { id: 'ev-1', eliminada: true } } as never)
})

describe('carga de evidencias', () => {
  it('muestra el estado de carga mientras consulta', () => {
    listar.mockReturnValue(new Promise<never>(() => {}))

    renderModal()

    expect(screen.getByText('Cargando evidencias...')).toBeInTheDocument()
  })

  it('renderiza la lista con metadatos, miniaturas y descripción', async () => {
    listar.mockResolvedValue({
      data: [
        evidencia({
          descripcion: 'Acta firmada',
          optimizada: true,
          created_at: '2026-03-10T15:00:00.000Z',
        }),
        evidencia({
          id: 'ev-2',
          nombre: 'zip-anexo.zip',
          tipo: 'application/octet-stream',
          tamano_almacenado: null,
          created_at: null,
        }),
      ],
    } as never)

    renderModal()
    await act(async () => {})

    expect(screen.getByText('foto-avance.png')).toBeInTheDocument()
    expect(screen.getByText('image/png')).toBeInTheDocument()
    expect(screen.getByText('2.0 KB')).toBeInTheDocument()
    expect(screen.getByText('Comprimida')).toBeInTheDocument()
    expect(screen.getByText('Acta firmada')).toBeInTheDocument()
    expect(screen.getByText(/2026/)).toBeInTheDocument()
    expect(screen.getByText('zip-anexo.zip')).toBeInTheDocument()
    expect(screen.getByText('application/octet-stream')).toBeInTheDocument()
    expect(screen.getByText('Sin descripción')).toBeInTheDocument()
    expect(screen.getAllByText('—')).toHaveLength(2)
    expect(
      screen.getByRole('button', { name: 'Ver vista previa de foto-avance.png' }),
    ).toBeEnabled()
    expect(
      screen.queryByRole('button', { name: 'Ver vista previa de zip-anexo.zip' }),
    ).toBeNull()
  })

  it('muestra error cuando la carga falla', async () => {
    listar.mockRejectedValue(new Error('network') as never)

    renderModal()

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'No fue posible cargar las evidencias.',
    )
  })

  it('muestra el estado vacío cuando no hay evidencias', async () => {
    renderModal()
    await act(async () => {})

    expect(screen.getByText('Sin evidencias adjuntas')).toBeInTheDocument()
    expect(screen.getByText(/Agrega fotos, actas o planillas/)).toBeInTheDocument()
    expect(screen.getByText('Agregar evidencias (0/4)')).toBeInTheDocument()
  })
})

describe('subida de evidencias', () => {
  it('sube los archivos seleccionados y recarga la lista', async () => {
    listar
      .mockResolvedValueOnce({ data: [] } as never)
      .mockResolvedValue({
        data: [evidencia({ id: 'ev-1' }), evidencia({ id: 'ev-2', nombre: 'b.png' })],
      } as never)
    renderModal()
    await act(async () => {})

    const files = [
      new File(['a'], 'a.png', { type: 'image/png' }),
      new File(['b'], 'b.png', { type: 'image/png' }),
    ]
    selectFiles(files)
    await act(async () => {})

    expect(subir).toHaveBeenCalledTimes(1)
    expect(subir).toHaveBeenCalledWith('av-1', files)
    expect(listar).toHaveBeenCalledTimes(2)
    expect(screen.getByText('Agregar evidencias (2/4)')).toBeInTheDocument()
  })

  it('muestra el estado de subida mientras procesa', async () => {
    subir.mockReturnValue(new Promise<never>(() => {}))
    renderModal()
    await act(async () => {})

    selectFiles([new File(['a'], 'a.png', { type: 'image/png' })])

    expect(await screen.findByText('Subiendo...')).toBeInTheDocument()
    expect(document.getElementById('evidencia-modal-input')).toBeDisabled()
  })

  it('rechaza subir más allá del cupo de 4 evidencias', async () => {
    listar.mockResolvedValue({
      data: [evidencia({ id: 'ev-1' }), evidencia({ id: 'ev-2' }), evidencia({ id: 'ev-3' })],
    } as never)
    renderModal()
    await act(async () => {})

    selectFiles([
      new File(['a'], 'a.png', { type: 'image/png' }),
      new File(['b'], 'b.png', { type: 'image/png' }),
    ])

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Solo puedes agregar 1 evidencia más.',
    )
    expect(subir).not.toHaveBeenCalled()
  })

  it('informa que ya no quedan cupos disponibles', async () => {
    listar.mockResolvedValue({
      data: [
        evidencia({ id: 'ev-1' }),
        evidencia({ id: 'ev-2' }),
        evidencia({ id: 'ev-3' }),
        evidencia({ id: 'ev-4' }),
      ],
    } as never)
    renderModal()
    await act(async () => {})

    selectFiles([new File(['a'], 'a.png', { type: 'image/png' })])

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Cada avance permite máximo 4 evidencias.',
    )
    expect(subir).not.toHaveBeenCalled()
  })

  it('deshabilita la carga al alcanzar el máximo', async () => {
    listar.mockResolvedValue({
      data: [
        evidencia({ id: 'ev-1' }),
        evidencia({ id: 'ev-2', tamano_almacenado: 500 }),
        evidencia({ id: 'ev-3', tamano_almacenado: 2097152 }),
        evidencia({ id: 'ev-4', nombre: 'nota.txt', tipo: 'text/plain' }),
      ],
    } as never)
    renderModal()
    await act(async () => {})

    expect(screen.getByText('500 B')).toBeInTheDocument()
    expect(screen.getByText('2.00 MB')).toBeInTheDocument()
    expect(screen.getByText('Máximo 4 evidencias')).toBeInTheDocument()
    expect(document.getElementById('evidencia-modal-input')).toBeDisabled()
  })

  it('muestra error cuando la subida falla', async () => {
    subir.mockRejectedValue(new Error('network') as never)
    renderModal()
    await act(async () => {})

    selectFiles([new File(['a'], 'a.png', { type: 'image/png' })])

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'No fue posible subir las evidencias.',
    )
  })
})

describe('descarga de evidencias', () => {
  it('descarga la evidencia seleccionada', async () => {
    const user = userEvent.setup()
    const clickSpy = vi
      .spyOn(HTMLAnchorElement.prototype, 'click')
      .mockImplementation(() => undefined)
    listar.mockResolvedValue({
      data: [evidencia({ id: 'ev-2', nombre: 'zip-anexo.zip', tipo: 'application/octet-stream' })],
    } as never)
    renderModal()
    await act(async () => {})

    await user.click(screen.getByTitle('Descargar'))

    expect(descargar).toHaveBeenCalledWith('av-1', 'ev-2')
    expect(URL.createObjectURL).toHaveBeenCalledTimes(1)
    expect(clickSpy).toHaveBeenCalledTimes(1)
    expect(clickSpy.mock.instances[0]).toHaveProperty('download', 'zip-anexo.zip')
  })

  it('muestra error cuando la descarga falla', async () => {
    const user = userEvent.setup()
    listar.mockResolvedValue({
      data: [evidencia({ id: 'ev-2', nombre: 'zip-anexo.zip', tipo: 'application/octet-stream' })],
    } as never)
    descargar.mockRejectedValue(new Error('network') as never)
    renderModal()
    await act(async () => {})

    await user.click(screen.getByTitle('Descargar'))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'No fue posible descargar la evidencia.',
    )
  })
})

describe('descripción de evidencias', () => {
  it('guarda la descripción editada', async () => {
    const user = userEvent.setup()
    listar.mockResolvedValue({
      data: [evidencia({ id: 'ev-2', nombre: 'zip-anexo.zip', tipo: 'application/octet-stream' })],
    } as never)
    renderModal({ canEdit: true })
    await act(async () => {})

    await user.click(screen.getByTitle('Editar descripción'))
    const textarea = screen.getByRole('textbox')
    expect(textarea).toHaveValue('')

    await user.type(textarea, 'acta del comite')
    await user.click(screen.getByTitle('Guardar'))

    expect(actualizarDescripcion).toHaveBeenCalledWith('av-1', 'ev-2', 'acta del comite')
    expect(screen.getByText('acta del comite')).toBeInTheDocument()
    expect(screen.queryByRole('textbox')).toBeNull()
  })

  it('conserva la edición cuando el guardado falla', async () => {
    const user = userEvent.setup()
    actualizarDescripcion.mockRejectedValue(new Error('network') as never)
    listar.mockResolvedValue({
      data: [evidencia({ id: 'ev-2', nombre: 'zip-anexo.zip', tipo: 'application/octet-stream' })],
    } as never)
    renderModal({ canEdit: true })
    await act(async () => {})

    await user.click(screen.getByTitle('Editar descripción'))
    await user.type(screen.getByRole('textbox'), 'borrador')
    await user.click(screen.getByTitle('Guardar'))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'No fue posible guardar la descripción.',
    )
    expect(screen.getByRole('textbox')).toHaveValue('borrador')
  })

  it('cancela la edición sin guardar', async () => {
    const user = userEvent.setup()
    listar.mockResolvedValue({ data: [evidencia()] } as never)
    renderModal({ canEdit: true })
    await act(async () => {})

    await user.click(screen.getByTitle('Editar descripción'))
    await user.type(screen.getByRole('textbox'), 'temporal')
    await user.click(screen.getByTitle('Cancelar'))

    expect(screen.queryByRole('textbox')).toBeNull()
    expect(actualizarDescripcion).not.toHaveBeenCalled()
    expect(screen.getByText('Sin descripción')).toBeInTheDocument()
  })
})

describe('eliminación de evidencias', () => {
  it('elimina tras confirmar', async () => {
    const user = userEvent.setup()
    listar.mockResolvedValue({
      data: [evidencia({ id: 'ev-2', nombre: 'zip-anexo.zip', tipo: 'application/octet-stream' })],
    } as never)
    renderModal({ canEdit: true })
    await act(async () => {})

    await user.click(screen.getByTitle('Eliminar evidencia'))
    expect(screen.getByTitle('Confirmar eliminación')).toBeInTheDocument()
    await user.click(screen.getByTitle('Confirmar eliminación'))

    expect(eliminar).toHaveBeenCalledWith('av-1', 'ev-2')
    expect(screen.queryByText('zip-anexo.zip')).toBeNull()
  })

  it('cancela la eliminación en la confirmación', async () => {
    const user = userEvent.setup()
    listar.mockResolvedValue({ data: [evidencia()] } as never)
    renderModal({ canEdit: true })
    await act(async () => {})

    await user.click(screen.getByTitle('Eliminar evidencia'))
    await user.click(screen.getByTitle('Cancelar'))

    expect(eliminar).not.toHaveBeenCalled()
    expect(screen.getByText('foto-avance.png')).toBeInTheDocument()
  })

  it('muestra error cuando la eliminación falla', async () => {
    const user = userEvent.setup()
    listar.mockResolvedValue({ data: [evidencia()] } as never)
    eliminar.mockRejectedValue(new Error('network') as never)
    renderModal({ canEdit: true })
    await act(async () => {})

    await user.click(screen.getByTitle('Eliminar evidencia'))
    await user.click(screen.getByTitle('Confirmar eliminación'))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'No fue posible eliminar la evidencia.',
    )
    expect(screen.getByText('foto-avance.png')).toBeInTheDocument()
  })
})

describe('permisos y cierre', () => {
  it('oculta los controles de edición sin permiso', async () => {
    renderModal({ canEdit: false })
    await act(async () => {})

    expect(screen.queryByTitle('Editar descripción')).toBeNull()
    expect(screen.queryByTitle('Eliminar evidencia')).toBeNull()
    expect(document.getElementById('evidencia-modal-input')).toBeNull()
    expect(screen.queryByText(/Agregar evidencias/)).toBeNull()
    expect(screen.getByText('Cerrar')).toBeInTheDocument()
  })

  it('cierra desde el botón del pie', async () => {
    const user = userEvent.setup()
    const { onClose } = renderModal()
    await act(async () => {})

    await user.click(screen.getByText('Cerrar'))

    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('cierra desde el botón de la cabecera', async () => {
    const user = userEvent.setup()
    const { onClose } = renderModal()
    await act(async () => {})

    await user.click(screen.getByLabelText('Cerrar'))

    expect(onClose).toHaveBeenCalledTimes(1)
  })
})
