STYLE = """
* {
    outline: none;
}
QMainWindow,
QWidget {
    color: #5a1f12;
    background: #f28b38;
}
QToolBar {
    border: none;
    background: #d93616;
}
QToolBar#navigationBar {
    border: none;
    border-bottom: 3px solid #8f1d0e;
    padding: 6px 8px;
    spacing: 6px;
}
QPushButton#toolbarButton {
    color: #5a1f12;
    background: #f47b32;
    border: 1px solid #bc3519;
    border-radius: 9px;
    padding: 6px 12px;
    min-width: 32px;
    min-height: 28px;
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
    padding: 6px 12px;
    min-height: 28px;
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
QLabel#zoomOverlay {
    color: #ffd0a8;
    background: rgba(117, 21, 8, 235);
    border: 1px solid #751508;
    border-radius: 10px;
    padding: 6px 14px;
    font: bold 11pt "Segoe UI";
}
QProgressBar#progress {
    background: #d93616;
    border: none;
    max-height: 3px;
}
QProgressBar#progress::chunk {
    background: #ffd0a8;
    border: none;
}
QTabWidget {
    background: #ef7935;
    border: none;
}
QTabWidget::pane {
    background: #ef7935;
    border: none;
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
    padding: 7px 34px 7px 12px;
    margin: 4px 3px 4px 0;
    min-width: 110px;
    max-width: 180px;
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
QToolButton#tabCloseButton {
    color: #6f2115;
    background: transparent;
    border: none;
    border-radius: 5px;
    font: bold 12pt "Segoe UI";
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
QMenu {
    color: #5a1f12;
    background: #f58c45;
    border: 2px solid #8f1d0e;
    border-radius: 8px;
    padding: 4px;
}
QMenu::item {
    padding: 6px 24px 6px 12px;
    border-radius: 5px;
}
QMenu::item:selected {
    color: #ffd0a8;
    background: #a92512;
}
QMenu::separator {
    height: 1px;
    background: #c44720;
    margin: 4px 8px;
}
QToolBar#bookmarkBar {
    background: #ef7935;
    border: none;
    border-bottom: 2px solid #d9662c;
    padding: 3px 6px;
    spacing: 4px;
}
QToolButton#bookmarkButton {
    color: #5a1f12;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 4px 10px;
    font: 10pt "Segoe UI";
}
QToolButton#bookmarkButton:hover {
    color: #ffd0a8;
    background: #c83a20;
}
QToolButton#bookmarkHint {
    color: #7a3a20;
    background: transparent;
    border: none;
    font: italic 10pt "Segoe UI";
}
QWidget#findBar {
    background: #f9a15d;
    border: 2px solid #bd3518;
    border-radius: 8px;
}
QLineEdit#findInput {
    color: #5a1f12;
    background: #f58c45;
    border: 1px solid #bd3518;
    border-radius: 6px;
    padding: 3px 8px;
    min-width: 170px;
    font: 10pt "Segoe UI";
    selection-background-color: #a92512;
    selection-color: #ffd0a8;
}
QLabel#findCount {
    color: #5a1f12;
    font: 10pt "Segoe UI";
}
QPushButton#findButton {
    color: #5a1f12;
    background: #f47b32;
    border: 1px solid #bc3519;
    border-radius: 6px;
    font: bold 10pt "Segoe UI";
}
QPushButton#findButton:hover {
    color: #ffd0a8;
    background: #a92512;
}
QLabel#gestureIndicator {
    color: #ffd0a8;
    background: rgba(117, 21, 8, 235);
    border: 1px solid #751508;
    border-radius: 10px;
    padding: 8px 18px;
    font: bold 12pt "Segoe UI";
}
QLabel#statusLink {
    color: #5a1f12;
    background: rgba(249, 161, 93, 240);
    border: 1px solid #bd3518;
    border-radius: 6px;
    padding: 2px 10px;
    font: 9pt "Segoe UI";
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