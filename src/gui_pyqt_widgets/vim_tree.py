"""Vim-style tree widget for PySide6."""

from typing import List, Any, Optional, Callable, Dict, Union
import time
from PySide6.QtWidgets import (
    QWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QDialog, 
    QDialogButtonBox, QLineEdit, QLabel, QApplication, 
    QAbstractItemView, QMessageBox, QHeaderView
)
from PySide6.QtCore import Qt, Signal, QTimer, QEvent
from PySide6.QtGui import QKeyEvent, QPalette, QClipboard, QBrush, QColor


class VimTreeInputDialog(QDialog):
    """A modal dialog for text input used by VimTree."""
    
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
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
        self.input_field.setFocus()
        self.input_field.selectAll()
    
    def get_value(self) -> str:
        """Get the entered value."""
        return self.input_field.text()
    
    def keyPressEvent(self, arg__1):
        """Handle key events."""
        if arg__1.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(arg__1)


class VimTree(QWidget):
    """A QTreeWidget with vim-style navigation and inline editing capabilities.
    
    Features:
    - Vim-style navigation (jk keys for up/down, hl for left/right)
    - Inline node editing with 'i' key
    - Node expansion/collapse with Space, Enter, or h/l keys
    - Visual mode selection (v key)
    - Add nodes: 'o' (child), 'O' (sibling above)
    - Delete operations: 'dd' (node), 'x' (node)
    - Copy/paste operations: 'yy' (copy), 'p' (paste)
    - Search: '/' for search mode
    - Refresh tree: 'r'
    
    Key Bindings:
    - j/k: Navigate down/up
    - h/l: Collapse/expand node or move to parent/child
    - gg: Go to first item
    - G: Go to last item
    - i: Enter edit mode for current node
    - v: Enter visual mode (node selection)
    - o: Add new child node below current position
    - O: Add new sibling node above current position
    - dd/x: Delete current node
    - yy: Copy current node
    - p: Paste copied node as child
    - P: Paste copied node as sibling above
    - Space/Enter: Toggle expand/collapse
    - /: Enter search mode
    - n: Next search result
    - N: Previous search result
    - r: Refresh/rebuild the entire tree
    - Escape: Cancel edit/operation/visual mode/search
    - Enter: Save edit or execute action
    
    Args:
        tree_data: Initial tree data (nested dict structure)
        zebra_stripes: Whether to show alternating item colors
        on_node_edit: Optional callback function called when a node is edited
        on_node_selected: Optional callback function called when a node is selected
        on_node_expanded: Optional callback function called when a node is expanded
        on_node_collapsed: Optional callback function called when a node is collapsed
    """
    
    node_edited = Signal(QTreeWidgetItem, str, str)  # item, old_value, new_value
    node_selected = Signal(QTreeWidgetItem, str)     # item, value
    node_added = Signal(QTreeWidgetItem, str)        # item, value
    node_deleted = Signal(QTreeWidgetItem, str)      # item, value
    node_expanded = Signal(QTreeWidgetItem)          # item
    node_collapsed = Signal(QTreeWidgetItem)         # item
    
    def __init__(
        self,
        tree_data: Optional[Dict] = None,
        zebra_stripes: bool = True,
        on_node_edit: Optional[Callable[[QTreeWidgetItem, str, str], None]] = None,
        on_node_selected: Optional[Callable[[QTreeWidgetItem, str], None]] = None,
        on_node_expanded: Optional[Callable[[QTreeWidgetItem], None]] = None,
        on_node_collapsed: Optional[Callable[[QTreeWidgetItem], None]] = None,
        parent=None
    ):
        """Initialize the VimTree widget."""
        super().__init__(parent)
        
        self.tree_data = tree_data or {}
        self.zebra_stripes = zebra_stripes
        self.on_node_edit = on_node_edit
        self.on_node_selected = on_node_selected
        self.on_node_expanded = on_node_expanded
        self.on_node_collapsed = on_node_collapsed
        
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
        self.visual_start_item = None
        self.visual_end_item = None
        
        self._setup_ui()
        
        # Timer for pending operations
        self.timer = QTimer()
        self.timer.timeout.connect(self._check_pending_operations)
        self.timer.start(100)
        
        # Connect signals
        if self.on_node_edit:
            self.node_edited.connect(self.on_node_edit)
        if self.on_node_selected:
            self.node_selected.connect(self.on_node_selected)
        if self.on_node_expanded:
            self.node_expanded.connect(self.on_node_expanded)
        if self.on_node_collapsed:
            self.node_collapsed.connect(self.on_node_collapsed)
    
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)  # Hide header for cleaner look
        self.tree_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.tree_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree_widget.setAlternatingRowColors(self.zebra_stripes)
        
        # Enable editing for specific items when needed
        self.tree_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        self.tree_widget.installEventFilter(self)
        self.setFocusProxy(self.tree_widget)
        
        # Disable input method
        self.tree_widget.setAttribute(Qt.WidgetAttribute.WA_InputMethodEnabled, False)
        self.setAttribute(Qt.WidgetAttribute.WA_InputMethodEnabled, False)
        self.tree_widget.setInputMethodHints(Qt.InputMethodHint.ImhNone)
        
        # Connect signals
        self.tree_widget.itemSelectionChanged.connect(self._on_selection_changed)
        self.tree_widget.itemChanged.connect(self._on_item_changed)
        self.tree_widget.itemExpanded.connect(self._on_item_expanded)
        self.tree_widget.itemCollapsed.connect(self._on_item_collapsed)
        
        layout.addWidget(self.tree_widget)
        self.setLayout(layout)
        
        # Load initial tree data
        self._build_tree()
    
    def set_tree_data(self, tree_data: Dict) -> None:
        """Set or update the tree data from outside."""
        self.tree_data = tree_data
        self._build_tree()
    
    def add_child_node(self, parent_item: Optional[QTreeWidgetItem], text: str, data: Any = None) -> QTreeWidgetItem:
        """Add a child node to the specified parent (or root if parent is None)."""
        if parent_item is None:
            item = QTreeWidgetItem(self.tree_widget, [text])
        else:
            item = QTreeWidgetItem(parent_item, [text])
        
        if data is not None:
            item.setData(0, Qt.ItemDataRole.UserRole, data)
        
        # Ensure items are not editable by default (vim-style control)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        
        self.node_added.emit(item, text)
        return item
    
    def add_sibling_node(self, reference_item: QTreeWidgetItem, text: str, above: bool = False, data: Any = None) -> QTreeWidgetItem:
        """Add a sibling node above or below the reference item."""
        parent_item = reference_item.parent()
        
        if parent_item is None:
            # Root level item
            root = self.tree_widget.invisibleRootItem()
            ref_index = root.indexOfChild(reference_item)
            insert_index = ref_index if above else ref_index + 1
            
            item = QTreeWidgetItem([text])
            root.insertChild(insert_index, item)
        else:
            # Child item
            ref_index = parent_item.indexOfChild(reference_item)
            insert_index = ref_index if above else ref_index + 1
            
            item = QTreeWidgetItem([text])
            parent_item.insertChild(insert_index, item)
        
        if data is not None:
            item.setData(0, Qt.ItemDataRole.UserRole, data)
        
        # Ensure items are not editable by default (vim-style control)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        
        self.node_added.emit(item, text)
        return item
    
    def remove_node(self, item: QTreeWidgetItem) -> None:
        """Remove a node from the tree."""
        if item is None:
            return
        
        text = item.text(0)
        parent = item.parent()
        
        if parent is None:
            # Root level item
            root = self.tree_widget.invisibleRootItem()
            root.removeChild(item)
        else:
            parent.removeChild(item)
        
        self.node_deleted.emit(item, text)
    
    def get_current_item(self) -> Optional[QTreeWidgetItem]:
        """Get currently selected item."""
        return self.tree_widget.currentItem()
    
    def get_current_text(self) -> Optional[str]:
        """Get text of currently selected item."""
        current_item = self.tree_widget.currentItem()
        if current_item:
            return current_item.text(0)
        return None
    
    def clear_tree(self) -> None:
        """Clear all items from the tree."""
        self.tree_widget.clear()
        self.tree_data = {}
    
    def _build_tree(self):
        """Build the tree from tree_data."""
        current_item = self.tree_widget.currentItem()
        current_text = current_item.text(0) if current_item else None
        
        self.tree_widget.clear()
        
        if self.tree_data:
            self._build_tree_recursive(None, self.tree_data)
        
        # Try to restore selection
        if current_text:
            self._find_and_select_item(current_text)
    
    def _build_tree_recursive(self, parent_item: Optional[QTreeWidgetItem], data: Dict):
        """Recursively build tree structure."""
        for key, value in data.items():
            if parent_item is None:
                item = QTreeWidgetItem(self.tree_widget, [str(key)])
            else:
                item = QTreeWidgetItem(parent_item, [str(key)])
            
            # Ensure items are not editable by default
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            if isinstance(value, dict) and value:
                # Has children
                self._build_tree_recursive(item, value)
            elif value is not None:
                # Leaf node with data
                item.setData(0, Qt.ItemDataRole.UserRole, value)
    
    def _find_and_select_item(self, text: str) -> bool:
        """Find and select an item by text."""
        items = self.tree_widget.findItems(text, Qt.MatchFlag.MatchRecursive)
        if items:
            self.tree_widget.setCurrentItem(items[0])
            return True
        return False
    
    def _on_selection_changed(self):
        """Handle selection change events."""
        if self.edit_mode:
            self._exit_edit_mode(save=True)
        
        current_item = self.tree_widget.currentItem()
        if current_item:
            self.node_selected.emit(current_item, current_item.text(0))
    
    def _on_item_changed(self, item: QTreeWidgetItem, column: int):
        """Handle item change events."""
        # Only process changes during edit mode to avoid infinite loops
        if not self.edit_mode or column != 0:
            return
        
        if hasattr(self, '_original_value'):
            old_value = self._original_value
            new_value = item.text(0)
            
            # Store the new value for exit_edit_mode to use
            self._current_edit_value = new_value
            
            # Emit signal only if value actually changed
            if old_value != new_value:
                self.node_edited.emit(item, old_value, new_value)
    
    def _on_item_expanded(self, item: QTreeWidgetItem):
        """Handle item expanded events."""
        self.node_expanded.emit(item)
    
    def _on_item_collapsed(self, item: QTreeWidgetItem):
        """Handle item collapsed events."""
        self.node_collapsed.emit(item)
    
    def eventFilter(self, watched, event):
        """Event filter to capture key events."""
        if event.type() == QEvent.Type.InputMethod or event.type() == QEvent.Type.InputMethodQuery:
            return True
            
        if watched == self.tree_widget and event.type() == QEvent.Type.KeyPress:
            # event is already a QKeyEvent when type is KeyPress
            if self._handle_key_event(event):  # type: ignore
                return True
        return super().eventFilter(watched, event)
    
    def _handle_key_event(self, event: QKeyEvent) -> bool:
        """Handle key events."""
        key = event.key()
        modifiers = event.modifiers()
        
        # Handle editing state
        if self.edit_mode or self.tree_widget.state() == QAbstractItemView.State.EditingState:
            if key == Qt.Key.Key_Escape:
                self._exit_edit_mode(save=False)
                return True
            elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
                # Let Qt handle the return key first to commit the edit
                QTimer.singleShot(0, lambda: self._exit_edit_mode(save=True))
                return False  # Let Qt process the return key
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
                self._delete_current_node()
                return True
            else:
                self.pending_delete = False
            return True
        
        if self.pending_copy:
            if key == Qt.Key.Key_Y:
                self._copy_current_node()
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
        elif key == Qt.Key.Key_H:
            self._move_left()
            return True
        elif key == Qt.Key.Key_L:
            self._move_right()
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
                self._add_sibling_above()
            else:  # o
                self._add_child_node()
            return True
        elif key == Qt.Key.Key_D:
            self.pending_delete = True
            self.delete_start_time = time.time()
            return True
        elif key == Qt.Key.Key_X:
            self._delete_current_node()
            return True
        elif key == Qt.Key.Key_Y:
            if self.pending_copy:
                self._copy_current_node()
                return True
            else:
                self.pending_copy = True
                self.copy_start_time = time.time()
                return True
        elif key == Qt.Key.Key_P:
            if modifiers & Qt.KeyboardModifier.ShiftModifier:  # P
                self._paste_sibling_above()
            else:  # p
                self._paste_child()
            return True
        elif key == Qt.Key.Key_Space or key == Qt.Key.Key_Return:
            self._toggle_expand()
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
            self._refresh_tree()
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
        elif key == Qt.Key.Key_H:
            self._visual_move_left()
            return True
        elif key == Qt.Key.Key_L:
            self._visual_move_right()
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
        current_item = self.tree_widget.currentItem()
        if current_item is None:
            return
        
        # Get the item above
        item_above = self.tree_widget.itemAbove(current_item)
        if item_above:
            self.tree_widget.setCurrentItem(item_above)
    
    def _move_down(self):
        """Move selection down."""
        current_item = self.tree_widget.currentItem()
        if current_item is None:
            return
        
        # Get the item below
        item_below = self.tree_widget.itemBelow(current_item)
        if item_below:
            self.tree_widget.setCurrentItem(item_below)
    
    def _move_left(self):
        """Move to parent or collapse current node."""
        current_item = self.tree_widget.currentItem()
        if current_item is None:
            return
        
        if current_item.isExpanded() and current_item.childCount() > 0:
            # Collapse if expanded
            current_item.setExpanded(False)
        else:
            # Move to parent
            parent = current_item.parent()
            if parent:
                self.tree_widget.setCurrentItem(parent)
    
    def _move_right(self):
        """Expand current node or move to first child."""
        current_item = self.tree_widget.currentItem()
        if current_item is None:
            return
        
        if current_item.childCount() > 0:
            if not current_item.isExpanded():
                # Expand if collapsed
                current_item.setExpanded(True)
            else:
                # Move to first child
                first_child = current_item.child(0)
                if first_child:
                    self.tree_widget.setCurrentItem(first_child)
    
    def _go_to_first(self):
        """Go to first item."""
        root = self.tree_widget.invisibleRootItem()
        if root.childCount() > 0:
            first_item = root.child(0)
            self.tree_widget.setCurrentItem(first_item)
    
    def _go_to_last(self):
        """Go to last visible item."""
        # Find the last visible item by iterating through all items
        iterator = QTreeWidgetItemIterator(self.tree_widget)
        last_item = None
        while iterator.value():
            last_item = iterator.value()
            iterator += 1
        
        if last_item:
            self.tree_widget.setCurrentItem(last_item)
    
    def _toggle_expand(self):
        """Toggle expand/collapse of current item."""
        current_item = self.tree_widget.currentItem()
        if current_item and current_item.childCount() > 0:
            current_item.setExpanded(not current_item.isExpanded())
    
    # Edit methods
    def _enter_edit_mode(self):
        """Enter edit mode for the current node."""
        current_item = self.tree_widget.currentItem()
        
        if current_item:
            self.edit_mode = True
            self._original_value = current_item.text(0)
            
            # Enable editing for this specific item
            current_item.setFlags(current_item.flags() | Qt.ItemFlag.ItemIsEditable)
            
            # Start editing the item directly
            self.tree_widget.editItem(current_item, 0)
    
    def _exit_edit_mode(self, save: bool = True):
        """Exit edit mode."""
        if not self.edit_mode:
            return
        
        current_item = self.tree_widget.currentItem()
        
        if current_item:
            if save:
                # Get the final edited value
                new_value = getattr(self, '_current_edit_value', current_item.text(0))
                old_value = getattr(self, '_original_value', "")
                
                # Emit signal if value changed
                if old_value != new_value:
                    self.node_edited.emit(current_item, old_value, new_value)
            else:
                # Restore original value
                original_value = getattr(self, '_original_value', "")
                # Temporarily disconnect signal to avoid loops
                self.tree_widget.itemChanged.disconnect(self._on_item_changed)
                current_item.setText(0, original_value)
                self.tree_widget.itemChanged.connect(self._on_item_changed)
            
            # Disable editing for this item
            current_item.setFlags(current_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        
        # Clean up edit mode state
        self.edit_mode = False
        if hasattr(self, '_original_value'):
            delattr(self, '_original_value')
        if hasattr(self, '_current_edit_value'):
            delattr(self, '_current_edit_value')
        
        # Ensure focus returns to the tree widget
        self.tree_widget.setFocus()
    
    # Add/Delete methods
    def _add_child_node(self):
        """Add a new child node to current item."""
        current_item = self.tree_widget.currentItem()
        
        dialog = VimTreeInputDialog("Add new child node", "", self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_text = dialog.get_value().strip()
            if new_text:
                new_item = self.add_child_node(current_item, new_text)
                self.tree_widget.setCurrentItem(new_item)
                
                # Expand parent if it has children
                if current_item and current_item.childCount() > 0:
                    current_item.setExpanded(True)
    
    def _add_sibling_above(self):
        """Add a new sibling node above current item."""
        current_item = self.tree_widget.currentItem()
        if current_item is None:
            return
        
        dialog = VimTreeInputDialog("Add new sibling node", "", self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_text = dialog.get_value().strip()
            if new_text:
                new_item = self.add_sibling_node(current_item, new_text, above=True)
                self.tree_widget.setCurrentItem(new_item)
    
    def _delete_current_node(self):
        """Delete the current node."""
        self.pending_delete = False
        current_item = self.tree_widget.currentItem()
        
        if current_item:
            # Find next item to select after deletion
            next_item = self.tree_widget.itemBelow(current_item)
            if not next_item:
                next_item = self.tree_widget.itemAbove(current_item)
            
            self.remove_node(current_item)
            
            # Select next item
            if next_item:
                self.tree_widget.setCurrentItem(next_item)
    
    # Copy/Paste methods
    def _copy_current_node(self):
        """Copy the current node."""
        self.pending_copy = False
        current_item = self.tree_widget.currentItem()
        
        if current_item:
            # Store a deep copy of the item
            self.copied_item = self._copy_tree_item(current_item)
            
            # Also copy text to system clipboard
            clipboard = QApplication.clipboard()
            clipboard.setText(current_item.text(0))
    
    def _copy_tree_item(self, item: QTreeWidgetItem) -> Dict:
        """Create a deep copy of a tree item and its children."""
        item_data = {
            'text': item.text(0),
            'data': item.data(0, Qt.ItemDataRole.UserRole),
            'children': []
        }
        
        for i in range(item.childCount()):
            child = item.child(i)
            item_data['children'].append(self._copy_tree_item(child))
        
        return item_data
    
    def _paste_child(self):
        """Paste copied node as child of current item."""
        if self.copied_item is None:
            # Try to get from system clipboard
            clipboard = QApplication.clipboard()
            clipboard_text = clipboard.text().strip()
            if clipboard_text:
                self.copied_item = {'text': clipboard_text, 'data': None, 'children': []}
            else:
                QMessageBox.information(self, "Information", "No node copied")
                return
        
        current_item = self.tree_widget.currentItem()
        new_item = self._paste_tree_item(current_item, self.copied_item)
        
        if new_item:
            self.tree_widget.setCurrentItem(new_item)
            # Expand parent if it has children
            if current_item and current_item.childCount() > 0:
                current_item.setExpanded(True)
    
    def _paste_sibling_above(self):
        """Paste copied node as sibling above current item."""
        if self.copied_item is None:
            # Try to get from system clipboard
            clipboard = QApplication.clipboard()
            clipboard_text = clipboard.text().strip()
            if clipboard_text:
                self.copied_item = {'text': clipboard_text, 'data': None, 'children': []}
            else:
                QMessageBox.information(self, "Information", "No node copied")
                return
        
        current_item = self.tree_widget.currentItem()
        if current_item is None:
            return
        
        parent_item = current_item.parent()
        new_item = self._paste_tree_item_sibling(current_item, self.copied_item, above=True)
        
        if new_item:
            self.tree_widget.setCurrentItem(new_item)
    
    def _paste_tree_item(self, parent_item: Optional[QTreeWidgetItem], item_data: Dict) -> Optional[QTreeWidgetItem]:
        """Paste a tree item data structure as child."""
        new_item = self.add_child_node(parent_item, item_data['text'], item_data.get('data'))
        
        # Add children recursively
        for child_data in item_data.get('children', []):
            self._paste_tree_item(new_item, child_data)
        
        return new_item
    
    def _paste_tree_item_sibling(self, reference_item: QTreeWidgetItem, item_data: Dict, above: bool = False) -> Optional[QTreeWidgetItem]:
        """Paste a tree item data structure as sibling."""
        new_item = self.add_sibling_node(reference_item, item_data['text'], above, item_data.get('data'))
        
        # Add children recursively
        for child_data in item_data.get('children', []):
            self._paste_tree_item(new_item, child_data)
        
        return new_item
    
    # Visual mode methods
    def _enter_visual_mode(self):
        """Enter visual selection mode."""
        current_item = self.tree_widget.currentItem()
        
        if current_item:
            self.visual_mode = True
            self.visual_start_item = current_item
            self.visual_end_item = current_item
            self._update_visual_selection()
    
    def _exit_visual_mode(self):
        """Exit visual mode and clear selection."""
        self.visual_mode = False
        self.visual_start_item = None
        self.visual_end_item = None
        self._clear_visual_selection()
    
    def _visual_move_up(self):
        """Move visual selection up."""
        current_item = self.tree_widget.currentItem()
        if current_item:
            item_above = self.tree_widget.itemAbove(current_item)
            if item_above:
                self.tree_widget.setCurrentItem(item_above)
                self.visual_end_item = item_above
                self._update_visual_selection()
    
    def _visual_move_down(self):
        """Move visual selection down."""
        current_item = self.tree_widget.currentItem()
        if current_item:
            item_below = self.tree_widget.itemBelow(current_item)
            if item_below:
                self.tree_widget.setCurrentItem(item_below)
                self.visual_end_item = item_below
                self._update_visual_selection()
    
    def _visual_move_left(self):
        """Move visual selection left (to parent)."""
        current_item = self.tree_widget.currentItem()
        if current_item:
            parent = current_item.parent()
            if parent:
                self.tree_widget.setCurrentItem(parent)
                self.visual_end_item = parent
                self._update_visual_selection()
    
    def _visual_move_right(self):
        """Move visual selection right (to first child)."""
        current_item = self.tree_widget.currentItem()
        if current_item and current_item.childCount() > 0:
            if not current_item.isExpanded():
                current_item.setExpanded(True)
            first_child = current_item.child(0)
            if first_child:
                self.tree_widget.setCurrentItem(first_child)
                self.visual_end_item = first_child
                self._update_visual_selection()
    
    def _update_visual_selection(self):
        """Update visual selection highlighting."""
        self._clear_visual_selection()
        
        if not self.visual_mode or not self.visual_start_item or not self.visual_end_item:
            return
        
        # For tree, we'll highlight the path between start and end items
        highlight_color = QColor(100, 150, 255, 80)
        highlight_brush = QBrush(highlight_color)
        
        # Simple implementation: highlight both start and end items
        self.visual_start_item.setBackground(0, highlight_brush)
        self.visual_end_item.setBackground(0, highlight_brush)
        
        # TODO: Could implement more sophisticated path highlighting
    
    def _clear_visual_selection(self):
        """Clear visual selection highlighting."""
        # Clear all backgrounds
        iterator = QTreeWidgetItemIterator(self.tree_widget)
        while iterator.value():
            item = iterator.value()
            item.setBackground(0, QBrush())
            iterator += 1
    
    def _copy_visual_selection(self):
        """Copy visual selection."""
        if not self.visual_mode or not self.visual_start_item:
            return
        
        # For simplicity, copy the current item
        self._copy_current_node()
    
    def _delete_visual_selection(self):
        """Delete visual selection."""
        if not self.visual_mode or not self.visual_start_item:
            return
        
        # For simplicity, delete the current item
        self._delete_current_node()
    
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
    
    def _update_search_display(self):
        """Update search display (could show search text in status bar)."""
        # For now, just update the window title to show search
        parent = self.parent()
        if parent and hasattr(parent, 'setWindowTitle'):
            try:
                if self.search_mode:
                    parent.setWindowTitle(f"Search: {self.search_text}")  # type: ignore
                else:
                    parent.setWindowTitle("VimTree")  # type: ignore
            except AttributeError:
                pass
    
    def _execute_search(self):
        """Execute the current search."""
        if not self.search_text:
            self._exit_search_mode()
            return
        
        self.search_results = []
        search_lower = self.search_text.lower()
        
        # Search through all items
        iterator = QTreeWidgetItemIterator(self.tree_widget)
        while iterator.value():
            item = iterator.value()
            if search_lower in item.text(0).lower():
                self.search_results.append(item)
            iterator += 1
        
        if self.search_results:
            self.current_search_index = 0
            self.tree_widget.setCurrentItem(self.search_results[0])
            # Ensure the item is visible
            self.tree_widget.scrollToItem(self.search_results[0])
        else:
            QMessageBox.information(self, "Search", f"No results found for '{self.search_text}'")
        
        self._exit_search_mode()
    
    def _search_next(self):
        """Go to next search result."""
        if not self.search_results:
            return
        
        self.current_search_index = (self.current_search_index + 1) % len(self.search_results)
        item = self.search_results[self.current_search_index]
        self.tree_widget.setCurrentItem(item)
        self.tree_widget.scrollToItem(item)
    
    def _search_previous(self):
        """Go to previous search result."""
        if not self.search_results:
            return
        
        self.current_search_index = (self.current_search_index - 1) % len(self.search_results)
        item = self.search_results[self.current_search_index]
        self.tree_widget.setCurrentItem(item)
        self.tree_widget.scrollToItem(item)
    
    # Utility methods
    def _refresh_tree(self):
        """Refresh the entire tree."""
        current_item = self.tree_widget.currentItem()
        current_text = current_item.text(0) if current_item else None
        
        self._build_tree()
        
        # Try to restore selection
        if current_text:
            self._find_and_select_item(current_text)
    
    def _check_pending_operations(self):
        """Check and timeout pending operations."""
        current_time = time.time()
        
        if self.pending_delete and current_time - self.delete_start_time > 1.0:
            self.pending_delete = False
        
        if self.pending_copy and current_time - self.copy_start_time > 1.0:
            self._copy_current_node()
            self.pending_copy = False
        
        # Clean up pending g
        if hasattr(self, '_pending_g') and current_time - self._pending_g > 0.5:
            delattr(self, '_pending_g')


# Import QTreeWidgetItemIterator for search functionality
from PySide6.QtWidgets import QTreeWidgetItemIterator
