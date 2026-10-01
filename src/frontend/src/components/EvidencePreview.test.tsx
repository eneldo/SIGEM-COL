import { act, fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { gestorDashboard } from '../lib/api'
import { EvidencePreview } from './EvidencePreview'
import type { Evidencia } from '../lib/types'

vi.mock('../lib/api', () => ({
  gestorDashboard: {
    descargarEvidenciaPorId: vi.fn(),
  },
  default: {},
}))

const descargar = vi.mocked(gestorDashboard.descargarEvidenciaPorId)

function evidencia(overrides: Partial<Evidencia> = {}): Evidencia {
  return {
    id: 'ev-1',
    avance_id: 'av-1',
    nombre: 'foto-avance.png',
    tipo: 'image/png',
    url: '/media/foto-avance.png',
    descripcion: null,
    tamano_original: 1024,
    tamano_almacenado: 512,
    optimizada: false,
    created_at: null,
    ...overrides,
  }
}

const nombreBoton = 'Ver vista previa de foto-avance.png'

beforeEach(() => {
  descargar.mockReset()
})

describe('EvidencePreview', () => {
  it('no ofrece vista previa ni descarga para tipos no soportados', () => {
    const { container } = render(
      <EvidencePreview avanceId="av-1" evidencia={evidencia({ tipo: 'application/zip' })} />,
    )

    expect(screen.queryByRole('button')).toBeNull()
    expect(descargar).not.toHaveBeenCalled()
    expect(container.querySelector('svg')).toBeInTheDocument()
  })

  it('muestra la miniatura deshabilitada mientras carga', () => {
    descargar.mockReturnValue(new Promise(() => {}))
    render(<EvidencePreview avanceId="av-1" evidencia={evidencia()} />)

    const boton = screen.getByRole('button', { name: nombreBoton })
    expect(boton).toBeDisabled()
    expect(boton.querySelector('img')).toBeNull()
    expect(descargar).toHaveBeenCalledWith('av-1', 'ev-1')
  })

  it('habilita la miniatura cuando la descarga termina', async () => {
    descargar.mockResolvedValue({ data: new Blob(['img']) } as never)
    render(<EvidencePreview avanceId="av-1" evidencia={evidencia()} />)

    await act(async () => {})

    const boton = screen.getByRole('button', { name: nombreBoton })
    expect(boton).toBeEnabled()
    expect(boton.querySelector('img')).toHaveAttribute('src', 'blob:mock-url')
    expect(URL.createObjectURL).toHaveBeenCalledWith(expect.any(Blob))
  })

  it('permanece deshabilitado y sin miniatura cuando la descarga falla', async () => {
    descargar.mockRejectedValue(new Error('500') as never)
    render(<EvidencePreview avanceId="av-1" evidencia={evidencia()} />)

    await act(async () => {})

    const boton = screen.getByRole('button', { name: nombreBoton })
    expect(descargar).toHaveBeenCalledTimes(1)
    expect(boton).toBeDisabled()
    expect(boton.querySelector('img')).toBeNull()
    expect(URL.createObjectURL).not.toHaveBeenCalled()
  })

  it('abre y cierra la vista previa con el botón de cierre', async () => {
    const user = userEvent.setup()
    descargar.mockResolvedValue({ data: new Blob(['img']) } as never)
    render(<EvidencePreview avanceId="av-1" evidencia={evidencia()} />)
    await act(async () => {})

    await user.click(screen.getByRole('button', { name: nombreBoton }))

    const dialogo = await screen.findByRole('dialog')
    expect(dialogo).toHaveAccessibleName('Vista previa de foto-avance.png')
    expect(screen.getByAltText('Vista previa de foto-avance.png')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Cerrar vista previa' }))
    expect(screen.queryByRole('dialog')).toBeNull()
  })

  it('cierra la vista previa con la tecla Escape', async () => {
    const user = userEvent.setup()
    descargar.mockResolvedValue({ data: new Blob(['img']) } as never)
    render(<EvidencePreview avanceId="av-1" evidencia={evidencia()} />)
    await act(async () => {})

    await user.click(screen.getByRole('button', { name: nombreBoton }))
    expect(await screen.findByRole('dialog')).toBeInTheDocument()

    await user.keyboard('{Escape}')
    expect(screen.queryByRole('dialog')).toBeNull()
  })

  it('cierra la vista previa al pulsar el fondo', async () => {
    const user = userEvent.setup()
    descargar.mockResolvedValue({ data: new Blob(['img']) } as never)
    render(<EvidencePreview avanceId="av-1" evidencia={evidencia()} />)
    await act(async () => {})

    await user.click(screen.getByRole('button', { name: nombreBoton }))
    const dialogo = await screen.findByRole('dialog')

    fireEvent.mouseDown(dialogo.parentElement as HTMLElement)
    expect(screen.queryByRole('dialog')).toBeNull()
  })

  it('muestra los PDF en un iframe dentro del diálogo', async () => {
    const user = userEvent.setup()
    descargar.mockResolvedValue({ data: new Blob(['pdf']) } as never)
    render(
      <EvidencePreview
        avanceId="av-1"
        evidencia={evidencia({ nombre: 'acta.pdf', tipo: 'application/pdf' })}
      />,
    )
    await act(async () => {})

    await user.click(screen.getByRole('button', { name: 'Ver vista previa de acta.pdf' }))

    await screen.findByRole('dialog')
    expect(screen.getByTitle('Vista previa de acta.pdf').tagName).toBe('IFRAME')
  })

  it('libera el object URL al desmontar', async () => {
    descargar.mockResolvedValue({ data: new Blob(['img']) } as never)
    const { unmount } = render(<EvidencePreview avanceId="av-1" evidencia={evidencia()} />)
    await act(async () => {})

    expect(URL.createObjectURL).toHaveBeenCalled()
    expect(URL.revokeObjectURL).not.toHaveBeenCalled()

    unmount()
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:mock-url')
  })
})
