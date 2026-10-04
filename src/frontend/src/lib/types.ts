export interface User {
  id: string
  username: string
  email: string
  nombre_completo: string
  municipio_id: string | null
  roles: string[]
  must_change_password?: boolean
}

export interface Municipio {
  id: string
  codigo: string
  nombre: string
  departamento: string
  activo: boolean
}

export interface Gestor {
  id: string
  codigo: string
  username: string
  email: string
  telefono?: string
  nombre_completo: string
  cargo?: string
  rol?: string
  rol_id?: string
  roles: string[]
  dependencia_principal_id?: string
  dependencia_principal?: string
  dependencias: GestorDependencia[]
  estado: 'ACTIVO' | 'INACTIVO' | 'BLOQUEADO'
  mfa_activo: boolean
  must_change_password: boolean
  ultimo_acceso?: string
  ip_ultimo_acceso?: string
  intentos_fallidos: number
  ultimo_cambio_password?: string
  created_at: string
  updated_at?: string
}

export interface GestorDependencia {
  id: string
  nombre: string
  es_principal: boolean
}

export interface Rol {
  id: string
  codigo: string
  nombre: string
  nivel: number
}

export interface Dependencia {
  id: string
  municipio_id: string
  codigo: string
  nombre: string
  descripcion?: string
  dependencia_padre_id?: string
  nivel: number
  estado: string
  created_at?: string
  updated_at?: string
}

export interface DependenciaCreatePayload {
  codigo: string
  nombre: string
  descripcion?: string
  dependencia_padre_id?: string
  nivel: number
  estado: string
}

export interface DependenciaUpdatePayload {
  codigo?: string
  nombre?: string
  descripcion?: string
  dependencia_padre_id?: string
  nivel?: number
  estado?: string
}

export interface GestorAcceso {
  id: string
  exitoso: boolean
  ip_address?: string
  user_agent?: string
  razon_fallo?: string
  fecha_intento: string
}

export interface GestorCreatePayload {
  nombre_completo: string
  email: string
  telefono?: string
  cargo?: string
  rol_id?: string
  dependencia_principal_id?: string
  dependencias_adicionales: string[]
  username?: string
  password?: string
}

export interface CredencialTemporal {
  nueva_password_temporal: string
  id?: string
  codigo?: string
  username?: string
}

export interface LineaEstrategica {
  id: string
  codigo: string
  numero?: string
  nombre: string
  descripcion?: string
  orden: number
  estado: 'ACTIVA' | 'INACTIVA'
  municipio_id: string
  plan_desarrollo_id: string
  plan_desarrollo_nombre?: string
  created_at: string
  updated_at: string
}

export interface LineaCreatePayload {
  numero?: string
  nombre: string
  descripcion?: string
  plan_desarrollo_id: string
}

export interface Programa {
  id: string
  codigo: string
  nombre: string
  sector?: string
  descripcion?: string
  estado: 'ACTIVO' | 'INACTIVO'
  municipio_id: string
  linea_estrategica_id: string
  linea_estrategica_nombre?: string
  created_at: string
  updated_at: string
}

export interface ProgramaCreatePayload {
  codigo: string
  nombre: string
  sector?: string
  descripcion?: string
  linea_estrategica_id: string
}

export interface Producto {
  id: string
  codigo: string
  nombre: string
  codigo_indicador?: string
  indicador?: string
  meta_redactada?: string
  linea_base?: number
  meta_cuatrienio?: number
  descripcion?: string
  unidad_medida?: string
  estado: 'ACTIVO' | 'INACTIVO'
  municipio_id: string
  programa_id: string
  programa_nombre?: string
  dependencia_responsable_id?: string
  dependencia_nombre?: string
  gestor_lider_id?: string
  gestor_nombre?: string
  asignado_at?: string | null
  created_at: string
  updated_at: string
}

export interface ProductoCreatePayload {
  codigo: string
  nombre: string
  codigo_indicador?: string
  indicador?: string
  meta_redactada?: string
  linea_base?: number
  meta_cuatrienio?: number
  descripcion?: string
  unidad_medida?: string
  programa_id: string
  dependencia_responsable_id?: string
  gestor_lider_id?: string | null
}

export interface ApiResponse<T> {
  success: boolean
  data: T
  message?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  must_change_password: boolean
  user: User
  mfa_required?: boolean
  mfa_token?: string
  expires_in?: number
}

export interface MfaStatusResponse {
  mfa_activo: boolean
  pending: boolean
  secret?: string | null
  qr_code_url?: string | null
}

export interface MfaSetupResponse {
  secret: string
  qr_code_url: string
}

export interface MfaLoginRequest {
  mfa_token: string
  code: string
}

export interface MfaDisableRequest {
  password: string
  code: string
}

export interface ChangePasswordRequest {
  current_password: string
  new_password: string
  confirm_password: string
}

export interface DashboardKPIs {
  total_gestores: number
  gestores_activos: number
  gestores_inactivos: number
  gestores_bloqueados: number
  total_lineas_estrategicas: number
  total_programas: number
  total_productos: number
  total_dependencias: number
}

export interface PlanResumen {
  plan: {
    id: string
    codigo: string
    nombre: string
    descripcion?: string
    fecha_inicio: string
    fecha_fin: string
    vigencias: number
    estado: string
  }
  total_lineas_estrategicas: number
  total_programas: number
  total_productos: number
  lineas_desglose: {
    id: string
    codigo: string
    nombre: string
    orden: number
    total_programas: number
    total_productos: number
  }[]
}

export interface Alert {
  tipo: 'intentos_fallidos' | 'bloqueado' | 'sin_acceso' | string
  severidad: 'ALTA' | 'MEDIA' | 'BAJA' | 'CRITICA'
  gestor_id?: string
  gestor_codigo?: string
  gestor_nombre?: string
  mensaje: string
  valor?: number
  motivo_bloqueo?: string
  fecha_bloqueo?: string
  ultimo_acceso?: string
  dias_inactividad?: number
  detectado_en: string
}

export interface AdminGestorResumen {
  id: string
  usuario_id: string
  codigo: string
  nombre_completo: string
  cargo?: string
  estado: 'ACTIVO' | 'INACTIVO' | 'BLOQUEADO'
  ultimo_acceso?: string
  intentos_fallidos: number
  mfa_activo: boolean
  total_productos_asignados: number
  created_at: string
}

export interface AdminDependenciaStat {
  dependencia_id: string
  dependencia_codigo: string
  dependencia_nombre: string
  nivel?: number
  total_productos: number
  total_gestores: number
}

export interface GestorKpis {
  total_productos_asignados: number
  total_dependencias_asignadas: number
  total_lineas_estrategicas: number
}

export interface GestorProductoItem {
  id: string
  codigo: string
  nombre: string
  descripcion?: string
  unidad_medida?: string
  estado: string
  programa: { id: string; codigo: string; nombre: string }
  dependencia_responsable: { id: string; codigo: string; nombre: string } | null
  updated_at: string | null
}

export interface GestorPendienteItem extends GestorProductoItem {
  dias_sin_actualizacion: number | null
}

export interface GestorAlert {
  tipo: string
  severidad: 'ALTA' | 'MEDIA' | 'BAJA' | 'CRITICA'
  mensaje: string
  valor?: number
  motivo_bloqueo?: string
  fecha_bloqueo?: string
  detectado_en: string
}

// --- Configuración: Usuarios ---

export interface ConfigUsuario {
  id: string
  municipio_id: string
  codigo: string
  username: string
  email: string
  nombre_completo: string
  telefono?: string
  cargo?: string
  activo: number
  roles: ConfigUsuarioRol[]
  must_change_password: boolean
  mfa_activo: boolean
  ultimo_acceso?: string
  intentos_fallidos: number
  created_at: string
  updated_at: string
}

export interface ConfigUsuarioRol {
  id?: string
  codigo: string
  nombre: string
}

export interface ConfigUsuarioCreatePayload {
  codigo: string
  username: string
  email: string
  nombre_completo: string
  telefono?: string
  cargo?: string
  password: string
  rol_id?: string
  dependencia_id?: string
}

export interface ConfigUsuarioUpdatePayload {
  email?: string
  nombre_completo?: string
  telefono?: string
  cargo?: string
  activo?: number
  must_change_password?: boolean
  rol_id?: string
}

// --- Configuración: Roles ---

export interface ConfigRol {
  id: string
  codigo: string
  nombre: string
  descripcion?: string
  nivel: number
  estado: string
  permisos: ConfigPermiso[]
  created_at: string
  updated_at: string
}

export interface ConfigPermiso {
  id: string
  codigo: string
  nombre: string
  modulo: string
  accion: string
}

export interface ConfigRolCreatePayload {
  codigo: string
  nombre: string
  descripcion?: string
  nivel?: number
  permisos_ids: string[]
}

export interface ConfigRolUpdatePayload {
  nombre?: string
  descripcion?: string
  nivel?: number
  estado?: string
  permisos_ids?: string[]
}

// --- Configuración: Auditoría ---

export interface AuditoriaEvento {
  id: string
  evento_tipo: string
  recurso_tipo?: string
  recurso_id?: string
  resultado: string
  ip_address?: string
  actor_nombre?: string
  actor_id?: string
  metadata_json?: string
  fecha_evento: string
}

export interface AuditoriaStats {
  total_eventos: number
  exitosos: number
  fallidos: number
  hoy: number
  por_tipo: Record<string, number>
}

// --- Reportes y Rendición de Cuentas ---

export interface ResumenGeneral {
  total_lineas: number
  total_programas: number
  total_productos: number
  productos_activos: number
  productos_inactivos: number
  total_gestores: number
}

export interface ResumenPorLinea {
  id: string
  codigo: string
  nombre: string
  total_programas: number
  total_productos: number
  estado: string
}

export interface ResumenPorPrograma {
  id: string
  codigo: string
  nombre: string
  sector: string | null
  linea_nombre: string
  total_productos: number
  productos_activos: number
  estado: string
}

export interface ResumenPorDependencia {
  id: string
  codigo: string
  nombre: string
  total_productos: number
  total_gestores: number
}

export interface MetricasProductos {
  total_productos: number
  con_indicador: number
  sin_indicador: number
  con_meta_cuatrienio: number
  con_linea_base: number
  con_gestor_asignado: number
  sin_gestor_asignado: number
  porcentaje_cumplimiento_indicador: number
  porcentaje_cumplimiento_meta: number
  promedio_avance: number
}

// --- Cumplimiento de Metas ---

export interface CumplimientoGeneral {
  total_productos: number
  con_meta_definida: number
  sin_meta_definida: number
  completados: number
  en_progreso: number
  sin_avance: number
  porcentaje_cumplimiento_general: number
}

export interface CumplimientoPorLinea {
  id: string
  codigo: string
  nombre: string
  total_productos: number
  con_meta_definida: number
  completados: number
  en_progreso: number
  sin_avance: number
  porcentaje_cumplimiento: number
}

export interface CumplimientoPorPrograma {
  id: string
  codigo: string
  nombre: string
  linea_nombre: string
  total_productos: number
  con_meta_definida: number
  completados: number
  en_progreso: number
  sin_avance: number
  porcentaje_cumplimiento: number
}

export interface ItemCumplimientoProducto {
  id: string
  codigo: string
  nombre: string
  indicador: string | null
  linea_base: number | null
  meta_cuatrienio: number | null
  programa_nombre: string
  linea_nombre: string
  porcentaje_avance: number
  estado_cumplimiento: string
}

export interface Evidencia {
  id: string
  avance_id: string
  nombre: string
  tipo: string
  url: string
  descripcion: string | null
  tamano_original: number | null
  tamano_almacenado: number | null
  optimizada: boolean
  created_at: string | null
}

export interface Personalizacion {
  color_primario: string
  color_secundario: string
  nombre_sistema: string
  logo_data_url: string | null
}