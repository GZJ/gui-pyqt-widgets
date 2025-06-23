"""Image viewer widget for PySide6."""

from typing import List, Optional
from PySide6.QtWidgets import QMainWindow, QLabel, QPushButton, QApplication
from PySide6.QtGui import QPixmap, QKeyEvent
from PySide6.QtCore import Qt, QSize, Signal


class ImageViewer(QMainWindow):
    """A full-featured image viewer with navigation capabilities.
    
    Features:
    - Full-screen image display with aspect ratio preservation
    - Navigation buttons (previous/next)
    - Keyboard navigation (H/L, P/N, Arrow keys)
    - Zoom to fit screen
    - Window controls (Q to quit, Escape to close)
    - Auto-hide navigation buttons when not applicable
    
    Signals:
        image_changed(int): Emitted when current image changes (passes new index)
        closed(): Emitted when viewer is closed
    
    Key Bindings:
    - H/Left Arrow: Previous image
    - L/Right Arrow: Next image  
    - P: Previous image
    - N: Next image
    - Q/Escape: Close viewer
    """
    
    image_changed = Signal(int)
    closed = Signal()
    
    def __init__(
        self, 
        image_paths: List[str], 
        current_index: int = 0,
        parent: Optional[QMainWindow] = None
    ):
        """Initialize the ImageViewer.
        
        Args:
            image_paths: List of image file paths
            current_index: Index of initial image to display
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.image_paths = image_paths
        self.current_index = max(0, min(current_index, len(image_paths) - 1))
        
        self._setup_ui()
        self._setup_styles()
        self._connect_signals()
        self._update_display()
        
        # Set initial window size and position
        self.setGeometry(100, 100, 800, 600)
    
    def _setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle('Image Viewer')
        
        # Create main image display label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background-color: #2b2b2b;")
        self.setCentralWidget(self.image_label)
        
        # Create navigation buttons
        self.prev_button = QPushButton('◄')
        self.next_button = QPushButton('►')
        
        # Set button properties
        button_size = QSize(40, 40)
        self.prev_button.setFixedSize(button_size)
        self.next_button.setFixedSize(button_size)
        
        # Set buttons as children but position them manually
        self.prev_button.setParent(self)
        self.next_button.setParent(self)
        
        # Ensure buttons are on top
        self.prev_button.raise_()
        self.next_button.raise_()
    
    def _setup_styles(self):
        """Set up widget styles."""
        button_style = """
            QPushButton {
                background-color: rgba(0, 0, 0, 120);
                color: white;
                border: none;
                border-radius: 20px;
                padding: 8px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 180);
            }
            QPushButton:pressed {
                background-color: rgba(0, 0, 0, 220);
            }
        """
        
        self.prev_button.setStyleSheet(button_style)
        self.next_button.setStyleSheet(button_style)
    
    def _connect_signals(self):
        """Connect internal signals."""
        self.prev_button.clicked.connect(self.show_previous)
        self.next_button.clicked.connect(self.show_next)
    
    def _update_display(self):
        """Update the image display and button states."""
        if not self.image_paths or self.current_index < 0 or self.current_index >= len(self.image_paths):
            self.image_label.setText("No image available")
            self.prev_button.hide()
            self.next_button.hide()
            return
        
        # Load and display current image
        current_path = self.image_paths[self.current_index]
        try:
            pixmap = QPixmap(current_path)
            if pixmap.isNull():
                self.image_label.setText(f"Cannot load image:\n{current_path}")
            else:
                # Scale image to fit window while maintaining aspect ratio
                scaled_pixmap = self._scale_image_to_fit(pixmap)
                self.image_label.setPixmap(scaled_pixmap)
                
                # Update window title
                import os
                filename = os.path.basename(current_path)
                self.setWindowTitle(f'Image Viewer - {filename} ({self.current_index + 1}/{len(self.image_paths)})')
                
        except Exception as e:
            self.image_label.setText(f"Error loading image:\n{str(e)}")
        
        # Update button visibility
        self.prev_button.setVisible(self.current_index > 0)
        self.next_button.setVisible(self.current_index < len(self.image_paths) - 1)
        
        # Update button positions
        self._update_button_positions()
        
        # Emit signal
        self.image_changed.emit(self.current_index)
    
    def _scale_image_to_fit(self, pixmap: QPixmap) -> QPixmap:
        """Scale image to fit within the window while maintaining aspect ratio.
        
        Args:
            pixmap: Original pixmap to scale
            
        Returns:
            Scaled pixmap
        """
        # Get available size (subtract some margin for UI elements)
        available_size = self.size()
        margin = 60  # Account for buttons and window chrome
        
        target_size = QSize(
            available_size.width() - margin,
            available_size.height() - margin
        )
        
        return pixmap.scaled(
            target_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
    
    def _update_button_positions(self):
        """Update navigation button positions."""
        if not self.prev_button or not self.next_button:
            return
            
        window_width = self.width()
        window_height = self.height()
        button_margin = 20
        
        # Position buttons vertically centered, with margins from edges
        y_pos = (window_height - self.prev_button.height()) // 2
        
        self.prev_button.move(button_margin, y_pos)
        self.next_button.move(window_width - self.next_button.width() - button_margin, y_pos)
    
    def show_previous(self):
        """Show the previous image."""
        if self.current_index > 0:
            self.current_index -= 1
            self._update_display()
    
    def show_next(self):
        """Show the next image."""
        if self.current_index < len(self.image_paths) - 1:
            self.current_index += 1
            self._update_display()
    
    def show_image_at_index(self, index: int):
        """Show image at specific index.
        
        Args:
            index: Index of image to show
        """
        if 0 <= index < len(self.image_paths):
            self.current_index = index
            self._update_display()
    
    def get_current_index(self) -> int:
        """Get current image index.
        
        Returns:
            Current image index
        """
        return self.current_index
    
    def get_current_image_path(self) -> Optional[str]:
        """Get current image path.
        
        Returns:
            Path to current image, or None if no valid image
        """
        if 0 <= self.current_index < len(self.image_paths):
            return self.image_paths[self.current_index]
        return None
    
    def set_image_paths(self, image_paths: List[str], current_index: int = 0):
        """Set new list of image paths.
        
        Args:
            image_paths: New list of image paths
            current_index: Index to start from
        """
        self.image_paths = image_paths
        self.current_index = max(0, min(current_index, len(image_paths) - 1))
        self._update_display()
    
    def resizeEvent(self, event):
        """Handle window resize events."""
        super().resizeEvent(event)
        self._update_button_positions()
        self._update_display()
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events."""
        key = event.key()
        
        # Navigation keys
        if key in (Qt.Key.Key_H, Qt.Key.Key_Left, Qt.Key.Key_P):
            self.show_previous()
        elif key in (Qt.Key.Key_L, Qt.Key.Key_Right, Qt.Key.Key_N):
            self.show_next()
        elif key in (Qt.Key.Key_Q, Qt.Key.Key_Escape):
            self.close()
        else:
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """Handle close events."""
        self.closed.emit()
        super().closeEvent(event)
