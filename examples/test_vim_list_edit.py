#!/usr/bin/env python3
"""Simple test for VimList inline editing functionality."""

import sys
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from gui_pyqt_widgets.vim_list import VimList


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VimList Inline Edit Test")
        self.setGeometry(100, 100, 600, 400)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        label = QLabel("Test VimList - Press 'i' to edit, j/k to navigate")
        label.setStyleSheet("font-weight: bold; padding: 10px;")
        layout.addWidget(label)
        
        # Create VimList with test data
        test_items = [
            "First item - try pressing 'i' to edit",
            "Second item - should edit inline",
            "Third item - press Escape to cancel",
            "Fourth item - press Enter to save",
            "Fifth item - j/k to navigate"
        ]
        
        self.vim_list = VimList(
            items=test_items,
            on_item_edit=self.on_item_edited
        )
        
        layout.addWidget(self.vim_list)
        
        # Focus the list
        self.vim_list.setFocus()
        
    def on_item_edited(self, index: int, old_value: str, new_value: str):
        print(f"Item {index} edited: '{old_value}' -> '{new_value}'")


def main():
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    print("Test started!")
    print("Instructions:")
    print("- Use j/k keys to navigate up/down")
    print("- Press 'i' to start editing an item")
    print("- Press Enter to save changes")
    print("- Press Escape to cancel editing")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
