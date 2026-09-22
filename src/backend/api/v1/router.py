from fastapi import APIRouter

from .auth import router as auth_router
from .gestores import router as gestores_router
from .health import router as health_router
from .lineas import router as lineas_router
from .programas import router as programas_router
from .productos import router as productos_router
from .dashboard import admin_router, gestor_router
from .catalogos import router as catalogos_router
from .usuarios import router as usuarios_router
from .roles import router as roles_router
from .auditoria import router as auditoria_router
from .reportes import router as reportes_router
from .cumplimiento import router as cumplimiento_router
from .gestor_dashboard import router as gestor_dashboard_router
from .dependencias import router as dependencias_router

api_router = APIRouter()

api_router.include_router(health_router, prefix="/health", tags=["Health"])
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(gestores_router)
api_router.include_router(catalogos_router)
api_router.include_router(lineas_router)
api_router.include_router(programas_router)
api_router.include_router(productos_router)
api_router.include_router(admin_router, prefix="/dashboard", tags=["Dashboard Admin"])
api_router.include_router(gestor_router, prefix="/dashboard", tags=["Dashboard Gestor"])
api_router.include_router(gestor_dashboard_router)
api_router.include_router(usuarios_router)
api_router.include_router(roles_router)
api_router.include_router(auditoria_router)
api_router.include_router(reportes_router)
api_router.include_router(cumplimiento_router)
api_router.include_router(dependencias_router)
