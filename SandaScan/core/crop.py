"""
Auto-Crop & Page Boundary Detection Module

Detects document page boundaries and automatically crops
to the content area.
"""

import cv2
import numpy as np
from typing import Tuple, Optional


def detect_page_boundaries(
    image: np.ndarray,
    edge_threshold: int = 50,
    min_content_ratio: float = 0.3,
) -> Optional[Tuple[int, int, int, int]]:
    """
    Detect the rectangular page boundaries within an image.

    Uses edge detection and contour analysis to find the document
    page region.

    Args:
        image: Input BGR or grayscale image.
        edge_threshold: Canny edge detection threshold.
        min_content_ratio: Minimum content area as fraction of image.

    Returns:
        (x, y, width, height) of the page region, or None.
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    h, w = gray.shape

    # Edge detection
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, edge_threshold, edge_threshold * 2)

    # Dilate to close gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    dilated = cv2.dilate(edges, kernel, iterations=2)

    # Find contours
    contours, _ = cv2.findContours(
        dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        return None

    # Find the largest contour that could be a page
    best_contour = None
    best_area = 0

    for cnt in contours:
        area = cv2.contourArea(cnt)
        area_ratio = area / (w * h)

        if area_ratio < min_content_ratio:
            continue

        if area > best_area:
            best_area = area
            best_contour = cnt

    if best_contour is None:
        return None

    x, y, bw, bh = cv2.boundingRect(best_contour)
    return (x, y, bw, bh)


def auto_crop(image: np.ndarray, padding: int = 10) -> np.ndarray:
    """
    Automatically crop to the document page boundaries.

    Adds a small padding around the detected page.

    Args:
        image: Input BGR image.
        padding: Padding in pixels to add around the detected page.

    Returns:
        Cropped image.
    """
    bounds = detect_page_boundaries(image)

    if bounds is None:
        # Fallback: crop white/empty borders
        return _crop_white_borders(image, padding)

    x, y, bw, bh = bounds
    h, w = image.shape[:2]

    # Add padding, ensuring we don't go out of bounds
    x1 = max(0, x - padding)
    y1 = max(0, y - padding)
    x2 = min(w, x + bw + padding)
    y2 = min(h, y + bh + padding)

    return image[y1:y2, x1:x2]


def _crop_white_borders(
    image: np.ndarray,
    padding: int = 10,
    threshold: int = 240,
) -> np.ndarray:
    """
    Crop white/empty borders from the image.
    Used as fallback when page detection fails.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Find rows and columns with content (non-white pixels)
    _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)

    rows = np.any(binary, axis=1)
    cols = np.any(binary, axis=0)

    y_min = np.argmax(rows) if np.any(rows) else 0
    y_max = len(rows) - np.argmax(rows[::-1]) if np.any(rows) else len(rows)
    x_min = np.argmax(cols) if np.any(cols) else 0
    x_max = len(cols) - np.argmax(cols[::-1]) if np.any(cols) else len(cols)

    # Add padding
    h, w = image.shape[:2]
    x_min = max(0, x_min - padding)
    y_min = max(0, y_min - padding)
    x_max = min(w, x_max + padding)
    y_max = min(h, y_max + padding)

    return image[y_min:y_max, x_min:x_max]


def normalize_to_a4(
    image: np.ndarray,
    dpi: int = 300,
) -> np.ndarray:
    """
    Resize/crop image to standard A4 aspect ratio.

    A4 at specified DPI:
        Width  = 210mm * DPI / 25.4
        Height = 297mm * DPI / 25.4

    Args:
        image: Input BGR image.
        dpi: Dots per inch for output.

    Returns:
        A4-normalized image.
    """
    a4_w = int(210 * dpi / 25.4)
    a4_h = int(297 * dpi / 25.4)

    return cv2.resize(image, (a4_w, a4_h), interpolation=cv2.INTER_CUBIC)
