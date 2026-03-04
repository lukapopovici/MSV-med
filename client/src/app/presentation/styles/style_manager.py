from typing import Optional
from PyQt6.QtWidgets import QWidget
from app.config.settings import Settings


class StyleManager:

    def __init__(self):
        self.settings = Settings()
        self._cached_style: Optional[str] = None

    def load_style(self, widget: QWidget, style_path: Optional[str] = None) -> bool:
        try:
            path = style_path or self.settings.STYLE_PATH

            if not self._cached_style or style_path:
                with open(path, "r", encoding="utf-8") as f:
                    self._cached_style = f.read()

            widget.setStyleSheet(self._cached_style)
            return True

        except FileNotFoundError:
            print(f"Style file not found: {path}")
            return False
        except Exception as e:
            print(f"Error loading style file: {e}")
            return False

    def get_style_content(self, style_path: Optional[str] = None) -> str:
        try:
            path = style_path or self.settings.STYLE_PATH
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Error reading style file: {e}")
            return ""

    def reload_style(self):
        self._cached_style = None


# Global instance
style_manager = StyleManager()


def load_style(widget: QWidget, style_path: Optional[str] = None):
    style_manager.load_style(widget, style_path)