"""
Adaptive Sharpening Module

Applies unsharp masking with adaptive strength based on local
image content to sharpen text without amplifying noise in blank areas.
"""

import cv2
import numpy as np


def adaptive_sharpen(
    image: np.ndarray,
    strength: float = 1.5,
    radius: float = 1.0,
    threshold: int = 10,
) -> np.ndarray:
    """
    Sharpen a document image using adaptive unsharp masking.

    Sharpening is applied more strongly in high-detail regions
    (text, borders) and gently in smooth regions (blank paper).

    Args:
        image: Input BGR image.
        strength: Sharpening strength (0.0 = no sharpening, 2.0+ = aggressive).
        radius: Gaussian blur radius for the mask.
        threshold: Minimum intensity difference to apply sharpening.

    Returns:
        Sharpened image.
    """
    # Convert to float
    img_float = image.astype(np.float32)

    # Create Gaussian blur
    if radius < 1:
        radius = 1
    ksize = int(2 * round(radius) + 1)
    blurred = cv2.GaussianBlur(img_float, (ksize, ksize), radius)

    # Calculate the unsharp mask (detail layer)
    detail = img_float - blurred

    # Create edge-aware weighting
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_32F)
    edge_weight = np.abs(laplacian)
    edge_weight = cv2.GaussianBlur(edge_weight, (15, 15), 5)
    edge_weight = np.clip(edge_weight / (edge_weight.max() + 1e-6), 0, 1)

    # Expand to 3 channels
    edge_weight_3ch = np.stack([edge_weight] * 3, axis=2)

    # Adaptive strength: more sharpening on edges
    adaptive_strength = strength * (0.3 + 0.7 * edge_weight_3ch)

    # Apply adaptive sharpening
    sharpened = img_float + adaptive_strength * detail

    # Apply threshold: don't sharpen very small differences
    mask = np.abs(detail) < threshold
    sharpened[mask] = img_float[mask]

    result = np.clip(sharpened, 0, 255).astype(np.uint8)
    return result


def simple_sharpen(
    image: np.ndarray,
    strength: float = 1.0,
) -> np.ndarray:
    """
    Simple kernel-based sharpening.

    Args:
        image: Input BGR image.
        strength: Sharpening intensity.

    Returns:
        Sharpened image.
    """
    kernel = np.array([
        [0, -strength, 0],
        [-strength, 1 + 4 * strength, -strength],
        [0, -strength, 0]
    ])

    sharpened = cv2.filter2D(image, -1, kernel)
    return np.clip(sharpened, 0, 255).astype(np.uint8)
