#!/usr/bin/env python3
"""Image Thumbnail example."""

import sys
import os
from pathlib import Path

# Add the src directory to the path
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from gui_pyqt_widgets import ImageThumbnail


class ThumbnailExample(QMainWindow):
    """Example showing ImageThumbnail functionality."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Image Thumbnail Example')
        self.setFixedSize(400, 350)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Find first image
        sample_dir = current_dir / "sample_images"
        if not sample_dir.exists():
            sample_dir = current_dir / "sample"
        
        supported_formats = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')
        image_path = None
        
        if sample_dir.exists():
            for ext in supported_formats:
                images = list(sample_dir.glob(f"*{ext}"))
                if images:
                    image_path = str(images[0])
                    break
        
        if not image_path:
            layout.addWidget(QPushButton("No images found in sample directory"))
            return
        
        print(f"Using image: {Path(image_path).name}")
        
        # Create thumbnail
        self.thumbnail = ImageThumbnail(
            image_path=image_path,
            index=0,
            size=250,
            show_filename=True
        )
        
        # Connect signals
        self.thumbnail.clicked.connect(self.on_thumbnail_clicked)
        self.thumbnail.double_clicked.connect(self.on_thumbnail_double_clicked)
        self.thumbnail.selection_changed.connect(self.on_selection_changed)
        
        layout.addWidget(self.thumbnail)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        toggle_btn = QPushButton('Toggle Selection')
        toggle_btn.clicked.connect(self.thumbnail.toggle_selection)
        button_layout.addWidget(toggle_btn)
        
        size_btn = QPushButton('Change Size')
        size_btn.clicked.connect(self.change_size)
        button_layout.addWidget(size_btn)
        
        layout.addLayout(button_layout)
        
        self.current_size = 250
    
    def on_thumbnail_clicked(self, index):
        """Handle thumbnail click."""
        print(f"Thumbnail {index} clicked!")
    
    def on_thumbnail_double_clicked(self, index):
        """Handle thumbnail double-click."""
        print(f"Thumbnail {index} double-clicked!")
    
    def on_selection_changed(self, index, is_selected):
        """Handle selection change."""
        print(f"Thumbnail {index} selection: {is_selected}")
    
    def change_size(self):
        """Change thumbnail size."""
        self.current_size = 150 if self.current_size == 250 else 250
        self.thumbnail.set_size(self.current_size)
        print(f"Changed size to: {self.current_size}")


def main():
    """Run Image Thumbnail example."""
    app = QApplication(sys.argv)
    
    example = ThumbnailExample()
    example.show()
    
    print("Image Thumbnail Features:")
    print("- Click to select")
    print("- Double-click for action")
    print("- Toggle selection button")
    print("- Resizable thumbnail")
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
