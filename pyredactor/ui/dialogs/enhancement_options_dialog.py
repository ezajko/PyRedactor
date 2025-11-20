#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko <ezajko@root.ba>

"""
Enhancement Options Dialog for PyRedactor Application

Dialog for configuring image enhancement options.
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QCheckBox, QSlider, QLabel, QPushButton, 
                               QDoubleSpinBox, QGroupBox)
from PySide6.QtCore import Qt

class EnhancementOptionsDialog(QDialog):
    """Dialog for configuring image enhancement options"""
    
    def __init__(self, parent=None, 
                 enhancement_enabled=False,
                 brightness=1.0,
                 contrast=1.0,
                 sharpness=1.0,
                 auto_level=True,
                 deskew=True,
                 denoise=True):
        super().__init__(parent)
        self.setWindowTitle("Image Enhancement Options")
        self.setModal(True)
        self.resize(400, 300)
        
        # Store current values
        self.enhancement_enabled = enhancement_enabled
        self.brightness = brightness
        self.contrast = contrast
        self.sharpness = sharpness
        self.auto_level = auto_level
        self.deskew = deskew
        self.denoise = denoise
        
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Enable enhancement checkbox
        self.enable_checkbox = QCheckBox("Enable Image Enhancement")
        self.enable_checkbox.setChecked(self.enhancement_enabled)
        layout.addWidget(self.enable_checkbox)
        
        # Enhancement options group
        self.options_group = QGroupBox("Enhancement Options")
        self.options_group.setEnabled(self.enhancement_enabled)
        options_layout = QFormLayout(self.options_group)
        
        # Brightness
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(0, 200)  # 0.0 to 2.0
        self.brightness_slider.setValue(int(self.brightness * 100))
        self.brightness_label = QLabel(f"{self.brightness:.2f}")
        
        brightness_layout = QHBoxLayout()
        brightness_layout.addWidget(self.brightness_slider)
        brightness_layout.addWidget(self.brightness_label)
        options_layout.addRow("Brightness:", brightness_layout)
        
        # Contrast
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(0, 200)  # 0.0 to 2.0
        self.contrast_slider.setValue(int(self.contrast * 100))
        self.contrast_label = QLabel(f"{self.contrast:.2f}")
        
        contrast_layout = QHBoxLayout()
        contrast_layout.addWidget(self.contrast_slider)
        contrast_layout.addWidget(self.contrast_label)
        options_layout.addRow("Contrast:", contrast_layout)
        
        # Sharpness
        self.sharpness_slider = QSlider(Qt.Horizontal)
        self.sharpness_slider.setRange(0, 200)  # 0.0 to 2.0
        self.sharpness_slider.setValue(int(self.sharpness * 100))
        self.sharpness_label = QLabel(f"{self.sharpness:.2f}")
        
        sharpness_layout = QHBoxLayout()
        sharpness_layout.addWidget(self.sharpness_slider)
        sharpness_layout.addWidget(self.sharpness_label)
        options_layout.addRow("Sharpness:", sharpness_layout)
        
        # Enhancement checkboxes
        self.auto_level_checkbox = QCheckBox("Auto-Level (CLAHE)")
        self.auto_level_checkbox.setChecked(self.auto_level)
        options_layout.addRow("", self.auto_level_checkbox)
        
        self.deskew_checkbox = QCheckBox("Deskew")
        self.deskew_checkbox.setChecked(self.deskew)
        options_layout.addRow("", self.deskew_checkbox)
        
        self.denoise_checkbox = QCheckBox("Noise Reduction")
        self.denoise_checkbox.setChecked(self.denoise)
        options_layout.addRow("", self.denoise_checkbox)
        
        layout.addWidget(self.options_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        self.reset_button = QPushButton("Reset")
        
        button_layout.addStretch()
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        layout.addLayout(button_layout)
        
        # Set OK button as default
        self.ok_button.setDefault(True)
        
    def _connect_signals(self):
        """Connect signals to slots"""
        self.enable_checkbox.stateChanged.connect(self._on_enable_changed)
        self.brightness_slider.valueChanged.connect(self._on_brightness_changed)
        self.contrast_slider.valueChanged.connect(self._on_contrast_changed)
        self.sharpness_slider.valueChanged.connect(self._on_sharpness_changed)
        self.reset_button.clicked.connect(self._on_reset_clicked)
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
    def _on_enable_changed(self, state):
        """Handle enable checkbox state change"""
        enabled = state == Qt.Checked
        self.options_group.setEnabled(enabled)
        
    def _on_brightness_changed(self, value):
        """Handle brightness slider change"""
        brightness = value / 100.0
        self.brightness_label.setText(f"{brightness:.2f}")
        
    def _on_contrast_changed(self, value):
        """Handle contrast slider change"""
        contrast = value / 100.0
        self.contrast_label.setText(f"{contrast:.2f}")
        
    def _on_sharpness_changed(self, value):
        """Handle sharpness slider change"""
        sharpness = value / 100.0
        self.sharpness_label.setText(f"{sharpness:.2f}")
        
    def _on_reset_clicked(self):
        """Handle reset button click"""
        self.enable_checkbox.setChecked(False)
        self.brightness_slider.setValue(100)  # 1.0
        self.contrast_slider.setValue(100)    # 1.0
        self.sharpness_slider.setValue(100)    # 1.0
        self.auto_level_checkbox.setChecked(True)
        self.deskew_checkbox.setChecked(True)
        self.denoise_checkbox.setChecked(True)
        
    def get_values(self):
        """Get the current enhancement values"""
        return {
            "enhancement_enabled": self.enable_checkbox.isChecked(),
            "brightness": self.brightness_slider.value() / 100.0,
            "contrast": self.contrast_slider.value() / 100.0,
            "sharpness": self.sharpness_slider.value() / 100.0,
            "auto_level": self.auto_level_checkbox.isChecked(),
            "deskew": self.deskew_checkbox.isChecked(),
            "denoise": self.denoise_checkbox.isChecked()
        }

