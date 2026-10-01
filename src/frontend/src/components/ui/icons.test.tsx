import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { Icon, EstadoBadge, ModalShell, formatDate, formatDateOnly } from './icons'

describe('formatDate', () => {
  it('devuelve Sin registro sin fecha', () => {
    expect(formatDate()).toBe('Sin registro')
    expect(formatDate(null)).toBe('Sin registro')
  })

  it('formatea una fecha ISO completa', () => {
    expect(formatDate('2026-03-10T15:00:00.000Z')).toContain('2026')
  })
})

describe('formatDateOnly', () => {
  it('devuelve Sin registro sin fecha', () => {
    expect(formatDateOnly()).toBe('Sin registro')
    expect(formatDateOnly(null)).toBe('Sin registro')
  })

  it('interpreta fechas sin hora como fecha local', () => {
    expect(formatDateOnly('2026-03-10')).toContain('2026')
  })

  it('formatea fechas completas', () => {
    expect(formatDateOnly('2026-03-10T15:00:00.000Z')).toContain('2026')
  })
})

describe('Icon', () => {
  it('renderiza el svg como decorativo', () => {
    const { container } = render(<Icon name="check" className="h-8 w-8" />)

    const svg = container.querySelector('svg')
    expect(svg).toHaveAttribute('aria-hidden', 'true')
    expect(svg).toHaveClass('h-8', 'w-8')
    expect(svg?.querySelector('path')).toHaveAttribute('d', expect.any(String))
  })
})

describe('EstadoBadge', () => {
  it('destaca los estados activos', () => {
    render(<EstadoBadge estado="ACTIVA" />)

    const badge = screen.getByText('ACTIVA')
    expect(badge).toHaveClass('bg-forest-soft')
  })

  it('usa tono neutro para el resto de estados', () => {
    render(<EstadoBadge estado="PENDIENTE" />)

    expect(screen.getByText('PENDIENTE')).toHaveClass('bg-line/60')
  })
})

describe('ModalShell', () => {
  it('renderiza título, descripción y contenido', () => {
    render(
      <ModalShell title="Asignar producto" description="Paso 1" close={vi.fn()}>
        <p>contenido</p>
      </ModalShell>,
    )

    const dialogo = screen.getByRole('dialog', { name: 'Asignar producto' })
    expect(dialogo).toHaveAttribute('aria-modal', 'true')
    expect(screen.getByText('Paso 1')).toBeInTheDocument()
    expect(screen.getByText('contenido')).toBeInTheDocument()
  })

  it('aplica el ancho amplio cuando se solicita', () => {
    const { container } = render(
      <ModalShell title="Evidencias" close={vi.fn()} wide>
        <p>contenido</p>
      </ModalShell>,
    )

    const dialogo = container.querySelector('section')
    expect(dialogo).toHaveClass('max-w-3xl')
  })

  it('usa ancho estándar por defecto', () => {
    const { container } = render(
      <ModalShell title="Evidencias" close={vi.fn()}>
        <p>contenido</p>
      </ModalShell>,
    )

    expect(container.querySelector('section')).toHaveClass('max-w-xl')
  })

  it('cierra desde el botón de la cabecera', async () => {
    const close = vi.fn()
    render(
      <ModalShell title="Asignar producto" close={close}>
        <p>contenido</p>
      </ModalShell>,
    )

    fireEvent.click(screen.getByLabelText('Cerrar'))
    expect(close).toHaveBeenCalledTimes(1)
  })

  it('cierra al pulsar el fondo', () => {
    const close = vi.fn()
    const { container } = render(
      <ModalShell title="Asignar producto" close={close}>
        <p>contenido</p>
      </ModalShell>,
    )

    fireEvent.mouseDown(container.firstElementChild as HTMLElement)
    expect(close).toHaveBeenCalledTimes(1)
  })

  it('no cierra al pulsar sobre el diálogo', () => {
    const close = vi.fn()
    render(
      <ModalShell title="Asignar producto" close={close}>
        <p>contenido</p>
      </ModalShell>,
    )

    fireEvent.mouseDown(screen.getByRole('dialog'))
    expect(close).not.toHaveBeenCalled()
  })
})
