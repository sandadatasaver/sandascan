"""
Background Whitening & Contrast Enhancement Module

Whitens the paper background while keeping ink/text natural black,
and applies adaptive contrast enhancement for readability.
"""

import cv2
import numpy as np


def whiten_background(
    image: np.ndarray,
    white_threshold: int = 200,
    strength: float = 0.7,
) -> np.ndarray:
    """
    Whiten the paper background of a document image.

    Uses the illumination-corrected image to map background pixels
    toward pure white while preserving foreground (text, ink, stamps).

    Args:
        image: Input BGR image (preferably after shadow removal).
        white_threshold: Pixels with all channels above this value
                         are considered background.
        strength: How strongly to whiten (0.0 = no change, 1.0 = full).

    Returns:
        Background-whitened image.
    """
    result = image.copy().astype(np.float32)

    # Create a background mask
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, bg_mask = cv2.threshold(gray, white_threshold, 255, cv2.THRESH_BINARY)

    # Smooth the mask to avoid hard edges
    bg_mask_float = cv2.GaussianBlur(bg_mask.astype(np.float32), (15, 15), 5) / 255.0

    # Expanded version for multi-channel
    bg_mask_3ch = np.stack([bg_mask_float] * 3, axis=2)

    # Target white value
    target_white = np.full_like(result, 255.0)

    # Blend: result = image + strength * mask * (white - image)
    blend = result + strength * bg_mask_3ch * (target_white - result)
    result = np.clip(blend, 0, 255).astype(np.uint8)

    return result


def enhance_contrast(
    image: np.ndarray,
    clip_limit: float = 2.0,
    tile_grid_size: tuple = (8, 8),
) -> np.ndarray:
    """
    Apply adaptive contrast enhancement using CLAHE.

    Improves readability of faint text and enhances detail without
    over-amplifying noise.

    Args:
        image: Input BGR image.
        clip_limit: Contrast limit for CLAHE. Higher = more contrast.
        tile_grid_size: Size of grid for local contrast enhancement.

    Returns:
        Contrast-enhanced image.
    """
    # Convert to LAB color space
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    # Apply CLAHE to L channel
    clahe = cv2.createCLAHE(
        clipLimit=clip_limit,
        tileGridSize=tile_grid_size
    )
    l_enhanced = clahe.apply(l)

    # Merge and convert back
    enhanced = cv2.merge([l_enhanced, a, b])
    result = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

    return result


def auto_levels(image: np.ndarray, saturation: float = 0.005) -> np.ndarray:
    """
    Automatically adjust image levels (histogram stretching).

    Saturates a small percentage of pixels at the low and high ends
    to maximise contrast.

    Args:
        image: Input BGR image.
        saturation: Fraction of pixels to saturate at each end (0.0-1.0).

    Returns:
        Level-adjusted image.
    """
    result = image.copy()
    for c in range(3):
        channel = image[:, :, c]
        h, w = channel.shape

        # Compute histogram
        hist = cv2.calcHist([channel], [0], None, [256], [0, 256])
        cumulative = np.cumsum(hist)
        total = cumulative[-1]

        # Find low and high thresholds
        low_val = np.searchsorted(cumulative, total * saturation)
        high_val = np.searchsorted(cumulative, total * (1.0 - saturation))

        if high_val <= low_val:
            continue

        # Apply stretch
        channel_stretched = np.clip(
            (channel.astype(np.float32) - low_val) * 255.0 / (high_val - low_val),
            0, 255
        ).astype(np.uint8)

        result[:, :, c] = channel_stretched

    return result
