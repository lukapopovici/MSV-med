from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import pyqtSignal
from typing import Optional


class BaseWidget(QWidget):

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        pass

    def connect_signals(self):
        pass


class ConfirmationDialog(BaseWidget):
    confirmed = pyqtSignal()
    cancelled = pyqtSignal()

    def __init__(self, title: str, message: str, parent: Optional[QWidget] = None):
        self.title = title
        self.message = message
        super().__init__(parent)
        self.setWindowTitle(title)

    def setup_ui(self):
        layout = QVBoxLayout(self)

        message_label = QLabel(self.message)
        layout.addWidget(message_label)

        button_layout = QHBoxLayout()

        self.confirm_button = QPushButton("Confirm")
        self.cancel_button = QPushButton("Cancel")

        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.confirm_button)

        layout.addLayout(button_layout)

    def connect_signals(self):
        self.confirm_button.clicked.connect(self.confirmed.emit)
        self.confirm_button.clicked.connect(self.close)
        self.cancel_button.clicked.connect(self.cancelled.emit)
        self.cancel_button.clicked.connect(self.close)


class LoadingWidget(BaseWidget):

    def __init__(self, message: str = "Loading...", parent: Optional[QWidget] = None):
        self.message = message
        super().__init__(parent)

    def setup_ui(self):
        layout = QVBoxLayout(self)

        loading_label = QLabel(self.message)
        loading_label.setObjectName("LoadingLabel")

        layout.addWidget(loading_label)

    def set_message(self, message: str):
        self.message = message
        if hasattr(self, 'loading_label'):
            self.loading_label.setText(message)