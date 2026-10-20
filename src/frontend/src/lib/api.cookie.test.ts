import { beforeEach, describe, expect, it } from 'vitest'
import type { InternalAxiosRequestConfig } from 'axios'
import api, { auth, clearAccessToken, refreshAccessToken, setAccessToken } from './api'

interface CapturedRequest {
  url: string | undefined
  method: string | undefined
  data: unknown
  withCredentials: unknown
}

let captured: CapturedRequest[] = []

function adapter(
  responses: Record<string, { status: number; data: unknown }>,
) {
  return (config: InternalAxiosRequestConfig) => {
    const key = `${config.method?.toUpperCase()} ${config.url}`
    captured.push({
      url: config.url,
      method: config.method,
      data: config.data,
      withCredentials: config.withCredentials,
    })
    const response = responses[key]
    if (!response) {
      return Promise.reject(
        Object.assign(new Error(`sin mock para ${key}`), {
          config,
          response: { status: 404, data: {}, headers: {}, config },
        }),
      )
    }
    if (response.status >= 400) {
      return Promise.reject(
        Object.assign(new Error(`HTTP ${response.status}`), {
          config,
          response: { status: response.status, data: response.data, headers: {}, config },
        }),
      )
    }
    return Promise.resolve({
      data: response.data,
      status: response.status,
      statusText: 'OK',
      headers: {},
      config,
    })
  }
}

describe('refresh por cookie HttpOnly', () => {
  beforeEach(() => {
    clearAccessToken()
    captured = []
  })

  it('envía las peticiones con credenciales para incluir la cookie HttpOnly', () => {
    expect(api.defaults.withCredentials).toBe(true)
  })

  it('renueva el token de acceso sin enviar el refresh token en el cuerpo', async () => {
    api.defaults.adapter = adapter({
      'POST /api/v1/auth/refresh': { status: 200, data: { access_token: 'token-nuevo' } },
    }) as never

    const token = await refreshAccessToken()

    expect(token).toBe('token-nuevo')
    expect(captured).toHaveLength(1)
    expect(captured[0].url).toBe('/api/v1/auth/refresh')
    expect(captured[0].data).toBe('{}')
    expect(captured[0].withCredentials).toBe(true)
  })

  it('propaga el error cuando la sesión ya no es renovable', async () => {
    api.defaults.adapter = adapter({
      'POST /api/v1/auth/refresh': { status: 401, data: { detail: 'sin sesión' } },
    }) as never

    await expect(refreshAccessToken()).rejects.toBeTruthy()
  })

  it('renueva de forma transparente un 401 y reintenta la petición original', async () => {
    let primeraPeticion = true
    api.defaults.adapter = ((config: InternalAxiosRequestConfig) => {
      captured.push({
        url: config.url,
        method: config.method,
        data: config.data,
        withCredentials: config.withCredentials,
      })
      if (config.url === '/api/v1/auth/refresh') {
        return Promise.resolve({
          data: { access_token: 'token-nuevo' },
          status: 200,
          statusText: 'OK',
          headers: {},
          config,
        })
      }
      if (primeraPeticion) {
        primeraPeticion = false
        return Promise.reject(
          Object.assign(new Error('HTTP 401'), {
            config,
            response: { status: 401, data: {}, headers: {}, config },
          }),
        )
      }
      return Promise.resolve({ data: { ok: true }, status: 200, statusText: 'OK', headers: {}, config })
    }) as never

    const response = await auth.getMe()

    expect(response.data).toEqual({ ok: true })
    expect(captured.map((item) => item.url)).toEqual([
      '/api/v1/auth/me',
      '/api/v1/auth/refresh',
      '/api/v1/auth/me',
    ])
  })

  it('no persiste tokens en el almacenamiento del navegador', () => {
    setAccessToken('token-en-memoria')

    expect(localStorage.getItem('token')).toBeNull()
    expect(localStorage.getItem('refresh_token')).toBeNull()
    expect(localStorage.getItem('sigem-auth')).toBeNull()
  })
})
