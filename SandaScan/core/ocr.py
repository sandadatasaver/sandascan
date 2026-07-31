"""
OCR Module - Multi-Engine Text Recognition

Provides text extraction and searchable PDF generation.
Supports multiple OCR backends with automatic fallback.

Backends (in priority order):
  1. pytesseract (recommended for Windows — easy to set up)
  2. tesserocr (faster, Linux only — needs compiled C lib)
  3. PaddleOCR (best for complex layouts)
"""

import os
import cv2
import numpy as np
from typing import List, Optional, Tuple

# ── Backend Detection ─────────────────────────────────────────────────────

# Default tessdata path (bundled in the SandaScan folder)
_DEFAULT_TESSDATA = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "tessdata",
)

TESSDATA_PREFIX = os.environ.get("TESSDATA_PREFIX", _DEFAULT_TESSDATA)

_HAS_TESSEROCR = False
_HAS_PYTESSERACT = False
_HAS_PADDLEOCR = False

# Try importing pytesseract first (most portable)
try:
    import pytesseract
    _HAS_PYTESSERACT = True
    # Check if Tesseract binary is actually available
    try:
        pytesseract.get_tesseract_version()
    except Exception:
        _HAS_PYTESSERACT = False
except (ImportError, Exception):
    pass

# Try tesserocr (faster but needs compiled C library)
try:
    from tesserocr import PyTessBaseAPI, PSM, OEM
    _HAS_TESSEROCR = True
except (ImportError, Exception):
    pass

# Try PaddleOCR (heavy but powerful)
try:
    from paddleocr import PaddleOCR
    _HAS_PADDLEOCR = True
except (ImportError, Exception):
    pass


def get_available_backends() -> List[str]:
    """Return list of available OCR backends."""
    backends = []
    if _HAS_PYTESSERACT:
        backends.append("pytesseract")
    if _HAS_TESSEROCR:
        backends.append("tesserocr")
    if _HAS_PADDLEOCR:
        backends.append("paddleocr")
    return backends


# ── Pytesseract Backend (Windows-friendly) ───────────────────────────────

def _find_tesseract_candidate_paths() -> List[str]:
    """Return common Tesseract installation paths for Windows/Linux/Mac."""
    return [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
        "/opt/homebrew/bin/tesseract",
    ]


def _configure_pytesseract():
    """
    Auto-configure pytesseract by searching common Tesseract binary locations.
    Call this before extracting text if pytesseract isn't configured.
    """
    import pytesseract
    try:
        pytesseract.get_tesseract_version()
        return  # already configured
    except Exception:
        pass

    # Search common paths
    for path in _find_tesseract_candidate_paths():
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            try:
                pytesseract.get_tesseract_version()
                return
            except Exception:
                continue

    raise RuntimeError(
        "Tesseract is not installed or not found.\n\n"
        "📥 Download & install Tesseract from:\n"
        "   https://github.com/UB-Mannheim/tesseract/wiki\n\n"
        "Then restart the app. No need to reinstall Python packages."
    )


def _extract_pytesseract(image: np.ndarray, lang: str = "eng") -> str:
    """Extract text via pytesseract."""
    import pytesseract
    _configure_pytesseract()

    # Convert BGR (OpenCV) to RGB (pytesseract expects RGB or grayscale)
    if len(image.shape) == 3:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    else:
        rgb = image

    # Custom config for better document OCR
    custom_config = r"--oem 3 --psm 4"
    text = pytesseract.image_to_string(rgb, lang=lang, config=custom_config)
    return text.strip()


# ── tesserocr Backend (Linux/Mac) ─────────────────────────────────────────

_tesserocr_api = None


def _get_tesserocr_api(lang: str = "eng") -> "PyTessBaseAPI":
    """Get a cached tesserocr API instance."""
    global _tesserocr_api
    if _tesserocr_api is None:
        from tesserocr import PyTessBaseAPI, PSM

        tessdata = TESSDATA_PREFIX
        if not os.path.exists(os.path.join(tessdata, f"{lang}.traineddata")):
            # Try alternative paths
            for candidate in [
                "/usr/share/tessdata",
                "/usr/local/share/tessdata",
                os.path.expanduser("~/.tessdata"),
            ]:
                if os.path.exists(os.path.join(candidate, f"{lang}.traineddata")):
                    tessdata = candidate
                    break

        os.environ["TESSDATA_PREFIX"] = tessdata
        _tesserocr_api = PyTessBaseAPI(lang=lang, psm=PSM.AUTO)
    return _tesserocr_api


def _extract_tesserocr(image: np.ndarray, lang: str = "eng") -> str:
    """Extract text via tesserocr."""
    from PIL import Image
    api = _get_tesserocr_api(lang)

    if len(image.shape) == 3:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    else:
        rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    pil_img = Image.fromarray(rgb)

    api.SetImage(pil_img)
    text = api.GetUTF8Text()
    return text.strip()


# ── PaddleOCR Backend ─────────────────────────────────────────────────────

_paddleocr_engine = None


def _get_paddleocr_engine(lang: str = "en"):
    """Get or create PaddleOCR engine."""
    global _paddleocr_engine
    if _paddleocr_engine is None:
        from paddleocr import PaddleOCR
        _paddleocr_engine = PaddleOCR(
            lang=lang,
            use_textline_orientation=True,
        )
    return _paddleocr_engine


def _extract_paddleocr(image: np.ndarray, lang: str = "en") -> str:
    """Extract text via PaddleOCR."""
    ocr = _get_paddleocr_engine(lang)
    result = ocr.ocr(image)

    if not result or not result[0]:
        return ""

    lines = []
    for line in result[0]:
        if line and len(line) >= 2:
            text = line[1][0]
            lines.append(text)
    return "\n".join(lines)


# ── Unified API ───────────────────────────────────────────────────────────

def extract_text(
    image: np.ndarray,
    lang: str = "eng",
    backend: Optional[str] = None,
) -> str:
    """
    Extract text from a document image using the best available OCR backend.

    Args:
        image: Input BGR image (OpenCV format).
        lang: Language code ('eng' for English).
        backend: Force a specific backend ('pytesseract', 'tesserocr', 'paddleocr').
                 If None, automatically selects the best available.

    Returns:
        Extracted text as a string.
    """
    # Automatically select backend
    if backend is None:
        if _HAS_PYTESSERACT:
            backend = "pytesseract"
        elif _HAS_TESSEROCR:
            backend = "tesserocr"
        elif _HAS_PADDLEOCR:
            backend = "paddleocr"
        else:
            raise RuntimeError(
                "No OCR backend available.\n\n"
                "📥 The easiest option for Windows:\n"
                "   1. pip install pytesseract\n"
                "   2. Download & install Tesseract from:\n"
                "      https://github.com/UB-Mannheim/tesseract/wiki\n\n"
                "Or install one of: tesserocr (Linux), paddleocr (requires paddlepaddle)"
            )

    # Map language codes
    tesseract_lang = lang  # 'eng' for both pytesseract and tesserocr

    # Extract using selected backend
    if backend == "pytesseract":
        return _extract_pytesseract(image, tesseract_lang)
    elif backend == "tesserocr":
        return _extract_tesserocr(image, tesseract_lang)
    elif backend == "paddleocr":
        paddle_lang = lang if lang != "eng" else "en"
        return _extract_paddleocr(image, paddle_lang)
    else:
        raise ValueError(f"Unknown OCR backend: {backend}")


def extract_text_with_confidence(
    image: np.ndarray,
    lang: str = "eng",
    min_confidence: float = 0.0,
) -> List[Tuple[str, float, np.ndarray]]:
    """
    Extract text with bounding boxes and confidence scores.

    Args:
        image: Input BGR image.
        lang: Language code.
        min_confidence: Minimum confidence threshold (0.0-1.0).

    Returns:
        List of (text, confidence, bbox) tuples.
    """
    results = []

    if _HAS_TESSEROCR:
        from PIL import Image
        api = _get_tesserocr_api(lang)

        if len(image.shape) == 3:
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        pil_img = Image.fromarray(rgb)
        api.SetImage(pil_img)

        api.Recognize()
        ri = api.GetIterator()
        if ri:
            for w in ri:
                text = w.GetUTF8Text(ri.RIL_WORD)
                conf = w.Confidence(ri.RIL_WORD) / 100.0
                if text and conf >= min_confidence:
                    bbox = w.BoundingBox(ri.RIL_WORD)
                    results.append((text, conf, np.array(bbox)))
    elif _HAS_PYTESSERACT:
        try:
            _configure_pytesseract()
            import pytesseract

            if len(image.shape) == 3:
                rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                rgb = image

            data = pytesseract.image_to_data(rgb, lang=lang, output_type=pytesseract.Output.DICT)
            for i in range(len(data["text"])):
                text = data["text"][i].strip()
                conf = int(data["conf"][i]) / 100.0 if data["conf"][i] != "-1" else 0
                if text and conf >= min_confidence:
                    x, y, w, h = (data["left"][i], data["top"][i],
                                  data["width"][i], data["height"][i])
                    bbox = np.array([[x, y], [x+w, y], [x+w, y+h], [x, y+h]], dtype=np.int32)
                    results.append((text, conf, bbox))
        except Exception:
            pass

    return results


def make_searchable_pdf(
    image_paths: List[str],
    output_path: str,
    lang: str = "eng",
    dpi: int = 300,
) -> str:
    """
    Create a searchable PDF from a list of image files.

    Processes each image with OCR and embeds the text as an
    invisible layer on top of the scanned page image.

    Args:
        image_paths: List of paths to input images.
        output_path: Path to save the searchable PDF.
        lang: Language code for OCR.
        dpi: Output DPI.

    Returns:
        Path to the generated PDF.
    """
    from .pdf import images_to_searchable_pdf

    images = []
    texts = []

    for img_path in image_paths:
        img = cv2.imread(img_path)
        if img is None:
            print(f"⚠️  Warning: Could not read {img_path}, skipping.")
            continue

        images.append(img)
        try:
            text = extract_text(img, lang=lang)
            texts.append(text)
            word_count = len(text.split())
            print(f"   OCR: {os.path.basename(img_path)} — {word_count} words")
        except Exception as e:
            print(f"   OCR: {os.path.basename(img_path)} — error: {e}")
            texts.append("")

    if not images:
        raise ValueError("No valid images to process")

    return images_to_searchable_pdf(images, texts, output_path, dpi=dpi)


def extract_text_from_file(image_path: str, lang: str = "eng") -> str:
    """
    Extract text from an image file.

    Args:
        image_path: Path to the image file.
        lang: Language code.

    Returns:
        Extracted text.
    """
    img = cv2.imread(image_path)
    if img is None:
        return ""
    return extract_text(img, lang=lang)
