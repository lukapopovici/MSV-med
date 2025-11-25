import re
from datetime import datetime
from PyQt6.QtWidgets import QTextEdit, QWidget, QVBoxLayout, QToolBar, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox
from PyQt6.QtGui import QAction, QFont, QTextCharFormat
from typing import Dict, Any
from app.utils.formatters import Formatters
from app.services.notification_service import NotificationService


class MetadataWidget(QTextEdit):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setObjectName("MetadataWidget")

    def display_metadata(self, metadata: Dict[str, Any]):
        formatted_text = Formatters.format_metadata_display(metadata)
        self.setPlainText(formatted_text)

    def clear_metadata(self):
        self.clear()


class ResultWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ResultWidget")
        self._setup_ui()
        self._load_titles()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("Title:"))
        
        self.title_combo = QComboBox()
        self.title_combo.setMinimumHeight(300)
        title_layout.addWidget(self.title_combo)

        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        indication_layout = QHBoxLayout()

        indication_layout.addWidget(QLabel("Age:"))

        self.age_input = QLineEdit()
        self.age_input.setMaximumWidth(75)
        indication_layout.addWidget(self.age_input)

        indication_layout.addWidget(QLabel("Dignosis:"))
        self.diagnosis_input = QLineEdit()
        self.diagnosis_input.setMinimumWidth(300)
        indication_layout.addWidget(self.diagnosis_input)

        self.generate_button = QPushButton("Generate Text")
        self.generate_button.setMaximumWidth(30)
        self.generate_button.setToolTip("Generate Text")
        self.generate_button.clicked.connect(self._generate_text)
        indication_layout.addWidget(self.generate_button)

        indication_layout.addStretch()
        layout.addLayout(indication_layout)

        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        
        self._create_format_actions()
        
        layout.addWidget(self.toolbar)
        
        # Text editor
        self.text_edit = QTextEdit()
        self.text_edit.setAcceptRichText(True)
        self.text_edit.setPlaceholderText("Rezultatul explorării...")
        self.text_edit.currentCharFormatChanged.connect(self._update_toolbar)
        
        layout.addWidget(self.text_edit)

    def update_from_metadata(self, metadata: Dict[str, Any]):
        try:
            patient_age = metadata.get("Patient Age", "")

            if patient_age and patient_age != "N/A":
                age_number = self._extract_age_number(patient_age)
                print(age_number)
                if age_number:
                    self.age_input.setText(str(age_number))
                    print(f"Auto-loaded age from DICOM: {age_number}")
                else:
                    self.age_input.clear()
            else:
                birth_date = metadata.get("Patient Birth Date", "")
                clean_date = birth_date.replace("-", "")
                if clean_date and clean_date != "N/A":
                    calculated_age = self._calculate_age_from_birth_date(clean_date)
                    if calculated_age:
                        self.age_input.setText(str(calculated_age))
                        print(f"Calculated age from birth date: {calculated_age}")
                    else:
                        self.age_input.clear()
                else:
                    self.age_input.clear()

        except Exception as e:
            print(f"Error updating fields from metadata: {e}")
            self.age_input.clear()

    def _extract_age_number(self, age_string: str) -> int:
        try:
            numbers = re.findall(r'\d+', age_string)
            if numbers:
                age = int(numbers[0])
                if 0 <= age <= 150:
                    return age
            return None
        except (ValueError, TypeError):
            return None

    def _calculate_age_from_birth_date(self, birth_date: str) -> int:
        try:
            if len(birth_date) == 8 and birth_date.isdigit():
                year = int(birth_date[:4])
                month = int(birth_date[4:6])
                day = int(birth_date[6:8])

                birth_datetime = datetime(year, month, day)
                today = datetime.now()

                age = today.year - birth_datetime.year

                if today.month < birth_datetime.month or \
                        (today.month == birth_datetime.month and today.day < birth_datetime.day):
                    age -= 1

                if 0 <= age <= 150:
                    return age
            return None
        except (ValueError, TypeError):
            return None

    def _create_format_actions(self):
        # Bold
        self.bold_action = QAction("Bold", self)
        self.bold_action.setShortcut("Ctrl+B")
        self.bold_action.setCheckable(True)
        self.bold_action.triggered.connect(lambda: self.text_edit.setFontWeight(
            QFont.Weight.Bold if self.bold_action.isChecked() else QFont.Weight.Normal))
        self.toolbar.addAction(self.bold_action)
        
        # Italic
        self.italic_action = QAction("Italic", self)
        self.italic_action.setShortcut("Ctrl+I") 
        self.italic_action.setCheckable(True)
        self.italic_action.triggered.connect(lambda: self.text_edit.setFontItalic(self.italic_action.isChecked()))
        self.toolbar.addAction(self.italic_action)
        
        # Underline
        self.underline_action = QAction("Underline", self)
        self.underline_action.setShortcut("Ctrl+U")
        self.underline_action.setCheckable(True) 
        self.underline_action.triggered.connect(lambda: self.text_edit.setFontUnderline(self.underline_action.isChecked()))
        self.toolbar.addAction(self.underline_action)

    def _update_toolbar(self, fmt):
        self.bold_action.setChecked(fmt.fontWeight() == QFont.Weight.Bold)
        self.italic_action.setChecked(fmt.fontItalic())
        self.underline_action.setChecked(fmt.fontUnderline())

    def _load_titles(self):
        try:
            from app.di.container import Container
            report_title_service = Container.get_report_title_service()

            self.title_combo.clear()
            title_texts = report_title_service.get_all_title_texts()
            self.title_combo.addItems(title_texts)

            default_title = report_title_service.get_default_title()
            index = self.title_combo.findText(default_title)
            if index >= 0:
                self.title_combo.setCurrentIndex(index)

        except Exception as e:
            print(f"Error loading report titles: {e}")

    def _generate_text(self):
        age = self.age_input.text().strip()
        diagnosis = self.diagnosis_input.text().strip()
        
        if not age or not diagnosis:
            NotificationService.show_warning(self, "Date incomplete", 
                                        "Completează vârsta și diagnosticul.")
            return

        if not age.isdigit():
            NotificationService.show_warning(self, "Atentie",
                                             "Varsta trebuie sa fie un numar.")
            return
        
        # HTML pentru formatare
        indicatie_html = f"""<p><b><i>Indicație:</i></b> Pacient în vârsta de {age} ani este diagnosticat cu {diagnosis}</p>

        <p><b><i>Realizare:</i></b> </p>

        <p><b><i>Rezultat:</i></b></p>

        <p><b>CONCLUZII<b><p>
        """

        self.text_edit.setHtml(indicatie_html)

        cursor = self.text_edit.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.text_edit.setTextCursor(cursor)
        
    def get_selected_title(self) -> str:
        return self.title_combo.currentText()

    def set_selected_title(self, title: str):
        index = self.title_combo.findText(title)
        if index >= 0:
            self.title_combo.setCurrentIndex(index)

    def get_result_text(self) -> str:
        return self.text_edit.toPlainText()

    def get_result_text_html(self) -> str:
        html_content = self.text_edit.toHtml()

        body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.DOTALL)
        if body_match:
            content = body_match.group(1)
        else:
            content = html_content

        content = re.sub(r'<p[^>]*>', '<p>', content)

        content = re.sub(r'<span[^>]*font-weight:\s*(700|bold)[^>]*>(.*?)</span>', r'<strong>\2</strong>', content)

        content = re.sub(r'<span[^>]*font-style:\s*italic[^>]*>(.*?)</span>', r'<em>\1</em>', content)

        content = re.sub(r'<span[^>]*text-decoration:\s*underline[^>]*>(.*?)</span>', r'<u>\1</u>', content)

        content = re.sub(r'<span[^>]*>', '', content)
        content = re.sub(r'</span>', '', content)

        content = re.sub(r'<p>\s*</p>', '', content)
        content = re.sub(r'<p></p>', '', content)

        content = re.sub(r'\s+', ' ', content)

        return content.strip()

    def set_result_text(self, text: str):
        self.text_edit.setPlainText(text)

    def clear_result(self, clear_all=False):
        self.text_edit.clear()
        if clear_all:
            self.age_input.clear()
            self.diagnosis_input.clear()