import { useState } from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { Input } from './Input'

function ControlledInput() {
  const [value, setValue] = useState('')
  return (
    <Input
      label="Usuario"
      placeholder="Ingrese su usuario"
      value={value}
      onChange={(event) => setValue(event.target.value)}
    />
  )
}

describe('Input', () => {
  it('asocia la etiqueta con el campo', () => {
    render(<Input label="Usuario" />)

    const input = screen.getByLabelText('Usuario')
    expect(input).toBeInTheDocument()
    expect(input).toHaveAttribute('id', 'usuario')
  })

  it('respeta el id proporcionado', () => {
    render(<Input label="Usuario" id="campo-usuario" />)

    expect(screen.getByLabelText('Usuario')).toHaveAttribute('id', 'campo-usuario')
  })

  it('no renderiza etiqueta ni mensaje sin props opcionales', () => {
    const { container } = render(<Input placeholder="Buscar" />)

    expect(container.querySelector('label')).toBeNull()
    expect(container.querySelector('p')).toBeNull()
    expect(screen.getByPlaceholderText('Buscar')).toBeInTheDocument()
  })

  it('refleja la escritura del usuario', async () => {
    const user = userEvent.setup()
    render(<ControlledInput />)

    await user.type(screen.getByLabelText('Usuario'), 'ana')

    expect(screen.getByLabelText('Usuario')).toHaveValue('ana')
  })

  it('muestra el mensaje de error', () => {
    render(<Input label="Usuario" error="Campo obligatorio" helperText="Ayuda" />)

    expect(screen.getByText('Campo obligatorio')).toBeInTheDocument()
    expect(screen.queryByText('Ayuda')).toBeNull()
  })

  it('muestra el texto de ayuda cuando no hay error', () => {
    render(<Input label="Usuario" helperText="Mínimo 6 caracteres" />)

    expect(screen.getByText('Mínimo 6 caracteres')).toBeInTheDocument()
  })

  it('renderiza los iconos laterales', () => {
    const { container } = render(
      <Input
        label="Buscar"
        leftIcon={<span data-testid="izquierdo" />}
        rightIcon={<span data-testid="derecho" />}
      />,
    )

    expect(screen.getByTestId('izquierdo')).toBeInTheDocument()
    expect(screen.getByTestId('derecho')).toBeInTheDocument()
    expect(container.querySelector('input')).toHaveClass('pl-10', 'pr-10')
  })

  it('propaga el tipo de contraseña', () => {
    render(<Input label="Contraseña" type="password" />)

    expect(screen.getByLabelText('Contraseña')).toHaveAttribute('type', 'password')
  })

  it('marca el campo como requerido', () => {
    const onChange = vi.fn()
    render(<Input label="Usuario" required onChange={onChange} />)

    expect(screen.getByLabelText('Usuario')).toBeRequired()
  })
})
