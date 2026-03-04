from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QFormLayout, QLineEdit, QPushButton, QVBoxLayout, QLabel, QHBoxLayout
)
from app.presentation.controllers.auth_controller import AuthController
from app.core.entities.user import UserRole
from app.presentation.styles.style_manager import load_style
from app.presentation.views.base_view import CenteredView
from app.services.notification_service import NotificationService


class LoginView(CenteredView):
    def __init__(self, auth_controller: AuthController):
        super().__init__()
        self._auth_controller = auth_controller
        self._notification_service = NotificationService()
        self.setWindowTitle("Medical App - Login")
        self.setGeometry(100, 100, 1600, 800)
        self._setup_ui()
        load_style(self)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Card-ul principal de login
        card = QWidget()
        card.setObjectName("LoginCard")
        card.setFixedSize(420, 480)

        # Layout pentru conținutul card-ului
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 25, 40, 25)
        card_layout.setSpacing(18)

        # Icon medical
        icon = QLabel("🏥")
        icon.setObjectName("LoginIcon")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(icon)

        # Title aplicație
        title = QLabel("MediCore")
        title.setObjectName("LoginTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Sistem de Imagistică Medicală")
        subtitle.setObjectName("LoginSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(subtitle)

        card_layout.addSpacing(12)

        # Username input
        self.username_input = QLineEdit()
        self.username_input.setObjectName("CredentialInput")
        self.username_input.setPlaceholderText("Introdu username-ul")
        card_layout.addWidget(self.username_input)

        # Password input
        self.password_input = QLineEdit()
        self.password_input.setObjectName("CredentialInput")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Introdu parola")
        card_layout.addWidget(self.password_input)

        card_layout.addSpacing(8)

        # Login button
        self.login_button = QPushButton("Conectează-te")
        self.login_button.setObjectName("LoginButton")
        self.login_button.clicked.connect(self._handle_login)
        card_layout.addWidget(self.login_button)

        main_layout.addStretch(2)

        h_layout = QHBoxLayout()
        h_layout.addStretch(1)
        h_layout.addWidget(card)
        h_layout.addStretch(1)

        main_layout.addLayout(h_layout)

        main_layout.addStretch(3)

        # Event handlers pentru Enter
        self.username_input.returnPressed.connect(self._handle_login)
        self.password_input.returnPressed.connect(self._handle_login)

        # Focus pe username
        self.username_input.setFocus()

    def _handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            self._notification_service.show_warning(
                self, "Atentie", "Introduceti username-ul si parola."
            )
            return

        if self._auth_controller.login(username, password, self):
            user = self._auth_controller.get_current_user()
            self._open_main_window(user.role)

    def _open_main_window(self, role: UserRole):
        from app.di.container import Container

        if role == UserRole.ADMIN:
            from app.presentation.views.admin_view import AdminView
            self.main_window = AdminView(Container.get_auth_controller())
        elif role == UserRole.DOCTOR:
            from app.presentation.views.main_view import MainView
            self.main_window = MainView(
                Container.get_auth_controller(),
                Container.get_pacs_controller()
            )
        else:
            self._notification_service.show_warning(self, "Atentie", "Rol necunoscut.")

        self.main_window.show()
        self.close()