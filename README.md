# GUI PyQt Widgets

A collection of reusable PySide6 GUI components with vim-style functionality.

## Overview

This project provides a set of advanced GUI widgets built with PySide6, focusing on keyboard-driven interfaces inspired by vim editor commands. The main component is `VimTable`, which offers an efficient table editing experience with vim-style navigation and commands.


## Features

- **VimTable**: Advanced table widget with vim-style navigation and editing
  - Modal editing (Normal/Insert/Visual modes)
  - Vim-style keybindings (h/j/k/l navigation, i/a/o for insert modes)
  - Row/column manipulation (dd for delete, yy for copy, p for paste)
  - Visual mode for selection (v for cell selection, V for row selection)
  - Cell editing with custom dialogs
  - Signal system for integration (cell_edited signal)
  - Customizable styling and behavior
  - Zebra stripe support for better readability

## Requirements

- Python 3.12+
- PySide6 6.9.1+

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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.