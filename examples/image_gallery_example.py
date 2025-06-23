#!/usr/bin/env python3
"""Image Gallery example."""

import sys
import os
from pathlib import Path

# Add the src directory to the path
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

from PySide6.QtWidgets import QApplication
from gui_pyqt_widgets import ImageGallery


def main():
    """Run Image Gallery example."""
    app = QApplication(sys.argv)
    
    # Use sample_images directory
    sample_dir = current_dir / "sample_images"
    if not sample_dir.exists():
        sample_dir = current_dir / "sample"
    
    print(f"Using image directory: {sample_dir}")
    if sample_dir.exists():
        image_count = len(list(sample_dir.glob("*.jpg")) + 
                         list(sample_dir.glob("*.png")) + 
                         list(sample_dir.glob("*.jpeg")))
        print(f"Found {image_count} images")
    
    # Create image gallery
    gallery = ImageGallery(
        image_folder=str(sample_dir),
        window_geometry=(200, 100, 800, 600)
    )
    
    # Connect signals
    gallery.image_selected.connect(lambda path, idx: print(f"Selected: {Path(path).name}"))
    gallery.selection_changed.connect(lambda indices: print(f"Selection count: {len(indices)}"))
    
    gallery.show()
    
    print("Image Gallery Controls:")
    print("- H/J/K/L: Navigate")
    print("- /: Search")
    print("- M: Toggle selection")
    print("- Enter: View image")
    print("- Q: Quit")
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
