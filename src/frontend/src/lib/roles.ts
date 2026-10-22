/**
 * Catálogo centralizado de roles del sistema (F4.1/F8.4/F9.3).
 * Los valores provienen de la capa de autenticación/autorización del backend
 * y no deben duplicarse en los componentes: importar desde aquí.
 */

/** Roles administrativos: acceso completo al panel /admin. */
export const ADMIN_ROLES: readonly string[] = [
  'SUPERADMIN_PLATAFORMA',
  'ADMINISTRADOR_MUNICIPAL',
]

/** Rol de coordinación: gestor líder que revisa avances de su equipo. */
export const GESTOR_LIDER_ROLES: readonly string[] = ['GESTOR_LIDER']

/** Roles operativos: usuarios que registran y siguen sus productos. */
export const GESTOR_ROLES: readonly string[] = ['GESTOR', 'GESTOR_LIDER']

/** Roles autorizados para navegar por /gestor (incluye administración). */
export const GESTOR_ROUTE_ROLES: readonly string[] = [...ADMIN_ROLES, ...GESTOR_ROLES]

/** Determina si alguno de los roles recibidos es administrativo. */
export function isAdminRole(roles: readonly string[] | undefined): boolean {
  return Boolean(roles?.some((role) => (ADMIN_ROLES as readonly string[]).includes(role)))
}

/** Determina si el usuario tiene el rol de gestor líder (coordinación). */
export function isGestorLiderRole(roles: readonly string[] | undefined): boolean {
  return Boolean(roles?.includes('GESTOR_LIDER'))
}

/** Ruta inicial según los roles del usuario autenticado. */
export function homeRouteForRoles(roles: readonly string[] | undefined): string {
  return isAdminRole(roles) ? '/admin/dashboard' : '/gestor/dashboard'
}
