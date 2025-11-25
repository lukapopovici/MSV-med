from PyQt6.QtWidgets import QWidget, QApplication


class CenteredView(QWidget):
    def __init__(self):
        super().__init__()

    def _center_on_screen(self):
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()

        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2

        self.move(x, y)

    def showEvent(self, event):
        super().showEvent(event)
        self._center_on_screen()