import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { personalizacion } from '../../lib/api'
import { DEFAULT_BRANDING, useBrandingStore } from '../../lib/branding'
import type { Personalizacion } from '../../lib/types'
import { PersonalizacionPage } from './PersonalizacionPage'

vi.mock('../../lib/api', () => ({
  personalizacion: {
    get: vi.fn(),
    update: vi.fn(),
  },
}))

const getMock = vi.mocked(personalizacion.get)
const updateMock = vi.mocked(personalizacion.update)

const configuracionPorDefecto: Personalizacion = {
  color_primario: '#0f3d3b',
  color_secundario: '#b9852f',
  nombre_sistema: 'SIGEM Colombia',
  logo_data_url: null,
}

beforeEach(() => {
  getMock.mockResolvedValue({ data: { ...configuracionPorDefecto } } as never)
  updateMock.mockResolvedValue({ data: { ...configuracionPorDefecto } } as never)
  useBrandingStore.setState({ config: DEFAULT_BRANDING })
  localStorage.clear()
})

afterEach(() => {
  vi.useRealTimers()
})

function renderPagina() {
  const utils = render(<PersonalizacionPage />)
  const inputs = utils.container.querySelectorAll('input')
  return { ...utils, inputs }
}

async function renderPaginaCargada() {
  const utils = renderPagina()
  await act(async () => {})
  return utils
}

describe('PersonalizacionPage', () => {
  it('renderiza la página con los valores por defecto', async () => {
    const { inputs, container } = await renderPaginaCargada()

    expect(screen.getByRole('heading', { name: 'Personalización' })).toBeInTheDocument()
    expect(screen.getByText('Colores del sistema')).toBeInTheDocument()
    expect(screen.getByText('Información institucional')).toBeInTheDocument()
    expect(screen.getByText('Formatos aceptados: PNG, SVG')).toBeInTheDocument()
    expect(inputs[0]).toHaveAttribute('type', 'color')
    expect(inputs[1]).toHaveValue('#0f3d3b')
    expect(inputs[2]).toHaveAttribute('type', 'color')
    expect(inputs[3]).toHaveValue('#b9852f')
    expect(inputs[4]).toHaveValue('SIGEM Colombia')
    expect(inputs[5]).toHaveAttribute('type', 'file')
    expect(container.querySelectorAll('div.h-12')).toHaveLength(2)
    expect(screen.getByRole('button', { name: 'Guardar cambios' })).toBeEnabled()
  })

  it('carga la configuración existente desde el servidor', async () => {
    getMock.mockResolvedValue({
      data: {
        color_primario: '#112233',
        color_secundario: '#445566',
        nombre_sistema: 'Municipio Andino',
        logo_data_url: 'data:image/png;base64,AAAA',
      },
    } as never)
    const { inputs } = renderPagina()

    await waitFor(() => expect(inputs[4]).toHaveValue('Municipio Andino'))
    expect(inputs[1]).toHaveValue('#112233')
    expect(inputs[3]).toHaveValue('#445566')
    expect(screen.getByAltText('Logotipo cargado')).toBeInTheDocument()
    expect(getMock).toHaveBeenCalledTimes(1)
  })

  it('mantiene los valores por defecto cuando la carga falla', async () => {
    getMock.mockRejectedValue(new Error('sin conexión') as never)
    const { inputs } = renderPagina()

    await act(async () => {})

    expect(inputs[1]).toHaveValue('#0f3d3b')
    expect(inputs[3]).toHaveValue('#b9852f')
    expect(inputs[4]).toHaveValue('SIGEM Colombia')
  })

  it('ignora la respuesta del servidor si se desmonta antes de que llegue', async () => {
    let resolver: (respuesta: unknown) => void = () => {}
    getMock.mockReturnValue(
      new Promise((resolve) => {
        resolver = resolve
      }) as never,
    )
    const { unmount, inputs } = renderPagina()

    unmount()
    resolver({ data: { ...configuracionPorDefecto } })
    await act(async () => {})

    expect(inputs[1]).toHaveValue('#0f3d3b')
  })

  it('actualiza el color primario desde el selector de color', async () => {
    const { inputs } = await renderPaginaCargada()

    fireEvent.change(inputs[0], { target: { value: '#123456' } })

    expect(inputs[0]).toHaveValue('#123456')
    expect(inputs[1]).toHaveValue('#123456')
  })

  it('actualiza el color primario desde el campo de texto', async () => {
    const user = userEvent.setup()
    const { inputs } = await renderPaginaCargada()

    await user.clear(inputs[1])
    await user.type(inputs[1], '#ABCDEF')

    expect(inputs[1]).toHaveValue('#ABCDEF')
    expect(inputs[0]).toHaveValue('#abcdef')
  })

  it('actualiza el color secundario desde el selector y el campo de texto', async () => {
    const user = userEvent.setup()
    const { inputs } = await renderPaginaCargada()

    fireEvent.change(inputs[2], { target: { value: '#654321' } })
    expect(inputs[3]).toHaveValue('#654321')

    await user.clear(inputs[3])
    await user.type(inputs[3], '#FEDCBA')

    expect(inputs[3]).toHaveValue('#FEDCBA')
    expect(inputs[2]).toHaveValue('#fedcba')
  })

  it('actualiza el nombre del sistema', async () => {
    const user = userEvent.setup()
    const { inputs } = await renderPaginaCargada()

    await user.clear(inputs[4])
    await user.type(inputs[4], 'Municipio Demo')

    expect(inputs[4]).toHaveValue('Municipio Demo')
  })

  it('carga el logotipo seleccionado y permite quitarlo', async () => {
    const { inputs } = await renderPaginaCargada()

    const file = new File(['contenido'], 'escudo.png', { type: 'image/png' })
    fireEvent.change(inputs[5], { target: { files: [file] } })

    await waitFor(() => expect(screen.getByAltText('Logotipo cargado')).toBeInTheDocument())
    expect(screen.getByRole('button', { name: 'Quitar logotipo' })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Quitar logotipo' }))

    expect(screen.queryByAltText('Logotipo cargado')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Quitar logotipo' })).not.toBeInTheDocument()
  })

  it('ignora la selección de archivo cancelada', async () => {
    const { inputs } = await renderPaginaCargada()

    fireEvent.change(inputs[5], { target: { files: [] } })

    expect(screen.queryByAltText('Logotipo cargado')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Quitar logotipo' })).not.toBeInTheDocument()
  })

  it('limpia la selección previa al abrir el selector de archivo', async () => {
    const { inputs } = await renderPaginaCargada()

    fireEvent.click(inputs[5])
    expect(inputs[5].value).toBe('')

    const file = new File(['png'], 'escudo.png', { type: 'image/png' })
    fireEvent.change(inputs[5], { target: { files: [file] } })

    await waitFor(() => expect(screen.getByAltText('Logotipo cargado')).toBeInTheDocument())
  })

  it('muestra los errores del logotipo junto a la zona de carga', async () => {
    await renderPaginaCargada()
    const zona = document.querySelector('label.cursor-pointer') as HTMLLabelElement

    const file = new File(['pdf'], 'documento.pdf', { type: 'application/pdf' })
    fireEvent.drop(zona, { dataTransfer: { files: [file] } })

    expect(screen.getByRole('alert')).toHaveTextContent('El logotipo debe ser una imagen PNG o SVG.')
  })

  it('asocia la etiqueta y la zona de vista previa con el input de archivo', async () => {
    const { inputs, container } = await renderPaginaCargada()

    expect(inputs[5]).toHaveAttribute('id', 'logo-input')
    expect(document.querySelectorAll('label[for="logo-input"]')).toHaveLength(2)
    expect(container.querySelector('label.cursor-pointer[for="logo-input"]')).not.toBeNull()
  })

  it('carga el logotipo al soltar un archivo PNG en la zona de vista previa', async () => {
    await renderPaginaCargada()
    const zona = document.querySelector('label.cursor-pointer') as HTMLLabelElement

    const file = new File(['png'], 'escudo.png', { type: 'image/png' })
    fireEvent.drop(zona, { dataTransfer: { files: [file] } })

    await waitFor(() => expect(screen.getByAltText('Logotipo cargado')).toBeInTheDocument())
  })

  it('acepta archivos con extensión .png cuando el tipo MIME viene vacío', async () => {
    await renderPaginaCargada()
    const zona = document.querySelector('label.cursor-pointer') as HTMLLabelElement

    const file = new File(['png'], 'escudo.PNG', { type: '' })
    fireEvent.drop(zona, { dataTransfer: { files: [file] } })

    await waitFor(() => expect(screen.getByAltText('Logotipo cargado')).toBeInTheDocument())
  })

  it('rechaza archivos que no son PNG ni SVG', async () => {
    await renderPaginaCargada()
    const zona = document.querySelector('label.cursor-pointer') as HTMLLabelElement

    const file = new File(['pdf'], 'documento.pdf', { type: 'application/pdf' })
    fireEvent.drop(zona, { dataTransfer: { files: [file] } })

    expect(screen.getByText('El logotipo debe ser una imagen PNG o SVG.')).toBeInTheDocument()
    expect(screen.queryByAltText('Logotipo cargado')).not.toBeInTheDocument()
  })

  it('rechaza archivos mayores a 2MB', async () => {
    await renderPaginaCargada()
    const zona = document.querySelector('label.cursor-pointer') as HTMLLabelElement

    const file = new File(['x'.repeat(2 * 1024 * 1024 + 1)], 'grande.png', { type: 'image/png' })
    fireEvent.drop(zona, { dataTransfer: { files: [file] } })

    expect(screen.getByText('El logotipo supera el tamaño máximo de 2MB.')).toBeInTheDocument()
    expect(screen.queryByAltText('Logotipo cargado')).not.toBeInTheDocument()
  })

  it('ignora el drop sin archivos', async () => {
    await renderPaginaCargada()
    const zona = document.querySelector('label.cursor-pointer') as HTMLLabelElement

    fireEvent.drop(zona, { dataTransfer: { files: [] } })

    expect(screen.queryByAltText('Logotipo cargado')).not.toBeInTheDocument()
    expect(screen.queryByText(/debe ser una imagen/)).not.toBeInTheDocument()
  })

  it('muestra un error cuando el archivo no se puede leer', async () => {
    const lector = {
      onload: null as (() => void) | null,
      onerror: null as (() => void) | null,
      readAsDataURL: () => {
        lector.onerror?.()
      },
    }
    vi.spyOn(window, 'FileReader').mockImplementation((() => lector) as unknown as () => FileReader)
    const { inputs } = await renderPaginaCargada()

    const file = new File(['png'], 'escudo.png', { type: 'image/png' })
    fireEvent.change(inputs[5], { target: { files: [file] } })

    expect(screen.getByText('No se pudo leer el archivo seleccionado.')).toBeInTheDocument()
    expect(screen.queryByAltText('Logotipo cargado')).not.toBeInTheDocument()
  })

  it('envía los cambios al servidor y aplica el branding guardado', async () => {
    const respuesta: Personalizacion = {
      color_primario: '#123456',
      color_secundario: '#654321',
      nombre_sistema: 'Municipio Demo',
      logo_data_url: null,
    }
    updateMock.mockResolvedValue({ data: respuesta } as never)
    vi.useFakeTimers()
    const { inputs } = await renderPaginaCargada()

    fireEvent.change(inputs[1], { target: { value: '#123456' } })
    fireEvent.change(inputs[3], { target: { value: '#654321' } })
    fireEvent.change(inputs[4], { target: { value: 'Municipio Demo' } })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar cambios' }))
    await act(async () => {})

    expect(updateMock).toHaveBeenCalledWith(respuesta)
    expect(useBrandingStore.getState().config).toEqual(respuesta)
    expect(document.documentElement.style.getPropertyValue('--pine')).toBe('18 52 86')
    expect(screen.getByText('Cambios guardados exitosamente.')).toBeInTheDocument()
  })

  it('muestra el mensaje de guardado y lo oculta después de tres segundos', async () => {
    vi.useFakeTimers()
    await renderPaginaCargada()

    fireEvent.click(screen.getByRole('button', { name: 'Guardar cambios' }))
    await act(async () => {})

    expect(screen.getByText('Cambios guardados exitosamente.')).toBeInTheDocument()

    act(() => {
      vi.advanceTimersByTime(3000)
    })

    expect(screen.queryByText('Cambios guardados exitosamente.')).not.toBeInTheDocument()
  })

  it('muestra un mensaje de error cuando el guardado falla', async () => {
    updateMock.mockRejectedValue(new Error('validación fallida') as never)
    vi.useFakeTimers()
    await renderPaginaCargada()

    fireEvent.click(screen.getByRole('button', { name: 'Guardar cambios' }))
    await act(async () => {})

    expect(
      screen.getByText('No se pudieron guardar los cambios. Revise los datos e intente de nuevo.'),
    ).toBeInTheDocument()
    expect(screen.queryByText('Cambios guardados exitosamente.')).not.toBeInTheDocument()
  })
})
