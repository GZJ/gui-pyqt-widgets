"""
VimList Component Example

This example demonstrates the VimList widget with vim-style navigation and editing.

VimList Key Bindings:
- j/k: Navigate down/up
- gg: Go to first item
- G: Go to last item
- i: Enter edit mode for current item
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

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QHBoxLayout, QTextEdit
from PySide6.QtCore import Qt

# Add the src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from gui_pyqt_widgets.vim_list import VimList


class VimListExampleWindow(QMainWindow):
    """Main window demonstrating VimList functionality."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VimList Example - Vim-style List Navigation")
        self.setGeometry(100, 100, 800, 600)
        
        # Sample data for the list
        self.sample_data = [
            "First item in the list",
            "Second item for navigation testing",
            "Third item with some content",
            "Fourth item to demonstrate vim navigation",
            "Fifth item for editing practice",
            "Sixth item - try pressing 'i' to edit",
            "Seventh item - use 'j' and 'k' to navigate",
            "Eighth item - press 'o' to add below",
            "Ninth item - press 'O' to add above",
            "Tenth item - press 'dd' to delete",
            "Eleventh item - press 'yy' to copy",
            "Twelfth item - press 'p' to paste",
            "Thirteenth item - press 'v' for visual mode",
            "Fourteenth item - press '/' to search",
            "Last item - press 'G' to go to end"
        ]
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        
        # Left side: VimList
        left_layout = QVBoxLayout()
        
        list_label = QLabel("VimList Demo (Focus and use vim keys)")
        list_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        left_layout.addWidget(list_label)
        
        # Create VimList with sample data
        self.vim_list = VimList(
            items=self.sample_data.copy(),
            zebra_stripes=True,
            on_item_edit=self._on_item_edited,
            on_item_selected=self._on_item_selected
        )
        
        # Connect additional signals
        self.vim_list.item_added.connect(self._on_item_added)
        self.vim_list.item_deleted.connect(self._on_item_deleted)
        
        left_layout.addWidget(self.vim_list)
        
        # Right side: Instructions and log
        right_layout = QVBoxLayout()
        
        instructions_label = QLabel("Vim Key Bindings:")
        instructions_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        right_layout.addWidget(instructions_label)
        
        instructions_text = """
Navigation:
• j/k - Move down/up
• gg - Go to first item
• G - Go to last item

Editing:
• i - Edit current item
• o - Add item below
• O - Add item above
• dd - Delete current item
• r - Refresh list

Copy/Paste:
• yy - Copy current item
• p - Paste below current
• P - Paste above current

Visual Mode:
• v - Enter visual mode
• (In visual) j/k - Extend selection
• (In visual) yy - Copy selection
• (In visual) dd - Delete selection

Search:
• / - Start search
• n - Next result
• N - Previous result

General:
• Escape - Cancel operation
• Enter - Confirm edit
        """
        
        instructions = QLabel(instructions_text)
        instructions.setStyleSheet("font-family: monospace; font-size: 11px; background: #f5f5f5; padding: 10px; border: 1px solid #ddd;")
        instructions.setWordWrap(True)
        right_layout.addWidget(instructions)
        
        # Event log
        log_label = QLabel("Event Log:")
        log_label.setStyleSheet("font-weight: bold; font-size: 12px; padding: 5px;")
        right_layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setStyleSheet("font-family: monospace; font-size: 10px;")
        right_layout.addWidget(self.log_text)
        
        # Add layouts to main layout
        layout.addLayout(left_layout, 2)  # VimList takes 2/3 of width
        layout.addLayout(right_layout, 1)  # Instructions take 1/3 of width
        
        # Initial focus to VimList
        self.vim_list.setFocus()
        
        self._log("VimList initialized with sample data. Try vim navigation keys!")
    
    def _on_item_selected(self, index: int, value: str):
        """Handle item selection."""
        self._log(f"Selected item {index}: '{value}'")
    
    def _on_item_edited(self, index: int, old_value: str, new_value: str):
        """Handle item editing."""
        self._log(f"Edited item {index}: '{old_value}' → '{new_value}'")
    
    def _on_item_added(self, index: int, value: str):
        """Handle item addition."""
        self._log(f"Added item {index}: '{value}'")
    
    def _on_item_deleted(self, index: int, value: str):
        """Handle item deletion."""
        self._log(f"Deleted item {index}: '{value}'")
    
    def _log(self, message: str):
        """Add a message to the event log."""
        self.log_text.append(f"• {message}")
        
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


def main():
    """Run the VimList example."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    window = VimListExampleWindow()
    window.show()
    
    # Instructions in console
    print("\n" + "="*60)
    print("VimList Example Started!")
    print("="*60)
    print("Focus the list widget and try these vim-style commands:")
    print("  j/k     - Navigate down/up")
    print("  i       - Edit current item")
    print("  o/O     - Add item below/above")
    print("  dd      - Delete current item")
    print("  yy/p    - Copy/paste item")
    print("  v       - Visual mode selection")
    print("  /       - Search")
    print("  gg/G    - Go to first/last")
    print("  Escape  - Cancel operation")
    print("="*60)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
