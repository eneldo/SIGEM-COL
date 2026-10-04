import { afterEach, beforeEach, describe, expect, it, vi, type Mock } from 'vitest'
import type { InternalAxiosRequestConfig } from 'axios'
import api, {
  auth,
  catalogos,
  configAuditoria,
  configDependencias,
  configRoles,
  configUsuarios,
  cumplimiento,
  dashboard,
  gestores,
  gestorDashboard,
  lineas,
  personalizacion,
  productos,
  programas,
  reportes,
} from './api'

interface CapturedRequest {
  url: string | undefined
  method: string | undefined
  params: unknown
  data: unknown
  responseType: string | undefined
  headers: Record<string, unknown>
}

let captured: CapturedRequest

function capture(config: InternalAxiosRequestConfig) {
  captured = {
    url: config.url,
    method: config.method,
    params: config.params,
    data: config.data,
    responseType: config.responseType,
    headers: config.headers as unknown as Record<string, unknown>,
  }
}

function okAdapter(config: InternalAxiosRequestConfig) {
  capture(config)
  return Promise.resolve({ data: {}, status: 200, statusText: 'OK', headers: {}, config })
}

function failAdapter(status: number, detail?: string) {
  return (config: InternalAxiosRequestConfig) => {
    capture(config)
    const data = detail === undefined ? {} : { detail }
    return Promise.reject(
      Object.assign(new Error(`HTTP ${status}`), {
        config,
        response: { status, statusText: '', data, headers: {}, config },
      }),
    )
  }
}

function header(name: string): string | undefined {
  const match = Object.entries(captured.headers).find(
    ([key]) => key.toLowerCase() === name.toLowerCase(),
  )
  return match ? String(match[1]) : undefined
}

let replaceMock: Mock
const originalLocationDescriptor = Object.getOwnPropertyDescriptor(window, 'location')

function stubLocation(pathname: string) {
  replaceMock = vi.fn()
  Object.defineProperty(window, 'location', {
    value: { pathname, replace: replaceMock },
    writable: true,
    configurable: true,
  })
}

beforeEach(() => {
  localStorage.clear()
  stubLocation('/')
  api.defaults.adapter = okAdapter
})

afterEach(() => {
  if (originalLocationDescriptor) {
    Object.defineProperty(window, 'location', originalLocationDescriptor)
  }
})

describe('configuración base', () => {
  it('usa la base URL definida por variable de entorno', () => {
    expect(api.defaults.baseURL).toBe(import.meta.env.VITE_API_URL ?? '')
  })

  it('declara content type JSON por defecto', async () => {
    await auth.getMe()
    expect(header('Content-Type')).toBe('application/json')
  })
})

describe('interceptor de peticiones', () => {
  it('adjunta el token de localStorage como Authorization', async () => {
    localStorage.setItem('token', 'token-123')
    await gestores.list()
    expect(header('Authorization')).toBe('Bearer token-123')
  })

  it('no envía Authorization cuando no hay token', async () => {
    await gestores.list()
    expect(header('Authorization')).toBeUndefined()
  })
})

describe('interceptor de respuestas 401', () => {
  it('no limpia sesión cuando falla el login', async () => {
    api.defaults.adapter = failAdapter(401, 'Credenciales inválidas')
    localStorage.setItem('token', 'token-123')
    localStorage.setItem('user', '{"username":"ana"}')

    await expect(auth.login({ username: 'ana', password: 'x' })).rejects.toThrow()

    expect(localStorage.getItem('token')).toBe('token-123')
    expect(localStorage.getItem('user')).toBe('{"username":"ana"}')
    expect(replaceMock).not.toHaveBeenCalled()
  })

  it('limpia el storage y redirige a login ante 401', async () => {
    api.defaults.adapter = failAdapter(401)
    localStorage.setItem('token', 'token-123')
    localStorage.setItem('user', '{"username":"ana"}')
    localStorage.setItem('sigem-auth', '{"state":{}}')

    await expect(gestores.list()).rejects.toThrow()

    expect(localStorage.getItem('token')).toBeNull()
    expect(localStorage.getItem('user')).toBeNull()
    expect(localStorage.getItem('sigem-auth')).toBeNull()
    expect(replaceMock).toHaveBeenCalledWith('/login')
  })

  it('solo redirige una vez ante 401 consecutivos', async () => {
    api.defaults.adapter = failAdapter(401)
    localStorage.setItem('token', 'token-123')

    await expect(lineas.list()).rejects.toThrow()

    expect(replaceMock).not.toHaveBeenCalled()
    expect(localStorage.getItem('token')).toBe('token-123')
  })
})

describe('interceptor de respuestas 403', () => {
  it('redirige a cambio de contraseña cuando el backend lo exige', async () => {
    api.defaults.adapter = failAdapter(403, 'PASSWORD_CHANGE_REQUIRED')

    await expect(auth.getMe()).rejects.toThrow()

    expect(replaceMock).toHaveBeenCalledWith('/change-password')
  })

  it('no redirige si ya está en la página de cambio de contraseña', async () => {
    stubLocation('/change-password')
    api.defaults.adapter = failAdapter(403, 'PASSWORD_CHANGE_REQUIRED')

    await expect(auth.getMe()).rejects.toThrow()

    expect(replaceMock).not.toHaveBeenCalled()
  })

  it('ignora otros 403 sin redirigir', async () => {
    api.defaults.adapter = failAdapter(403, 'SIN_PERMISO')

    await expect(auth.getMe()).rejects.toThrow()

    expect(replaceMock).not.toHaveBeenCalled()
  })
})

describe('endpoints', () => {
  const gestorPayload = {
    nombre_completo: 'Gestor Uno',
    email: 'gestor@mun.co',
    dependencias_adicionales: [],
  }
  const dependenciaPayload = { codigo: 'D1', nombre: 'Dependencia', nivel: 1, estado: 'ACTIVA' }
  const lineaPayload = { nombre: 'Linea', plan_desarrollo_id: 'pl-1' }
  const programaPayload = { codigo: 'P1', nombre: 'Programa', linea_estrategica_id: 'le-1' }
  const productoPayload = { codigo: 'PR1', nombre: 'Producto', programa_id: 'pg-1' }
  const usuarioPayload = {
    codigo: 'U1',
    username: 'user1',
    email: 'user1@mun.co',
    nombre_completo: 'Usuario Uno',
    password: 'Secreta123*',
  }
  const rolPayload = { codigo: 'R1', nombre: 'Rol', permisos_ids: [] }
  const passwordPayload = {
    current_password: 'anterior',
    new_password: 'Nueva1234*',
    confirm_password: 'Nueva1234*',
  }
  const avancePayload = { avance_porcentaje: 50 }
  const personalizacionPayload = {
    color_primario: '#123abc',
    color_secundario: '#456def',
    nombre_sistema: 'SIGEM Demo',
    logo_data_url: null,
  }
  const file = new File(['contenido'], 'evidencia.png', { type: 'image/png' })

  const casos: Array<[string, () => Promise<unknown>, string, string]> = [
    ['auth.login', () => auth.login({ username: 'u', password: 'p' }), 'post', '/api/v1/auth/login'],
    ['auth.logout', () => auth.logout(), 'post', '/api/v1/auth/logout'],
    ['auth.getMe', () => auth.getMe(), 'get', '/api/v1/auth/me'],
    ['auth.changePassword', () => auth.changePassword(passwordPayload), 'post', '/api/v1/auth/change-password'],
    ['gestores.list', () => gestores.list(), 'get', '/api/v1/gestores'],
    ['gestores.get', () => gestores.get('g1'), 'get', '/api/v1/gestores/g1'],
    ['gestores.create', () => gestores.create(gestorPayload), 'post', '/api/v1/gestores'],
    ['gestores.update', () => gestores.update('g1', gestorPayload), 'put', '/api/v1/gestores/g1'],
    ['gestores.activate', () => gestores.activate('g1'), 'post', '/api/v1/gestores/g1/activate'],
    ['gestores.deactivate', () => gestores.deactivate('g1'), 'post', '/api/v1/gestores/g1/deactivate'],
    ['gestores.block', () => gestores.block('g1', 'incumplimiento'), 'post', '/api/v1/gestores/g1/block'],
    ['gestores.unblock', () => gestores.unblock('g1'), 'post', '/api/v1/gestores/g1/unblock'],
    ['gestores.resetPassword', () => gestores.resetPassword('g1', 'Nueva1234*'), 'post', '/api/v1/gestores/g1/reset-password'],
    ['gestores.updatePermissions', () => gestores.updatePermissions('g1', { dependencias_adicionales: [] }), 'post', '/api/v1/gestores/g1/permisos'],
    ['gestores.accesos', () => gestores.accesos('g1'), 'get', '/api/v1/gestores/g1/accesos'],
    ['gestores.delete', () => gestores.delete('g1'), 'delete', '/api/v1/gestores/g1'],
    ['catalogos.roles', () => catalogos.roles(), 'get', '/api/v1/catalogos/roles'],
    ['catalogos.dependencias', () => catalogos.dependencias(), 'get', '/api/v1/catalogos/dependencias'],
    ['configDependencias.list', () => configDependencias.list(), 'get', '/api/v1/dependencias'],
    ['configDependencias.get', () => configDependencias.get('d1'), 'get', '/api/v1/dependencias/d1'],
    ['configDependencias.create', () => configDependencias.create(dependenciaPayload), 'post', '/api/v1/dependencias'],
    ['configDependencias.update', () => configDependencias.update('d1', { nombre: 'Otra' }), 'put', '/api/v1/dependencias/d1'],
    ['configDependencias.delete', () => configDependencias.delete('d1'), 'delete', '/api/v1/dependencias/d1'],
    ['lineas.list', () => lineas.list(), 'get', '/api/v1/lineas-estrategicas'],
    ['lineas.get', () => lineas.get('l1'), 'get', '/api/v1/lineas-estrategicas/l1'],
    ['lineas.create', () => lineas.create(lineaPayload), 'post', '/api/v1/lineas-estrategicas'],
    ['lineas.update', () => lineas.update('l1', { nombre: 'Linea 2' }), 'put', '/api/v1/lineas-estrategicas/l1'],
    ['lineas.delete', () => lineas.delete('l1'), 'delete', '/api/v1/lineas-estrategicas/l1'],
    ['programas.list', () => programas.list(), 'get', '/api/v1/programas'],
    ['programas.get', () => programas.get('pg1'), 'get', '/api/v1/programas/pg1'],
    ['programas.create', () => programas.create(programaPayload), 'post', '/api/v1/programas'],
    ['programas.update', () => programas.update('pg1', { nombre: 'Programa 2' }), 'put', '/api/v1/programas/pg1'],
    ['programas.delete', () => programas.delete('pg1'), 'delete', '/api/v1/programas/pg1'],
    ['productos.list', () => productos.list(), 'get', '/api/v1/productos'],
    ['productos.get', () => productos.get('pr1'), 'get', '/api/v1/productos/pr1'],
    ['productos.create', () => productos.create(productoPayload), 'post', '/api/v1/productos'],
    ['productos.update', () => productos.update('pr1', { nombre: 'Producto 2' }), 'put', '/api/v1/productos/pr1'],
    ['productos.delete', () => productos.delete('pr1'), 'delete', '/api/v1/productos/pr1'],
    ['dashboard.adminKpis', () => dashboard.adminKpis(), 'get', '/api/v1/dashboard/admin/kpis'],
    ['dashboard.adminResumenPlan', () => dashboard.adminResumenPlan(), 'get', '/api/v1/dashboard/admin/resumen-plan'],
    ['dashboard.adminGestores', () => dashboard.adminGestores(), 'get', '/api/v1/dashboard/admin/gestores'],
    ['dashboard.adminAlertas', () => dashboard.adminAlertas(), 'get', '/api/v1/dashboard/admin/alertas'],
    ['dashboard.adminEstadisticasDep', () => dashboard.adminEstadisticasDep(), 'get', '/api/v1/dashboard/admin/estadisticas-dependencia'],
    ['dashboard.gestorKpis', () => dashboard.gestorKpis(), 'get', '/api/v1/dashboard/gestor/kpis'],
    ['dashboard.gestorMisProductos', () => dashboard.gestorMisProductos(), 'get', '/api/v1/dashboard/gestor/mis-productos'],
    ['dashboard.gestorMisPendientes', () => dashboard.gestorMisPendientes(), 'get', '/api/v1/dashboard/gestor/mis-pendientes'],
    ['dashboard.gestorMisAlertas', () => dashboard.gestorMisAlertas(), 'get', '/api/v1/dashboard/gestor/mis-alertas'],
    ['configUsuarios.list', () => configUsuarios.list(), 'get', '/api/v1/usuarios'],
    ['configUsuarios.get', () => configUsuarios.get('u1'), 'get', '/api/v1/usuarios/u1'],
    ['configUsuarios.create', () => configUsuarios.create(usuarioPayload), 'post', '/api/v1/usuarios'],
    ['configUsuarios.update', () => configUsuarios.update('u1', { nombre_completo: 'Usuario Actualizado' }), 'put', '/api/v1/usuarios/u1'],
    ['configUsuarios.delete', () => configUsuarios.delete('u1'), 'delete', '/api/v1/usuarios/u1'],
    ['configRoles.list', () => configRoles.list(), 'get', '/api/v1/roles'],
    ['configRoles.get', () => configRoles.get('r1'), 'get', '/api/v1/roles/r1'],
    ['configRoles.create', () => configRoles.create(rolPayload), 'post', '/api/v1/roles'],
    ['configRoles.update', () => configRoles.update('r1', { nombre: 'Rol 2' }), 'put', '/api/v1/roles/r1'],
    ['configRoles.delete', () => configRoles.delete('r1'), 'delete', '/api/v1/roles/r1'],
    ['configRoles.permisos', () => configRoles.permisos(), 'get', '/api/v1/roles/permisos'],
    ['configAuditoria.list', () => configAuditoria.list(), 'get', '/api/v1/auditoria'],
    ['configAuditoria.stats', () => configAuditoria.stats(), 'get', '/api/v1/auditoria/stats'],
    ['personalizacion.get', () => personalizacion.get(), 'get', '/api/v1/personalizacion'],
    ['personalizacion.update', () => personalizacion.update(personalizacionPayload), 'put', '/api/v1/personalizacion'],
    ['reportes.resumenGeneral', () => reportes.resumenGeneral(), 'get', '/api/v1/reportes/resumen-general'],
    ['reportes.porLinea', () => reportes.porLinea(), 'get', '/api/v1/reportes/por-linea'],
    ['reportes.porPrograma', () => reportes.porPrograma(), 'get', '/api/v1/reportes/por-programa'],
    ['reportes.porDependencia', () => reportes.porDependencia(), 'get', '/api/v1/reportes/por-dependencia'],
    ['reportes.metricasProductos', () => reportes.metricasProductos(), 'get', '/api/v1/reportes/metricas-productos'],
    ['reportes.informePdf', () => reportes.informePdf(), 'get', '/api/v1/reportes/informe-pdf'],
    ['cumplimiento.general', () => cumplimiento.general(), 'get', '/api/v1/cumplimiento/general'],
    ['cumplimiento.porLinea', () => cumplimiento.porLinea(), 'get', '/api/v1/cumplimiento/por-linea'],
    ['cumplimiento.porPrograma', () => cumplimiento.porPrograma(), 'get', '/api/v1/cumplimiento/por-programa'],
    ['cumplimiento.productos', () => cumplimiento.productos(), 'get', '/api/v1/cumplimiento/productos'],
    ['cumplimiento.producto', () => cumplimiento.producto('pr1'), 'get', '/api/v1/cumplimiento/producto/pr1'],
    ['gestorDashboard.misProductos', () => gestorDashboard.misProductos(), 'get', '/api/v1/gestor/dashboard/mis-productos'],
    ['gestorDashboard.avances', () => gestorDashboard.avances('pr1'), 'get', '/api/v1/gestor/dashboard/avances/pr1'],
    ['gestorDashboard.registrarAvance', () => gestorDashboard.registrarAvance('pr1', avancePayload), 'post', '/api/v1/gestor/dashboard/avances'],
    ['gestorDashboard.actualizarAvance', () => gestorDashboard.actualizarAvance('av1', avancePayload), 'put', '/api/v1/gestor/dashboard/avances/av1'],
    ['gestorDashboard.eliminarAvance', () => gestorDashboard.eliminarAvance('av1'), 'delete', '/api/v1/gestor/dashboard/avances/av1'],
    ['gestorDashboard.resumen', () => gestorDashboard.resumen(), 'get', '/api/v1/gestor/dashboard/resumen'],
    ['gestorDashboard.revisionAvances', () => gestorDashboard.revisionAvances(), 'get', '/api/v1/gestor/dashboard/revision/avances'],
    ['gestorDashboard.revisionEstadisticas', () => gestorDashboard.revisionEstadisticas(), 'get', '/api/v1/gestor/dashboard/revision/estadisticas'],
    ['gestorDashboard.revisarAvance', () => gestorDashboard.revisarAvance('av1', { nuevo_estado: 'APROBADO' }), 'patch', '/api/v1/gestor/dashboard/revision/av1'],
    ['gestorDashboard.subirEvidencia', () => gestorDashboard.subirEvidencia('av1', file), 'post', '/api/v1/gestor/dashboard/avances/av1/evidencia'],
    ['gestorDashboard.descargarEvidencia', () => gestorDashboard.descargarEvidencia('av1'), 'get', '/api/v1/gestor/dashboard/avances/av1/evidencia'],
    ['gestorDashboard.subirEvidencias', () => gestorDashboard.subirEvidencias('av1', [file]), 'post', '/api/v1/gestor/dashboard/avances/av1/evidencias'],
    ['gestorDashboard.listarEvidencias', () => gestorDashboard.listarEvidencias('av1'), 'get', '/api/v1/gestor/dashboard/avances/av1/evidencias'],
    ['gestorDashboard.descargarEvidenciaPorId', () => gestorDashboard.descargarEvidenciaPorId('av1', 'ev1'), 'get', '/api/v1/gestor/dashboard/avances/av1/evidencias/ev1'],
    ['gestorDashboard.actualizarDescripcionEvidencia', () => gestorDashboard.actualizarDescripcionEvidencia('av1', 'ev1', 'desc'), 'put', '/api/v1/gestor/dashboard/avances/av1/evidencias/ev1'],
    ['gestorDashboard.eliminarEvidencia', () => gestorDashboard.eliminarEvidencia('av1', 'ev1'), 'delete', '/api/v1/gestor/dashboard/avances/av1/evidencias/ev1'],
  ]

  it.each(casos)('%s envía %s a la ruta esperada', async (_name, call, method, url) => {
    await call()
    expect(captured.method).toBe(method)
    expect(captured.url).toBe(url)
  })

  it('gestores.list reenvía parámetros de paginación', async () => {
    await gestores.list({ page: 3, search: 'ana' })
    expect(captured.params).toEqual({ page: 3, search: 'ana' })
  })

  it('gestores.block envía el motivo en el cuerpo', async () => {
    await gestores.block('g1', 'incumplimiento')
    expect(JSON.parse(String(captured.data))).toEqual({ motivo: 'incumplimiento' })
  })

  it('auth.login envía las credenciales en el cuerpo', async () => {
    await auth.login({ username: 'ana', password: 'secreta' })
    expect(JSON.parse(String(captured.data))).toEqual({ username: 'ana', password: 'secreta' })
  })

  it('gestores.resetPassword sin contraseña envía cuerpo vacío', async () => {
    await gestores.resetPassword('g1')
    expect(JSON.parse(String(captured.data))).toEqual({})
  })

  it('configRoles.permisos filtra por módulo', async () => {
    await configRoles.permisos('gestion')
    expect(captured.params).toEqual({ modulo: 'gestion' })
  })

  it('gestorDashboard.registrarAvance envía producto_id como query param', async () => {
    await gestorDashboard.registrarAvance('pr9', { avance_porcentaje: 80 })
    expect(captured.params).toEqual({ producto_id: 'pr9' })
    expect(JSON.parse(String(captured.data))).toEqual({ avance_porcentaje: 80 })
  })

  it('gestorDashboard.revisionAvances construye la query string con filtros', async () => {
    await gestorDashboard.revisionAvances('PENDIENTE', 'escuela', '2026-T1')
    expect(captured.url).toBe(
      '/api/v1/gestor/dashboard/revision/avances?estado=PENDIENTE&search=escuela&periodo=2026-T1',
    )
  })

  it('gestorDashboard.subirEvidencia usa multipart con el archivo', async () => {
    await gestorDashboard.subirEvidencia('av1', file)
    expect(captured.data).toBeInstanceOf(FormData)
    expect((captured.data as FormData).get('file')).toBe(file)
    expect(header('Content-Type')).toContain('multipart/form-data')
  })

  it('gestorDashboard.subirEvidencias adjunta archivos y descripción', async () => {
    await gestorDashboard.subirEvidencias('av1', [file], 'acta firmada')
    const form = captured.data as FormData
    expect(form).toBeInstanceOf(FormData)
    expect(form.getAll('files')).toEqual([file])
    expect(form.get('descripcion')).toBe('acta firmada')
    expect(header('Content-Type')).toContain('multipart/form-data')
  })

  it('las descargas solicitan responseType blob', async () => {
    await gestorDashboard.descargarEvidenciaPorId('av1', 'ev1')
    expect(captured.responseType).toBe('blob')

    await reportes.informePdf()
    expect(captured.responseType).toBe('blob')
  })
})
