import json
import os
from PySide6.QtCore import QStandardPaths
APP_FOLDER = "honeybell"
DEFAULT_SETTINGS = {
    "start_fullscreen": True,
    "bookmarks_bar": True,
    "search_engine": "duckduckgo",
    "adblock": True,
    "force_https": True,
    "whitelist_only": False,
}
def data_dir():
    base = QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation)
    path = os.path.join(base, APP_FOLDER)
    os.makedirs(path, exist_ok=True)
    return path
def settings_path():
    return os.path.join(data_dir(), "settings.json")
def bookmarks_path():
    return os.path.join(data_dir(), "bookmarks.json")
def whitelist_path():
    return os.path.join(data_dir(), "whitelist.txt")
def rules_path():
    return os.path.join(data_dir(), "rules.txt")
def load_settings():
    settings = dict(DEFAULT_SETTINGS)
    try:
        with open(settings_path(), "r", encoding="utf-8") as handle:
            stored = json.load(handle)
        if isinstance(stored, dict):
            for key, value in stored.items():
                if key in settings:
                    settings[key] = value
    except (OSError, ValueError):
        pass
    return settings
def save_settings(settings):
    try:
        with open(settings_path(), "w", encoding="utf-8") as handle:
            json.dump(settings, handle, indent=2)
    except OSError:
        pass
def load_bookmarks():
    try:
        with open(bookmarks_path(), "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, list):
            return [
                {"title": str(item.get("title") or item["url"]),
                 "url": str(item["url"])}
                for item in data
                if isinstance(item, dict) and item.get("url")
            ]
    except (OSError, ValueError):
        pass
    return []
def save_bookmarks(bookmarks):
    try:
        with open(bookmarks_path(), "w", encoding="utf-8") as handle:
            json.dump(bookmarks, handle, indent=2, ensure_ascii=False)
    except OSError:
        pass
def ensure_file(path, template=""):
    if not os.path.exists(path):
        try:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(template)
        except OSError:
            return None
    return path
def load_wordlist(path):
    entries = []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line and not line.startswith("#"):
                    entries.append(line.lower())
    except OSError:
        pass
    return entries