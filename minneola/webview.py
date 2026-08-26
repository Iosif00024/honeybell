from PySide6.QtCore import QTimer, QUrl
from PySide6.QtWidgets import QStackedLayout, QWidget
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
def chromium_version():
    try:
        from PySide6.QtWebEngineCore import qWebEngineChromiumVersion
        return qWebEngineChromiumVersion()
    except Exception:
        return "120"
def create_profile():
    profile = QWebEngineProfile(None)
    version = chromium_version()
    profile.setHttpUserAgent(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        f"(KHTML, like Gecko) Chrome/{version} Safari/537.36"
    )
    settings = profile.settings()
    settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
    settings.setAttribute(QWebEngineSettings.ScrollAnimatorEnabled, True)
    settings.setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False)
    settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
    settings.setAttribute(QWebEngineSettings.ErrorPageEnabled, True)
    settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
    settings.setAttribute(QWebEngineSettings.PdfViewerEnabled, True)
    settings.setAttribute(QWebEngineSettings.DnsPrefetchEnabled, True)
    return profile
class BrowserPage(QWebEnginePage):
    def __init__(self, profile, parent=None):
        super().__init__(profile, parent)
        self.browser = None
        self._blocked_replays = set()
    def set_browser(self, browser):
        self.browser = browser
    def createWindow(self, window_type):
        if self.browser is not None:
            view = self.browser.open_popup_view()
            if view is not None:
                return view.page()
        return None
    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        pass
    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        if self.browser is not None and is_main_frame:
            key = url.toString()
            if key in self._blocked_replays:
                self._blocked_replays.discard(key)
                return True
            allowed, replacement = self.browser.check_navigation(url)
            if not allowed:
                self._blocked_replays.add(key)
                QTimer.singleShot(
                    2000, lambda: self._blocked_replays.discard(key))
                html = replacement
                QTimer.singleShot(0, lambda: self.setHtml(html, url))
                return False
        return super().acceptNavigationRequest(url, nav_type, is_main_frame)
class WebView(QWebEngineView):
    def __init__(self, profile, parent=None):
        super().__init__(parent)
        self.page_obj = BrowserPage(profile, self)
        self.setPage(self.page_obj)
        self.loading = False
class WebTab(QWidget):
    def __init__(self, builder, view):
        super().__init__()
        self.builder = builder
        self.web_view = view
        layout = QStackedLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(builder)
        layout.addWidget(view)
    @property
    def showing_web(self):
        return self.layout().currentIndex() == 1
    def show_web_page(self):
        self.layout().setCurrentWidget(self.web_view)
    def show_builder(self):
        self.layout().setCurrentWidget(self.builder)