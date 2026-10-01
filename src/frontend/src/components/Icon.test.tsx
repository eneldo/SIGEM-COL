import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import {
  MIconBuilding,
  MIconChart,
  MIconCheck,
  MIconDocument,
  MIconInfo,
  MIconSchool,
  MIconTrendingUp,
  MIconUser,
  MIconWarning,
} from './Icon'

const iconos = [
  MIconBuilding,
  MIconChart,
  MIconCheck,
  MIconDocument,
  MIconInfo,
  MIconSchool,
  MIconTrendingUp,
  MIconUser,
  MIconWarning,
]

describe('Icon', () => {
  it('renderiza todos los iconos exportados', () => {
    for (const Icono of iconos) {
      const { container, unmount } = render(<Icono className="h-5 w-5" />)
      const svg = container.querySelector('svg')

      expect(svg).toBeInTheDocument()
      expect(svg).toHaveClass('h-5', 'w-5')
      expect(svg?.querySelector('path')).toBeInTheDocument()

      unmount()
    }
  })

  it('renderiza sin className personalizado', () => {
    const { container } = render(<MIconCheck />)
    const svg = container.querySelector('svg')

    expect(svg).toBeInTheDocument()
    expect(svg).not.toHaveClass('h-5')
  })
})
