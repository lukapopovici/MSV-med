from typing import Optional
from PyQt6.QtWidgets import QMessageBox, QWidget


class NotificationService:
    @staticmethod
    def show_info(parent: Optional[QWidget], title: str, message: str):
        QMessageBox.information(parent, title, message)

    @staticmethod
    def show_warning(parent: Optional[QWidget], title: str, message: str):
        QMessageBox.warning(parent, title, message)

    @staticmethod
    def show_error(parent: Optional[QWidget], title: str, message: str):
        QMessageBox.critical(parent, title, message)

    @staticmethod
    def ask_confirmation(parent: Optional[QWidget], title: str, message: str) -> bool:
        reply = QMessageBox.question(
            parent, title, message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes