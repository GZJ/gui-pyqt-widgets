"""Image gallery widget for PySide6."""

import os
import math
from typing import List, Optional, Callable, Dict, Any
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QScrollArea, QGridLayout, QLabel, 
    QVBoxLayout, QLineEdit, QApplication
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QKeyEvent

from .image_viewer import ImageViewer
from .image_thumbnail import ImageThumbnail


class ImageGallery(QMainWindow):
    """A comprehensive image gallery widget with thumbnails and search.
    
    Features:
    - Grid layout of image thumbnails
    - Search functionality with real-time filtering
    - Keyboard navigation (vim-style hjkl)
    - Multi-selection support
    - Full-screen image viewer integration
    - Responsive layout that adapts to window size
    - Customizable thumbnail size and spacing
    - Configurable keyboard shortcuts
    - Custom callback functions
    
    Signals:
        image_selected(str, int): Emitted when image is selected (path, index)
        selection_changed(List[int]): Emitted when selection changes (list of indices)
        search_text_changed(str): Emitted when search text changes
        key_pressed(int): Emitted when a key is pressed (key code)
    
    Default Key Bindings:
    - H/J/K/L: Navigate left/down/up/right
    - Enter: Open selected image in viewer
    - /: Focus search box
    - Escape: Clear search / Exit search mode
    - M: Toggle selection of current thumbnail
    - Shift+M: Open folder gallery (if callback provided)
    - Q: Close gallery
    """
    
    image_selected = Signal(str, int)
    selection_changed = Signal(list)
    search_text_changed = Signal(str)
    key_pressed = Signal(int)
    
    def __init__(
        self,
        image_folder: str = "images",
        additional_folders: Optional[List[str]] = None,
        thumbnail_size: int = 240,
        window_geometry: tuple = (100, 100, 900, 600),
        key_bindings: Optional[Dict[str, Callable]] = None,
        callbacks: Optional[Dict[str, Callable]] = None,
        parent: Optional[QWidget] = None
    ):
        """Initialize the ImageGallery.
        
        Args:
            image_folder: Primary folder to scan for images
            additional_folders: Additional folders to include
            thumbnail_size: Size of thumbnails in pixels
            window_geometry: (x, y, width, height) for initial window
            key_bindings: Custom key bindings {key_name: callback}
            callbacks: Custom callback functions for various actions
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.image_folder = image_folder
        self.additional_folders = additional_folders or []
        self.thumbnail_size = thumbnail_size
        self.min_spacing = 10
        
        # State variables
        self.thumbnails: List[ImageThumbnail] = []
        self.visible_thumbnails: List[ImageThumbnail] = []
        self.image_paths: List[str] = []
        self.current_focus = 0
        self.current_cols = 0
        self.selected_indices: set = set()
        self.is_searching = False
        
        # Custom key bindings and callbacks
        self.key_bindings = key_bindings or {}
        self.callbacks = callbacks or {}
        
        # Set up window
        x, y, w, h = window_geometry
        self.setGeometry(x, y, w, h)
        self.setWindowTitle('Image Gallery')
        
        self._setup_ui()
        self._setup_styles()
        self._connect_signals()
        self._load_images()
        
        # Initial layout after a short delay
        QTimer.singleShot(0, self._initial_layout)
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Main widget and layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        
        # Scroll area for thumbnails
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Container for grid layout
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setSpacing(0)
        self.container_layout.setContentsMargins(10, 10, 10, 10)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to search images...")
        self.search_input.hide()  # Initially hidden
        self.container_layout.addWidget(self.search_input)
        
        # Grid layout for thumbnails
        self.grid = QGridLayout()
        self.grid.setSpacing(self.min_spacing)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.container_layout.addLayout(self.grid)
        
        # Add stretch to push everything to top
        self.container_layout.addStretch()
        
        # Set up scroll area
        self.scroll_area.setWidget(self.container)
        
        # Main layout
        main_layout = QVBoxLayout(self.main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.scroll_area)
    
    def _setup_styles(self):
        """Set up widget styles."""
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f5f5f5;
            }
        """)
        
        self.container.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
            }
        """)
        
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
                margin-bottom: 10px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #4a90e2;
                outline: none;
            }
        """)
    
    def _connect_signals(self):
        """Connect internal signals."""
        self.search_input.textChanged.connect(self._on_search_text_changed)
    
    def _load_images(self):
        """Load images from specified folders."""
        self.image_paths.clear()
        self.thumbnails.clear()
        
        # Ensure primary folder exists
        if not os.path.exists(self.image_folder):
            os.makedirs(self.image_folder)
        
        # Collect all image paths
        folders_to_scan = [self.image_folder] + self.additional_folders
        supported_formats = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')
        
        for folder in folders_to_scan:
            if os.path.exists(folder) and os.path.isdir(folder):
                for filename in sorted(os.listdir(folder)):
                    if filename.lower().endswith(supported_formats):
                        full_path = os.path.join(folder, filename)
                        self.image_paths.append(full_path)
        
        # Create thumbnails
        for i, image_path in enumerate(self.image_paths):
            thumbnail = ImageThumbnail(image_path, i, self.thumbnail_size, True, self)
            thumbnail.clicked.connect(self._on_thumbnail_clicked)
            thumbnail.double_clicked.connect(self._on_thumbnail_double_clicked)
            thumbnail.selection_changed.connect(self._on_thumbnail_selection_changed)
            self.thumbnails.append(thumbnail)
        
        # Show message if no images found
        if not self.thumbnails:
            self._show_no_images_message()
        else:
            self.visible_thumbnails = self.thumbnails.copy()
    
    def _show_no_images_message(self):
        """Show a message when no images are found."""
        label = QLabel(f"No images found in:\n{self.image_folder}")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 16px;
                padding: 40px;
            }
        """)
        self.grid.addWidget(label, 0, 0)
    
    def _initial_layout(self):
        """Perform initial layout of thumbnails."""
        self._update_layout()
        if self.thumbnails:
            self.thumbnails[0].image_button.setFocus()
    
    def _update_layout(self):
        """Update the grid layout of thumbnails."""
        # Clear existing layout
        self._clear_grid_layout()
        
        if not self.visible_thumbnails:
            return
        
        # Calculate columns based on available width
        available_width = self.scroll_area.viewport().width() - 20  # Account for margins
        self.current_cols = max(1, available_width // (self.thumbnail_size + self.min_spacing))
        
        # Arrange thumbnails in grid
        for i, thumbnail in enumerate(self.visible_thumbnails):
            row = i // self.current_cols
            col = i % self.current_cols
            self.grid.addWidget(thumbnail, row, col, Qt.AlignmentFlag.AlignTop)
            thumbnail.show()
        
        # Set focus if not searching
        if self.visible_thumbnails and not self.is_searching:
            current_thumbnail = self.visible_thumbnails[min(self.current_focus, len(self.visible_thumbnails) - 1)]
            current_thumbnail.image_button.setFocus()
    
    def _clear_grid_layout(self):
        """Clear all widgets from the grid layout."""
        while self.grid.count():
            child = self.grid.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
    
    def _on_search_text_changed(self, text: str):
        """Handle search text changes."""
        self._filter_thumbnails(text)
        self.search_text_changed.emit(text)
    
    def _filter_thumbnails(self, search_text: Optional[str] = None):
        """Filter thumbnails based on search text."""
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
            # Filter by filename
            for thumbnail in self.thumbnails:
                filename = os.path.basename(thumbnail.get_image_path()).lower()
                if search_text in filename:
                    self.visible_thumbnails.append(thumbnail)
        
        # Reset focus
        self.current_focus = 0
        self._update_layout()
    
    def _on_thumbnail_clicked(self, index: int):
        """Handle thumbnail click."""
        # Find the actual thumbnail and emit signal
        for thumbnail in self.thumbnails:
            if thumbnail.get_index() == index:
                self.image_selected.emit(thumbnail.get_image_path(), index)
                break
    
    def _on_thumbnail_double_clicked(self, index: int):
        """Handle thumbnail double-click - open in viewer."""
        self._show_image_viewer(index)
    
    def _on_thumbnail_selection_changed(self, index: int, is_selected: bool):
        """Handle thumbnail selection changes."""
        if is_selected:
            self.selected_indices.add(index)
        else:
            self.selected_indices.discard(index)
        
        self.selection_changed.emit(list(self.selected_indices))
    
    def _show_image_viewer(self, index: int):
        """Show image viewer for given index."""
        if 0 <= index < len(self.image_paths):
            viewer = ImageViewer(self.image_paths, index, self)
            viewer.show()
    
    def _ensure_thumbnail_visible(self, thumbnail: ImageThumbnail):
        """Ensure the given thumbnail is visible in the scroll area."""
        # Get thumbnail position relative to scroll viewport
        viewport_pos = thumbnail.mapTo(self.scroll_area.viewport(), thumbnail.rect().topLeft())
        viewport_rect = self.scroll_area.viewport().rect()
        
        thumbnail_rect = thumbnail.rect()
        thumbnail_bottom = viewport_pos.y() + thumbnail_rect.height()
        
        scroll_value = self.scroll_area.verticalScrollBar().value()
        
        # Scroll if thumbnail is outside visible area
        if viewport_pos.y() < 0:
            # Thumbnail is above visible area
            self.scroll_area.verticalScrollBar().setValue(scroll_value + viewport_pos.y())
        elif thumbnail_bottom > viewport_rect.height():
            # Thumbnail is below visible area
            self.scroll_area.verticalScrollBar().setValue(
                scroll_value + (thumbnail_bottom - viewport_rect.height())
            )
    
    def set_thumbnail_size(self, size: int):
        """Set thumbnail size and update layout.
        
        Args:
            size: New thumbnail size in pixels
        """
        self.thumbnail_size = size
        for thumbnail in self.thumbnails:
            thumbnail.set_size(size)
        self._update_layout()
    
    def get_selected_image_paths(self) -> List[str]:
        """Get paths of selected images.
        
        Returns:
            List of selected image paths
        """
        return [self.image_paths[i] for i in self.selected_indices if i < len(self.image_paths)]
    
    def clear_selection(self):
        """Clear all selections."""
        for thumbnail in self.thumbnails:
            thumbnail.set_selected(False)
        self.selected_indices.clear()
    
    def refresh_images(self):
        """Refresh the image list and thumbnails."""
        self._load_images()
        self._update_layout()
    
    def showEvent(self, event):
        """Handle show events."""
        super().showEvent(event)
        self._initial_layout()
    
    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        QTimer.singleShot(100, self._update_layout)  # Delay to avoid too frequent updates
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events with support for custom key bindings."""
        if not self.visible_thumbnails:
            super().keyPressEvent(event)
            return
        
        key = event.key()
        modifiers = event.modifiers()
        
        # Emit key pressed signal
        self.key_pressed.emit(key)
        
        # Check custom key bindings first
        key_name = self._get_key_name(key, modifiers)
        if key_name in self.key_bindings:
            callback = self.key_bindings[key_name]
            if callable(callback):
                callback(self, event)
                event.accept()
                return
        
        # Search functionality
        if key == Qt.Key.Key_Slash and not self.search_input.hasFocus():
            self.is_searching = True
            self.search_input.show()
            self.search_input.setFocus()
            event.accept()
            return
        elif key == Qt.Key.Key_Escape:
            if self.search_input.hasFocus():
                self.is_searching = False
                self.search_input.clear()
                self.search_input.hide()
                self._filter_thumbnails("")
                if self.visible_thumbnails:
                    self.visible_thumbnails[self.current_focus].image_button.setFocus()
                event.accept()
                return
        
        # Skip navigation if search has focus
        if self.search_input.hasFocus():
            super().keyPressEvent(event)
            return
        
        # Handle Shift+M for folder gallery (from mrm)
        if key == Qt.Key.Key_M and modifiers == Qt.KeyboardModifier.ShiftModifier:
            if 'open_folder_gallery' in self.callbacks:
                callback = self.callbacks['open_folder_gallery']
                if callable(callback):
                    callback(self.additional_folders, self)
                    event.accept()
                    return
        
        # Navigation
        old_focus = self.current_focus
        max_index = len(self.visible_thumbnails) - 1
        
        if key == Qt.Key.Key_H:  # Left
            if self.current_focus % self.current_cols > 0:
                self.current_focus -= 1
        elif key == Qt.Key.Key_L:  # Right
            if (self.current_focus % self.current_cols < self.current_cols - 1 and 
                self.current_focus < max_index):
                self.current_focus += 1
        elif key == Qt.Key.Key_J:  # Down
            if self.current_focus + self.current_cols <= max_index:
                self.current_focus += self.current_cols
        elif key == Qt.Key.Key_K:  # Up
            if self.current_focus >= self.current_cols:
                self.current_focus -= self.current_cols
        elif key == Qt.Key.Key_Return:  # View image
            thumbnail = self.visible_thumbnails[self.current_focus]
            self._show_image_viewer(thumbnail.get_index())
        elif key == Qt.Key.Key_M:  # Toggle selection
            thumbnail = self.visible_thumbnails[self.current_focus]
            thumbnail.toggle_selection()
        elif key == Qt.Key.Key_Q:  # Quit
            self.close()
        
        # Update focus if it changed
        if old_focus != self.current_focus:
            self.current_focus = max(0, min(self.current_focus, max_index))
            current_thumbnail = self.visible_thumbnails[self.current_focus]
            current_thumbnail.image_button.setFocus()
            self._ensure_thumbnail_visible(current_thumbnail)
        
        super().keyPressEvent(event)
    
    def _get_key_name(self, key: int, modifiers: Qt.KeyboardModifier) -> str:
        """Convert key and modifiers to a string name for key bindings."""
        key_names = {
            int(Qt.Key.Key_H): 'H',
            int(Qt.Key.Key_J): 'J', 
            int(Qt.Key.Key_K): 'K',
            int(Qt.Key.Key_L): 'L',
            int(Qt.Key.Key_Return): 'Enter',
            int(Qt.Key.Key_M): 'M',
            int(Qt.Key.Key_Q): 'Q',
            int(Qt.Key.Key_Slash): 'Slash',
            int(Qt.Key.Key_Escape): 'Escape'
        }
        
        key_name = key_names.get(key, f'Key_{key}')
        
        if modifiers == Qt.KeyboardModifier.ShiftModifier:
            key_name = f'Shift+{key_name}'
        elif modifiers == Qt.KeyboardModifier.ControlModifier:
            key_name = f'Ctrl+{key_name}'
        elif modifiers == Qt.KeyboardModifier.AltModifier:
            key_name = f'Alt+{key_name}'
        
        return key_name
    
    def set_key_binding(self, key_name: str, callback: Callable):
        """Set a custom key binding.
        
        Args:
            key_name: Key name (e.g., 'H', 'Shift+M', 'Ctrl+Q')
            callback: Function to call when key is pressed
        """
        self.key_bindings[key_name] = callback
    
    def set_callback(self, action_name: str, callback: Callable):
        """Set a custom callback function.
        
        Args:
            action_name: Action name (e.g., 'open_folder_gallery', 'show_image_viewer')
            callback: Function to call for the action
        """
        self.callbacks[action_name] = callback
    
    def get_current_image_path(self) -> Optional[str]:
        """Get the path of the currently focused image.
        
        Returns:
            Path to current image or None if no images
        """
        if self.visible_thumbnails and 0 <= self.current_focus < len(self.visible_thumbnails):
            thumbnail = self.visible_thumbnails[self.current_focus]
            return thumbnail.get_image_path()
        return None
    
    def get_current_image_index(self) -> Optional[int]:
        """Get the index of the currently focused image.
        
        Returns:
            Index of current image or None if no images
        """
        if self.visible_thumbnails and 0 <= self.current_focus < len(self.visible_thumbnails):
            thumbnail = self.visible_thumbnails[self.current_focus]
            return thumbnail.get_index()
        return None
