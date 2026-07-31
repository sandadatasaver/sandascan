"""
Noise Removal Module

Removes camera noise, JPEG artifacts, and dust spots from
document images while preserving text edges.
"""

import cv2
import numpy as np


def denoise(
    image: np.ndarray,
    strength: int = 10,
    template_window: int = 7,
    search_window: int = 21,
) -> np.ndarray:
    """
    Remove noise from a document image using Non-Local Means Denoising.

    Preserves text edges better than Gaussian blur while removing
    high-frequency noise and JPEG artifacts.

    Args:
        image: Input BGR image.
        strength: Filter strength (higher = more denoising, 1-20).
        template_window: Size of template patch (odd, 5-15).
        search_window: Size of search window (odd, 15-35).

    Returns:
        Denoised image.
    """
    # Ensure odd window sizes
    if template_window % 2 == 0:
        template_window += 1
    if search_window % 2 == 0:
        search_window += 1

    # NLM denoising works color or grayscale
    denoised = cv2.fastNlMeansDenoisingColored(
        image, None, strength, strength,
        template_window, search_window
    )

    return denoised


def denoise_light(image: np.ndarray) -> np.ndarray:
    """
    Lightweight denoising using a bilateral filter.
    Faster than NLM but slightly less effective.

    Args:
        image: Input BGR image.

    Returns:
        Denoised image.
    """
    return cv2.bilateralFilter(image, 9, 75, 75)


def remove_dust_and_specks(
    image: np.ndarray,
    kernel_size: int = 3,
    threshold_area: int = 50,
) -> np.ndarray:
    """
    Remove small dust specks and artifacts using morphological
    operations.

    Args:
        image: Input BGR image.
        kernel_size: Size of the morphological kernel.
        threshold_area: Maximum contour area to consider as speck.

    Returns:
        Cleaned image.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Find small contours
    contours, _ = cv2.findContours(
        binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    # Create mask of specks to remove
    speck_mask = np.zeros_like(binary)
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if 0 < area <= threshold_area:
            cv2.drawContours(speck_mask, [cnt], -1, 255, -1)

    # Inpaint specks
    result = cv2.inpaint(image, speck_mask, 3, cv2.INPAINT_TELEA)

    return result
