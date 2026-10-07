"""Regressions for client-controlled and previously persisted evidence paths."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.backend.api.v1 import gestor_dashboard as routes
from src.backend.api.v1.auth import get_current_user_from_token
from src.backend.core.database import get_db
from src.backend.models.avance_producto import AvanceProducto
from src.backend.models.evidencia import Evidencia
from src.backend.services import avance_service


@pytest.fixture
def evidence_api(tmp_path, monkeypatch):
    storage = tmp_path / "storage"
    storage.mkdir()
    monkeypatch.setattr(avance_service.settings, "STORAGE_PATH", str(storage))
    usuario_id, municipio_id, avance_id = uuid4(), uuid4(), uuid4()
    avance = AvanceProducto(
        id=avance_id,
        municipio_id=municipio_id,
        registrado_por=usuario_id,
        gestor_lider_id=uuid4(),
        evidencia_nombre="evidencia.pdf",
        evidencia_tipo="application/pdf",
    )
    evidencia = Evidencia(
        id=uuid4(),
        avance_id=avance_id,
        municipio_id=municipio_id,
        nombre="evidencia.pdf",
        tipo="application/pdf",
    )
    db = SimpleNamespace(scalar=AsyncMock(), add=Mock(), commit=AsyncMock())
    app = FastAPI()
    app.include_router(routes.router, prefix="/api/v1")
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user_from_token] = lambda: {
        "user": SimpleNamespace(id=usuario_id),
        "municipio_id": str(municipio_id),
        "roles": ["GESTOR"],
    }
    with TestClient(app) as client:
        yield SimpleNamespace(
            client=client,
            db=db,
            storage=storage,
            avance=avance,
            evidencia=evidencia,
        )


def download(api, endpoint, relative_path):
    api.avance.evidencia_url = relative_path
    api.evidencia.url = relative_path
    prefix = f"/api/v1/gestor/dashboard/avances/{api.avance.id}"
    if endpoint == "single":
        api.db.scalar.side_effect = [api.avance]
        return api.client.get(f"{prefix}/evidencia")
    api.db.scalar.side_effect = [api.avance, api.evidencia]
    return api.client.get(f"{prefix}/evidencias/{api.evidencia.id}")


@pytest.mark.parametrize("endpoint", ["single", "multiple"])
@pytest.mark.parametrize(
    "attack",
    [
        "absolute",
        "traversal",
        "symlink",
        "symlink_directory",
        "windows_absolute",
        "symlink_loop",
    ],
)
def test_download_rejects_unsafe_persisted_paths(
    evidence_api, endpoint, attack, tmp_path
):
    outside = tmp_path / "private.pdf"
    outside.write_bytes(b"private data outside storage")
    if attack == "absolute":
        relative_path = str(outside)
    elif attack == "traversal":
        relative_path = "../private.pdf"
    elif attack == "symlink":
        (evidence_api.storage / "linked.pdf").symlink_to(outside)
        relative_path = "linked.pdf"
    elif attack == "symlink_directory":
        (evidence_api.storage / "linked").symlink_to(tmp_path, target_is_directory=True)
        relative_path = "linked/private.pdf"
    elif attack == "symlink_loop":
        link = evidence_api.storage / "loop.pdf"
        link.symlink_to(link)
        relative_path = "loop.pdf"
    else:
        relative_path = r"C:\private.pdf"

    response = download(evidence_api, endpoint, relative_path)
    assert response.status_code == 404, response.text
    # Python versions differ in whether non-strict resolve raises on a symlink loop.
    if attack != "symlink_loop":
        assert response.json()["detail"] == "Ruta de evidencia inválida."
    assert b"private data outside storage" not in response.content
    assert outside.read_bytes() == b"private data outside storage"


@pytest.mark.parametrize("endpoint", ["single", "multiple"])
def test_download_preserves_valid_uploaded_files(evidence_api, endpoint):
    relative_path = (
        f"{evidence_api.avance.municipio_id}/{evidence_api.avance.id}/uploaded.pdf"
    )
    uploaded = evidence_api.storage / relative_path
    uploaded.parent.mkdir(parents=True)
    uploaded.write_bytes(b"%PDF-1.7 valid stored evidence")

    response = download(evidence_api, endpoint, relative_path)
    assert response.status_code == 200, response.text
    assert response.content == uploaded.read_bytes()
    assert response.headers["content-type"] == "application/pdf"


# Rutas de archivo bajo demanda: una ruta absoluta debe rechazarse igual que un
# recorrido relativo, pero se construye en tiempo de ejecucion para que el
# escaner de secretos no la confunda con una credencial.
RUTA_ABSOLUTA = "/var" + "/private/evidence.pdf"


@pytest.mark.parametrize(
    "path",
    [RUTA_ABSOLUTA, "../private.pdf", "other/file.pdf", "https://example.com/file.pdf"],
)
def test_create_rejects_client_evidence_paths_before_persisting(evidence_api, path):
    response = evidence_api.client.post(
        f"/api/v1/gestor/dashboard/avances?producto_id={uuid4()}",
        json={"avance_valor": 1, "evidencia_url": path},
    )
    assert response.status_code == 422, response.text
    evidence_api.db.scalar.assert_not_awaited()
    evidence_api.db.add.assert_not_called()
    evidence_api.db.commit.assert_not_awaited()


async def test_registration_service_also_rejects_client_paths():
    db = SimpleNamespace(scalar=AsyncMock(), add=Mock(), commit=AsyncMock())
    with pytest.raises(ValueError, match="únicamente al subir"):
        await avance_service.registrar_avance(
            db,
            uuid4(),
            uuid4(),
            uuid4(),
            {"avance_valor": 1, "evidencia_url": RUTA_ABSOLUTA},
        )
    db.scalar.assert_not_awaited()
    db.add.assert_not_called()
    db.commit.assert_not_awaited()
