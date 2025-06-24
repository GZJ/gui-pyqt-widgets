#!/usr/bin/env python3
"""Example demonstrating VimTree usage."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QHBoxLayout, QPushButton
from PySide6.QtCore import QTimer
from gui_pyqt_widgets.vim_tree import VimTree


class TreeTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VimTree Test")
        self.setGeometry(100, 100, 1000, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Left side - Instructions and controls
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        instructions = QLabel(
            "VimTree Test Instructions:\n\n"
            "Vim Navigation:\n"
            "- j/k: Move down/up\n"
            "- h/l: Collapse/expand or move to parent/child\n"
            "- gg: Go to first item\n"
            "- G: Go to last item\n"
            "- i: Edit node text\n"
            "- o: Add child node\n"
            "- O: Add sibling node above\n"
            "- dd or x: Delete node\n"
            "- yy: Copy node\n"
            "- p: Paste as child\n"
            "- P: Paste as sibling above\n"
            "- Space/Enter: Toggle expand/collapse\n"
            "- v: Visual mode (h/j/k/l to select, y to copy, d to delete)\n"
            "- /: Search mode\n"
            "- n/N: Next/previous search result\n"
            "- r: Refresh tree\n"
            "- Esc: Cancel operation\n\n"
            "Controls:"
        )
        instructions.setWordWrap(True)
        left_layout.addWidget(instructions)
        
        # Add some control buttons
        add_root_btn = QPushButton("Add Root Node")
        add_root_btn.clicked.connect(self.add_root_node)
        left_layout.addWidget(add_root_btn)
        
        expand_all_btn = QPushButton("Expand All")
        expand_all_btn.clicked.connect(self.expand_all)
        left_layout.addWidget(expand_all_btn)
        
        collapse_all_btn = QPushButton("Collapse All")
        collapse_all_btn.clicked.connect(self.collapse_all)
        left_layout.addWidget(collapse_all_btn)
        
        clear_btn = QPushButton("Clear Tree")
        clear_btn.clicked.connect(self.clear_tree)
        left_layout.addWidget(clear_btn)
        
        load_sample_btn = QPushButton("Load Sample Data")
        load_sample_btn.clicked.connect(self.load_sample_data)
        left_layout.addWidget(load_sample_btn)
        
        left_layout.addStretch()
        left_widget.setMaximumWidth(300)
        
        # Right side - VimTree
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        tree_label = QLabel("Vim Tree (Focus here and use vim keys):")
        right_layout.addWidget(tree_label)
        
        # Create sample tree data
        sample_tree_data = {
            "Project Root": {
                "src": {
                    "components": {
                        "VimTree.py": None,
                        "VimList.py": None,
                        "VimTable.py": None
                    },
                    "utils": {
                        "helpers.py": None,
                        "constants.py": None
                    },
                    "__init__.py": None
                },
                "tests": {
                    "test_vim_tree.py": None,
                    "test_vim_list.py": None,
                    "__init__.py": None
                },
                "examples": {
                    "tree_example.py": None,
                    "list_example.py": None
                },
                "docs": {
                    "README.md": None,
                    "API.md": None,
                    "CHANGELOG.md": None
                },
                "requirements.txt": None,
                "setup.py": None,
                ".gitignore": None
            },
            "Another Root": {
                "folder1": {
                    "subfolder": {
                        "file1.txt": None,
                        "file2.txt": None
                    }
                },
                "folder2": {
                    "data.json": None
                }
            }
        }
        
        self.vim_tree = VimTree(
            tree_data=sample_tree_data,
            on_node_edit=self.on_node_edited,
            on_node_selected=self.on_node_selected,
            on_node_expanded=self.on_node_expanded,
            on_node_collapsed=self.on_node_collapsed
        )
        right_layout.addWidget(self.vim_tree)
        
        # Status label
        self.status_label = QLabel("Status: Ready - Click on the tree and use vim keys")
        right_layout.addWidget(self.status_label)
        
        # Add widgets to main layout
        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget, 1)
        
        # Set focus to the tree
        QTimer.singleShot(100, self.vim_tree.setFocus)
    
    def add_root_node(self):
        """Add a root node."""
        import random
        names = ["New Project", "Folder", "Directory", "Module", "Package"]
        name = random.choice(names) + f"_{random.randint(1, 999)}"
        self.vim_tree.add_child_node(None, name)
        self.status_label.setText(f"Added root node: {name}")
    
    def expand_all(self):
        """Expand all nodes."""
        self.vim_tree.tree_widget.expandAll()
        self.status_label.setText("Expanded all nodes")
    
    def collapse_all(self):
        """Collapse all nodes."""
        self.vim_tree.tree_widget.collapseAll()
        self.status_label.setText("Collapsed all nodes")
    
    def clear_tree(self):
        """Clear the tree."""
        self.vim_tree.clear_tree()
        self.status_label.setText("Tree cleared")
    
    def load_sample_data(self):
        """Load sample data."""
        sample_data = {
            "File System": {
                "Documents": {
                    "Projects": {
                        "GUI Project": {
                            "src": {
                                "main.py": None,
                                "gui.py": None
                            },
                            "tests": {
                                "test_main.py": None
                            }
                        },
                        "Web Project": {
                            "frontend": {
                                "index.html": None,
                                "styles.css": None,
                                "script.js": None
                            },
                            "backend": {
                                "app.py": None,
                                "models.py": None
                            }
                        }
                    },
                    "Notes": {
                        "meeting_notes.txt": None,
                        "ideas.md": None
                    }
                },
                "Downloads": {
                    "software": {
                        "installer.exe": None
                    },
                    "media": {
                        "video.mp4": None,
                        "music.mp3": None
                    }
                },
                "Pictures": {
                    "vacation": {
                        "beach.jpg": None,
                        "sunset.png": None
                    },
                    "work": {
                        "presentation.pdf": None
                    }
                }
            },
            "Configuration": {
                "System": {
                    "config.ini": None,
                    "settings.json": None
                },
                "User": {
                    "preferences.yaml": None,
                    "shortcuts.conf": None
                }
            }
        }
        self.vim_tree.set_tree_data(sample_data)
        self.status_label.setText("Sample data loaded")
    
    def on_node_edited(self, item, old_text, new_text):
        """Callback when node is edited."""
        self.status_label.setText(f"✓ EDITED: '{old_text}' → '{new_text}'")
        print(f"Node edited: '{old_text}' -> '{new_text}'")
    
    def on_node_selected(self, item, text):
        """Callback when node is selected."""
        # Get path to current item
        path_parts = []
        current = item
        while current:
            path_parts.insert(0, current.text(0))
            current = current.parent()
        
        path = " / ".join(path_parts)
        has_children = item.childCount() > 0
        is_expanded = item.isExpanded()
        
        self.status_label.setText(f"Selected: {path} (Children: {has_children}, Expanded: {is_expanded})")
    
    def on_node_expanded(self, item):
        """Callback when node is expanded."""
        text = item.text(0)
        self.status_label.setText(f"Expanded: {text}")
        print(f"Node expanded: {text}")
    
    def on_node_collapsed(self, item):
        """Callback when node is collapsed."""
        text = item.text(0)
        self.status_label.setText(f"Collapsed: {text}")
        print(f"Node collapsed: {text}")


def main():
    app = QApplication(sys.argv)
    
    window = TreeTestWindow()
    window.show()
    
    print("VimTree test started!")
    print("Click on the tree and try vim navigation keys")
    print("Key shortcuts:")
    print("  j/k: Navigate up/down")
    print("  h/l: Collapse/expand or move to parent/child")
    print("  i: Edit current node")
    print("  o: Add child node")
    print("  O: Add sibling node above")
    print("  dd/x: Delete node")
    print("  yy: Copy node")
    print("  p/P: Paste as child/sibling")
    print("  Space/Enter: Toggle expand/collapse")
    print("  /: Search")
    print("  v: Visual mode")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
