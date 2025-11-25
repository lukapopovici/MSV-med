from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QHBoxLayout, QLabel, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal

from app.di.container import Container
from app.services.notification_service import NotificationService


class ReportTitleManagementWidget(QWidget):
    titles_updated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._notification_service = NotificationService()

        # Editing state
        self._editing_title_id = None
        self._editing_mode = False

        self._setup_ui()
        self._load_titles()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side - Titles list
        left_widget = self._create_titles_list_section()
        splitter.addWidget(left_widget)

        # Right side - Title form
        right_widget = self._create_title_form_section()
        splitter.addWidget(right_widget)

        splitter.setSizes([600, 400])
        layout.addWidget(splitter)

    def _create_titles_list_section(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        section_title = QLabel("Titluri Rapoarte")
        section_title.setObjectName("SectionTitle")
        layout.addWidget(section_title)

        # Search layout
        search_layout = QHBoxLayout()

        self.title_search_input = QLineEdit()
        self.title_search_input.setPlaceholderText("Caută titluri...")
        self.title_search_input.setObjectName("SearchInput")
        self.title_search_input.textChanged.connect(self._filter_titles)

        self.clear_title_search_button = QPushButton("x")
        self.clear_title_search_button.setObjectName("ClearSearchButton")
        self.clear_title_search_button.setMaximumWidth(25)
        self.clear_title_search_button.setToolTip("Sterge cautarea")
        self.clear_title_search_button.clicked.connect(self._clear_title_search)
        self.clear_title_search_button.setVisible(False)

        search_layout.addWidget(self.title_search_input)
        search_layout.addWidget(self.clear_title_search_button)
        layout.addLayout(search_layout)

        # Results label
        self.title_results_label = QLabel()
        self.title_results_label.setVisible(False)
        self.title_results_label.setStyleSheet("color: #6b7280; font-size: 11px; padding: 2px;")
        layout.addWidget(self.title_results_label)

        # Titles table
        self.titles_table = QTableWidget()
        self.titles_table.setColumnCount(3)
        self.titles_table.setHorizontalHeaderLabels(["ID", "Titlu", "Data Creării"])
        self.titles_table.verticalHeader().setVisible(False)
        self.titles_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.titles_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.titles_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.titles_table.itemSelectionChanged.connect(self._on_title_selected)
        self.titles_table.itemDoubleClicked.connect(self._on_title_double_clicked)

        layout.addWidget(self.titles_table)

        # Title actions
        title_actions_layout = QHBoxLayout()

        self.refresh_titles_button = QPushButton("Refresh")
        self.refresh_titles_button.clicked.connect(self.refresh_data)

        self.edit_title_button = QPushButton("Modifica Titlu")
        self.edit_title_button.clicked.connect(self._edit_selected_title)
        self.edit_title_button.setEnabled(False)

        self.delete_title_button = QPushButton("Sterge Titlu")
        self.delete_title_button.clicked.connect(self._delete_title)
        self.delete_title_button.setEnabled(False)

        title_actions_layout.addWidget(self.refresh_titles_button)
        title_actions_layout.addWidget(self.edit_title_button)
        title_actions_layout.addWidget(self.delete_title_button)
        title_actions_layout.addStretch()

        layout.addLayout(title_actions_layout)

        return widget

    def _create_title_form_section(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Form group
        self.title_form_group = QGroupBox("Creeaza Titlu Raport")
        form_layout = QFormLayout(self.title_form_group)

        self.title_text_input = QLineEdit()
        self.title_text_input.setObjectName("UsernameInput")
        self.title_text_input.setPlaceholderText("ex: REZULTAT INVESTIGAȚIE MEDICALĂ")
        self.title_text_input.setMaxLength(255)
        self.title_text_input.editingFinished.connect(self._on_enter_pressed)

        form_layout.addRow("Titlu:", self.title_text_input)

        layout.addWidget(self.title_form_group)

        # Form buttons
        title_form_buttons_layout = QHBoxLayout()

        self.clear_title_button = QPushButton("Reset")
        self.clear_title_button.clicked.connect(self._clear_title_form)

        self.cancel_title_button = QPushButton("Anuleaza")
        self.cancel_title_button.setObjectName("CancelButton")
        self.cancel_title_button.clicked.connect(self._cancel_title_edit)
        self.cancel_title_button.setVisible(False)

        self.create_title_button = QPushButton("Creaza Titlu")
        self.create_title_button.setObjectName("CreateButton")
        self.create_title_button.clicked.connect(self._handle_create_or_update_title)

        title_form_buttons_layout.addWidget(self.clear_title_button)
        title_form_buttons_layout.addWidget(self.cancel_title_button)
        title_form_buttons_layout.addWidget(self.create_title_button)

        layout.addLayout(title_form_buttons_layout)

        return widget

    def _on_enter_pressed(self):
        print(f"Enter pressed! Input has focus: {self.title_text_input.hasFocus()}")
        print(f"Input text: '{self.title_text_input.text()}'")
        self._handle_create_or_update_title()

    def refresh_data(self):
        self._load_titles()

    def focus_search(self):
        self.title_search_input.setFocus()

    def clear_search_if_focused(self):
        if self.title_search_input.hasFocus():
            self._clear_title_search()

    def edit_selected(self):
        self._edit_selected_title()

    def _load_titles(self):
        try:
            report_title_service = Container.get_report_title_service()
            titles = report_title_service.get_all_titles()

            self.titles_table.setRowCount(len(titles))

            for row, title in enumerate(titles):
                self.titles_table.setItem(row, 0, QTableWidgetItem(str(title.id)))
                self.titles_table.setItem(row, 1, QTableWidgetItem(title.title_text))

                # Format date
                created_at = title.created_at.strftime("%d.%m.%Y %H:%M") if title.created_at else "N/A"
                self.titles_table.setItem(row, 2, QTableWidgetItem(created_at))

            # Adjust column widths
            header = self.titles_table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Title
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Date

            self._clear_title_search()

        except Exception as e:
            self._notification_service.show_error(self, "Eroare", f"Nu s-au putut incarca titlurile: {e}")

    def _filter_titles(self, text: str):
        self.clear_title_search_button.setVisible(bool(text.strip()))

        if not text.strip():
            self._show_all_titles()
            return

        visible_count = 0
        total_count = self.titles_table.rowCount()

        for row in range(total_count):
            title_item = self.titles_table.item(row, 1)  # Title column

            title_match = text.lower() in title_item.text().lower() if title_item else False

            if title_match:
                self.titles_table.setRowHidden(row, False)
                visible_count += 1
            else:
                self.titles_table.setRowHidden(row, True)

        if visible_count == 0:
            self.title_results_label.setText(f"Nu s-au găsit titluri pentru '{text}'")
            self.title_results_label.setStyleSheet("color: #dc2626; font-size: 11px; padding: 2px;")
        else:
            self.title_results_label.setText(f"Găsite {visible_count} din {total_count} titluri")
            self.title_results_label.setStyleSheet("color: #059669; font-size: 11px; padding: 2px;")

        self.title_results_label.setVisible(True)

    def _show_all_titles(self):
        for row in range(self.titles_table.rowCount()):
            self.titles_table.setRowHidden(row, False)
        self.title_results_label.setVisible(False)

    def _clear_title_search(self):
        self.title_search_input.clear()
        self.clear_title_search_button.setVisible(False)
        self._show_all_titles()

    def _on_title_selected(self):
        current_row = self.titles_table.currentRow()
        has_selection = current_row >= 0

        self.edit_title_button.setEnabled(has_selection)
        self.delete_title_button.setEnabled(has_selection)

    def _on_title_double_clicked(self, item):
        self._edit_selected_title()

    def _edit_selected_title(self):
        current_row = self.titles_table.currentRow()
        if current_row < 0:
            return

        title_id = int(self.titles_table.item(current_row, 0).text())

        try:
            report_title_service = Container.get_report_title_service()
            title = report_title_service.get_title_by_id(title_id)

            if not title:
                self._notification_service.show_error(self, "Eroare", "Titlul nu a fost gasit.")
                return

            # Fill form with title data
            self.title_text_input.setText(title.title_text)

            # Switch to edit mode
            self._editing_mode = True
            self._editing_title_id = title_id

            self.title_form_group.setTitle(f"Modifica Titlu: {title.title_text[:30]}...")
            self.create_title_button.setText("Actualizeaza Titlu")
            self.cancel_title_button.setVisible(True)

            self.title_text_input.setFocus()
            self.title_text_input.selectAll()

        except Exception as e:
            self._notification_service.show_error(self, "Eroare", f"Eroare la incarcarea datelor titlului: {e}")

    def _cancel_title_edit(self):
        self._editing_mode = False
        self._editing_title_id = None

        self.title_form_group.setTitle("Creeaza Titlu Raport")
        self.create_title_button.setText("Creaza Titlu")
        self.cancel_title_button.setVisible(False)

        self._clear_title_form()

    def _handle_create_or_update_title(self):
        if self._editing_mode:
            self._handle_update_title()
        else:
            self._handle_create_title()

    def _handle_create_title(self):
        title_text = self.title_text_input.text().strip()

        if not title_text:
            self._notification_service.show_warning(self, "Eroare validare", "Titlul nu poate fi gol.")
            self.title_text_input.setFocus()
            return

        if len(title_text) > 255:
            self._notification_service.show_warning(self, "Eroare validare",
                                                    "Titlul trebuie să aibă mai puțin de 255 caractere.")
            self.title_text_input.setFocus()
            return

        try:
            report_title_service = Container.get_report_title_service()
            report_title_service.create_title(title_text)

            self._clear_title_form()
            self._load_titles()
            self.titles_updated.emit()
            self.title_text_input.setFocus()

        except ValueError as e:
            self._notification_service.show_warning(self, "Eroare", str(e))
        except Exception as e:
            self._notification_service.show_error(self, "Eroare", f"Nu s-a putut crea titlul: {e}")

    def _handle_update_title(self):
        title_text = self.title_text_input.text().strip()

        if not title_text:
            self._notification_service.show_warning(self, "Eroare validare", "Titlul nu poate fi gol.")
            self.title_text_input.setFocus()
            return

        if len(title_text) > 255:
            self._notification_service.show_warning(self, "Eroare validare",
                                                    "Titlul trebuie să aibă mai puțin de 255 caractere.")
            self.title_text_input.setFocus()
            return

        try:
            report_title_service = Container.get_report_title_service()
            report_title_service.update_title(self._editing_title_id, title_text)

            self._cancel_title_edit()
            self._load_titles()
            self.titles_updated.emit()

        except ValueError as e:
            self._notification_service.show_warning(self, "Eroare", str(e))
        except Exception as e:
            self._notification_service.show_error(self, "Eroare", f"Nu s-a putut actualiza titlul: {e}")

    def _delete_title(self):
        current_row = self.titles_table.currentRow()
        if current_row >= 0:
            title_id = int(self.titles_table.item(current_row, 0).text())
            title_text = self.titles_table.item(current_row, 1).text()

            if self._notification_service.ask_confirmation(
                    self, "Confirm Delete", f"Esti sigur ca vrei sa stergi titlul '{title_text}'?"
            ):
                try:
                    report_title_service = Container.get_report_title_service()
                    report_title_service.delete_title(title_id)

                    # If editing this title, cancel edit mode
                    if self._editing_mode and self._editing_title_id == title_id:
                        self._cancel_title_edit()

                    self._load_titles()
                    self.titles_updated.emit()

                except ValueError as e:
                    self._notification_service.show_warning(self, "Eroare", str(e))
                except Exception as e:
                    self._notification_service.show_error(self, "Eroare", f"Nu s-a putut sterge titlul: {e}")

    def _clear_title_form(self):
        self.title_text_input.clear()

        if not self._editing_mode:
            self.title_text_input.setFocus()