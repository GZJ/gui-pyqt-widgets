#!/usr/bin/env python3
"""Main example launcher for GUI PyQt Widgets."""

import sys
import subprocess
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, 
    QPushButton, QLabel, QTextEdit, QHBoxLayout
)


class ExampleLauncher(QMainWindow):
    """Main launcher for all widget examples."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle('GUI PyQt Widgets - Examples')
        self.setGeometry(100, 100, 700, 500)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel('GUI PyQt Widgets Examples')
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                margin: 20px 0;
                text-align: center;
            }
        """)
        layout.addWidget(title)
        
        # Example buttons
        buttons_layout = QVBoxLayout()
        
        # VimTable example
        vim_btn = QPushButton('📊 VimTable - Vim-style table editor')
        vim_btn.setStyleSheet(self._get_button_style())
        vim_btn.clicked.connect(lambda: self.run_example('vim_table_demo.py'))
        buttons_layout.addWidget(vim_btn)
        
        # Image Gallery example
        gallery_btn = QPushButton('🖼️ Image Gallery - Browse images with thumbnails')
        gallery_btn.setStyleSheet(self._get_button_style())
        gallery_btn.clicked.connect(lambda: self.run_example('image_gallery_example.py'))
        buttons_layout.addWidget(gallery_btn)
        
        # Folder Gallery example
        folder_btn = QPushButton('📁 Folder Gallery - Browse folders with previews')
        folder_btn.setStyleSheet(self._get_button_style())
        folder_btn.clicked.connect(lambda: self.run_example('folder_gallery_example.py'))
        buttons_layout.addWidget(folder_btn)
        
        # Image Viewer example
        viewer_btn = QPushButton('🔍 Image Viewer - Full-screen image viewer')
        viewer_btn.setStyleSheet(self._get_button_style())
        viewer_btn.clicked.connect(lambda: self.run_example('image_viewer_example.py'))
        buttons_layout.addWidget(viewer_btn)
        
        # Image Thumbnail example
        thumb_btn = QPushButton('🏷️ Image Thumbnail - Individual thumbnail widget')
        thumb_btn.setStyleSheet(self._get_button_style())
        thumb_btn.clicked.connect(lambda: self.run_example('image_thumbnail_example.py'))
        buttons_layout.addWidget(thumb_btn)
        
        layout.addLayout(buttons_layout)
        
        # Information text
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(200)
        info_text.setPlainText("""
GUI PyQt Widgets Collection

This collection provides reusable PySide6 components designed with high cohesion 
and low coupling principles:

• VimTable: Advanced table with vim-style navigation and editing
• ImageGallery: Grid-based image browser with search and navigation
• FolderImageGallery: Folder browser with image previews
• ImageViewer: Full-screen image viewer with keyboard controls
• ImageThumbnail: Configurable image thumbnail component

Key Features:
- Vim-style keyboard navigation (H/J/K/L)
- Search functionality
- Multi-selection support
- Responsive layouts
- Signal-based event system
- Customizable styling

Click the buttons above to run individual examples.
        """)
        info_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
                color: #495057;
            }
        """)
        layout.addWidget(info_text)
        
        # Status and controls
        controls_layout = QHBoxLayout()
        
        # Status label
        self.status_label = QLabel('Ready to run examples')
        self.status_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 12px;
                padding: 5px;
            }
        """)
        controls_layout.addWidget(self.status_label)
        
        controls_layout.addStretch()
        
        # Exit button
        exit_btn = QPushButton('Exit')
        exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        exit_btn.clicked.connect(self.close)
        controls_layout.addWidget(exit_btn)
        
        layout.addLayout(controls_layout)
    
    def _get_button_style(self):
        """Get consistent button styling."""
        return """
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                text-align: left;
                margin: 3px 0;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """
    
    def run_example(self, script_name):
        """Run an example script."""
        try:
            script_path = Path(__file__).parent / script_name
            if not script_path.exists():
                self.status_label.setText(f"❌ Script not found: {script_name}")
                return
            
            self.status_label.setText(f"🚀 Running: {script_name}")
            
            # Run the script in a new process
            subprocess.Popen([sys.executable, str(script_path)], 
                           cwd=str(script_path.parent))
            
            self.status_label.setText(f"✅ Started: {script_name}")
            
        except Exception as e:
            self.status_label.setText(f"❌ Error running {script_name}: {str(e)}")


def main():
    """Run the example launcher."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName('GUI PyQt Widgets Examples')
    app.setApplicationVersion('1.0')
    
    # Create and show launcher
    launcher = ExampleLauncher()
    launcher.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
