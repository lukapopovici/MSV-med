from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QVBoxLayout, QStackedWidget, QLabel
)
from app.presentation.controllers.auth_controller import AuthController
from app.presentation.controllers.hybrid_pacs_controller import HybridPacsController
from app.presentation.views.base_view import CenteredView
from app.presentation.views.enhanced_pacs_view import EnhancedPacsView
from app.presentation.views.patients_view import PatientsView
from app.presentation.styles.style_manager import load_style


class MainView(CenteredView):

    def __init__(self, auth_controller: AuthController, pacs_controller: HybridPacsController):
        super().__init__()
        self._auth_controller = auth_controller
        self._pacs_controller = pacs_controller
        self.setWindowTitle("Enhanced Medical PACS System")
        self.setGeometry(100, 100, 1800, 900)
        self._setup_ui()
        load_style(self)
        self.patients_button.setEnabled(False)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        self.nav_widget = QWidget()
        self.nav_widget.setObjectName("NavBar")
        nav_bar = QHBoxLayout(self.nav_widget)

        # Navigation buttons
        self.studies_button = QPushButton("Studies")
        self.studies_button.setObjectName("NavButton")
        self.patients_button = QPushButton("Patients")
        self.patients_button.setObjectName("NavButton")

        current_user = self._auth_controller.get_current_user()
        username = current_user.username if current_user else "Unknown"
        role = current_user.role.value.title() if current_user else "Unknown"
        full_name = current_user.get_full_name() if current_user and hasattr(current_user, 'get_full_name') else ""

        user_display = f"{full_name} ({username})" if full_name else username
        self.user_label = QLabel(f"{user_display} | {role}")
        self.user_label.setObjectName("UserLabel")

        self.logout_button = QPushButton("Logout")
        self.logout_button.setObjectName("LogoutButton")

        self.studies_button.clicked.connect(lambda: self._switch_page(0))
        self.patients_button.clicked.connect(lambda: self._switch_page(1))
        self.logout_button.clicked.connect(self._handle_logout)

        nav_bar.addWidget(self.studies_button)
        nav_bar.addWidget(self.patients_button)
        nav_bar.addStretch()
        nav_bar.addWidget(self.user_label)
        nav_bar.addWidget(self.logout_button)

        main_layout.addWidget(self.nav_widget)

        self.pages = QStackedWidget()

        self.pacs_page = EnhancedPacsView(self._pacs_controller, self._auth_controller)
        self.patients_page = PatientsView()

        self.pages.addWidget(self.pacs_page)
        self.pages.addWidget(self.patients_page)

        main_layout.addWidget(self.pages)

        self._switch_page(0)

    def _switch_page(self, index: int):
        self.pages.setCurrentIndex(index)

        self.studies_button.setProperty("active", index == 0)
        self.patients_button.setProperty("active", index == 1)

        self.studies_button.style().unpolish(self.studies_button)
        self.studies_button.style().polish(self.studies_button)
        self.patients_button.style().unpolish(self.patients_button)
        self.patients_button.style().polish(self.patients_button)

    def _handle_logout(self):
        if self._auth_controller.logout(self):
            self._open_login_window()

    def _open_login_window(self):
        from app.presentation.views.login_view import LoginView
        from app.di.container import Container

        self.login_window = LoginView(Container.get_auth_controller())
        self.login_window.show()
        self.close()
