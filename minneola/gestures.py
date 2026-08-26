from PySide6.QtCore import QObject, QPoint, Qt
from PySide6.QtCore import QEvent
GESTURES = {
    "R": "back",
    "L": "forward",
    "U": "reload",
    "D": "new_tab",
    "DR": "close_tab",
}
GESTURE_LABELS = {
    "back": "\u2192 Back",
    "forward": "\u2190 Forward",
    "reload": "\u2191 Reload",
    "new_tab": "\u2193 New tab",
    "close_tab": "\u2193\u2192 Close tab",
}
THRESHOLD = 18
class GestureController(QObject):
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        self.active = False
        self.start_pos = QPoint()
        self.last_pos = QPoint()
        self.segments = []
    def attach(self, view):
        view.installEventFilter(self)
        focus_proxy = view.focusProxy()
        if focus_proxy is not None:
            focus_proxy.installEventFilter(self)
    def perform(self, action):
        if action == "back":
            self.browser.go_back()
        elif action == "forward":
            self.browser.go_forward()
        elif action == "reload":
            self.browser.reload_page()
        elif action == "new_tab":
            self.browser.add_tab()
        elif action == "close_tab":
            self.browser.close_tab(self.browser.tabs.currentIndex())
    def show_indicator(self, sequence):
        action = GESTURES.get(sequence)
        label = GESTURE_LABELS.get(action, "")
        arrows = "".join({"R": "\u2192", "L": "\u2190",
                          "U": "\u2191", "D": "\u2193"}.get(c, c)
                         for c in sequence)
        self.browser.show_gesture(f"{arrows}  {label}" if label else arrows)
    def eventFilter(self, obj, event):
        etype = event.type()
        if etype == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.XButton1:
                self.perform("back")
                return True
            if event.button() == Qt.MouseButton.XButton2:
                self.perform("forward")
                return True
            if event.button() == Qt.MouseButton.RightButton:
                self.active = True
                self.segments = []
                self.start_pos = event.position().toPoint()
                self.last_pos = self.start_pos
            return False
        if etype == QEvent.Type.MouseMove and self.active:
            if not (event.buttons() & Qt.MouseButton.RightButton):
                return False
            pos = event.position().toPoint()
            base = self.last_pos if self.segments else self.start_pos
            dx = pos.x() - base.x()
            dy = pos.y() - base.y()
            if abs(dx) >= THRESHOLD or abs(dy) >= THRESHOLD:
                if abs(dx) >= abs(dy):
                    direction = "R" if dx > 0 else "L"
                else:
                    direction = "D" if dy > 0 else "U"
                if not self.segments or self.segments[-1] != direction:
                    self.segments.append(direction)
                    self.show_indicator("".join(self.segments))
                self.last_pos = pos
            return False
        if etype == QEvent.Type.MouseButtonRelease:
            if event.button() == Qt.MouseButton.RightButton and self.active:
                self.active = False
                sequence = "".join(self.segments)
                self.browser.hide_gesture()
                action = GESTURES.get(sequence)
                if action:
                    self.perform(action)
                    return True
            return False
        if etype == QEvent.Type.Wheel:
            if event.modifiers() & Qt.ControlModifier:
                if event.angleDelta().y() > 0:
                    self.browser.zoom_in()
                else:
                    self.browser.zoom_out()
                return True
            return False
        return False