#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko <ezajko@root.ba>

"""
Image Enhancement Service for PyRedactor Application

Provides built-in image enhancement options for preprocessing input files.
"""

from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import cv2
from typing import Optional

class ImageEnhancementService:
    """Service for enhancing image quality of input documents"""
    
    def __init__(self):
        pass
    
    def enhance_brightness_contrast(self, image: Image.Image, 
                                  brightness: float = 1.0, 
                                  contrast: float = 1.0) -> Image.Image:
        """
        Enhance brightness and contrast of an image
        
        Args:
            image: PIL Image to enhance
            brightness: Brightness factor (1.0 = unchanged)
            contrast: Contrast factor (1.0 = unchanged)
            
        Returns:
            Enhanced PIL Image
        """
        # Adjust brightness
        enhancer = ImageEnhance.Brightness(image)
        bright_image = enhancer.enhance(brightness)
        
        # Adjust contrast
        enhancer = ImageEnhance.Contrast(bright_image)
        contrast_image = enhancer.enhance(contrast)
        
        return contrast_image
    
    def enhance_sharpness(self, image: Image.Image, 
                         sharpness: float = 1.0) -> Image.Image:
        """
        Enhance sharpness of an image
        
        Args:
            image: PIL Image to enhance
            sharpness: Sharpness factor (1.0 = unchanged)
            
        Returns:
            Sharpened PIL Image
        """
        enhancer = ImageEnhance.Sharpness(image)
        return enhancer.enhance(sharpness)
    
    def reduce_noise(self, image: Image.Image) -> Image.Image:
        """
        Reduce noise in an image using PIL median filter
        
        Args:
            image: PIL Image to denoise
            
        Returns:
            Denoised PIL Image
        """
        # Convert to grayscale if needed for noise reduction
        if image.mode != "L":
            gray_image = image.convert("L")
        else:
            gray_image = image
            
        # Apply median filter for noise reduction
        denoised = gray_image.filter(ImageFilter.MedianFilter(size=3))
        
        # Convert back to original mode if needed
        if image.mode != "L":
            denoised = denoised.convert(image.mode)
            
        return denoised
    
    def auto_level(self, image: Image.Image) -> Image.Image:
        """
        Automatically adjust levels to improve contrast
        
        Args:
            image: PIL Image to auto-level
            
        Returns:
            Auto-leveled PIL Image
        """
        # Convert to numpy array for processing
        img_array = np.array(image)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        if len(img_array.shape) == 3:  # Color image
            # Convert to LAB color space
            lab = cv2.cvtColor(img_array, cv2.COLOR_RGB2LAB)
            l_channel, a_channel, b_channel = cv2.split(lab)
            
            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            l_clahe = clahe.apply(l_channel)
            
            # Merge channels and convert back to RGB
            lab_clahe = cv2.merge((l_clahe, a_channel, b_channel))
            enhanced_array = cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2RGB)
        else:  # Grayscale image
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced_array = clahe.apply(img_array)
        
        # Convert back to PIL Image
        enhanced_image = Image.fromarray(enhanced_array)
        return enhanced_image
    
    def deskew(self, image: Image.Image) -> Image.Image:
        """
        Automatically correct skewed images using optimized PCA
        
        Args:
            image: PIL Image to deskew
            
        Returns:
            Deskewed PIL Image
        """
        # Convert to grayscale
        gray = image.convert("L")
        img_array = np.array(gray)
        
        # Optimization: Resize for angle calculation if image is large
        # This significantly speeds up PCA without losing much precision
        h, w = img_array.shape
        scale = 1.0
        max_dim = 800  # Max dimension for analysis
        
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            new_size = (int(w * scale), int(h * scale))
            # Use cv2 for faster resizing
            img_small = cv2.resize(img_array, new_size, interpolation=cv2.INTER_AREA)
        else:
            img_small = img_array

        # Threshold the image
        # Use THRESH_BINARY_INV so text becomes white (foreground) and background black
        # This is crucial because we want to analyze the text structure
        _, thresh = cv2.threshold(img_small, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Find coordinates of all non-zero pixels (foreground text)
        coords = np.column_stack(np.where(thresh > 0))
        
        # Calculate angle of rotation using PCA
        if len(coords) > 100: # Need enough points for reliable statistics
            # Center the coordinates
            mean_coords = np.mean(coords, axis=0)
            centered_coords = coords - mean_coords
            
            # Calculate covariance matrix and eigenvectors
            cov_matrix = np.cov(centered_coords.T)
            eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)
            
            # Determine dominant angle
            # eigenvector[0] corresponds to x, eigenvector[1] to y
            # Note: numpy indices are (row, col) -> (y, x)
            angle = np.arctan2(eigenvectors[0, 1], eigenvectors[0, 0]) * 180 / np.pi
            
            # Handle 90 degree ambiguity if needed, but for deskew usually angle is small
            # If the text is horizontal, the largest eigenvector should be roughly horizontal
            
            # Correct angle range to be between -45 and 45
            if angle < -45:
                angle += 90
            elif angle > 45:
                angle -= 90

            # Rotate image to correct skew
            # Only rotate if skew is significant (> 0.5 degree) but not too extreme (> 10 degrees usually means wrong detection)
            if 0.5 < abs(angle) < 20:
                # print(f"[DEBUG] Deskewing by {angle:.2f} degrees")
                rotated = image.rotate(angle, expand=True, fillcolor="white")
                return rotated
        
        # Return original image if no significant skew detected
        return image
    
    def preprocess_document(self, image: Image.Image, 
                          brightness: float = 1.0,
                          contrast: float = 1.0,
                          sharpness: float = 1.0,
                          auto_level: bool = True,
                          deskew: bool = True,
                          denoise: bool = True) -> Image.Image:
        """
        Apply comprehensive preprocessing to a document image
        
        Args:
            image: PIL Image to preprocess
            brightness: Brightness factor (1.0 = unchanged)
            contrast: Contrast factor (1.0 = unchanged)
            sharpness: Sharpness factor (1.0 = unchanged)
            auto_level: Whether to apply auto-leveling
            deskew: Whether to apply deskewing
            denoise: Whether to apply noise reduction
            
        Returns:
            Preprocessed PIL Image
        """
        processed = image.copy()
        
        # Apply brightness and contrast
        if brightness != 1.0 or contrast != 1.0:
            processed = self.enhance_brightness_contrast(processed, brightness, contrast)
        
        # Apply auto-leveling
        if auto_level:
            processed = self.auto_level(processed)
        
        # Apply deskewing
        if deskew:
            processed = self.deskew(processed)
        
        # Apply noise reduction
        if denoise:
            processed = self.reduce_noise(processed)
        
        # Apply sharpness
        if sharpness != 1.0:
            processed = self.enhance_sharpness(processed, sharpness)
        
        return processed
