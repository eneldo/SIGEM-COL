import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Personalizacion } from './types'

export const DEFAULT_BRANDING: Personalizacion = {
  color_primario: '#0f3d3b',
  color_secundario: '#b9852f',
  nombre_sistema: 'SIGEM Colombia',
  logo_data_url: null,
}

type Rgb = [number, number, number]

const BLACK: Rgb = [0, 0, 0]
const WHITE: Rgb = [255, 255, 255]
const DEFAULT_PRIMARIO: Rgb = [15, 61, 59]
const DEFAULT_SECUNDARIO: Rgb = [185, 133, 47]
const DEFAULT_FAVICON = '/favicon.svg'

function parseHex(hex: string): Rgb | null {
  const match = /^#([0-9a-fA-F]{6})$/.exec(hex)
  if (!match) return null
  const value = Number.parseInt(match[1], 16)
  return [(value >> 16) & 255, (value >> 8) & 255, value & 255]
}

function mix(base: Rgb, target: Rgb, weight: number): Rgb {
  return [
    Math.round(base[0] + (target[0] - base[0]) * weight),
    Math.round(base[1] + (target[1] - base[1]) * weight),
    Math.round(base[2] + (target[2] - base[2]) * weight),
  ]
}

function toTriplet(rgb: Rgb): string {
  return `${rgb[0]} ${rgb[1]} ${rgb[2]}`
}

function resolveColor(hex: string, fallback: Rgb): Rgb {
  return parseHex(hex) ?? fallback
}

export function applyBranding(config: Personalizacion): void {
  const primario = resolveColor(config.color_primario, DEFAULT_PRIMARIO)
  const secundario = resolveColor(config.color_secundario, DEFAULT_SECUNDARIO)
  const root = document.documentElement
  const usaColoresPorDefecto =
    config.color_primario === DEFAULT_BRANDING.color_primario &&
    config.color_secundario === DEFAULT_BRANDING.color_secundario

  if (usaColoresPorDefecto) {
    root.style.removeProperty('--pine')
    root.style.removeProperty('--pine-deep')
    root.style.removeProperty('--ochre')
    root.style.removeProperty('--ochre-deep')
    root.style.removeProperty('--ochre-soft')
  } else {
    root.style.setProperty('--pine', toTriplet(primario))
    root.style.setProperty('--pine-deep', toTriplet(mix(primario, BLACK, 0.3)))
    root.style.setProperty('--ochre', toTriplet(secundario))
    root.style.setProperty('--ochre-deep', toTriplet(mix(secundario, BLACK, 0.23)))
    root.style.setProperty('--ochre-soft', toTriplet(mix(secundario, WHITE, 0.85)))
  }

  document.title = config.nombre_sistema

  const favicon = document.querySelector<HTMLLinkElement>('link[rel~="icon"]')
  if (favicon) {
    favicon.href = config.logo_data_url ?? DEFAULT_FAVICON
  }
}

interface BrandingState {
  config: Personalizacion
  setBranding: (config: Personalizacion) => void
}

export const useBrandingStore = create<BrandingState>()(
  persist(
    (set) => ({
      config: DEFAULT_BRANDING,
      setBranding: (config: Personalizacion) => {
        applyBranding(config)
        set({ config })
      },
    }),
    {
      name: 'sigem-branding',
      partialize: (state) => ({ config: state.config }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          applyBranding(state.config)
        }
      },
    },
  ),
)
