from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from app.presentation.styles.style_manager import load_style
from app.presentation.views.base_view import CenteredView


class PatientsView(CenteredView):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Patients Management")
        load_style(self)

