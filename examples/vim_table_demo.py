#!/usr/bin/env python3
"""Main entry point for GUI PyQt Widgets demonstration."""

import sys
from pathlib import Path

# Add src to Python path for development
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt
from gui_pyqt_widgets import VimTable


class DemoWindow(QMainWindow):
    """Main demo window for GUI PyQt Widgets."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GUI PyQt Widgets - VimTable Demo")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Add title label
        title_label = QLabel("VimTable Demo - Try vim-style navigation!")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)
        
        # Add instruction label
        instruction_label = QLabel(
            "Navigation: h/j/k/l or arrow keys | "
            "Edit: i (insert) | "
            "Row ops: o (new below), O (new above), dd (delete) | "
            "Copy/Paste: yy (copy), p (paste)"
        )
        instruction_label.setAlignment(Qt.AlignCenter)
        instruction_label.setStyleSheet("font-size: 12px; color: gray; margin-bottom: 10px;")
        layout.addWidget(instruction_label)
        
        # Create vim table with column headers
        column_headers = ["Name", "Age", "City", "Occupation", "Email"]
        self.vim_table = VimTable(columns=column_headers)
        
        # Disable input method for the VimTable and its internal QTableWidget
        # This prevents Windows IME from activating when the table gets focus
        self.vim_table.setAttribute(Qt.WA_InputMethodEnabled, False)
        if hasattr(self.vim_table, 'table'):
            self.vim_table.table.setAttribute(Qt.WA_InputMethodEnabled, False)
        
        # Set sample data (without headers since they're already set)
        sample_data = [
            ["Alice Johnson", "28", "New York", "Software Engineer", "alice@example.com"],
            ["Bob Smith", "34", "San Francisco", "Product Manager", "bob@example.com"],
            ["Carol Davis", "31", "Chicago", "UX Designer", "carol@example.com"],
            ["David Wilson", "29", "Seattle", "Data Scientist", "david@example.com"],
            ["Eva Brown", "26", "Boston", "Frontend Developer", "eva@example.com"],
            ["Frank Miller", "33", "Austin", "DevOps Engineer", "frank@example.com"],
            ["Grace Chen", "30", "Portland", "Technical Writer", "grace@example.com"],
            ["Henry Lopez", "27", "Denver", "Backend Developer", "henry@example.com"],
            ["Ivy Taylor", "32", "Miami", "UI Designer", "ivy@example.com"],
            ["Jack Thompson", "35", "Atlanta", "Engineering Manager", "jack@example.com"]
        ]
        
        self.vim_table.set_data(sample_data)
        
        # Connect signals for demonstration
        self.vim_table.cell_edited.connect(self.on_cell_changed)
        
        layout.addWidget(self.vim_table)
        
        # Add status label
        self.status_label = QLabel("Ready - Navigate with vim keys or use mouse")
        self.status_label.setStyleSheet("color: green; margin-top: 5px;")
        layout.addWidget(self.status_label)
    
    def on_cell_changed(self, row: int, col: int, old_value: str, new_value: str):
        """Handle cell change events."""
        self.status_label.setText(
            f"Cell ({row}, {col}) changed: '{old_value}' → '{new_value}'"
        )
        self.status_label.setStyleSheet("color: blue; margin-top: 5px;")


def main():
    """Main entry point."""
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("GUI PyQt Widgets")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("GUI PyQt Widgets Project")
    
    # Create and show main window
    window = DemoWindow()
    window.show()
    
    # Additional input method disabling after window is shown
    # This helps prevent Windows IME activation at application level
    if hasattr(app, 'inputMethod'):
        input_method = app.inputMethod()
        if hasattr(input_method, 'setVisible'):
            input_method.setVisible(False)
        if hasattr(input_method, 'hide'):
            input_method.hide()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
