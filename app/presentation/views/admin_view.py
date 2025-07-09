from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QTabWidget
)
from PyQt6.QtCore import Qt

from app.presentation.controllers.auth_controller import AuthController
from app.presentation.views.base_view import CenteredView
from app.presentation.widgets.report_title_management_widget import ReportTitleManagementWidget
from app.presentation.widgets.user_management_widget import UserManagementWidget
from app.presentation.widgets.pacs_management_widget import PacsManagementWidget
from app.services.notification_service import NotificationService
from app.presentation.styles.style_manager import load_style


class AdminView(CenteredView):
    def __init__(self, auth_controller: AuthController):
        super().__init__()
        self._auth_controller = auth_controller
        self._notification_service = NotificationService()
        self.setWindowTitle("Admin Panel")
        self.setGeometry(100, 100, 1600, 800)

        self._setup_ui()
        load_style(self)
        self._setup_shortcuts()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Header section
        header_layout = QHBoxLayout()

        title_label = QLabel("Admin Panel - Management System")
        title_label.setObjectName("AdminTitle")

        current_user = self._auth_controller.get_current_user()
        username = current_user.username if current_user else "Unknown"
        full_name = current_user.get_full_name() if current_user and hasattr(current_user, 'get_full_name') else ""
        user_display = f"{full_name} ({username})" if full_name else username

        user_info_label = QLabel(f"Logat ca: {user_display}")
        user_info_label.setObjectName("UserLabel")

        self.logout_button = QPushButton("Logout")
        self.logout_button.setObjectName("LogoutButton")
        self.logout_button.clicked.connect(self._handle_logout)

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(user_info_label)
        header_layout.addWidget(self.logout_button)

        main_layout.addLayout(header_layout)

        # Create tab widget for admin sections
        self.admin_tabs = QTabWidget()
        # self.admin_tabs.setObjectName("AdminTabs")

        # Users tab
        self.user_widget = UserManagementWidget(self._auth_controller)
        self.user_widget.user_updated.connect(self._on_user_updated)
        self.admin_tabs.addTab(self.user_widget, "Users")

        # PACS URLs tab
        self.pacs_widget = PacsManagementWidget()
        self.pacs_widget.pacs_updated.connect(self._on_pacs_updated)
        self.admin_tabs.addTab(self.pacs_widget, "PACS URLs")

        # Report Title tab
        self.report_titles_widget = ReportTitleManagementWidget()
        self.report_titles_widget.titles_updated.connect(self._on_report_titles_updated)
        self.admin_tabs.addTab(self.report_titles_widget, "Report Titles")

        main_layout.addWidget(self.admin_tabs)

        # Shortcuts info
        shortcuts_info = QLabel(
            "💡 Shortcuts: Ctrl+F (Cauta) • Esc (Goleste cautarea) • F5 (Refresh) • Enter/Dublu-click (Editeaza)")
        shortcuts_info.setStyleSheet("color: #6b7280; font-size: 10px; font-style: italic; padding: 5px;")
        shortcuts_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        shortcuts_info.setMaximumHeight(25)
        main_layout.addWidget(shortcuts_info)

    def _setup_shortcuts(self):
        # Ctrl+F to focus search
        search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        search_shortcut.activated.connect(self._focus_current_search)

        # Escape to clear search
        clear_search_shortcut = QShortcut(QKeySequence("Escape"), self)
        clear_search_shortcut.activated.connect(self._clear_current_search_if_focused)

        # F5 to refresh current tab
        refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        refresh_shortcut.activated.connect(self._refresh_current_tab)

        # Enter to edit selected item
        edit_shortcut = QShortcut(QKeySequence("Return"), self)
        edit_shortcut.activated.connect(self._edit_selected_current_tab)

    def _focus_current_search(self):
        current_index = self.admin_tabs.currentIndex()
        if current_index == 0:  # Users tab
            self.user_widget.focus_search()
        elif current_index == 1:  # PACS tab
            self.pacs_widget.focus_search()
        elif current_index == 2:
            self.pacs_widget.focus_search() # Report Titles tab

    def _clear_current_search_if_focused(self):
        current_index = self.admin_tabs.currentIndex()
        if current_index == 0:  # Users tab
            self.user_widget.clear_search_if_focused()
        elif current_index == 1:  # PACS tab
            self.pacs_widget.clear_search_if_focused()
        elif current_index == 2:
            self.pacs_widget.focus_search() # Report Titles tab

    def _refresh_current_tab(self):
        current_index = self.admin_tabs.currentIndex()
        if current_index == 0:  # Users tab
            self.user_widget.refresh_data()
        elif current_index == 1:  # PACS tab
            self.pacs_widget.refresh_data()
        elif current_index == 2:
            self.pacs_widget.focus_search() # Report Titles tab

    def _edit_selected_current_tab(self):
        current_index = self.admin_tabs.currentIndex()
        if current_index == 0:  # Users tab
            self.user_widget.edit_selected()
        elif current_index == 1:  # PACS tab
            self.pacs_widget.edit_selected()
        elif current_index == 2:
            self.pacs_widget.focus_search() # Report Titles tab

    def _on_user_updated(self):
        print("User data updated")

    def _on_pacs_updated(self):
        print("PACS data updated")

    def _on_report_titles_updated(self):
        print("Report titles data updated")

    def _handle_logout(self):
        if self._auth_controller.logout(self):
            self._open_login_window()

    def _open_login_window(self):
        from app.presentation.views.login_view import LoginView
        from app.di.container import Container

        self.login_window = LoginView(Container.get_auth_controller())
        self.login_window.show()
        self.close()