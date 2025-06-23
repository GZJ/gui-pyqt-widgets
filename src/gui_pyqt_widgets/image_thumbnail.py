"""Image thumbnail widget for PySide6."""

import os
from typing import Optional, Callable
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt, Signal


class ImageThumbnail(QWidget):
    """A reusable image thumbnail widget with selection capabilities.
    
    Features:
    - Displays image thumbnail with filename
    - Configurable size
    - Selection state management
    - Click and double-click events
    - Hover effects
    - Customizable styling
    
    Signals:
        clicked(int): Emitted when thumbnail is clicked (passes index)
        double_clicked(int): Emitted when thumbnail is double-clicked (passes index)
        selection_changed(int, bool): Emitted when selection state changes (index, is_selected)
    """
    
    clicked = Signal(int)
    double_clicked = Signal(int)
    selection_changed = Signal(int, bool)
    
    def __init__(
        self,
        image_path: str,
        index: int,
        size: int = 200,
        show_filename: bool = True,
        parent: Optional[QWidget] = None
    ):
        """Initialize the ImageThumbnail widget.
        
        Args:
            image_path: Path to the image file
            index: Index identifier for this thumbnail
            size: Size of the thumbnail (width/height in pixels)
            show_filename: Whether to show filename below thumbnail
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.image_path = image_path
        self.index = index
        self.base_size = size
        self.show_filename = show_filename
        self.is_selected = False
        
        self._setup_ui()
        self._setup_styles()
        self._connect_signals()
        self._load_thumbnail()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Create layout
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Create image button
        self.image_button = QPushButton()
        self.image_button.setFixedSize(self.base_size - 10, self.base_size - 10)
        self.image_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.image_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Create filename label if needed
        if self.show_filename:
            self.filename_label = QLabel(os.path.basename(self.image_path))
            self.filename_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.filename_label.setWordWrap(True)
            self.filename_label.setFixedWidth(self.base_size - 10)
        
        # Add to layout
        layout.addWidget(self.image_button)
        if self.show_filename:
            layout.addWidget(self.filename_label)
    
    def _setup_styles(self):
        """Set up widget styles."""
        self.base_button_style = """
            QPushButton {
                border: 2px solid #ddd;
                border-radius: 5px;
                padding: 5px;
                background-color: white;
            }
            QPushButton:hover, QPushButton:focus {
                border: 3px solid #4a90e2;
            }
        """
        
        self.selected_button_style = """
            QPushButton {
                border: 3px solid #ffa500;
                border-radius: 5px;
                padding: 5px;
                background-color: #fff9cc;
            }
            QPushButton:hover, QPushButton:focus {
                border: 3px solid #ff8c00;
            }
        """
        
        if self.show_filename:
            self.filename_label.setStyleSheet("""
                QLabel {
                    color: #333;
                    font-size: 12px;
                    padding: 2px;
                }
            """)
        
        self._update_button_style()
    
    def _connect_signals(self):
        """Connect internal signals."""
        self.image_button.clicked.connect(self._on_clicked)
    
    def _load_thumbnail(self):
        """Load and set the thumbnail image."""
        try:
            # Handle special folder icon marker
            if self.image_path == "__FOLDER_ICON__":
                self._set_folder_icon()
                return
                
            pixmap = QPixmap(self.image_path)
            if pixmap.isNull():
                # Set default icon for invalid images
                self._set_default_icon()
                return
                
            scaled_pixmap = pixmap.scaled(
                self.base_size - 20, self.base_size - 20,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.image_button.setIcon(QIcon(scaled_pixmap))
            self.image_button.setIconSize(scaled_pixmap.size())
            
        except Exception:
            self._set_default_icon()
    
    def _set_folder_icon(self):
        """Set a folder icon."""
        self.image_button.setText("📁")
        self.image_button.setStyleSheet(self.base_button_style + """
            QPushButton {
                font-size: 48px;
                color: #ffa500;
                background-color: #f9f9f9;
            }
        """)
    
    def _set_default_icon(self):
        """Set a default icon for invalid images."""
        # Create a simple default icon or use system default
        self.image_button.setText("📷")
        self.image_button.setStyleSheet(self.base_button_style + """
            QPushButton {
                font-size: 24px;
                color: #999;
            }
        """)
    
    def _update_button_style(self):
        """Update button style based on selection state."""
        if self.is_selected:
            self.image_button.setStyleSheet(self.selected_button_style)
        else:
            self.image_button.setStyleSheet(self.base_button_style)
    
    def _on_clicked(self):
        """Handle button click."""
        self.clicked.emit(self.index)
    
    def toggle_selection(self):
        """Toggle selection state."""
        self.set_selected(not self.is_selected)
    
    def set_selected(self, selected: bool):
        """Set selection state.
        
        Args:
            selected: Whether the thumbnail should be selected
        """
        if self.is_selected != selected:
            self.is_selected = selected
            self._update_button_style()
            self.selection_changed.emit(self.index, selected)
    
    def get_image_path(self) -> str:
        """Get the image path.
        
        Returns:
            The path to the image file
        """
        return self.image_path
    
    def get_index(self) -> int:
        """Get the thumbnail index.
        
        Returns:
            The index identifier
        """
        return self.index
    
    def set_size(self, size: int):
        """Set the thumbnail size.
        
        Args:
            size: New size in pixels
        """
        self.base_size = size
        self.image_button.setFixedSize(size - 10, size - 10)
        if self.show_filename:
            self.filename_label.setFixedWidth(size - 10)
        self._load_thumbnail()
    
    def set_filename_text(self, text: str):
        """Set custom filename text.
        
        Args:
            text: Text to display as filename
        """
        if self.show_filename:
            self.filename_label.setText(text)
    
    def mouseDoubleClickEvent(self, event):
        """Handle double-click events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.index)
        super().mouseDoubleClickEvent(event)
