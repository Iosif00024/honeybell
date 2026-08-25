from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)
class FindBar(QWidget):
    find_requested = Signal(str, bool)  # text, backward
    closed = Signal()
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("findBar")
        self.hide()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)
        self.input = QLineEdit(objectName="findInput")
        self.input.setPlaceholderText("Find in page")
        self.input.returnPressed.connect(lambda: self.find_requested.emit(
            self.input.text(), False))
        self.input.textChanged.connect(self.reset_count)
        layout.addWidget(self.input)
        self.count_label = QLabel("", objectName="findCount")
        layout.addWidget(self.count_label)
        previous = QPushButton("\u2191", objectName="findButton")
        previous.setFixedSize(30, 26)
        previous.setToolTip("Previous (Shift+F3)")
        previous.clicked.connect(lambda: self.find_requested.emit(
            self.input.text(), True))
        layout.addWidget(previous)
        nxt = QPushButton("\u2193", objectName="findButton")
        nxt.setFixedSize(30, 26)
        nxt.setToolTip("Next (F3)")
        nxt.clicked.connect(lambda: self.find_requested.emit(
            self.input.text(), False))
        layout.addWidget(nxt)
        close = QPushButton("\u00d7", objectName="findButton")
        close.setFixedSize(30, 26)
        close.setToolTip("Closed (Esc)")
        close.clicked.connect(self.close_bar)
        layout.addWidget(close)
        escape = QShortcut(QKeySequence("Escape"), self)
        escape.setContext(Qt.WidgetWithChildrenShortcut)
        escape.activated.connect(self.close_bar)
    def open(self):
        self.show()
        self.raise_()
        self.input.setFocus()
        self.input.selectAll()
    def close_bar(self):
        self.hide()
        self.reset_count()
        self.closed.emit()
    def text(self):
        return self.input.text()
    def reset_count(self):
        self.count_label.setText("")
        self.adjustSize()
    def set_count(self, matches, active):
        if not self.input.text():
            self.count_label.setText("")
        elif matches:
            self.count_label.setText(f"{active}/{matches}")
        else:
            self.count_label.setText("No matches")
        self.adjustSize()