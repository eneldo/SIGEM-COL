import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { Button } from './Button'

type ButtonProps = Parameters<typeof Button>[0]
type Variant = NonNullable<ButtonProps['variant']>
type Size = NonNullable<ButtonProps['size']>

describe('Button', () => {
  it('renderiza el contenido', () => {
    render(<Button>Guardar</Button>)

    expect(screen.getByRole('button', { name: 'Guardar' })).toBeInTheDocument()
  })

  it('usa la variante primaria por defecto', () => {
    render(<Button>Guardar</Button>)

    expect(screen.getByRole('button')).toHaveClass('bg-pine')
  })

  it.each<[Variant, string]>([
    ['secondary', 'bg-forest'],
    ['danger', 'bg-warn'],
    ['ghost', 'bg-transparent'],
  ])('aplica la variante %s', (variant, expectedClass) => {
    render(<Button variant={variant}>Guardar</Button>)

    expect(screen.getByRole('button')).toHaveClass(expectedClass)
  })

  it.each<[Size, string]>([
    ['sm', 'px-3'],
    ['md', 'px-4'],
    ['lg', 'px-6'],
  ])('aplica el tamaño %s', (size, expectedClass) => {
    render(<Button size={size}>Guardar</Button>)

    expect(screen.getByRole('button')).toHaveClass(expectedClass)
  })

  it('ejecuta onClick al presionarlo', async () => {
    const user = userEvent.setup()
    const onClick = vi.fn()
    render(<Button onClick={onClick}>Guardar</Button>)

    await user.click(screen.getByRole('button'))

    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('no responde a clicks cuando está deshabilitado', async () => {
    const user = userEvent.setup()
    const onClick = vi.fn()
    render(
      <Button disabled onClick={onClick}>
        Guardar
      </Button>,
    )

    const boton = screen.getByRole('button')
    expect(boton).toBeDisabled()
    expect(boton).toHaveAttribute('aria-disabled', 'true')

    await user.click(boton)
    expect(onClick).not.toHaveBeenCalled()
  })

  it('muestra el spinner y bloquea la interacción mientras carga', async () => {
    const user = userEvent.setup()
    const onClick = vi.fn()
    render(
      <Button loading onClick={onClick}>
        Guardar
      </Button>,
    )

    const boton = screen.getByRole('button')
    expect(boton).toBeDisabled()
    expect(boton).toHaveAttribute('aria-busy', 'true')
    expect(boton.querySelector('svg')).toBeInTheDocument()

    await user.click(boton)
    expect(onClick).not.toHaveBeenCalled()
  })
})
