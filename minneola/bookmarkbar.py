import json
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QApplication, QMenu, QToolBar, QToolButton
from .storage import load_bookmarks, save_bookmarks
class BookmarkButton(QToolButton):
    open_requested = Signal(str, bool)
    remove_requested = Signal(str)
    def __init__(self, title, url):
        super().__init__(objectName="bookmarkButton")
        self.url = url
        self.title = title
        self.setText(title[:24])
        self.setToolTip(url)
        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(lambda: self.open_requested.emit(self.url, False))
    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.open_requested.emit(self.url, True)
            event.accept()
            return
        super().mousePressEvent(event)
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.addAction("Open", lambda: self.open_requested.emit(self.url, False))
        menu.addAction("New tab open",
                       lambda: self.open_requested.emit(self.url, True))
        menu.addAction("Address copy",
                       lambda: QApplication.clipboard().setText(self.url))
        menu.addSeparator()
        menu.addAction("Removal",
                       lambda: self.remove_requested.emit(self.url))
        menu.exec(event.globalPos())
class BookmarkBar(QToolBar):
    open_requested = Signal(str, bool)
    changed = Signal()
    def __init__(self):
        super().__init__("Bookmarks", objectName="bookmarkBar")
        self.setMovable(False)
        self.setFloatable(False)
        self.bookmarks = load_bookmarks()
        self._buttons = []
        self.rebuild()
    def rebuild(self):
        for action in list(self.actions()):
            self.removeAction(action)
        for button in self._buttons:
            button.deleteLater()
        self._buttons = []
        if not self.bookmarks:
            hint = QToolButton(objectName="bookmarkHint")
            hint.setText("no bookmarks yet \u2014 Ctrl+D for bookmarking this page")
            hint.setEnabled(False)
            self.addWidget(hint)
            self._buttons.append(hint)
            return
        for item in self.bookmarks:
            button = BookmarkButton(item["title"], item["url"])
            button.open_requested.connect(self.open_requested.emit)
            button.remove_requested.connect(self.remove_bookmark)
            self._buttons.append(button)
            self.addWidget(button)
    def save(self):
        save_bookmarks(self.bookmarks)
        self.changed.emit()
    def add_bookmark(self, title, url):
        url = (url or "").strip()
        if not url:
            return
        for item in self.bookmarks:
            if item["url"] == url:
                item["title"] = title or url
                self.save()
                self.rebuild()
                return
        self.bookmarks.append({"title": title or url, "url": url})
        self.save()
        self.rebuild()
    def remove_bookmark(self, url):
        self.bookmarks = [b for b in self.bookmarks if b["url"] != url]
        self.save()
        self.rebuild()
    def has_bookmark(self, url):
        return any(b["url"] == url for b in self.bookmarks)
    def export_to(self, path):
        try:
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(self.bookmarks, handle, indent=2, ensure_ascii=False)
            return True
        except OSError:
            return False
    def import_from(self, path):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, ValueError):
            return 0
        if not isinstance(data, list):
            return 0
        existing = {b["url"] for b in self.bookmarks}
        added = 0
        for item in data:
            if (isinstance(item, dict) and item.get("url")
                    and item["url"] not in existing):
                self.bookmarks.append({
                    "title": str(item.get("title") or item["url"]),
                    "url": str(item["url"]),
                })
                existing.add(item["url"])
                added += 1
        if added:
            self.save()
            self.rebuild()
        return added