#!/usr/bin/env python3
"""
Nonogram Logic Puzzle Creator & Player  —  v4.0
A PySide6 desktop application for creating, editing, solving, and exporting Nonogram puzzles.

v4.0 additions:
  - Keyboard cell navigation (arrow keys + Space/X/Delete)
  - Step-by-step solver animation (reveals cells one by one)
  - Rotate 90 CW / CCW grid content
  - Shift rows/cols cyclically (up/down/left/right)
  - Drag-and-drop .json file loading
  - Puzzle Collection save/load (.ncol format, multiple puzzles)
  - Import puzzle from text (#/. grid format)
  - Undo/Redo history display
  - Cell count indicators per row/col in play mode
  - Everything from v3.0 preserved
"""

import os, sys, json, time, random, copy, math
from pathlib import Path

# Ensure EGL library is found (needed by Qt on some systems)
_ld_path = os.path.expanduser("~/.local/lib")
if os.path.isdir(_ld_path):
    os.environ.setdefault("LD_LIBRARY_PATH", "")
    if _ld_path not in os.environ["LD_LIBRARY_PATH"]:
        os.environ["LD_LIBRARY_PATH"] = _ld_path + ":" + os.environ["LD_LIBRARY_PATH"]

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QSpinBox, QFileDialog,
    QMessageBox, QScrollArea, QFrame, QSplitter, QStatusBar,
    QMenuBar, QMenu, QToolBar, QSizePolicy, QCheckBox, QComboBox,
    QGroupBox, QDialog, QDialogButtonBox, QLineEdit, QFormLayout,
    QSlider, QProgressBar, QListWidget, QListWidgetItem, QTextEdit,
    QAbstractItemView, QToolButton
)
from PySide6.QtCore import Qt, QSize, Signal, QRectF, QTimer, QPointF, QRect, QPropertyAnimation, QEasingCurve
from PySide6.QtCore import Qt, QSize, Signal, QRectF, QTimer, QPointF, QRect, QPropertyAnimation, QEasingCurve, QMimeData
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QIcon,
    QAction, QKeySequence, QCursor, QPixmap, QPainterPath,
    QShortcut, QUndoCommand, QUndoStack, QImage, QPicture
)

# Try to import PIL for image import
try:
    from PIL import Image as PILImage
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


# ════════════════════════════════════════════════════════════════════════════════
# SAMPLE PUZZLES LIBRARY — 30+ puzzles in 6 categories
# ════════════════════════════════════════════════════════════════════════════════

SAMPLE_PUZZLES = {
    # ── Animals ──────────────────────────────────────────────────────────────
    "Animals: Heart": {
        "title": "Heart", "category": "Animals", "difficulty": "Easy",
        "description": "A classic heart shape",
        "rows": 5, "cols": 5,
        "solution": [
            [0,1,0,1,0],[1,1,1,1,1],[1,1,1,1,1],[0,1,1,1,0],[0,0,1,0,0],
        ]
    },
    "Animals: Fish": {
        "title": "Fish", "category": "Animals", "difficulty": "Easy",
        "description": "A simple fish swimming right",
        "rows": 7, "cols": 7,
        "solution": [
            [0,0,1,0,0,0,0],[0,0,1,1,1,1,0],[1,1,1,1,1,1,1],[1,1,1,1,1,1,1],[1,1,1,1,1,1,1],[0,0,1,1,1,1,0],[0,0,1,0,0,0,0],
        ]
    },
    "Animals: Cat": {
        "title": "Cat", "category": "Animals", "difficulty": "Hard",
        "description": "A cat face with pointy ears",
        "rows": 10, "cols": 10,
        "solution": [
            [1,0,0,0,0,0,0,0,0,1],[1,1,0,0,0,0,0,0,1,1],[1,1,1,1,1,1,1,1,1,1],
            [1,0,1,0,1,1,0,1,0,1],[1,1,1,1,1,1,1,1,1,1],[0,1,0,1,0,0,1,0,1,0],
            [0,1,1,1,1,1,1,1,1,0],[0,0,1,0,1,1,0,1,0,0],[0,0,0,1,1,1,1,0,0,0],[0,0,0,0,1,1,0,0,0,0],
        ]
    },
    "Animals: Dog": {
        "title": "Dog", "category": "Animals", "difficulty": "Medium",
        "description": "A dog face with floppy ears",
        "rows": 10, "cols": 10,
        "solution": [
            [1,1,0,0,0,0,0,0,1,1],[1,1,1,0,0,0,0,1,1,1],[1,1,1,1,1,1,1,1,1,1],
            [1,1,0,1,1,1,1,0,1,1],[1,1,1,1,0,0,1,1,1,1],[1,1,1,1,1,1,1,1,1,1],
            [0,1,1,1,1,1,1,1,1,0],[0,0,1,1,0,0,1,1,0,0],[0,0,1,1,1,1,1,1,0,0],[0,0,0,1,1,1,1,0,0,0],
        ]
    },
    "Animals: Bird": {
        "title": "Bird", "category": "Animals", "difficulty": "Medium",
        "description": "A bird in flight",
        "rows": 9, "cols": 11,
        "solution": [
            [0,0,0,0,0,1,0,0,0,0,0],[0,0,0,0,1,1,1,0,0,0,0],[0,0,0,1,1,1,1,1,0,0,0],
            [0,0,1,1,1,1,1,1,1,0,0],[1,1,1,1,1,1,1,1,1,1,1],[0,0,1,1,1,1,1,1,1,0,0],
            [0,0,0,0,1,0,1,0,0,0,0],[0,0,0,0,0,1,0,0,0,0,0],[0,0,0,0,1,0,1,0,0,0,0],
        ]
    },
    "Animals: Rabbit": {
        "title": "Rabbit", "category": "Animals", "difficulty": "Medium",
        "description": "A cute bunny face",
        "rows": 10, "cols": 8,
        "solution": [
            [0,0,1,1,1,1,0,0],[0,0,1,1,1,1,0,0],[0,0,1,0,0,1,0,0],[0,0,1,1,1,1,0,0],
            [0,1,1,1,1,1,1,0],[1,1,1,1,1,1,1,1],[1,1,0,1,1,0,1,1],[1,1,1,1,1,1,1,1],
            [0,1,1,0,0,1,1,0],[0,0,1,1,1,1,0,0],
        ]
    },

    # ── Objects ─────────────────────────────────────────────────────────────
    "Objects: House": {
        "title": "House", "category": "Objects", "difficulty": "Easy",
        "description": "A simple house with roof and door",
        "rows": 10, "cols": 10,
        "solution": [
            [0,0,0,0,1,1,0,0,0,0],[0,0,0,1,1,1,1,0,0,0],[0,0,1,1,1,1,1,1,0,0],
            [0,1,1,1,1,1,1,1,1,0],[1,1,1,1,1,1,1,1,1,1],[0,1,1,1,1,1,1,1,1,0],
            [0,1,1,0,0,0,0,1,1,0],[0,1,1,0,0,0,0,1,1,0],[0,1,1,0,0,0,0,1,1,0],[0,1,1,1,1,1,1,1,1,0],
        ]
    },
    "Objects: Anchor": {
        "title": "Anchor", "category": "Objects", "difficulty": "Hard",
        "description": "A ship's anchor",
        "rows": 10, "cols": 10,
        "solution": [
            [0,0,0,0,1,1,0,0,0,0],[0,0,0,1,1,1,1,0,0,0],[0,0,0,0,1,1,0,0,0,0],
            [0,0,0,0,1,1,0,0,0,0],[0,1,0,0,1,1,0,0,1,0],[1,1,1,0,1,1,0,1,1,1],
            [0,1,1,1,1,1,1,1,1,0],[0,0,1,1,1,1,1,1,0,0],[0,0,0,1,1,1,1,0,0,0],[0,0,1,1,0,0,1,1,0,0],
        ]
    },
    "Objects: Key": {
        "title": "Key", "category": "Objects", "difficulty": "Medium",
        "description": "An old-fashioned key",
        "rows": 10, "cols": 7,
        "solution": [
            [0,1,1,1,0,0,0],[1,1,0,1,1,0,0],[1,1,0,1,1,0,0],[1,1,1,1,0,0,0],
            [0,1,1,1,0,0,0],[0,0,1,0,0,0,0],[0,0,1,0,0,0,0],[0,0,1,0,1,0,0],
            [0,0,1,0,1,0,0],[0,0,1,0,1,0,0],
        ]
    },
    "Objects: Cup": {
        "title": "Cup", "category": "Objects", "difficulty": "Easy",
        "description": "A coffee cup with handle",
        "rows": 8, "cols": 7,
        "solution": [
            [1,1,1,1,1,1,1],[1,0,0,0,0,0,1],[1,0,0,0,0,0,1],[1,0,0,0,0,0,1],
            [1,0,0,0,0,0,1],[1,0,0,0,0,0,1],[1,1,1,1,1,0,0],[0,1,1,1,0,0,0],
        ]
    },
    "Objects: Umbrella": {
        "title": "Umbrella", "category": "Objects", "difficulty": "Medium",
        "description": "A rain umbrella",
        "rows": 10, "cols": 9,
        "solution": [
            [0,0,0,0,1,0,0,0,0],[0,0,0,1,1,1,0,0,0],[0,0,1,1,1,1,1,0,0],
            [0,1,1,1,1,1,1,1,0],[1,1,1,1,1,1,1,1,1],[0,0,0,0,1,0,0,0,0],
            [0,0,0,0,1,0,0,0,0],[0,0,0,0,1,0,0,0,0],[0,0,0,0,1,0,0,0,0],[0,0,0,1,1,1,0,0,0],
        ]
    },
    "Objects: Tree": {
        "title": "Tree", "category": "Objects", "difficulty": "Easy",
        "description": "A pine tree",
        "rows": 9, "cols": 7,
        "solution": [
            [0,0,0,1,0,0,0],[0,0,1,1,1,0,0],[0,1,1,1,1,1,0],[1,1,1,1,1,1,1],
            [0,1,1,1,1,1,0],[0,0,1,1,1,0,0],[0,0,0,1,0,0,0],[0,0,0,1,0,0,0],[0,0,1,1,1,0,0],
        ]
    },
    "Objects: Rocket": {
        "title": "Rocket", "category": "Objects", "difficulty": "Medium",
        "description": "A rocket ship blasting off",
        "rows": 10, "cols": 7,
        "solution": [
            [0,0,0,1,0,0,0],[0,0,1,1,1,0,0],[0,0,1,1,1,0,0],[0,1,1,1,1,1,0],
            [0,1,1,1,1,1,0],[0,1,1,1,1,1,0],[1,1,0,1,0,1,1],[1,0,0,1,0,0,1],
            [0,0,0,1,0,0,0],[0,0,1,0,1,0,0],
        ]
    },

    # ── Symbols ─────────────────────────────────────────────────────────────
    "Symbols: Star": {
        "title": "Star", "category": "Symbols", "difficulty": "Hard",
        "description": "A five-pointed star",
        "rows": 9, "cols": 9,
        "solution": [
            [0,0,0,0,1,0,0,0,0],[0,0,0,1,1,1,0,0,0],[0,0,0,1,1,1,0,0,0],
            [1,1,1,1,1,1,1,1,1],[0,1,1,1,1,1,1,1,0],[0,0,1,1,1,1,1,0,0],
            [0,1,1,0,0,0,1,1,0],[0,1,0,0,0,0,0,1,0],[1,0,0,0,0,0,0,0,1],
        ]
    },
    "Symbols: Smiley": {
        "title": "Smiley", "category": "Symbols", "difficulty": "Medium",
        "description": "A smiling face",
        "rows": 7, "cols": 7,
        "solution": [
            [0,0,1,1,1,0,0],[0,1,0,0,0,1,0],[1,0,1,0,1,0,1],[1,0,0,0,0,0,1],
            [1,0,1,0,1,0,1],[0,1,0,1,0,1,0],[0,0,1,1,1,0,0],
        ]
    },
    "Symbols: Diamond": {
        "title": "Diamond", "category": "Symbols", "difficulty": "Easy",
        "description": "A diamond shape",
        "rows": 7, "cols": 7,
        "solution": [
            [0,0,0,1,0,0,0],[0,0,1,1,1,0,0],[0,1,1,1,1,1,0],[1,1,1,1,1,1,1],
            [0,1,1,1,1,1,0],[0,0,1,1,1,0,0],[0,0,0,1,0,0,0],
        ]
    },
    "Symbols: Arrow": {
        "title": "Arrow", "category": "Symbols", "difficulty": "Easy",
        "description": "A right-pointing arrow",
        "rows": 7, "cols": 7,
        "solution": [
            [0,0,0,1,0,0,0],[0,0,0,1,1,0,0],[0,0,0,1,1,1,0],[1,1,1,1,1,1,1],
            [0,0,0,1,1,1,0],[0,0,0,1,1,0,0],[0,0,0,1,0,0,0],
        ]
    },
    "Symbols: Music Note": {
        "title": "Music Note", "category": "Symbols", "difficulty": "Medium",
        "description": "A musical note",
        "rows": 10, "cols": 7,
        "solution": [
            [0,0,0,0,1,1,0],[0,0,0,0,1,1,0],[0,0,0,0,1,0,0],[0,0,0,0,1,0,0],
            [0,0,0,0,1,0,0],[0,0,0,0,1,0,0],[1,0,0,0,1,0,0],[1,1,0,0,1,0,0],
            [1,1,1,0,1,0,0],[0,1,1,1,0,0,0],
        ]
    },
    "Symbols: Crown": {
        "title": "Crown", "category": "Symbols", "difficulty": "Medium",
        "description": "A royal crown",
        "rows": 7, "cols": 9,
        "solution": [
            [1,0,0,0,0,0,0,0,1],[1,1,0,0,0,0,0,1,1],[1,1,1,0,0,0,1,1,1],
            [1,1,1,1,1,1,1,1,1],[0,1,1,1,1,1,1,1,0],[0,0,1,1,1,1,1,0,0],[0,0,0,1,1,1,0,0,0],
        ]
    },
    "Symbols: Peace": {
        "title": "Peace Sign", "category": "Symbols", "difficulty": "Hard",
        "description": "A peace sign in a circle",
        "rows": 11, "cols": 11,
        "solution": [
            [0,0,0,0,1,1,1,0,0,0,0],[0,0,1,1,1,1,1,1,1,0,0],[0,1,1,0,0,1,0,0,1,1,0],
            [1,1,0,0,0,1,0,0,0,1,1],[1,0,0,0,1,1,1,0,0,0,1],[1,0,0,0,1,1,1,0,0,0,1],
            [1,0,0,1,1,1,1,1,0,0,1],[1,1,0,0,0,1,0,0,0,1,1],[0,1,1,0,0,1,0,0,1,1,0],
            [0,0,1,1,1,1,1,1,1,0,0],[0,0,0,0,1,1,1,0,0,0,0],
        ]
    },
    "Symbols: Checkmark": {
        "title": "Checkmark", "category": "Symbols", "difficulty": "Easy",
        "description": "A check mark",
        "rows": 7, "cols": 7,
        "solution": [
            [0,0,0,0,0,1,0],[0,0,0,0,1,1,0],[0,0,0,0,1,1,0],[0,0,0,1,1,1,0],
            [0,1,1,1,1,0,0],[1,1,1,1,0,0,0],[0,1,1,0,0,0,0],
        ]
    },

    # ── Letters ─────────────────────────────────────────────────────────────
    "Letters: A": {
        "title": "Letter A", "category": "Letters", "difficulty": "Medium",
        "description": "The letter A",
        "rows": 7, "cols": 5,
        "solution": [
            [0,1,1,1,0],[1,1,0,1,1],[1,1,0,1,1],[1,1,1,1,1],[1,1,0,1,1],
            [1,1,0,1,1],[1,1,0,1,1],
        ]
    },
    "Letters: Z": {
        "title": "Letter Z", "category": "Letters", "difficulty": "Easy",
        "description": "The letter Z",
        "rows": 7, "cols": 5,
        "solution": [
            [1,1,1,1,1],[0,0,0,1,1],[0,0,1,1,0],[0,1,1,0,0],[1,1,0,0,0],
            [1,1,0,0,0],[1,1,1,1,1],
        ]
    },
    "Letters: F": {
        "title": "Letter F", "category": "Letters", "difficulty": "Easy",
        "description": "The letter F",
        "rows": 7, "cols": 5,
        "solution": [
            [1,1,1,1,1],[1,1,0,0,0],[1,1,0,0,0],[1,1,1,1,0],[1,1,0,0,0],
            [1,1,0,0,0],[1,1,0,0,0],
        ]
    },
    "Letters: Hi": {
        "title": "HI Text", "category": "Letters", "difficulty": "Medium",
        "description": "The word HI in block letters",
        "rows": 5, "cols": 7,
        "solution": [
            [1,0,1,0,1,1,1],[1,0,1,0,1,0,1],[1,1,1,0,1,0,1],[1,0,1,0,1,0,1],[1,0,1,0,1,1,1],
        ]
    },
    "Letters: OK": {
        "title": "OK Text", "category": "Letters", "difficulty": "Medium",
        "description": "The word OK in block letters",
        "rows": 5, "cols": 9,
        "solution": [
            [1,1,1,1,0,1,1,1,0],[1,1,0,1,0,1,0,1,0],[1,1,0,1,0,1,0,1,0],[1,1,0,1,0,1,0,1,0],[1,1,1,1,0,1,1,1,0],
        ]
    },

    # ── Patterns ────────────────────────────────────────────────────────────
    "Patterns: Cross": {
        "title": "Cross", "category": "Patterns", "difficulty": "Easy",
        "description": "A plus/cross pattern",
        "rows": 7, "cols": 7,
        "solution": [
            [0,0,1,1,1,0,0],[0,0,1,1,1,0,0],[1,1,1,1,1,1,1],[1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1],[0,0,1,1,1,0,0],[0,0,1,1,1,0,0],
        ]
    },
    "Patterns: Border": {
        "title": "Border", "category": "Patterns", "difficulty": "Easy",
        "description": "A rectangular border frame",
        "rows": 8, "cols": 10,
        "solution": [
            [1,1,1,1,1,1,1,1,1,1],[1,0,0,0,0,0,0,0,0,1],[1,0,0,0,0,0,0,0,0,1],
            [1,0,0,0,0,0,0,0,0,1],[1,0,0,0,0,0,0,0,0,1],[1,0,0,0,0,0,0,0,0,1],
            [1,0,0,0,0,0,0,0,0,1],[1,1,1,1,1,1,1,1,1,1],
        ]
    },
    "Patterns: Checkerboard": {
        "title": "Checkerboard", "category": "Patterns", "difficulty": "Medium",
        "description": "A classic checkerboard pattern",
        "rows": 8, "cols": 8,
        "solution": [
            [1,0,1,0,1,0,1,0],[0,1,0,1,0,1,0,1],[1,0,1,0,1,0,1,0],[0,1,0,1,0,1,0,1],
            [1,0,1,0,1,0,1,0],[0,1,0,1,0,1,0,1],[1,0,1,0,1,0,1,0],[0,1,0,1,0,1,0,1],
        ]
    },
    "Patterns: Spiral": {
        "title": "Spiral", "category": "Patterns", "difficulty": "Hard",
        "description": "A square spiral",
        "rows": 11, "cols": 11,
        "solution": [
            [1,1,1,1,1,1,1,1,1,1,1],[1,0,0,0,0,0,0,0,0,0,1],[1,0,1,1,1,1,1,1,1,0,1],
            [1,0,1,0,0,0,0,0,1,0,1],[1,0,1,0,1,1,1,0,1,0,1],[1,0,1,0,1,0,1,0,1,0,1],
            [1,0,1,0,1,1,1,0,1,0,1],[1,0,1,0,0,0,0,0,1,0,1],[1,0,1,1,1,1,1,1,1,0,1],
            [1,0,0,0,0,0,0,0,0,0,1],[1,1,1,1,1,1,1,1,1,1,1],
        ]
    },
    "Patterns: Stairs": {
        "title": "Staircase", "category": "Patterns", "difficulty": "Easy",
        "description": "Ascending stairs",
        "rows": 8, "cols": 8,
        "solution": [
            [1,0,0,0,0,0,0,0],[1,1,0,0,0,0,0,0],[0,1,1,0,0,0,0,0],[0,0,1,1,0,0,0,0],
            [0,0,0,1,1,0,0,0],[0,0,0,0,1,1,0,0],[0,0,0,0,0,1,1,0],[0,0,0,0,0,0,1,1],
        ]
    },

    # ── Scenes ──────────────────────────────────────────────────────────────
    "Scenes: Mushroom": {
        "title": "Mushroom", "category": "Scenes", "difficulty": "Medium",
        "description": "A red mushroom",
        "rows": 10, "cols": 9,
        "solution": [
            [0,0,0,0,1,1,0,0,0],[0,0,0,1,1,1,1,0,0],[0,0,1,1,1,1,1,1,0],
            [0,1,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,1,1],[0,0,0,1,1,0,0,0,0],
            [0,0,0,1,1,0,0,0,0],[0,0,0,1,1,0,0,0,0],[0,0,1,1,1,1,0,0,0],[0,0,1,1,1,1,0,0,0],
        ]
    },
    "Scenes: Boat": {
        "title": "Sailboat", "category": "Scenes", "difficulty": "Medium",
        "description": "A sailboat on water",
        "rows": 10, "cols": 9,
        "solution": [
            [0,0,0,0,1,0,0,0,0],[0,0,0,1,1,0,0,0,0],[0,0,1,1,1,0,0,0,0],
            [0,1,1,1,1,0,0,0,0],[1,1,1,1,1,0,0,0,0],[0,0,0,1,1,0,0,0,0],
            [0,0,1,1,1,1,1,0,0],[0,1,1,1,1,1,1,1,0],[1,1,0,0,0,0,0,1,1],
            [1,1,0,0,0,0,0,1,1],
        ]
    },
    "Scenes: Heart Lock": {
        "title": "Heart Lock", "category": "Scenes", "difficulty": "Hard",
        "description": "A padlock with heart shape",
        "rows": 10, "cols": 8,
        "solution": [
            [0,1,1,0,0,1,1,0],[1,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,1],[0,1,1,1,1,1,1,0],
            [0,0,1,1,1,1,0,0],[0,0,0,1,1,0,0,0],[0,0,0,1,1,0,0,0],[0,0,1,1,1,1,0,0],
            [0,0,1,1,1,1,0,0],[0,0,1,1,1,1,0,0],
        ]
    },
    "Scenes: Gift Box": {
        "title": "Gift Box", "category": "Scenes", "difficulty": "Easy",
        "description": "A present/gift box with ribbon",
        "rows": 8, "cols": 9,
        "solution": [
            [1,1,1,1,1,1,1,1,1],[1,0,1,1,1,1,1,0,1],[1,0,1,0,1,0,1,0,1],[1,0,1,0,1,0,1,0,1],
            [1,0,1,0,1,0,1,0,1],[1,0,1,1,1,1,1,0,1],[1,1,1,1,1,1,1,1,1],[0,0,1,1,1,1,1,0,0],
        ]
    },
    "Scenes: Snowman": {
        "title": "Snowman", "category": "Scenes", "difficulty": "Medium",
        "description": "A snowman with hat",
        "rows": 11, "cols": 7,
        "solution": [
            [0,0,1,1,1,0,0],[1,1,1,1,1,1,1],[0,0,1,1,1,0,0],[0,0,0,1,0,0,0],
            [0,0,1,1,1,0,0],[0,1,1,1,1,1,0],[0,0,1,1,1,0,0],[1,1,1,1,1,1,1],
            [0,1,1,1,1,1,0],[0,0,1,1,1,0,0],[0,0,0,1,0,0,0],
        ]
    },
    "Scenes: Flower": {
        "title": "Flower", "category": "Scenes", "difficulty": "Medium",
        "description": "A flower with stem and leaves",
        "rows": 10, "cols": 7,
        "solution": [
            [0,0,1,1,1,0,0],[0,1,1,1,1,1,0],[1,1,0,1,0,1,1],[0,1,1,1,1,1,0],
            [0,0,0,1,0,0,0],[0,0,0,1,0,0,0],[0,0,1,1,0,0,0],[0,1,1,0,0,0,0],
            [1,1,0,0,0,0,0],[1,0,0,0,0,0,0],
        ]
    },
}


# ════════════════════════════════════════════════════════════════════════════════
# UNDO SYSTEM
# ════════════════════════════════════════════════════════════════════════════════

class GridChangeCommand(QUndoCommand):
    def __init__(self, model, row, col, old_val, new_val, desc="Cell Change"):
        super().__init__(desc)
        self.model, self.row, self.col = model, row, col
        self.old_val, self.new_val = old_val, new_val

    def undo(self):
        g = self.model.player_grid if self.model._play_mode_active else self.model.solution
        g[self.row][self.col] = self.old_val

    def redo(self):
        g = self.model.player_grid if self.model._play_mode_active else self.model.solution
        g[self.row][self.col] = self.new_val


class BatchGridCommand(QUndoCommand):
    def __init__(self, model, changes, desc="Batch Change"):
        super().__init__(desc)
        self.model, self.changes = model, changes

    def undo(self):
        g = self.model.player_grid if self.model._play_mode_active else self.model.solution
        for r, c, old, _ in self.changes: g[r][c] = old

    def redo(self):
        g = self.model.player_grid if self.model._play_mode_active else self.model.solution
        for r, c, _, new in self.changes: g[r][c] = new




class ModelSnapshotCommand(QUndoCommand):
    """Undo command that saves/restores full model state (for rotate/shift)."""
    def __init__(self, model, old_state, new_state, desc="Model Change"):
        super().__init__(desc)
        self.model = model
        self.old_state = old_state
        self.new_state = new_state

    def undo(self):
        r, c, sol, pg = self.old_state
        self.model.rows, self.model.cols = r, c
        self.model.solution = copy.deepcopy(sol)
        self.model.player_grid = copy.deepcopy(pg)

    def redo(self):
        r, c, sol, pg = self.new_state
        self.model.rows, self.model.cols = r, c
        self.model.solution = copy.deepcopy(sol)
        self.model.player_grid = copy.deepcopy(pg)

# ════════════════════════════════════════════════════════════════════════════════
# Nonogram Model
# ════════════════════════════════════════════════════════════════════════════════

class NonogramModel:
    EMPTY, FILLED, MARKED = 0, 1, 2

    def __init__(self, rows=10, cols=10):
        self.rows, self.cols = rows, cols
        self.solution = [[self.EMPTY]*cols for _ in range(rows)]
        self.player_grid = [[self.EMPTY]*cols for _ in range(rows)]
        self._play_mode_active = False
        self.title = ""

    def clear_solution(self):
        self.solution = [[self.EMPTY]*self.cols for _ in range(self.rows)]

    def clear_player_grid(self):
        self.player_grid = [[self.EMPTY]*self.cols for _ in range(self.rows)]

    def resize(self, rows, cols):
        self.rows, self.cols = rows, cols
        self.solution = [[self.EMPTY]*cols for _ in range(rows)]
        self.player_grid = [[self.EMPTY]*cols for _ in range(rows)]

    def get_row_clues(self, row_idx, grid=None):
        row = (grid or self.solution)[row_idx]
        clues, count = [], 0
        for cell in row:
            if cell == self.FILLED: count += 1
            else:
                if count > 0: clues.append(count)
                count = 0
        if count > 0: clues.append(count)
        return clues if clues else [0]

    def get_col_clues(self, col_idx, grid=None):
        g = grid or self.solution
        clues, count = [], 0
        for r in range(self.rows):
            cell = g[r][col_idx]
            if cell == self.FILLED: count += 1
            else:
                if count > 0: clues.append(count)
                count = 0
        if count > 0: clues.append(count)
        return clues if clues else [0]

    def get_all_row_clues(self, grid=None):
        return [self.get_row_clues(r, grid) for r in range(self.rows)]

    def get_all_col_clues(self, grid=None):
        return [self.get_col_clues(c, grid) for c in range(self.cols)]

    def max_row_clue_len(self, grid=None):
        return max(len(c) for c in self.get_all_row_clues(grid))

    def max_col_clue_len(self, grid=None):
        return max(len(c) for c in self.get_all_col_clues(grid))

    def is_valid_solution(self):
        return any(cell == self.FILLED for row in self.solution for cell in row)

    def filled_count(self):
        return sum(cell == self.FILLED for row in self.solution for cell in row)

    def total_cells(self):
        return self.rows * self.cols

    def fill_percentage(self):
        return self.filled_count() / self.total_cells() * 100 if self.total_cells() else 0

    def difficulty_rating(self):
        if not self.is_valid_solution(): return "N/A"
        row_clues = self.get_all_row_clues()
        col_clues = self.get_all_col_clues()
        avg_clue_len = (sum(len(c) for c in row_clues) + sum(len(c) for c in col_clues)) / (self.rows + self.cols)
        fill = self.fill_percentage()
        size_factor = (self.rows * self.cols) / 100
        score = avg_clue_len * 0.4 + (fill / 100) * 0.3 + size_factor * 0.3
        if score < 0.4: return "Easy"
        elif score < 0.7: return "Medium"
        elif score < 1.0: return "Hard"
        else: return "Expert"

    def is_row_complete(self, row_idx):
        return self.get_row_clues(row_idx, self.player_grid) == self.get_row_clues(row_idx, self.solution)

    def is_col_complete(self, col_idx):
        return self.get_col_clues(col_idx, self.player_grid) == self.get_col_clues(col_idx, self.solution)

    def player_filled_count(self):
        return sum(cell == self.FILLED for row in self.player_grid for cell in row)

    def player_progress(self):
        total = self.filled_count()
        if total == 0: return 0
        correct = sum(1 for r in range(self.rows) for c in range(self.cols)
                      if self.solution[r][c] == self.FILLED and self.player_grid[r][c] == self.FILLED)
        return correct / total * 100

    def check_player_solution(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if (self.solution[r][c] == self.FILLED) != (self.player_grid[r][c] == self.FILLED):
                    return False
        return True

    def get_errors(self):
        """Return list of (r,c) where player is wrong."""
        errors = []
        for r in range(self.rows):
            for c in range(self.cols):
                sol_filled = self.solution[r][c] == self.FILLED
                pl_filled = self.player_grid[r][c] == self.FILLED
                if sol_filled != pl_filled:
                    errors.append((r, c))
        return errors

    def get_hint(self):
        """Return a random unfilled correct cell for hint."""
        candidates = []
        for r in range(self.rows):
            for c in range(self.cols):
                if (self.solution[r][c] == self.FILLED and
                    self.player_grid[r][c] != self.FILLED):
                    candidates.append((r, c))
        if candidates:
            return random.choice(candidates)
        return None

    def to_dict(self):
        return {"title": self.title or f"Nonogram {self.rows}x{self.cols}",
                "rows": self.rows, "cols": self.cols, "solution": self.solution}

    def from_dict(self, data):
        self.rows, self.cols = data["rows"], data["cols"]
        self.solution = data["solution"]
        self.title = data.get("title", "")
        self.player_grid = [[self.EMPTY]*self.cols for _ in range(self.rows)]

    def rotate_cw(self):
        """Rotate grid 90 degrees clockwise. Swaps rows/cols."""
        R, C = self.rows, self.cols
        new_sol = [[self.EMPTY]*R for _ in range(C)]
        new_pg = [[self.EMPTY]*R for _ in range(C)]
        for r in range(R):
            for c in range(C):
                new_sol[c][R-1-r] = self.solution[r][c]
                new_pg[c][R-1-r] = self.player_grid[r][c]
        self.rows, self.cols = C, R
        self.solution, self.player_grid = new_sol, new_pg

    def rotate_ccw(self):
        """Rotate grid 90 degrees counter-clockwise. Swaps rows/cols."""
        R, C = self.rows, self.cols
        new_sol = [[self.EMPTY]*R for _ in range(C)]
        new_pg = [[self.EMPTY]*R for _ in range(C)]
        for r in range(R):
            for c in range(C):
                new_sol[C-1-c][r] = self.solution[r][c]
                new_pg[C-1-c][r] = self.player_grid[r][c]
        self.rows, self.cols = C, R
        self.solution, self.player_grid = new_sol, new_pg

    def shift_rows(self, direction=1):
        """Shift rows cyclically. direction: 1=down, -1=up."""
        if direction == 1:
            self.solution.insert(0, self.solution.pop())
            self.player_grid.insert(0, self.player_grid.pop())
        else:
            self.solution.append(self.solution.pop(0))
            self.player_grid.append(self.player_grid.pop(0))

    def shift_cols(self, direction=1):
        """Shift cols cyclically. direction: 1=right, -1=left."""
        if direction == 1:
            for r in range(self.rows):
                self.solution[r].insert(0, self.solution[r].pop())
                self.player_grid[r].insert(0, self.player_grid[r].pop())
        else:
            for r in range(self.rows):
                self.solution[r].append(self.solution[r].pop(0))
                self.player_grid[r].append(self.player_grid[r].pop(0))

    def snapshot(self):
        """Return a snapshot of the current model state for undo."""
        return (self.rows, self.cols, copy.deepcopy(self.solution), copy.deepcopy(self.player_grid))


# ════════════════════════════════════════════════════════════════════════════════
# AUTO-SOLVER
# ════════════════════════════════════════════════════════════════════════════════

class NonogramSolver:
    @staticmethod
    def _generate_line_possibilities(clues, length):
        if clues == [0]: return [[NonogramModel.EMPTY]*length]
        results = []
        NonogramSolver._backtrack_line(clues, length, [], results)
        return results

    @staticmethod
    def _backtrack_line(clues, length, current, results):
        if not clues:
            remaining = length - len(current)
            if remaining >= 0: results.append(current + [NonogramModel.EMPTY]*remaining)
            return
        c, rest = clues[0], clues[1:]
        needed = sum(rest) + len(rest)
        max_start = length - c - needed
        for start in range(len(current), max_start + 1):
            padding = [NonogramModel.EMPTY]*(start - len(current))
            block = [NonogramModel.FILLED]*c
            gap = [NonogramModel.EMPTY] if rest else []
            NonogramSolver._backtrack_line(rest, length, current + padding + block + gap, results)

    @staticmethod
    def _solve_line(clues, line):
        possibilities = NonogramSolver._generate_line_possibilities(clues, len(line))
        if not possibilities: return None
        valid = [p for p in possibilities
                 if all(line[i] == NonogramModel.EMPTY or line[i] == p[i] for i in range(len(line)))]
        if not valid: return None
        result = list(line)
        for i in range(len(line)):
            if result[i] != NonogramModel.EMPTY: continue
            vals = set(p[i] for p in valid)
            if len(vals) == 1: result[i] = vals.pop()
        return result if result != line else None

    @staticmethod
    def solve(model):
        grid = [[NonogramModel.EMPTY]*model.cols for _ in range(model.rows)]
        row_clues = model.get_all_row_clues()
        col_clues = model.get_all_col_clues()
        for _ in range(max(model.rows, model.cols) * 3):
            progress = False
            for r in range(model.rows):
                result = NonogramSolver._solve_line(row_clues[r], grid[r])
                if result is not None: grid[r] = result; progress = True
            for c in range(model.cols):
                col = [grid[r][c] for r in range(model.rows)]
                result = NonogramSolver._solve_line(col_clues[c], col)
                if result is not None:
                    for r in range(model.rows): grid[r][c] = result[r]
                    progress = True
            if not progress: break
        sol_rc = model.get_all_row_clues()
        sol_cc = model.get_all_col_clues()
        grid_rc = [NonogramModel.get_row_clues(model, r, grid) for r in range(model.rows)]
        grid_cc = [NonogramModel.get_col_clues(model, c, grid) for c in range(model.cols)]
        model.player_grid = grid
        return grid_rc == sol_rc and grid_cc == sol_cc


# ════════════════════════════════════════════════════════════════════════════════
# CONFETTI WIDGET
# ════════════════════════════════════════════════════════════════════════════════

class ConfettiWidget(QWidget):
    """Overlay widget that shows a confetti celebration animation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.particles = []
        self._timer = QTimer(self)
        self._timer.setInterval(30)
        self._timer.timeout.connect(self._tick)
        self._frame = 0
        self._max_frames = 120  # ~4 seconds at 30fps

    def start(self):
        self.particles = []
        w, h = self.parent().width(), self.parent().height()
        colors = [
            QColor(255, 99, 132), QColor(54, 162, 235), QColor(255, 206, 86),
            QColor(75, 192, 192), QColor(153, 102, 255), QColor(255, 159, 64),
            QColor(46, 204, 113), QColor(231, 76, 60), QColor(52, 152, 219),
        ]
        for _ in range(150):
            self.particles.append({
                'x': random.uniform(0, w), 'y': random.uniform(-h, 0),
                'vx': random.uniform(-3, 3), 'vy': random.uniform(2, 6),
                'size': random.uniform(4, 10),
                'color': random.choice(colors),
                'rotation': random.uniform(0, 360),
                'rot_speed': random.uniform(-10, 10),
                'shape': random.choice(['rect', 'circle']),
            })
        self._frame = 0
        self.setGeometry(0, 0, w, h)
        self.raise_()
        self.show()
        self._timer.start()

    def _tick(self):
        self._frame += 1
        if self._frame >= self._max_frames:
            self._timer.stop()
            self.hide()
            self.deleteLater()
            return
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += 0.1  # gravity
            p['rotation'] += p['rot_speed']
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        alpha = max(0, 255 - int(255 * self._frame / self._max_frames))
        for p in self.particles:
            c = QColor(p['color'])
            c.setAlpha(alpha)
            painter.save()
            painter.translate(p['x'], p['y'])
            painter.rotate(p['rotation'])
            painter.setBrush(QBrush(c))
            painter.setPen(Qt.NoPen)
            s = p['size']
            if p['shape'] == 'rect':
                painter.drawRect(QRectF(-s/2, -s/2, s, s*1.5))
            else:
                painter.drawEllipse(QRectF(-s/2, -s/2, s, s))
            painter.restore()
        painter.end()


# ════════════════════════════════════════════════════════════════════════════════
# Nonogram Grid Widget
# ════════════════════════════════════════════════════════════════════════════════

FILL_COLORS = [
    ("Blue", QColor(37, 99, 235)),
    ("Red", QColor(220, 38, 38)),
    ("Green", QColor(22, 163, 74)),
    ("Purple", QColor(124, 58, 237)),
    ("Orange", QColor(234, 88, 12)),
    ("Teal", QColor(13, 148, 136)),
    ("Pink", QColor(219, 39, 119)),
    ("Black", QColor(30, 41, 59)),
]

class NonogramGridWidget(QWidget):
    cellChanged = Signal(int, int, int, int)
    batchChanged = Signal(list)
    gridChanged = Signal()

    def __init__(self, model, undo_stack, parent=None):
        super().__init__(parent)
        self.model, self.undo_stack = model, undo_stack
        self.cell_size = 36
        self.zoom_level = 1.0
        self.mode = "create"
        self._hover_cell = (-1, -1)
        self._dragging = False
        self._drag_button = None
        self._drag_value = None
        self._drag_changes = []
        self.dark_mode = False
        self.show_cross_highlight = True
        self.show_completed_clues = True
        self.show_coordinates = False
        self.show_errors = False  # error highlighting in play mode
        self.show_cell_counts = True  # cell count indicators
        self._error_cells = set()
        self.fill_color_idx = 0
        self._selected_cell = (0, 0)
        self._show_selection = False
        self._step_highlight = set()
        self.setMinimumSize(200, 200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

    @property
    def fill_color(self):
        return FILL_COLORS[self.fill_color_idx][1]

    def set_zoom(self, level):
        self.zoom_level = max(0.4, min(3.0, level)); self.update()

    def zoom_in(self): self.set_zoom(self.zoom_level + 0.15)
    def zoom_out(self): self.set_zoom(self.zoom_level - 0.15)
    def zoom_fit(self): self.zoom_level = 1.0; self.update()

    def update_cell_size(self):
        mrc = self.model.max_row_clue_len()
        mcc = self.model.max_col_clue_len()
        cml = mrc * 22 + 16
        cmt = mcc * 22 + 16
        coord_extra = 20 if self.show_coordinates else 0
        aw = max(self.width() - cml - 20 - coord_extra, 100)
        ah = max(self.height() - cmt - 20 - coord_extra, 100)
        cw = aw // self.model.cols
        ch = ah // self.model.rows
        base = max(min(cw, ch, 48), 14)
        self.cell_size = max(int(base * self.zoom_level), 10)

    def _get_offsets(self):
        mrc = self.model.max_row_clue_len()
        mcc = self.model.max_col_clue_len()
        ox = mrc * 22 + 16 + (20 if self.show_coordinates else 0)
        oy = mcc * 22 + 16 + (20 if self.show_coordinates else 0)
        return ox, oy

    def _cell_rect(self, r, c):
        ox, oy = self._get_offsets()
        return QRectF(ox + c*self.cell_size, oy + r*self.cell_size, self.cell_size, self.cell_size)

    def _hit_test(self, pos):
        ox, oy = self._get_offsets()
        c = int((pos.x() - ox) / self.cell_size)
        r = int((pos.y() - oy) / self.cell_size)
        return (r, c) if 0 <= r < self.model.rows and 0 <= c < self.model.cols else None

    def _colors(self):
        dm = self.dark_mode
        fc = self.fill_color
        return {
            "bg": QColor(30,30,40) if dm else QColor(245,245,248),
            "cell_empty": QColor(45,45,60) if dm else QColor(255,255,255),
            "cell_filled": fc,
            "cell_marked": QColor(55,55,70) if dm else QColor(229,231,235),
            "cell_marked_x": QColor(120,120,140) if dm else QColor(156,163,175),
            "cell_hover": QColor(59,130,246,60) if dm else QColor(37,99,235,40),
            "cell_error": QColor(239,68,68,120),
            "cross_highlight": QColor(255,255,255,15) if dm else QColor(37,99,235,12),
            "border": QColor(70,70,90) if dm else QColor(203,213,225),
            "border_thick": QColor(100,100,120) if dm else QColor(75,85,99),
            "border_outer": QColor(140,140,160) if dm else QColor(30,41,59),
            "clue_text": QColor(200,200,220) if dm else QColor(55,65,81),
            "clue_done": QColor(80,80,100) if dm else QColor(180,185,195),
            "corner_line": QColor(80,80,100) if dm else QColor(148,163,184),
            "coord_text": QColor(130,130,150) if dm else QColor(148,163,184),
        }

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)
        C = self._colors()
        self.update_cell_size()
        ox, oy = self._get_offsets()
        cs = self.cell_size

        painter.fillRect(self.rect(), C["bg"])

        # Cross-highlight
        hr, hc = self._hover_cell
        if self.show_cross_highlight and hr >= 0 and hc >= 0:
            painter.fillRect(QRectF(ox, oy+hr*cs, self.model.cols*cs, cs), C["cross_highlight"])
            painter.fillRect(QRectF(ox+hc*cs, oy, cs, self.model.rows*cs), C["cross_highlight"])

        # Coordinate labels
        if self.show_coordinates:
            coord_font = QFont("Segoe UI", max(int(8*self.zoom_level), 6))
            coord_font.setBold(False)
            painter.setFont(coord_font)
            painter.setPen(QPen(C["coord_text"]))
            for c in range(self.model.cols):
                cx = ox + c*cs + cs/2
                coord_x = ox - (20 if self.show_coordinates else 0) + 10
                painter.drawText(QRectF(coord_x - 10, oy + c*cs, 20, cs), Qt.AlignCenter, str(c+1))
            for r in range(self.model.rows):
                cy = oy + r*cs + cs/2
                coord_y = oy - (20 if self.show_coordinates else 0) + 10
                painter.drawText(QRectF(ox + r*cs, coord_y - 10, cs, 20), Qt.AlignCenter, str(r+1))

        # Column clues
        col_clues = self.model.get_all_col_clues()
        mccl = self.model.max_col_clue_len()
        fs = max(min(int(10*self.zoom_level), 14), 7)
        painter.setFont(QFont("Segoe UI", fs, QFont.Bold))
        for c, clues in enumerate(col_clues):
            done = self.mode == "play" and self.show_completed_clues and self.model.is_col_complete(c)
            cx = ox + c*cs + cs/2
            for i, num in enumerate(clues):
                cy = oy - (mccl-i)*22 + 10
                painter.setPen(QPen(C["clue_done"] if done else C["clue_text"]))
                painter.drawText(QRectF(cx-cs/2, cy, cs, 20), Qt.AlignCenter, str(num))


        # Cell count indicators in play mode (filled count per col)
        if self.mode == "play" and self.show_cell_counts:
            count_font = QFont("Segoe UI", max(int(7*self.zoom_level), 5))
            count_font.setItalic(True)
            painter.setFont(count_font)
            painter.setPen(QPen(QColor(100,116,139) if not self.dark_mode else QColor(108,112,134)))
            for c in range(self.model.cols):
                filled = sum(1 for r in range(self.model.rows) if self.model.player_grid[r][c] == NonogramModel.FILLED)
                cx = ox + c*self.cell_size + self.cell_size/2
                cy = oy - 2
                painter.drawText(QRectF(cx-self.cell_size/2, cy-mccl*22-14, self.cell_size, 12), Qt.AlignCenter, str(filled))

        # Row clues
        row_clues = self.model.get_all_row_clues()
        mrcl = self.model.max_row_clue_len()
        for r, clues in enumerate(row_clues):
            done = self.mode == "play" and self.show_completed_clues and self.model.is_row_complete(r)
            cy = oy + r*cs + cs/2
            for i, num in enumerate(clues):
                cx = ox - (mrcl-i)*22 + 10
                painter.setPen(QPen(C["clue_done"] if done else C["clue_text"]))
                painter.drawText(QRectF(cx, cy-10, 20, 20), Qt.AlignCenter, str(num))


        # Cell count indicators per row in play mode
        if self.mode == "play" and self.show_cell_counts:
            count_font = QFont("Segoe UI", max(int(7*self.zoom_level), 5))
            count_font.setItalic(True)
            painter.setFont(count_font)
            painter.setPen(QPen(QColor(100,116,139) if not self.dark_mode else QColor(108,112,134)))
            for r in range(self.model.rows):
                filled = sum(1 for c in range(self.model.cols) if self.model.player_grid[r][c] == NonogramModel.FILLED)
                cy = oy + r*self.cell_size + self.cell_size/2
                cx = ox - 2
                painter.drawText(QRectF(cx-mrcl*22-14, cy-6, 12, self.cell_size), Qt.AlignCenter, str(filled))

        # Grid cells
        grid = self.model.solution if self.mode == "create" else self.model.player_grid
        for r in range(self.model.rows):
            for c in range(self.model.cols):
                rect = self._cell_rect(r, c)
                val = grid[r][c]
                if val == NonogramModel.FILLED:
                    painter.fillRect(rect, C["cell_filled"])
                elif val == NonogramModel.MARKED:
                    painter.fillRect(rect, C["cell_marked"])
                    pen = QPen(C["cell_marked_x"], max(1, cs//16))
                    painter.setPen(pen)
                    m = max(cs//5, 4)
                    painter.drawLine(rect.topLeft()+QPointF(m,m), rect.bottomRight()-QPointF(m,m))
                    painter.drawLine(rect.topRight()+QPointF(-m,m), rect.bottomLeft()-QPointF(-m,m))
                else:
                    painter.fillRect(rect, C["cell_empty"])

                # Error highlight
                if self.show_errors and self.mode == "play" and (r, c) in self._error_cells:
                    painter.fillRect(rect, C["cell_error"])

                if r == hr and c == hc:
                    painter.fillRect(rect, C["cell_hover"])

                painter.setPen(QPen(C["border"], 1))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(rect)

        # Thick lines every 5
        painter.setPen(QPen(C["border_thick"], 2))
        for r in range(self.model.rows + 1):
            if r % 5 == 0:
                y = oy + r*cs
                painter.drawLine(int(ox), int(y), int(ox+self.model.cols*cs), int(y))
        for c in range(self.model.cols + 1):
            if c % 5 == 0:
                x = ox + c*cs
                painter.drawLine(int(x), int(oy), int(x), int(oy+self.model.rows*cs))

        # Outer border
        painter.setPen(QPen(C["border_outer"], 2.5))
        painter.drawRect(QRectF(ox, oy, self.model.cols*cs, self.model.rows*cs))

        # Corner lines
        painter.setPen(QPen(C["corner_line"], 1))
        painter.drawLine(int(ox), int(oy), int(ox), int(oy-mccl*22))
        painter.drawLine(int(ox), int(oy), int(ox-mrcl*22), int(oy))

        # Step-solve highlight (green glow on recently solved cells)
        if self._step_highlight:
            for (sr, sc) in self._step_highlight:
                rect = self._cell_rect(sr, sc)
                painter.setPen(QPen(QColor(34, 197, 94, 180), 2))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(rect.adjusted(1, 1, -1, -1))

        # Keyboard selection highlight
        if self._show_selection:
            sr, sc = self._selected_cell
            if 0 <= sr < self.model.rows and 0 <= sc < self.model.cols:
                rect = self._cell_rect(sr, sc)
                sel_color = QColor(59, 130, 246, 180) if not self.dark_mode else QColor(137, 180, 250, 180)
                painter.setPen(QPen(sel_color, 3))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(rect)
        painter.end()

    def set_error_cells(self, errors):
        self._error_cells = set(errors)
        self.update()

    def mousePressEvent(self, event):
        hit = self._hit_test(event.position())
        if hit is None: return
        row, col = hit
        self._dragging = True
        self._drag_button = event.button()
        self._drag_changes = []
        if event.button() == Qt.LeftButton:
            grid = self.model.solution if self.mode == "create" else self.model.player_grid
            old = grid[row][col]
            if self.mode == "create":
                new = NonogramModel.EMPTY if old == NonogramModel.FILLED else NonogramModel.FILLED
            else:
                new = NonogramModel.EMPTY if old == NonogramModel.FILLED else NonogramModel.FILLED
            self._drag_value = new
            grid[row][col] = new
            self._drag_changes.append((row, col, old, new))
        elif event.button() == Qt.RightButton and self.mode == "play":
            old = self.model.player_grid[row][col]
            new = NonogramModel.EMPTY if old == NonogramModel.MARKED else NonogramModel.MARKED
            self._drag_value = new
            self.model.player_grid[row][col] = new
            self._drag_changes.append((row, col, old, new))
        self.update()

    def mouseMoveEvent(self, event):
        hit = self._hit_test(event.position())
        if self._dragging and hit and self._drag_button:
            row, col = hit
            if self._drag_changes and self._drag_changes[-1][:2] == (row, col):
                self._hover_cell = (row, col); self.update(); return
            if self._drag_button == Qt.LeftButton:
                grid = self.model.solution if self.mode == "create" else self.model.player_grid
                old = grid[row][col]
                if old != self._drag_value:
                    grid[row][col] = self._drag_value
                    self._drag_changes.append((row, col, old, self._drag_value))
            elif self._drag_button == Qt.RightButton and self.mode == "play":
                old = self.model.player_grid[row][col]
                if old != self._drag_value:
                    self.model.player_grid[row][col] = self._drag_value
                    self._drag_changes.append((row, col, old, self._drag_value))
        self._hover_cell = hit if hit else (-1, -1)
        self.update()

    def mouseReleaseEvent(self, event):
        if self._dragging and self._drag_changes:
            if len(self._drag_changes) == 1:
                r, c, old, new = self._drag_changes[0]
                self.undo_stack.push(GridChangeCommand(self.model, r, c, old, new))
                self.cellChanged.emit(r, c, old, new)
            else:
                cmd = BatchGridCommand(self.model, list(self._drag_changes), f"Paint {len(self._drag_changes)} cells")
                self.undo_stack.push(cmd)
                self.batchChanged.emit(list(self._drag_changes))
            self.gridChanged.emit()
        self._dragging = False; self._drag_button = None; self._drag_value = None; self._drag_changes = []
        self.update()

    def leaveEvent(self, event):
        self._hover_cell = (-1, -1); self.update()

    def keyPressEvent(self, event):
        if not self._show_selection:
            self._show_selection = True
            self._selected_cell = (0, 0)
        r, c = self._selected_cell
        key = event.key()
        moved = False
        if key == Qt.Key_Up:
            self._selected_cell = (max(0, r-1), c); moved = True
        elif key == Qt.Key_Down:
            self._selected_cell = (min(self.model.rows-1, r+1), c); moved = True
        elif key == Qt.Key_Left:
            self._selected_cell = (r, max(0, c-1)); moved = True
        elif key == Qt.Key_Right:
            self._selected_cell = (r, min(self.model.cols-1, c+1)); moved = True
        elif key == Qt.Key_Space:
            nr, nc = self._selected_cell
            grid = self.model.solution if self.mode == "create" else self.model.player_grid
            old = grid[nr][nc]
            new = NonogramModel.EMPTY if old == NonogramModel.FILLED else NonogramModel.FILLED
            grid[nr][nc] = new
            self.undo_stack.push(GridChangeCommand(self.model, nr, nc, old, new, "Key Fill"))
            self.gridChanged.emit()
        elif key == Qt.Key_X and self.mode == "play":
            nr, nc = self._selected_cell
            old = self.model.player_grid[nr][nc]
            new = NonogramModel.EMPTY if old == NonogramModel.MARKED else NonogramModel.MARKED
            self.model.player_grid[nr][nc] = new
            self.undo_stack.push(GridChangeCommand(self.model, nr, nc, old, new, "Key Mark"))
            self.gridChanged.emit()
        elif key in (Qt.Key_Delete, Qt.Key_Backspace, Qt.Key_0):
            nr, nc = self._selected_cell
            grid = self.model.solution if self.mode == "create" else self.model.player_grid
            old = grid[nr][nc]
            if old != NonogramModel.EMPTY:
                grid[nr][nc] = NonogramModel.EMPTY
                self.undo_stack.push(GridChangeCommand(self.model, nr, nc, old, NonogramModel.EMPTY, "Key Clear"))
                self.gridChanged.emit()
        else:
            super().keyPressEvent(event); return
        self.update()

    def resizeEvent(self, event):
        self.update()


# ════════════════════════════════════════════════════════════════════════════════
# DIALOGS
# ════════════════════════════════════════════════════════════════════════════════

class SavePuzzleDialog(QDialog):
    def __init__(self, current_title="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Save Puzzle"); self.setMinimumWidth(350)
        layout = QFormLayout(self)
        self.title_edit = QLineEdit(current_title)
        self.title_edit.setPlaceholderText("Enter puzzle title...")
        layout.addRow("Title:", self.title_edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_title(self): return self.title_edit.text().strip()


class ExportOptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Options"); self.setMinimumWidth(300)
        layout = QVBoxLayout(self)
        self.clues_only_cb = QCheckBox("Clues only (no solution visible)"); layout.addWidget(self.clues_only_cb)
        self.include_title_cb = QCheckBox("Include title"); self.include_title_cb.setChecked(True); layout.addWidget(self.include_title_cb)
        self.high_res_cb = QCheckBox("High resolution (2x)"); self.high_res_cb.setChecked(True); layout.addWidget(self.high_res_cb)
        self.dark_bg_cb = QCheckBox("Dark background"); layout.addWidget(self.dark_bg_cb)
        self.with_coords_cb = QCheckBox("Include coordinates"); layout.addWidget(self.with_coords_cb)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class NewPuzzleDialog(QDialog):
    def __init__(self, current_rows=10, current_cols=10, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Puzzle"); self.setMinimumWidth(300)
        layout = QFormLayout(self)
        self.rows_spin = QSpinBox(); self.rows_spin.setRange(2,50); self.rows_spin.setValue(current_rows)
        layout.addRow("Rows:", self.rows_spin)
        self.cols_spin = QSpinBox(); self.cols_spin.setRange(2,50); self.cols_spin.setValue(current_cols)
        layout.addRow("Columns:", self.cols_spin)
        pg = QGroupBox("Presets"); pl = QHBoxLayout(pg)
        for label, r, c in [("5x5",5,5),("10x10",10,10),("15x15",15,15),("20x20",20,20)]:
            b = QPushButton(label); b.clicked.connect(lambda _, rr=r, cc=c: self._set_size(rr,cc)); pl.addWidget(b)
        layout.addRow(pg)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _set_size(self, r, c): self.rows_spin.setValue(r); self.cols_spin.setValue(c)
    def get_size(self): return self.rows_spin.value(), self.cols_spin.value()


class ImportImageDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import from Image")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        info = QLabel("Import a black & white image as a nonogram puzzle.\n"
                       "Dark pixels become filled cells.\n\n"
                       "Supported: PNG, JPG, BMP")
        info.setWordWrap(True)
        layout.addWidget(info)
        self.threshold_label = QLabel("Binarization threshold: 128")
        layout.addWidget(self.threshold_label)
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setRange(0, 255)
        self.threshold_slider.setValue(128)
        self.threshold_slider.valueChanged.connect(lambda v: self.threshold_label.setText(f"Binarization threshold: {v}"))
        layout.addWidget(self.threshold_slider)

        self.invert_cb = QCheckBox("Invert (light = filled)")
        layout.addWidget(self.invert_cb)

        self.target_size_label = QLabel("Target grid size: 15x15")
        layout.addWidget(self.target_size_label)
        size_row = QHBoxLayout()
        self.rows_spin = QSpinBox(); self.rows_spin.setRange(5,50); self.rows_spin.setValue(15)
        self.cols_spin = QSpinBox(); self.cols_spin.setRange(5,50); self.cols_spin.setValue(15)
        size_row.addWidget(QLabel("R:")); size_row.addWidget(self.rows_spin)
        size_row.addWidget(QLabel("C:")); size_row.addWidget(self.cols_spin)
        layout.addLayout(size_row)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class TextExportDialog(QDialog):
    def __init__(self, puzzle_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Text Export - Copy to Share")
        self.setMinimumSize(500, 400)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Copy the text below to share this puzzle:"))
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlainText(puzzle_data)
        layout.addWidget(self.text_edit)
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(lambda: (QApplication.clipboard().setText(self.text_edit.toPlainText()),
                                          copy_btn.setText("Copied!")))
        layout.addWidget(copy_btn)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


# ════════════════════════════════════════════════════════════════════════════════
# ENHANCED SAMPLE PUZZLE PICKER
# ════════════════════════════════════════════════════════════════════════════════

class SamplePuzzleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sample Puzzles")
        self.setMinimumSize(550, 480)
        layout = QVBoxLayout(self)

        # Filter bar
        filter_bar = QHBoxLayout()
        filter_bar.addWidget(QLabel("Category:"))
        self.cat_combo = QComboBox()
        self.cat_combo.addItem("All")
        categories = sorted(set(p.get("category", "Other") for p in SAMPLE_PUZZLES.values()))
        for cat in categories:
            self.cat_combo.addItem(cat)
        self.cat_combo.currentTextChanged.connect(self._filter)
        filter_bar.addWidget(self.cat_combo)

        filter_bar.addWidget(QLabel("Difficulty:"))
        self.diff_combo = QComboBox()
        self.diff_combo.addItem("All")
        for d in ["Easy", "Medium", "Hard", "Expert"]:
            self.diff_combo.addItem(d)
        self.diff_combo.currentTextChanged.connect(self._filter)
        filter_bar.addWidget(self.diff_combo)
        layout.addLayout(filter_bar)

        # Puzzle list
        self.puzzle_list = QListWidget()
        self.puzzle_list.setIconSize(QSize(40, 40))
        self.puzzle_list.setFlow(QListWidget.LeftToRight)
        self.puzzle_list.setWrapping(True)
        self.puzzle_list.setResizeMode(QListWidget.Adjust)
        self.puzzle_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.puzzle_list.currentRowChanged.connect(self._update_preview)
        layout.addWidget(self.puzzle_list, 1)

        # Preview + info
        bottom = QHBoxLayout()
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(180, 180)
        self.preview_label.setStyleSheet("border: 1px solid #d1d5db; border-radius: 8px; background: #f9fafb;")
        bottom.addWidget(self.preview_label)

        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setMinimumWidth(200)
        self.info_label.setStyleSheet("padding: 8px; font-size: 13px;")
        bottom.addWidget(self.info_label, 1)
        layout.addLayout(bottom)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._populate()

    def _populate(self):
        self.puzzle_list.clear()
        for name, p in SAMPLE_PUZZLES.items():
            diff = p.get("difficulty", "?")
            size = f"{p['rows']}x{p['cols']}"
            item = QListWidgetItem(f"{p['title']}  ({size})  [{diff}]")
            item.setData(Qt.UserRole, name)
            self.puzzle_list.addItem(item)

    def _filter(self):
        cat = self.cat_combo.currentText()
        diff = self.diff_combo.currentText()
        self.puzzle_list.clear()
        for name, p in SAMPLE_PUZZLES.items():
            if cat != "All" and p.get("category", "") != cat: continue
            if diff != "All" and p.get("difficulty", "") != diff: continue
            size = f"{p['rows']}x{p['cols']}"
            d = p.get("difficulty", "?")
            item = QListWidgetItem(f"{p['title']}  ({size})  [{d}]")
            item.setData(Qt.UserRole, name)
            self.puzzle_list.addItem(item)
        if self.puzzle_list.count() > 0:
            self.puzzle_list.setCurrentRow(0)

    def _update_preview(self, row):
        if row < 0: return
        name = self.puzzle_list.item(row).data(Qt.UserRole)
        if not name: return
        p = SAMPLE_PUZZLES[name]
        rows, cols, sol = p["rows"], p["cols"], p["solution"]
        cell = min(8, 160 // max(rows, cols))
        w, h = cols*cell+2, rows*cell+2
        pixmap = QPixmap(w, h)
        pixmap.fill(QColor(245,245,248))
        pp = QPainter(pixmap)
        for r in range(rows):
            for c in range(cols):
                color = QColor(37,99,235) if sol[r][c] == 1 else QColor(255,255,255)
                pp.fillRect(QRect(c*cell, r*cell, cell, cell), color)
                pp.setPen(QPen(QColor(200,210,220), 1))
                pp.drawRect(QRect(c*cell, r*cell, cell, cell))
        pp.end()
        self.preview_label.setPixmap(pixmap.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        # Info
        diff = p.get("difficulty", "?")
        desc = p.get("description", "")
        filled = sum(cell == 1 for row in sol for cell in row)
        total = rows * cols
        diff_colors = {"Easy": "#16a34a", "Medium": "#d97706", "Hard": "#dc2626", "Expert": "#7c3aed"}
        dc = diff_colors.get(diff, "#64748b")
        self.info_label.setText(
            f"<b>{p['title']}</b><br>"
            f"<span style='color:{dc}; font-weight:bold;'>{diff}</span> &middot; {rows}x{cols}<br>"
            f"Filled: {filled}/{total} ({filled/total*100:.0f}%)<br><br>"
            f"{desc}"
        )

    def get_selected(self):
        row = self.puzzle_list.currentRow()
        if row < 0: return None
        name = self.puzzle_list.item(row).data(Qt.UserRole)
        return SAMPLE_PUZZLES.get(name)




# ════════════════════════════════════════════════════════════════════════════════
# PUZZLE COLLECTION DIALOG
# ════════════════════════════════════════════════════════════════════════════════

class CollectionDialog(QDialog):
    """Dialog for managing puzzle collections (.ncol files)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Puzzle Collection Manager")
        self.setMinimumSize(600, 500)
        self.puzzles = []
        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        header.addWidget(QLabel("Puzzle Collection"))
        header.addStretch()
        self.add_btn = QPushButton("Add Current Puzzle")
        self.add_btn.setStyleSheet("background:#dcfce7;color:#166534;border:1px solid #86efac;font-weight:bold;")
        header.addWidget(self.add_btn)
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.setStyleSheet("background:#fee2e2;color:#991b1b;border:1px solid #fca5a5;")
        header.addWidget(self.remove_btn)
        layout.addLayout(header)

        self.puzzle_list = QListWidget()
        self.puzzle_list.currentRowChanged.connect(self._update_info)
        layout.addWidget(self.puzzle_list, 1)

        self.info_label = QLabel("No puzzle selected")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("padding:8px;border:1px solid #e2e8f0;border-radius:6px;background:#f8fafc;")
        layout.addWidget(self.info_label)

        btn_row = QHBoxLayout()
        self.load_btn = QPushButton("Load Selected")
        self.load_btn.setStyleSheet("background:#dbeafe;color:#1d4ed8;border:1px solid #93c5fd;font-weight:bold;")
        self.load_btn.setEnabled(False)
        btn_row.addWidget(self.load_btn)
        btn_row.addStretch()
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        btn_row.addWidget(buttons)
        layout.addLayout(btn_row)

    def load_collection(self, path):
        """Load a .ncol file."""
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            self.puzzles = data if isinstance(data, list) else data.get("puzzles", [])
            self._refresh_list()
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load collection:\n{e}")
            return False

    def save_collection(self, path):
        """Save collection to a .ncol file."""
        try:
            with open(path, 'w') as f:
                json.dump({"version": "4.0", "puzzles": self.puzzles}, f, indent=2)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save collection:\n{e}")
            return False

    def add_puzzle(self, model):
        """Add current puzzle to the collection."""
        data = model.to_dict()
        data["category"] = "Custom"
        data["difficulty"] = model.difficulty_rating()
        data["description"] = f"Custom {model.rows}x{model.cols} puzzle"
        self.puzzles.append(data)
        self._refresh_list()

    def _refresh_list(self):
        self.puzzle_list.clear()
        for i, p in enumerate(self.puzzles):
            title = p.get("title", f"Puzzle {i+1}")
            size = f"{p['rows']}x{p['cols']}"
            diff = p.get("difficulty", "?")
            self.puzzle_list.addItem(f"{title}  ({size})  [{diff}]")

    def _update_info(self, row):
        if row < 0 or row >= len(self.puzzles):
            self.info_label.setText("No puzzle selected")
            self.load_btn.setEnabled(False)
            return
        self.load_btn.setEnabled(True)
        p = self.puzzles[row]
        sol = p.get("solution", [])
        rows, cols = p["rows"], p["cols"]
        filled = sum(cell == 1 for row in sol for cell in row)
        total = rows * cols
        self.info_label.setText(
            f"<b>{p.get('title', 'Untitled')}</b><br>"
            f"Size: {rows}x{cols} | Filled: {filled}/{total} ({filled/total*100:.0f}%)<br>"
            f"Difficulty: {p.get('difficulty', 'N/A')} | Category: {p.get('category', 'N/A')}"
        )

    def get_selected(self):
        row = self.puzzle_list.currentRow()
        if 0 <= row < len(self.puzzles):
            return self.puzzles[row]
        return None


# ════════════════════════════════════════════════════════════════════════════════
# IMPORT FROM TEXT DIALOG
# ════════════════════════════════════════════════════════════════════════════════

class ImportTextDialog(QDialog):
    """Dialog for importing a puzzle from text (#/. grid format)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import from Text")
        self.setMinimumSize(500, 450)
        layout = QVBoxLayout(self)

        info = QLabel(
            "Paste a puzzle grid using # (filled) and . (empty).\n"
            "Each line is one row. Example:\n"
            ".#.#.\n"
            "#####\n"
            ".#.#.\n"
            "#####\n"
            ".#.#."
        )
        info.setStyleSheet("padding:8px;border:1px solid #e2e8f0;border-radius:6px;background:#f0f9ff;font-size:12px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Paste grid here...\nUse # for filled, . for empty")
        self.text_edit.setFont(QFont("Courier New", 12))
        layout.addWidget(self.text_edit, 1)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color:#dc2626;padding:4px;")
        layout.addWidget(self.status_label)

        btn_row = QHBoxLayout()
        preview_btn = QPushButton("Preview")
        preview_btn.clicked.connect(self._preview)
        btn_row.addWidget(preview_btn)
        btn_row.addStretch()
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        btn_row.addWidget(buttons)
        layout.addLayout(btn_row)

        self._parsed_grid = None

    def _parse(self):
        text = self.text_edit.toPlainText().strip()
        if not text:
            self.status_label.setText("No text provided!")
            return None
        lines = text.split("\n")
        grid = []
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            row = []
            for ch in line:
                if ch == '#':
                    row.append(NonogramModel.FILLED)
                elif ch == '.':
                    row.append(NonogramModel.EMPTY)
                elif ch in ('0', ' '):
                    row.append(NonogramModel.EMPTY)
                elif ch in ('1', 'X', 'x', '*', 'O'):
                    row.append(NonogramModel.FILLED)
                else:
                    self.status_label.setText(f"Invalid character '{ch}' on line {i+1}")
                    return None
            if row:
                grid.append(row)
        if not grid:
            self.status_label.setText("No valid rows found!")
            return None
        # Normalize row lengths
        max_len = max(len(r) for r in grid)
        for r in grid:
            while len(r) < max_len:
                r.append(NonogramModel.EMPTY)
        self.status_label.setText(f"Parsed {len(grid)}x{max_len} grid ({sum(c==1 for r in grid for c in r)} filled cells)")
        self.status_label.setStyleSheet("color:#16a34a;padding:4px;")
        return grid

    def _preview(self):
        grid = self._parse()
        if grid:
            self._parsed_grid = grid
            QMessageBox.information(self, "Preview", f"Grid: {len(grid)} rows x {len(grid[0])} cols\n"
                                   f"Filled: {sum(c==1 for r in grid for c in r)} cells")

    def _validate_and_accept(self):
        grid = self._parse()
        if grid:
            self._parsed_grid = grid
            self.accept()

    def get_grid(self):
        return self._parsed_grid

# ════════════════════════════════════════════════════════════════════════════════
# STYLESHEETS
# ════════════════════════════════════════════════════════════════════════════════

LIGHT_SS = """
QMainWindow{background:#fff}QMenuBar{background:#f8fafc;border-bottom:1px solid #e2e8f0;padding:2px}
QMenuBar::item{padding:6px 12px;border-radius:4px}QMenuBar::item:selected{background:#e2e8f0}
QMenu{border:1px solid #e2e8f0;border-radius:8px;padding:4px}
QMenu::item{padding:6px 24px;border-radius:4px}QMenu::item:selected{background:#2563eb;color:#fff}
QStatusBar{background:#f8fafc;border-top:1px solid #e2e8f0}
QSpinBox{padding:4px 8px;border:1px solid #d1d5db;border-radius:6px;background:#fff;min-width:60px}
QScrollArea{border:none}
"""
DARK_SS = """
QMainWindow{background:#1e1e2e}QMenuBar{background:#2a2a3c;border-bottom:1px solid #3a3a50;padding:2px;color:#cdd6f4}
QMenuBar::item{padding:6px 12px;border-radius:4px}QMenuBar::item:selected{background:#45475a}
QMenu{background:#2a2a3c;border:1px solid #3a3a50;border-radius:8px;padding:4px;color:#cdd6f4}
QMenu::item{padding:6px 24px;border-radius:4px}QMenu::item:selected{background:#2563eb;color:#fff}
QStatusBar{background:#2a2a3c;border-top:1px solid #3a3a50;color:#a6adc8}
QSpinBox{padding:4px 8px;border:1px solid #3a3a50;border-radius:6px;background:#313244;color:#cdd6f4;min-width:60px}
QScrollArea{border:none}QLabel{color:#cdd6f4}QGroupBox{color:#cdd6f4;border-color:#45475a}
QGroupBox::title{color:#cdd6f4}QLineEdit{background:#313244;color:#cdd6f4;border:1px solid #45475a;border-radius:6px;padding:4px 8px}
QCheckBox{color:#cdd6f4}QComboBox{background:#313244;color:#cdd6f4;border:1px solid #45475a;border-radius:6px;padding:4px 8px}
QComboBox QAbstractItemView{background:#313244;color:#cdd6f4;selection-background-color:#2563eb}
QListWidget{background:#313244;color:#cdd6f4;border:1px solid #45475a;border-radius:6px}
QListWidget::item{padding:4px}QListWidget::item:selected{background:#2563eb}
QTextEdit{background:#313244;color:#cdd6f4;border:1px solid #45475a;border-radius:6px}
"""
PANEL_LIGHT = """
QWidget#cp{font-family:'Segoe UI',sans-serif;background:#fafbfc}
QWidget#cp QGroupBox{font-weight:bold;border:1px solid #d1d5db;border-radius:8px;margin-top:12px;padding-top:16px}
QWidget#cp QGroupBox::title{subcontrol-origin:margin;left:12px;padding:0 6px}
QWidget#cp QPushButton{padding:6px 12px;border-radius:6px;border:1px solid #d1d5db;background:#f9fafb;font-size:12px}
QWidget#cp QPushButton:hover{background:#e5e7eb}QWidget#cp QPushButton:pressed{background:#d1d5db}
QWidget#cp QPushButton:disabled{color:#9ca3af;background:#f3f4f6}
"""
PANEL_DARK = """
QWidget#cp{font-family:'Segoe UI',sans-serif;background:#1e1e2e}
QWidget#cp QGroupBox{font-weight:bold;border:1px solid #45475a;border-radius:8px;margin-top:12px;padding-top:16px;color:#cdd6f4}
QWidget#cp QGroupBox::title{subcontrol-origin:margin;left:12px;padding:0 6px;color:#cdd6f4}
QWidget#cp QPushButton{padding:6px 12px;border-radius:6px;border:1px solid #45475a;background:#313244;color:#cdd6f4;font-size:12px}
QWidget#cp QPushButton:hover{background:#45475a}QWidget#cp QPushButton:pressed{background:#585b70}
QWidget#cp QPushButton:disabled{color:#6c7086;background:#2a2a3c}
QWidget#cp QLabel{color:#cdd6f4}QWidget#cp QSpinBox{background:#313244;color:#cdd6f4;border-color:#45475a}
QWidget#cp QComboBox{background:#313244;color:#cdd6f4;border-color:#45475a}
QWidget#cp QComboBox QAbstractItemView{background:#313244;color:#cdd6f4;selection-background-color:#2563eb}
"""


# ════════════════════════════════════════════════════════════════════════════════
# MAIN WINDOW
# ════════════════════════════════════════════════════════════════════════════════

class NonogramCreatorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nonogram Puzzle Creator v4.0")
        self.setMinimumSize(960, 740)
        self.resize(1200, 860)
        self.model = NonogramModel(10, 10)
        self.current_file = None
        self.dark_mode = False
        self.undo_stack = QUndoStack(self)
        self.timer_active = False
        self.timer_seconds = 0
        self.best_time = None
        self.move_count = 0
        self.hints_used = 0
        self.max_hints = 5
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick_timer)
        self._step_timer = QTimer(self)
        self._step_timer.setInterval(60)
        self._step_timer.timeout.connect(self._step_solve_tick)
        self._step_changes = []
        self._step_index = 0
        self._recent_files = []
        self._max_recent = 5
        self._build_ui()
        self._build_menus()
        self._build_toolbar()
        self._build_statusbar()
        self._connect_signals()
        self.setAcceptDrops(True)
        self._update_stats()

    def _build_ui(self):
        central = QWidget(); self.setCentralWidget(central)
        ml = QHBoxLayout(central); ml.setContentsMargins(0,0,0,0); ml.setSpacing(0)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff); scroll.setFixedWidth(270)
        self.control_panel = self._build_control_panel(); self.control_panel.setObjectName("cp")
        scroll.setWidget(self.control_panel); ml.addWidget(scroll)
        sep = QFrame(); sep.setFrameShape(QFrame.VLine); sep.setStyleSheet("color:#d1d5db;"); ml.addWidget(sep)
        gc = QWidget(); gl = QVBoxLayout(gc); gl.setContentsMargins(16,16,16,16)
        # Top bar
        tb = QHBoxLayout()
        self.mode_label = QLabel("CREATING MODE"); self.mode_label.setFont(QFont("Segoe UI",13,QFont.Bold))
        self.mode_label.setStyleSheet("color:#2563eb;padding:4px 0px;"); tb.addWidget(self.mode_label)
        tb.addStretch()
        self.move_label = QLabel("Moves: 0"); self.move_label.setStyleSheet("color:#64748b;font-size:12px;padding:4px 8px;")
        self.move_label.setVisible(False); tb.addWidget(self.move_label)
        self.hint_label = QLabel("Hints: 5/5"); self.hint_label.setStyleSheet("color:#64748b;font-size:12px;padding:4px 8px;")
        self.hint_label.setVisible(False); tb.addWidget(self.hint_label)
        self.timer_label = QLabel("00:00"); self.timer_label.setFont(QFont("Segoe UI",14,QFont.Bold))
        self.timer_label.setStyleSheet("color:#64748b;padding:4px 8px;"); self.timer_label.setVisible(False); tb.addWidget(self.timer_label)
        self.progress_bar = QProgressBar(); self.progress_bar.setFixedWidth(140); self.progress_bar.setFixedHeight(18)
        self.progress_bar.setTextVisible(True); self.progress_bar.setFormat("%p%"); self.progress_bar.setVisible(False); tb.addWidget(self.progress_bar)
        gl.addLayout(tb)
        self.grid_widget = NonogramGridWidget(self.model, self.undo_stack); gl.addWidget(self.grid_widget, 1)
        # Zoom bar
        zb = QHBoxLayout(); zb.addStretch()
        self.zoom_out_btn = QPushButton("-"); self.zoom_out_btn.setFixedSize(32,32)
        self.zoom_out_btn.setStyleSheet("font-size:18px;font-weight:bold;padding:0;")
        self.zoom_out_btn.clicked.connect(self.grid_widget.zoom_out); zb.addWidget(self.zoom_out_btn)
        self.zoom_label = QLabel("100%"); self.zoom_label.setFixedWidth(50); self.zoom_label.setAlignment(Qt.AlignCenter); zb.addWidget(self.zoom_label)
        self.zoom_slider = QSlider(Qt.Horizontal); self.zoom_slider.setRange(40,300); self.zoom_slider.setValue(100)
        self.zoom_slider.setFixedWidth(150); self.zoom_slider.valueChanged.connect(self._on_zoom_slider); zb.addWidget(self.zoom_slider)
        self.zoom_in_btn = QPushButton("+"); self.zoom_in_btn.setFixedSize(32,32)
        self.zoom_in_btn.setStyleSheet("font-size:18px;font-weight:bold;padding:0;")
        self.zoom_in_btn.clicked.connect(self.grid_widget.zoom_in); zb.addWidget(self.zoom_in_btn)
        self.zoom_fit_btn = QPushButton("Fit"); self.zoom_fit_btn.setFixedHeight(32); self.zoom_fit_btn.clicked.connect(self._on_zoom_fit); zb.addWidget(self.zoom_fit_btn)
        zb.addStretch(); gl.addLayout(zb)
        ml.addWidget(gc, 1)

    def _build_control_panel(self):
        p = QWidget(); p.setStyleSheet(PANEL_LIGHT)
        l = QVBoxLayout(p); l.setContentsMargins(12,12,10,12); l.setSpacing(5)
        title = QLabel("Nonogram Creator v4"); title.setFont(QFont("Segoe UI",14,QFont.Bold))
        title.setStyleSheet("color:#1e293b;padding-bottom:2px;"); l.addWidget(title)

        # Grid Size
        sg = QGroupBox("Grid Size"); sl = QFormLayout(sg)
        self.rows_spin = QSpinBox(); self.rows_spin.setRange(2,50); self.rows_spin.setValue(10); sl.addRow("Rows:", self.rows_spin)
        self.cols_spin = QSpinBox(); self.cols_spin.setRange(2,50); self.cols_spin.setValue(10); sl.addRow("Columns:", self.cols_spin)
        self.resize_btn = QPushButton("Apply Size"); self.resize_btn.setStyleSheet("background:#dbeafe;color:#1d4ed8;font-weight:bold;border:1px solid #93c5fd;")
        self.resize_btn.clicked.connect(self._on_resize); sl.addRow(self.resize_btn); l.addWidget(sg)

        # Tools
        tg = QGroupBox("Tools"); tl = QVBoxLayout(tg)
        r1 = QHBoxLayout(); self.clear_btn = QPushButton("Clear"); self.clear_btn.clicked.connect(self._on_clear); r1.addWidget(self.clear_btn)
        self.fill_all_btn = QPushButton("Fill All"); self.fill_all_btn.clicked.connect(self._on_fill_all); r1.addWidget(self.fill_all_btn); tl.addLayout(r1)
        r2 = QHBoxLayout(); self.invert_btn = QPushButton("Invert"); self.invert_btn.clicked.connect(self._on_invert); r2.addWidget(self.invert_btn)
        self.random_btn = QPushButton("Random"); self.random_btn.clicked.connect(self._on_random)
        self.random_btn.setStyleSheet("background:#fef3c7;color:#92400e;border:1px solid #fcd34d;"); r2.addWidget(self.random_btn); tl.addLayout(r2)
        l.addWidget(tg)

        # Symmetry
        sym = QGroupBox("Symmetry"); syl = QHBoxLayout(sym)
        self.sym_h_btn = QPushButton("H"); self.sym_h_btn.setToolTip("Mirror horizontal"); self.sym_h_btn.clicked.connect(lambda: self._on_mirror("h")); syl.addWidget(self.sym_h_btn)
        self.sym_v_btn = QPushButton("V"); self.sym_v_btn.setToolTip("Mirror vertical"); self.sym_v_btn.clicked.connect(lambda: self._on_mirror("v")); syl.addWidget(self.sym_v_btn)
        self.sym_both_btn = QPushButton("H+V"); self.sym_both_btn.setToolTip("Mirror both"); self.sym_both_btn.clicked.connect(lambda: self._on_mirror("both")); syl.addWidget(self.sym_both_btn)
        l.addWidget(sym)

        # Rotate & Shift
        tsg = QGroupBox("Rotate / Shift"); tsl = QVBoxLayout(tsg)
        tr = QHBoxLayout()
        self.rot_cw_btn = QPushButton("CW 90"); self.rot_cw_btn.setToolTip("Rotate 90 clockwise"); self.rot_cw_btn.clicked.connect(lambda: self._on_rotate("cw")); tr.addWidget(self.rot_cw_btn)
        self.rot_ccw_btn = QPushButton("CCW 90"); self.rot_ccw_btn.setToolTip("Rotate 90 counter-clockwise"); self.rot_ccw_btn.clicked.connect(lambda: self._on_rotate("ccw")); tr.addWidget(self.rot_ccw_btn)
        tsl.addLayout(tr)
        shr = QHBoxLayout()
        self.sh_up_btn = QPushButton("Up"); self.sh_up_btn.setToolTip("Shift rows up"); self.sh_up_btn.clicked.connect(lambda: self._on_shift("rows", -1)); shr.addWidget(self.sh_up_btn)
        self.sh_dn_btn = QPushButton("Down"); self.sh_dn_btn.setToolTip("Shift rows down"); self.sh_dn_btn.clicked.connect(lambda: self._on_shift("rows", 1)); shr.addWidget(self.sh_dn_btn)
        self.sh_lt_btn = QPushButton("Left"); self.sh_lt_btn.setToolTip("Shift cols left"); self.sh_lt_btn.clicked.connect(lambda: self._on_shift("cols", -1)); shr.addWidget(self.sh_lt_btn)
        self.sh_rt_btn = QPushButton("Right"); self.sh_rt_btn.setToolTip("Shift cols right"); self.sh_rt_btn.clicked.connect(lambda: self._on_shift("cols", 1)); shr.addWidget(self.sh_rt_btn)
        tsl.addLayout(shr)
        l.addWidget(tsg)

        # Fill Color
        cg = QGroupBox("Fill Color"); cl_ = QHBoxLayout(cg)
        self.color_combo = QComboBox()
        for name, _ in FILL_COLORS: self.color_combo.addItem(name)
        self.color_combo.currentIndexChanged.connect(lambda i: (setattr(self.grid_widget, 'fill_color_idx', i), self.grid_widget.update()))
        cl_.addWidget(self.color_combo); l.addWidget(cg)

        # Mode
        mg = QGroupBox("Mode"); mol = QVBoxLayout(mg)
        mr = QHBoxLayout(); self.create_btn = QPushButton("Create"); self.create_btn.setCheckable(True); self.create_btn.setChecked(True)
        self.create_btn.setStyleSheet("background:#2563eb;color:white;font-weight:bold;border:none;")
        self.create_btn.clicked.connect(lambda: self._set_mode("create")); mr.addWidget(self.create_btn)
        self.play_btn = QPushButton("Play"); self.play_btn.setCheckable(True)
        self.play_btn.clicked.connect(lambda: self._set_mode("play")); mr.addWidget(self.play_btn); mol.addLayout(mr)
        pr = QHBoxLayout(); self.check_btn = QPushButton("Check"); self.check_btn.clicked.connect(self._on_check_solution); self.check_btn.setEnabled(False)
        self.check_btn.setStyleSheet("background:#dcfce7;color:#166534;border:1px solid #86efac;"); pr.addWidget(self.check_btn)
        self.hint_btn = QPushButton("Hint"); self.hint_btn.clicked.connect(self._on_hint); self.hint_btn.setEnabled(False)
        self.hint_btn.setStyleSheet("background:#fef3c7;color:#92400e;border:1px solid #fcd34d;"); pr.addWidget(self.hint_btn); mol.addLayout(pr)
        sr = QHBoxLayout(); self.solve_btn = QPushButton("Solve"); self.solve_btn.clicked.connect(self._on_auto_solve); self.solve_btn.setEnabled(False)
        self.solve_btn.setStyleSheet("background:#e0e7ff;color:#3730a3;border:1px solid #a5b4fc;"); sr.addWidget(self.solve_btn)
        self.reveal_btn = QPushButton("Reveal"); self.reveal_btn.clicked.connect(self._on_reveal); self.reveal_btn.setEnabled(False)
        self.reveal_btn.setStyleSheet("background:#fee2e2;color:#991b1b;border:1px solid #fca5a5;"); sr.addWidget(self.reveal_btn); mol.addLayout(sr)
        str2 = QHBoxLayout()
        self.step_solve_btn = QPushButton("Step Solve"); self.step_solve_btn.clicked.connect(self._on_step_solve); self.step_solve_btn.setEnabled(False)
        self.step_solve_btn.setStyleSheet("background:#f0fdf4;color:#166534;border:1px solid #86efac;"); str2.addWidget(self.step_solve_btn); mol.addLayout(str2)
        l.addWidget(mg)

        # Stats
        stg = QGroupBox("Statistics"); stl = QFormLayout(stg)
        self.stat_size = QLabel("10 x 10"); stl.addRow("Size:", self.stat_size)
        self.stat_filled = QLabel("0 / 100"); stl.addRow("Filled:", self.stat_filled)
        self.stat_pct = QLabel("0.0%"); stl.addRow("Density:", self.stat_pct)
        self.stat_diff = QLabel("N/A"); stl.addRow("Difficulty:", self.stat_diff)
        self.stat_best = QLabel("--:--"); stl.addRow("Best Time:", self.stat_best)
        l.addWidget(stg)

        # File
        fg = QGroupBox("File"); fl = QVBoxLayout(fg)
        fr = QHBoxLayout(); self.save_btn = QPushButton("Save"); self.save_btn.clicked.connect(self._on_save)
        self.save_btn.setStyleSheet("background:#f0fdf4;color:#166534;border:1px solid #86efac;"); fr.addWidget(self.save_btn)
        self.load_btn = QPushButton("Load"); self.load_btn.clicked.connect(self._on_load); fr.addWidget(self.load_btn); fl.addLayout(fr)
        self.sample_btn = QPushButton("Samples..."); self.sample_btn.clicked.connect(self._on_sample_puzzles)
        self.sample_btn.setStyleSheet("background:#fef9c3;color:#854d0e;border:1px solid #fde047;"); fl.addWidget(self.sample_btn)
        self.import_btn = QPushButton("Import Image..."); self.import_btn.clicked.connect(self._on_import_image)
        self.import_btn.setStyleSheet("background:#f0f9ff;color:#075985;border:1px solid #7dd3fc;"); fl.addWidget(self.import_btn)
        self.export_img_btn = QPushButton("Export Image..."); self.export_img_btn.clicked.connect(self._on_export_image)
        self.export_img_btn.setStyleSheet("background:#fdf4ff;color:#86198f;border:1px solid #e9d5ff;"); fl.addWidget(self.export_img_btn)
        self.export_text_btn = QPushButton("Export as Text..."); self.export_text_btn.clicked.connect(self._on_export_text)
        self.export_text_btn.setStyleSheet("background:#f5f5f4;color:#44403c;border:1px solid #d6d3d1;"); fl.addWidget(self.export_text_btn)
        self.collection_btn = QPushButton("Collection..."); self.collection_btn.clicked.connect(self._on_collection)
        self.collection_btn.setStyleSheet("background:#faf5ff;color:#7e22ce;border:1px solid #d8b4fe;"); fl.addWidget(self.collection_btn)
        self.import_text_btn = QPushButton("Import Text..."); self.import_text_btn.clicked.connect(self._on_import_text)
        self.import_text_btn.setStyleSheet("background:#fff7ed;color:#9a3412;border:1px solid #fdba74;"); fl.addWidget(self.import_text_btn)
        l.addWidget(fg)

        # Settings
        setg = QGroupBox("Settings"); setl = QVBoxLayout(setg)
        self.dark_cb = QCheckBox("Dark Mode"); self.dark_cb.toggled.connect(self._toggle_dark_mode); setl.addWidget(self.dark_cb)
        self.cross_cb = QCheckBox("Cross-highlight"); self.cross_cb.setChecked(True)
        self.cross_cb.toggled.connect(lambda v: (setattr(self.grid_widget,'show_cross_highlight',v), self.grid_widget.update())); setl.addWidget(self.cross_cb)
        self.clue_hl_cb = QCheckBox("Grey solved clues"); self.clue_hl_cb.setChecked(True)
        self.clue_hl_cb.toggled.connect(lambda v: (setattr(self.grid_widget,'show_completed_clues',v), self.grid_widget.update())); setl.addWidget(self.clue_hl_cb)
        self.coord_cb = QCheckBox("Show coordinates")
        self.coord_cb.toggled.connect(lambda v: (setattr(self.grid_widget,'show_coordinates',v), self.grid_widget.update())); setl.addWidget(self.coord_cb)
        self.error_hl_cb = QCheckBox("Error highlighting")
        self.error_hl_cb.toggled.connect(self._toggle_error_hl); setl.addWidget(self.error_hl_cb)
        self.keyboard_cb = QCheckBox("Keyboard navigation")
        self.keyboard_cb.toggled.connect(self._toggle_keyboard_nav); setl.addWidget(self.keyboard_cb)
        self.cellcount_cb = QCheckBox("Cell counts in play mode")
        self.cellcount_cb.setChecked(True)
        self.cellcount_cb.toggled.connect(lambda v: (setattr(self.grid_widget, 'show_cell_counts', v), self.grid_widget.update())); setl.addWidget(self.cellcount_cb)
        l.addWidget(setg)

        l.addStretch()
        return p

    def _build_menus(self):
        mb = self.menuBar()
        fm = mb.addMenu("&File")
        self._a(fm,"&New Puzzle...","Ctrl+N",self._on_new); fm.addSeparator()
        self._a(fm,"&Save...","Ctrl+S",self._on_save); self._a(fm,"&Open...","Ctrl+O",self._on_load)
        self._a(fm,"Sample Puzzles...","Ctrl+Shift+L",self._on_sample_puzzles)
        self._a(fm,"Import from Image...","Ctrl+I",self._on_import_image); fm.addSeparator()
        self._a(fm,"Export as &Image...","Ctrl+E",self._on_export_image)
        self._a(fm,"Export as &Text...","Ctrl+T",self._on_export_text); fm.addSeparator()
        self._a(fm,"Puzzle &Collection...","Ctrl+Shift+C",self._on_collection)
        self._a(fm,"&Import from Text...","Ctrl+Shift+T",self._on_import_text); fm.addSeparator()
        self._recent_menu = fm.addMenu("&Recent Files")
        self._update_recent_menu(); fm.addSeparator()
        self._a(fm,"&Quit","Ctrl+Q",self.close)
        em = mb.addMenu("&Edit")
        self._a(em,"&Undo","Ctrl+Z",self.undo_stack.undo); self._a(em,"&Redo","Ctrl+Shift+Z",self.undo_stack.redo)
        em.addSeparator(); self._a(em,"Clear Grid","",self._on_clear); self._a(em,"Fill All","",self._on_fill_all)
        self._a(em,"Invert Grid","",self._on_invert); self._a(em,"Random Pattern","Ctrl+R",self._on_random)
        em.addSeparator()
        self._a(em,"Mirror &Horizontal","Ctrl+Shift+H",lambda:self._on_mirror("h"))
        self._a(em,"Mirror &Vertical","Ctrl+Shift+V",lambda:self._on_mirror("v"))
        em.addSeparator()
        self._a(em,"Rotate &CW 90","Ctrl+Shift+R",lambda:self._on_rotate("cw"))
        self._a(em,"Rotate &CCW 90","Ctrl+Shift+L",lambda:self._on_rotate("ccw"))
        em.addSeparator()
        self._a(em,"Shift Rows Up","",lambda:self._on_shift("rows",-1))
        self._a(em,"Shift Rows Down","",lambda:self._on_shift("rows",1))
        self._a(em,"Shift Cols Left","",lambda:self._on_shift("cols",-1))
        self._a(em,"Shift Cols Right","",lambda:self._on_shift("cols",1))
        em.addSeparator()
        self._a(em,"Undo History...","",self._show_undo_history)
        vm = mb.addMenu("&View")
        self._a(vm,"Zoom &In","Ctrl++",self.grid_widget.zoom_in); self._a(vm,"Zoom &Out","Ctrl+-",self.grid_widget.zoom_out)
        self._a(vm,"Zoom to &Fit","Ctrl+0",self._on_zoom_fit); vm.addSeparator()
        da = QAction("Dark Mode",self,checkable=True); da.toggled.connect(self._toggle_dark_mode); da.setShortcut("Ctrl+D"); vm.addAction(da); self._dark_menu=da
        pm = mb.addMenu("&Puzzle")
        self._a(pm,"Create Mode","",lambda:self._set_mode("create")); self._a(pm,"Play Mode","",lambda:self._set_mode("play"))
        pm.addSeparator(); self._a(pm,"Check Solution","",self._on_check_solution)
        self._a(pm,"Get Hint","Ctrl+H",self._on_hint)
        self._a(pm,"Auto-Solve","Ctrl+Shift+S",self._on_auto_solve)
        self._a(pm,"Step Solve (Animated)","Ctrl+Shift+A",self._on_step_solve)
        self._a(pm,"Reveal Solution","",self._on_reveal)
        hm = mb.addMenu("&Help"); self._a(hm,"&How to Use","F1",self._show_howto); self._a(hm,"&About","",self._show_about)

    def _a(self, menu, text, shortcut, cb):
        a = QAction(text, self)
        if shortcut: a.setShortcut(QKeySequence(shortcut))
        a.triggered.connect(cb); menu.addAction(a); return a

    def _build_toolbar(self):
        tb = self.addToolBar("Main"); tb.setMovable(False); tb.setIconSize(QSize(20,20))
        tb.setStyleSheet("QToolBar{background:#f8fafc;border-bottom:1px solid #e2e8f0;spacing:4px;padding:4px}QToolButton{padding:5px 10px;border-radius:4px}QToolButton:hover{background:#e2e8f0}")
        for t,c in [("New",self._on_new),("Save",self._on_save),("Open",self._on_load),("Samples",self._on_sample_puzzles)]:
            a=QAction(t,self); a.triggered.connect(c); tb.addAction(a)
        tb.addSeparator()
        for t,c in [("Undo",self.undo_stack.undo),("Redo",self.undo_stack.redo)]: a=QAction(t,self); a.triggered.connect(c); tb.addAction(a)
        tb.addSeparator()
        for t,c in [("Clear",self._on_clear),("Random",self._on_random)]: a=QAction(t,self); a.triggered.connect(c); tb.addAction(a)
        tb.addSeparator()
        for t,c in [("Create",lambda:self._set_mode("create")),("Play",lambda:self._set_mode("play")),("Check",self._on_check_solution),("Hint",self._on_hint),("Solve",self._on_auto_solve)]:
            a=QAction(t,self); a.triggered.connect(c); tb.addAction(a)
        tb.addSeparator()
        da=QAction("Dark",self,checkable=True); da.toggled.connect(self._toggle_dark_mode); tb.addAction(da); self._dark_tb=da

    def _build_statusbar(self):
        self.statusBar().showMessage("Ready | Click/drag: draw | Arrow keys: navigate | Drag & drop .json to load | Ctrl+Z: undo")
        self.statusBar().setStyleSheet("color:#64748b;")

    def _connect_signals(self):
        self.grid_widget.gridChanged.connect(self._update_stats)

    # ── Mode ──
    def _set_mode(self, mode):
        self.grid_widget.mode = mode; self.model._play_mode_active = (mode == "play")
        ic = mode == "create"
        self.mode_label.setText("CREATING MODE" if ic else "PLAYING MODE")
        self.mode_label.setStyleSheet(f"color:{'#2563eb' if ic else '#16a34a'};padding:4px 0px;")
        self.create_btn.setChecked(ic)
        if ic:
            self.create_btn.setStyleSheet("background:#2563eb;color:white;font-weight:bold;border:none;")
            self.play_btn.setStyleSheet("")
        else:
            if not self.model.is_valid_solution():
                QMessageBox.warning(self,"No Puzzle","Draw a puzzle first!")
                self.grid_widget.mode="create"; self.model._play_mode_active=False
                self.create_btn.setChecked(True); self.create_btn.setStyleSheet("background:#2563eb;color:white;font-weight:bold;border:none;")
                self.play_btn.setChecked(False); self.play_btn.setStyleSheet=""; return
            self.play_btn.setStyleSheet("background:#16a34a;color:white;font-weight:bold;border:none;")
            self.create_btn.setStyleSheet=""; self.model.clear_player_grid()
            self._start_timer(); self.move_count=0; self.hints_used=0
        self.check_btn.setEnabled(not ic); self.reveal_btn.setEnabled(not ic)
        self.solve_btn.setEnabled(not ic); self.hint_btn.setEnabled(not ic)
        self.clear_btn.setEnabled(ic); self.fill_all_btn.setEnabled(ic); self.invert_btn.setEnabled(ic)
        self.random_btn.setEnabled(ic); self.resize_btn.setEnabled(ic)
        self.sym_h_btn.setEnabled(ic); self.sym_v_btn.setEnabled(ic); self.sym_both_btn.setEnabled(ic)
        self.rot_cw_btn.setEnabled(ic); self.rot_ccw_btn.setEnabled(ic)
        self.sh_up_btn.setEnabled(ic); self.sh_dn_btn.setEnabled(ic)
        self.sh_lt_btn.setEnabled(ic); self.sh_rt_btn.setEnabled(ic)
        self.step_solve_btn.setEnabled(not ic)
        self.timer_label.setVisible(not ic); self.progress_bar.setVisible(not ic)
        self.move_label.setVisible(not ic); self.hint_label.setVisible(not ic)
        if ic: self._stop_timer()
        self._update_hint_label()
        self.move_label.setText("Moves: 0")
        undo_info = f" | Undo: {self.undo_stack.count()}" if self.undo_stack.count() > 0 else ""
        self.statusBar().showMessage(("Create Mode | Click: draw | Arrows: navigate" if ic else "Play Mode | Click: fill | Right-click: mark X | Arrows: navigate") + undo_info)
        self.grid_widget.set_error_cells(set()); self.grid_widget.update(); self._update_stats()

    # ── Timer ──
    def _start_timer(self):
        self.timer_seconds=0; self.timer_active=True; self.timer_label.setText("00:00"); self.progress_bar.setValue(0); self.timer.start()
    def _stop_timer(self): self.timer_active=False; self.timer.stop()
    def _tick_timer(self):
        if not self.timer_active: return
        self.timer_seconds += 1; m,s = divmod(self.timer_seconds,60)
        self.timer_label.setText(f"{m:02d}:{s:02d}")
        self.progress_bar.setValue(int(self.model.player_progress()))
        # Live error highlighting
        if self.grid_widget.show_errors and self.model.player_filled_count() > 0:
            self.grid_widget.set_error_cells(self.model.get_errors())
        self.grid_widget.update()
    def _record_best(self):
        if self.best_time is None or self.timer_seconds < self.best_time:
            self.best_time = self.timer_seconds; m,s = divmod(self.best_time,60); self.stat_best.setText(f"{m:02d}:{s:02d}")

    # ── Stats ──
    def _update_stats(self):
        self.stat_size.setText(f"{self.model.rows} x {self.model.cols}")
        f = self.model.filled_count(); t = self.model.total_cells()
        self.stat_filled.setText(f"{f} / {t}"); self.stat_pct.setText(f"{self.model.fill_percentage():.1f}%")
        self.stat_diff.setText(self.model.difficulty_rating())
        if self.grid_widget.mode == "play": self.progress_bar.setValue(int(self.model.player_progress()))

    # ── Zoom ──
    def _on_zoom_slider(self, v): self.grid_widget.set_zoom(v/100); self.zoom_label.setText(f"{v}%")
    def _on_zoom_fit(self): self.grid_widget.zoom_fit(); self.zoom_slider.setValue(100); self.zoom_label.setText("100%")

    # ── Dark Mode ──
    def _toggle_dark_mode(self, en):
        self.dark_mode = en; self.grid_widget.dark_mode = en; self.dark_cb.setChecked(en)
        self._dark_menu.setChecked(en); self._dark_tb.setChecked(en)
        app = QApplication.instance(); app.setStyleSheet(DARK_SS if en else LIGHT_SS)
        self.control_panel.setStyleSheet(PANEL_DARK if en else PANEL_LIGHT)
        tb = self.findChild(QToolBar)
        if tb:
            bg="#2a2a3c" if en else "#f8fafc"; br="#3a3a50" if en else "#e2e8f0"; hv="#45475a" if en else "#e2e8f0"; tc="#cdd6f4" if en else "black"
            tb.setStyleSheet(f"QToolBar{{background:{bg};border-bottom:1px solid {br};spacing:4px;padding:4px}}QToolButton{{padding:5px 10px;border-radius:4px;color:{tc}}}QToolButton:hover{{background:{hv}}}")
        self.statusBar().setStyleSheet(f"background:{'#2a2a3c' if en else '#f8fafc'};border-top:1px solid {'#3a3a50' if en else '#e2e8f0'};color:{'#a6adc8' if en else '#64748b'};")
        self.timer_label.setStyleSheet(f"color:{'#89b4fa' if en else '#64748b'};padding:4px 8px;font-size:14px;font-weight:bold;")
        self.move_label.setStyleSheet(f"color:{'#89b4fa' if en else '#64748b'};font-size:12px;padding:4px 8px;")
        self.hint_label.setStyleSheet(f"color:{'#89b4fa' if en else '#64748b'};font-size:12px;padding:4px 8px;")
        for b in [self.zoom_in_btn,self.zoom_out_btn,self.zoom_fit_btn]:
            b.setStyleSheet(f"background:{'#313244' if en else '#f9fafb'};color:{'#cdd6f4' if en else 'black'};border:1px solid {'#45475a' if en else '#d1d5db'};border-radius:6px;")
        self.zoom_label.setStyleSheet(f"color:{'#cdd6f4' if en else 'black'};")
        pb_bg="#313244" if en else "#f3f4f6"; pb_border="#45475a" if en else "#d1d5db"; pb_text="#cdd6f4" if en else "#374151"
        self.progress_bar.setStyleSheet(f"QProgressBar{{border:1px solid {pb_border};border-radius:4px;text-align:center;background:{pb_bg};color:{pb_text}}}QProgressBar::chunk{{background:#2563eb;border-radius:3px}}")
        self.grid_widget.update()

    # ── Error Highlighting ──
    def _toggle_error_hl(self, en):
        self.grid_widget.show_errors = en
        if en and self.grid_widget.mode == "play":
            self.grid_widget.set_error_cells(self.model.get_errors())
        else:
            self.grid_widget.set_error_cells(set())
        self.grid_widget.update()

    # ── Hint ──
    def _on_hint(self):
        if self.grid_widget.mode != "play": return
        if self.hints_used >= self.max_hints:
            QMessageBox.information(self, "No Hints Left", f"You've used all {self.max_hints} hints!"); return
        cell = self.model.get_hint()
        if cell:
            r, c = cell
            old = self.model.player_grid[r][c]
            self.model.player_grid[r][c] = NonogramModel.FILLED
            self.undo_stack.push(GridChangeCommand(self.model, r, c, old, NonogramModel.FILLED, "Hint"))
            self.hints_used += 1
            self._update_hint_label()
            self.move_count += 1; self.move_label.setText(f"Moves: {self.move_count}")
            self.grid_widget.update(); self._update_stats()
            self.statusBar().showMessage(f"Hint revealed cell ({r+1},{c+1})! {self.max_hints - self.hints_used} hints remaining")
            if self.model.check_player_solution(): self._on_solved()

    def _update_hint_label(self):
        remaining = self.max_hints - self.hints_used
        self.hint_label.setText(f"Hints: {remaining}/{self.max_hints}")

    # ── Actions ──
    def _on_resize(self):
        r,c = self.rows_spin.value(), self.cols_spin.value()
        if r != self.model.rows or c != self.model.cols:
            self.undo_stack.clear(); self.model.resize(r,c); self.grid_widget.update(); self._update_stats()
            self.statusBar().showMessage(f"Grid resized to {r}x{c}")

    def _on_clear(self):
        old = copy.deepcopy(self.model.solution); self.model.clear_solution()
        changes = [(r,c,old[r][c],NonogramModel.EMPTY) for r in range(self.model.rows) for c in range(self.model.cols) if old[r][c]!=0]
        if changes: self.undo_stack.push(BatchGridCommand(self.model, changes, "Clear Grid"))
        self.grid_widget.update(); self._update_stats(); self.statusBar().showMessage("Grid cleared")

    def _on_fill_all(self):
        old = copy.deepcopy(self.model.solution)
        for r in range(self.model.rows):
            for c in range(self.model.cols): self.model.solution[r][c] = NonogramModel.FILLED
        changes = [(r,c,old[r][c],NonogramModel.FILLED) for r in range(self.model.rows) for c in range(self.model.cols)]
        self.undo_stack.push(BatchGridCommand(self.model, changes, "Fill All"))
        self.grid_widget.update(); self._update_stats(); self.statusBar().showMessage("All cells filled")

    def _on_invert(self):
        old = copy.deepcopy(self.model.solution)
        for r in range(self.model.rows):
            for c in range(self.model.cols):
                self.model.solution[r][c] = NonogramModel.EMPTY if self.model.solution[r][c]==NonogramModel.FILLED else NonogramModel.FILLED
        changes = [(r,c,old[r][c],self.model.solution[r][c]) for r in range(self.model.rows) for c in range(self.model.cols) if old[r][c]!=self.model.solution[r][c]]
        if changes: self.undo_stack.push(BatchGridCommand(self.model, changes, "Invert Grid"))
        self.grid_widget.update(); self._update_stats(); self.statusBar().showMessage("Grid inverted")

    def _on_random(self):
        old = copy.deepcopy(self.model.solution)
        for r in range(self.model.rows):
            for c in range(self.model.cols): self.model.solution[r][c] = NonogramModel.FILLED if random.random()<0.35 else NonogramModel.EMPTY
        changes = [(r,c,old[r][c],self.model.solution[r][c]) for r in range(self.model.rows) for c in range(self.model.cols)]
        self.undo_stack.push(BatchGridCommand(self.model, changes, "Random Pattern"))
        self.grid_widget.update(); self._update_stats(); self.statusBar().showMessage("Random pattern generated")

    def _on_mirror(self, d):
        old = copy.deepcopy(self.model.solution); R, C = self.model.rows, self.model.cols
        if d in ("h","both"):
            for r in range(R):
                for c in range(C//2): self.model.solution[r][C-1-c] = self.model.solution[r][c]
        if d in ("v","both"):
            for r in range(R//2):
                for c in range(C): self.model.solution[R-1-r][c] = self.model.solution[r][c]
        changes = [(r,c,old[r][c],self.model.solution[r][c]) for r in range(R) for c in range(C) if old[r][c]!=self.model.solution[r][c]]
        if changes: self.undo_stack.push(BatchGridCommand(self.model, changes, f"Mirror {d}"))
        self.grid_widget.update(); self._update_stats(); self.statusBar().showMessage(f"Mirrored {d}")

    def _on_solved(self):
        self._stop_timer(); self._record_best(); m,s = divmod(self.timer_seconds,60)
        # Confetti!
        confetti = ConfettiWidget(self.grid_widget)
        confetti.start()
        QMessageBox.information(self, "Congratulations!", f"You solved the puzzle!\n\nTime: {m:02d}:{s:02d}\nMoves: {self.move_count}\nHints used: {self.hints_used}")
        self.statusBar().showMessage(f"Solved in {m:02d}:{s:02d} with {self.move_count} moves!")

    def _on_check_solution(self):
        if self.grid_widget.mode != "play": return
        self._stop_timer()
        if self.model.check_player_solution():
            self._on_solved()
        else:
            errors = self.model.get_errors()
            self.grid_widget.set_error_cells(set(errors) if self.grid_widget.show_errors else set())
            self.grid_widget.update()
            msg = "Not quite right yet. Check these cells:\n"
            if len(errors) > 10: msg += "\n".join(f"  Row {r+1}, Col {c+1}" for r,c in errors[:10]) + f"\n  ... and {len(errors)-10} more"
            else: msg += "\n".join(f"  Row {r+1}, Col {c+1}" for r,c in errors)
            QMessageBox.information(self, "Keep Trying!", msg)
            self.statusBar().showMessage(f"{len(errors)} incorrect cells"); self.timer_active=True; self.timer.start()

    def _on_auto_solve(self):
        if self.grid_widget.mode != "play": return
        if QMessageBox.question(self,"Auto-Solve","Run the line-solving algorithm?",QMessageBox.Yes|QMessageBox.No,QMessageBox.No)==QMessageBox.Yes:
            self._stop_timer(); solved = NonogramSolver.solve(self.model); self.grid_widget.update(); self._update_stats()
            if solved: self._on_solved()
            else: QMessageBox.information(self,"Partial Solve","Algorithm made progress but couldn't fully solve.\nContinue manually or reveal.")
            self.statusBar().showMessage("Auto-solve complete" if solved else "Partially solved")

    def _on_reveal(self):
        if QMessageBox.question(self,"Reveal","Reveal the solution?",QMessageBox.Yes|QMessageBox.No,QMessageBox.No)==QMessageBox.Yes:
            self._stop_timer()
            for r in range(self.model.rows):
                for c in range(self.model.cols): self.model.player_grid[r][c] = self.model.solution[r][c]
            self.grid_widget.update(); self._update_stats(); self.statusBar().showMessage("Solution revealed")

    def _on_new(self):
        dlg = NewPuzzleDialog(self.model.rows, self.model.cols, self)
        if dlg.exec()==QDialog.Accepted:
            r,c = dlg.get_size(); self.undo_stack.clear(); self.model.resize(r,c)
            self.rows_spin.setValue(r); self.cols_spin.setValue(c); self._set_mode("create")
            self.grid_widget.update(); self.current_file=None; self.best_time=None; self.stat_best.setText("--:--")
            self._update_stats(); self.statusBar().showMessage(f"New {r}x{c} puzzle")

    def _on_save(self):
        if not self.model.is_valid_solution(): QMessageBox.warning(self,"Empty","Draw a puzzle first!"); return
        dlg = SavePuzzleDialog(self.model.title, self)
        if dlg.exec()!=QDialog.Accepted: return
        title = dlg.get_title()
        if self.current_file: path=self.current_file
        else:
            sn = title.replace(" ","_").lower() or "nonogram"
            path,_ = QFileDialog.getSaveFileName(self,"Save",f"{sn}.json","Nonogram (*.json);;All (*)")
        if path:
            self.model.title=title; data=self.model.to_dict()
            if self.best_time is not None: data["best_time"]=self.best_time
            with open(path,'w') as f: json.dump(data,f,indent=2)
            self.current_file=path; self.statusBar().showMessage(f"Saved to {path}")

    def _on_load(self):
        path,_ = QFileDialog.getOpenFileName(self,"Open","","Nonogram (*.json);;All (*)")
        if path:
            try:
                with open(path,'r') as f: data=json.load(f)
                self.undo_stack.clear(); self.model.from_dict(data)
                self.rows_spin.setValue(self.model.rows); self.cols_spin.setValue(self.model.cols)
                bt=data.get("best_time")
                if bt is not None: m,s=divmod(bt,60); self.stat_best.setText(f"{m:02d}:{s:02d}"); self.best_time=bt
                else: self.stat_best.setText("--:--"); self.best_time=None
                self._set_mode("create"); self.grid_widget.update(); self.current_file=path; self._update_stats()
                self._add_recent_file(path)
                self.statusBar().showMessage(f"Loaded {path}")
            except Exception as e: QMessageBox.critical(self,"Error",f"Failed to load:\n{e}")

    def _on_sample_puzzles(self):
        dlg = SamplePuzzleDialog(self)
        if dlg.exec()==QDialog.Accepted:
            data = dlg.get_selected()
            if data:
                self.undo_stack.clear()
                self.model.rows=data["rows"]; self.model.cols=data["cols"]
                self.model.solution=[list(r) for r in data["solution"]]; self.model.title=data.get("title","")
                self.model.player_grid=[[NonogramModel.EMPTY]*self.model.cols for _ in range(self.model.rows)]
                self.rows_spin.setValue(self.model.rows); self.cols_spin.setValue(self.model.cols)
                self.best_time=None; self.stat_best.setText("--:--")
                self._set_mode("create"); self.current_file=None; self.grid_widget.update(); self._update_stats()
                self.statusBar().showMessage(f"Loaded: {self.model.title}")

    def _on_import_image(self):
        if not HAS_PIL:
            QMessageBox.warning(self,"Missing Dependency","Install Pillow to import images:\n\npip install Pillow")
            return
        path,_ = QFileDialog.getOpenFileName(self,"Import Image","","Images (*.png *.jpg *.jpeg *.bmp *.gif);;All (*)")
        if not path: return
        dlg = ImportImageDialog(self)
        if dlg.exec()!=QDialog.Accepted: return
        try:
            img = PILImage.open(path).convert("L")
            target_r, target_c = dlg.rows_spin.value(), dlg.cols_spin.value()
            img = img.resize((target_c, target_r), PILImage.LANCZOS)
            threshold = dlg.threshold_slider.value()
            invert = dlg.invert_cb.isChecked()
            self.undo_stack.clear()
            self.model.resize(target_r, target_c)
            for r in range(target_r):
                for c in range(target_c):
                    px = img.getpixel((c, r))
                    dark = px < threshold
                    if invert: dark = not dark
                    self.model.solution[r][c] = NonogramModel.FILLED if dark else NonogramModel.EMPTY
            self.rows_spin.setValue(target_r); self.cols_spin.setValue(target_c)
            self._set_mode("create"); self.current_file=None; self.grid_widget.update(); self._update_stats()
            filled = self.model.filled_count()
            self.statusBar().showMessage(f"Imported image: {target_r}x{target_c}, {filled} cells filled")
        except Exception as e:
            QMessageBox.critical(self,"Import Error",f"Failed to import image:\n{e}")

    def _on_export_text(self):
        if not self.model.is_valid_solution(): QMessageBox.warning(self,"Empty","Draw a puzzle first!"); return
        m = self.model; title = m.title or "Nonogram"
        lines = [f"=== {title} ({m.rows}x{m.cols}) ===", ""]
        lines.append("Row clues (top to bottom):")
        for r in range(m.rows): lines.append(f"  Row {r+1}: {', '.join(str(n) for n in m.get_row_clues(r))}")
        lines.append("")
        lines.append("Column clues (left to right):")
        for c in range(m.cols): lines.append(f"  Col {c+1}: {', '.join(str(n) for n in m.get_col_clues(c))}")
        lines.append("")
        lines.append("Solution grid (# = filled, . = empty):")
        for r in range(m.rows):
            lines.append("  " + "".join("#" if m.solution[r][c]==NonogramModel.FILLED else "." for c in range(m.cols)))
        text = "\n".join(lines)
        dlg = TextExportDialog(text, self)
        dlg.exec()

    def _on_export_image(self):
        if not self.model.is_valid_solution(): QMessageBox.warning(self,"Empty","Draw a puzzle first!"); return
        dlg = ExportOptionsDialog(self)
        if dlg.exec()!=QDialog.Accepted: return
        clues_only = dlg.clues_only_cb.isChecked(); include_title = dlg.include_title_cb.isChecked()
        high_res = dlg.high_res_cb.isChecked(); dark_bg = dlg.dark_bg_cb.isChecked()
        with_coords = dlg.with_coords_cb.isChecked()
        path,_ = QFileDialog.getSaveFileName(self,"Export","nonogram.png","PNG (*.png);;All (*)")
        if not path: return
        scale = 2 if high_res else 1; m = self.model; cs = 36*scale
        mrc, mcc = m.max_row_clue_len(), m.max_col_clue_len()
        ml = mrc*22*scale+20*scale; mt = mcc*22*scale+20*scale
        coord_extra = 20*scale if with_coords else 0
        th = 50*scale if include_title and m.title else 0
        tw = ml + m.cols*cs + 20*scale + coord_extra
        tt = mt + m.rows*cs + 20*scale + coord_extra + th
        pixmap = QPixmap(tw, tt)
        bg = QColor(30,30,40) if dark_bg else QColor(255,255,255)
        tc = QColor(200,200,220) if dark_bg else QColor(30,41,59)
        ec = QColor(45,45,60) if dark_bg else QColor(255,255,255)
        fc = QColor(59,130,246) if dark_bg else QColor(30,41,59)
        bc = QColor(70,70,90) if dark_bg else QColor(200,210,220)
        tkc = QColor(100,100,120) if dark_bg else QColor(100,110,120)
        pixmap.fill(bg)
        p = QPainter(pixmap); p.setRenderHint(QPainter.Antialiasing,False)
        ox, oy = ml+coord_extra, mt+coord_extra+th
        if include_title and m.title:
            p.setFont(QFont("Segoe UI",18*scale,QFont.Bold)); p.setPen(QPen(tc))
            p.drawText(QRectF(0,10*scale,tw,40*scale),Qt.AlignCenter,m.title)
        # Coordinates
        if with_coords:
            p.setFont(QFont("Segoe UI",8*scale)); p.setPen(QPen(QColor(150,150,170) if dark_bg else QColor(148,163,184)))
            for c in range(m.cols):
                p.drawText(QRectF(ox+c*cs, oy-mcc*22*scale-18*scale, cs, 16*scale), Qt.AlignRight, str(c+1))
            for r in range(m.rows):
                p.drawText(QRectF(ox-mrc*22*scale-18*scale, oy+r*cs, 16*scale, cs), Qt.AlignRight|Qt.AlignVCenter, str(r+1))
        col_clues = m.get_all_col_clues(); mccl = m.max_col_clue_len()
        p.setFont(QFont("Segoe UI",11*scale,QFont.Bold))
        for c,clues in enumerate(col_clues):
            cx=ox+c*cs+cs/2
            for i,num in enumerate(clues):
                cy=oy-(mccl-i)*22*scale+10*scale; p.setPen(QPen(tc))
                p.drawText(QRectF(cx-cs/2,cy,cs,20*scale),Qt.AlignCenter,str(num))
        row_clues=m.get_all_row_clues(); mrcl=m.max_row_clue_len()
        for r,clues in enumerate(row_clues):
            cy=oy+r*cs+cs/2
            for i,num in enumerate(clues):
                cx=ox-(mrcl-i)*22*scale+10*scale; p.setPen(QPen(tc))
                p.drawText(QRectF(cx,cy-10*scale,20*scale,20*scale),Qt.AlignCenter,str(num))
        grid = [[NonogramModel.EMPTY]*m.cols for _ in range(m.rows)] if clues_only else m.solution
        for r in range(m.rows):
            for c in range(m.cols):
                rect=QRectF(ox+c*cs,oy+r*cs,cs,cs)
                p.fillRect(rect,fc if grid[r][c]==NonogramModel.FILLED else ec)
                p.setPen(QPen(bc,scale)); p.setBrush(Qt.NoBrush); p.drawRect(rect)
        p.setPen(QPen(tkc,2*scale))
        for r in range(m.rows+1):
            if r%5==0: y=oy+r*cs; p.drawLine(int(ox),int(y),int(ox+m.cols*cs),int(y))
        for c in range(m.cols+1):
            if c%5==0: x=ox+c*cs; p.drawLine(int(x),int(oy),int(x),int(oy+m.rows*cs))
        p.setPen(QPen(tkc,3*scale)); p.drawRect(QRectF(ox,oy,m.cols*cs,m.rows*cs))
        p.setPen(QPen(bc,scale))
        p.drawLine(int(ox),int(oy),int(ox),int(oy-mccl*22*scale))
        p.drawLine(int(ox),int(oy),int(ox-mrcl*22*scale),int(oy))
        p.end(); pixmap.save(path); self.statusBar().showMessage(f"Exported to {path}")


    # ── Rotate ──
    def _on_rotate(self, direction):
        old = self.model.snapshot()
        if direction == "cw":
            self.model.rotate_cw()
        else:
            self.model.rotate_ccw()
        new = self.model.snapshot()
        self.undo_stack.push(ModelSnapshotCommand(self.model, old, new, f"Rotate {direction}"))
        self.rows_spin.setValue(self.model.rows); self.cols_spin.setValue(self.model.cols)
        self.grid_widget._selected_cell = (min(self.grid_widget._selected_cell[0], self.model.rows-1),
                                            min(self.grid_widget._selected_cell[1], self.model.cols-1))
        self.grid_widget.update(); self._update_stats()
        self.statusBar().showMessage(f"Rotated {direction}")

    # ── Shift ──
    def _on_shift(self, axis, direction):
        old = self.model.snapshot()
        if axis == "rows":
            self.model.shift_rows(direction)
            label = "down" if direction == 1 else "up"
        else:
            self.model.shift_cols(direction)
            label = "right" if direction == 1 else "left"
        new = self.model.snapshot()
        self.undo_stack.push(ModelSnapshotCommand(self.model, old, new, f"Shift {axis} {label}"))
        self.grid_widget.update(); self._update_stats()
        self.statusBar().showMessage(f"Shifted {axis} {label}")

    # ── Step Solve Animation ──
    def _on_step_solve(self):
        if self.grid_widget.mode != "play": return
        if self._step_timer.isActive():
            self._step_timer.stop()
            self.grid_widget._step_highlight.clear()
            self.grid_widget.update()
            self.step_solve_btn.setText("Step Solve")
            self.statusBar().showMessage("Step solve stopped")
            return
        # Save current player grid and run solver
        saved_pg = copy.deepcopy(self.model.player_grid)
        old_pg = copy.deepcopy(self.model.player_grid)
        solved = NonogramSolver.solve(self.model)
        # Collect changes
        changes = []
        for r in range(self.model.rows):
            for c in range(self.model.cols):
                if old_pg[r][c] != self.model.player_grid[r][c]:
                    changes.append((r, c, old_pg[r][c], self.model.player_grid[r][c]))
        # Restore old grid for animation
        self.model.player_grid = saved_pg
        if not changes:
            QMessageBox.information(self, "No Progress", "The solver couldn\'t determine any new cells from the current state.\nTry filling or marking more cells first.")
            return
        self._step_changes = changes
        self._step_index = 0
        self.grid_widget._step_highlight.clear()
        self._step_timer.start()
        self.step_solve_btn.setText("Stop")
        self.statusBar().showMessage(f"Step solving... {len(changes)} cells to reveal")

    def _step_solve_tick(self):
        if self._step_index >= len(self._step_changes):
            self._step_timer.stop()
            # Keep highlight for a moment then clear
            QTimer.singleShot(1500, lambda: (self.grid_widget._step_highlight.clear(), self.grid_widget.update()))
            self.step_solve_btn.setText("Step Solve")
            self._update_stats()
            if self.model.check_player_solution():
                self._on_solved()
            else:
                self.statusBar().showMessage(f"Step solve done — {len(self._step_changes)} cells revealed")
            return
        r, c, old, new = self._step_changes[self._step_index]
        self.model.player_grid[r][c] = new
        self.grid_widget._step_highlight.add((r, c))
        self._step_index += 1
        self.move_count += 1
        self.move_label.setText(f"Moves: {self.move_count}")
        self.progress_bar.setValue(int(self.model.player_progress()))
        # Live error highlighting
        if self.grid_widget.show_errors:
            self.grid_widget.set_error_cells(self.model.get_errors())
        self.grid_widget.update()

    # ── Keyboard Nav Toggle ──
    def _toggle_keyboard_nav(self, en):
        self.grid_widget._show_selection = en
        if en:
            self.grid_widget.setFocus()
        self.grid_widget.update()

    # ── Drag and Drop ──
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(u.toLocalFile().endswith('.json') or u.toLocalFile().endswith('.ncol') for u in urls):
                event.acceptProposedAction()
                return
        event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if not path:
                continue
            if path.endswith('.ncol'):
                self._load_collection_file(path)
                return
            elif path.endswith('.json'):
                self._load_file_direct(path)
                return
        event.ignore()

    def _load_file_direct(self, path):
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            # Could be a collection or single puzzle
            if isinstance(data, list) or (isinstance(data, dict) and "puzzles" in data):
                self._load_collection_file(path)
                return
            self.undo_stack.clear()
            self.model.from_dict(data)
            self.rows_spin.setValue(self.model.rows); self.cols_spin.setValue(self.model.cols)
            bt = data.get("best_time")
            if bt is not None:
                m, s = divmod(bt, 60); self.stat_best.setText(f"{m:02d}:{s:02d}"); self.best_time = bt
            else:
                self.stat_best.setText("--:--"); self.best_time = None
            self._add_recent_file(path)
            self._set_mode("create"); self.current_file = path
            self.grid_widget.update(); self._update_stats()
            self.statusBar().showMessage(f"Dropped & loaded: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load:\n{e}")

    def _load_collection_file(self, path):
        dlg = CollectionDialog(self)
        if dlg.load_collection(path):
            dlg.add_btn.clicked.connect(lambda: (dlg.add_puzzle(self.model), None))
            dlg.remove_btn.clicked.connect(lambda: (dlg._remove_selected(), None))
            dlg.load_btn.clicked.connect(lambda: (self._load_from_collection(dlg), dlg.accept()))
            # Monkey-patch remove method
            def _remove():
                row = dlg.puzzle_list.currentRow()
                if 0 <= row < len(dlg.puzzles):
                    dlg.puzzles.pop(row)
                    dlg._refresh_list()
            dlg._remove_selected = _remove
            dlg.exec()

    def _load_from_collection(self, dlg):
        data = dlg.get_selected()
        if not data: return
        self.undo_stack.clear()
        self.model.rows = data["rows"]; self.model.cols = data["cols"]
        self.model.solution = [list(r) for r in data["solution"]]
        self.model.title = data.get("title", "")
        self.model.player_grid = [[NonogramModel.EMPTY]*self.model.cols for _ in range(self.model.rows)]
        self.rows_spin.setValue(self.model.rows); self.cols_spin.setValue(self.model.cols)
        self.best_time = None; self.stat_best.setText("--:--")
        self._set_mode("create"); self.current_file = None
        self.grid_widget.update(); self._update_stats()
        self.statusBar().showMessage(f"Loaded from collection: {self.model.title}")

    # ── Recent Files ──
    def _add_recent_file(self, path):
        if path in self._recent_files:
            self._recent_files.remove(path)
        self._recent_files.insert(0, path)
        self._recent_files = self._recent_files[:self._max_recent]
        self._update_recent_menu()

    def _update_recent_menu(self):
        if hasattr(self, '_recent_menu'):
            self._recent_menu.clear()
            if not self._recent_files:
                self._recent_menu.addAction("(No recent files)").setEnabled(False)
                return
            for path in self._recent_files:
                name = os.path.basename(path)
                self._recent_menu.addAction(f"{name}  ({path})",
                    lambda p=path: self._load_file_direct(p))
            self._recent_menu.addSeparator()
            self._recent_menu.addAction("Clear Recent", self._clear_recent)

    def _clear_recent(self):
        self._recent_files.clear()
        self._update_recent_menu()

    # ── Collection ──
    def _on_collection(self):
        dlg = CollectionDialog(self)
        dlg.add_btn.clicked.connect(lambda: (dlg.add_puzzle(self.model), None))
        def _remove():
            row = dlg.puzzle_list.currentRow()
            if 0 <= row < len(dlg.puzzles):
                dlg.puzzles.pop(row); dlg._refresh_list()
        dlg.remove_btn.clicked.connect(_remove)
        dlg.load_btn.clicked.connect(lambda: (self._load_from_collection(dlg), dlg.accept()))
        # Add save button
        dlg.add_btn.setText("Add Current + Save")
        dlg.exec()
        # Auto-save if puzzles were added
        if dlg.puzzles:
            path, _ = QFileDialog.getSaveFileName(self, "Save Collection", "my_collection.ncol",
                                                   "Nonogram Collection (*.ncol);;JSON (*.json);;All (*)")
            if path:
                dlg.save_collection(path)
                self.statusBar().showMessage(f"Collection saved: {path} ({len(dlg.puzzles)} puzzles)")

    # ── Import from Text ──
    def _on_import_text(self):
        dlg = ImportTextDialog(self)
        if dlg.exec() == QDialog.Accepted:
            grid = dlg.get_grid()
            if not grid: return
            rows, cols = len(grid), len(grid[0])
            self.undo_stack.clear()
            self.model.resize(rows, cols)
            for r in range(rows):
                for c in range(cols):
                    self.model.solution[r][c] = grid[r][c]
            self.rows_spin.setValue(rows); self.cols_spin.setValue(cols)
            self._set_mode("create"); self.current_file = None
            self.grid_widget.update(); self._update_stats()
            filled = self.model.filled_count()
            self.statusBar().showMessage(f"Imported from text: {rows}x{cols}, {filled} cells filled")

    # ── Undo History Display ──
    def _show_undo_history(self):
        if self.undo_stack.count() == 0:
            QMessageBox.information(self, "History", "No actions to show."); return
        text = "Undo Stack (most recent first):\n\n"
        for i in range(self.undo_stack.count() - 1, -1, -1):
            cmd = self.undo_stack.command(i)
            text += f"  {i+1}. {cmd.text()}\n"
        idx = self.undo_stack.index()
        text += f"\nCurrent position: {idx + 1} / {self.undo_stack.count()}"
        QMessageBox.information(self, "Undo History", text)

    def _show_about(self):
        QMessageBox.about(self,"About Nonogram Creator v4.0",
            "<h3>Nonogram Puzzle Creator v4.0</h3>"
            "<p>Full-featured nonogram puzzle creator and player with 30+ built-in puzzles.</p>"
            "<p><b>v4:</b> Keyboard navigation, step-solve animation, rotate/shift, drag-and-drop, "
            "puzzle collections, import from text, cell counts, undo history</p>"
            "<p>v3: 30+ puzzles, confetti, hints, error highlight, image import, text export, fill colors, coordinates</p>"
            "<p>v2: Undo/redo, drag paint, solver, dark mode, zoom, timer</p>"
            "<p>v1: Core puzzle creator & player</p>")

    def _show_howto(self):
        QMessageBox.information(self,"How to Use",
            "<h3>Creating</h3><ol>"
            "<li>Set grid size, left-click/drag to draw</li>"
            "<li>Use Symmetry (H/V/Both) for patterns</li>"
            "<li>Rotate (CW/CCW) and Shift rows/cols for designs</li>"
            "<li>Pick a Fill Color from the dropdown</li>"
            "<li>Import an image or text: File menu</li>"
            "<li>Ctrl+Z undo, Ctrl+Shift+Z redo</li></ol>"
            "<h3>Playing</h3><ol>"
            "<li>Switch to Play Mode</li>"
            "<li>Left-click fill, Right-click mark X, drag to paint</li>"
            "<li><b>Keyboard:</b> Arrow keys navigate, Space fills, X marks, Delete clears</li>"
            "<li>Ctrl+H for a Hint, Step Solve for animated solving</li>"
            "<li>Enable Error Highlighting in Settings</li>"
            "<li>Check Solution when done — confetti on success!</li></ol>"
            "<h3>Collections & Sharing</h3>"
            "<p>Save/Load puzzle collections (.ncol), drag-and-drop .json files, "
            "Export as Image (PNG) or Text</p>")


def main():
    app = QApplication(sys.argv); app.setStyle("Fusion"); app.setStyleSheet(LIGHT_SS)
    w = NonogramCreatorWindow(); w.show(); sys.exit(app.exec())

if __name__ == "__main__":
    main()