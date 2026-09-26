"""Optimización segura de evidencias antes de almacenarlas."""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from io import BytesIO

from PIL import Image, ImageOps
from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError

from ..core.config import settings

MAX_IMAGE_PIXELS = 40_000_000
MAX_PDF_PAGES_TO_OPTIMIZE = 200


@dataclass(frozen=True)
class EvidenceOptimizationResult:
    content: bytes
    original_size: int
    stored_size: int
    optimized: bool
    method: str

    @property
    def saved_bytes(self) -> int:
        return self.original_size - self.stored_size

    @property
    def reduction_percent(self) -> float:
        if not self.original_size:
            return 0.0
        return round((self.saved_bytes / self.original_size) * 100, 2)


def optimize_evidence(content: bytes, content_type: str) -> EvidenceOptimizationResult:
    """Optimiza una evidencia y conserva el original si no obtiene ahorro."""
    if content_type in {"image/jpeg", "image/png"}:
        candidate = _optimize_image(content, content_type)
        method = "image-reencode"
    elif content_type == "application/pdf":
        candidate, method = _optimize_pdf(content)
    else:
        raise ValueError("Tipo de evidencia no soportado para optimización.")

    if len(candidate) >= len(content):
        candidate = content
        if method in {"image-reencode", "pdf-streams-and-images"}:
            method = "original-smaller"

    return EvidenceOptimizationResult(
        content=candidate,
        original_size=len(content),
        stored_size=len(candidate),
        optimized=len(candidate) < len(content),
        method=method,
    )


def _optimize_image(content: bytes, content_type: str) -> bytes:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(content)) as source:
                width, height = source.size
                if width * height > MAX_IMAGE_PIXELS:
                    raise ValueError("La imagen excede la resolución máxima permitida.")

                source.load()
                image = ImageOps.exif_transpose(source)
                max_dimension = settings.EVIDENCE_IMAGE_MAX_DIMENSION
                if max(image.size) > max_dimension:
                    image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

                output = BytesIO()
                if content_type == "image/jpeg":
                    if image.mode not in {"RGB", "L"}:
                        image = image.convert("RGB")
                    image.save(
                        output,
                        format="JPEG",
                        quality=settings.EVIDENCE_JPEG_QUALITY,
                        optimize=True,
                        progressive=True,
                    )
                else:
                    image.save(output, format="PNG", optimize=True, compress_level=9)
                return output.getvalue()
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValueError("La imagen excede la resolución máxima permitida.") from exc
    except (OSError, SyntaxError) as exc:
        raise ValueError("La imagen está dañada o no tiene un formato válido.") from exc


def _optimize_pdf(content: bytes) -> tuple[bytes, str]:
    try:
        reader = PdfReader(BytesIO(content), strict=False)
        if reader.is_encrypted:
            return content, "encrypted-pdf-preserved"
        if len(reader.pages) > MAX_PDF_PAGES_TO_OPTIMIZE:
            return content, "large-pdf-preserved"
        if _has_digital_signature(reader):
            return content, "signed-pdf-preserved"

        writer = PdfWriter(clone_from=BytesIO(content))
        for page in writer.pages:
            for image_file in page.images:
                try:
                    image = image_file.image
                    max_dimension = settings.EVIDENCE_IMAGE_MAX_DIMENSION
                    if max(image.size) > max_dimension:
                        image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
                    image_file.replace(image, quality=settings.EVIDENCE_PDF_IMAGE_QUALITY)
                except (OSError, ValueError, TypeError, NotImplementedError):
                    continue
            page.compress_content_streams(level=9)

        writer.compress_identical_objects(remove_duplicates=True, remove_unreferenced=True)
        output = BytesIO()
        writer.write(output)
        return output.getvalue(), "pdf-streams-and-images"
    except (PdfReadError, OSError, ValueError) as exc:
        raise ValueError("El PDF está dañado o no tiene una estructura válida.") from exc


def _has_digital_signature(reader: PdfReader) -> bool:
    fields = reader.get_fields() or {}
    return any(str(field.get("/FT", "")) == "/Sig" for field in fields.values())
