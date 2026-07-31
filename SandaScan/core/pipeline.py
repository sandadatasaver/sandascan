"""
Restoration Pipeline Module

Orchestrates the complete document restoration pipeline:
  1. Auto-crop & page detection
  2. Perspective correction & deskew
  3. Shadow removal
  4. Background whitening
  5. Contrast enhancement
  6. Noise removal
  7. Adaptive sharpening
  8. A4 normalization
  9. PDF output (with optional OCR)
"""

import os
import cv2
import numpy as np
from typing import Callable, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .perspective import correct_perspective, deskew
from .shadows import remove_shadows
from .enhance import whiten_background, enhance_contrast
from .sharpen import adaptive_sharpen
from .noise import denoise
from .crop import normalize_to_a4

# PDF/OCR are imported lazily inside the functions that use them
# (they depend on reportlab which may not be installed yet)


class PipelineStep(Enum):
    """Identifies each step in the restoration pipeline."""
    LOAD = "load"
    PAGE_DETECT = "page_detection"
    DESKEW = "deskew"
    PERSPECTIVE = "perspective_correction"
    SHADOW_REMOVAL = "shadow_removal"
    WHITEN = "background_whitening"
    CONTRAST = "contrast_enhancement"
    DENOISE = "noise_removal"
    SHARPEN = "adaptive_sharpening"
    NORMALIZE = "a4_normalization"
    OCR = "ocr"
    PDF = "pdf_export"


@dataclass
class PipelineConfig:
    """Configuration for the document restoration pipeline."""

    # Output
    dpi: int = 300
    output_format: str = "pdf"  # 'pdf', 'searchable_pdf', 'images'

    # Page detection & Perspective correction
    page_detection: bool = True        # Find document edges & crop background
    perspective_correction: bool = True  # Correct camera angle distortion
    deskew_enabled: bool = True
    document_width: int = 2480   # A4 at 300 DPI
    document_height: int = 3508  # A4 at 300 DPI

    # Shadow removal
    shadow_removal_enabled: bool = True
    shadow_kernel_size: int = 75

    # Background whitening
    whiten_enabled: bool = True
    white_threshold: int = 200
    whiten_strength: float = 0.7

    # Contrast
    contrast_enabled: bool = True
    contrast_clip_limit: float = 2.0

    # Denoise
    denoise_enabled: bool = True
    denoise_strength: int = 10

    # Sharpening
    sharpen_enabled: bool = True
    sharpen_strength: float = 1.5
    sharpen_radius: float = 1.0

    # Normalize to A4
    normalize_a4: bool = True

    # OCR
    ocr_enabled: bool = True
    ocr_language: str = "en"

    # Callbacks
    progress_callback: Optional[Callable[[str, float], None]] = None

    def __post_init__(self):
        if self.progress_callback is None:
            self.progress_callback = lambda step, pct: None


def restore_document(
    image: np.ndarray,
    config: Optional[PipelineConfig] = None,
) -> np.ndarray:
    """
    Run the full document restoration pipeline on a single image.

    Args:
        image: Input BGR image.
        config: Pipeline configuration. Uses defaults if None.

    Returns:
        Fully restored document image.
    """
    if config is None:
        config = PipelineConfig()

    cb = config.progress_callback
    result = image.copy()

    try:
        # Step 1: Page detection + Perspective correction (also crops out background)
        if config.perspective_correction:
            cb(PipelineStep.PAGE_DETECT, 0.05)
            result = correct_perspective(
                result,
                output_width=config.document_width,
                output_height=config.document_height,
                auto_detect=config.page_detection,
            )

        # Step 2: Deskew (fine-tune rotation after perspective correction)
        if config.deskew_enabled:
            cb(PipelineStep.DESKEW, 0.15)
            result = deskew(result)

        # Step 3: Shadow removal
        if config.shadow_removal_enabled:
            cb(PipelineStep.SHADOW_REMOVAL, 0.40)
            result = remove_shadows(result, kernel_size=config.shadow_kernel_size)

        # Step 4: Background whitening
        if config.whiten_enabled:
            cb(PipelineStep.WHITEN, 0.55)
            result = whiten_background(
                result,
                white_threshold=config.white_threshold,
                strength=config.whiten_strength,
            )

        # Step 5: Contrast enhancement
        if config.contrast_enabled:
            cb(PipelineStep.CONTRAST, 0.65)
            result = enhance_contrast(result, clip_limit=config.contrast_clip_limit)

        # Step 6: Denoise
        if config.denoise_enabled:
            cb(PipelineStep.DENOISE, 0.75)
            result = denoise(result, strength=config.denoise_strength)

        # Step 7: Adaptive sharpening
        if config.sharpen_enabled:
            cb(PipelineStep.SHARPEN, 0.85)
            result = adaptive_sharpen(
                result,
                strength=config.sharpen_strength,
                radius=config.sharpen_radius,
            )

        # Step 8: Ensure consistent output size (in case perspective was skipped)
        if config.normalize_a4:
            cb(PipelineStep.NORMALIZE, 0.95)
            result = normalize_to_a4(result, dpi=config.dpi)
    except Exception as e:
        # If anything fails on this page, return a safe fallback
        cb(PipelineStep.PDF, 1.0)
        print(f"⚠️  Page restoration failed: {e}. Using original image resized.")
        return _safe_fallback(image, config.document_width, config.document_height)

    cb(PipelineStep.PDF, 1.0)
    return result


def _safe_fallback(image, target_w, target_h):
    """Safe fallback when restoration fails - resize while preserving aspect ratio, white padding."""
    h, w = image.shape[:2]
    scale = min(target_w / w, target_h / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    canvas = np.ones((target_h, target_w, 3), dtype=np.uint8) * 255
    x_off = (target_w - new_w) // 2
    y_off = (target_h - new_h) // 2
    canvas[y_off:y_off+new_h, x_off:x_off+new_w] = resized
    return canvas


def restore_batch(
    images: List[np.ndarray],
    output_path: str,
    config: Optional[PipelineConfig] = None,
    filenames: Optional[List[str]] = None,
) -> str:
    """
    Restore a batch of images and save as a single PDF.

    Args:
        images: List of input BGR images.
        output_path: Path to save the output PDF.
        config: Pipeline configuration.
        filenames: Optional list of original filenames for logging.

    Returns:
        Path to the output file.
    """
    if config is None:
        config = PipelineConfig()

    cb = config.progress_callback
    restored_images = []
    page_names = []

    total = len(images)
    for i, img in enumerate(images):
        name = filenames[i] if filenames and i < len(filenames) else f"page_{i+1}"
        page_names.append(name)
        cb(PipelineStep.LOAD, i / total)

        try:
            restored = restore_document(img, config)
            restored_images.append(restored)
            print(f"   ✅ {name} restored successfully ({restored.shape[1]}x{restored.shape[0]})")
        except Exception as e:
            print(f"   ❌ {name} failed: {e}. Using original image.")
            # Use safe fallback for this page
            if hasattr(config, 'document_width') and hasattr(config, 'document_height'):
                restored = _safe_fallback(img, config.document_width, config.document_height)
            else:
                restored = _safe_fallback(img, 2480, 3508)
            restored_images.append(restored)

    if not restored_images:
        raise ValueError("No pages could be processed!")

    # Export to PDF
    cb(PipelineStep.PDF, 1.0)

    if config.ocr_enabled and config.output_format == "searchable_pdf":
        from .ocr import extract_text

        texts = []
        ocr_failed_count = 0
        for i, img in enumerate(restored_images):
            cb(PipelineStep.OCR, 0.5 + 0.5 * i / len(restored_images))
            try:
                text = extract_text(img, lang=config.ocr_language)
                texts.append(text)
                wc = len(text.split())
                print(f"   OCR {page_names[i]}: {wc} words")
            except Exception as e:
                ocr_failed_count += 1
                print(f"   OCR {page_names[i]}: failed ({e})")
                texts.append("")

        if ocr_failed_count == len(restored_images):
            # All OCR failed — fall back to image PDF
            print("⚠️  OCR failed on all pages. Falling back to image-only PDF.")
            from .pdf import images_to_pdf
            return images_to_pdf(restored_images, output_path, dpi=config.dpi)
        else:
            from .pdf import images_to_searchable_pdf
            note = f" (OCR failed on {ocr_failed_count} page(s))" if ocr_failed_count > 0 else ""
            print(f"✅ Searchable PDF with OCR{note}")
            return images_to_searchable_pdf(
                restored_images, texts, output_path, dpi=config.dpi
            )

    # Fallback: regular image PDF (no searchable text layer)
    from .pdf import images_to_pdf
    return images_to_pdf(restored_images, output_path, dpi=config.dpi)
