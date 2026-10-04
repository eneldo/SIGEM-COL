import { afterEach, describe, expect, it, vi } from 'vitest'
import { DEFAULT_BRANDING, applyBranding, useBrandingStore } from './branding'

function crearLinkIcono(): HTMLLinkElement {
  const link = document.createElement('link')
  link.setAttribute('rel', 'icon')
  document.head.appendChild(link)
  return link
}

afterEach(() => {
  document.head.querySelectorAll('link[rel~="icon"]').forEach((node) => node.remove())
  document.documentElement.removeAttribute('style')
  localStorage.clear()
})

describe('applyBranding', () => {
  it('aplica colores personalizados con derivados, título y favicon', () => {
    const link = crearLinkIcono()

    applyBranding({
      color_primario: '#123456',
      color_secundario: '#654321',
      nombre_sistema: 'Municipio Demo',
      logo_data_url: 'data:image/png;base64,AAAA',
    })

    expect(document.documentElement.style.getPropertyValue('--pine')).toBe('18 52 86')
    expect(document.documentElement.style.getPropertyValue('--pine-deep')).toBe('13 36 60')
    expect(document.documentElement.style.getPropertyValue('--ochre')).toBe('101 67 33')
    expect(document.documentElement.style.getPropertyValue('--ochre-deep')).toBe('78 52 25')
    expect(document.documentElement.style.getPropertyValue('--ochre-soft')).toBe('232 227 222')
    expect(document.title).toBe('Municipio Demo')
    expect(link.getAttribute('href')).toBe('data:image/png;base64,AAAA')
  })

  it('conserva los colores por defecto del CSS sin variables en línea', () => {
    applyBranding({
      color_primario: '#123456',
      color_secundario: '#654321',
      nombre_sistema: 'Otro',
      logo_data_url: null,
    })

    applyBranding(DEFAULT_BRANDING)

    expect(document.documentElement.style.getPropertyValue('--pine')).toBe('')
    expect(document.documentElement.style.getPropertyValue('--pine-deep')).toBe('')
    expect(document.documentElement.style.getPropertyValue('--ochre')).toBe('')
    expect(document.documentElement.style.getPropertyValue('--ochre-deep')).toBe('')
    expect(document.documentElement.style.getPropertyValue('--ochre-soft')).toBe('')
    expect(document.title).toBe('SIGEM Colombia')
  })

  it('usa el color por defecto cuando el valor no es hexadecimal', () => {
    applyBranding({
      ...DEFAULT_BRANDING,
      color_primario: 'no-es-color',
      color_secundario: 'tampoco-es-color',
    })

    expect(document.documentElement.style.getPropertyValue('--pine')).toBe('15 61 59')
    expect(document.documentElement.style.getPropertyValue('--ochre')).toBe('185 133 47')
  })

  it('aplica el favicon por defecto cuando no hay logotipo', () => {
    const link = crearLinkIcono()

    applyBranding({ ...DEFAULT_BRANDING, color_primario: '#123456' })

    expect(link.getAttribute('href')).toBe('/favicon.svg')
  })

  it('no falla cuando el documento no tiene favicon', () => {
    expect(() =>
      applyBranding({ ...DEFAULT_BRANDING, color_primario: '#123456' }),
    ).not.toThrow()
  })
})

describe('useBrandingStore', () => {
  it('setBranding aplica los cambios y actualiza el estado', () => {
    const config = {
      color_primario: '#123456',
      color_secundario: '#654321',
      nombre_sistema: 'Otro Municipio',
      logo_data_url: 'data:image/svg+xml;base64,AAAA',
    }

    useBrandingStore.getState().setBranding(config)

    expect(useBrandingStore.getState().config).toEqual(config)
    expect(document.documentElement.style.getPropertyValue('--pine')).toBe('18 52 86')
    const persistido = JSON.parse(localStorage.getItem('sigem-branding') ?? '{}')
    expect(persistido.state.config).toEqual(config)
  })

  it('restaura los valores por defecto al guardar la configuración inicial', () => {
    useBrandingStore.getState().setBranding({ ...DEFAULT_BRANDING, color_primario: '#123456' })

    useBrandingStore.getState().setBranding(DEFAULT_BRANDING)

    expect(document.documentElement.style.getPropertyValue('--pine')).toBe('')
    expect(useBrandingStore.getState().config).toEqual(DEFAULT_BRANDING)
  })
})

describe('persistencia del branding', () => {
  afterEach(() => {
    vi.resetModules()
    localStorage.clear()
  })

  it('aplica la configuración persistida al rehidratar', async () => {
    localStorage.setItem(
      'sigem-branding',
      JSON.stringify({
        state: {
          config: {
            color_primario: '#123456',
            color_secundario: '#b9852f',
            nombre_sistema: 'Persistido',
            logo_data_url: null,
          },
        },
        version: 0,
      }),
    )
    vi.resetModules()

    const modulo = await import('./branding')

    expect(modulo.useBrandingStore.getState().config.nombre_sistema).toBe('Persistido')
    expect(document.documentElement.style.getPropertyValue('--pine')).toBe('18 52 86')
  })

  it('mantiene la configuración por defecto con almacenamiento corrupto', async () => {
    localStorage.setItem('sigem-branding', '{corrupto')
    vi.resetModules()

    const modulo = await import('./branding')

    expect(modulo.useBrandingStore.getState().config).toEqual(modulo.DEFAULT_BRANDING)
  })
})
