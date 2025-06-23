#!/usr/bin/env python3
"""Image Viewer example."""

import sys
import os
from pathlib import Path

# Add the src directory to the path
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

from PySide6.QtWidgets import QApplication
from gui_pyqt_widgets import ImageViewer


def main():
    """Run Image Viewer example."""
    app = QApplication(sys.argv)
    
    # Get image files from sample directory
    sample_dir = current_dir / "sample_images"
    if not sample_dir.exists():
        sample_dir = current_dir / "sample"
    
    if not sample_dir.exists():
        print("No sample images directory found.")
        return
    
    # Supported formats
    supported_formats = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')
    
    # Find image files
    image_files = []
    for ext in supported_formats:
        image_files.extend(sample_dir.glob(f"*{ext}"))
        image_files.extend(sample_dir.glob(f"*{ext.upper()}"))
    
    image_files = [str(p) for p in sorted(image_files)]
    
    if not image_files:
        print(f"No images found in {sample_dir}")
        return
    
    print(f"Found {len(image_files)} images")
    
    # Create image viewer
    viewer = ImageViewer(image_files, 0)
    
    # Connect signals
    viewer.image_changed.connect(lambda idx: print(f"Viewing image {idx + 1}/{len(image_files)}"))
    viewer.closed.connect(lambda: print("Viewer closed"))
    
    viewer.show()
    
    print("Image Viewer Controls:")
    print("- H/Left Arrow: Previous image")
    print("- L/Right Arrow: Next image")
    print("- P: Previous image")
    print("- N: Next image")
    print("- Q/Escape: Close viewer")
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
