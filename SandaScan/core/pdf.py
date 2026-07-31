"""
PDF Generation Module

Converts processed document images to high-quality PDF files
with optional searchable text overlay.
"""

import os
import cv2
import numpy as np
from PIL import Image
from typing import List, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def images_to_pdf(
    images: List[np.ndarray],
    output_path: str,
    dpi: int = 300,
    quality: int = 95,
    page_size: tuple = A4,
) -> str:
    """
    Convert a list of OpenCV images (BGR) into a single multi-page PDF.

    Args:
        images: List of image arrays (BGR format from OpenCV).
        output_path: Path to save the PDF file.
        dpi: Output DPI for the PDF images.
        quality: JPEG quality for embedded images (1-100).
        page_size: Tuple of (width, height) in points (default A4).

    Returns:
        Path to the created PDF file.
    """
    pdf_images = []
    for img in images:
        # Convert BGR (OpenCV) to RGB (Pillow)
        rgb_img = cv2_bgr_to_pil(img)
        pdf_images.append(rgb_img)

    # Save first image and append the rest
    if pdf_images:
        first = pdf_images[0]
        rest = pdf_images[1:] if len(pdf_images) > 1 else None

        first.save(
            output_path,
            "PDF",
            save_all=True,
            append_images=rest,
            resolution=dpi,
            quality=quality,
        )

    return output_path


def cv2_bgr_to_pil(img: np.ndarray) -> Image.Image:
    """Convert OpenCV BGR image to PIL RGB image."""
    if img.shape[2] == 3:
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    else:
        rgb = img
    return Image.fromarray(rgb)


def cv2_bgr_to_bytes(img: np.ndarray, format: str = "PNG") -> bytes:
    """Convert OpenCV BGR image to bytes."""
    rgb = cv2_bgr_to_pil(img)
    import io
    buf = io.BytesIO()
    rgb.save(buf, format=format)
    return buf.getvalue()


def images_to_searchable_pdf(
    images: List[np.ndarray],
    text_pages: List[str],
    output_path: str,
    dpi: int = 300,
) -> str:
    """
    Create a searchable PDF with text layer overlay using ReportLab.

    The text layer is transparent and sits on top of the scanned image.
    This produces a true searchable PDF (not just image-only).

    Args:
        images: List of image arrays (BGR format).
        text_pages: List of OCR text strings, one per image.
        output_path: Output PDF file path.
        dpi: Output DPI.

    Returns:
        Path to the created PDF file.
    """
    from reportlab.lib.utils import ImageReader
    import io

    a4_w, a4_h = A4  # points (595.27, 841.89)

    c = canvas.Canvas(output_path, pagesize=A4)

    for i, (img, text) in enumerate(zip(images, text_pages)):
        # Convert image to PNG bytes
        pil_img = cv2_bgr_to_pil(img)

        # Resize image to fit A4 at given DPI
        target_w = int(a4_w)
        target_h = int(a4_h)
        pil_img_resized = pil_img.resize((target_w, target_h), Image.LANCZOS)

        # Save to bytes for embedding
        img_buffer = io.BytesIO()
        pil_img_resized.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        # Draw image as background
        c.drawImage(
            ImageReader(img_buffer),
            0, 0,
            width=a4_w,
            height=a4_h,
            preserveAspectRatio=False,
        )

        # Draw invisible text layer for searchability
        if text.strip():
            c.setFont("Helvetica", 1)  # tiny font for invisible text
            c.setFillColorRGB(0, 0, 0, 0.0)  # fully transparent
            c.setStrokeColorRGB(0, 0, 0, 0.0)

            # Draw text character by character... actually just draw a block
            # of invisible text so search engines can index it
            c.setFont("Helvetica", 8)
            c.setFillColorRGB(1, 1, 1, 0.001)  # nearly invisible

            # Draw text in a narrow column
            text_object = c.beginText(10, a4_h - 20)
            text_object.setCharSpace(0.5)

            # Split text into lines
            words = text.split()
            line = ""
            for word in words:
                test_line = f"{line} {word}".strip()
                if c.stringWidth(test_line, "Helvetica", 8) < a4_w - 20:
                    line = test_line
                else:
                    text_object.textLine(line)
                    line = word
            if line:
                text_object.textLine(line)

            c.drawText(text_object)

        c.showPage()

    c.save()
    return output_path
