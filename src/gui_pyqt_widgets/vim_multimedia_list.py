"""Vim-style multimedia list widget for PySide6."""

from typing import List, Any, Optional, Callable, Union
import time
from PySide6.QtWidgets import (
    QWidget, QListWidget, QListWidgetItem, QVBoxLayout, QHBoxLayout, 
    QDialog, QDialogButtonBox, QLineEdit, QLabel, QApplication, 
    QAbstractItemView, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer, QEvent, QSize, QMimeData
from PySide6.QtGui import QKeyEvent, QPalette, QClipboard, QBrush, QColor, QPixmap, QImage, QDrag, QDragEnterEvent, QDropEvent


class VimMultimediaListInputDialog(QDialog):
    """A modal dialog for text input used by VimMultimediaList."""
    
    def __init__(self, title: str, initial_value: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(400, 120)
        
        layout = QVBoxLayout()
        
        label = QLabel(title)
        layout.addWidget(label)
        
        self.input_field = QLineEdit(initial_value)
        layout.addWidget(self.input_field)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
        self.input_field.setFocus()
        self.input_field.selectAll()
    
    def get_value(self) -> str:
        """Get the entered value."""
        return self.input_field.text()
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key events."""
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)


class MultimediaListItem(QWidget):
    """Custom list item that can display both image and text."""
    
    def __init__(self, text="", pixmap=None, item_id=None, parent=None):
        super().__init__(parent)
        self.text = text
        self.pixmap = pixmap
        self.item_id = item_id
        
        # Create layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        
        # Create image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if pixmap:
            self.set_image(pixmap)
        
        # Create text label
        self.text_label = QLabel(text)
        self.text_label.setWordWrap(True)
        self.text_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        # Add labels to layout
        self.layout.addWidget(self.image_label)
        self.layout.addWidget(self.text_label, 1)

    def set_text(self, text):
        """Set text content."""
        self.text = text
        self.text_label.setText(text)
    
    def set_image(self, pixmap):
        """Set image content."""
        if isinstance(pixmap, QPixmap):
            self.pixmap = pixmap
            # Scale image
            scaled_pixmap = pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, 
                                          Qt.TransformationMode.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.setFixedSize(70, 70)
        else:
            self.pixmap = None
            self.image_label.clear()
            self.image_label.setFixedSize(0, 0)
    
    def get_text(self) -> str:
        """Get text content."""
        return self.text
    
    def get_pixmap(self) -> Optional[QPixmap]:
        """Get pixmap content."""
        return self.pixmap
    
    def sizeHint(self):
        """Return suggested size."""
        return QSize(300, 80)


class VimMultimediaList(QWidget):
    """A multimedia list widget with vim-style navigation and editing capabilities.
    
    Features:
    - Vim-style navigation (jk keys for up/down)
    - Inline item editing with 'i' key
    - Visual mode selection (v key)
    - Add items: 'o' (below), 'O' (above)
    - Delete operations: 'dd' (item), 'x' (item)
    - Copy/paste operations: 'yy' (copy), 'p' (paste)
    - Search: '/' for search mode
    - Refresh list: 'r'
    - Support for both text and image content
    
    Key Bindings:
    - j/k: Navigate down/up
    - gg: Go to first item
    - G: Go to last item
    - i: Enter edit mode for current item text
    - v: Enter visual mode (item selection)
    - o: Add new item below current position
    - O: Add new item above current position
    - dd/x: Delete current item
    - yy: Copy current item
    - p: Paste copied item below current position
    - P: Paste copied item above current position
    - /: Enter search mode
    - n: Next search result
    - N: Previous search result
    - r: Refresh/rebuild the entire list
    - Escape: Cancel edit/operation/visual mode/search
    - Enter: Save edit or execute action
    """
    
    item_edited = Signal(int, str, str)  # index, old_text, new_text
    item_selected = Signal(int, object)  # index, item_data
    item_added = Signal(int, object)     # index, item_data
    item_deleted = Signal(int, object)   # index, item_data
    
    def __init__(
        self,
        items: Optional[List[dict]] = None,
        zebra_stripes: bool = True,
        on_item_edit: Optional[Callable[[int, str, str], None]] = None,
        on_item_selected: Optional[Callable[[int, dict], None]] = None,
        parent=None
    ):
        """Initialize the VimMultimediaList widget.
        
        Args:
            items: Initial list of items (each item is a dict with 'text', 'pixmap', 'id' keys)
            zebra_stripes: Whether to show alternating item colors
            on_item_edit: Optional callback function called when an item is edited
            on_item_selected: Optional callback function called when an item is selected
        """
        super().__init__(parent)
        
        self.items = items or []  # List of dicts: {'text': str, 'pixmap': QPixmap, 'id': Any}
        self.zebra_stripes = zebra_stripes
        self.on_item_edit = on_item_edit
        self.on_item_selected = on_item_selected
        
        # State variables
        self.copied_item = None
        self.pending_delete = False
        self.pending_copy = False
        self.delete_start_time = 0
        self.copy_start_time = 0
        self.edit_mode = False
        self.search_mode = False
        self.search_text = ""
        self.search_results = []
        self.current_search_index = -1
        
        # Visual mode
        self.visual_mode = False
        self.visual_start = -1
        self.visual_end = -1
        
        self._setup_ui()
        
        # Timer for pending operations
        self.timer = QTimer()
        self.timer.timeout.connect(self._check_pending_operations)
        self.timer.start(100)
        
        # Connect signals
        if self.on_item_edit:
            self.item_edited.connect(self.on_item_edit)
        if self.on_item_selected:
            self.item_selected.connect(self.on_item_selected)
    
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.list_widget = QListWidget()
        self.list_widget.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_widget.setAlternatingRowColors(self.zebra_stripes)
        
        # Enable editing for specific items when needed
        self.list_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        self.list_widget.installEventFilter(self)
        self.setFocusProxy(self.list_widget)
        
        # Disable input method
        self.list_widget.setAttribute(Qt.WA_InputMethodEnabled, False)
        self.setAttribute(Qt.WA_InputMethodEnabled, False)
        self.list_widget.setInputMethodHints(Qt.ImhNone)
        
        # Connect signals
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        
        layout.addWidget(self.list_widget)
        self.setLayout(layout)
        
        # Load initial items
        self._rebuild_list()
    
    def add_item(self, text: str = "", pixmap: Optional[QPixmap] = None, item_id: Any = None, index: Optional[int] = None) -> None:
        """Add an item to the list."""
        item_data = {
            'text': text,
            'pixmap': pixmap,
            'id': item_id
        }
        
        if index is None:
            self.items.append(item_data)
            index = len(self.items) - 1
        else:
            self.items.insert(index, item_data)
        
        self._rebuild_list()
        self.item_added.emit(index, item_data)
    
    def add_text_item(self, text: str, item_id: Any = None, index: Optional[int] = None) -> None:
        """Add a text-only item to the list."""
        self.add_item(text=text, item_id=item_id, index=index)
    
    def add_image_item(self, pixmap: QPixmap, text: str = "", item_id: Any = None, index: Optional[int] = None) -> None:
        """Add an image item to the list."""
        self.add_item(text=text, pixmap=pixmap, item_id=item_id, index=index)
    
    def update_item(self, index: int, text: Optional[str] = None, pixmap: Optional[QPixmap] = None) -> None:
        """Update an item at specific index."""
        if 0 <= index < len(self.items):
            if text is not None:
                old_text = self.items[index]['text']
                self.items[index]['text'] = text
                self.item_edited.emit(index, old_text, text)
            if pixmap is not None:
                self.items[index]['pixmap'] = pixmap
            self._rebuild_list()
    
    def remove_item(self, index: int) -> None:
        """Remove an item at specific index."""
        if 0 <= index < len(self.items):
            removed_item = self.items.pop(index)
            self._rebuild_list()
            self.item_deleted.emit(index, removed_item)
    
    def get_items(self) -> List[dict]:
        """Get all items."""
        return self.items.copy()
    
    def get_current_item(self) -> Optional[dict]:
        """Get currently selected item."""
        current_row = self.list_widget.currentRow()
        if 0 <= current_row < len(self.items):
            return self.items[current_row]
        return None
    
    def get_current_index(self) -> int:
        """Get currently selected index."""
        return self.list_widget.currentRow()
    
    def clear_items(self) -> None:
        """Clear all items from the list."""
        self.items = []
        self.list_widget.clear()
    
    def _rebuild_list(self):
        """Rebuild the entire list with current items."""
        current_row = self.list_widget.currentRow()
        
        self.list_widget.clear()
        
        for item_data in self.items:
            # Create custom widget
            custom_widget = MultimediaListItem(
                text=item_data.get('text', ''),
                pixmap=item_data.get('pixmap'),
                item_id=item_data.get('id')
            )
            
            # Create list item
            list_item = QListWidgetItem(self.list_widget)
            list_item.setSizeHint(custom_widget.sizeHint())
            
            # Set custom widget to list item
            self.list_widget.setItemWidget(list_item, custom_widget)
            
            # Store item ID as user data
            if item_data.get('id') is not None:
                list_item.setData(Qt.ItemDataRole.UserRole, item_data.get('id'))
        
        # Restore selection
        if 0 <= current_row < self.list_widget.count():
            self.list_widget.setCurrentRow(current_row)
        elif self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)
        
        # Update visual selection if active
        if self.visual_mode:
            self._update_visual_selection()
    
    def _get_item_widget(self, index: int) -> Optional[MultimediaListItem]:
        """Get the custom widget for an item at the given index."""
        if 0 <= index < self.list_widget.count():
            item = self.list_widget.item(index)
            return self.list_widget.itemWidget(item)
        return None
    
    def _on_selection_changed(self):
        """Handle selection change events."""
        if self.edit_mode:
            self._exit_edit_mode(save=True)
        
        current_row = self.list_widget.currentRow()
        if 0 <= current_row < len(self.items):
            self.item_selected.emit(current_row, self.items[current_row])
    
    def eventFilter(self, obj, event):
        """Event filter to capture key events."""
        if event.type() == QEvent.Type.InputMethod or event.type() == QEvent.Type.InputMethodQuery:
            return True
            
        if obj == self.list_widget and event.type() == QEvent.Type.KeyPress:
            if self._handle_key_event(event):
                return True
        return super().eventFilter(obj, event)
    
    def _handle_key_event(self, event: QKeyEvent) -> bool:
        """Handle key events."""
        key = event.key()
        modifiers = event.modifiers()
        
        # Handle editing state
        if self.edit_mode:
            if key == Qt.Key.Key_Escape:
                self._exit_edit_mode(save=False)
                return True
            elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
                self._exit_edit_mode(save=True)
                return True
            # Let other keys pass through for normal editing
            return False
        
        # Handle search mode
        if self.search_mode:
            return self._handle_search_key(event)
        
        # Check pending operations timeout
        if self.pending_delete or self.pending_copy:
            current_time = time.time()
            if self.pending_delete and current_time - self.delete_start_time > 1.0:
                self.pending_delete = False
            if self.pending_copy and current_time - self.copy_start_time > 1.0:
                self.pending_copy = False
        
        return self._handle_navigation_key(event)
    
    def _handle_navigation_key(self, event: QKeyEvent) -> bool:
        """Handle key events in navigation mode."""
        key = event.key()
        modifiers = event.modifiers()
        
        # Handle escape
        if key == Qt.Key.Key_Escape:
            if self.visual_mode:
                self._exit_visual_mode()
                return True
            elif self.pending_delete:
                self.pending_delete = False
                return True
            elif self.pending_copy:
                self.pending_copy = False
                return True
        
        # Handle visual mode
        if self.visual_mode:
            return self._handle_visual_mode_key(event)
        
        # Handle pending operations
        if self.pending_delete:
            if key == Qt.Key.Key_D:
                self._delete_current_item()
                return True
            else:
                self.pending_delete = False
            return True
        
        if self.pending_copy:
            if key == Qt.Key.Key_Y:
                self._copy_current_item()
                return True
            else:
                self.pending_copy = False
            return True
        
        # Navigation keys
        if key == Qt.Key.Key_J:
            self._move_down()
            return True
        elif key == Qt.Key.Key_K:
            self._move_up()
            return True
        elif key == Qt.Key.Key_G:
            if modifiers & Qt.KeyboardModifier.ShiftModifier:  # G
                self._go_to_last()
            else:  # gg (handled in sequence)
                if hasattr(self, '_pending_g') and time.time() - self._pending_g < 0.5:
                    self._go_to_first()
                    delattr(self, '_pending_g')
                else:
                    self._pending_g = time.time()
            return True
        elif key == Qt.Key.Key_I:
            self._enter_edit_mode()
            return True
        elif key == Qt.Key.Key_V:
            self._enter_visual_mode()
            return True
        elif key == Qt.Key.Key_O:
            if modifiers & Qt.KeyboardModifier.ShiftModifier:  # O
                self._add_item_above()
            else:  # o
                self._add_item_below()
            return True
        elif key == Qt.Key.Key_D:
            self.pending_delete = True
            self.delete_start_time = time.time()
            return True
        elif key == Qt.Key.Key_X:
            self._delete_current_item()
            return True
        elif key == Qt.Key.Key_Y:
            if self.pending_copy:
                self._copy_current_item()
                return True
            else:
                self.pending_copy = True
                self.copy_start_time = time.time()
                return True
        elif key == Qt.Key.Key_P:
            if modifiers & Qt.KeyboardModifier.ShiftModifier:  # P
                self._paste_above()
            else:  # p
                self._paste_below()
            return True
        elif key == Qt.Key.Key_Slash:
            self._enter_search_mode()
            return True
        elif key == Qt.Key.Key_N:
            if modifiers & Qt.KeyboardModifier.ShiftModifier:  # N
                self._search_previous()
            else:  # n
                self._search_next()
            return True
        elif key == Qt.Key.Key_R:
            self._refresh_list()
            return True
        
        return False
    
    def _handle_search_key(self, event: QKeyEvent) -> bool:
        """Handle key events in search mode."""
        key = event.key()
        
        if key == Qt.Key.Key_Escape:
            self._exit_search_mode()
            return True
        elif key == Qt.Key.Key_Return:
            self._execute_search()
            return True
        elif key == Qt.Key.Key_Backspace:
            if self.search_text:
                self.search_text = self.search_text[:-1]
                self._update_search_display()
            else:
                self._exit_search_mode()
            return True
        else:
            text = event.text()
            if text.isprintable():
                self.search_text += text
                self._update_search_display()
                return True
        
        return False
    
    def _handle_visual_mode_key(self, event: QKeyEvent) -> bool:
        """Handle key events in visual mode."""
        key = event.key()
        
        if key == Qt.Key.Key_J:
            self._visual_move_down()
            return True
        elif key == Qt.Key.Key_K:
            self._visual_move_up()
            return True
        elif key == Qt.Key.Key_Y:
            self._copy_visual_selection()
            self._exit_visual_mode()
            return True
        elif key == Qt.Key.Key_D or key == Qt.Key.Key_X:
            self._delete_visual_selection()
            self._exit_visual_mode()
            return True
        
        return False
    
    # Navigation methods
    def _move_up(self):
        """Move selection up."""
        current_row = self.list_widget.currentRow()
        if current_row > 0:
            self.list_widget.setCurrentRow(current_row - 1)
    
    def _move_down(self):
        """Move selection down."""
        current_row = self.list_widget.currentRow()
        if current_row < self.list_widget.count() - 1:
            self.list_widget.setCurrentRow(current_row + 1)
    
    def _go_to_first(self):
        """Go to first item."""
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)
    
    def _go_to_last(self):
        """Go to last item."""
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(self.list_widget.count() - 1)
    
    # Edit methods
    def _enter_edit_mode(self):
        """Enter edit mode for the current item text."""
        current_row = self.list_widget.currentRow()
        
        if current_row >= 0 and current_row < len(self.items):
            self.edit_mode = True
            widget = self._get_item_widget(current_row)
            if widget and widget.text_label:
                self._original_value = widget.text_label.text()
                
                # Convert QLabel to QLineEdit for editing
                self._start_inline_edit(widget)
    
    def _start_inline_edit(self, widget: MultimediaListItem):
        """Start inline editing on the text label."""
        # Store reference to the original widget
        self._editing_widget = widget
        
        # Create a QLineEdit for inline editing
        self._edit_line = QLineEdit(widget.text_label.text(), widget)
        
        # Position the line edit over the text label
        text_rect = widget.text_label.geometry()
        self._edit_line.setGeometry(text_rect)
        
        # Style the line edit
        self._edit_line.setStyleSheet("""
            QLineEdit {
                border: 2px solid #4A90E2;
                background-color: white;
                padding: 2px;
                font: """ + widget.text_label.font().toString() + """;
            }
        """)
        
        # Hide the text label temporarily
        widget.text_label.hide()
        
        # Focus and select all text
        self._edit_line.setFocus()
        self._edit_line.selectAll()
        
        # Connect signals
        self._edit_line.editingFinished.connect(lambda: self._exit_edit_mode(save=True))
        self._edit_line.textChanged.connect(self._on_text_changed)
        
        self._edit_line.show()
    
    def _on_text_changed(self, text):
        """Handle text changes during editing."""
        if self.edit_mode:
            self._current_edit_value = text
    
    def _exit_edit_mode(self, save: bool = True):
        """Exit edit mode."""
        if not self.edit_mode:
            return
        
        current_row = self.list_widget.currentRow()
        widget = self._get_item_widget(current_row)
        
        if widget and hasattr(self, '_edit_line'):
            if save:
                # Get the final edited value
                new_value = getattr(self, '_current_edit_value', self._edit_line.text())
                old_value = getattr(self, '_original_value', "")
                
                # Update internal data
                if current_row < len(self.items):
                    self.items[current_row]['text'] = new_value
                    
                # Update the widget text
                widget.set_text(new_value)
                
                # Emit signal if value changed
                if old_value != new_value:
                    self.item_edited.emit(current_row, old_value, new_value)
            else:
                # Restore original value
                original_value = getattr(self, '_original_value', "")
                widget.set_text(original_value)
                
                if current_row < len(self.items):
                    self.items[current_row]['text'] = original_value
            
            # Clean up inline edit
            self._finish_inline_edit(widget)
        
        # Clean up edit mode state
        self.edit_mode = False
        if hasattr(self, '_original_value'):
            delattr(self, '_original_value')
        if hasattr(self, '_current_edit_value'):
            delattr(self, '_current_edit_value')
        
        # Ensure focus returns to the list widget
        self.list_widget.setFocus()
    
    def _finish_inline_edit(self, widget: MultimediaListItem):
        """Finish inline editing and restore the text label."""
        if hasattr(self, '_edit_line'):
            # Clean up the edit line
            self._edit_line.hide()
            self._edit_line.deleteLater()
            delattr(self, '_edit_line')
            
        if hasattr(self, '_editing_widget'):
            delattr(self, '_editing_widget')
            
        # Restore the text label
        widget.text_label.show()
    
    # Add/Delete methods
    def _add_item_below(self):
        """Add a new item below current position."""
        current_row = self.list_widget.currentRow()
        insert_pos = current_row + 1 if current_row >= 0 else len(self.items)
        
        dialog = VimMultimediaListInputDialog("Add new item", "", self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_text = dialog.get_value().strip()
            if new_text:
                self.add_item(text=new_text, index=insert_pos)
                
                if insert_pos < self.list_widget.count():
                    self.list_widget.setCurrentRow(insert_pos)
    
    def _add_item_above(self):
        """Add a new item above current position."""
        current_row = self.list_widget.currentRow()
        insert_pos = current_row if current_row >= 0 else 0
        
        dialog = VimMultimediaListInputDialog("Add new item", "", self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_text = dialog.get_value().strip()
            if new_text:
                self.add_item(text=new_text, index=insert_pos)
                self.list_widget.setCurrentRow(insert_pos)
    
    def _delete_current_item(self):
        """Delete the current item."""
        self.pending_delete = False
        current_row = self.list_widget.currentRow()
        
        if current_row >= 0 and len(self.items) > 0:
            self.remove_item(current_row)
            
            # Adjust selection
            if current_row >= self.list_widget.count():
                current_row = self.list_widget.count() - 1
            if current_row >= 0:
                self.list_widget.setCurrentRow(current_row)
    
    # Copy/Paste methods
    def _copy_current_item(self):
        """Copy the current item."""
        self.pending_copy = False
        current_row = self.list_widget.currentRow()
        
        if 0 <= current_row < len(self.items):
            self.copied_item = self.items[current_row].copy()
            
            # Also copy text to system clipboard
            clipboard = QApplication.clipboard()
            clipboard.setText(self.copied_item.get('text', ''))
    
    def _paste_below(self):
        """Paste copied item below current position."""
        if self.copied_item is None:
            # Try to get from system clipboard
            clipboard = QApplication.clipboard()
            clipboard_text = clipboard.text().strip()
            if clipboard_text:
                self.copied_item = {'text': clipboard_text, 'pixmap': None, 'id': None}
            else:
                QMessageBox.information(self, "Information", "No item copied")
                return
        
        current_row = self.list_widget.currentRow()
        insert_pos = current_row + 1 if current_row >= 0 else len(self.items)
        
        self.add_item(
            text=self.copied_item.get('text', ''),
            pixmap=self.copied_item.get('pixmap'),
            item_id=self.copied_item.get('id'),
            index=insert_pos
        )
        
        if insert_pos < self.list_widget.count():
            self.list_widget.setCurrentRow(insert_pos)
    
    def _paste_above(self):
        """Paste copied item above current position."""
        if self.copied_item is None:
            # Try to get from system clipboard
            clipboard = QApplication.clipboard()
            clipboard_text = clipboard.text().strip()
            if clipboard_text:
                self.copied_item = {'text': clipboard_text, 'pixmap': None, 'id': None}
            else:
                QMessageBox.information(self, "Information", "No item copied")
                return
        
        current_row = self.list_widget.currentRow()
        insert_pos = current_row if current_row >= 0 else 0
        
        self.add_item(
            text=self.copied_item.get('text', ''),
            pixmap=self.copied_item.get('pixmap'),
            item_id=self.copied_item.get('id'),
            index=insert_pos
        )
        
        self.list_widget.setCurrentRow(insert_pos)
    
    # Visual mode methods
    def _enter_visual_mode(self):
        """Enter visual selection mode."""
        current_row = self.list_widget.currentRow()
        
        if current_row >= 0:
            self.visual_mode = True
            self.visual_start = current_row
            self.visual_end = current_row
            self._update_visual_selection()
    
    def _exit_visual_mode(self):
        """Exit visual mode and clear selection."""
        self.visual_mode = False
        self.visual_start = -1
        self.visual_end = -1
        self._clear_visual_selection()
    
    def _visual_move_up(self):
        """Move visual selection up."""
        current_row = self.list_widget.currentRow()
        if current_row > 0:
            new_row = current_row - 1
            self.list_widget.setCurrentRow(new_row)
            self.visual_end = new_row
            self._update_visual_selection()
    
    def _visual_move_down(self):
        """Move visual selection down."""
        current_row = self.list_widget.currentRow()
        if current_row < self.list_widget.count() - 1:
            new_row = current_row + 1
            self.list_widget.setCurrentRow(new_row)
            self.visual_end = new_row
            self._update_visual_selection()
    
    def _update_visual_selection(self):
        """Update visual selection highlighting."""
        self._clear_visual_selection()
        
        if not self.visual_mode:
            return
        
        start = min(self.visual_start, self.visual_end)
        end = max(self.visual_start, self.visual_end)
        
        highlight_color = QColor(100, 150, 255, 80)
        highlight_brush = QBrush(highlight_color)
        
        for row in range(start, end + 1):
            item = self.list_widget.item(row)
            if item:
                item.setBackground(highlight_brush)
    
    def _clear_visual_selection(self):
        """Clear visual selection highlighting."""
        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)
            if item:
                item.setBackground(QBrush())
    
    def _copy_visual_selection(self):
        """Copy visual selection."""
        if not self.visual_mode:
            return
        
        start = min(self.visual_start, self.visual_end)
        end = max(self.visual_start, self.visual_end)
        
        selected_items = []
        for row in range(start, end + 1):
            if row < len(self.items):
                selected_items.append(self.items[row]['text'])
        
        if selected_items:
            # Join multiple items with newlines
            combined_text = '\n'.join(selected_items)
            self.copied_item = {'text': combined_text, 'pixmap': None, 'id': None}
            
            # Copy to system clipboard
            clipboard = QApplication.clipboard()
            clipboard.setText(combined_text)
    
    def _delete_visual_selection(self):
        """Delete visual selection."""
        if not self.visual_mode:
            return
        
        start = min(self.visual_start, self.visual_end)
        end = max(self.visual_start, self.visual_end)
        
        # Delete from end to start to maintain indices
        for row in range(end, start - 1, -1):
            if row < len(self.items):
                self.remove_item(row)
        
        # Adjust selection
        if start < self.list_widget.count():
            self.list_widget.setCurrentRow(start)
        elif self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(self.list_widget.count() - 1)
    
    # Search methods
    def _enter_search_mode(self):
        """Enter search mode."""
        self.search_mode = True
        self.search_text = ""
        self.search_results = []
        self.current_search_index = -1
        self._update_search_display()
    
    def _exit_search_mode(self):
        """Exit search mode."""
        self.search_mode = False
        self.search_text = ""
        self.search_results = []
        self.current_search_index = -1
        # Could show/hide search indicator here
    
    def _update_search_display(self):
        """Update search display (could show search text in status bar)."""
        # For now, just update the window title to show search
        parent = self.parent()
        if parent and hasattr(parent, 'setWindowTitle'):
            try:
                if self.search_mode:
                    parent.setWindowTitle(f"Search: {self.search_text}")
                else:
                    parent.setWindowTitle("VimMultimediaList")
            except AttributeError:
                pass
    
    def _execute_search(self):
        """Execute the current search."""
        if not self.search_text:
            self._exit_search_mode()
            return
        
        self.search_results = []
        search_lower = self.search_text.lower()
        
        for i, item in enumerate(self.items):
            item_text = item.get('text', '')
            if search_lower in item_text.lower():
                self.search_results.append(i)
        
        if self.search_results:
            self.current_search_index = 0
            self.list_widget.setCurrentRow(self.search_results[0])
        else:
            QMessageBox.information(self, "Search", f"No results found for '{self.search_text}'")
        
        self._exit_search_mode()
    
    def _search_next(self):
        """Go to next search result."""
        if not self.search_results:
            return
        
        self.current_search_index = (self.current_search_index + 1) % len(self.search_results)
        self.list_widget.setCurrentRow(self.search_results[self.current_search_index])
    
    def _search_previous(self):
        """Go to previous search result."""
        if not self.search_results:
            return
        
        self.current_search_index = (self.current_search_index - 1) % len(self.search_results)
        self.list_widget.setCurrentRow(self.search_results[self.current_search_index])
    
    # Utility methods
    def _refresh_list(self):
        """Refresh the entire list."""
        current_row = self.list_widget.currentRow()
        self._rebuild_list()
        
        if 0 <= current_row < self.list_widget.count():
            self.list_widget.setCurrentRow(current_row)
    
    def _check_pending_operations(self):
        """Check and timeout pending operations."""
        current_time = time.time()
        
        if self.pending_delete and current_time - self.delete_start_time > 1.0:
            self.pending_delete = False
        
        if self.pending_copy and current_time - self.copy_start_time > 1.0:
            self._copy_current_item()
            self.pending_copy = False
        
        # Clean up pending g
        if hasattr(self, '_pending_g') and current_time - self._pending_g > 0.5:
            delattr(self, '_pending_g')
