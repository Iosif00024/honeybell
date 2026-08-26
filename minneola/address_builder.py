from functools import partial
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
class AddressBuilder(QWidget):
    address_changed = Signal(str)
    navigate_requested = Signal()
    open_url = Signal(str)
    KEYBOARD_ROWS = (
        "1234567890-=",
        "qwertyuiop[]",
        "asdfghjkl;'",
        "zxcvbnm,./",
    )
    SHIFT_MAP = {
        "1": "!", "2": "@", "3": "#", "4": "$", "5": "%",
        "6": "^", "7": "&", "8": "*", "9": "(", "0": ")",
        "-": "_", "=": "+", "[": "{", "]": "}",
        ";": ":", "'": '"', ",": "<", ".": ">", "/": "?",
    }
    def __init__(self, bookmarks=None):
        super().__init__()
        self.address = ""
        self.shift_enabled = False
        self.setFocusPolicy(Qt.StrongFocus)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        self.hint = QLabel(objectName="hint")
        layout.addWidget(self.hint)
        if bookmarks:
            tiles = QHBoxLayout()
            tiles.setSpacing(7)
            for item in bookmarks[:8]:
                tile = QPushButton(
                    (item.get("title") or item["url"])[:16],
                    objectName="characterButton")
                tile.setToolTip(item["url"])
                tile.setFixedHeight(40)
                tile.clicked.connect(
                    lambda checked=False, url=item["url"]: self.open_url.emit(url))
                tiles.addWidget(tile, 1)
            layout.insertLayout(1, tiles)
        keyboard = QWidget()
        self.keyboard_layout = QVBoxLayout(keyboard)
        self.keyboard_layout.setContentsMargins(12, 12, 12, 12)
        self.keyboard_layout.setSpacing(7)
        scroll = QScrollArea(objectName="optionsScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(keyboard)
        layout.addWidget(scroll, 1)
        self.create_keyboard()
    def display_character(self, character):
        value = self.character_to_append(character)
        return (self.address + value)[-4:] or value
    def character_to_append(self, character):
        if self.shift_enabled:
            return self.SHIFT_MAP.get(character, character.upper())
        return character
    def create_key(self, text, character=None, callback=None, width=None):
        button = QPushButton(text, objectName="characterButton")
        button.setFocusPolicy(Qt.StrongFocus)
        if width:
            button.setFixedSize(width, 48)
        else:
            button.setMinimumWidth(48)
            button.setMinimumHeight(52)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        if character is not None:
            button.clicked.connect(partial(self.append_character, character))
        elif callback:
            button.clicked.connect(callback)
        return button
    def create_keyboard(self):
        self.clear_keyboard()
        for row_number, characters in enumerate(self.KEYBOARD_ROWS):
            row = QHBoxLayout()
            row.setSpacing(7)
            indent = row_number * 18
            row.setContentsMargins(indent, 0, indent, 0)
            for character in characters:
                button = self.create_key(
                    self.display_character(character), character=character
                )
                row.addWidget(button, 1)
            self.keyboard_layout.addLayout(row)
        controls = QHBoxLayout()
        controls.setSpacing(7)
        shift = QPushButton("\u21e7", objectName="characterButton")
        shift.setToolTip("Shift")
        shift.setCheckable(True)
        shift.setChecked(self.shift_enabled)
        shift.setFixedSize(76, 48)
        shift.clicked.connect(self.toggle_shift)
        controls.addWidget(shift)
        controls.addWidget(self.create_key("\u232b", callback=self.remove_last, width=76))
        controls.addWidget(self.create_key(
            "space", callback=partial(self.append_character, " "), width=160))
        controls.addWidget(self.create_key("x", callback=self.clear, width=76))
        controls.addWidget(self.create_key(
            "\u2192", callback=self.navigate_requested.emit, width=76))
        self.keyboard_layout.addLayout(controls)
        self.update_hint()
    def clear_keyboard(self):
        while self.keyboard_layout.count():
            item = self.keyboard_layout.takeAt(0)
            if item.layout():
                self.delete_layout(item.layout())
            elif item.widget():
                item.widget().deleteLater()
    def delete_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.layout():
                self.delete_layout(item.layout())
            elif item.widget():
                item.widget().deleteLater()
    def toggle_shift(self):
        self.shift_enabled = not self.shift_enabled
        self.setFocus()
        self.create_keyboard()
    def append_character(self, character):
        self.address += self.character_to_append(character)
        self.address_changed.emit(self.address)
        if self.shift_enabled:
            self.shift_enabled = False
        self.setFocus()
        self.create_keyboard()
    def remove_last(self):
        self.address = self.address[:-1]
        self.address_changed.emit(self.address)
        self.setFocus()
        self.create_keyboard()
    def clear(self):
        self.address = ""
        self.shift_enabled = False
        self.address_changed.emit(self.address)
        self.setFocus()
        self.create_keyboard()
    def update_hint(self):
        self.hint.setText(self.address)