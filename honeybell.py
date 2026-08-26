import os
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from minneola import APP_DISPLAY, VERSION
def apply_chromium_flags(settings):
    """rendering mode:

    hardware_acceleration (default on): ANGLE/Direct3D 11
    set "hardware_acceleration": false in settings.json for pure-software
    """
    if settings.get("hardware_acceleration", True):
        mode = "--use-angle=d3d11 --enable-gpu-rasterization"
        label = "gpu (angle/d3d11)"
    else:
        mode = "--disable-gpu"
        label = "software"
    os.environ.setdefault(
        "QTWEBENGINE_CHROMIUM_FLAGS",
        mode + " --disable-logging --log-level=3 "
               "--disable-features=CalculateNativeWinOcclusion")
    os.environ.setdefault("QT_LOGGING_RULES", "qt.webenginecontext.debug=false")
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
    from minneola.storage import load_settings
    settings = load_settings()
    apply_chromium_flags(settings)
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
    from minneola.webview import create_profile
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
    if "--smoke" in sys.argv:
        QTimer.singleShot(2500, app.quit)
    exit_code = app.exec()
    sys.exit(exit_code)
if __name__ == "__main__":
    server = start_server()
    try:
        main()
    finally:
        if server is not None:
            server.shutdown()