#!/usr/bin/env python3
"""Example demonstrating VimMultimediaList usage."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QHBoxLayout, QPushButton
from PySide6.QtCore import QTimer
from PySide6.QtGui import QPixmap, QPainter, QColor, QBrush
from gui_pyqt_widgets.vim_multimedia_list import VimMultimediaList


def create_sample_pixmap(color, text, size=(64, 64)):
    """Create a simple colored pixmap with text for demonstration."""
    pixmap = QPixmap(size[0], size[1])
    pixmap.fill(QColor(color))
    
    painter = QPainter(pixmap)
    painter.setPen(QColor("white"))
    painter.drawText(pixmap.rect(), 0x0004 | 0x0080, text)  # AlignCenter | AlignVCenter
    painter.end()
    
    return pixmap


class MultimediaTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VimMultimediaList Test")
        self.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Left side - Instructions and controls
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        instructions = QLabel(
            "VimMultimediaList Test Instructions:\n\n"
            "Vim Navigation:\n"
            "- j/k: Move down/up\n"
            "- gg: Go to first item\n"
            "- G: Go to last item\n"
            "- i: Edit item text\n"
            "- o/O: Add new item below/above\n"
            "- dd or x: Delete item\n"
            "- yy: Copy item\n"
            "- p/P: Paste item below/above\n"
            "- v: Visual mode (j/k to select, y to copy, d to delete)\n"
            "- /: Search mode\n"
            "- n/N: Next/previous search result\n"
            "- r: Refresh list\n"
            "- Esc: Cancel operation\n\n"
            "Controls:"
        )
        instructions.setWordWrap(True)
        left_layout.addWidget(instructions)
        
        # Add some control buttons
        add_text_btn = QPushButton("Add Text Item")
        add_text_btn.clicked.connect(self.add_text_item)
        left_layout.addWidget(add_text_btn)
        
        add_image_btn = QPushButton("Add Image Item")
        add_image_btn.clicked.connect(self.add_image_item)
        left_layout.addWidget(add_image_btn)
        
        add_mixed_btn = QPushButton("Add Mixed Item")
        add_mixed_btn.clicked.connect(self.add_mixed_item)
        left_layout.addWidget(add_mixed_btn)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_all)
        left_layout.addWidget(clear_btn)
        
        left_layout.addStretch()
        left_widget.setMaximumWidth(300)
        
        # Right side - VimMultimediaList
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        list_label = QLabel("Multimedia List (Focus here and use vim keys):")
        right_layout.addWidget(list_label)
        
        # Create sample items
        sample_items = [
            {
                'text': 'Text only item - This is a simple text item',
                'pixmap': None,
                'id': 'text_1'
            },
            {
                'text': 'Image with text - Red square with description',
                'pixmap': create_sample_pixmap('red', 'R'),
                'id': 'mixed_1'
            },
            {
                'text': 'Blue square image item',
                'pixmap': create_sample_pixmap('blue', 'B'),
                'id': 'mixed_2'
            },
            {
                'text': '',
                'pixmap': create_sample_pixmap('green', 'G'),
                'id': 'image_1'
            },
            {
                'text': 'Another text item with longer content that might wrap to multiple lines',
                'pixmap': None,
                'id': 'text_2'
            },
            {
                'text': 'Yellow square with description',
                'pixmap': create_sample_pixmap('yellow', 'Y'),
                'id': 'mixed_3'
            }
        ]
        
        self.multimedia_list = VimMultimediaList(
            items=sample_items,
            on_item_edit=self.on_item_edited,
            on_item_selected=self.on_item_selected
        )
        right_layout.addWidget(self.multimedia_list)
        
        # Status label
        self.status_label = QLabel("Status: Ready - Click on the list and use vim keys")
        right_layout.addWidget(self.status_label)
        
        # Add widgets to main layout
        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget, 1)
        
        # Set focus to the multimedia list
        QTimer.singleShot(100, self.multimedia_list.setFocus)
    
    def add_text_item(self):
        """Add a text-only item."""
        import random
        texts = [
            "New text item",
            "Sample text content",
            "Another text entry",
            "Text item with some content",
            "Simple text example"
        ]
        text = random.choice(texts)
        self.multimedia_list.add_text_item(text, f"text_{random.randint(1000, 9999)}")
        self.status_label.setText(f"Added text item: {text}")
    
    def add_image_item(self):
        """Add an image-only item."""
        import random
        colors = ['purple', 'orange', 'cyan', 'magenta', 'brown']
        letters = ['P', 'O', 'C', 'M', 'B']
        color = random.choice(colors)
        letter = random.choice(letters)
        pixmap = create_sample_pixmap(color, letter)
        self.multimedia_list.add_image_item(pixmap, f"Image: {color} {letter}", f"img_{random.randint(1000, 9999)}")
        self.status_label.setText(f"Added image item: {color} {letter}")
    
    def add_mixed_item(self):
        """Add a mixed text and image item."""
        import random
        colors = ['lightblue', 'lightgreen', 'pink', 'gold']
        letters = ['L', 'G', 'P', 'G']
        descriptions = ['Mixed content item', 'Combined text and image', 'Multimedia example', 'Text with picture']
        
        color = random.choice(colors)
        letter = random.choice(letters)
        description = random.choice(descriptions)
        
        pixmap = create_sample_pixmap(color, letter)
        self.multimedia_list.add_item(description, pixmap, f"mixed_{random.randint(1000, 9999)}")
        self.status_label.setText(f"Added mixed item: {description}")
    
    def clear_all(self):
        """Clear all items."""
        self.multimedia_list.clear_items()
        self.status_label.setText("Cleared all items")
    
    def on_item_edited(self, index, old_text, new_text):
        """Callback when item is edited."""
        self.status_label.setText(f"✓ EDITED: '{old_text}' → '{new_text}'")
        print(f"Item edited: Index {index}, '{old_text}' -> '{new_text}'")
    
    def on_item_selected(self, index, item_data):
        """Callback when item is selected."""
        text = item_data.get('text', '')
        item_id = item_data.get('id', '')
        has_image = item_data.get('pixmap') is not None
        self.status_label.setText(f"Selected: [{index}] {text} (ID: {item_id}, Image: {has_image})")


def main():
    app = QApplication(sys.argv)
    
    window = MultimediaTestWindow()
    window.show()
    
    print("VimMultimediaList test started!")
    print("Click on the list and try vim navigation keys")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
