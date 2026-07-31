"""
Batch Processing Module

Orchestrates batch processing of document images with
progress tracking, error handling, and multi-threading support.
"""

import os
import cv2
import numpy as np
from typing import Callable, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from .pipeline import restore_document, PipelineConfig, PipelineStep


@dataclass
class BatchResult:
    """Result of a batch processing operation."""
    total: int = 0
    succeeded: int = 0
    failed: int = 0
    output_path: str = ""
    errors: List[str] = field(default_factory=list)


class BatchProcessor:
    """
    Processes multiple document images in batch.

    Supports multi-threaded processing, progress reporting,
    and error handling per file.
    """

    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        max_workers: int = 2,
    ):
        """
        Initialize the batch processor.

        Args:
            config: Pipeline configuration.
            max_workers: Maximum number of parallel workers.
        """
        self.config = config or PipelineConfig()
        self.max_workers = max_workers
        self._progress_callback = None

    def set_progress_callback(
        self, callback: Optional[Callable[[str, float, int, int], None]]
    ):
        """
        Set a progress callback.

        Callback signature: (step_name, percentage, current_file, total_files)
        """
        self._progress_callback = callback

    def process_folder(
        self,
        input_folder: str,
        output_path: str,
        image_extensions: tuple = (".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".tif"),
    ) -> BatchResult:
        """
        Process all images in a folder.

        Args:
            input_folder: Path to folder containing document images.
            output_path: Path to save the output PDF.
            image_extensions: Tuple of valid image file extensions.

        Returns:
            BatchResult with processing statistics.
        """
        # Collect image files
        image_files = sorted([
            os.path.join(input_folder, f)
            for f in os.listdir(input_folder)
            if f.lower().endswith(image_extensions)
        ])

        if not image_files:
            raise ValueError(
                f"No images found in {input_folder} "
                f"(extensions: {image_extensions})"
            )

        return self.process_files(image_files, output_path)

    def process_files(
        self,
        file_paths: List[str],
        output_path: str,
    ) -> BatchResult:
        """
        Process a list of image files.

        Args:
            file_paths: List of paths to image files.
            output_path: Path to save the output PDF.

        Returns:
            BatchResult with processing statistics.
        """
        result = BatchResult(total=len(file_paths), output_path=output_path)

        # Load images
        images = []
        valid_paths = []

        for i, fpath in enumerate(file_paths):
            try:
                img = cv2.imread(fpath)
                if img is None:
                    raise ValueError(f"Cannot read image: {fpath}")
                images.append(img)
                valid_paths.append(fpath)
                result.succeeded += 1
            except Exception as e:
                result.failed += 1
                result.errors.append(f"{fpath}: {str(e)}")

        if not images:
            return result

        # Update config for progress tracking
        self.config.progress_callback = self._make_step_callback(len(images))

        # Process through pipeline
        from .pipeline import restore_batch
        try:
            final_path = restore_batch(
                images, output_path, self.config,
                filenames=[os.path.basename(p) for p in valid_paths],
            )
            result.output_path = final_path
        except Exception as e:
            result.errors.append(f"Pipeline error: {str(e)}")
            result.failed += len(images)
            result.succeeded -= len(images)

        return result

    def _make_step_callback(self, total_files: int):
        """Create a wrapped progress callback that includes file counts."""
        config_cb = self._progress_callback

        def callback(step: PipelineStep, pct: float):
            if config_cb:
                current_file = int(pct * total_files)
                config_cb(step.value, pct, current_file, total_files)

        return callback
