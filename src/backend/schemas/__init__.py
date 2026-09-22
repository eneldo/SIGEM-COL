"""Schemas package - Pydantic schemas"""
from .auth import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    ChangePasswordRequest,
    MFASetupResponse,
    MFAVerifyRequest,
    UserResponse,
    TokenPayload,
)
from .gestor import (
    GestorCreate,
    GestorPermisosUpdate,
    GestorResponse,
    GestorListResponse,
    GestorUpdate,
    GestorAccion,
    GestorPasswordReset,
    GestorAccesoResponse,
)
from .catalogos import (
    RolOut,
    DependenciaOut,
)
from .linea import (
    LineaCreate,
    LineaUpdate,
    LineaResponse,
    LineaListResponse,
    LineaFiltros,
)
from .programa import (
    ProgramaCreate,
    ProgramaUpdate,
    ProgramaResponse,
    ProgramaListResponse,
    ProgramaFiltros,
)
from .producto import (
    ProductoCreate,
    ProductoUpdate,
    ProductoResponse,
    ProductoListResponse,
    ProductoFiltros,
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
