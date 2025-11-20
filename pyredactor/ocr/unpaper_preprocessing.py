#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko <ezajko@root.ba>

"""
Unpaper Preprocessing Service for PyRedactor Application

Handles document preprocessing using unpaper to improve scan quality.
"""

import subprocess
import tempfile
import os
from PIL import Image
from typing import Optional

class UnpaperPreprocessingService:
    """Service for preprocessing scanned documents using unpaper"""

    def __init__(self):
        self.unpaper_available = self._check_unpaper_availability()

    def _check_unpaper_availability(self) -> bool:
        """Check if unpaper is available on the system"""
        try:
            result = subprocess.run(["unpaper", "--version"],
                                  capture_output=True,
                                  timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def is_available(self) -> bool:
        """Check if unpaper preprocessing is available"""
        return self.unpaper_available

    def preprocess_image(self, image_path: str, output_path: str,
                        paper_format: str = "a4") -> bool:
        """
        Preprocess an image using unpaper

        Args:
            image_path: Path to input image
            output_path: Path to output processed image
            paper_format: Target paper format (a4, letter, etc.)

        Returns:
            bool: True if preprocessing successful, False otherwise
        """
        if not self.unpaper_available:
            return False

        try:
            # Build unpaper command
            cmd = [
                "unpaper",
                "--layout", "single",
                "--paper", paper_format,
                "--no-deskew",  # We can make this configurable
                "--no-border-align",  # We can make this configurable
                image_path,
                output_path
            ]

            # Run unpaper
            result = subprocess.run(cmd,
                                  capture_output=True,
                                  timeout=30)  # 30 second timeout

            return result.returncode == 0

        except subprocess.TimeoutExpired:
            print("Unpaper preprocessing timed out")
            return False
        except Exception as e:
            print(f"Error during unpaper preprocessing: {e}")
            return False

    def preprocess_pil_image(self, image: Image.Image,
                           paper_format: str = "a4") -> Optional[Image.Image]:
        """
        Preprocess a PIL Image using unpaper

        Args:
            image: PIL Image to preprocess
            paper_format: Target paper format (a4, letter, etc.)

        Returns:
            PIL Image: Preprocessed image, or None if failed
        """
        if not self.unpaper_available:
            return None

        try:
            # Create temporary files
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_input:
                input_path = temp_input.name

            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_output:
                output_path = temp_output.name

            try:
                # Save input image
                image.save(input_path, PNG)

                # Process with unpaper
                if self.preprocess_image(input_path, output_path, paper_format):
                    # Load processed image
                    processed_image = Image.open(output_path)
                    return processed_image.copy()
                else:
                    return None

            finally:
                # Clean up temporary files
                if os.path.exists(input_path):
                    os.unlink(input_path)
                if os.path.exists(output_path):
                    os.unlink(output_path)

        except Exception as e:
            print(f"Error preprocessing PIL image with unpaper: {e}")
            return None
