from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QSizePolicy, QScrollArea
)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QIcon
from typing import Dict, List, Tuple, NamedTuple

class QueuedStudy(NamedTuple):
    study_id: str
    display_text: str
    examination_result: str
    patient_name: str
    study_date: str
    description: str

class SearchableStudyListWidget(QWidget):
    study_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_studies: List[Tuple[str, str]] = []
        self.filtered_studies: Dict[str, str] = {}

        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(0, 0, 0, 0)

        # Search
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("Caută studii...")
        self.search_input.textChanged.connect(self._on_search_text_changed)
        self.search_input.returnPressed.connect(self._perform_search)

        self.clear_button = QPushButton("x")
        self.clear_button.setObjectName("ClearSearchButton")
        self.clear_button.setMaximumWidth(30)
        self.clear_button.clicked.connect(self._clear_search)
        self.clear_button.setVisible(False)

        search_container = QWidget()
        search_container.setObjectName("SearchContainer")
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(4)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.clear_button)
        layout.addWidget(search_container)

        # Results label
        self.results_label = QLabel()
        self.results_label.setVisible(False)
        self.results_label.setMaximumHeight(0)
        layout.addWidget(self.results_label)

        # Study list
        self.study_list = QListWidget()
        self.study_list.setObjectName("StudyList")
        self.study_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.study_list.itemClicked.connect(self._on_item_clicked)
        self.study_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout.addWidget(self.study_list)

    def _on_search_text_changed(self, text: str):
        self.clear_button.setVisible(bool(text.strip()))

        self.search_timer.stop()
        if text.strip():
            self.search_timer.start(300)  # 300ms delay
        else:
            self._clear_search()

    def _perform_search(self):
        search_text = self.search_input.text().strip().lower()

        if not search_text:
            self._show_all_studies()
            return

        # Filter studies based on search text
        filtered = []
        for study_id, display_text in self.all_studies:
            if search_text in display_text.lower():
                filtered.append((study_id, display_text))

        self._display_filtered_studies(filtered, search_text)

    def _display_filtered_studies(self, filtered_studies: List[Tuple[str, str]], search_text: str):
        self.study_list.clear()
        self.filtered_studies.clear()

        for study_id, display_text in filtered_studies:
            self.filtered_studies[display_text] = study_id

            highlighted_text = self._highlight_search_terms(display_text, search_text)
            item = QListWidgetItem(highlighted_text)
            item.setData(Qt.ItemDataRole.UserRole, study_id)
            self.study_list.addItem(item)

        # Update results info
        total_studies = len(self.all_studies)
        found_studies = len(filtered_studies)

        if found_studies == 0:
            self.results_label.setText(f"Nu s-au gasit studii pentru '{search_text}'")
            self.results_label.setStyleSheet("color: #dc2626; font-weight: 500;")
        else:
            self.results_label.setText(f"Gasite {found_studies} din {total_studies} studii")
            self.results_label.setStyleSheet("color: #059669; font-weight: 500;")

        self.results_label.setVisible(True)

    def _highlight_search_terms(self, text: str, search_term: str) -> str:
        return text

    def _show_all_studies(self):
        self.study_list.clear()
        self.filtered_studies.clear()

        for study_id, display_text in self.all_studies:
            self.filtered_studies[display_text] = study_id
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, study_id)
            self.study_list.addItem(item)

        self.results_label.setVisible(False)

    def _clear_search(self):
        self.search_input.clear()
        self.clear_button.setVisible(False)
        self._show_all_studies()

    def add_study(self, study_id: str, display_text: str):
        self.all_studies.append((study_id, display_text))

        if not self.search_input.text().strip():
            self.filtered_studies[display_text] = study_id
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, study_id)
            self.study_list.addItem(item)

    def clear_studies(self):
        self.all_studies.clear()
        self.study_list.clear()
        self.filtered_studies.clear()
        self.search_input.clear()
        self.clear_button.setVisible(False)
        self.results_label.setVisible(False)

    def set_loading(self, is_loading: bool):
        if is_loading:
            self.clear_studies()
            self.study_list.addItem("Se încarcă studiile...")
            self.search_input.setEnabled(False)
        else:
            # Remove loading item if it exists
            for i in range(self.study_list.count()):
                item = self.study_list.item(i)
                if item and item.text() == "Se încarcă studiile...":
                    self.study_list.takeItem(i)
                    break
            self.search_input.setEnabled(True)

    def get_selected_study_id(self) -> str:
        current_item = self.study_list.currentItem()
        if current_item:
            # Try to get from UserRole data first
            study_id = current_item.data(Qt.ItemDataRole.UserRole)
            if study_id:
                return study_id

            # Fallback to text-based lookup
            if current_item.text() in self.filtered_studies:
                return self.filtered_studies[current_item.text()]
        return ""

    def _on_item_clicked(self, item: QListWidgetItem):
        study_id = item.data(Qt.ItemDataRole.UserRole)
        if study_id:
            self.study_selected.emit(study_id)
        else:
            # Fallback for text-based lookup
            if item.text() in self.filtered_studies:
                study_id = self.filtered_studies[item.text()]
                self.study_selected.emit(study_id)

    def focus_search(self):
        self.search_input.setFocus()

    def get_search_text(self) -> str:
        return self.search_input.text().strip()

    def set_search_text(self, text: str):
        self.search_input.setText(text)


class StudyQueueWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.queued_studies: List[QueuedStudy] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        header_layout = QHBoxLayout()

        self.queue_count_label = QLabel("(0 studii)")
        self.queue_count_label.setStyleSheet("color: #6b7280; font-size: 12px;")

        self.clear_queue_button = QPushButton("Clear")
        self.clear_queue_button.setObjectName("ClearSearchButton")
        self.clear_queue_button.setMaximumWidth(60)
        self.clear_queue_button.setMaximumHeight(25)
        self.clear_queue_button.clicked.connect(self.clear_queue)

        header_layout.addWidget(self.queue_count_label)
        header_layout.addStretch()
        header_layout.addWidget(self.clear_queue_button)

        layout.addLayout(header_layout)

        # Queue list
        self.queue_list = QListWidget()
        self.queue_list.setObjectName("QueueList")
        self.queue_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.queue_list.setMaximumHeight(120)
        self.queue_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Context menu for queue items
        self.queue_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.queue_list.customContextMenuRequested.connect(self._show_queue_context_menu)

        layout.addWidget(self.queue_list)

    def add_study_to_queue(self, study_id: str, display_text: str, examination_result: str,
                           patient_name: str, study_date: str, description: str) -> bool:

        # Check if study is already in queue
        for queued_study in self.queued_studies:
            if queued_study.study_id == study_id:
                return False

        # Create queued study object
        queued_study = QueuedStudy(
            study_id=study_id,
            display_text=display_text,
            examination_result=examination_result,
            patient_name=patient_name,
            study_date=study_date,
            description=description
        )

        # Add to internal list
        self.queued_studies.append(queued_study)

        # Add to visual list
        result_preview = examination_result[:50] + "..." if len(examination_result) > 50 else examination_result
        item_text = f"{display_text}\n📝 {result_preview}" if examination_result else f"{display_text}\n📝 (fără rezultat)"

        item = QListWidgetItem(item_text)
        item.setData(Qt.ItemDataRole.UserRole, study_id)
        item.setToolTip(f"Studiu: {display_text}\nRezultat: {examination_result}")
        self.queue_list.addItem(item)

        self._update_queue_count()
        return True

    def remove_study_from_queue(self, study_id: str) -> bool:
        # Remove from internal list
        self.queued_studies = [qs for qs in self.queued_studies if qs.study_id != study_id]

        # Remove from visual list
        for i in range(self.queue_list.count()):
            item = self.queue_list.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == study_id:
                self.queue_list.takeItem(i)
                break

        self._update_queue_count()
        return True

    def get_queued_studies(self) -> List[QueuedStudy]:
        return self.queued_studies.copy()

    def clear_queue(self):
        self.queued_studies.clear()
        self.queue_list.clear()
        self._update_queue_count()

    def is_study_in_queue(self, study_id: str) -> bool:
        return any(qs.study_id == study_id for qs in self.queued_studies)

    def get_queue_count(self) -> int:
        return len(self.queued_studies)

    def _update_queue_count(self):
        count = len(self.queued_studies)
        self.queue_count_label.setText(f"({count} studii)" if count != 1 else "(1 studiu)")

    def _show_queue_context_menu(self, position):
        item = self.queue_list.itemAt(position)
        if item:
            from PyQt6.QtWidgets import QMenu
            from PyQt6.QtGui import QAction

            menu = QMenu(self)

            remove_action = QAction("Elimină din queue", self)
            remove_action.triggered.connect(lambda: self._remove_selected_item())
            menu.addAction(remove_action)

            view_result_action = QAction("Vezi rezultatul", self)
            view_result_action.triggered.connect(lambda: self._view_result_for_item(item))
            menu.addAction(view_result_action)

            menu.exec(self.queue_list.mapToGlobal(position))

    def _remove_selected_item(self):
        current_item = self.queue_list.currentItem()
        if current_item:
            study_id = current_item.data(Qt.ItemDataRole.UserRole)
            self.remove_study_from_queue(study_id)

    def _view_result_for_item(self, item):
        study_id = item.data(Qt.ItemDataRole.UserRole)
        queued_study = next((qs for qs in self.queued_studies if qs.study_id == study_id), None)

        if queued_study:
            from PyQt6.QtWidgets import QMessageBox, QTextEdit, QVBoxLayout, QDialog

            dialog = QDialog(self)
            dialog.setWindowTitle(f"Rezultat explorare - {queued_study.patient_name}")
            dialog.setModal(True)
            dialog.resize(500, 300)

            layout = QVBoxLayout(dialog)

            result_text = QTextEdit()
            result_text.setPlainText(queued_study.examination_result)
            result_text.setReadOnly(True)
            layout.addWidget(result_text)

            dialog.exec()