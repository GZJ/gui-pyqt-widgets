"""GUI PyQt Widgets - A collection of reusable PySide6 GUI components."""

from .vim_table import VimTable, VimTableInputDialog
from .vim_list import VimList, VimListInputDialog
from .image_thumbnail import ImageThumbnail
from .image_viewer import ImageViewer
from .image_gallery import ImageGallery
from .folder_image_gallery import FolderImageGallery

__version__ = "0.1.0"
__all__ = [
    "VimTable", 
    "VimTableInputDialog",
    "VimList",
    "VimListInputDialog",
    "ImageThumbnail",
    "ImageViewer", 
    "ImageGallery",
    "FolderImageGallery"
]
