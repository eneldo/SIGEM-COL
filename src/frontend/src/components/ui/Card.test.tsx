import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Card, CardContent, CardFooter, CardHeader } from './Card'

describe('Card', () => {
  it('renderiza los hijos', () => {
    render(
      <Card>
        <p>Contenido de la tarjeta</p>
      </Card>,
    )

    expect(screen.getByText('Contenido de la tarjeta')).toBeInTheDocument()
  })

  it('combina className propio con los estilos base', () => {
    const { container } = render(<Card className="mi-clase">hola</Card>)

    const card = container.firstElementChild as HTMLElement
    expect(card).toHaveClass('mi-clase')
    expect(card).toHaveClass('bg-paper-raised', 'rounded-xl')
  })

  it('renderiza las secciones con sus estilos', () => {
    render(
      <Card>
        <CardHeader className="header-propio">Encabezado</CardHeader>
        <CardContent>Detalle</CardContent>
        <CardFooter>Pie</CardFooter>
      </Card>,
    )

    const header = screen.getByText('Encabezado')
    expect(header).toHaveClass('border-b', 'header-propio')

    const content = screen.getByText('Detalle')
    expect(content).toHaveClass('px-6', 'py-4')

    const footer = screen.getByText('Pie')
    expect(footer).toHaveClass('border-t')
  })
})
