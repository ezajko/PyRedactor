#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko <ezajko@root.ba>

"""
OCR Language Selection Dialog
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                               QCheckBox, QPushButton, QLabel, QScrollArea, QWidget)
from PySide6.QtCore import Qt

class OCRLanguageDialog(QDialog):
    def __init__(self, parent=None, available_languages=None, selected_languages=None):
        super().__init__(parent)
        self.setWindowTitle("Select OCR Languages")
        self.resize(300, 400)
        
        self.available_languages = available_languages or []
        self.selected_languages = set(selected_languages or [])
        self.checkboxes = {}
        
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Instructions
        layout.addWidget(QLabel("Select languages for text recognition:"))
        
        # Scroll area for languages
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        for lang in sorted(self.available_languages):
            cb = QCheckBox(lang)
            if lang in self.selected_languages:
                cb.setChecked(True)
            self.checkboxes[lang] = cb
            scroll_layout.addWidget(cb)
            
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # Buttons
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)
        
    def get_selected_languages(self):
        selected = []
        for lang, cb in self.checkboxes.items():
            if cb.isChecked():
                selected.append(lang)
        return selected
