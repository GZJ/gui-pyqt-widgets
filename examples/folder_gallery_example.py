#!/usr/bin/env python3
"""Folder Image Gallery example."""

import sys
import os
from pathlib import Path

# Add the src directory to the path
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

from PySide6.QtWidgets import QApplication
from gui_pyqt_widgets import FolderImageGallery


def main():
    """Run Folder Image Gallery example."""
    app = QApplication(sys.argv)
    
    # Use sample_folders directory
    sample_folders_dir = current_dir / "sample_folders"
    
    if not sample_folders_dir.exists():
        print("sample_folders directory not found.")
        return
    
    # Get all subdirectories
    folder_paths = [str(p) for p in sample_folders_dir.iterdir() if p.is_dir()]
    
    if not folder_paths:
        print("No folders found in sample_folders directory.")
        return
    
    print(f"Using sample folders: {[Path(p).name for p in folder_paths]}")
    
    # Create folder gallery
    folder_gallery = FolderImageGallery(
        folder_paths=folder_paths,
        window_geometry=(250, 150, 700, 500)
    )
    
    # Connect signals
    folder_gallery.folder_selected.connect(lambda path: print(f"Selected folder: {Path(path).name}"))
    folder_gallery.folder_opened.connect(lambda path: print(f"Opened folder: {Path(path).name}"))
    
    folder_gallery.show()
    
    print("Folder Gallery Controls:")
    print("- H/J/K/L: Navigate")
    print("- /: Search folders")
    print("- Enter: Open folder with Image Viewer")
    print("- Double-click: Open folder with Image Viewer")
    print("- Q: Quit")
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
