import os
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from PySide6.QtCore import QStandardPaths, QUrl, Qt, Signal, QTimer
from PySide6.QtGui import QCursor, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedLayout,
    QTabBar,
    QTabWidget,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView
def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), relative_path)
STYLE = """
QApplication,
QMainWindow,
QWidget {
    color: #5a1f12;
    background: #f28b38;
}
QToolBar#navigationBar {
    background: #d93616;
    border: none;
    border-bottom: 3px solid #8f1d0e;
    padding: 8px 10px;
    spacing: 8px;
}
QPushButton#toolbarButton {
    color: #5a1f12;
    background: #f47b32;
    border: 1px solid #bc3519;
    border-radius: 9px;
    padding: 7px 14px;
    min-width: 34px;
    min-height: 30px;
    font: bold 11pt "Segoe UI";
}
QPushButton#toolbarButton:hover {
    color: #ffd0a8;
    background: #a92512;
    border-color: #751508;
}
QPushButton#toolbarButton:pressed {
    color: #ffd0a8;
    background: #751508;
}
QPushButton#toolbarButton:disabled {
    color: #a94b2c;
    background: #dd6730;
    border-color: #b84424;
}
QLineEdit#addressBar {
    color: #5a1f12;
    background: #f58c45;
    border: 2px solid #bd3518;
    border-radius: 11px;
    padding: 8px 13px;
    min-height: 30px;
    font: 11pt "Segoe UI";
    selection-background-color: #a92512;
    selection-color: #ffd0a8;
}
QLineEdit#addressBar:hover {
    background: #f79b55;
    border-color: #92200f;
}
QLineEdit#addressBar:focus {
    background: #f9a15d;
    border: 2px solid #751508;
}
QTabWidget {
    background: #ef7935;
    border: 0px solid transparent;
}
QTabWidget::pane {
    background: #ef7935;
    border: 0px solid transparent;
}
QTabWidget::tab-bar {
    left: 0px;
}
QTabBar {
    background: transparent;
    border: none;
    outline: none;
}
QTabBar::tab {
    color: #5a1f12;
    background: #ed7040;
    border: 1px solid #b83a24;
    border-radius: 8px;
    padding: 8px 48px 8px 14px;
    margin: 5px 4px 5px 0;
    min-width: 120px;
    font: 10pt "Segoe UI";
}
QTabBar::tab:hover {
    color: #ffd0a8;
    background: #c83a20;
    border-color: #8f1d0e;
}
QTabBar::tab:selected {
    color: #5a1f12;
    background: #f58c45;
    border: 2px solid #9f2714;
}
QTabBar::tab:focus, QTabBar::tab:selected:focus {
    outline: none;
}
QToolButton#tabCloseButton {
    color: #6f2115;
    background: #ed7040;
    border: none;
    border-radius: 5px;
    font: bold 13pt "Segoe UI";
}
QToolButton#tabCloseButton:hover {
    color: #ffd0a8;
    background: #8f1d0e;
}
QLabel#hint {
    color: #5a1f12;
    background: #f58c45;
    border: 2px solid #c44720;
    border-radius: 9px;
    padding: 9px 11px;
    font: 10pt "Segoe UI";
}
QScrollArea#optionsScroll {
    background: #ed7938;
    border: 2px solid #bc3519;
    border-radius: 11px;
}
QScrollArea#optionsScroll QWidget {
    background: #ed7938;
}
QPushButton#characterButton {
    color: #5a1f12;
    background: #ee8845;
    border: 2px solid #c14a24;
    border-radius: 9px;
    min-height: 52px;
    font: 12pt "Segoe UI";
}
QPushButton#characterButton:hover {
    color: #ffd0a8;
    background: #d93616;
    border-color: #8f1d0e;
}
QPushButton#characterButton:pressed {
    color: #ffd0a8;
    background: #9f2714;
    border-color: #751508;
}
QPushButton#characterButton:checked {
    color: #ffd0a8;
    background: #b92819;
    border-color: #751508;
}
QScrollBar:vertical {
    background: #c44720;
    width: 12px;
    margin: 2px;
    border-radius: 6px;
}
QScrollBar::handle:vertical {
    background: #8f1d0e;
    min-height: 30px;
    border-radius: 6px;
}
QScrollBar::handle:vertical:hover {
    background: #621108;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background: #c44720;
    height: 12px;
    margin: 2px;
    border-radius: 6px;
}
QScrollBar::handle:horizontal {
    background: #8f1d0e;
    min-width: 30px;
    border-radius: 6px;
}
QScrollBar::handle:horizontal:hover {
    background: #621108;
}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0px;
}
"""
class AddressBuilder(QWidget):
    address_changed = Signal(str)
    navigate_requested = Signal()
    KEYBOARD_ROWS = (
        "1234567890-=",
        "qwertyuiop[]",
        "asdfghjkl;'",
        "zxcvbnm,./",
    )
    SHIFT_MAP = {
        "1": "!",
        "2": "@",
        "3": "#",
        "4": "$",
        "5": "%",
        "6": "^",
        "7": "&",
        "8": "*",
        "9": "(",
        "0": ")",
        "-": "_",
        "=": "+",
        "[": "{",
        "]": "}",
        "\\": "|",
        ";": ":",
        "'": '"',
        ",": "<",
        ".": ">",
        "/": "?",
    }
    def __init__(self):
        super().__init__()
        self.address = ""
        self.shift_enabled = False
        self.setFocusPolicy(Qt.StrongFocus)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        self.hint = QLabel(objectName="hint")
        layout.addWidget(self.hint)
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
    def create_key(
        self,
        text,
        character=None,
        callback=None,
        width=None,
    ):
        button = QPushButton(text, objectName="characterButton")
        button.setFocusPolicy(Qt.StrongFocus)
        if width:
            button.setFixedSize(width, 48)
        else:
            button.setMinimumWidth(48)
            button.setMinimumHeight(52)
            button.setSizePolicy(
                QSizePolicy.Expanding,
                QSizePolicy.Fixed,
            )
        if character is not None:
            value = self.character_to_append(character)
            button.setToolTip(self.address + value)
            button.clicked.connect(
                partial(self.append_character, character)
            )
        elif callback:
            button.clicked.connect(callback)
        return button
    def create_keyboard(self):
        self.clear_keyboard()
        for row_number, characters in enumerate(self.KEYBOARD_ROWS):
            row = QHBoxLayout()
            row.setSpacing(7)
            left_margin = row_number * 18
            right_margin = row_number * 18
            row.setContentsMargins(
                left_margin,
                0,
                right_margin,
                0,
            )
            for character in characters:
                button = self.create_key(
                    self.display_character(character),
                    character=character,
                )
                row.addWidget(button, 1)
            self.keyboard_layout.addLayout(row)
        controls = QHBoxLayout()
        controls.setSpacing(7)
        shift = QPushButton(
            "⇧",
            objectName="characterButton",
        )
        shift.setToolTip("Shift")
        shift.setCheckable(True)
        shift.setChecked(self.shift_enabled)
        shift.setFixedSize(76, 48)
        shift.clicked.connect(self.toggle_shift)
        controls.addWidget(shift)
        controls.addWidget(
            self.create_key(
                "⌫",
                callback=self.remove_last,
                width=76,
            )
        )
        controls.addWidget(
            self.create_key(
                "space",
                callback=partial(
                    self.append_character,
                    " ",
                ),
                width=160,
            )
        )
        controls.addWidget(
            self.create_key(
                "x",
                callback=self.clear,
                width=76,
            )
        )
        controls.addWidget(
            self.create_key(
                "→",
                callback=self.navigate_requested.emit,
                width=76,
            )
        )
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
        self.hint.setText(
            f"{self.address}"
        )
class BrowserTab(QWidget):
    def __init__(self, builder, web_page):
        super().__init__()
        self.builder = builder
        self.web_page = web_page
        self.current_page = builder
        self.layout = QStackedLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(builder)
        self.layout.addWidget(web_page)
    def show_web_page(self):
        self.current_page = self.web_page
        self.layout.setCurrentWidget(self.web_page)
class BrowserPage(QWebEnginePage):
    def __init__(self, browser):
        super().__init__(browser)
        self.browser = browser
    def createWindow(self, window_type):
        return self.browser.add_web_tab().page()
class Browser(QMainWindow):
    def __init__(self, start_url):
        super().__init__()
        self.setWindowTitle("minneola")
        self.resize(1160, 780)
        self.setMinimumSize(720, 520)
        self.setStyleSheet(STYLE)
        self.toolbar = QToolBar("Navigation")
        self.toolbar.setObjectName("navigationBar")
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)
        
        self.back = self.add_toolbar_button(
            self.toolbar,
            "←",
            lambda: self.page().back(),
        )
        self.forward = self.add_toolbar_button(
            self.toolbar,
            "→",
            lambda: self.page().forward(),
        )
        self.reload = self.add_toolbar_button(
            self.toolbar,
            "↻",
            lambda: self.page().reload(),
        )
        self.add_toolbar_button(
            self.toolbar,
            "+",
            self.add_tab,
        )
        self.address = QLineEdit(
            objectName="addressBar"
        )
        self.address.returnPressed.connect(
            self.navigate
        )
        self.toolbar.addWidget(self.address)
        self.add_toolbar_button(
            self.toolbar,
            "→",
            self.navigate,
        )
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(False)
        self.tabs.setMovable(True)
        self.tabs.setTabsClosable(False)
        self.tabs.setUsesScrollButtons(True)
        self.tabs.tabBar().setExpanding(False)
        self.tabs.currentChanged.connect(
            self.update_address
        )
        self.setCentralWidget(self.tabs)
        QShortcut(
            QKeySequence("Ctrl+L"),
            self,
            activated=self.focus_address,
        )
        self.add_tab(start_url)
        self.autohide_timer = QTimer(self)
        self.autohide_timer.setInterval(150)
        self.autohide_timer.timeout.connect(self.check_autohide)
        self.autohide_timer.start()
    def check_autohide(self):
        if self.address.hasFocus():
            self.toolbar.show()
            self.tabs.tabBar().show()
            return
        pos = self.mapFromGlobal(QCursor.pos())
        if 0 <= pos.x() <= self.width() and 0 <= pos.y() <= 45:
            self.toolbar.show()
            self.tabs.tabBar().show()
        elif pos.y() > 120 or pos.x() < 0 or pos.x() > self.width() or pos.y() < 0:
            self.toolbar.hide()
            self.tabs.tabBar().hide()
    def add_toolbar_button(self, toolbar, text, action):
        button = QPushButton(
            text,
            objectName="toolbarButton",
        )
        button.clicked.connect(
            lambda checked=False: action()
        )
        toolbar.addWidget(button)
        return button
    def page(self):
        return self.tabs.currentWidget().current_page
    def current_tab(self):
        return self.tabs.currentWidget()
    def add_tab(self, url="about:blank"):
        builder = AddressBuilder()
        builder.address_changed.connect(
            self.update_builder_address
        )
        builder.navigate_requested.connect(
            self.navigate
        )
        web_page = self.create_web_page()
        tab = self.add_page_tab(builder, web_page)
        if url != "about:blank":
            tab.show_web_page()
            web_page.setUrl(
                QUrl.fromUserInput(url)
            )
        return web_page
    def add_page_tab(
        self,
        builder,
        web_page,
        title="",
    ):
        tab = BrowserTab(builder, web_page)
        index = self.tabs.addTab(tab, title)
        self.install_close_button(tab, index)
        self.tabs.setCurrentIndex(index)
        self.update_buttons(tab.current_page)
        return tab
    def create_web_page(self):
        page = QWebEngineView()
        page.setPage(BrowserPage(self))
        page.urlChanged.connect(
            self.update_address
        )
        page.titleChanged.connect(
            lambda title: self.rename_tab(page, title)
        )
        page.loadFinished.connect(
            lambda: self.update_buttons(page)
        )
        page.page().profile().downloadRequested.connect(
            self.handle_download
        )
        return page
    def handle_download(self, download):
        filename = (
            download.downloadFileName()
            or "download"
        )
        folder = QStandardPaths.writableLocation(
            QStandardPaths.DownloadLocation
        )
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save download",
            os.path.join(folder, filename),
            "All files (*)",
        )
        if not path:
            download.cancel()
            return
        download.setDownloadDirectory(
            os.path.dirname(path)
        )
        download.setDownloadFileName(
            os.path.basename(path)
        )
        download.accept()
    def add_web_tab(self, url="about:blank"):
        page = self.add_tab()
        self.tabs.currentWidget().show_web_page()
        if url != "about:blank":
            page.setUrl(
                QUrl.fromUserInput(url)
            )
        return page
    def install_close_button(self, tab, index):
        button = QToolButton()
        button.setText("×")
        button.setAutoRaise(True)
        button.setObjectName("tabCloseButton")
        button.clicked.connect(
            lambda: self.close_tab(
                self.tabs.indexOf(tab)
            )
        )
        self.tabs.tabBar().setTabButton(
            index,
            QTabBar.RightSide,
            button,
        )
    def tab_index_for_page(self, page):
        for index in range(self.tabs.count()):
            tab = self.tabs.widget(index)
            if tab.current_page is page:
                return index
        return -1
    def rename_tab(self, page, title):
        index = self.tab_index_for_page(page)
        if index >= 0:
            title = (title or "")[:24]
            self.tabs.setTabText(index, title)
            if page is self.page():
                self.setWindowTitle(
                    f"{title}"
                )
    def navigate(self):
        address = self.address.text().strip()
        if address:
            self.open_address(address)
    def open_address(self, address):
        page = self.page()
        if isinstance(page, AddressBuilder):
            tab = self.current_tab()
            tab.show_web_page()
            tab.web_page.setUrl(
                QUrl.fromUserInput(address)
            )
            self.update_buttons(tab.web_page)
        else:
            page.setUrl(
                QUrl.fromUserInput(address)
            )
    def update_builder_address(self, address):
        self.address.setText(address)
        self.address.clearFocus()
        if self.current_tab():
            self.current_tab().builder.setFocus()
    def update_address(self, *_):
        page = self.page()
        if isinstance(page, QWebEngineView):
            url = page.url().toString()
            self.address.setText(
                "" if url == "about:blank" else url
            )
            self.update_buttons(page)
        else:
            self.address.setText(page.address)
            self.update_buttons(page)
    def update_buttons(self, page):
        enabled = isinstance(page, QWebEngineView)
        self.back.setEnabled(
            enabled and page.history().canGoBack()
        )
        self.forward.setEnabled(
            enabled and page.history().canGoForward()
        )
        self.reload.setEnabled(enabled)
    def focus_address(self):
        self.toolbar.show()
        self.tabs.tabBar().show()
        self.address.setFocus()
        self.address.selectAll()
    def close_tab(self, index):
        if index < 0:
            return
        if self.tabs.count() == 1:
            self.close()
            return
        tab = self.tabs.widget(index)
        self.tabs.removeTab(index)
        tab.deleteLater()
def start_server():
    directory = os.path.dirname(
        os.path.abspath(__file__)
    )
    handler = partial(
        SimpleHTTPRequestHandler,
        directory=directory,
    )
    server = ThreadingHTTPServer(
        ("127.0.0.1", 8080),
        handler,
    )
    threading.Thread(
        target=server.serve_forever,
        daemon=True,
    ).start()
    return server
def hide_windows_console():
    if sys.platform == "win32":
        import ctypes
        window = ctypes.windll.kernel32.GetConsoleWindow()
        if window:
            ctypes.windll.user32.ShowWindow(window, 0)
if __name__ == "__main__":
    hide_windows_console()
    server = start_server()
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(get_resource_path("minneola.svg")))
    browser = Browser(
        sys.argv[1]
        if len(sys.argv) > 1
        else "about:blank"
    )
    browser.show()
    try:
        sys.exit(app.exec())
    finally:
        server.shutdown()