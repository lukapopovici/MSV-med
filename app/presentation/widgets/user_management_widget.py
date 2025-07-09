from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QPushButton, QHBoxLayout, QLabel, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal

from app.di.container import Container
from app.core.entities.user import User, UserRole
from app.services.notification_service import NotificationService
from app.utils.validators import Validators


class UserManagementWidget(QWidget):
    user_updated = pyqtSignal()

    def __init__(self, auth_controller, parent=None):
        super().__init__(parent)
        self._auth_controller = auth_controller
        self._notification_service = NotificationService()

        # Editing state
        self._editing_user_id = None
        self._editing_mode = False

        self._setup_ui()
        self._load_users()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side - User list
        left_widget = self._create_user_list_section()
        splitter.addWidget(left_widget)

        # Right side - User form
        right_widget = self._create_user_form_section()
        splitter.addWidget(right_widget)

        splitter.setSizes([600, 400])
        layout.addWidget(splitter)

    def _create_user_list_section(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        section_title = QLabel("Utilizatori")
        section_title.setObjectName("SectionTitle")
        layout.addWidget(section_title)

        # Search layout
        search_layout = QHBoxLayout()

        self.user_search_input = QLineEdit()
        self.user_search_input.setPlaceholderText("Caută utilizatori (username sau nume)...")
        self.user_search_input.setObjectName("SearchInput")
        self.user_search_input.textChanged.connect(self._filter_users)

        self.clear_user_search_button = QPushButton("x")
        self.clear_user_search_button.setObjectName("ClearSearchButton")
        self.clear_user_search_button.setMaximumWidth(25)
        self.clear_user_search_button.setToolTip("Sterge cautarea")
        self.clear_user_search_button.clicked.connect(self._clear_user_search)
        self.clear_user_search_button.setVisible(False)

        search_layout.addWidget(self.user_search_input)
        search_layout.addWidget(self.clear_user_search_button)
        layout.addLayout(search_layout)

        # Results label
        self.user_results_label = QLabel()
        self.user_results_label.setVisible(False)
        self.user_results_label.setStyleSheet("color: #6b7280; font-size: 11px; padding: 2px;")
        layout.addWidget(self.user_results_label)

        self.users_table = QTableWidget()
        self.users_table.setColumnCount(5)  # Added column for title
        self.users_table.setHorizontalHeaderLabels(["ID", "Username", "Titulatura", "Nume Complet", "Rol"])
        self.users_table.verticalHeader().setVisible(False)
        self.users_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.users_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.users_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.users_table.itemSelectionChanged.connect(self._on_user_selected)
        self.users_table.itemDoubleClicked.connect(self._on_user_double_clicked)

        layout.addWidget(self.users_table)

        # User actions
        user_actions_layout = QHBoxLayout()

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_data)

        self.edit_user_button = QPushButton("Modifica user")
        self.edit_user_button.clicked.connect(self._edit_selected_user)
        self.edit_user_button.setEnabled(False)

        self.delete_user_button = QPushButton("Sterge user")
        self.delete_user_button.clicked.connect(self._delete_user)
        self.delete_user_button.setEnabled(False)

        user_actions_layout.addWidget(self.refresh_button)
        user_actions_layout.addWidget(self.edit_user_button)
        user_actions_layout.addWidget(self.delete_user_button)
        user_actions_layout.addStretch()

        layout.addLayout(user_actions_layout)

        return widget

    def _create_user_form_section(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.form_group = QGroupBox("Creeaza user")
        form_layout = QFormLayout(self.form_group)

        self.username_input = QLineEdit()
        self.username_input.setObjectName("UsernameInput")
        self.username_input.setPlaceholderText("Introdu username")

        self.first_name_input = QLineEdit()
        self.first_name_input.setObjectName("UsernameInput")
        self.first_name_input.setPlaceholderText("Introdu prenumele")

        self.last_name_input = QLineEdit()
        self.last_name_input.setObjectName("UsernameInput")
        self.last_name_input.setPlaceholderText("Introdu numele de familie")

        # New title input field
        self.title_input = QLineEdit()
        self.title_input.setObjectName("UsernameInput")
        self.title_input.setPlaceholderText("Dr., Univ. Dr., Prof. Dr., etc. (opțional)")

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setObjectName("PasswordInput")
        self.password_input.setPlaceholderText("Introdu parola")

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setObjectName("PasswordInput")
        self.confirm_password_input.setPlaceholderText("Confirma parola")

        self.role_input = QComboBox()
        self.role_input.addItems([role.value for role in UserRole])

        # Connect role change to title field visibility
        self.role_input.currentTextChanged.connect(self._on_role_changed)

        form_layout.addRow("Username:", self.username_input)
        form_layout.addRow("Prenume:", self.first_name_input)
        form_layout.addRow("Nume familie:", self.last_name_input)
        form_layout.addRow("Titulatura:", self.title_input)  # New title field
        form_layout.addRow("Parola:", self.password_input)
        form_layout.addRow("Confirma parola:", self.confirm_password_input)
        form_layout.addRow("Rol:", self.role_input)

        layout.addWidget(self.form_group)

        # Form buttons
        form_buttons_layout = QHBoxLayout()

        self.clear_button = QPushButton("Reset")
        self.clear_button.clicked.connect(self._clear_form)

        self.cancel_button = QPushButton("Anuleaza")
        self.cancel_button.setObjectName("CancelButton")
        self.cancel_button.clicked.connect(self._cancel_edit)
        self.cancel_button.setVisible(False)

        self.create_button = QPushButton("Creaza user")
        self.create_button.setObjectName("CreateButton")
        self.create_button.clicked.connect(self._handle_create_or_update_user)

        form_buttons_layout.addWidget(self.clear_button)
        form_buttons_layout.addWidget(self.cancel_button)
        form_buttons_layout.addWidget(self.create_button)

        layout.addLayout(form_buttons_layout)
        layout.addStretch()

        # Set initial title field state
        self._on_role_changed(self.role_input.currentText())

        return widget

    def _on_role_changed(self, role_text: str):
        is_doctor = role_text == "doctor"
        self.title_input.setEnabled(is_doctor)
        if not is_doctor:
            self.title_input.clear()
            self.title_input.setPlaceholderText("(doar pentru doctori)")
        else:
            self.title_input.setPlaceholderText("Dr., Univ. Dr., Prof. Dr., etc. (opțional)")

    def refresh_data(self):
        self._load_users()

    def focus_search(self):
        self.user_search_input.setFocus()

    def clear_search_if_focused(self):
        if self.user_search_input.hasFocus():
            self._clear_user_search()

    def edit_selected(self):
        self._edit_selected_user()

    def _load_users(self):
        try:
            user_repo = Container.get_user_repository()
            users = user_repo.find_all()

            self.users_table.setRowCount(len(users))

            for row, user in enumerate(users):
                self.users_table.setItem(row, 0, QTableWidgetItem(str(user.id)))
                self.users_table.setItem(row, 1, QTableWidgetItem(user.username))

                # Title column
                title_text = user.title if user.title else ""
                self.users_table.setItem(row, 2, QTableWidgetItem(title_text))

                # Full name column
                full_name = ""
                if user.first_name or user.last_name:
                    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
                self.users_table.setItem(row, 3, QTableWidgetItem(full_name))

                # Role column
                self.users_table.setItem(row, 4, QTableWidgetItem(user.role.value.title()))

            # Adjust column widths
            header = self.users_table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Username
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Title
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Full Name
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Role

            self._clear_user_search()

        except Exception as e:
            self._notification_service.show_error(self, "Eroare",
                                                  f"Nu s-au putut incarca conturile utilizatorilor: {e}")

    def _filter_users(self, text: str):
        self.clear_user_search_button.setVisible(bool(text.strip()))

        if not text.strip():
            self._show_all_users()
            return

        visible_count = 0
        total_count = self.users_table.rowCount()

        for row in range(total_count):
            username_item = self.users_table.item(row, 1)
            fullname_item = self.users_table.item(row, 3)
            title_item = self.users_table.item(row, 2)

            username_match = text.lower() in username_item.text().lower() if username_item else False
            fullname_match = text.lower() in fullname_item.text().lower() if fullname_item else False
            title_match = text.lower() in title_item.text().lower() if title_item else False

            if username_match or fullname_match or title_match:
                self.users_table.setRowHidden(row, False)
                visible_count += 1
            else:
                self.users_table.setRowHidden(row, True)

        if visible_count == 0:
            self.user_results_label.setText(f"Nu s-au gasit utilizatori pentru '{text}'")
            self.user_results_label.setStyleSheet("color: #dc2626; font-size: 11px; padding: 2px;")
        else:
            self.user_results_label.setText(f"Gasit {visible_count} din {total_count} utilizatori")
            self.user_results_label.setStyleSheet("color: #059669; font-size: 11px; padding: 2px;")

        self.user_results_label.setVisible(True)

    def _show_all_users(self):
        for row in range(self.users_table.rowCount()):
            self.users_table.setRowHidden(row, False)
        self.user_results_label.setVisible(False)

    def _clear_user_search(self):
        self.user_search_input.clear()
        self.clear_user_search_button.setVisible(False)
        self._show_all_users()

    def _on_user_selected(self):
        current_row = self.users_table.currentRow()
        has_selection = current_row >= 0

        self.delete_user_button.setEnabled(has_selection)
        self.edit_user_button.setEnabled(has_selection)

    def _on_user_double_clicked(self, item):
        self._edit_selected_user()

    def _edit_selected_user(self):
        current_row = self.users_table.currentRow()
        if current_row < 0:
            return

        user_id = int(self.users_table.item(current_row, 0).text())

        try:
            user_repo = Container.get_user_repository()
            user = user_repo.find_by_id(user_id)

            if not user:
                self._notification_service.show_error(self, "Eroare", "Utilizatorul nu a fost gasit.")
                return

            self.username_input.setText(user.username)
            self.first_name_input.setText(user.first_name or "")
            self.last_name_input.setText(user.last_name or "")
            self.title_input.setText(user.title or "")  # Set title field
            self.password_input.clear()
            self.confirm_password_input.clear()

            role_index = 0
            for i, role in enumerate(UserRole):
                if role == user.role:
                    role_index = i
                    break
            self.role_input.setCurrentIndex(role_index)

            # Update title field state based on role
            self._on_role_changed(user.role.value)

            self._editing_mode = True
            self._editing_user_id = user_id

            self.form_group.setTitle(f"Modifica user: {user.username}")
            self.create_button.setText("Actualizeaza user")
            self.cancel_button.setVisible(True)

            self.password_input.setPlaceholderText("Lasa gol pentru a pastra parola actuala")
            self.confirm_password_input.setPlaceholderText("Lasa gol pentru a pastra parola actuala")

            self.username_input.setFocus()

        except Exception as e:
            self._notification_service.show_error(self, "Eroare", f"Eroare la incarcarea datelor utilizatorului: {e}")

    def _cancel_edit(self):
        self._editing_mode = False
        self._editing_user_id = None

        self.form_group.setTitle("Creeaza user")
        self.create_button.setText("Creaza user")
        self.cancel_button.setVisible(False)

        self.password_input.setPlaceholderText("Introdu parola")
        self.confirm_password_input.setPlaceholderText("Confirma parola")

        self._clear_form()

    def _handle_create_or_update_user(self):
        if self._editing_mode:
            self._handle_update_user()
        else:
            self._handle_create_user()

    def _handle_create_user(self):
        username = self.username_input.text().strip()
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        title = self.title_input.text().strip()
        password = self.password_input.text().strip()
        confirm_password = self.confirm_password_input.text().strip()
        role_value = self.role_input.currentText()

        # Validation
        username_error = Validators.validate_username(username)
        if username_error:
            self._notification_service.show_warning(self, "Validation Error", username_error)
            return

        if first_name:
            first_name_error = Validators.validate_name(first_name, "Prenumele")
            if first_name_error:
                self._notification_service.show_warning(self, "Validation Error", first_name_error)
                return

        if last_name:
            last_name_error = Validators.validate_name(last_name, "Numele de familie")
            if last_name_error:
                self._notification_service.show_warning(self, "Validation Error", last_name_error)
                return

        # Validate title for doctors
        if role_value == "doctor" and title:
            if len(title) > 100:
                self._notification_service.show_warning(self, "Validation Error",
                                                        "Titulatura trebuie să aibă mai puțin de 100 caractere")
                return

        password_error = Validators.validate_password(password)
        if password_error:
            self._notification_service.show_warning(self, "Validation Error", password_error)
            return

        if password != confirm_password:
            self._notification_service.show_warning(self, "Validation Error", "Parolele sunt diferite.")
            return

        try:
            auth_service = Container.get_auth_service()
            user_repo = Container.get_user_repository()

            hashed_password = auth_service.hash_password(password)
            role = UserRole(role_value)

            new_user = User(
                id=0,
                username=username,
                password=hashed_password,
                role=role,
                first_name=first_name if first_name else None,
                last_name=last_name if last_name else None,
                title=title if title and role == UserRole.DOCTOR else None  # Only set title for doctors
            )

            user_repo.create(new_user)

            display_name = new_user.get_full_name_with_title() if new_user.title else f"{username}"
            self._notification_service.show_info(self, "Succes",
                                                 f"Utilizatorul '{display_name}' a fost creat cu succes.")
            self._clear_form()
            self._load_users()
            self.user_updated.emit()

        except Exception as e:
            self._notification_service.show_error(self, "Error", f"Nu s-a putut crea utilizatorul nou: {e}")

    def _handle_update_user(self):
        username = self.username_input.text().strip()
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        title = self.title_input.text().strip()
        password = self.password_input.text().strip()
        confirm_password = self.confirm_password_input.text().strip()
        role_value = self.role_input.currentText()

        # Validation
        username_error = Validators.validate_username(username)
        if username_error:
            self._notification_service.show_warning(self, "Validation Error", username_error)
            return

        if first_name:
            first_name_error = Validators.validate_name(first_name, "Prenumele")
            if first_name_error:
                self._notification_service.show_warning(self, "Validation Error", first_name_error)
                return

        if last_name:
            last_name_error = Validators.validate_name(last_name, "Numele de familie")
            if last_name_error:
                self._notification_service.show_warning(self, "Validation Error", last_name_error)
                return

        # Validate title for doctors
        if role_value == "doctor" and title:
            if len(title) > 100:
                self._notification_service.show_warning(self, "Validation Error",
                                                        "Titulatura trebuie să aibă mai puțin de 100 caractere")
                return

        if password:
            password_error = Validators.validate_password(password)
            if password_error:
                self._notification_service.show_warning(self, "Validation Error", password_error)
                return

            if password != confirm_password:
                self._notification_service.show_warning(self, "Validation Error", "Parolele sunt diferite.")
                return

        try:
            auth_service = Container.get_auth_service()
            user_repo = Container.get_user_repository()

            current_user = user_repo.find_by_id(self._editing_user_id)
            if not current_user:
                self._notification_service.show_error(self, "Eroare", "Utilizatorul nu mai existe.")
                return

            existing_user = user_repo.find_by_username(username)
            if existing_user and existing_user.id != self._editing_user_id:
                self._notification_service.show_error(self, "Eroare",
                                                      f"Username-ul '{username}' este deja folosit de alt utilizator.")
                return

            role = UserRole(role_value)

            if password:
                hashed_password = auth_service.hash_password(password)
            else:
                hashed_password = current_user.password

            updated_user = User(
                id=self._editing_user_id,
                username=username,
                password=hashed_password,
                role=role,
                first_name=first_name if first_name else None,
                last_name=last_name if last_name else None,
                title=title if title and role == UserRole.DOCTOR else None  # Only set title for doctors
            )

            user_repo.update(updated_user)

            display_name = updated_user.get_full_name_with_title() if updated_user.title else f"{username}"
            self._notification_service.show_info(self, "Succes",
                                                 f"Utilizatorul '{display_name}' a fost actualizat cu succes.")

            self._cancel_edit()
            self._load_users()
            self.user_updated.emit()

        except Exception as e:
            self._notification_service.show_error(self, "Error", f"Nu s-a putut actualiza utilizatorul: {e}")

    def _delete_user(self):
        current_row = self.users_table.currentRow()

        if current_row >= 0:
            user_id = int(self.users_table.item(current_row, 0).text())
            username = self.users_table.item(current_row, 1).text()
            title = self.users_table.item(current_row, 2).text()
            full_name = self.users_table.item(current_row, 3).text()

            current_user = self._auth_controller.get_current_user()
            if current_user and current_user.id == user_id:
                self._notification_service.show_warning(self, "Atentie", "Nu poti sa iti stergi propriu cont.")
                return

            display_name = f"{title} {full_name}".strip() if title else full_name
            if not display_name:
                display_name = username

            if self._notification_service.ask_confirmation(
                    self, "Confirm Delete", f"Esti sigur ca vrei sa stergi utilizatorul '{display_name}'?"
            ):
                try:
                    user_repo = Container.get_user_repository()

                    if user_repo.delete(user_id):
                        self._notification_service.show_info(self, "Succes", "Utilizator sters cu succes.")

                        if self._editing_mode and self._editing_user_id == user_id:
                            self._cancel_edit()

                        self._load_users()
                        self.user_updated.emit()
                    else:
                        self._notification_service.show_error(self, "Eroare", "Eroare la stergerea utilizatorului")

                except Exception as e:
                    self._notification_service.show_error(self, "Eroare", f"Eroare la stergerea utilizatorului: {e}")

    def _clear_form(self):
        self.username_input.clear()
        self.first_name_input.clear()
        self.last_name_input.clear()
        self.title_input.clear()
        self.password_input.clear()
        self.confirm_password_input.clear()
        self.role_input.setCurrentIndex(0)
        self._on_role_changed(self.role_input.currentText())

        if not self._editing_mode:
            self.username_input.setFocus()