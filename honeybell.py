import os
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
os.environ.setdefault(
    "QTWEBENGINE_CHROMIUM_FLAGS",
    "--disable-gpu --disable-logging --log-level=3")
os.environ.setdefault("QT_LOGGING_RULES", "qt.webenginecontext.debug=false")
from minneola import APP_DISPLAY, VERSION
def get_resource_path(relative_path):
    base = getattr(sys, "_MEIPASS", os.path.abspath(os.path.dirname(__file__)))
    return os.path.join(base, relative_path)
def get_icon_path():
    for name in ("honeybell.ico", "honeybell.png"):
        path = get_resource_path(name)
        if os.path.exists(path):
            return path
    return None
class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass
def start_server():
    directory = os.path.dirname(os.path.abspath(__file__))
    handler = partial(QuietHandler, directory=directory)
    for port in (8080, 0):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), handler)
        except OSError:
            continue
        threading.Thread(target=server.serve_forever, daemon=True).start()
        print(f"[{APP_DISPLAY}] local server on port {server.server_address[1]}")
        return server
    print(f"[{APP_DISPLAY}] local server unavailable (port busy)")
    return None
def main():
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication
    if hasattr(Qt, "AA_ShareOpenGLContexts"):
        QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_DISPLAY)
    app.setOrganizationName(APP_DISPLAY)
    app.setApplicationVersion(VERSION)
    icon_path = get_icon_path()
    if icon_path:
        app.setWindowIcon(QIcon(icon_path))
    from minneola.browser import Browser
    from minneola.storage import load_settings
    from minneola.webview import create_profile
    settings = load_settings()
    profile = create_profile()
    start_url = "about:blank"
    for argument in sys.argv[1:]:
        if not argument.startswith("-"):
            start_url = argument
            break
    browser = Browser(profile, start_url, settings, app_icon=app.windowIcon())
    if settings.get("start_fullscreen"):
        browser.showFullScreen()
    else:
        browser.show()
    print(f"[{APP_DISPLAY}] {VERSION} ready")
    if "--smoke" in sys.argv:
        QTimer.singleShot(2500, app.quit)
    exit_code = app.exec()
    print(f"[{APP_DISPLAY}] exited cleanly")
    sys.exit(exit_code)
if __name__ == "__main__":
    server = start_server()
    try:
        main()
    finally:
        if server is not None:
            server.shutdown()