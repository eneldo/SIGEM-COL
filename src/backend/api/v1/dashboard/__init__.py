"""
Dashboard API - SIGEM Colombia
==============================
Rutas API para los paneles de administración y gestor.

Autor: SIGEM Colombia
Versión: 1.0
Fecha: 2026-09-20
"""

from .admin import router as admin_router
from .gestor import router as gestor_router

__all__ = ["admin_router", "gestor_router"]
