import os
from urllib.parse import quote_plus
from PySide6.QtCore import (
    QEvent,
    QEasingCurve,
    QPropertyAnimation,
    QStandardPaths,
    QTimer,
    QUrl,
    Qt,
)
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtGui import QCursor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSystemTrayIcon,
    QTabBar,
    QTabWidget,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from . import APP_DISPLAY
from .adblock import (
    BLOCKED_PAGE,
    AdBlockInterceptor,
    RuleEngine,
    install_cosmetic_filter,
)
from .address_builder import AddressBuilder
from .bookmarkbar import BookmarkBar
from .findbar import FindBar
from .gestures import GestureController
from .reader import extract_readable, render_reader_html
from .storage import ensure_file, rules_path, save_settings
from .styles import STYLE
from .webview import WebTab, WebView
ZOOM_STEPS = (0.25, 0.33, 0.5, 0.67, 0.75, 0.8, 0.9, 1.0,
              1.1, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0)
SEARCH_ENGINES = {
    "duckduckgo": ("DuckDuckGo", "https://duckduckgo.com/?q={}", "D"),
    "brave": ("Brave", "https://search.brave.com/search?q={}", "Br"),
    "google": ("Google", "https://www.google.com/search?q={}", "G"),
    "bing": ("Bing", "https://www.bing.com/search?q={}", "Bi"),
}
class Browser(QMainWindow):
    def __init__(self, profile, start_url, settings, app_icon=None):
        super().__init__()
        self.profile = profile
        self.settings = settings
        self.app_icon = app_icon
        self.closed_tabs = []
        self.handled_downloads = set()
        self.web_fullscreen = False
        self.state_before_video = None
        self.setWindowTitle(APP_DISPLAY)
        self.setStyleSheet(STYLE)
        self.setAcceptDrops(True)
        if app_icon is not None:
            self.setWindowIcon(app_icon)
        self.resize(1160, 780)
        self.setMinimumSize(640, 420)
        profile.downloadRequested.connect(self.handle_download)
        self.engine = RuleEngine(settings)
        self.interceptor = AdBlockInterceptor(self.engine)
        profile.setUrlRequestInterceptor(self.interceptor)
        install_cosmetic_filter(profile)
        self.build_toolbar()
        self.build_central()
        self._chrome_hidden = False
        self._bar_anims = []
        self._setup_bar_fades()
        self.build_tray()
        self.build_shortcuts()
        self.gestures = GestureController(self)
        self.add_tab(start_url)
        self.autohide_timer = QTimer(self)
        self.autohide_timer.setInterval(150)
        self.autohide_timer.timeout.connect(self.check_autohide)
        self.autohide_timer.start()
    def build_toolbar(self):
        self.toolbar = QToolBar("Navigation", objectName="navigationBar")
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.addToolBar(self.toolbar)
        self.back_button = self.add_toolbar_button("\u2190", self.go_back,
                                                   "back (Alt+Left)")
        self.forward_button = self.add_toolbar_button("\u2192", self.go_forward,
                                                      "forward (Alt+Right)")
        self.reload_button = self.add_toolbar_button("\u21bb", self.toggle_reload,
                                                     "reload (F5)")
        self.add_toolbar_button("+", self.add_tab, "new tab (Ctrl+T)")
        self.engine_button = QPushButton("D", objectName="toolbarButton")
        self.engine_button.setFixedWidth(44)
        self.engine_button.setToolTip("search engine")
        self.engine_button.clicked.connect(self.show_engine_menu)
        self.toolbar.addWidget(self.engine_button)
        self.update_engine_button()
        self.address = QLineEdit(objectName="addressBar")
        self.address.setPlaceholderText("")
        self.address.setClearButtonEnabled(True)
        self.address.returnPressed.connect(self.navigate)
        self.address.setContextMenuPolicy(Qt.CustomContextMenu)
        self.address.customContextMenuRequested.connect(self.address_menu)
        self.toolbar.addWidget(self.address)
        self.shield_button = QPushButton("\U0001F6E1", objectName="toolbarButton")
        self.shield_button.setFixedWidth(44)
        self.shield_button.setToolTip("protection")
        self.shield_button.clicked.connect(self.show_shield_menu)
        self.toolbar.addWidget(self.shield_button)
        self.star_button = self.add_toolbar_button(
            "\u2606", self.toggle_bookmark, "(Ctrl+D) for bookmarking this page")
        self.reader_button = QPushButton("Aa", objectName="toolbarButton")
        self.reader_button.setCheckable(True)
        self.reader_button.setToolTip("reader view (F9)")
        self.reader_button.clicked.connect(self.toggle_reader)
        self.toolbar.addWidget(self.reader_button)
        self.menu_button = self.add_toolbar_button("\u22ee", self.show_menu,
                                                   "Menu")
        self.addToolBarBreak(Qt.TopToolBarArea)
        self.bookmark_bar = BookmarkBar()
        self.bookmark_bar.open_requested.connect(self.open_bookmark)
        self.bookmark_bar.changed.connect(self.update_star)
        self.addToolBar(self.bookmark_bar)
        self.bookmark_bar.setVisible(
            bool(self.settings.get("bookmarks_bar", True)))
    def build_central(self):
        central = QWidget()
        vbox = QVBoxLayout(central)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        self.progress = QProgressBar(objectName="progress")
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(3)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.hide()
        vbox.addWidget(self.progress)
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setMovable(True)
        self.tabs.setTabsClosable(False)
        self.tabs.setUsesScrollButtons(True)
        self.tabs.tabBar().setExpanding(False)
        self.tabs.tabBar().setDrawBase(False)
        self.tabs.currentChanged.connect(self.on_current_changed)
        self.tabs.tabBar().installEventFilter(self)
        vbox.addWidget(self.tabs, 1)
        self.setCentralWidget(central)
        self.zoom_overlay = QLabel(central, objectName="zoomOverlay")
        self.zoom_overlay.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.zoom_overlay.hide()
        self.zoom_timer = QTimer(self)
        self.zoom_timer.setSingleShot(True)
        self.zoom_timer.timeout.connect(self.zoom_overlay.hide)
        self.status_link = QLabel(central, objectName="statusLink")
        self.status_link.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.status_link.hide()
        self.gesture_label = QLabel(central, objectName="gestureIndicator")
        self.gesture_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.gesture_label.hide()
        self.find_bar = FindBar(central)
        self.find_bar.find_requested.connect(self.find_in_page)
        self.find_bar.closed.connect(self.clear_find)
    def build_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = None
            return
        self.tray = QSystemTrayIcon(self.app_icon, self)
        self.tray.setToolTip(APP_DISPLAY)
        menu = QMenu()
        menu.addAction("show / hidden window", self.toggle_window_visible)
        menu.addAction("new tab", self.add_tab)
        menu.addSeparator()
        menu.addAction("quit", self.close)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()
    def build_shortcuts(self):
        def bind(sequence, callback):
            QShortcut(QKeySequence(sequence), self, activated=callback)
        bind("Ctrl+T", self.add_tab)
        bind("Ctrl+W", lambda: self.close_tab(self.tabs.currentIndex()))
        bind("Ctrl+Shift+T", self.reopen_closed_tab)
        bind("Ctrl+Tab", lambda: self.cycle_tab(1))
        bind("Ctrl+Shift+Tab", lambda: self.cycle_tab(-1))
        for number in range(1, 9):
            bind(f"Ctrl+{number}",
                 lambda checked=False, n=number - 1: self.select_tab(n))
        bind("Ctrl+9", lambda: self.select_tab(self.tabs.count() - 1))
        bind("F5", self.reload_page)
        bind("Ctrl+R", self.reload_page)
        bind("Escape", self.escape_pressed)
        bind("Alt+Left", self.go_back)
        bind("Alt+Right", self.go_forward)
        bind("Ctrl+L", self.focus_address)
        bind("Alt+D", self.focus_address)
        bind("F6", self.focus_address)
        bind("Ctrl++", self.zoom_in)
        bind("Ctrl+=", self.zoom_in)
        bind("Ctrl+-", self.zoom_out)
        bind("Ctrl+0", self.zoom_reset)
        bind("Ctrl+Shift+B", self.toggle_bookmark_bar)
        bind("Ctrl+D", self.toggle_bookmark)
        bind("F9", self.toggle_reader)
        bind("Ctrl+F", self.open_find)
        bind("F3", lambda: self.find_in_page(self.find_bar.text(), False))
        bind("Shift+F3", lambda: self.find_in_page(self.find_bar.text(), True))
        bind("Ctrl+Shift+S", self.save_as_pdf)
        bind("Ctrl+P", self.print_page)
        bind("F11", self.toggle_window_fullscreen)
    def add_toolbar_button(self, text, action, tooltip=""):
        button = QPushButton(text, objectName="toolbarButton")
        if tooltip:
            button.setToolTip(tooltip)
        button.clicked.connect(lambda checked=False: action())
        self.toolbar.addWidget(button)
        return button
    def add_tab(self, url="about:blank"):
        builder = AddressBuilder(self.bookmark_bar.bookmarks)
        view = self.create_view()
        tab = WebTab(builder, view)
        builder.address_changed.connect(self.update_builder_address)
        builder.navigate_requested.connect(self.navigate)
        builder.open_url.connect(self.open_address)
        index = self.tabs.addTab(tab, "New Tab")
        self.install_close_button(tab, index)
        self.tabs.setCurrentIndex(index)
        if url != "about:blank":
            tab.show_web_page()
            view.setUrl(QUrl.fromUserInput(url))
        self.update_buttons()
        return view
    def open_popup_view(self):
        view = self.add_tab()
        self.current_tab().show_web_page()
        return view
    def create_view(self):
        view = WebView(self.profile)
        view.page_obj.set_browser(self)
        view.urlChanged.connect(self.on_url_changed)
        view.titleChanged.connect(lambda title, v=view: self.rename_tab(v, title))
        view.iconChanged.connect(lambda icon, v=view: self.set_tab_icon(v, icon))
        view.loadStarted.connect(lambda v=view: self.on_load_started(v))
        view.loadProgress.connect(lambda value, v=view: self.on_load_progress(v, value))
        view.loadFinished.connect(lambda ok, v=view: self.on_load_finished(v, ok))
        view.page().linkHovered.connect(self.show_link_preview)
        view.page().findTextFinished.connect(self.on_find_result)
        view.page_obj.fullScreenRequested.connect(self.handle_fullscreen_request)
        view.reader_active = False
        view.reader_original_url = ""
        self.gestures.attach(view)
        return view
    def install_close_button(self, tab, index):
        button = QToolButton()
        button.setText("\u00d7")
        button.setAutoRaise(True)
        button.setObjectName("tabCloseButton")
        button.clicked.connect(
            lambda: self.close_tab(self.tabs.indexOf(tab)))
        self.tabs.tabBar().setTabButton(index, QTabBar.RightSide, button)
    def tab_index_for_view(self, view):
        for index in range(self.tabs.count()):
            tab = self.tabs.widget(index)
            if isinstance(tab, WebTab) and tab.web_view is view:
                return index
        return -1
    def current_tab(self):
        return self.tabs.currentWidget()
    def current_view(self):
        tab = self.current_tab()
        if isinstance(tab, WebTab) and tab.showing_web:
            return tab.web_view
        return None
    def close_tab(self, index):
        if index < 0:
            return
        if self.tabs.count() == 1:
            self.close()
            return
        tab = self.tabs.widget(index)
        if isinstance(tab, WebTab):
            url = tab.web_view.url().toString()
            if url and url != "about:blank":
                self.closed_tabs.append(url)
                del self.closed_tabs[:-20]
        self.tabs.removeTab(index)
        tab.deleteLater()
    def reopen_closed_tab(self):
        if self.closed_tabs:
            self.add_tab(self.closed_tabs.pop())
    def cycle_tab(self, direction):
        count = self.tabs.count()
        if count:
            index = (self.tabs.currentIndex() + direction) % count
            self.tabs.setCurrentIndex(index)
    def select_tab(self, index):
        if 0 <= index < self.tabs.count():
            self.tabs.setCurrentIndex(index)
    def rename_tab(self, view, title):
        index = self.tab_index_for_view(view)
        if index < 0:
            return
        title = (title or "").strip()[:24]
        self.tabs.setTabText(index, title or "new tab")
        if index == self.tabs.currentIndex():
            self.setWindowTitle(f"{title} \u2014 {APP_DISPLAY}" if title else APP_DISPLAY)
    def set_tab_icon(self, view, icon):
        index = self.tab_index_for_view(view)
        if index >= 0:
            self.tabs.setTabIcon(index, icon)
    def eventFilter(self, obj, event):
        if obj is self.tabs.tabBar():
            if event.type() == QEvent.Type.MouseButtonPress:
                if event.button() == Qt.MiddleButton:
                    index = self.tabs.tabBar().tabAt(event.pos())
                    if index >= 0:
                        self.close_tab(index)
                        return True
            elif event.type() == QEvent.Type.MouseButtonDblClick:
                if event.button() == Qt.LeftButton:
                    if self.tabs.tabBar().tabAt(event.pos()) == -1:
                        self.add_tab()
                        return True
        return super().eventFilter(obj, event)
    def navigate(self):
        text = self.address.text().strip()
        if text:
            self.open_address(text)
    def resolve_input(self, text):
        lowered = text.lower()
        if lowered.startswith(("http://", "https://", "about:", "file:",
                               "data:", "localhost")):
            return QUrl.fromUserInput(text)
        head = text.split("/")[0]
        if " " not in text and "." in head and head and head[0].isalnum():
            candidate = QUrl.fromUserInput(text)
            if candidate.isValid() and candidate.host():
                return candidate
        key = self.settings.get("search_engine", "duckduckgo")
        _, template, _ = SEARCH_ENGINES.get(key, SEARCH_ENGINES["duckduckgo"])
        return QUrl.fromUserInput(template.format(quote_plus(text)))
    def open_address(self, text):
        url = self.resolve_input(text)
        if not url.isValid():
            return
        if (self.settings.get("force_https", True)
                and url.scheme() == "http"
                and url.host() not in ("localhost", "127.0.0.1", "::1")):
            url.setScheme("https")
        tab = self.current_tab()
        if tab is None:
            self.add_tab(url.toString())
            return
        if not tab.showing_web:
            tab.show_web_page()
        tab.web_view.setUrl(url)
    def go_back(self):
        view = self.current_view()
        if view is not None and view.history().canGoBack():
            view.back()
    def go_forward(self):
        view = self.current_view()
        if view is not None and view.history().canGoForward():
            view.forward()
    def reload_page(self):
        view = self.current_view()
        if view is not None:
            view.reload()
    def stop_page(self):
        view = self.current_view()
        if view is not None:
            view.stop()
    def toggle_reload(self):
        view = self.current_view()
        if view is None:
            return
        if view.loading:
            view.stop()
        else:
            view.reload()
    def focus_address(self):
        self.show_bars()
        self.address.setFocus()
        self.address.selectAll()
    def escape_pressed(self):
        if self.find_bar.isVisible():
            self.find_bar.close_bar()
            return
        if self.address.hasFocus():
            self.address.clearFocus()
            return
        view = self.current_view()
        if view is not None:
            view.stop()
    def on_url_changed(self, url):
        view = self.sender()
        if view is None:
            return
        text = url.toString()
        if getattr(view, "reader_active", False) and text != view.reader_original_url:
            view.reader_active = False
            if view is self.current_view():
                self.reader_button.setChecked(False)
        if view is not self.current_view():
            return
        self.address.setText("" if text == "about:blank" else text)
        self.update_buttons()
        self.update_shield()
        self.update_star()
    def on_load_started(self, view):
        view.loading = True
        if view is self.current_view():
            self.progress.setValue(0)
            self.progress.show()
            self.reload_button.setText("\u2715")
    def on_load_progress(self, view, value):
        if view is self.current_view():
            self.progress.setValue(value)
    def on_load_finished(self, view, ok):
        view.loading = False
        if view is self.current_view():
            self.progress.hide()
            self.reload_button.setText("\u21bb")
            self.update_buttons()
            self.update_shield()
            self.update_star()
    def on_current_changed(self, index):
        tab = self.tabs.widget(index)
        self.progress.hide()
        if isinstance(tab, WebTab) and tab.showing_web:
            url = tab.web_view.url().toString()
            self.address.setText("" if url == "about:blank" else url)
            title = tab.web_view.title().strip()[:24]
            self.setWindowTitle(f"{title} \u2014 {APP_DISPLAY}" if title else APP_DISPLAY)
        else:
            self.address.setText(tab.builder.address if isinstance(tab, WebTab) else "")
            self.setWindowTitle(APP_DISPLAY)
        view = self.current_view()
        self.reader_button.setChecked(
            bool(view and getattr(view, "reader_active", False)))
        self.update_buttons()
        self.update_star()
        if self.find_bar.isVisible():
            self.find_in_page(self.find_bar.text(), False)
    def update_buttons(self):
        view = self.current_view()
        has_view = view is not None
        self.back_button.setEnabled(has_view and view.history().canGoBack())
        self.forward_button.setEnabled(has_view and view.history().canGoForward())
        self.reload_button.setEnabled(has_view)
        self.reload_button.setText("\u2715" if has_view and view.loading else "\u21bb")
    def update_builder_address(self, text):
        self.address.setText(text)
        self.address.clearFocus()
        tab = self.current_tab()
        if isinstance(tab, WebTab):
            tab.builder.setFocus()
    def show_link_preview(self, url):
        if url:
            text = url if len(url) <= 110 else url[:107] + "\u2026"
            self.status_link.setText(text)
            self.status_link.adjustSize()
            self.position_overlays()
            self.status_link.show()
        else:
            self.status_link.hide()
    def update_engine_button(self):
        key = self.settings.get("search_engine", "duckduckgo")
        _, _, badge = SEARCH_ENGINES.get(key, SEARCH_ENGINES["duckduckgo"])
        self.engine_button.setText(badge)
    def show_engine_menu(self):
        menu = QMenu(self)
        current = self.settings.get("search_engine", "duckduckgo")
        for key, (name, _, _) in SEARCH_ENGINES.items():
            action = menu.addAction(name)
            action.setCheckable(True)
            action.setChecked(key == current)
            action.triggered.connect(
                lambda checked=False, k=key: self.select_engine(k))
        menu.exec(self.engine_button.mapToGlobal(
            self.engine_button.rect().bottomLeft()))
    def select_engine(self, key):
        self.settings["search_engine"] = key
        save_settings(self.settings)
        self.update_engine_button()
    def address_menu(self, pos):
        line = self.address
        clipboard = QApplication.clipboard().text()
        menu = QMenu(self)
        menu.addAction("Cut", line.cut).setEnabled(line.hasSelectedText())
        menu.addAction("Copy", line.copy).setEnabled(line.hasSelectedText())
        menu.addAction("Paste", line.paste).setEnabled(bool(clipboard))
        paste_go = menu.addAction("Paste & go", self.paste_and_go)
        paste_go.setEnabled(bool(clipboard))
        menu.addSeparator()
        menu.addAction("Selection of all", line.selectAll)
        menu.exec(line.mapToGlobal(pos))
    def paste_and_go(self):
        text = QApplication.clipboard().text().strip()
        if text:
            self.address.setText(text)
            self.navigate()
    def update_shield(self):
        view = self.current_view()
        host = view.url().host().lower() if view is not None else ""
        count = self.engine.blocked_on(host) if host else 0
        state = "on" if self.engine.enabled else "off"
        self.shield_button.setToolTip(
            f"")
    def show_shield_menu(self):
        menu = QMenu(self)
        adblock_action = menu.addAction("ad blocker")
        adblock_action.setCheckable(True)
        adblock_action.setChecked(self.engine.enabled)
        adblock_action.triggered.connect(self.toggle_adblock)
        https_action = menu.addAction("https-first")
        https_action.setCheckable(True)
        https_action.setChecked(bool(self.settings.get("force_https", True)))
        https_action.triggered.connect(self.toggle_https_first)
        hw_action = menu.addAction("hardware acceleration")
        hw_action.setCheckable(True)
        hw_action.setChecked(bool(self.settings.get("hardware_acceleration", True)))
        hw_action.triggered.connect(self.toggle_hardware_acceleration)
        menu.addSeparator()
        view = self.current_view()
        host = view.url().host().lower() if view is not None else ""
        if host:
            allowed = self.engine.host_in_set(host, self.engine.site_allow)
            label = ("blockage of ads on this site again" if allowed
                     else "permission for ads on this site")
            menu.addAction(label,
                           lambda checked=False, h=host: self.toggle_site_allow(h))
        count_action = menu.addAction(
            f"{self.engine.blocked_on(host)}\u2014 "
            f"{self.engine.total_blocked} total")
        count_action.setEnabled(False)
        menu.addSeparator()
        menu.addAction("rules file\u2026", self.open_rules_file)
        menu.exec(self.shield_button.mapToGlobal(
            self.shield_button.rect().bottomLeft()))
    def toggle_adblock(self):
        self.engine.enabled = not self.engine.enabled
        self.settings["adblock"] = self.engine.enabled
        save_settings(self.settings)
        self.update_shield()
    def toggle_https_first(self):
        self.settings["force_https"] = not self.settings.get("force_https", True)
        save_settings(self.settings)
    def toggle_hardware_acceleration(self):
        self.settings["hardware_acceleration"] = not self.settings.get(
            "hardware_acceleration", True)
        save_settings(self.settings)
        QMessageBox.information(
            self, APP_DISPLAY,
            "hardware acceleration mode changed.\n"
            "restart honeybell if you want to apply the new rendering mode.")
    def toggle_site_allow(self, host):
        if host in self.engine.site_allow:
            self.engine.site_allow.discard(host)
        else:
            self.engine.site_allow.add(host)
        self.update_shield()
    def open_rules_file(self):
        path = ensure_file(
            rules_path(),
            "# honeybell extra ad-block rules (adblock-style)\n"
            "# ||example.com^        blockage of a domain\n"
            "# *banner-ads*          wildcard rule\n")
        if path:
            os.startfile(path)
    def toggle_reader(self):
        view = self.current_view()
        if view is None:
            return
        if getattr(view, "reader_active", False):
            view.reader_active = False
            self.reader_button.setChecked(False)
            view.setUrl(QUrl(view.reader_original_url))
            return
        url = view.url().toString()
        if not url.startswith(("http://", "https://")):
            return
        view.reader_original_url = url
        view.reader_active = True
        self.reader_button.setChecked(True)
        def render(html_text):
            data = extract_readable(html_text)
            view.setHtml(render_reader_html(data, url), QUrl(url))
        view.page().toHtml(render)
    def open_find(self):
        if self.current_view() is None:
            return
        self.find_bar.open()
        self.position_overlays()
    def find_in_page(self, text, backward):
        view = self.current_view()
        if view is None:
            return
        if not text:
            view.findText("")
            self.find_bar.set_count(0, 0)
            return
        flags = QWebEnginePage.FindFlag(0)
        if backward:
            flags = QWebEnginePage.FindFlag.FindBackward
        view.findText(text, flags)
    def on_find_result(self, result):
        if not self.find_bar.isVisible():
            return
        self.find_bar.set_count(result.numberOfMatches(), result.activeMatch())
        self.position_overlays()
    def clear_find(self):
        view = self.current_view()
        if view is not None:
            view.findText("")
    def save_as_pdf(self):
        view = self.current_view()
        if view is None:
            return
        name = (view.title().strip() or "page")[:40] + ".pdf"
        path, _ = QFileDialog.getSaveFileName(
            self, "save as pdf", name, "pdf (*.pdf)")
        if not path:
            return
        view.page().printToPdf(path)
        print(f"[honeybell] pdf saved: {path}")
    def print_page(self):
        view = self.current_view()
        if view is None:
            return
        try:
            from PySide6.QtPrintSupport import QPrintDialog, QPrinter
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            dialog = QPrintDialog(printer, self)
            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                view.print(printer, lambda ok: None)
        except Exception as error:
            print(f"[honeybell] print unavailable: {error}")
    def show_gesture(self, text):
        self.gesture_label.setText(text)
        self.gesture_label.adjustSize()
        central = self.centralWidget()
        if central is not None:
            self.gesture_label.move(
                (central.width() - self.gesture_label.width()) // 2,
                central.height() - self.gesture_label.height() - 48)
        self.gesture_label.show()
        self.gesture_label.raise_()
    def hide_gesture(self):
        self.gesture_label.hide()
    def open_bookmark(self, url, new_tab):
        if new_tab:
            self.add_tab(url)
        else:
            self.open_address(url)
    def toggle_bookmark(self):
        view = self.current_view()
        if view is None:
            return
        url = view.url().toString()
        if not url or url == "about:blank":
            return
        if self.bookmark_bar.has_bookmark(url):
            self.bookmark_bar.remove_bookmark(url)
        else:
            self.bookmark_bar.add_bookmark(view.title().strip() or url, url)
        self.update_star()
    def update_star(self):
        view = self.current_view()
        url = view.url().toString() if view is not None else ""
        marked = bool(url) and self.bookmark_bar.has_bookmark(url)
        self.star_button.setText("\u2605" if marked else "\u2606")
    def toggle_bookmark_bar(self):
        visible = not self.settings.get("bookmarks_bar", True)
        self.settings["bookmarks_bar"] = visible
        save_settings(self.settings)
        self.bookmark_bar.setVisible(visible)
    def export_bookmarks(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export bookmarks", "honeybell-bookmarks.json",
            "JSON (*.json)")
        if path:
            self.bookmark_bar.export_to(path)
    def import_bookmarks(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Bookmarks import", "", "JSON (*.json)")
        if path:
            added = self.bookmark_bar.import_from(path)
    def zoom_in(self):
        self.zoom_step(1)
    def zoom_out(self):
        self.zoom_step(-1)
    def zoom_step(self, direction):
        view = self.current_view()
        if view is None:
            return
        factor = view.zoomFactor()
        if direction > 0:
            target = next((s for s in ZOOM_STEPS if s > factor + 0.001), ZOOM_STEPS[-1])
        else:
            target = next((s for s in reversed(ZOOM_STEPS) if s < factor - 0.001), ZOOM_STEPS[0])
        view.setZoomFactor(target)
        self.show_zoom_overlay(target)
    def zoom_reset(self):
        view = self.current_view()
        if view is None:
            return
        view.setZoomFactor(1.0)
        self.show_zoom_overlay(1.0)
    def show_zoom_overlay(self, factor):
        percentage = int(round(factor * 100))
        self.zoom_overlay.setText(f"{percentage}%")
        self.zoom_overlay.adjustSize()
        self.position_overlays()
        self.zoom_overlay.show()
        self.zoom_overlay.raise_()
        if percentage == 100:
            self.zoom_timer.start(1200)
        else:
            self.zoom_timer.stop()
    def position_overlays(self):
        central = self.centralWidget()
        if central is None:
            return
        overlay = self.zoom_overlay
        overlay.move(max(8, central.width() - overlay.width() - 16), 12)
        status = self.status_link
        status.move(8, max(8, central.height() - status.height() - 8))
        if self.find_bar.isVisible():
            self.find_bar.adjustSize()
            self.find_bar.move(
                max(8, central.width() - self.find_bar.width() - 16), 12)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.position_overlays()
    def handle_fullscreen_request(self, request):
        request.accept()
        self.set_web_fullscreen(request.toggleOn())
    def set_web_fullscreen(self, on):
        if on:
            self.state_before_video = self.windowState()
            self.hide_bars()
            self.showFullScreen()
            self.web_fullscreen = True
        else:
            self.web_fullscreen = False
            if self.state_before_video is not None:
                self.setWindowState(self.state_before_video)
            else:
                self.showNormal()
            self.show_bars()
    def toggle_window_fullscreen(self):
        if self.isFullScreen():
            self.setWindowState(Qt.WindowMaximized)
            self.settings["start_fullscreen"] = False
        else:
            self.showFullScreen()
            self.settings["start_fullscreen"] = True
        save_settings(self.settings)
    def _bar_widgets(self):
        return (self.toolbar, self.bookmark_bar, self.tabs.tabBar())
    def _setup_bar_fades(self):
        for widget in self._bar_widgets():
            effect = QGraphicsOpacityEffect(widget)
            effect.setOpacity(1.0)
            widget.setGraphicsEffect(effect)
            animation = QPropertyAnimation(effect, b"opacity", self)
            animation.setDuration(170)
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._bar_anims.append(animation)
    def _bar_opacity(self, index):
        effect = self._bar_widgets()[index].graphicsEffect()
        return effect.opacity() if effect is not None else 1.0
    def show_bars(self):
        if not self._chrome_hidden and self.toolbar.isVisible():
            return
        self._chrome_hidden = False
        for animation in self._bar_anims:
            animation.stop()
        self.toolbar.show()
        if self.settings.get("bookmarks_bar", True):
            self.bookmark_bar.show()
        self.tabs.tabBar().show()
        for index, animation in enumerate(self._bar_anims):
            animation.setStartValue(self._bar_opacity(index))
            animation.setEndValue(1.0)
            animation.start()
    def hide_bars(self):
        if self._chrome_hidden:
            return
        self._chrome_hidden = True
        for index, animation in enumerate(self._bar_anims):
            animation.stop()
            animation.setStartValue(self._bar_opacity(index))
            animation.setEndValue(0.0)
            animation.start()
        QTimer.singleShot(200, self._finalize_hide)
    def _finalize_hide(self):
        if not self._chrome_hidden:
            return
        for widget in self._bar_widgets():
            widget.hide()
            effect = widget.graphicsEffect()
            if effect is not None:
                effect.setOpacity(0.0)
    def check_autohide(self):
        if self.web_fullscreen:
            self.hide_bars()
            return
        if self.address.hasFocus() or QApplication.activePopupWidget() is not None:
            self.show_bars()
            return
        pos = self.mapFromGlobal(QCursor.pos())
        inside_x = 0 <= pos.x() <= self.width()
        if self._chrome_hidden:
            if inside_x and 0 <= pos.y() <= 4:
                self.show_bars()
            return
        limit = self.toolbar.height() + self.tabs.tabBar().height()
        if self.bookmark_bar.isVisible():
            limit += self.bookmark_bar.height()
        if not inside_x or pos.y() < 0 or pos.y() > limit:
            self.hide_bars()
    def handle_download(self, download):
        if id(download) in self.handled_downloads:
            download.cancel()
            return
        self.handled_downloads.add(id(download))
        filename = download.downloadFileName() or "download"
        folder = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
        path, _ = QFileDialog.getSaveFileName(
            self, "Save file", os.path.join(folder, filename), "All files (*)")
        if not path:
            download.cancel()
            print("[honeybell] download cancelled")
            return
        download.setDownloadDirectory(os.path.dirname(path))
        download.setDownloadFileName(os.path.basename(path))
        download.accept()
        print(f"[honeybell] download started: {os.path.basename(path)}")
        def report():
            total = download.totalBytes() or 0
            done = download.receivedBytes()
            if total:
                print(f"[honeybell] download {done * 100 // total}%")
        if hasattr(download, "receivedBytesChanged"):
            download.receivedBytesChanged.connect(report)
        def finished():
            state = "completed" if download.state() == download.DownloadState.Completed else "stopped"
            print(f"[honeybell] download {state}: {download.downloadFileName()}")
            self.handled_downloads.discard(id(download))
        download.finished.connect(finished)
    def check_navigation(self, url):
        if url.scheme() not in ("http", "https"):
            return True, ""
        if self.engine.whitelist_only and not self.engine.host_allowed(
                url.host().lower()):
            return False, BLOCKED_PAGE.format(code="ERR_BLOCKED_BY_CLIENT")
        return True, ""
    def show_menu(self):
        menu = QMenu(self)
        menu.addAction("new tab\tctrl+t", self.add_tab)
        menu.addAction("tab closed\tctrl+w",
                       lambda: self.close_tab(self.tabs.currentIndex()))
        menu.addSeparator()
        menu.addAction("zoomed in\tctrl++", self.zoom_in)
        menu.addAction("zoomed out\tctrl+-", self.zoom_out)
        menu.addAction("zoom reset\tctrl+0", self.zoom_reset)
        menu.addSeparator()
        bar_action = menu.addAction("bookmarks bar\tctrl+shift+b",
                                    self.toggle_bookmark_bar)
        bar_action.setCheckable(True)
        bar_action.setChecked(bool(self.settings.get("bookmarks_bar", True)))
        menu.addAction("bookmarks export\u2026", self.export_bookmarks)
        menu.addAction("bookmarks import\u2026", self.import_bookmarks)
        menu.addSeparator()
        menu.addAction("page searching\tctrl+f", self.open_find)
        menu.addAction("reader view\tf9", self.toggle_reader)
        menu.addAction("save as PDF\tctrl+shift+s", self.save_as_pdf)
        menu.addAction("print\tctrl+p", self.print_page)
        menu.addSeparator()
        menu.addAction("fullscreen toggle\tf11", self.toggle_window_fullscreen)
        menu.addSeparator()
        menu.addAction(f"about {APP_DISPLAY}", lambda: QMessageBox.about(
            self, APP_DISPLAY,
            f"<b>{APP_DISPLAY}</b> {'' }<br>a private browser.<br>"
            ""))
        menu.exec(self.menu_button.mapToGlobal(self.menu_button.rect().bottomLeft()))
    def on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.toggle_window_visible()
    def toggle_window_visible(self):
        if self.isVisible() and not self.isMinimized():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                self.add_tab(url.toString())
            event.acceptProposedAction()
        elif event.mimeData().hasText():
            text = event.mimeData().text().strip()
            if text:
                self.add_tab(text)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)
    def closeEvent(self, event):
        save_settings(self.settings)
        for index in range(self.tabs.count()):
            tab = self.tabs.widget(index)
            if isinstance(tab, WebTab):
                try:
                    old_page = tab.web_view.page()
                    tab.web_view.setPage(None)
                    if old_page is not None:
                        old_page.deleteLater()
                except Exception:
                    pass
        if getattr(self, "tray", None) is not None:
            self.tray.hide()
        super().closeEvent(event)