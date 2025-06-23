# GUI PyQt Widgets

A collection of reusable PySide6 GUI components designed for high cohesion and low coupling.

## Overview

This project provides a comprehensive set of GUI widgets built with PySide6, including advanced table editing with vim-style navigation and a complete image gallery system. All components are designed to be highly reusable and easily integrated into other applications.

## Components

### 1. VimTable
Advanced table widget with vim-style navigation and editing capabilities.

**Features:**
- Modal editing (Normal/Insert/Visual modes)
- Vim-style keybindings (h/j/k/l navigation, i/a/o for insert modes)
- Row/column manipulation (dd for delete, yy for copy, p for paste)
- Visual mode for selection (v for cell selection, V for row selection)
- Cell editing with custom dialogs
- Signal system for integration (cell_edited signal)
- Customizable styling and behavior
- Zebra stripe support for better readability

### 2. ImageThumbnail
A reusable image thumbnail widget with selection capabilities.

**Features:**
- Displays image thumbnail with filename
- Configurable size and appearance
- Selection state management  
- Click and double-click events
- Hover effects and focus states
- Customizable styling through Qt stylesheets
- Handles invalid images gracefully

### 3. ImageViewer
A full-featured image viewer with navigation capabilities.

**Features:**
- Full-screen image display with aspect ratio preservation
- Navigation buttons (previous/next) with auto-hide
- Keyboard navigation (H/L, P/N, Arrow keys)
- Automatic scaling to fit window
- Window controls (Q to quit, Escape to close)
- Image information in title bar

### 4. ImageGallery
A comprehensive image gallery widget with thumbnails and search.

**Features:**
- Responsive grid layout of image thumbnails
- Real-time search functionality with filtering
- Vim-style keyboard navigation (hjkl)
- Multi-selection support with visual feedback
- Integrated full-screen image viewer
- Auto-adjusting layout based on window size
- Scroll area with smooth navigation
- Support for multiple image formats

**Key Bindings:**
- `H/J/K/L`: Navigate left/down/up/right
- `Enter`: Open selected image in viewer
- `/`: Focus search box
- `Escape`: Clear search / Exit search mode
- `M`: Toggle selection of current thumbnail
- `Q`: Close gallery

### 5. FolderImageGallery
A specialized image gallery for displaying and browsing folder previews.

**Features:**
- Displays folders as thumbnails with preview images
- Uses folder.jpg, preview.jpg, or first image as preview
- Falls back to default folder icon when no preview available
- Opens folder content in new ImageGallery on interaction
- Inherits all ImageGallery navigation and search features
- Automatic window sizing based on content
- Parent-child gallery navigation

## Installation

### Using uv (Development)

```bash
# Clone the repository (for development)
git clone https://github.com/gzj/gui-pyqt-widgets.git
cd gui-pyqt-widgets

# Install development dependencies
uv sync
```

### As a Library Dependency

Add this library to your project using uv:

```bash
# Add from GitHub
uv add git+https://github.com/gzj/gui-pyqt-widgets.git

# Add PySide6 dependency
uv add "PySide6>=6.9.1"
```

## Quick Start

Here's a simple example of using the VimTable widget:

```python
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

from gui_pyqt_widgets import VimTable

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VimTable Demo")
        
        # Create the vim table with column headers
        columns = ["Name", "Age", "City"]
        vim_table = VimTable(columns=columns)
        
        # Set sample data (data rows only, headers already defined)
        sample_data = [
            ["Alice", "25", "New York"],
            ["Bob", "30", "San Francisco"],
            ["Carol", "35", "Chicago"]
        ]
        vim_table.set_data(sample_data)
        
        # Optional: Connect to cell edit events
        vim_table.cell_edited.connect(self.on_cell_changed)
        
        # Set up the main widget
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(vim_table)
        self.setCentralWidget(central_widget)
    
    def on_cell_changed(self, row, col, old_value, new_value):
        """Handle cell change events."""
        print(f"Cell ({row}, {col}) changed: '{old_value}' → '{new_value}'")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
```

## Key Bindings

The VimTable supports various vim-style commands:

### Navigation (Normal Mode)

- `h` / `←` : Move left
- `j` / `↓` : Move down  
- `k` / `↑` : Move up
- `l` / `→` : Move right

### Editing

- `i` : Insert mode (edit current cell)
- `I` : Edit column header/title
- `Enter` : Edit current cell
- `Escape` : Return to normal mode

### Row Operations

- `o` : Insert new row below current position
- `O` : Insert new row above current position
- `dd` : Delete current row
- `yy` : Copy current row
- `p` : Paste row below current position

### Column Operations

- `a` : Add new column to the right of current position
- `A` : Add new column at the end of the table
- `dc` : Delete current column

### Visual Mode

- `v` : Enter visual mode (cell selection)
- `V` : Enter visual line mode (row selection)
- `y` : Copy current cell or visual selection
- `Escape` : Exit visual mode

### Other Operations

- `r` : Refresh/rebuild the entire table

## API Reference

### VimTable Class

```python
VimTable(
    columns: List[str],
    zebra_stripes: bool = True,
    on_cell_edit: Optional[Callable[[int, int, str, str], None]] = None,
    parent=None
)
```

**Parameters:**

- `columns`: List of column header names
- `zebra_stripes`: Enable alternating row colors (default: True)
- `on_cell_edit`: Optional callback function for cell edit events
- `parent`: Parent widget (optional)

**Methods:**

- `set_data(data: List[List[Any]])`: Set table data (rows only, no headers)
- `update_row_external(row_idx: int, row_data: List[Any])`: Update specific row
- `update_column_external(col_idx: int, col_data: List[Any])`: Update specific column (col_data length should match or exceed the number of rows)  
- `update_cell_external(row_idx: int, col_idx: int, value: Any)`: Update specific cell

**Signals:**

- `cell_edited(int, int, str, str)`: Emitted when cell is edited (row, col, old_value, new_value)

### Usage Examples

#### Basic Usage

```python
from gui_pyqt_widgets import VimTable

# Create table with columns
table = VimTable(columns=["ID", "Name", "Status"])

# Set data
table.set_data([
    ["1", "Task 1", "Complete"],
    ["2", "Task 2", "In Progress"],
    ["3", "Task 3", "Pending"]
])
```

#### With Event Handling

```python
def handle_edit(row, col, old_val, new_val):
    print(f"Row {row}, Col {col}: {old_val} -> {new_val}")

table = VimTable(
    columns=["Name", "Value"],
    on_cell_edit=handle_edit,
    zebra_stripes=False
)

# Set some sample data
table.set_data([
    ["Alice", "100"],
    ["Bob", "200"],
    ["Carol", "300"]
])

# Or connect to signal (alternative method)
table.cell_edited.connect(handle_edit)
```

#### Dynamic Updates

```python
# Update entire row
table.update_row_external(0, ["New Name", "New Value"])

# Update single cell
table.update_cell_external(1, 0, "Updated Name")

# Update entire column
table.update_column_external(1, ["Val1", "Val2", "Val3"])
```

## Quick Start Examples

### Basic ImageGallery Example

```python
import sys
from PySide6.QtWidgets import QApplication
from gui_pyqt_widgets import ImageGallery

app = QApplication(sys.argv)

# Create image gallery
gallery = ImageGallery(
    image_folder="path/to/images",
    thumbnail_size=240,
    window_geometry=(100, 100, 900, 600)
)

# Connect signals
gallery.image_selected.connect(lambda path, idx: print(f"Selected: {path}"))
gallery.selection_changed.connect(lambda indices: print(f"Selection: {indices}"))

gallery.show()
sys.exit(app.exec())
```

### ImageThumbnail Example

```python
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from gui_pyqt_widgets import ImageThumbnail

app = QApplication(sys.argv)
window = QMainWindow()
widget = QWidget()
layout = QVBoxLayout(widget)

# Create thumbnail
thumbnail = ImageThumbnail(
    image_path="path/to/image.jpg",
    index=0,
    size=200,
    show_filename=True
)

# Connect signals
thumbnail.clicked.connect(lambda idx: print(f"Clicked thumbnail {idx}"))
thumbnail.selection_changed.connect(lambda idx, sel: print(f"Selection changed: {sel}"))

layout.addWidget(thumbnail)
window.setCentralWidget(widget)
window.show()
sys.exit(app.exec())
```

### ImageViewer Example

```python
from gui_pyqt_widgets import ImageViewer

# List of image paths
image_paths = ["image1.jpg", "image2.jpg", "image3.jpg"]

# Create viewer
viewer = ImageViewer(image_paths, current_index=0)

# Connect signals
viewer.image_changed.connect(lambda idx: print(f"Now viewing image {idx}"))
viewer.closed.connect(lambda: print("Viewer closed"))

viewer.show()
```

### FolderImageGallery Example

```python
from gui_pyqt_widgets import FolderImageGallery

# List of folder paths
folder_paths = ["folder1", "folder2", "folder3"]

# Create folder gallery
folder_gallery = FolderImageGallery(
    folder_paths=folder_paths,
    thumbnail_size=240,
    window_geometry=(150, 150, 800, 500)
)

# Connect signals
folder_gallery.folder_selected.connect(lambda path: print(f"Selected folder: {path}"))
folder_gallery.folder_opened.connect(lambda path: print(f"Opened folder: {path}"))

folder_gallery.show()
```

### VimTable Example

```python
from gui_pyqt_widgets import VimTable

# Create table with columns
table = VimTable(
    columns=["Name", "Age", "City"],
    zebra_stripes=True,
    on_cell_edit=lambda row, col, old, new: print(f"Cell edited: {old} -> {new}")
)

# Add some data
table.add_row(["Alice", "25", "New York"])
table.add_row(["Bob", "30", "London"])
table.add_row(["Charlie", "35", "Tokyo"])

table.show()
```

## Running the Demo

```bash
cd examples
python image_gallery_demo.py
```

The demo creates a test environment and showcases all components with interactive examples.

## Design Principles

These components follow the principles of **high cohesion and low coupling**:

### High Cohesion

- Each component has a single, well-defined responsibility
- All methods and properties within a component work together toward the same goal
- Clear, focused APIs that are easy to understand and use
- Self-contained functionality with minimal external dependencies

### Low Coupling

- Components can be used independently without requiring others
- Minimal dependencies between components
- Clear interfaces using Qt signals and slots for communication
- Components communicate through well-defined events
- Easy to extend and customize without affecting other components
- No hardcoded dependencies on specific applications

### Reusability Features

- **Configurable**: Extensive customization through constructor parameters
- **Styleable**: Full styling support through Qt stylesheets and CSS
- **Event-driven**: Rich signal system for integration with any application
- **Modular**: Each component can be used standalone or in combination
- **Extensible**: Easy to inherit and extend for specific needs

## Requirements

- Python >= 3.12
- PySide6 >= 6.9.1

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.