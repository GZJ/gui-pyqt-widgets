#!/usr/bin/env python3
"""Demo script for the image gallery widgets."""

import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout

# Add the src directory to the path to import our widgets
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from gui_pyqt_widgets import ImageGallery, FolderImageGallery, ImageViewer, ImageThumbnail


class ImageGalleryDemo(QMainWindow):
    """Demo application showing the image gallery widgets."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Image Gallery Widgets Demo')
        self.setGeometry(100, 100, 600, 400)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create demo buttons
        button_layout = QHBoxLayout()
        
        # Image Gallery button
        gallery_btn = QPushButton('Open Image Gallery')
        gallery_btn.clicked.connect(self.show_image_gallery)
        button_layout.addWidget(gallery_btn)
        
        # Folder Gallery button
        folder_btn = QPushButton('Open Folder Gallery')
        folder_btn.clicked.connect(self.show_folder_gallery)
        button_layout.addWidget(folder_btn)
        
        # Image Viewer button
        viewer_btn = QPushButton('Open Image Viewer')
        viewer_btn.clicked.connect(self.show_image_viewer)
        button_layout.addWidget(viewer_btn)
        
        # Thumbnail Demo button
        thumb_btn = QPushButton('Show Thumbnail Demo')
        thumb_btn.clicked.connect(self.show_thumbnail_demo)
        button_layout.addWidget(thumb_btn)
        
        layout.addLayout(button_layout)
        
        # Instructions
        instructions = """
        Image Gallery Widgets Demo
        
        This demo showcases the reusable image gallery components:
        
        1. ImageGallery - Main gallery with thumbnail grid and search
        2. FolderImageGallery - Gallery for browsing folders
        3. ImageViewer - Full-screen image viewer
        4. ImageThumbnail - Individual thumbnail component
        
        Key Features:
        • Vim-style navigation (H/J/K/L keys)
        • Search functionality (/ key)
        • Multi-selection support (M key)
        • Responsive grid layout
        • High-quality image scaling
        
        To test:
        1. Use your existing sample directories with test data
        2. Click the buttons above to test different components
        """
        
        from PySide6.QtWidgets import QTextEdit
        text_widget = QTextEdit()
        text_widget.setPlainText(instructions)
        text_widget.setReadOnly(True)
        layout.addWidget(text_widget)
        
        # Use existing sample directories
        self.test_dir = os.path.join(os.path.dirname(__file__), 'sample_images')
        # Alternative sample directory
        if not os.path.exists(self.test_dir):
            self.test_dir = os.path.join(os.path.dirname(__file__), 'sample')
        
        print(f"Using test directory: {self.test_dir}")
        if os.path.exists(self.test_dir):
            image_count = len([f for f in os.listdir(self.test_dir) 
                             if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))])
            print(f"Found {image_count} images in test directory")
    
    def show_image_gallery(self):
        """Show the image gallery."""
        try:
            self.gallery = ImageGallery(
                image_folder=self.test_dir,
                window_geometry=(200, 100, 800, 600)
            )
            self.gallery.show()
        except Exception as e:
            print(f"Error opening gallery: {e}")
    
    def show_folder_gallery(self):
        """Show the folder gallery."""
        try:
            # Use existing sample_folders directory
            base_dir = os.path.dirname(__file__)
            sample_folders_dir = os.path.join(base_dir, 'sample_folders')
            
            if not os.path.exists(sample_folders_dir):
                print("sample_folders directory not found.")
                return
            
            # Get all subdirectories in sample_folders
            test_folders = []
            for item in os.listdir(sample_folders_dir):
                folder_path = os.path.join(sample_folders_dir, item)
                if os.path.isdir(folder_path):
                    test_folders.append(folder_path)
            
            if not test_folders:
                print("No folders found in sample_folders directory.")
                return
            
            print(f"Using sample folders: {[os.path.basename(f) for f in test_folders]}")
            
            self.folder_gallery = FolderImageGallery(
                folder_paths=test_folders,
                window_geometry=(250, 150, 700, 500)
            )
            self.folder_gallery.show()
        except Exception as e:
            print(f"Error opening folder gallery: {e}")
    
    def show_image_viewer(self):
        """Show the image viewer with test images."""
        try:
            # Get image files from test directory
            supported_formats = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')
            image_files = []
            
            if os.path.exists(self.test_dir):
                for filename in sorted(os.listdir(self.test_dir)):
                    if filename.lower().endswith(supported_formats):
                        image_files.append(os.path.join(self.test_dir, filename))
            
            if not image_files:
                print(f"No images found in {self.test_dir}")
                print("Add some image files to test the viewer")
                return
            
            self.viewer = ImageViewer(image_files, 0, self)
            self.viewer.show()
        except Exception as e:
            print(f"Error opening viewer: {e}")
    
    def show_thumbnail_demo(self):
        """Show individual thumbnail demo."""
        try:
            # Find first image in test directory
            supported_formats = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')
            image_path = None
            
            if os.path.exists(self.test_dir):
                for filename in sorted(os.listdir(self.test_dir)):
                    if filename.lower().endswith(supported_formats):
                        image_path = os.path.join(self.test_dir, filename)
                        break
            
            if not image_path:
                print(f"No images found in {self.test_dir}")
                print("Add some image files to test the thumbnail")
                return
            
            # Create a window to hold the thumbnail
            from PySide6.QtWidgets import QDialog
            dialog = QDialog(self)
            dialog.setWindowTitle('Thumbnail Demo')
            dialog.setFixedSize(300, 300)
            
            layout = QVBoxLayout(dialog)
            
            # Create thumbnail
            thumbnail = ImageThumbnail(image_path, 0, 200, True, dialog)
            thumbnail.clicked.connect(lambda idx: print(f"Thumbnail {idx} clicked!"))
            thumbnail.selection_changed.connect(
                lambda idx, selected: print(f"Thumbnail {idx} selection: {selected}")
            )
            
            layout.addWidget(thumbnail)
            
            # Add selection button
            toggle_btn = QPushButton('Toggle Selection')
            toggle_btn.clicked.connect(thumbnail.toggle_selection)
            layout.addWidget(toggle_btn)
            
            dialog.show()
            self.thumbnail_dialog = dialog  # Keep reference
            
        except Exception as e:
            print(f"Error creating thumbnail demo: {e}")


def main():
    """Run the demo application."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName('Image Gallery Demo')
    app.setApplicationVersion('1.0')
    
    # Create and show demo window
    demo = ImageGalleryDemo()
    demo.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
