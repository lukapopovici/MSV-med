from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QCheckBox,
    QPushButton, QHBoxLayout, QLabel, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QSplitter, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from app.di.container import Container
from app.services.notification_service import NotificationService


class PacsManagementWidget(QWidget):
    pacs_updated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._notification_service = NotificationService()
        self._needs_restart = False

        # Editing state
        self._editing_pacs_id = None
        self._editing_pacs_mode = False

        self._setup_ui()
        self._load_pacs_urls()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side - PACS list
        left_widget = self._create_pacs_list_section()
        splitter.addWidget(left_widget)

        # Right side - PACS form
        right_widget = self._create_pacs_form_section()
        splitter.addWidget(right_widget)

        splitter.setSizes([600, 400])
        layout.addWidget(splitter)

    def _create_pacs_list_section(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        section_title = QLabel("PACS URLs")
        section_title.setObjectName("SectionTitle")
        layout.addWidget(section_title)

        # Search layout
        search_layout = QHBoxLayout()

        self.pacs_search_input = QLineEdit()
        self.pacs_search_input.setPlaceholderText("Caută PACS (nume sau URL)...")
        self.pacs_search_input.setObjectName("SearchInput")
        self.pacs_search_input.textChanged.connect(self._filter_pacs)

        self.clear_pacs_search_button = QPushButton("x")
        self.clear_pacs_search_button.setObjectName("ClearSearchButton")
        self.clear_pacs_search_button.setMaximumWidth(25)
        self.clear_pacs_search_button.setToolTip("Sterge cautarea")
        self.clear_pacs_search_button.clicked.connect(self._clear_pacs_search)
        self.clear_pacs_search_button.setVisible(False)

        search_layout.addWidget(self.pacs_search_input)
        search_layout.addWidget(self.clear_pacs_search_button)
        layout.addLayout(search_layout)

        # Results label
        self.pacs_results_label = QLabel()
        self.pacs_results_label.setVisible(False)
        self.pacs_results_label.setStyleSheet("color: #6b7280; font-size: 11px; padding: 2px;")
        layout.addWidget(self.pacs_results_label)

        # PACS table
        self.pacs_table = QTableWidget()
        self.pacs_table.setColumnCount(4)
        self.pacs_table.setHorizontalHeaderLabels(["ID", "Name", "URL", "Username"])
        self.pacs_table.verticalHeader().setVisible(False)
        self.pacs_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.pacs_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pacs_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.pacs_table.itemSelectionChanged.connect(self._on_pacs_selected)
        self.pacs_table.itemDoubleClicked.connect(self._on_pacs_double_clicked)

        layout.addWidget(self.pacs_table)

        # PACS actions
        pacs_actions_layout = QHBoxLayout()

        self.refresh_pacs_button = QPushButton("Refresh")
        self.refresh_pacs_button.clicked.connect(self.refresh_data)

        self.edit_pacs_button = QPushButton("Modifica PACS")
        self.edit_pacs_button.clicked.connect(self._edit_selected_pacs)
        self.edit_pacs_button.setEnabled(False)

        self.test_connection_button = QPushButton("Test Connection")
        self.test_connection_button.setObjectName("TestButton")
        self.test_connection_button.clicked.connect(self._test_pacs_connection)
        self.test_connection_button.setEnabled(False)

        self.delete_pacs_button = QPushButton("Sterge PACS")
        self.delete_pacs_button.clicked.connect(self._delete_pacs_url)
        self.delete_pacs_button.setEnabled(False)

        pacs_actions_layout.addWidget(self.refresh_pacs_button)
        pacs_actions_layout.addWidget(self.edit_pacs_button)
        pacs_actions_layout.addWidget(self.test_connection_button)
        pacs_actions_layout.addWidget(self.delete_pacs_button)
        pacs_actions_layout.addStretch()

        layout.addLayout(pacs_actions_layout)

        return widget

    def _create_pacs_form_section(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Form group
        self.pacs_form_group = QGroupBox("Creeaza PACS URL")
        form_layout = QFormLayout(self.pacs_form_group)

        self.pacs_name_input = QLineEdit()
        self.pacs_name_input.setObjectName("UsernameInput")
        self.pacs_name_input.setPlaceholderText("ex: Main PACS, Backup PACS")

        self.pacs_url_input = QLineEdit()
        self.pacs_url_input.setObjectName("UsernameInput")
        self.pacs_url_input.setPlaceholderText("http://localhost:8042")

        self.pacs_username_input = QLineEdit()
        self.pacs_username_input.setObjectName("UsernameInput")
        self.pacs_username_input.setPlaceholderText("orthanc")

        self.pacs_password_input = QLineEdit()
        self.pacs_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pacs_password_input.setObjectName("PasswordInput")
        self.pacs_password_input.setPlaceholderText("parola PACS")

        form_layout.addRow("Nume:", self.pacs_name_input)
        form_layout.addRow("URL:", self.pacs_url_input)
        form_layout.addRow("Username:", self.pacs_username_input)
        form_layout.addRow("Parola:", self.pacs_password_input)

        layout.addWidget(self.pacs_form_group)

        # Form buttons
        pacs_form_buttons_layout = QHBoxLayout()

        self.clear_pacs_button = QPushButton("Reset")
        self.clear_pacs_button.clicked.connect(self._clear_pacs_form)

        self.cancel_pacs_button = QPushButton("Anuleaza")
        self.cancel_pacs_button.setObjectName("CancelButton")
        self.cancel_pacs_button.clicked.connect(self._cancel_pacs_edit)
        self.cancel_pacs_button.setVisible(False)

        self.create_pacs_button = QPushButton("Creaza PACS")
        self.create_pacs_button.setObjectName("CreateButton")
        self.create_pacs_button.clicked.connect(self._handle_create_or_update_pacs)

        pacs_form_buttons_layout.addWidget(self.clear_pacs_button)
        pacs_form_buttons_layout.addWidget(self.cancel_pacs_button)
        pacs_form_buttons_layout.addWidget(self.create_pacs_button)

        layout.addLayout(pacs_form_buttons_layout)

        # Global PACS Selection
        selection_group = QGroupBox("Selectare PACS Global")
        selection_layout = QFormLayout(selection_group)

        self.source_pacs_combo = QComboBox()
        self.source_pacs_combo.setObjectName("SourcePacsCombo")
        self.source_pacs_combo.currentIndexChanged.connect(self._on_source_pacs_changed)

        self.target_pacs_combo = QComboBox()
        self.target_pacs_combo.setObjectName("TargetPacsCombo")
        self.target_pacs_combo.currentIndexChanged.connect(self._on_target_pacs_changed)

        selection_layout.addRow("PACS Sursă (pentru citire):", self.source_pacs_combo)
        selection_layout.addRow("PACS Țintă (pentru trimitere):", self.target_pacs_combo)

        layout.addWidget(selection_group)

        # Restart section
        restart_group = QGroupBox("Restart Aplicație")
        restart_layout = QVBoxLayout(restart_group)

        restart_info_label = QLabel(
            "Dacă ai modificat configurația PACS, repornește aplicația\n"
            "pentru ca modificările să aibă efect complet."
        )
        restart_info_label.setWordWrap(True)
        restart_info_label.setStyleSheet("color: #f59e0b; font-size: 11px; padding: 8px;")
        restart_layout.addWidget(restart_info_label)

        restart_button_layout = QHBoxLayout()

        self.restart_app_button = QPushButton("Restart Aplicație")
        self.restart_app_button.setObjectName("RestartButton")
        self.restart_app_button.clicked.connect(self._restart_application)

        restart_button_layout.addStretch()
        restart_button_layout.addWidget(self.restart_app_button)
        restart_button_layout.addStretch()

        restart_layout.addLayout(restart_button_layout)
        layout.addWidget(restart_group)

        layout.addStretch()
        return widget

    def refresh_data(self):
        self._load_pacs_urls()

    def focus_search(self):
        self.pacs_search_input.setFocus()

    def clear_search_if_focused(self):
        if self.pacs_search_input.hasFocus():
            self._clear_pacs_search()

    def edit_selected(self):
        self._edit_selected_pacs()

    def _load_pacs_urls(self):
        try:
            pacs_service = Container.get_pacs_url_service()
            pacs_urls = pacs_service.get_all_pacs_urls()

            self.pacs_table.setRowCount(len(pacs_urls))

            for row, pacs in enumerate(pacs_urls):
                self.pacs_table.setItem(row, 0, QTableWidgetItem(str(pacs.id)))
                self.pacs_table.setItem(row, 1, QTableWidgetItem(pacs.name))
                self.pacs_table.setItem(row, 2, QTableWidgetItem(pacs.url))
                self.pacs_table.setItem(row, 3, QTableWidgetItem(pacs.username))

            # Adjust column widths
            header = self.pacs_table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Name
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # URL
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Username

            self._clear_pacs_search()
            self._load_pacs_combos()

        except Exception as e:
            self._notification_service.show_error(self, "Eroare", f"Nu s-au putut incarca URL-urile PACS: {e}")

    def _filter_pacs(self, text: str):
        self.clear_pacs_search_button.setVisible(bool(text.strip()))

        if not text.strip():
            self._show_all_pacs()
            return

        visible_count = 0
        total_count = self.pacs_table.rowCount()

        for row in range(total_count):
            name_item = self.pacs_table.item(row, 1)  # Name column
            url_item = self.pacs_table.item(row, 2)  # URL column

            name_match = text.lower() in name_item.text().lower() if name_item else False
            url_match = text.lower() in url_item.text().lower() if url_item else False

            if name_match or url_match:
                self.pacs_table.setRowHidden(row, False)
                visible_count += 1
            else:
                self.pacs_table.setRowHidden(row, True)

        if visible_count == 0:
            self.pacs_results_label.setText(f"Nu s-au găsit PACS-uri pentru '{text}'")
            self.pacs_results_label.setStyleSheet("color: #dc2626; font-size: 11px; padding: 2px;")
        else:
            self.pacs_results_label.setText(f"Găsite {visible_count} din {total_count} PACS-uri")
            self.pacs_results_label.setStyleSheet("color: #059669; font-size: 11px; padding: 2px;")

        self.pacs_results_label.setVisible(True)

    def _show_all_pacs(self):
        for row in range(self.pacs_table.rowCount()):
            self.pacs_table.setRowHidden(row, False)
        self.pacs_results_label.setVisible(False)

    def _clear_pacs_search(self):
        self.pacs_search_input.clear()
        self.clear_pacs_search_button.setVisible(False)
        self._show_all_pacs()

    def _on_pacs_selected(self):
        current_row = self.pacs_table.currentRow()
        has_selection = current_row >= 0

        self.edit_pacs_button.setEnabled(has_selection)
        self.test_connection_button.setEnabled(has_selection)
        self.delete_pacs_button.setEnabled(has_selection)

    def _on_pacs_double_clicked(self, item):
        self._edit_selected_pacs()

    def _edit_selected_pacs(self):
        current_row = self.pacs_table.currentRow()
        if current_row < 0:
            return

        pacs_id = int(self.pacs_table.item(current_row, 0).text())

        try:
            pacs_service = Container.get_pacs_url_service()
            pacs = pacs_service.get_pacs_by_id(pacs_id)

            if not pacs:
                self._notification_service.show_error(self, "Eroare", "PACS-ul nu a fost gasit.")
                return

            # Fill form with PACS data
            self.pacs_name_input.setText(pacs.name)
            self.pacs_url_input.setText(pacs.url)
            self.pacs_username_input.setText(pacs.username)
            self.pacs_password_input.setText(pacs.password)

            # Switch to edit mode
            self._editing_pacs_mode = True
            self._editing_pacs_id = pacs_id

            self.pacs_form_group.setTitle(f"Modifica PACS: {pacs.name}")
            self.create_pacs_button.setText("Actualizeaza PACS")
            self.cancel_pacs_button.setVisible(True)

            self.pacs_name_input.setFocus()

        except Exception as e:
            self._notification_service.show_error(self, "Eroare", f"Eroare la incarcarea datelor PACS: {e}")

    def _cancel_pacs_edit(self):
        self._editing_pacs_mode = False
        self._editing_pacs_id = None

        self.pacs_form_group.setTitle("Creeaza PACS URL")
        self.create_pacs_button.setText("Creaza PACS")
        self.cancel_pacs_button.setVisible(False)

        self._clear_pacs_form()

    def _handle_create_or_update_pacs(self):
        if self._editing_pacs_mode:
            self._handle_update_pacs()
        else:
            self._handle_create_pacs()

    def _handle_create_pacs(self):
        name = self.pacs_name_input.text().strip()
        url = self.pacs_url_input.text().strip()
        username = self.pacs_username_input.text().strip()
        password = self.pacs_password_input.text().strip()

        try:
            pacs_service = Container.get_pacs_url_service()

            # Validate
            errors = pacs_service.validate_pacs_data(name, url, username, password)
            if errors:
                self._notification_service.show_warning(self, "Eroare validare", "\n".join(errors))
                return

            # Create PACS
            pacs_service.create_pacs_url(name, url, username, password)

            self._notification_service.show_info(self, "Succes", f"PACS '{name}' a fost creat cu succes.")
            self._clear_pacs_form()
            self._load_pacs_urls()
            self.pacs_updated.emit()

        except Exception as e:
            self._notification_service.show_error(self, "Eroare", f"Nu s-a putut crea PACS-ul: {e}")

    def _handle_update_pacs(self):
        name = self.pacs_name_input.text().strip()
        url = self.pacs_url_input.text().strip()
        username = self.pacs_username_input.text().strip()
        password = self.pacs_password_input.text().strip()

        try:
            pacs_service = Container.get_pacs_url_service()

            # Validate
            errors = pacs_service.validate_pacs_data(name, url, username, password)
            if errors:
                self._notification_service.show_warning(self, "Eroare validare", "\n".join(errors))
                return

            # Update PACS
            success = pacs_service.update_pacs_url(
                self._editing_pacs_id, name, url, username, password
            )

            if success:
                self._notification_service.show_info(self, "Succes", f"PACS '{name}' a fost actualizat cu succes.")
                self._cancel_pacs_edit()
                self._load_pacs_urls()
                self.pacs_updated.emit()
            else:
                self._notification_service.show_error(self, "Eroare", "Nu s-a putut actualiza PACS-ul.")

        except Exception as e:
            self._notification_service.show_error(self, "Eroare", f"Nu s-a putut actualiza PACS-ul: {e}")

    def _test_pacs_connection(self):
        current_row = self.pacs_table.currentRow()
        if current_row >= 0:
            pacs_id = int(self.pacs_table.item(current_row, 0).text())
            pacs_name = self.pacs_table.item(current_row, 1).text()

            try:
                pacs_service = Container.get_pacs_url_service()

                # Show testing message
                self.test_connection_button.setText("Testing...")
                self.test_connection_button.setEnabled(False)

                # Test connection
                if pacs_service.test_pacs_connection(pacs_id):
                    self._notification_service.show_info(self, "Test Conexiune",
                                                         f"Conexiunea la PACS '{pacs_name}' a reușit!")
                else:
                    self._notification_service.show_warning(self, "Test Conexiune",
                                                            f"Conexiunea la PACS '{pacs_name}' a eșuat.")

            except Exception as e:
                self._notification_service.show_error(self, "Eroare", f"Eroare la testarea conexiunii: {e}")

            finally:
                self.test_connection_button.setText("Test Connection")
                self.test_connection_button.setEnabled(True)

    def _delete_pacs_url(self):
        current_row = self.pacs_table.currentRow()
        if current_row >= 0:
            pacs_id = int(self.pacs_table.item(current_row, 0).text())
            pacs_name = self.pacs_table.item(current_row, 1).text()

            if self._notification_service.ask_confirmation(
                    self, "Confirm Delete", f"Esti sigur ca vrei sa stergi PACS-ul '{pacs_name}'?"
            ):
                try:
                    pacs_service = Container.get_pacs_url_service()

                    if pacs_service.delete_pacs_url(pacs_id):
                        self._notification_service.show_info(self, "Succes", "PACS sters cu succes.")

                        # If editing this PACS, cancel edit mode
                        if self._editing_pacs_mode and self._editing_pacs_id == pacs_id:
                            self._cancel_pacs_edit()

                        self._load_pacs_urls()
                        self.pacs_updated.emit()
                    else:
                        self._notification_service.show_error(self, "Eroare", "Nu s-a putut sterge PACS-ul.")

                except Exception as e:
                    self._notification_service.show_error(self, "Eroare", f"Nu s-a putut sterge PACS-ul: {e}")

    def _clear_pacs_form(self):
        self.pacs_name_input.clear()
        self.pacs_url_input.clear()
        self.pacs_username_input.clear()
        self.pacs_password_input.clear()

        if not self._editing_pacs_mode:
            self.pacs_name_input.setFocus()

    def _load_pacs_combos(self):
        try:
            from app.di.container import Container
            pacs_service = Container.get_pacs_url_service()
            settings_service = Container.get_settings_service()

            all_pacs = pacs_service.get_all_pacs_urls()

            # Clear combos
            self.source_pacs_combo.clear()
            self.target_pacs_combo.clear()

            # Get current selections from database
            source_pacs_id = settings_service.get_source_pacs_id()
            target_pacs_id = settings_service.get_target_pacs_id()

            # Track if we found the current selections
            source_found = False
            target_found = False

            # Add all PACS
            for pacs in all_pacs:
                display_text = f"{pacs.name} ({pacs.url})"

                # Mark current selections with indicators
                if pacs.id == source_pacs_id:
                    source_display = f"{display_text}"
                    source_found = True
                else:
                    source_display = display_text

                if pacs.id == target_pacs_id:
                    target_display = f"{display_text}"
                    target_found = True
                else:
                    target_display = display_text

                self.source_pacs_combo.addItem(source_display, pacs.id)
                self.target_pacs_combo.addItem(target_display, pacs.id)

            # Set current selections based on database values
            if source_pacs_id is None:
                # Auto mode
                self.source_pacs_combo.setCurrentIndex(0)
            elif source_found:
                # Find and select the source PACS
                for i in range(self.source_pacs_combo.count()):
                    if self.source_pacs_combo.itemData(i) == source_pacs_id:
                        self.source_pacs_combo.setCurrentIndex(i)
                        break

            if target_pacs_id and target_found:
                # Find and select the target PACS
                for i in range(self.target_pacs_combo.count()):
                    if self.target_pacs_combo.itemData(i) == target_pacs_id:
                        self.target_pacs_combo.setCurrentIndex(i)
                        break

            # Show status messages
            if source_pacs_id:
                source_pacs = pacs_service.get_pacs_by_id(source_pacs_id)
                if source_pacs:
                    print(f"Source PACS loaded: {source_pacs.name} ({source_pacs.url})")
                else:
                    print(f"Source PACS ID {source_pacs_id} not found")
            else:
                print("Source PACS set to Auto mode")

            if target_pacs_id:
                target_pacs = pacs_service.get_pacs_by_id(target_pacs_id)
                if target_pacs:
                    print(f"Target PACS loaded: {target_pacs.name} ({target_pacs.url})")
                else:
                    print(f"Target PACS ID {target_pacs_id} not found")
            else:
                print("No target PACS set")

        except Exception as e:
            self._notification_service.show_error(self, "Eroare", f"Nu s-au putut încărca PACS-urile în combo: {e}")

    def _on_source_pacs_changed(self, index):
        pacs_id = self.source_pacs_combo.itemData(index)

        try:
            from app.di.container import Container
            settings_service = Container.get_settings_service()

            if pacs_id == -1:  # Auto mode
                settings_service.set_source_pacs_id(None)
                print("Source PACS set to Auto (First)")
            else:
                settings_service.set_source_pacs_id(pacs_id)
                pacs_name = self.source_pacs_combo.currentText()
                print(f"Source PACS set to: {pacs_name}")

            self._needs_restart = True
            self._update_restart_indicator()

        except Exception as e:
            print(f"Error saving source PACS setting: {e}")

    def _on_target_pacs_changed(self, index):
        pacs_id = self.target_pacs_combo.itemData(index)

        try:
            from app.di.container import Container
            settings_service = Container.get_settings_service()

            settings_service.set_target_pacs_id(pacs_id)
            pacs_name = self.target_pacs_combo.currentText()
            print(f"Target PACS set to: {pacs_name}")

            self._needs_restart = True
            self._update_restart_indicator()

        except Exception as e:
            print(f"Error saving target PACS setting: {e}")

    def _restart_application(self):
        try:
            import sys
            import os
            from PyQt6.QtWidgets import QApplication

            # Show final confirmation
            final_reply = self._notification_service.ask_confirmation(
                self,
                "Confirmare restart",
                "Aplicația se va închide și va reporni.\n\n"
                "Asigură-te că ai salvat toate datele importante.\n\n"
                "Continui?"
            )

            if final_reply:
                print("Restarting application...")

                python = sys.executable

                QApplication.quit()

                os.execl(python, python, "-m", "app.main")

        except Exception as e:
            self._notification_service.show_error(
                self,
                "Eroare restart",
                f"Nu am putut reporni aplicația automat: {e}\n\n"
                "Te rog să închizi și să repornești manual aplicația."
            )

    def _update_restart_indicator(self):
        if self._needs_restart:
            self.restart_app_button.setText("Restart Aplicație (NECESAR)")
        else:
            self.restart_app_button.setText("Restart Aplicație")
