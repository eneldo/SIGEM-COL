import axios from 'axios'
import type {
  PaginatedResponse,
  LoginRequest,
  LoginResponse,
  ChangePasswordRequest,
  User,
  Gestor,
  GestorAcceso,
  GestorCreatePayload,
  CredencialTemporal,
  Rol,
  Dependencia,
  LineaEstrategica,
  LineaCreatePayload,
  Programa,
  ProgramaCreatePayload,
  Producto,
  ProductoCreatePayload,
  DashboardKPIs,
  PlanResumen,
  Alert,
  AdminGestorResumen,
  AdminDependenciaStat,
  GestorKpis,
  GestorProductoItem,
  GestorPendienteItem,
  GestorAlert,
  ConfigUsuario,
  ConfigUsuarioCreatePayload,
  ConfigUsuarioUpdatePayload,
  ConfigRol,
  ConfigRolCreatePayload,
  ConfigRolUpdatePayload,
  ConfigPermiso,
  AuditoriaEvento,
  AuditoriaStats,
  ResumenGeneral,
  ResumenPorLinea,
  ResumenPorPrograma,
  ResumenPorDependencia,
  MetricasProductos,
  CumplimientoGeneral,
  CumplimientoPorLinea,
  CumplimientoPorPrograma,
  ItemCumplimientoProducto,
  DependenciaCreatePayload,
  DependenciaUpdatePayload,
  Evidencia,
  Personalizacion,
} from './types'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '',
  headers: {
    'Content-Type': 'application/json',
  },
})

let redirectingToLogin = false

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const isLoginRequest = error.config?.url === '/api/v1/auth/login'

    if (error.response?.status === 401 && !isLoginRequest && !redirectingToLogin) {
      redirectingToLogin = true
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      localStorage.removeItem('sigem-auth')
      window.location.replace('/login')
    }

    if (
      error.response?.status === 403 &&
      error.response?.data?.detail === 'PASSWORD_CHANGE_REQUIRED' &&
      window.location.pathname !== '/change-password'
    ) {
      window.location.replace('/change-password')
    }
    return Promise.reject(error)
  },
)

export const auth = {
  login: (data: LoginRequest) =>
    api.post<LoginResponse>('/api/v1/auth/login', data),

  logout: () =>
    api.post('/api/v1/auth/logout'),

  getMe: () =>
    api.get<User>('/api/v1/auth/me'),

  changePassword: (data: ChangePasswordRequest) =>
    api.post<void>('/api/v1/auth/change-password', data),
}

export const gestores = {
  list: (params?: Record<string, unknown>) =>
    api.get<PaginatedResponse<Gestor>>('/api/v1/gestores', { params }),

  get: (id: string) =>
    api.get<Gestor>(`/api/v1/gestores/${id}`),

  create: (data: GestorCreatePayload) =>
    api.post<CredencialTemporal>('/api/v1/gestores', data),

  update: (id: string, data: Partial<GestorCreatePayload>) =>
    api.put<Gestor>(`/api/v1/gestores/${id}`, data),

  activate: (id: string) => api.post<Gestor>(`/api/v1/gestores/${id}/activate`),

  deactivate: (id: string) => api.post<Gestor>(`/api/v1/gestores/${id}/deactivate`),

  block: (id: string, motivo: string) =>
    api.post<Gestor>(`/api/v1/gestores/${id}/block`, { motivo }),

  unblock: (id: string) => api.post<Gestor>(`/api/v1/gestores/${id}/unblock`),

  resetPassword: (id: string, nuevaPassword?: string) =>
    api.post<CredencialTemporal>(`/api/v1/gestores/${id}/reset-password`, nuevaPassword ? { nueva_password: nuevaPassword } : {}),

  updatePermissions: (id: string, data: { rol_id?: string; dependencia_principal_id?: string; dependencias_adicionales: string[] }) =>
    api.post<Gestor>(`/api/v1/gestores/${id}/permisos`, data),

  accesos: (id: string) => api.get<GestorAcceso[]>(`/api/v1/gestores/${id}/accesos`),

  delete: (id: string) => api.delete<void>(`/api/v1/gestores/${id}`),
}

export const catalogos = {
  roles: () => api.get<Rol[]>('/api/v1/catalogos/roles'),
  dependencias: () => api.get<Dependencia[]>('/api/v1/catalogos/dependencias'),
}

export const configDependencias = {
  list: (params?: Record<string, unknown>) =>
    api.get<PaginatedResponse<Dependencia>>('/api/v1/dependencias', { params }),
  get: (id: string) =>
    api.get<Dependencia>(`/api/v1/dependencias/${id}`),
  create: (data: DependenciaCreatePayload) =>
    api.post<Dependencia>('/api/v1/dependencias', data),
  update: (id: string, data: DependenciaUpdatePayload) =>
    api.put<Dependencia>(`/api/v1/dependencias/${id}`, data),
  delete: (id: string) =>
    api.delete<void>(`/api/v1/dependencias/${id}`),
}

export const lineas = {
  list: (params?: Record<string, unknown>) =>
    api.get<PaginatedResponse<LineaEstrategica>>('/api/v1/lineas-estrategicas', { params }),

  get: (id: string) =>
    api.get<LineaEstrategica>(`/api/v1/lineas-estrategicas/${id}`),

  create: (data: LineaCreatePayload) =>
    api.post<LineaEstrategica>('/api/v1/lineas-estrategicas', data),

  update: (id: string, data: Partial<Omit<LineaCreatePayload, 'plan_desarrollo_id'>>) =>
    api.put<LineaEstrategica>(`/api/v1/lineas-estrategicas/${id}`, data),

  delete: (id: string) =>
    api.delete<void>(`/api/v1/lineas-estrategicas/${id}`),
}

export const programas = {
  list: (params?: Record<string, unknown>) =>
    api.get<PaginatedResponse<Programa>>('/api/v1/programas', { params }),

  get: (id: string) =>
    api.get<Programa>(`/api/v1/programas/${id}`),

  create: (data: ProgramaCreatePayload) =>
    api.post<Programa>('/api/v1/programas', data),

  update: (id: string, data: Partial<Omit<ProgramaCreatePayload, 'linea_estrategica_id'>>) =>
    api.put<Programa>(`/api/v1/programas/${id}`, data),

  delete: (id: string) =>
    api.delete<void>(`/api/v1/programas/${id}`),
}

export const productos = {
  list: (params?: Record<string, unknown>) =>
    api.get<PaginatedResponse<Producto>>('/api/v1/productos', { params }),

  get: (id: string) =>
    api.get<Producto>(`/api/v1/productos/${id}`),

  create: (data: ProductoCreatePayload) =>
    api.post<Producto>('/api/v1/productos', data),

  update: (id: string, data: Partial<ProductoCreatePayload>) =>
    api.put<Producto>(`/api/v1/productos/${id}`, data),

  delete: (id: string) =>
    api.delete<void>(`/api/v1/productos/${id}`),
}

export const dashboard = {
  adminKpis: () =>
    api.get<DashboardKPIs>('/api/v1/dashboard/admin/kpis'),

  adminResumenPlan: () =>
    api.get<PlanResumen>('/api/v1/dashboard/admin/resumen-plan'),

  adminGestores: () =>
    api.get<{ gestores: AdminGestorResumen[]; total: number }>('/api/v1/dashboard/admin/gestores'),

  adminAlertas: () =>
    api.get<{ alertas: Alert[]; total: number }>('/api/v1/dashboard/admin/alertas'),

  adminEstadisticasDep: () =>
    api.get<{ dependencias: AdminDependenciaStat[]; total: number }>('/api/v1/dashboard/admin/estadisticas-dependencia'),

  gestorKpis: () =>
    api.get<GestorKpis>('/api/v1/dashboard/gestor/kpis'),

  gestorMisProductos: () =>
    api.get<{ productos: GestorProductoItem[]; total: number }>('/api/v1/dashboard/gestor/mis-productos'),

  gestorMisPendientes: () =>
    api.get<{ pendientes: GestorPendienteItem[]; total: number }>('/api/v1/dashboard/gestor/mis-pendientes'),

  gestorMisAlertas: () =>
    api.get<{ alertas: GestorAlert[]; total: number }>('/api/v1/dashboard/gestor/mis-alertas'),
}

// --- Configuración: Usuarios ---

export const configUsuarios = {
  list: (params?: Record<string, unknown>) =>
    api.get<PaginatedResponse<ConfigUsuario>>('/api/v1/usuarios', { params }),

  get: (id: string) =>
    api.get<ConfigUsuario>(`/api/v1/usuarios/${id}`),

  create: (data: ConfigUsuarioCreatePayload) =>
    api.post<ConfigUsuario>('/api/v1/usuarios', data),

  update: (id: string, data: ConfigUsuarioUpdatePayload) =>
    api.put<ConfigUsuario>(`/api/v1/usuarios/${id}`, data),

  delete: (id: string) =>
    api.delete<void>(`/api/v1/usuarios/${id}`),
}

// --- Configuración: Roles ---

export const configRoles = {
  list: (params?: Record<string, unknown>) =>
    api.get<PaginatedResponse<ConfigRol>>('/api/v1/roles', { params }),

  get: (id: string) =>
    api.get<ConfigRol>(`/api/v1/roles/${id}`),

  create: (data: ConfigRolCreatePayload) =>
    api.post<ConfigRol>('/api/v1/roles', data),

  update: (id: string, data: ConfigRolUpdatePayload) =>
    api.put<ConfigRol>(`/api/v1/roles/${id}`, data),

  delete: (id: string) =>
    api.delete<void>(`/api/v1/roles/${id}`),

  permisos: (modulo?: string) =>
    api.get<{ items: ConfigPermiso[]; total: number }>('/api/v1/roles/permisos', { params: modulo ? { modulo } : {} }),
}

// --- Configuración: Auditoría ---

export const configAuditoria = {
  list: (params?: Record<string, unknown>) =>
    api.get<PaginatedResponse<AuditoriaEvento>>('/api/v1/auditoria', { params }),

  stats: () =>
    api.get<AuditoriaStats>('/api/v1/auditoria/stats'),
}

// --- Reportes y Rendición de Cuentas ---

export const reportes = {
  resumenGeneral: () =>
    api.get<ResumenGeneral>('/api/v1/reportes/resumen-general'),

  porLinea: () =>
    api.get<ResumenPorLinea[]>('/api/v1/reportes/por-linea'),

  porPrograma: () =>
    api.get<ResumenPorPrograma[]>('/api/v1/reportes/por-programa'),

  porDependencia: () =>
    api.get<ResumenPorDependencia[]>('/api/v1/reportes/por-dependencia'),

  metricasProductos: () =>
    api.get<MetricasProductos>('/api/v1/reportes/metricas-productos'),

  informePdf: () =>
    api.get('/api/v1/reportes/informe-pdf', { responseType: 'blob' }),
}

// --- Cumplimiento de Metas ---

export const cumplimiento = {
  general: () =>
    api.get<CumplimientoGeneral>('/api/v1/cumplimiento/general'),

  porLinea: () =>
    api.get<CumplimientoPorLinea[]>('/api/v1/cumplimiento/por-linea'),

  porPrograma: () =>
    api.get<CumplimientoPorPrograma[]>('/api/v1/cumplimiento/por-programa'),

  productos: () =>
    api.get<ItemCumplimientoProducto[]>('/api/v1/cumplimiento/productos'),

  producto: (id: string) =>
    api.get<ItemCumplimientoProducto>(`/api/v1/cumplimiento/producto/${id}`),
}

// --- Gestor Dashboard: Mis Productos y Avances ---

export const gestorDashboard = {
  misProductos: () =>
    api.get<{ id: string; codigo: string; nombre: string; indicador: string | null; codigo_indicador: string | null; meta_redactada: string | null; linea_base: number | null; meta_cuatrienio: number | null; unidad_medida: string | null; estado: string }[]>('/api/v1/gestor/dashboard/mis-productos'),

  avances: (productoId: string) =>
    api.get<{ id: string; producto_id: string; avance_porcentaje: number; avance_valor: number | null; observaciones: string | null; evidencia_url: string | null; indicador: string | null; periodo: string | null; fecha_registro: string | null; estado_revision: string; evidencia_nombre: string | null; evidencia_tipo: string | null; observaciones_revision: string | null; estado: string; created_at: string | null }[]>(`/api/v1/gestor/dashboard/avances/${productoId}`),

  registrarAvance: (productoId: string, data: { avance_porcentaje?: number; avance_valor?: number; observaciones?: string; indicador?: string; periodo?: string; estado_revision?: string; evidencia_nombre?: string; evidencia_tipo?: string }) =>
    api.post('/api/v1/gestor/dashboard/avances', data, { params: { producto_id: productoId } }),

  actualizarAvance: (avanceId: string, data: { avance_porcentaje?: number; avance_valor?: number | null; observaciones?: string | null; indicador?: string | null; periodo?: string | null; estado_revision?: string | null }) =>
    api.put<{ id: string; producto_id: string; avance_porcentaje: number; avance_valor: number | null; observaciones: string | null; periodo: string | null; estado_revision: string; created_at: string | null }>(
      `/api/v1/gestor/dashboard/avances/${avanceId}`,
      data,
    ),

  eliminarAvance: (avanceId: string) =>
    api.delete<{ id: string; eliminado: boolean }>(
      `/api/v1/gestor/dashboard/avances/${avanceId}`,
    ),

  resumen: () =>
    api.get<{ total_productos: number; productos_con_avance: number; avance_promedio: number; productos_completados: number }>('/api/v1/gestor/dashboard/resumen'),

  revisionAvances: (estado?: string, search?: string, periodo?: string) => {
    const params = new URLSearchParams()
    if (estado) params.set('estado', estado)
    if (search) params.set('search', search)
    if (periodo) params.set('periodo', periodo)
    const qs = params.toString()
    return api.get<{ id: string; producto_id: string; producto_codigo: string; producto_nombre: string; codigo_indicador: string | null; indicador: string | null; gestor_id: string; gestor_codigo: string; gestor_nombre: string; avance_porcentaje: number; avance_valor: number | null; periodo: string | null; fecha_registro: string | null; estado_revision: string; evidencia_nombre: string | null; evidencia_tipo: string | null; evidencia_url: string | null; observaciones: string | null; observaciones_revision: string | null; created_at: string | null }[]>(`/api/v1/gestor/dashboard/revision/avances${qs ? '?' + qs : ''}`)
  },

  revisionEstadisticas: () =>
    api.get<{ pendientes: number; aprobados_semana: number; devueltos: number }>('/api/v1/gestor/dashboard/revision/estadisticas'),

  revisarAvance: (avanceId: string, data: { nuevo_estado: string; observacion?: string }) =>
    api.patch(`/api/v1/gestor/dashboard/revision/${avanceId}`, data),

  subirEvidencia: (avanceId: string, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post<{ id: string; evidencia_url: string | null; evidencia_nombre: string | null; evidencia_tipo: string | null }>(
      `/api/v1/gestor/dashboard/avances/${avanceId}/evidencia`,
      form,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    )
  },

  descargarEvidencia: (avanceId: string) =>
    api.get<Blob>(`/api/v1/gestor/dashboard/avances/${avanceId}/evidencia`, {
      responseType: 'blob',
    }),

  // --- Evidencias múltiples ---
  subirEvidencias: (avanceId: string, files: File[], descripcion?: string) => {
    const form = new FormData()
    files.forEach((f) => form.append('files', f))
    if (descripcion) form.append('descripcion', descripcion)
    return api.post<Evidencia[]>(
      `/api/v1/gestor/dashboard/avances/${avanceId}/evidencias`,
      form,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    )
  },

  listarEvidencias: (avanceId: string) =>
    api.get<Evidencia[]>(`/api/v1/gestor/dashboard/avances/${avanceId}/evidencias`),

  descargarEvidenciaPorId: (avanceId: string, evidenciaId: string) =>
    api.get<Blob>(`/api/v1/gestor/dashboard/avances/${avanceId}/evidencias/${evidenciaId}`, {
      responseType: 'blob',
    }),

  actualizarDescripcionEvidencia: (avanceId: string, evidenciaId: string, descripcion: string | null) =>
    api.put<{ id: string; descripcion: string | null }>(
      `/api/v1/gestor/dashboard/avances/${avanceId}/evidencias/${evidenciaId}`,
      { descripcion },
    ),

  eliminarEvidencia: (avanceId: string, evidenciaId: string) =>
    api.delete<{ id: string; eliminada: boolean }>(
      `/api/v1/gestor/dashboard/avances/${avanceId}/evidencias/${evidenciaId}`,
    ),
}

export const personalizacion = {
  get: () =>
    api.get<Personalizacion>('/api/v1/personalizacion'),

  update: (data: Personalizacion) =>
    api.put<Personalizacion>('/api/v1/personalizacion', data),
}

export default api
