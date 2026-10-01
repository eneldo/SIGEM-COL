"""Schemas package - Pydantic schemas"""

from .auth import (
    ChangePasswordRequest,
    LoginRequest,
    MFASetupResponse,
    MFAVerifyRequest,
    RefreshTokenRequest,
    TokenPayload,
    TokenResponse,
    UserResponse,
)
from .catalogos import (
    DependenciaOut,
    RolOut,
)
from .gestor import (
    GestorAccesoResponse,
    GestorAccion,
    GestorCreate,
    GestorListResponse,
    GestorPasswordReset,
    GestorPermisosUpdate,
    GestorResponse,
    GestorUpdate,
)
from .linea import (
    LineaCreate,
    LineaFiltros,
    LineaListResponse,
    LineaResponse,
    LineaUpdate,
)
from .producto import (
    ProductoCreate,
    ProductoFiltros,
    ProductoListResponse,
    ProductoResponse,
    ProductoUpdate,
)
from .programa import (
    ProgramaCreate,
    ProgramaFiltros,
    ProgramaListResponse,
    ProgramaResponse,
    ProgramaUpdate,
)

__all__ = [
    "LoginRequest",
    "TokenResponse",
    "RefreshTokenRequest",
    "ChangePasswordRequest",
    "MFASetupResponse",
    "MFAVerifyRequest",
    "UserResponse",
    "TokenPayload",
    "GestorCreate",
    "GestorPermisosUpdate",
    "GestorResponse",
    "GestorListResponse",
    "GestorUpdate",
    "GestorAccion",
    "GestorPasswordReset",
    "GestorAccesoResponse",
    "RolOut",
    "DependenciaOut",
    "LineaCreate",
    "LineaUpdate",
    "LineaResponse",
    "LineaListResponse",
    "LineaFiltros",
    "ProgramaCreate",
    "ProgramaUpdate",
    "ProgramaResponse",
    "ProgramaListResponse",
    "ProgramaFiltros",
    "ProductoCreate",
    "ProductoUpdate",
    "ProductoResponse",
    "ProductoListResponse",
    "ProductoFiltros",
]
