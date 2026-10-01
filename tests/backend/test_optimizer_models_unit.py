"""Cobertura unitaria de rutas defensivas del optimizador y del modelo base."""

from io import BytesIO
from types import SimpleNamespace
from uuid import uuid4

import pytest
from PIL import Image
from pypdf.errors import PdfReadError

from src.backend.models.base import BaseModel
from src.backend.services import evidence_optimizer as optimizer


def _image_bytes(mode: str, image_format: str) -> bytes:
    image = Image.new(mode, (2, 2), 0)
    output = BytesIO()
    image.save(output, format=image_format)
    return output.getvalue()


def test_optimization_result_zero_size_and_unsupported_type():
    result = optimizer.EvidenceOptimizationResult(b"", 0, 0, False, "none")

    assert result.saved_bytes == 0
    assert result.reduction_percent == 0.0
    with pytest.raises(ValueError, match="no soportado"):
        optimizer.optimize_evidence(b"data", "text/plain")


def test_optimization_result_calculates_reduction():
    result = optimizer.EvidenceOptimizationResult(b"x", 3, 1, True, "test")

    assert result.reduction_percent == 66.67


def test_optimize_evidence_preserves_larger_candidates(monkeypatch):
    monkeypatch.setattr(optimizer, "_optimize_image", lambda *_: b"candidate")
    image_result = optimizer.optimize_evidence(b"tiny", "image/jpeg")
    monkeypatch.setattr(optimizer, "_optimize_pdf", lambda _: (b"candidate", "custom"))
    pdf_result = optimizer.optimize_evidence(b"tiny", "application/pdf")

    assert image_result.method == "original-smaller"
    assert image_result.content == b"tiny"
    assert pdf_result.method == "custom"
    assert pdf_result.content == b"tiny"


def test_optimize_image_converts_non_rgb_jpeg():
    result = optimizer._optimize_image(_image_bytes("RGBA", "PNG"), "image/jpeg")

    with Image.open(BytesIO(result)) as image:
        assert image.mode == "RGB"
        assert image.format == "JPEG"


def test_optimize_image_rejects_excessive_dimensions(monkeypatch):
    monkeypatch.setattr(optimizer, "MAX_IMAGE_PIXELS", 1)

    with pytest.raises(ValueError, match="resolución máxima"):
        optimizer._optimize_image(_image_bytes("RGB", "PNG"), "image/png")


@pytest.mark.parametrize(
    "error",
    [
        Image.DecompressionBombError("bomb"),
        Image.DecompressionBombWarning("warning"),
        OSError("broken"),
        SyntaxError("broken"),
    ],
)
def test_optimize_image_translates_library_errors(monkeypatch, error):
    def fail_open(*_args, **_kwargs):
        raise error

    monkeypatch.setattr(optimizer.Image, "open", fail_open)

    expected = (
        "resolución máxima"
        if isinstance(
            error, (Image.DecompressionBombError, Image.DecompressionBombWarning)
        )
        else "dañada"
    )
    with pytest.raises(ValueError, match=expected):
        optimizer._optimize_image(b"image", "image/png")


def test_optimize_pdf_preserves_large_and_signed_documents(monkeypatch):
    large_reader = SimpleNamespace(
        is_encrypted=False,
        pages=[None] * (optimizer.MAX_PDF_PAGES_TO_OPTIMIZE + 1),
    )
    monkeypatch.setattr(optimizer, "PdfReader", lambda *_args, **_kwargs: large_reader)
    assert optimizer._optimize_pdf(b"pdf") == (b"pdf", "large-pdf-preserved")

    signed_reader = SimpleNamespace(
        is_encrypted=False, pages=[], get_fields=lambda: {"x": {"/FT": "/Sig"}}
    )
    monkeypatch.setattr(optimizer, "PdfReader", lambda *_args, **_kwargs: signed_reader)
    assert optimizer._optimize_pdf(b"pdf") == (b"pdf", "signed-pdf-preserved")


def test_optimize_pdf_handles_missing_and_failing_images(monkeypatch):
    oversized = Image.new("RGB", (4, 2))

    class ImageFile:
        def __init__(self, image, error=None):
            self.image = image
            self.error = error
            self.replaced = False

        def replace(self, *_args, **_kwargs):
            if self.error:
                raise self.error
            self.replaced = True

    missing = ImageFile(None)
    failing = ImageFile(oversized.copy(), ValueError("unsupported"))
    valid = ImageFile(oversized.copy())

    class Page:
        images = [missing, failing, valid]

        def compress_content_streams(self, level):
            assert level == 9

    class Writer:
        pages = [Page()]

        def __init__(self, **_kwargs):
            pass

        def compress_identical_objects(self, **kwargs):
            assert kwargs == {"remove_duplicates": True, "remove_unreferenced": True}

        def write(self, output):
            output.write(b"optimized")

    reader = SimpleNamespace(is_encrypted=False, pages=[], get_fields=lambda: None)
    monkeypatch.setattr(optimizer, "PdfReader", lambda *_args, **_kwargs: reader)
    monkeypatch.setattr(optimizer, "PdfWriter", Writer)
    monkeypatch.setattr(optimizer.settings, "EVIDENCE_IMAGE_MAX_DIMENSION", 2)

    assert optimizer._optimize_pdf(b"pdf") == (b"optimized", "pdf-streams-and-images")
    assert valid.replaced is True
    assert max(valid.image.size) == 2


@pytest.mark.parametrize(
    "error", [PdfReadError("broken"), OSError("broken"), ValueError("broken")]
)
def test_optimize_pdf_translates_reader_errors(monkeypatch, error):
    def fail_reader(*_args, **_kwargs):
        raise error

    monkeypatch.setattr(optimizer, "PdfReader", fail_reader)

    with pytest.raises(ValueError, match="PDF está dañado"):
        optimizer._optimize_pdf(b"pdf")


def test_signature_detection_handles_empty_and_non_signature_fields():
    assert (
        optimizer._has_digital_signature(SimpleNamespace(get_fields=lambda: None))
        is False
    )
    reader = SimpleNamespace(get_fields=lambda: {"text": {"/FT": "/Tx"}, "empty": {}})
    assert optimizer._has_digital_signature(reader) is False


def test_base_model_soft_delete_and_properties():
    model = BaseModel(deleted_at=None)
    user_id = uuid4()

    assert model.is_deleted is False
    assert model.eliminado is False
    model.soft_delete(user_id)

    assert model.is_deleted is True
    assert model.eliminado is True
    assert model.deleted_by == user_id
    assert model.estado == "ELIMINADO_LOGICAMENTE"


def test_base_model_eliminado_setter_and_class_expression():
    model = BaseModel(deleted_at=None)

    model.eliminado = True
    assert model.deleted_at is not None
    assert model.estado == "ELIMINADO_LOGICAMENTE"
    model.eliminado = False
    assert model.deleted_at is None
    assert str(BaseModel.eliminado.expression).endswith("IS NOT NULL")
