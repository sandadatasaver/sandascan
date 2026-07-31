"""
SandaScan Core - Computer Vision Document Restoration Engine

A professional-grade document restoration pipeline using OpenCV.
Preserves every pixel faithfully — never regenerates or invents text.
"""

# Lazy imports — individual modules are imported when actually used,
# so missing optional dependencies (like reportlab) don't break everything.

from .perspective import correct_perspective, deskew, find_document_contour
from .shadows import remove_shadows
from .enhance import whiten_background, enhance_contrast, auto_levels
from .sharpen import adaptive_sharpen, simple_sharpen
from .noise import denoise, denoise_light
from .crop import auto_crop, detect_page_boundaries, normalize_to_a4
from .pipeline import PipelineConfig, PipelineStep, restore_document, restore_batch
from .batch import BatchProcessor, BatchResult

# PDF and OCR are imported on demand (they have heavier dependencies)
# from .pdf import images_to_pdf, images_to_searchable_pdf
# from .ocr import extract_text, make_searchable_pdf
