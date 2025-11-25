import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QProgressBar, QListWidget, QListWidgetItem,
    QGroupBox, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from typing import List, Dict, Any

from app.services.notification_service import NotificationService


class LocalFileLoaderWorker(QObject):
    progress_updated = pyqtSignal(int, str)
    file_loaded = pyqtSignal(dict)
    folder_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, local_file_service, file_paths: List[str] = None, folder_path: str = None):
        super().__init__()
        self._local_file_service = local_file_service
        self._file_paths = file_paths or []
        self._folder_path = folder_path

    def run(self):
        try:
            if self._folder_path:
                self._load_folder()
            else:
                self._load_files()
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self.finished.emit()

    def _load_folder(self):
        self.progress_updated.emit(0, f"Scanning folder: {self._folder_path}")

        try:
            studies = self._local_file_service.load_dicom_folder(self._folder_path)
            self.folder_loaded.emit(studies)
            self.progress_updated.emit(100, f"Loaded {len(studies)} studies from folder")
        except Exception as e:
            self.error_occurred.emit(f"Error loading folder: {e}")

    def _load_files(self):
        total_files = len(self._file_paths)

        for i, file_path in enumerate(self._file_paths):
            try:
                progress = int((i / total_files) * 100)
                filename = os.path.basename(file_path)
                self.progress_updated.emit(progress, f"Loading: {filename}")

                file_data = self._local_file_service.load_dicom_file(file_path)
                self.file_loaded.emit(file_data)

            except Exception as e:
                self.error_occurred.emit(f"Error loading {file_path}: {e}")

        self.progress_updated.emit(100, f"Loaded {total_files} files")


class LocalFileManagerWidget(QWidget):
    studies_updated = pyqtSignal()

    def __init__(self, local_file_service, parent=None):
        super().__init__(parent)
        self._local_file_service = local_file_service
        self._notification_service = NotificationService()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header
        header_layout = QHBoxLayout()

        title_label = QLabel("Local DICOM Files")
        title_label.setObjectName("SectionTitle")

        header_layout.addWidget(title_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Load buttons
        buttons_layout = QHBoxLayout()

        self.load_files_button = QPushButton("Load DICOM Files")
        self.load_files_button.setObjectName("LoadFilesButton")
        self.load_files_button.clicked.connect(self._load_dicom_files)

        self.load_folder_button = QPushButton("Load DICOM Folder")
        self.load_folder_button.setObjectName("LoadFolderButton")
        self.load_folder_button.clicked.connect(self._load_dicom_folder)

        self.clear_button = QPushButton("Clear All")
        self.clear_button.setObjectName("ClearButton")
        self.clear_button.clicked.connect(self._clear_local_studies)

        buttons_layout.addWidget(self.load_files_button)
        buttons_layout.addWidget(self.load_folder_button)
        buttons_layout.addWidget(self.clear_button)
        buttons_layout.addStretch()

        layout.addLayout(buttons_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(20)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #6b7280; font-size: 11px; padding: 4px;")
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        # Local studies list (collapsible)
        self.studies_group = QGroupBox("Loaded Local Studies")
        self.studies_group.setCheckable(True)
        self.studies_group.setChecked(False)
        studies_layout = QVBoxLayout(self.studies_group)

        self.local_studies_list = QListWidget()
        self.local_studies_list.setMaximumHeight(150)
        self.local_studies_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.local_studies_list.customContextMenuRequested.connect(self._show_local_study_context_menu)
        studies_layout.addWidget(self.local_studies_list)

        layout.addWidget(self.studies_group)

        self._update_local_studies_display()

    def _load_dicom_files(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select DICOM Files",
            "",
            "DICOM Files (*.dcm *.dicom *.dic);;All Files (*)"
        )

        if file_paths:
            self._load_files_in_background(file_paths)

    def _load_dicom_folder(self):
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select DICOM Folder"
        )

        if folder_path:
            self._load_folder_in_background(folder_path)

    def _load_files_in_background(self, file_paths: List[str]):
        self._show_loading_state(True, f"Loading {len(file_paths)} files...")

        self.loader_thread = QThread()
        self.loader_worker = LocalFileLoaderWorker(
            self._local_file_service,
            file_paths=file_paths
        )
        self.loader_worker.moveToThread(self.loader_thread)

        # Connect signals
        self.loader_thread.started.connect(self.loader_worker.run)
        self.loader_worker.progress_updated.connect(self._update_loading_progress)
        self.loader_worker.file_loaded.connect(self._on_file_loaded)
        self.loader_worker.error_occurred.connect(self._on_loading_error)
        self.loader_worker.finished.connect(self._on_loading_finished)

        # Cleanup
        self.loader_worker.finished.connect(self.loader_thread.quit)
        self.loader_worker.finished.connect(self.loader_worker.deleteLater)
        self.loader_thread.finished.connect(self.loader_thread.deleteLater)

        self.loader_thread.start()

    def _load_folder_in_background(self, folder_path: str):
        self._show_loading_state(True, f"Scanning folder: {os.path.basename(folder_path)}")

        self.loader_thread = QThread()
        self.loader_worker = LocalFileLoaderWorker(
            self._local_file_service,
            folder_path=folder_path
        )
        self.loader_worker.moveToThread(self.loader_thread)

        # Connect signals
        self.loader_thread.started.connect(self.loader_worker.run)
        self.loader_worker.progress_updated.connect(self._update_loading_progress)
        self.loader_worker.folder_loaded.connect(self._on_folder_loaded)
        self.loader_worker.error_occurred.connect(self._on_loading_error)
        self.loader_worker.finished.connect(self._on_loading_finished)

        # Cleanup
        self.loader_worker.finished.connect(self.loader_thread.quit)
        self.loader_worker.finished.connect(self.loader_worker.deleteLater)
        self.loader_thread.finished.connect(self.loader_thread.deleteLater)

        self.loader_thread.start()

    def _show_loading_state(self, loading: bool, message: str = ""):
        self.progress_bar.setVisible(loading)
        self.status_label.setVisible(loading)
        if loading:
            self.progress_bar.setValue(0)
            self.status_label.setText(message)

        # Disable buttons during loading
        self.load_files_button.setEnabled(not loading)
        self.load_folder_button.setEnabled(not loading)
        self.clear_button.setEnabled(not loading)

    def _update_loading_progress(self, progress: int, message: str):
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)

    def _on_file_loaded(self, file_data: Dict[str, Any]):
        self._update_local_studies_display()

    def _on_folder_loaded(self, studies: List[Dict[str, Any]]):
        study_count = len(studies)
        total_files = sum(study.get("file_count", 0) for study in studies)

        message = f"Loaded {study_count} studies ({total_files} files) from folder"
        self._notification_service.show_info(self, "Folder Loaded", message)

        self._update_local_studies_display()

    def _on_loading_error(self, error_message: str):
        self._notification_service.show_error(self, "Loading Error", error_message)

    def _on_loading_finished(self):
        self._show_loading_state(False)
        self.studies_updated.emit()

    def _update_local_studies_display(self):
        self.local_studies_list.clear()

        try:
            local_studies = self._local_file_service.get_all_local_studies()

            # Update count label
            count = len(local_studies)

            # Update list
            for study_id in local_studies:
                try:
                    metadata = self._local_file_service.get_local_study_metadata(study_id)
                    instances = self._local_file_service.get_local_study_instances(study_id)

                    patient_name = metadata.get("Patient Name", "Unknown")
                    study_date = metadata.get("Study Date", "Unknown")
                    description = metadata.get("Description", "Local Study")
                    file_count = len(instances)

                    item_text = f"{patient_name} - {study_date}\n   {description} ({file_count} files)"

                    item = QListWidgetItem(item_text)
                    item.setData(Qt.ItemDataRole.UserRole, study_id)
                    item.setToolTip(f"Study ID: {study_id}\nFiles: {file_count}")

                    self.local_studies_list.addItem(item)

                except Exception as e:
                    print(f"Error displaying local study {study_id}: {e}")

            # Auto-expand if we have studies
            if count > 0 and not self.studies_group.isChecked():
                self.studies_group.setChecked(True)

        except Exception as e:
            print(f"Error updating local studies display: {e}")

    def _clear_local_studies(self):
        try:
            count = len(self._local_file_service.get_all_local_studies())
            if count == 0:
                self._notification_service.show_info(self, "Info", "No local studies to clear.")
                return

            if self._notification_service.ask_confirmation(
                    self,
                    "Clear Local Studies",
                    f"Are you sure you want to clear all {count} local studies?\n\n"
                    "This will only remove them from memory, not delete the original files."
            ):
                self._local_file_service.clear_local_studies()
                self._update_local_studies_display()
                self.studies_updated.emit()
                self._notification_service.show_info(self, "Cleared", "All local studies have been cleared.")

        except Exception as e:
            self._notification_service.show_error(self, "Error", f"Error clearing local studies: {e}")

    def _show_local_study_context_menu(self, position):
        item = self.local_studies_list.itemAt(position)
        if not item:
            return

        study_id = item.data(Qt.ItemDataRole.UserRole)

        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction

        menu = QMenu(self)

        view_action = QAction("View Details", self)
        view_action.triggered.connect(lambda: self._view_local_study_details(study_id))
        menu.addAction(view_action)

        # Remove action
        remove_action = QAction("Remove from List", self)
        remove_action.triggered.connect(lambda: self._remove_local_study(study_id))
        menu.addAction(remove_action)

        menu.exec(self.local_studies_list.mapToGlobal(position))

    def _view_local_study_details(self, study_id: str):
        try:
            metadata = self._local_file_service.get_local_study_metadata(study_id)
            instances = self._local_file_service.get_local_study_instances(study_id)
            examination_result = self._local_file_service.get_examination_result_from_local_study(study_id)

            # Create details dialog
            dialog = LocalStudyDetailsDialog(study_id, metadata, instances, examination_result, self)
            dialog.exec()

        except Exception as e:
            self._notification_service.show_error(self, "Error", f"Error viewing study details: {e}")

    def _remove_local_study(self, study_id: str):
        try:
            metadata = self._local_file_service.get_local_study_metadata(study_id)
            patient_name = metadata.get("Patient Name", "Unknown")

            if self._notification_service.ask_confirmation(
                    self,
                    "Remove Local Study",
                    f"Remove '{patient_name}' from the local studies list?\n\n"
                    "This will not delete the original files."
            ):
                success = self._local_file_service.remove_local_study(study_id)
                if success:
                    self._update_local_studies_display()
                    self.studies_updated.emit()
                    self._notification_service.show_info(self, "Removed", f"Study '{patient_name}' removed from list.")
                else:
                    self._notification_service.show_error(self, "Error", "Failed to remove study.")

        except Exception as e:
            self._notification_service.show_error(self, "Error", f"Error removing study: {e}")

    def refresh_display(self):
        self._update_local_studies_display()


class LocalStudyDetailsDialog(QMessageBox):

    def __init__(self, study_id: str, metadata: Dict[str, Any], instances: List[Dict[str, Any]],
                 examination_result: str, parent=None):
        super().__init__(parent)

        self.setWindowTitle(f"Local Study Details - {study_id}")
        self.setIcon(QMessageBox.Icon.Information)

        # Build details text
        details_text = "**Study Metadata:**\n"
        for key, value in metadata.items():
            details_text += f"• **{key}:** {value}\n"

        details_text += f"\n**Files ({len(instances)}):**\n"
        for i, instance in enumerate(instances, 1):
            file_path = instance.get("FilePath", "Unknown")
            filename = os.path.basename(file_path) if file_path else "Unknown"
            details_text += f"{i}. {filename}\n"

        if examination_result:
            details_text += f"\n**Examination Result:**\n{examination_result}"
        else:
            details_text += f"\n**Examination Result:** Not set"

        self.setText(details_text)

        # Make it resizable
        self.setDetailedText("")
        self.setStandardButtons(QMessageBox.StandardButton.Ok)


class LocalFileDropWidget(QFrame):
    files_dropped = pyqtSignal(list)  # List of file paths

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setLineWidth(2)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Drop icon and text
        drop_label = QLabel("\nDrag & Drop DICOM Files Here\n\nSupported formats: .dcm, .dicom, .dic")
        drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_label.setStyleSheet("""
            QLabel {
                color: #6b7280;
                font-size: 14px;
                padding: 40px;
                border: 2px dashed #cbd5e1;
                border-radius: 8px;
                background: #f8fafc;
            }
        """)

        layout.addWidget(drop_label)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            for url in urls:
                if url.isLocalFile():
                    event.acceptProposedAction()
                    self.setStyleSheet("QFrame { border: 2px solid #2563eb; background: #dbeafe; }")
                    return
        event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet("")  # Reset style

    def dropEvent(self, event):
        self.setStyleSheet("")  # Reset style

        file_paths = []
        urls = event.mimeData().urls()

        for url in urls:
            if url.isLocalFile():
                file_path = url.toLocalFile()
                if os.path.isfile(file_path):
                    file_paths.append(file_path)
                elif os.path.isdir(file_path):
                    for root, dirs, files in os.walk(file_path):
                        for file in files:
                            full_path = os.path.join(root, file)
                            file_paths.append(full_path)

        if file_paths:
            self.files_dropped.emit(file_paths)

        event.acceptProposedAction()