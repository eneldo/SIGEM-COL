"""Pruebas unitarias del optimizador de evidencias."""

from io import BytesIO

import pytest
from PIL import Image
from pypdf import PdfReader, PdfWriter

from src.backend.services.evidence_optimizer import optimize_evidence


def _large_jpeg() -> bytes:
    image = Image.effect_noise((3200, 2400), 80).convert("RGB")
    output = BytesIO()
    image.save(output, format="JPEG", quality=98)
    return output.getvalue()


def test_optimize_jpeg_reduces_size_and_resolution():
    original = _large_jpeg()

    result = optimize_evidence(original, "image/jpeg")

    assert result.optimized is True
    assert result.stored_size < result.original_size
    assert result.saved_bytes == result.original_size - result.stored_size
    with Image.open(BytesIO(result.content)) as image:
        assert max(image.size) <= 2200
        assert image.format == "JPEG"


def test_optimize_png_keeps_original_when_candidate_is_larger():
    image = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    original = output.getvalue()

    result = optimize_evidence(original, "image/png")

    assert result.content == original
    assert result.optimized is False
    assert result.saved_bytes == 0


def test_optimize_pdf_produces_readable_pdf():
    image = Image.effect_noise((1600, 1200), 80).convert("RGB")
    output = BytesIO()
    image.save(output, format="PDF", quality=98, resolution=150)
    original = output.getvalue()

    result = optimize_evidence(original, "application/pdf")

    assert result.optimized is True
    assert result.stored_size < result.original_size
    assert len(PdfReader(BytesIO(result.content)).pages) == 1


def test_optimize_preserves_encrypted_pdf():
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.encrypt("secret")
    output = BytesIO()
    writer.write(output)
    original = output.getvalue()

    result = optimize_evidence(original, "application/pdf")

    assert result.content == original
    assert result.optimized is False
    assert result.method == "encrypted-pdf-preserved"


@pytest.mark.parametrize(
    ("content", "content_type"),
    [(b"not-an-image", "image/jpeg"), (b"%PDF-invalid", "application/pdf")],
)
def test_optimize_rejects_corrupted_files(content: bytes, content_type: str):
    with pytest.raises(ValueError):
        optimize_evidence(content, content_type)
