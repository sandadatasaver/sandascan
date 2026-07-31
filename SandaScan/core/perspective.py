"""
Perspective Correction & Page Detection Module

Detects document page boundaries in a photo and applies a perspective
transform to produce a flat, rectangular, front-facing view.

Uses multiple strategies in order of reliability to find the document:
  1. Canny edges + largest quadrilateral contour
  2. Multi-epsilon polygon approximation
  3. Largest convex hull with 4-vertex approximation
  4. Frame-based detection (document on dark/lit background)
"""

import cv2
import numpy as np
from typing import Tuple, Optional


def find_document_contour(
    image: np.ndarray,
) -> Optional[np.ndarray]:
    """
    Find the four corners of a document page in a photo using
    multiple detection strategies.

    Strategies (tried in order):
      1. Canny edge detection + find largest quadrilateral contour
      2. Multiple epsilon polygon approximation values
      3. Largest convex hull fitted to 4 points
      4. Edge detection on borders for high-contrast documents

    Args:
        image: Input BGR image.

    Returns:
        Ordered 4 corner points [top-left, top-right, bottom-right, bottom-left]
        as ndarray of shape (4, 2) dtype float32, or None if not found.
    """
    h, w = image.shape[:2]
    total_area = h * w

    # Pre-process: convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # ── Strategy 1: Canny edges + find 4-point contours ────────────────
    corners = _strategy_canny(blurred, total_area)
    if corners is not None:
        return corners

    # ── Strategy 2: Adaptive threshold + multi-epsilon approximation ────
    corners = _strategy_adaptive_thresh(blurred, total_area)
    if corners is not None:
        return corners

    # ── Strategy 3: OTSU + multi-epsilon ──────────────────────────────
    corners = _strategy_otsu(blurred, total_area)
    if corners is not None:
        return corners

    # ── Strategy 4: Convex hull of largest contour ─────────────────────
    corners = _strategy_convex_hull(blurred, total_area)
    if corners is not None:
        return corners

    # ── Strategy 5: Frame detection (document on contrasting bg) ───────
    corners = _strategy_frame_edge(gray, h, w, total_area)
    if corners is not None:
        return corners

    return None


def _strategy_canny(gray: np.ndarray, total_area: float,
                    min_ratio: float = 0.05) -> Optional[np.ndarray]:
    """Find document using Canny edge detection."""
    # Try multiple Canny threshold pairs
    for low, high in [(30, 90), (50, 150), (20, 60), (80, 200)]:
        edges = cv2.Canny(gray, low, high)

        # Dilate to close gaps in edges
        kernel = np.ones((5, 5), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=2)

        contours, _ = cv2.findContours(
            dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # Sort by area descending
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

        for cnt in contours:
            area = cv2.contourArea(cnt)
            area_ratio = area / total_area

            if area_ratio < min_ratio:
                continue

            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)

            if len(approx) == 4:
                return _order_points(approx.reshape(4, 2).astype(np.float32))

    return None


def _strategy_adaptive_thresh(gray: np.ndarray, total_area: float,
                               min_ratio: float = 0.05) -> Optional[np.ndarray]:
    """Find document using adaptive thresholding."""
    # Try different block sizes
    for block_size in [31, 51, 21, 71]:
        if block_size % 2 == 0:
            block_size += 1

        for c_val in [5, 10, 2, 15]:
            try:
                thresh = cv2.adaptiveThreshold(
                    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY_INV, block_size, c_val
                )

                kernel = np.ones((5, 5), np.uint8)
                closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

                contours, _ = cv2.findContours(
                    closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                )

                contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

                for cnt in contours:
                    area = cv2.contourArea(cnt)
                    area_ratio = area / total_area

                    if area_ratio < min_ratio:
                        continue

                    # Try multiple epsilon values to find 4 corners
                    peri = cv2.arcLength(cnt, True)
                    for eps_factor in [0.02, 0.01, 0.03, 0.05, 0.005, 0.1]:
                        approx = cv2.approxPolyDP(cnt, eps_factor * peri, True)
                        if len(approx) == 4:
                            pts = approx.reshape(4, 2).astype(np.float32)
                            if _is_good_quadrilateral(pts):
                                return _order_points(pts)
            except cv2.error:
                continue

    return None


def _strategy_otsu(gray: np.ndarray, total_area: float,
                    min_ratio: float = 0.05) -> Optional[np.ndarray]:
    """Find document using OTSU threshold."""
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Try both normal and inverted
    for bin_img in [thresh, cv2.bitwise_not(thresh)]:
        kernel = np.ones((5, 5), np.uint8)
        closed = cv2.morphologyEx(bin_img, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(
            closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

        for cnt in contours:
            area = cv2.contourArea(cnt)
            area_ratio = area / total_area
            if area_ratio < min_ratio:
                continue

            peri = cv2.arcLength(cnt, True)
            for eps_factor in [0.02, 0.01, 0.03, 0.05]:
                approx = cv2.approxPolyDP(cnt, eps_factor * peri, True)
                if len(approx) == 4:
                    pts = approx.reshape(4, 2).astype(np.float32)
                    if _is_good_quadrilateral(pts):
                        return _order_points(pts)

    return None


def _strategy_convex_hull(gray: np.ndarray, total_area: float,
                           min_ratio: float = 0.05) -> Optional[np.ndarray]:
    """Find document using convex hull of the largest contour."""
    edges = cv2.Canny(gray, 50, 150)
    kernel = np.ones((7, 7), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=3)

    contours, _ = cv2.findContours(
        dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        return None

    # Merge all large contours into one
    all_pts = np.vstack([cnt for cnt in contours
                         if cv2.contourArea(cnt) > total_area * min_ratio])

    if len(all_pts) < 4:
        return None

    hull = cv2.convexHull(all_pts)

    # Try to approximate the hull to a quadrilateral
    peri = cv2.arcLength(hull, True)
    for eps_factor in [0.02, 0.03, 0.01, 0.05, 0.005]:
        approx = cv2.approxPolyDP(hull, eps_factor * peri, True)
        if len(approx) == 4:
            pts = approx.reshape(4, 2).astype(np.float32)
            if _is_good_quadrilateral(pts):
                return _order_points(pts)

    # If still not 4, try to find the 4 extreme points of the hull
    if len(hull) >= 4:
        pts = hull.reshape(-1, 2)
        top_left = pts[np.argmin(pts.sum(axis=1))]
        bottom_right = pts[np.argmax(pts.sum(axis=1))]
        top_right = pts[np.argmin(np.diff(pts, axis=1))]
        bottom_left = pts[np.argmax(np.diff(pts, axis=1))]
        rect = np.array([top_left, top_right, bottom_right, bottom_left],
                        dtype=np.float32)
        if _is_good_quadrilateral(rect):
            return _order_points(rect)

    return None


def _strategy_frame_edge(gray: np.ndarray, h: int, w: int,
                          total_area: float) -> Optional[np.ndarray]:
    """
    For documents on contrasting backgrounds.
    Detects the document by finding edges near the image center
    using horizontal and vertical line scans.
    """
    # Use Sobel edge detection
    sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)

    # Magnitude
    mag = np.sqrt(sobel_x ** 2 + sobel_y ** 2)
    mag = np.uint8(np.clip(mag, 0, 255))

    # Threshold to get strong edges
    _, edges = cv2.threshold(mag, 50, 255, cv2.THRESH_BINARY)

    # Find lines using Hough
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100,
                            minLineLength=max(h, w) // 4,
                            maxLineGap=50)

    if lines is None or len(lines) < 4:
        return None

    # Find the bounding box of all line intersections
    all_pts = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        all_pts.extend([(x1, y1), (x2, y2)])

    if not all_pts:
        return None

    all_pts = np.array(all_pts, dtype=np.float32)
    rect = cv2.minAreaRect(all_pts)
    box = cv2.boxPoints(rect)

    if _is_good_quadrilateral(box):
        return _order_points(box)

    return None


def _is_good_quadrilateral(pts: np.ndarray) -> bool:
    """Check if 4 points form a reasonable document shape."""
    if len(pts) != 4:
        return False

    # Check that points are not too close together
    for i in range(4):
        for j in range(i + 1, 4):
            dist = np.linalg.norm(pts[i] - pts[j])
            if dist < 10:
                return False

    # Check for reasonable angles (not too extreme)
    def angle(p1, p2, p3):
        v1 = p1 - p2
        v2 = p3 - p2
        dot = np.dot(v1, v2)
        norm = np.linalg.norm(v1) * np.linalg.norm(v2)
        if norm == 0:
            return 0
        cos_angle = dot / norm
        return np.degrees(np.arccos(np.clip(cos_angle, -1, 1)))

    for i in range(4):
        ang = angle(pts[i], pts[(i + 1) % 4], pts[(i + 2) % 4])
        # Angle should be between 30 and 150 degrees
        if ang < 30 or ang > 150:
            return False

    return True


def _order_points(pts: np.ndarray) -> np.ndarray:
    """Order 4 points: top-left, top-right, bottom-right, bottom-left."""
    rect = np.zeros((4, 2), dtype=np.float32)

    # Sum and diff to identify corners
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)

    rect[0] = pts[np.argmin(s)]       # top-left (smallest sum)
    rect[2] = pts[np.argmax(s)]       # bottom-right (largest sum)
    rect[1] = pts[np.argmin(diff)]    # top-right (smallest diff)
    rect[3] = pts[np.argmax(diff)]    # bottom-left (largest diff)

    return rect


def correct_perspective(
    image: np.ndarray,
    output_width: int = 2480,
    output_height: int = 3508,
    auto_detect: bool = True,
) -> np.ndarray:
    """
    Detect document page corners and apply perspective correction
    to produce a flat, rectangular view.

    This crops out everything outside the detected document and
    transforms it to a perfectly rectangular A4-sized page.

    Args:
        image: Input BGR image (photo of a document).
        output_width: Width of output in pixels (default A4 at 300 DPI).
        output_height: Height of output in pixels (default A4 at 300 DPI).
        auto_detect: Whether to auto-detect document boundaries.

    Returns:
        Perspective-corrected, cropped image of the document alone.
    """
    h, w = image.shape[:2]

    if auto_detect:
        corners = find_document_contour(image)
    else:
        corners = None

    if corners is not None:
        dst_pts = np.array([
            [0, 0],
            [output_width - 1, 0],
            [output_width - 1, output_height - 1],
            [0, output_height - 1],
        ], dtype=np.float32)

        matrix = cv2.getPerspectiveTransform(corners, dst_pts)
        corrected = cv2.warpPerspective(
            image, matrix, (output_width, output_height),
            flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT,
            borderValue=(255, 255, 255)
        )
        return corrected

    # Fallback: resize image to A4 while preserving aspect ratio
    # pad with white borders so nothing is stretched or distorted
    return _resize_to_fit(image, output_width, output_height)


def _resize_to_fit(image: np.ndarray, target_w: int, target_h: int) -> np.ndarray:
    """
    Resize an image to fit within target dimensions while preserving aspect ratio,
    padding with white borders. This is a safe fallback when page detection fails.
    """
    h, w = image.shape[:2]
    
    # Calculate scale to fit within target dimensions
    scale = min(target_w / w, target_h / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    
    # Create white canvas and center the image
    canvas = np.ones((target_h, target_w, 3), dtype=np.uint8) * 255
    x_offset = (target_w - new_w) // 2
    y_offset = (target_h - new_h) // 2
    canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
    
    return canvas


def deskew(
    image: np.ndarray,
    max_angle: float = 15.0,
) -> np.ndarray:
    """
    Deskew a document image by detecting text orientation.

    Uses Hough Line Transform to find the dominant angle of text lines.

    Args:
        image: Input image (BGR or grayscale).
        max_angle: Maximum skew angle to correct.

    Returns:
        Deskewed image.
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    if np.mean(gray) < 127:
        gray = cv2.bitwise_not(gray)

    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    edges = cv2.Canny(binary, 50, 150, apertureSize=3)
    lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=150)

    if lines is None:
        return image

    angles = []
    for rho, theta in lines[:, 0]:
        angle = np.degrees(theta) - 90
        if abs(angle) <= max_angle:
            angles.append(angle)

    if not angles:
        return image

    median_angle = np.median(angles)

    if abs(median_angle) < 0.5:
        return image

    h, w = image.shape[:2]
    center = (w // 2, h // 2)

    rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
    deskewed = cv2.warpAffine(
        image, rotation_matrix, (w, h),
        flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255)
    )

    return deskewed
