"""Folder image gallery widget for PySide6."""

import os
import math
from typing import List, Optional
from PySide6.QtWidgets import QLabel, QApplication
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QKeyEvent

from .image_gallery import ImageGallery
from .image_thumbnail import ImageThumbnail


class FolderImageGallery(ImageGallery):
    """A specialized image gallery for displaying folder previews.
    
    This gallery shows folders as thumbnails, using folder.jpg files as previews
    when available, or default folder icons otherwise. Clicking on a folder
    thumbnail opens a regular ImageGallery for that folder.
    
    Features:
    - Displays folders as thumbnails
    - Uses folder.jpg as preview image when available
    - Falls back to default folder icon
    - Opens folder content in new gallery on click
    - Inherits all ImageGallery navigation and search features
    
    Signals:
        folder_selected(str): Emitted when folder is selected (folder path)
        folder_opened(str): Emitted when folder is opened (folder path)
    """
    
    folder_selected = Signal(str)
    folder_opened = Signal(str)
    
    def __init__(
        self,
        folder_paths: List[str],
        parent_gallery: Optional['ImageGallery'] = None,
        thumbnail_size: int = 240,
        window_geometry: tuple = (150, 150, 800, 500),
        parent=None
    ):
        """Initialize the FolderImageGallery.
        
        Args:
            folder_paths: List of folder paths to display
            parent_gallery: Reference to parent gallery (for navigation back)
            thumbnail_size: Size of thumbnails in pixels
            window_geometry: (x, y, width, height) for initial window
            parent: Parent widget
        """
        self.folder_paths = folder_paths
        self.parent_gallery = parent_gallery
        
        # Initialize with a temporary valid folder to avoid loading images initially
        import tempfile
        temp_dir = tempfile.mkdtemp()
        
        super().__init__(
            image_folder=temp_dir,  # Use temp directory instead of empty string
            thumbnail_size=thumbnail_size,
            window_geometry=window_geometry,
            parent=parent
        )
        
        self.setWindowTitle('Folder Preview')
        
        # Override the image loading and clean up temp directory
        self._load_folder_thumbnails()
        
        # Clean up the temporary directory
        import shutil
        try:
            shutil.rmtree(temp_dir)
        except:
            pass  # Ignore cleanup errors
        
        # Adjust window size after loading
        QTimer.singleShot(100, self._adjust_window_size)
    
    def _load_folder_thumbnails(self):
        """Load folder thumbnails instead of image thumbnails."""
        # Clear any existing data
        self.image_paths.clear()
        self.thumbnails.clear()
        self._clear_grid_layout()
        
        # Process each folder path
        for i, folder_path in enumerate(self.folder_paths):
            if not os.path.isdir(folder_path):
                continue
                
            # Look for folder preview image
            preview_path = self._get_folder_preview_path(folder_path)
            
            # Create thumbnail with folder preview
            thumbnail = ImageThumbnail(preview_path, i, self.thumbnail_size, True, self)
            
            # Set display name to folder name
            folder_name = os.path.basename(folder_path)
            thumbnail.set_filename_text(folder_name)
            
            # Store the actual folder path using setProperty
            thumbnail.setProperty("folder_path", folder_path)
            
            # Connect signals
            thumbnail.clicked.connect(self._on_folder_clicked)
            thumbnail.double_clicked.connect(self._on_folder_double_clicked)
            
            self.thumbnails.append(thumbnail)
            self.image_paths.append(preview_path)  # For compatibility
        
        # Update visible thumbnails
        if self.thumbnails:
            self.visible_thumbnails = self.thumbnails.copy()
            self.current_focus = 0
        else:
            self._show_no_folders_message()
    
    def _get_folder_preview_path(self, folder_path: str) -> str:
        """Get preview image path for a folder.
        
        Args:
            folder_path: Path to the folder
            
        Returns:
            Path to preview image (folder.jpg or default icon)
        """
        folder_jpg_path = os.path.join(folder_path, 'folder.jpg')
        
        if os.path.exists(folder_jpg_path):
            return folder_jpg_path
        
        # Try other common preview image names
        for preview_name in ['preview.jpg', 'preview.png', 'thumbnail.jpg', 'thumbnail.png']:
            preview_path = os.path.join(folder_path, preview_name)
            if os.path.exists(preview_path):
                return preview_path
        
        # If no preview image found, try to find the first image in the folder
        try:
            supported_formats = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')
            for filename in sorted(os.listdir(folder_path)):
                if filename.lower().endswith(supported_formats):
                    return os.path.join(folder_path, filename)
        except (OSError, PermissionError):
            pass
        
        # Return a placeholder path for default folder icon
        return self._get_default_folder_icon_path()
    
    def _get_default_folder_icon_path(self) -> str:
        """Get path to default folder icon.
        
        Returns:
            Path to default folder icon (creates a simple one if needed)
        """
        # Return a special marker that ImageThumbnail can handle
        return "__FOLDER_ICON__"
    
    def _show_no_folders_message(self):
        """Show a message when no folders are found."""
        label = QLabel("No folders found")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 16px;
                padding: 40px;
            }
        """)
        self.grid.addWidget(label, 0, 0)
    
    def _adjust_window_size(self):
        """Adjust window size to fit content optimally."""
        if not self.thumbnails:
            return
        
        # Get screen dimensions
        screen = QApplication.primaryScreen().availableGeometry()
        screen_width = screen.width()
        screen_height = screen.height()
        
        # Calculate required space
        num_items = len(self.thumbnails)
        thumb_width = self.thumbnail_size + self.min_spacing
        thumb_height = self.thumbnail_size + 50  # Extra space for labels
        
        # Calculate optimal layout
        max_screen_width = int(screen_width * 0.8)
        ideal_cols = min(max(1, max_screen_width // thumb_width), num_items)
        rows = math.ceil(num_items / ideal_cols)
        
        # Calculate window size
        window_width = min((ideal_cols * thumb_width) + 40, max_screen_width)
        window_height = min((rows * thumb_height) + 100, int(screen_height * 0.8))
        
        # Resize and center window
        self.resize(window_width, window_height)
        
        # Center on screen
        center_point = screen.center()
        geometry = self.frameGeometry()
        geometry.moveCenter(center_point)
        self.move(geometry.topLeft())
    
    def _on_folder_clicked(self, index: int):
        """Handle folder thumbnail click."""
        if 0 <= index < len(self.thumbnails):
            folder_path = self.thumbnails[index].property("folder_path") or ''
            if folder_path:
                self.folder_selected.emit(folder_path)
    
    def _on_folder_double_clicked(self, index: int):
        """Handle folder thumbnail double-click - open folder with image viewer."""
        if 0 <= index < len(self.thumbnails):
            folder_path = self.thumbnails[index].property("folder_path") or ''
            if folder_path:
                self._open_folder_with_viewer(folder_path)
    
    def _open_folder_with_viewer(self, folder_path: str):
        """Open a folder's images with ImageViewer.
        
        Args:
            folder_path: Path to folder to open
        """
        try:
            # Get all image files from the folder
            supported_formats = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')
            image_files = []
            
            for filename in sorted(os.listdir(folder_path)):
                if filename.lower().endswith(supported_formats):
                    full_path = os.path.join(folder_path, filename)
                    image_files.append(full_path)
            
            if not image_files:
                print(f"No images found in folder: {os.path.basename(folder_path)}")
                return
            
            # Import ImageViewer here to avoid circular imports
            from .image_viewer import ImageViewer
            
            # Create and show ImageViewer
            viewer = ImageViewer(image_files, 0, self)
            viewer.setWindowTitle(f'Images in {os.path.basename(folder_path)}')
            viewer.show()
            
            self.folder_opened.emit(folder_path)
            
        except Exception as e:
            print(f"Error opening folder with viewer: {e}")
    
    def _open_folder_gallery(self, folder_path: str):
        """Open a new ImageGallery for the selected folder (alternative method).
        
        Args:
            folder_path: Path to folder to open
        """
        try:
            # Create new ImageGallery for this folder
            folder_gallery = ImageGallery(
                image_folder=folder_path,
                window_geometry=(200, 200, 900, 600),
                parent=self
            )
            folder_gallery.show()
            self.folder_opened.emit(folder_path)
            
        except Exception as e:
            print(f"Error opening folder gallery: {e}")
    
    def _filter_thumbnails(self, search_text: Optional[str] = None):
        """Filter thumbnails based on folder names."""
        if search_text is None:
            search_text = self.search_input.text()
        
        search_text = search_text.lower().strip()
        
        # Clear and rebuild visible thumbnails
        self._clear_grid_layout()
        self.visible_thumbnails.clear()
        
        if not search_text:
            # Show all thumbnails if no search text
            self.visible_thumbnails = self.thumbnails.copy()
        else:
            # Filter by folder name
            for thumbnail in self.thumbnails:
                folder_path = thumbnail.property("folder_path") or ''
                folder_name = os.path.basename(folder_path).lower()
                if search_text in folder_name:
                    self.visible_thumbnails.append(thumbnail)
        
        # Reset focus and update layout
        self.current_focus = 0
        self._update_layout()
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events with folder-specific behavior."""
        key = event.key()
        
        # Handle Enter key to open folder with image viewer
        if (key == Qt.Key.Key_Return and 
            not self.search_input.hasFocus() and 
            self.visible_thumbnails):
            
            thumbnail = self.visible_thumbnails[self.current_focus]
            folder_path = thumbnail.property("folder_path") or ''
            if folder_path:
                self._open_folder_with_viewer(folder_path)
                return
        
        # Handle Escape to go back to parent gallery
        if key == Qt.Key.Key_Escape and not self.search_input.hasFocus():
            if self.parent_gallery:
                self.close()
                self.parent_gallery.raise_()
                self.parent_gallery.activateWindow()
                return
        
        # Use parent class for other key handling
        super().keyPressEvent(event)
    
    def get_folder_paths(self) -> List[str]:
        """Get the list of folder paths.
        
        Returns:
            List of folder paths being displayed
        """
        return self.folder_paths.copy()
    
    def set_folder_paths(self, folder_paths: List[str]):
        """Set new folder paths and refresh display.
        
        Args:
            folder_paths: New list of folder paths to display
        """
        self.folder_paths = folder_paths
        self._load_folder_thumbnails()
        self._update_layout()
        QTimer.singleShot(100, self._adjust_window_size)
    
    def refresh_folders(self):
        """Refresh the folder display."""
        self._load_folder_thumbnails()
        self._update_layout()
