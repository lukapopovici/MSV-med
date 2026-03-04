import os
import re
import base64
from datetime import datetime
from weasyprint import HTML, CSS
from typing import Dict, Any
from pathlib import Path


class PdfGenerator:
    def __init__(self, css_path: str):
        self.css_path = css_path

    def create_pdf(self, content: str, metadata: Dict[str, Any], output_path: str, doctor_name: str = None,
                   selected_title: str = None, header_image_path: str = None):

        generated_date = datetime.now().strftime("%d.%m.%Y %H:%M")
        current_year = datetime.now().strftime("%Y")

        patient_metadata = self._filter_patient_metadata(metadata)

        html_content = self._build_html_content(
            content, patient_metadata, generated_date, doctor_name, current_year, selected_title, header_image_path
        )

        stylesheets = []
        if self.css_path:
            stylesheets.append(CSS(self.css_path))

        html_obj = HTML(string=html_content, base_url=Path.cwd().as_uri())
        html_obj.write_pdf(output_path, stylesheets=stylesheets)

    def _image_to_base64(self, image_path: str) -> str:
        try:
            with open(image_path, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
                
                ext = os.path.splitext(image_path)[1].lower()
                if ext == '.png':
                    mime_type = 'image/png'
                elif ext in ['.jpg', '.jpeg']:
                    mime_type = 'image/jpeg'
                elif ext == '.gif':
                    mime_type = 'image/gif'
                else:
                    mime_type = 'image/png'
                
                base64_string = f"data:{mime_type};base64,{image_data}"
                return base64_string
                
        except Exception as e:
            print(f"Error converting image to base64: {e}")
            return ""

    def _get_windows_file_uri(self, file_path: str) -> str:
        try:
            normalized_path = os.path.normpath(file_path)
            
            path_obj = Path(normalized_path)
            file_uri = path_obj.as_uri()
            
            return file_uri
            
        except Exception as e:
            print(f"Error creating Windows file URI: {e}")
            return ""

    def _build_html_content(self, content: str, patient_metadata: Dict[str, Any], generated_date: str,
                            doctor_name: str = None, current_year: str = None, selected_title: str = None, 
                            header_image_path: str = None) -> str:

        # Extrage datele din metadata
        patient_name = patient_metadata.get("Nume pacient", "")
        cnp = patient_metadata.get("CNP", "")
        dosar_nr = patient_metadata.get("Dosar nr.", "")
        gamma_camera = patient_metadata.get("Model echipament", "")
        investigation = patient_metadata.get("Tip examinare", "")
        diagnosis = patient_metadata.get("Diagnostic de trimitere", "")
        dose_mbq = patient_metadata.get("Doza administrata", "")
        radiopharmaceutical = patient_metadata.get("Radiofarmaceutic", "")
        exam_date = patient_metadata.get("Data examinarii", "")
        referring_doctor = patient_metadata.get("Medic trimitator", "")

        exam_title = selected_title if selected_title else ""

        header_content = ""
        if header_image_path and os.path.exists(header_image_path):
            base64_image = self._image_to_base64(header_image_path)
            if base64_image:
                header_content = f'<img src="{base64_image}" alt="Antet Spital" class="header-image">'
            else:
                file_uri = self._get_windows_file_uri(header_image_path)
                if file_uri:
                    header_content = f'<img src="{file_uri}" alt="Antet Spital" class="header-image">'
                else:
                    header_content = '<div class="header-placeholder"><!-- ANTET SPITAL - IMAGE ERROR --></div>'
        else:
            header_content = '<div class="header-placeholder"><!-- ANTET SPITAL --></div>'

        return f"""
        <!DOCTYPE html>
        <html lang="ro">
        <head>
            <meta charset="UTF-8">
            <title>{exam_title}</title>
        </head>
        <body>
            <div class="page-container">
                <!-- PARTEA STÂNGĂ - IDENTICĂ CU IMAGINEA -->
                <div class="left-panel">
                    <div class="lab-title">
                        <strong>Laborator<br>MEDICINA<br>NUCLEARĂ</strong>
                    </div>

                    <div class="prof-name">
                        <strong>Prof. dr.<br>Valeriu Rusu</strong>
                    </div>

                    <div class="address">
                        B-dul Independentei<br>
                        nr. 1, etaj, cod 700111<br>
                        tel./programări:<br>
                        <strong>0232 240 822,<br>
                        int.120</strong><br>
                        sau <strong>0770 936 586</strong><br>
                        e-mail:<br>
                        <strong>laboratornucleara<br>
                        @spitalspiridon.ro</strong>
                    </div>

                    <div class="section-header">
                        <strong>Sef laborator</strong><br>
                        <strong>Prof. dr. Cipriana<br>
                        STEFANESCU –</strong><br>
                        medic primar<br>
                        medicina nucleara si<br>
                        endocrinologie
                    </div>

                    <div class="section-header">
                        <strong><u>Medici</u></strong><br>
                        <strong>Ana Maria STATESCU</strong><br>
                        – medic primar med.<br>
                        nucl.<br>
                        <strong>Irena GRIEROSU</strong><br>
                        – sef lucr. dr., medic<br>
                        primar med. nucl.<br>
                        <strong>Cati-Raluca<br>
                        STOLNICEANU</strong><br>
                        – asist. univ. dr.,<br>
                        medic primar med.nucl.<br>
                        <strong>Wael JALLOUL</strong><br>
                        – asist. univ. dr., medic<br>
                        medic primar med.nucl.
                    </div>

                    <div class="section-header">
                        <strong><u>Fizician</u></strong><br>
                        <strong>Vlad GHIZDOVAT</strong>
                    </div>

                    <div class="section-header">
                        <strong><u>Medici rezidenti</u></strong><br>
                        <strong>Laura PINTILIE<br>
                        Radu CONSTANTIN<br>
                        Larisa Elena RAU<br>
                        Angela OARZA<br>
                        Oana OLARIU<br>
                        Raluca Rafaela ION<br>
                        Ana Maria NISTOR<br>
                        Sabina DEJMASU<br>
                        Malina EPURE</strong>
                    </div>

                    <div class="section-header">
                        <strong><u>Asistenta sefa</u></strong><br>
                        <strong>Alina TIMOFTI</strong>
                    </div>

                    <div class="section-header">
                        <strong><u>Asistenti</u></strong><br>
                        <strong>Ofelia PERJU<br>
                        Alina STEFAN<br>
                        Monica PENISOARA<br>
                        Otilia LISMAN<br>
                        Laura VARZAR</strong>
                    </div>

                    <div class="section-header">
                        <strong><u>Personal auxiliar</u></strong><br>
                        <strong>Irina ATASIEI<br>
                        Genoveva SPATARU</strong>
                    </div>

                    <div class="section-header">
                        <strong><u>Registrator medical</u></strong><br>
                        <strong>Lupascu Adrian</strong>
                    </div>
                </div>

                <!-- PARTEA DREAPTĂ - IDENTICĂ CU IMAGINEA -->
                <div class="right-panel">
                    <!-- SPAȚIU PENTRU ANTETUL SPITALULUI -->
                    <div class="hospital-header-space">
                        {header_content}<br><br><br><br>
                    </div>

                    <!-- DATELE PACIENTULUI -->
                    <div class="patient-section">
                        <div class="patient-data">
                            <strong>Nume:</strong> {patient_name}<br>
                            <strong>CNP:</strong> {cnp}<br>
                            <strong>Dosar nr.:</strong> {dosar_nr}<br>
                            <strong>Gamma camera:</strong> {gamma_camera}<br>
                            <strong>Investigatie la recomandarea:</strong> {referring_doctor}<br> 
                            <strong>Diagnostic de trimitere:</strong> {diagnosis}<br>
                            <strong>Doza:</strong> {dose_mbq} <strong>Radiofarmaceutic:</strong> <strong>{radiopharmaceutical}</strong>
                        </div>

                        <div class="exam-date-right">
                            <strong>Data {self._format_date(exam_date)}</strong>
                        </div>
                    </div>

                    <!-- TITLUL EXAMINĂRII -->
                    <div class="main-title">
                        <h1>{exam_title}</h1>
                    </div>

                    <!-- CONȚINUTUL EXAMINĂRII -->
                    <div class="examination-content">
                        {self._format_content_for_html(content)}
                    </div>

                    <!-- SEMNĂTURILE -->
                    <div class="signatures-section">
                        <div class="signature-left-bottom">
                            <strong>Sef laborator</strong><br>
                            Medic primar Medicina Nucleara<br>
                            <strong>Prof. dr. Cipriana STEFANESCU</strong>
                        </div>

                        <div class="signature-right-bottom">
                            Medic specialist Medicina Nucleara<br>
                            <strong>{doctor_name if doctor_name else "Dr. [Nume Medic]"}</strong>
                        </div>
                    </div>

                    <div class="resident-signature-bottom">
                        <strong>Medic rezident Medicina Nucleara</strong>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

    def _filter_patient_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        patient_fields = {
            # Patient information
            "Patient Name": "Nume pacient",
            "CNP": "CNP",
            "Patient Birth Date": "Data nasterii",
            "Patient Sex": "Sex",
            "Patient Age": "Varsta",

            # Examination information
            "Study Date": "Data examinarii",
            "Description": "Tip examinare",
            "Body Part Examined": "Zona examinata",
            "Referring Physician Name": "Medic trimitator",
            "Accession Number": "Dosar nr.",
            "Radiopharmaceutical": "Radiofarmaceutic",

            # Institution information
            "Institution Name": "Institutia medicala"
        }

        filtered_metadata = {}

        for original_key, friendly_name in patient_fields.items():
            value = metadata.get(original_key)
            if value and value != 'N/A' and value.strip():
                if original_key == "Study Time" and len(value) >= 6:
                    try:
                        formatted_time = f"{value[:2]}:{value[2:4]}:{value[4:6]}"
                        filtered_metadata[friendly_name] = formatted_time
                    except:
                        filtered_metadata[friendly_name] = value
                elif original_key == "Patient Sex":
                    sex_mapping = {"M": "Masculin", "F": "Feminin", "O": "Altul"}
                    filtered_metadata[friendly_name] = sex_mapping.get(value.upper(), value)
                else:
                    filtered_metadata[friendly_name] = value

        return filtered_metadata

    def _format_content_for_html(self, content: str) -> str:
        if not content.strip():
            return "<p><em style='color: #94a3b8; font-size: 11px; font-style: italic;'>Nu a fost introdus niciun rezultat al investigației.</em></p>"

        if '<p>' in content or '<strong>' in content or '<em>' in content:
            content = re.sub(r'<p>', '<p style="margin: 12px 0; line-height: 1.5;">', content)
            return content

        import html
        content = html.escape(content)

        paragraphs = content.split('\n\n')
        formatted_paragraphs = []

        for paragraph in paragraphs:
            if paragraph.strip():
                paragraph = paragraph.replace('\n', '<br>')
                formatted_paragraphs.append(f'<p style="margin: 12px 0; line-height: 1.5;">{paragraph}</p>')

        return ''.join(
            formatted_paragraphs) if formatted_paragraphs else f'<p style="margin: 12px 0; line-height: 1.5;">{content}</p>'

    def _format_date(self, date_str: str) -> str:
        if not date_str or date_str == 'N/A' or not date_str.strip():
            return date_str

        clean_date = ''.join(filter(str.isdigit, date_str))

        if len(clean_date) >= 8:
            year = clean_date[:4]
            month = clean_date[4:6]
            day = clean_date[6:8]
            return f"{year}-{month}-{day}"

        if '-' in date_str and len(date_str) == 10:
            return date_str

        return date_str