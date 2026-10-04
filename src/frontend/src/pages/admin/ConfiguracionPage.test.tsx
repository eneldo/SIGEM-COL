import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ConfiguracionPage } from './ConfiguracionPage'

describe('ConfiguracionPage', () => {
  it('renderiza el encabezado del panel de configuración', () => {
    render(<ConfiguracionPage />)

    expect(
      screen.getByRole('heading', { level: 1, name: 'Panel de configuración' }),
    ).toBeInTheDocument()
    expect(screen.getByText('Configuración')).toBeInTheDocument()
    expect(
      screen.getByText(
        'Administre los módulos del sistema, usuarios, roles, permisos y la apariencia de la plataforma.',
      ),
    ).toBeInTheDocument()
  })

  it('muestra los cuatro módulos con sus descripciones y enlaces', () => {
    render(<ConfiguracionPage />)

    expect(screen.getAllByRole('link')).toHaveLength(4)

    expect(
      screen.getByRole('link', { name: /Usuarios del sistema/ }),
    ).toHaveAttribute('href', '/admin/configuracion/usuarios')
    expect(
      screen.getByRole('link', { name: /Roles y permisos/ }),
    ).toHaveAttribute('href', '/admin/configuracion/roles')
    expect(
      screen.getByRole('link', { name: /Auditoría/ }),
    ).toHaveAttribute('href', '/admin/configuracion/auditoria')
    expect(
      screen.getByRole('link', { name: /Personalización/ }),
    ).toHaveAttribute('href', '/admin/configuracion/personalizacion')

    expect(
      screen.getByText(
        'Administre cuentas de acceso, credenciales y roles de los usuarios.',
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        'Defina roles del sistema y asigne permisos de acceso por módulo.',
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        'Consulte el registro de eventos y acciones realizadas en el sistema.',
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        'Configure colores, logotipo y información visual del sistema.',
      ),
    ).toBeInTheDocument()
    expect(screen.getAllByText('Ir al módulo →')).toHaveLength(4)
  })
})
