import re
import os
import subprocess
import sys
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QProgressBar,
    QScrollArea, QSizePolicy, QSplitter, QTabWidget, QFrame, QApplication, QFileDialog
)
from PyQt6.QtCore import QThread, Qt
from PyQt6.QtGui import QKeySequence, QShortcut

from app.presentation.controllers.auth_controller import AuthController
from app.presentation.controllers.hybrid_pacs_controller import HybridPacsController, StudiesWorker, QueueSenderWorker
from app.presentation.views.base_view import CenteredView
from app.presentation.widgets.study_list_widget import SearchableStudyListWidget, StudyQueueWidget
from app.presentation.widgets.metadata_widget import MetadataWidget, ResultWidget
from app.presentation.widgets.local_file_widgets import LocalFileManagerWidget, LocalFileDropWidget
from app.services.notification_service import NotificationService
from app.presentation.styles.style_manager import load_style
from app.config.settings import Settings


class EnhancedPacsView(CenteredView):
    def __init__(self, pacs_controller: HybridPacsController, auth_controller: AuthController):
        super().__init__()
        self._pacs_controller = pacs_controller
        self._auth_controller = auth_controller
        self._notification_service = NotificationService()
        self._settings = Settings()
        self.last_generated_pdf_path = None
        self.setWindowTitle("Enhanced PACS Viewer")
        self.setGeometry(100, 100, 1800, 900)
        self._setup_ui()
        self._setup_shortcuts()
        load_style(self)
        self._load_studies()
        self._last_save_directory = None

    def _setup_ui(self):
        # Main layout with tabs
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # Header with statistics
        header_layout = QHBoxLayout()

        title_label = QLabel("PACS Viewer")
        title_label.setObjectName("SectionTitle")

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setMaximumWidth(100)
        self.refresh_button.setFixedHeight(30)
        self.refresh_button.clicked.connect(self._load_studies)

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.refresh_button)

        main_layout.addLayout(header_layout)

        # Create tab widget
        self.tab_widget = QTabWidget()
        # self.tab_widget.setObjectName("StudiesTab")
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)

        # Studies tab (main functionality)
        self.studies_tab = self._create_studies_tab()
        self.tab_widget.addTab(self.studies_tab, "Studies")

        # Local files management tab
        self.local_files_tab = self._create_local_files_tab()
        self.tab_widget.addTab(self.local_files_tab, "Local Files")

        main_layout.addWidget(self.tab_widget)

        # Progress bar (shared across tabs)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(20)
        main_layout.addWidget(self.progress_bar)

        # Shortcuts info
        shortcuts_label = QLabel(
            "💡 Ctrl+F (Search) • F5 (Refresh) • Ctrl+Q (Add to Queue) • Ctrl+G (Generate PDF) • Ctrl+P (Preview)")
        shortcuts_label.setStyleSheet("color: #6b7280; font-size: 10px; font-style: italic; padding: 4px;")
        shortcuts_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        shortcuts_label.setMaximumHeight(20)
        main_layout.addWidget(shortcuts_label)

    def _create_studies_tab(self):
        tab_widget = QWidget()

        # Scrollable container
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_container = QWidget()
        scroll_layout = QVBoxLayout(scroll_container)
        scroll_layout.setSpacing(8)
        scroll_layout.setContentsMargins(8, 8, 8, 8)

        # Study list section
        studies_label = QLabel("All Studies")
        studies_label.setObjectName("SectionTitle")
        scroll_layout.addWidget(studies_label)

        self.study_list = SearchableStudyListWidget()
        self.study_list.study_selected.connect(self._on_study_selected)
        self.study_list.setMinimumHeight(400)
        self.study_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        scroll_layout.addWidget(self.study_list)

        # Horizontal splitter for metadata and queue
        h_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side - Metadata
        metadata_widget = QWidget()
        metadata_layout = QVBoxLayout(metadata_widget)

        metadata_label = QLabel("Study Metadata")
        metadata_label.setObjectName("SectionTitle")
        metadata_layout.addWidget(metadata_label)

        self.metadata_widget = MetadataWidget()
        self.metadata_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        metadata_layout.addWidget(self.metadata_widget)

        # Right side - Queue
        queue_widget = QWidget()
        queue_layout = QVBoxLayout(queue_widget)

        queue_label = QLabel("Processing Queue")
        queue_label.setObjectName("SectionTitle")
        queue_layout.addWidget(queue_label)

        self.queue_widget = StudyQueueWidget()
        self.queue_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        queue_layout.addWidget(self.queue_widget)

        # Queue buttons
        queue_buttons_layout = QHBoxLayout()

        self.add_to_queue_button = QPushButton("➕ Add to Queue")
        self.add_to_queue_button.setObjectName("QueueButton")
        self.add_to_queue_button.clicked.connect(self._add_study_to_queue)

        self.send_queue_button = QPushButton("Send to PACS")
        self.send_queue_button.setObjectName("SendPACSButton")
        self.send_queue_button.clicked.connect(self._send_queue_to_pacs)

        queue_buttons_layout.addWidget(self.add_to_queue_button)
        queue_buttons_layout.addWidget(self.send_queue_button)
        queue_buttons_layout.addStretch()

        queue_layout.addLayout(queue_buttons_layout)

        h_splitter.addWidget(metadata_widget)
        h_splitter.addWidget(queue_widget)
        h_splitter.setSizes([400, 400])

        scroll_layout.addWidget(h_splitter)

        # Results section
        results_label = QLabel("Examination Results")
        results_label.setObjectName("SectionTitle")
        scroll_layout.addWidget(results_label)

        self.result_widget = ResultWidget()
        self.result_widget.setMinimumHeight(400)
        self.result_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        scroll_layout.addWidget(self.result_widget)

        # PDF action buttons
        pdf_buttons_layout = QHBoxLayout()

        self.preview_button = QPushButton("Preview PDF")
        self.preview_button.setObjectName("PreviewButton")
        self.preview_button.clicked.connect(self._preview_pdf)

        self.generate_pdf_button = QPushButton("Generate PDF")
        self.generate_pdf_button.setObjectName("GeneratePDFButton")
        self.generate_pdf_button.clicked.connect(self._export_pdf)

        self.print_button = QPushButton("Print")
        self.print_button.setObjectName("PrintButton")
        self.print_button.clicked.connect(self._print_pdf)

        pdf_buttons_layout.addStretch()
        pdf_buttons_layout.addWidget(self.preview_button)
        pdf_buttons_layout.addWidget(self.generate_pdf_button)
        pdf_buttons_layout.addWidget(self.print_button)

        scroll_layout.addLayout(pdf_buttons_layout)
        scroll_layout.addStretch()

        scroll_area.setWidget(scroll_container)

        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.addWidget(scroll_area)

        return tab_widget

    def _create_local_files_tab(self):
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setSpacing(12)
        tab_layout.setContentsMargins(12, 12, 12, 12)

        # Get local file service from pacs controller
        local_file_service = None
        if hasattr(self._pacs_controller._pacs_service, '_local_file_service'):
            local_file_service = self._pacs_controller._pacs_service._local_file_service

        if local_file_service:
            # Local file manager
            self.local_file_manager = LocalFileManagerWidget(local_file_service)
            self.local_file_manager.studies_updated.connect(self._on_local_studies_updated)
            tab_layout.addWidget(self.local_file_manager)

            # Drag and drop area
            drop_label = QLabel("Drag and Drop:")
            drop_label.setObjectName("SectionTitle")
            tab_layout.addWidget(drop_label)

            self.drop_widget = LocalFileDropWidget()
            self.drop_widget.setStyleSheet("min-width:1500;")
            self.drop_widget.files_dropped.connect(self._handle_dropped_files)
            self.drop_widget.setMaximumHeight(120)
            tab_layout.addWidget(self.drop_widget)

        tab_layout.addStretch()
        return tab_widget

    def _setup_shortcuts(self):
        # Ctrl+F to focus search
        search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        search_shortcut.activated.connect(self.study_list.focus_search)

        # Escape to clear search
        clear_shortcut = QShortcut(QKeySequence("Escape"), self)
        clear_shortcut.activated.connect(self._clear_search_if_focused)

        # F5 to refresh
        refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        refresh_shortcut.activated.connect(self._load_studies)

        # Ctrl+Q to add to queue
        queue_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        queue_shortcut.activated.connect(self._add_study_to_queue)

        # Ctrl+G to generate PDF
        generate_shortcut = QShortcut(QKeySequence("Ctrl+G"), self)
        generate_shortcut.activated.connect(self._export_pdf)

        # Ctrl+P to preview
        preview_shortcut = QShortcut(QKeySequence("Ctrl+P"), self)
        preview_shortcut.activated.connect(self._preview_pdf)

    def _clear_search_if_focused(self):
        if hasattr(self.study_list, 'search_input') and self.study_list.search_input.hasFocus():
            self.study_list._clear_search()

    def _load_studies(self):
        self.study_list.set_loading(True)
        self.refresh_button.setEnabled(False)
        self.refresh_button.setText("⏳ Loading...")

        self.study_thread = QThread()
        self.worker = StudiesWorker(self._pacs_controller)
        self.worker.moveToThread(self.study_thread)

        self.study_thread.started.connect(self.worker.run)
        self.worker.studies_loaded.connect(self._on_studies_loaded)
        self.worker.error_occurred.connect(self._on_studies_error)

        self.worker.studies_loaded.connect(self.study_thread.quit)
        self.worker.studies_loaded.connect(self.worker.deleteLater)
        self.worker.error_occurred.connect(self.study_thread.quit)
        self.worker.error_occurred.connect(self.worker.deleteLater)
        self.study_thread.finished.connect(self.study_thread.deleteLater)

        self.study_thread.start()

    def _on_studies_loaded(self, study_ids):
        self.study_list.clear_studies()
        self.study_list.set_loading(False)
        self.refresh_button.setEnabled(True)
        self.refresh_button.setText("Refresh")

        pacs_count = 0
        local_count = 0

        for study_id in study_ids:
            try:
                metadata = self._pacs_controller.get_study_metadata(study_id)

                # Count study types
                if study_id.startswith("local_"):
                    local_count += 1
                    display_text = f"[LOCAL]{metadata['Patient Name']} - {metadata['Study Date']} - {metadata['Description']}"
                else:
                    pacs_count += 1
                    display_text = f"{metadata['Patient Name']} - {metadata['Study Date']} - {metadata['Description']}"

                self.study_list.add_study(study_id, display_text)

            except Exception as e:
                print(f"Error loading metadata for study {study_id}: {e}")

    def _on_studies_error(self, error_message):
        self.study_list.set_loading(False)
        self.refresh_button.setEnabled(True)
        self.refresh_button.setText("Refresh")
        self._notification_service.show_error(self, "Error", f"Error loading studies:\n{error_message}")

    def _on_study_selected(self, study_id: str):
        try:
            metadata = self._pacs_controller.get_study_metadata(study_id)
            self.metadata_widget.display_metadata(metadata)

            self.result_widget.update_from_metadata(metadata)

            # Load examination result if available
            examination_result = self._pacs_controller.get_examination_result_from_study(study_id)
            if examination_result:
                self.result_widget.set_result_text(examination_result)
            else:
                self.result_widget.clear_result()

        except Exception as e:
            self._notification_service.show_error(self, "Error", f"Error loading study data:\n{e}")

    def _on_local_studies_updated(self):
        self._load_studies()

    def _handle_dropped_files(self, file_paths: list):
        if hasattr(self._pacs_controller._pacs_service, '_local_file_service'):
            local_file_service = self._pacs_controller._pacs_service._local_file_service

            # Filter DICOM files
            dicom_files = []
            for file_path in file_paths:
                if local_file_service._is_dicom_file(file_path):
                    dicom_files.append(file_path)

            if dicom_files:
                self._notification_service.show_info(
                    self,
                    "Files Dropped",
                    f"Loading {len(dicom_files)} DICOM files..."
                )

                # Switch to local files tab to show progress
                self.tab_widget.setCurrentIndex(1)

                # Trigger loading through local file manager
                if hasattr(self, 'local_file_manager'):
                    self.local_file_manager._load_files_in_background(dicom_files)
            else:
                self._notification_service.show_warning(
                    self,
                    "No DICOM Files",
                    "No valid DICOM files found in the dropped files."
                )

    def _export_pdf(self):
        study_id = self.study_list.get_selected_study_id()
        if not study_id:
            self._notification_service.show_warning(self, "Warning", "Please select a study.")
            return

        result_text = self.result_widget.get_result_text()
        if not result_text:
            self._notification_service.show_warning(self, "Warning", "Please enter examination results.")
            return

        try:
            metadata = self._pacs_controller.get_study_metadata(study_id)
            patient_name = re.sub(r'\W+', '_', metadata["Patient Name"])
            study_date = metadata["Study Date"].replace("-", "")
            timestamp = datetime.now().strftime("%H%M%S")
            default_filename = f"{patient_name}_{study_date}_{timestamp}.pdf"
        except:
            default_filename = f"medical_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        if self._last_save_directory and os.path.exists(self._last_save_directory):
            start_directory = os.path.join(self._last_save_directory, default_filename)
        else:
            settings = Settings()
            default_save_dir = settings.PDF_OUTPUT_DIR
            os.makedirs(default_save_dir, exist_ok=True)
            start_directory = os.path.join(default_save_dir, default_filename)

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvează raportul PDF",
            start_directory,
            "PDF Files (*.pdf);;All Files (*)"
        )

        if not file_path:
            return

        if not file_path.lower().endswith('.pdf'):
            file_path += '.pdf'

        self._last_save_directory = os.path.dirname(file_path)

        current_user = self._auth_controller.get_current_user() if self._auth_controller else None
        selected_title = self.result_widget.get_selected_title()

        settings = Settings()
        header_image_path = settings.HEADER_IMAGE_PATH

        success = self._pacs_controller.export_pdf(
            study_id, result_text, self, current_user, selected_title, 
            header_image_path, custom_path=file_path
        )
        
        if success:
            self.last_generated_pdf_path = file_path

    def _preview_pdf(self):
        study_id = self.study_list.get_selected_study_id()
        if not study_id:
            self._notification_service.show_warning(self, "Warning", "Please select a study.")
            return

        result_text = self.result_widget.get_result_text_html()
        current_user = self._auth_controller.get_current_user() if self._auth_controller else None
        selected_title = self.result_widget.get_selected_title()
        settings = Settings()
        header_image_path = settings.HEADER_IMAGE_PATH

        self._pacs_controller.preview_pdf(study_id, result_text, self, current_user, selected_title, header_image_path)

    def _print_pdf(self):
        if not self.last_generated_pdf_path or not os.path.exists(self.last_generated_pdf_path):
            self._notification_service.show_warning(self, "Warning", "No PDF to print. Generate a PDF first.")
            return

        try:
            if sys.platform.startswith("linux"):
                subprocess.run(["lp", self.last_generated_pdf_path])
            elif sys.platform == "win32":
                os.startfile(self.last_generated_pdf_path, "print")
            else:
                self._notification_service.show_info(self, "Info", "Printing not supported on this platform")
        except Exception as e:
            self._notification_service.show_error(self, "Error", f"Error printing PDF: {e}")

    def _add_study_to_queue(self):
        study_id = self.study_list.get_selected_study_id()
        if not study_id:
            self._notification_service.show_warning(self, "Atenție", "Selectează un studiu pentru a-l adăuga în queue.")
            return

        if self.queue_widget.is_study_in_queue(study_id):
            self._notification_service.show_warning(
                self,
                "Studiu deja în coada",
                "Acest studiu este deja în queue pentru trimitere."
            )
            return

        # Validate study
        is_valid, metadata = self._pacs_controller.validate_study_for_queue(study_id, self)
        if not is_valid:
            return

        # Get examination result
        examination_result = self.result_widget.get_result_text()

        if not examination_result.strip():
            proceed = self._notification_service.ask_confirmation(
                self,
                "Rezultat lipsă",
                "Nu există rezultat al explorării introdus.\n\n"
                "Vrei să adaugi studiul în queue fără rezultat?"
            )
            if not proceed:
                return

        # Add to queue
        patient_name = metadata.get("Patient Name", "Unknown")
        study_date = metadata.get("Study Date", "Unknown")
        description = metadata.get("Description", "Unknown")
        study_type = "LOCAL" if study_id.startswith("local_") else "PACS"
        display_text = f"[{study_type}] {patient_name} - {study_date} - {description}"

        success = self.queue_widget.add_study_to_queue(
            study_id,
            display_text,
            examination_result,
            patient_name,
            study_date,
            description
        )

        if success:
            message = f"Studiul '{patient_name}' ({study_type}) a fost adăugat în queue."
            if examination_result.strip():
                message += f"\nRezultatul explorării ({len(examination_result)} caractere) a fost atașat."
            else:
                message += "\nStudiul a fost adăugat fără rezultat al explorării."

            self._notification_service.show_info(self, "Studiu adăugat", message)

    def _send_queue_to_pacs(self):
        queued_studies = self.queue_widget.get_queued_studies()

        if not queued_studies:
            self._notification_service.show_warning(self, "Queue gol", "Nu sunt studii în queue pentru trimitere.")
            return

        self._show_sending_progress(queued_studies)

    def _show_sending_progress(self, queued_studies):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.send_queue_button.setEnabled(False)
        self.send_queue_button.setText("⏳ Trimitere...")

        self.sender_thread = QThread()
        self.sender_worker = QueueSenderWorker(
            self._pacs_controller,
            queued_studies
        )
        self.sender_worker.moveToThread(self.sender_thread)

        # Connect signals
        self.sender_thread.started.connect(self.sender_worker.run)
        self.sender_worker.progress_updated.connect(self._update_sending_progress)
        self.sender_worker.sending_completed.connect(self._on_sending_completed)

        # Cleanup
        self.sender_worker.sending_completed.connect(self.sender_thread.quit)
        self.sender_worker.sending_completed.connect(self.sender_worker.deleteLater)
        self.sender_thread.finished.connect(self.sender_thread.deleteLater)

        self.sender_thread.start()

    def _update_sending_progress(self, progress: int, current_study: str):
        self.progress_bar.setValue(progress)
        if progress < 100:
            self.send_queue_button.setText(f"⏳ Trimitere... {current_study}")

    def _on_sending_completed(self, success: bool, message: str):
        self.progress_bar.setVisible(False)
        self.send_queue_button.setEnabled(True)
        self.send_queue_button.setText("🚀 Send Queue to PACS")

        if success:
            # Clear queue on success
            self.queue_widget.clear_queue()
            self._notification_service.show_info(self, "Trimitere finalizată", message)
        else:
            self._notification_service.show_error(self, "Eroare trimitere", message)

    def refresh_all(self):
        self._load_studies()
        if hasattr(self, 'local_file_manager'):
            self.local_file_manager.refresh_display()
