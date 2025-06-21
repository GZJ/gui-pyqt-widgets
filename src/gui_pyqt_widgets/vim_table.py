"""Vim-style editable table widget for PySide6."""

from typing import List, Any, Optional, Callable
import time
from PySide6.QtWidgets import (
    QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QDialog, 
    QDialogButtonBox, QLineEdit, QLabel, QHeaderView, QApplication, 
    QAbstractItemView, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QTimer, QEvent
from PySide6.QtGui import QKeyEvent, QPalette, QClipboard, QBrush, QColor


class VimTableInputDialog(QDialog):
    """A modal dialog for text input used by VimTable."""
    
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
        if event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)


class VimTable(QWidget):
    """A QTableWidget with vim-style navigation and inline editing capabilities.
    
    Features:
    - Vim-style navigation (hjkl keys)
    - Inline cell editing with 'i' key
    - Visual mode selection (v and V keys)
    - Escape to cancel, Enter to save
    - Add rows: 'o' (below), 'O' (above)
    - Add columns: 'a' (right), 'A' (end)
    - Delete operations: 'dd' (row), 'dc' (column)
    - Refresh table: 'r' (rebuild entire table)
    
    Key Bindings:
    - h/j/k/l: Navigate left/down/up/right
    - i: Enter edit mode for current cell
    - I: Edit column header/title
    - v: Enter visual mode (cell selection)
    - V: Enter visual line mode (row selection)
    - o: Add new row below current position
    - O: Add new row above current position  
    - a: Add new column to the right of current position
    - A: Add new column at the end of the table
    - dd: Delete current row
    - dc: Delete current column
    - y: Copy current cell / Copy visual selection in visual mode
    - yy: Copy current row
    - p: Paste copied content below current position (row) or to current cell
    - r: Refresh/rebuild the entire table
    - Escape: Cancel edit/operation/visual mode
    - Enter: Save edit
    
    Args:
        columns: List of column names
        zebra_stripes: Whether to show alternating row colors
        on_cell_edit: Optional callback function called when a cell is edited
    """
    
    cell_edited = Signal(int, int, str, str)
    
    def __init__(
        self,
        columns: List[str],
        zebra_stripes: bool = True,
        on_cell_edit: Optional[Callable[[int, int, str, str], None]] = None,
        parent=None
    ):
        """Initialize the VimTable widget."""
        super().__init__(parent)
        self.columns = columns
        self.zebra_stripes = zebra_stripes
        self.on_cell_edit = on_cell_edit
        self.data = []
        self.copied_row = None
        self.copied_cell = None
        self.copied_selection = None  
        self.pending_delete = False
        self.pending_copy = False
        self.delete_start_time = 0
        self.copy_start_time = 0
        self.edit_mode = False
        
        self.visual_mode = False
        self.visual_line_mode = False
        self.visual_start_row = -1
        self.visual_start_col = -1
        self.visual_end_row = -1
        self.visual_end_col = -1
        
        self._setup_ui()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self._check_pending_operations)
        self.timer.start(100)  
        
        if self.on_cell_edit:
            self.cell_edited.connect(self.on_cell_edit)
    
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        
        self.table.setAlternatingRowColors(self.zebra_stripes)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        
        self.table.installEventFilter(self)
        self.setFocusProxy(self.table)
        
        self.table.setAttribute(Qt.WA_InputMethodEnabled, False)
        self.setAttribute(Qt.WA_InputMethodEnabled, False)
        
        self.table.setInputMethodHints(Qt.ImhNone)
        
        self.table.itemChanged.connect(self._on_item_changed)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        
        layout.addWidget(self.table)
        self.setLayout(layout)
    
    def set_data(self, data: List[List[Any]]) -> None:
        """Set or update the table data from outside."""
        self.data = data
        self._rebuild_table()
    
    def update_row_external(self, row_idx: int, row_data: List[Any]) -> None:
        """Update a specific row from outside."""
        if 0 <= row_idx < len(self.data):
            self.data[row_idx] = row_data
            self._rebuild_table()
    
    def update_column_external(self, col_idx: int, col_data: List[Any]) -> None:
        """Update a specific column from outside."""
        if 0 <= col_idx < len(self.columns):
            for i, row in enumerate(self.data):
                if i < len(col_data):
                    row[col_idx] = col_data[i]
            self._rebuild_table()
    
    def update_cell_external(self, row_idx: int, col_idx: int, value: Any) -> None:
        """Update a specific cell from outside."""
        if 0 <= row_idx < len(self.data) and 0 <= col_idx < len(self.columns):
            self.data[row_idx][col_idx] = value
            self._rebuild_table()
    
    def add_row(self, *cells: Any) -> None:
        """Add a new row to the table."""
        self.data.append(list(cells))
        self._rebuild_table()
    
    def update_cell(self, row_idx: int, col_idx: int, value: Any) -> None:
        """Update a cell value by row and column index."""
        if 0 <= row_idx < len(self.data) and 0 <= col_idx < len(self.columns):
            self.data[row_idx][col_idx] = value
            item = QTableWidgetItem(str(value))
            self.table.setItem(row_idx, col_idx, item)
    
    def get_cell(self, row_idx: int, col_idx: int) -> Any:
        """Get a cell value by row and column index."""
        if 0 <= row_idx < len(self.data) and 0 <= col_idx < len(self.data[0]):
            return self.data[row_idx][col_idx]
        return None
    
    def clear_data(self) -> None:
        """Clear all data from the table."""
        self.data = []
        self.table.setRowCount(0)
    
    def _on_item_changed(self, item):
        """Handle item change events from the table."""
        row = item.row()
        col = item.column()
        old_value = str(self.data[row][col]) if row < len(self.data) and col < len(self.data[row]) else ""
        new_value = item.text()
        
        if row < len(self.data) and col < len(self.data[row]):
            self.data[row][col] = new_value
        
        if old_value != new_value:
            self.cell_edited.emit(row, col, old_value, new_value)
            
            if self.on_cell_edit:
                self.on_cell_edit(row, col, old_value, new_value)
    
    def _on_selection_changed(self):
        """Handle selection change events."""
        if self.edit_mode:
            self._exit_edit_mode(save=True)
    
    def eventFilter(self, obj, event):
        """Event filter to capture key events."""
        if event.type() == QEvent.InputMethod or event.type() == QEvent.InputMethodQuery:
            return True
            
        if obj == self.table and event.type() == QEvent.KeyPress:
            if self._handle_key_event(event):
                return True
        return super().eventFilter(obj, event)
    
    def _handle_key_event(self, event: QKeyEvent) -> bool:
        """Handle key events."""
        key = event.key()
        
        if self.table.state() == QAbstractItemView.EditingState:
            if key == Qt.Key_Escape:
                self.edit_mode = False
                return False  
            return False  
        
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
        
        if key == Qt.Key_Escape:
            if self.visual_mode or self.visual_line_mode:
                self._exit_visual_mode()
                return True
            elif self.pending_delete:
                self.pending_delete = False
                return True
            elif self.pending_copy:
                self.pending_copy = False
                return True
        
        if self.visual_mode or self.visual_line_mode:
            return self._handle_visual_mode_key(event)
        
        if self.pending_delete:
            if key == Qt.Key_D:
                self._delete_current_row()
                return True
            elif key == Qt.Key_C:
                self._delete_current_column()
                return True
            else:
                self.pending_delete = False
            return True
        
        if self.pending_copy:
            if key == Qt.Key_Y:
                self._copy_current_row()
                return True
            else:
                self._copy_current_cell()
                self.pending_copy = False
        
        if key == Qt.Key_H:
            self._move_cursor_left()
            return True
        elif key == Qt.Key_J:
            self._move_cursor_down()
            return True
        elif key == Qt.Key_K:
            self._move_cursor_up()
            return True
        elif key == Qt.Key_L:
            self._move_cursor_right()
            return True
        elif key == Qt.Key_V:
            if event.modifiers() & Qt.ShiftModifier:  
                self._enter_visual_line_mode()
            else:  
                self._enter_visual_mode()
            return True
        elif key == Qt.Key_I:
            if event.modifiers() & Qt.ShiftModifier:  
                self._enter_header_edit_mode()
            else:  
                self._enter_edit_mode()
            return True
        elif key == Qt.Key_O:
            if event.modifiers() & Qt.ShiftModifier:  
                self._add_row_above()
            else:
                self._add_row_below()
            return True
        elif key == Qt.Key_A:
            if event.modifiers() & Qt.ShiftModifier:  
                self._add_column_end()
            else:
                self._add_column_right()
            return True
        elif key == Qt.Key_D:
            self.pending_delete = True
            self.delete_start_time = time.time()
            return True
        elif key == Qt.Key_Y:
            if self.pending_copy:
                self._copy_current_row()
                return True
            else:
                self.pending_copy = True
                self.copy_start_time = time.time()
                return True
        elif key == Qt.Key_P:
            self._paste_row()
            return True
        elif key == Qt.Key_R:
            self._refresh_table()
            return True
        
        return False
    
    def _move_cursor_left(self):
        """Move cursor left."""
        current_row = self.table.currentRow()
        current_col = self.table.currentColumn()
        if current_col > 0:
            self.table.setCurrentCell(current_row, current_col - 1)
    
    def _move_cursor_right(self):
        """Move cursor right."""
        current_row = self.table.currentRow()
        current_col = self.table.currentColumn()
        if current_col < self.table.columnCount() - 1:
            self.table.setCurrentCell(current_row, current_col + 1)
    
    def _move_cursor_up(self):
        """Move cursor up."""
        current_row = self.table.currentRow()
        current_col = self.table.currentColumn()
        if current_row > 0:
            self.table.setCurrentCell(current_row - 1, current_col)
    
    def _move_cursor_down(self):
        """Move cursor down."""
        current_row = self.table.currentRow()
        current_col = self.table.currentColumn()
        if current_row < self.table.rowCount() - 1:
            self.table.setCurrentCell(current_row + 1, current_col)
    
    def _enter_edit_mode(self):
        """Enter edit mode for the current cell."""
        current_row = self.table.currentRow()
        current_col = self.table.currentColumn()
        
        if current_row >= 0 and current_col >= 0:
            self.edit_mode = True
            item = self.table.item(current_row, current_col)
            if item:
                self._original_value = item.text()
            else:
                self._original_value = ""
            
            self.table.edit(self.table.currentIndex())
    
    def _exit_edit_mode(self, save: bool = True):
        """Exit edit mode."""
        if not self.edit_mode:
            return
        
        current_row = self.table.currentRow()
        current_col = self.table.currentColumn()
        
        if save and current_row >= 0 and current_col >= 0:
            item = self.table.item(current_row, current_col)
            if item:
                old_value = getattr(self, '_original_value', "")
                new_value = item.text()
                
                if current_row < len(self.data) and current_col < len(self.data[current_row]):
                    self.data[current_row][current_col] = new_value
                
                if old_value != new_value:
                    self.table.itemChanged.disconnect(self._on_item_changed)
                    item.setText(new_value)  
                    self.table.itemChanged.connect(self._on_item_changed)
                    
                    self._on_item_changed(item)
        elif not save:
            if current_row >= 0 and current_col >= 0:
                item = self.table.item(current_row, current_col)
                if item:
                    original_value = getattr(self, '_original_value', "")
                    self.table.itemChanged.disconnect(self._on_item_changed)
                    item.setText(original_value)
                    self.table.itemChanged.connect(self._on_item_changed)
        
        self.edit_mode = False
        self._original_value = ""
    
    def _enter_header_edit_mode(self):
        """Enter header edit mode for the current column."""
        current_col = self.table.currentColumn()
        
        if current_col >= 0:
            current_header = self.columns[current_col]
            dialog = VimTableInputDialog("Edit column header", current_header, self)
            
            if dialog.exec() == QDialog.Accepted:
                new_header = dialog.get_value().strip()
                if new_header:
                    self.columns[current_col] = new_header
                    self.table.setHorizontalHeaderLabels(self.columns)
    
    def _add_row_below(self):
        """Add a new row below the current cursor position."""
        current_row = self.table.currentRow()
        insert_pos = current_row + 1 if current_row >= 0 else len(self.data)
        
        empty_row = [""] * len(self.columns)
        self.data.insert(insert_pos, empty_row)
        self._rebuild_table()
        
        if insert_pos < self.table.rowCount():
            self.table.setCurrentCell(insert_pos, self.table.currentColumn())
    
    def _add_row_above(self):
        """Add a new row above the current cursor position."""
        current_row = self.table.currentRow()
        insert_pos = current_row if current_row >= 0 else 0
        
        empty_row = [""] * len(self.columns)
        self.data.insert(insert_pos, empty_row)
        self._rebuild_table()
        
        self.table.setCurrentCell(insert_pos, self.table.currentColumn())
    
    def _add_column_right(self):
        """Add a new column to the right of the current cursor position."""
        current_col = self.table.currentColumn()
        insert_pos = current_col + 1 if current_col >= 0 else len(self.columns)
        
        new_col_name = f"Col{len(self.columns) + 1}"
        self.columns.insert(insert_pos, new_col_name)
        
        for row in self.data:
            row.insert(insert_pos, "")
        
        self._rebuild_table()
        
        if insert_pos < self.table.columnCount():
            self.table.setCurrentCell(self.table.currentRow(), insert_pos)
    
    def _add_column_end(self):
        """Add a new column at the end of the table."""
        new_col_name = f"Col{len(self.columns) + 1}"
        self.columns.append(new_col_name)
        
        for row in self.data:
            row.append("")
        
        self._rebuild_table()
        
        new_col_index = len(self.columns) - 1
        self.table.setCurrentCell(self.table.currentRow(), new_col_index)
    
    def _delete_current_row(self):
        """Delete the current row."""
        self.pending_delete = False
        current_row = self.table.currentRow()
        
        if current_row >= 0 and len(self.data) > 1:
            self.data.pop(current_row)
            self._rebuild_table()
            
            if current_row >= self.table.rowCount():
                current_row = self.table.rowCount() - 1
            if current_row >= 0:
                self.table.setCurrentCell(current_row, self.table.currentColumn())
        else:
            QMessageBox.warning(self, "Warning", "Cannot delete the last remaining row")
    
    def _delete_current_column(self):
        """Delete the current column."""
        self.pending_delete = False
        current_col = self.table.currentColumn()
        
        if current_col >= 0 and len(self.columns) > 1:
            self.columns.pop(current_col)
            
            for row in self.data:
                if current_col < len(row):
                    row.pop(current_col)
            
            self._rebuild_table()
            
            if current_col >= self.table.columnCount():
                current_col = self.table.columnCount() - 1
            if current_col >= 0:
                self.table.setCurrentCell(self.table.currentRow(), current_col)
        else:
            QMessageBox.warning(self, "Warning", "Cannot delete the last remaining column")
    
    def _copy_current_row(self):
        """Copy the current row to clipboard."""
        self.pending_copy = False
        current_row = self.table.currentRow()
        
        if current_row >= 0 and current_row < len(self.data):
            self.copied_row = self.data[current_row].copy()
            self.copied_cell = None  
            
            clipboard = QApplication.clipboard()
            row_text = '\t'.join(str(cell) for cell in self.copied_row)
            clipboard.setText(row_text)
    
    def _copy_current_cell(self):
        """Copy the current cell to clipboard."""
        current_row = self.table.currentRow()
        current_col = self.table.currentColumn()
        
        if current_row >= 0 and current_col >= 0 and current_row < len(self.data) and current_col < len(self.data[current_row]):
            cell_value = self.data[current_row][current_col]
            self.copied_cell = str(cell_value)
            self.copied_row = None  
            
            clipboard = QApplication.clipboard()
            clipboard.setText(self.copied_cell)
    
    def _paste_row(self):
        """Paste the copied content. Supports cell, row, and visual selection pasting."""
        clipboard = QApplication.clipboard()
        clipboard_text = clipboard.text().strip()
        current_row = self.table.currentRow()
        current_col = self.table.currentColumn()
        
        if self.copied_selection is not None:
            self._paste_visual_selection()
            return
        
        if self.copied_cell is not None:
            if current_row >= 0 and current_col >= 0:
                if current_row < len(self.data) and current_col < len(self.data[current_row]):
                    old_value = str(self.data[current_row][current_col])
                    self.data[current_row][current_col] = self.copied_cell
                    
                    item = QTableWidgetItem(str(self.copied_cell))
                    self.table.setItem(current_row, current_col, item)
                    
                    self.cell_edited.emit(current_row, current_col, old_value, self.copied_cell)
                    if self.on_cell_edit:
                        self.on_cell_edit(current_row, current_col, old_value, self.copied_cell)
            return
        
        pasted_row = None
        
        if clipboard_text:
            if '\n' in clipboard_text:
                self._paste_clipboard_visual_selection(clipboard_text)
                return
            elif '\t' in clipboard_text:
                clipboard_cells = clipboard_text.split('\t')
                if clipboard_cells:
                    pasted_row = clipboard_cells
            else:
                if current_row >= 0 and current_col >= 0:
                    if current_row < len(self.data) and current_col < len(self.data[current_row]):
                        old_value = str(self.data[current_row][current_col])
                        self.data[current_row][current_col] = clipboard_text
                        
                        item = QTableWidgetItem(clipboard_text)
                        self.table.setItem(current_row, current_col, item)
                        
                        self.cell_edited.emit(current_row, current_col, old_value, clipboard_text)
                        if self.on_cell_edit:
                            self.on_cell_edit(current_row, current_col, old_value, clipboard_text)
                return
        
        if not pasted_row and self.copied_row:
            pasted_row = self.copied_row.copy()
        
        if not pasted_row:
            QMessageBox.information(self, "Information", "No content copied")
            return
        
        insert_pos = current_row + 1 if current_row >= 0 else len(self.data)
        
        if len(pasted_row) < len(self.columns):
            pasted_row.extend([""] * (len(self.columns) - len(pasted_row)))
        elif len(pasted_row) > len(self.columns):
            pasted_row = pasted_row[:len(self.columns)]
        
        self.data.insert(insert_pos, pasted_row)
        self._rebuild_table()
        
        if insert_pos < self.table.rowCount():
            self.table.setCurrentCell(insert_pos, self.table.currentColumn())
    
    def _refresh_table(self):
        """Refresh the entire table by rebuilding it."""
        current_row = self.table.currentRow()
        current_col = self.table.currentColumn()
        
        self._rebuild_table()
        
        if current_row >= 0 and current_col >= 0:
            if current_row < self.table.rowCount() and current_col < self.table.columnCount():
                self.table.setCurrentCell(current_row, current_col)
            else:
                self.table.setCurrentCell(0, 0)
    
    def _rebuild_table(self):
        """Rebuild the entire table with current data."""
        current_row = self.table.currentRow()
        current_col = self.table.currentColumn()
        visual_mode_backup = self.visual_mode
        visual_line_mode_backup = self.visual_line_mode
        
        self.table.setRowCount(len(self.data))
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)
        
        for row_idx, row_data in enumerate(self.data):
            for col_idx, cell_value in enumerate(row_data):
                item = QTableWidgetItem(str(cell_value))
                self.table.setItem(row_idx, col_idx, item)
        
        if current_row >= 0 and current_col >= 0:
            if current_row < self.table.rowCount() and current_col < self.table.columnCount():
                self.table.setCurrentCell(current_row, current_col)
            elif self.table.rowCount() > 0 and self.table.columnCount() > 0:
                self.table.setCurrentCell(0, 0)
        
        if visual_mode_backup or visual_line_mode_backup:
            self._update_visual_selection()
    
    def _check_pending_operations(self):
        """Check and timeout pending operations."""
        if self.pending_delete or self.pending_copy:
            current_time = time.time()
            if self.pending_delete and current_time - self.delete_start_time > 1.0:
                self.pending_delete = False
            if self.pending_copy and current_time - self.copy_start_time > 1.0:
                self._copy_current_cell()
                self.pending_copy = False
    
    def _enter_visual_mode(self):
        """Enter visual cell selection mode."""
        current_row = self.table.currentRow()
        current_col = self.table.currentColumn()
        
        if current_row >= 0 and current_col >= 0:
            self.visual_mode = True
            self.visual_line_mode = False
            self.visual_start_row = current_row
            self.visual_start_col = current_col
            self.visual_end_row = current_row
            self.visual_end_col = current_col
            self._update_visual_selection()
    
    def _enter_visual_line_mode(self):
        """Enter visual line selection mode."""
        current_row = self.table.currentRow()
        current_col = self.table.currentColumn()
        
        if current_row >= 0:
            self.visual_line_mode = True
            self.visual_mode = False
            self.visual_start_row = current_row
            self.visual_start_col = 0
            self.visual_end_row = current_row
            self.visual_end_col = self.table.columnCount() - 1
            self._update_visual_selection()
    
    def _exit_visual_mode(self):
        """Exit visual mode and clear selection."""
        self.visual_mode = False
        self.visual_line_mode = False
        self.visual_start_row = -1
        self.visual_start_col = -1
        self.visual_end_row = -1
        self.visual_end_col = -1
        self._clear_visual_selection()
    
    def _handle_visual_mode_key(self, event: QKeyEvent) -> bool:
        """Handle key events in visual mode."""
        key = event.key()
        
        if key == Qt.Key_H:
            self._visual_move_left()
            return True
        elif key == Qt.Key_J:
            self._visual_move_down()
            return True
        elif key == Qt.Key_K:
            self._visual_move_up()
            return True
        elif key == Qt.Key_L:
            self._visual_move_right()
            return True
        elif key == Qt.Key_Y:
            self._copy_visual_selection()
            self._exit_visual_mode()
            return True
        elif key == Qt.Key_D:
            self._exit_visual_mode()
            return True
        
        return False
    
    def _visual_move_left(self):
        """Move visual selection left."""
        if self.visual_line_mode:
            return  
        
        current_col = self.table.currentColumn()
        if current_col > 0:
            new_col = current_col - 1
            self.table.setCurrentCell(self.table.currentRow(), new_col)
            self.visual_end_col = new_col
            self._update_visual_selection()
    
    def _visual_move_right(self):
        """Move visual selection right."""
        if self.visual_line_mode:
            return  
        
        current_col = self.table.currentColumn()
        if current_col < self.table.columnCount() - 1:
            new_col = current_col + 1
            self.table.setCurrentCell(self.table.currentRow(), new_col)
            self.visual_end_col = new_col
            self._update_visual_selection()
    
    def _visual_move_up(self):
        """Move visual selection up."""
        current_row = self.table.currentRow()
        if current_row > 0:
            new_row = current_row - 1
            self.table.setCurrentCell(new_row, self.table.currentColumn())
            self.visual_end_row = new_row
            if self.visual_line_mode:
                self.visual_end_col = self.table.columnCount() - 1
            self._update_visual_selection()
    
    def _visual_move_down(self):
        """Move visual selection down."""
        current_row = self.table.currentRow()
        if current_row < self.table.rowCount() - 1:
            new_row = current_row + 1
            self.table.setCurrentCell(new_row, self.table.currentColumn())
            self.visual_end_row = new_row
            if self.visual_line_mode:
                self.visual_end_col = self.table.columnCount() - 1
            self._update_visual_selection()
    
    def _update_visual_selection(self):
        """Update the visual selection highlighting."""
        self._clear_visual_selection()
        
        if not (self.visual_mode or self.visual_line_mode):
            return
        
        start_row = min(self.visual_start_row, self.visual_end_row)
        end_row = max(self.visual_start_row, self.visual_end_row)
        start_col = min(self.visual_start_col, self.visual_end_col)
        end_col = max(self.visual_start_col, self.visual_end_col)
        
        highlight_color = QColor(100, 150, 255, 80)  
        highlight_brush = QBrush(highlight_color)
        
        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                item = self.table.item(row, col)
                if item is None:
                    item = QTableWidgetItem("")
                    self.table.setItem(row, col, item)
                item.setBackground(highlight_brush)
    
    def _clear_visual_selection(self):
        """Clear visual selection highlighting."""
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setBackground(QBrush())  
    
    def _copy_visual_selection(self):
        """Copy the visual selection to clipboard."""
        if not (self.visual_mode or self.visual_line_mode):
            return
        
        start_row = min(self.visual_start_row, self.visual_end_row)
        end_row = max(self.visual_start_row, self.visual_end_row)
        start_col = min(self.visual_start_col, self.visual_end_col)
        end_col = max(self.visual_start_col, self.visual_end_col)
        
        selected_data = []
        for row in range(start_row, end_row + 1):
            row_data = []
            for col in range(start_col, end_col + 1):
                if row < len(self.data) and col < len(self.data[row]):
                    row_data.append(str(self.data[row][col]))
                else:
                    row_data.append("")
            selected_data.append(row_data)
        
        self.copied_selection = selected_data
        self.copied_row = None  
        self.copied_cell = None
        
        clipboard = QApplication.clipboard()
        if len(selected_data) == 1 and len(selected_data[0]) == 1:
            clipboard.setText(selected_data[0][0])
        else:
            clipboard_text = '\n'.join('\t'.join(row) for row in selected_data)
            clipboard.setText(clipboard_text)
    
    def _paste_visual_selection(self):
        """Paste a visual selection starting from current position."""
        if self.copied_selection is None:
            return
        
        current_row = self.table.currentRow()
        current_col = self.table.currentColumn()
        
        if current_row < 0 or current_col < 0:
            return
        
        for row_offset, row_data in enumerate(self.copied_selection):
            target_row = current_row + row_offset
            
            
            while target_row >= len(self.data):
                self.data.append([""] * len(self.columns))
            
            for col_offset, cell_value in enumerate(row_data):
                target_col = current_col + col_offset
                
                if target_col >= len(self.columns):
                    continue  
                
                while target_col >= len(self.data[target_row]):
                    self.data[target_row].append("")
                
                old_value = str(self.data[target_row][target_col])
                self.data[target_row][target_col] = cell_value
                
                self.cell_edited.emit(target_row, target_col, old_value, cell_value)
                if self.on_cell_edit:
                    self.on_cell_edit(target_row, target_col, old_value, cell_value)
        
        self._rebuild_table()
    
    def _paste_clipboard_visual_selection(self, clipboard_text: str):
        """Paste multi-line clipboard content as visual selection."""
        lines = clipboard_text.split('\n')
        selection_data = []
        
        for line in lines:
            if '\t' in line:
                row_data = line.split('\t')
            else:
                row_data = [line]
            selection_data.append(row_data)
        
        old_copied_selection = self.copied_selection
        self.copied_selection = selection_data
        self._paste_visual_selection()
        self.copied_selection = old_copied_selection
