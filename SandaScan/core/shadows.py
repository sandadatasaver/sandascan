"""
Shadow Removal Module

Removes uneven lighting, shadows, and dark corners from document photos
while preserving text and image content.
"""

import cv2
import numpy as np


def remove_shadows(
    image: np.ndarray,
    kernel_size: int = 75,
    blur_sigma: float = 0.0,
) -> np.ndarray:
    """
    Remove shadows and uneven illumination from a document image.

    Uses morphological operations and division-based normalisation
    to separate the background illumination from the foreground content.

    Args:
        image: Input BGR image.
        kernel_size: Size of the morphological kernel (odd number).
                     Larger values handle larger shadows.
        blur_sigma: Sigma for Gaussian blur on the background model.
                    0 = auto-calculated from kernel_size.

    Returns:
        Shadow-free image.
    """
    if kernel_size % 2 == 0:
        kernel_size += 1

    # Convert to grayscale for illumination estimation
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    # Ensure float
    gray_float = gray.astype(np.float32)

    # Method 1: Morphological closing to estimate background illumination
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    background = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)

    # Further smooth the background
    if blur_sigma == 0:
        blur_sigma = kernel_size / 6
    background = cv2.GaussianBlur(background, (0, 0), blur_sigma)

    background = background.astype(np.float32)
    background = np.clip(background, 1, 255)

    # Normalize: divide by background, then scale
    normalized = (gray_float / background) * 255.0
    normalized = np.clip(normalized, 0, 255).astype(np.uint8)

    # Apply to each channel of color image
    result = image.copy()
    for c in range(3):
        channel = image[:, :, c].astype(np.float32)
        corrected = (channel / background) * 255.0
        result[:, :, c] = np.clip(corrected, 0, 255).astype(np.uint8)

    return result


def remove_shadows_adaptive(
    image: np.ndarray,
    block_size: int = 31,
    c_value: int = 10,
) -> np.ndarray:
    """
    Alternative shadow removal using adaptive thresholding approach.
    Works well for documents with strong shadows.

    Args:
        image: Input BGR image.
        block_size: Block size for adaptive thresholding (odd number).
        c_value: Constant subtracted from mean.

    Returns:
        Shadow-reduced image.
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    if block_size % 2 == 0:
        block_size += 1

    # Apply adaptive threshold
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, block_size, c_value
    )

    # Use the threshold as a mask to guide bilateral filtering
    filtered = cv2.bilateralFilter(gray, 9, 75, 75)

    # Blend based on shadow regions
    shadow_mask = cv2.bitwise_not(thresh)
    shadow_mask = cv2.dilate(shadow_mask, np.ones((5, 5), np.uint8), iterations=1)

    result = np.where(shadow_mask > 0, filtered, gray)

    if len(image.shape) == 3:
        return cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
    return result
