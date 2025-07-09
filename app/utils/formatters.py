import re
from datetime import datetime
from typing import Dict, Any


class Formatters:
    @staticmethod
    def format_filename(patient_name: str, study_date: str, timestamp: str = None) -> str:
        safe_name = re.sub(r'\W+', '_', patient_name)
        safe_date = study_date.replace("-", "")

        if timestamp is None:
            timestamp = datetime.now().strftime("%H%M%S")

        return f"{safe_name}_{safe_date}_{timestamp}.pdf"

    @staticmethod
    def format_study_display_text(patient_name: str, study_date: str, description: str) -> str:
        return f"{patient_name} - {study_date} - {description}"

    @staticmethod
    def format_metadata_display(metadata: Dict[str, Any]) -> str:
        formatted_items = []

        display_names = {
            # Date Pacient
            "Patient Name": "Nume pacient",
            "CNP": "CNP",
            "Patient ID": "ID pacient",
            "Patient Birth Date": "Data nașterii",
            "Patient Sex": "Sex",
            "Patient Age": "Vârsta",

            # Date Studiu
            "Study Date": "Data examinării",
            "Study Time": "Ora examinării",
            "Study Description": "Tip examinare",
            "Accession Number": "Număr acces",
            "Referring Physician": "Medic trimițător",
            "Study ID": "ID studiu",

            # Date Tehnice
            "Institution Name": "Instituția",
            "Modality": "Tip echipament",
            "Body Part Examined": "Zonă examinată",
            "Series Description": "Descriere secvență",

            # Status
            "Study Instance UID": "ID instanță",
            "Series Status": "Status"
        }

        patient_section = []
        study_section = []
        technical_section = []

        for key, value in metadata.items():
            display_name = display_names.get(key, key)
            formatted_value = value if value and value != 'N/A' else "Necunoscut"

            if key in ["Patient Name", "CNP", "Patient ID", "Patient Birth Date", "Patient Sex", "Patient Age"]:
                patient_section.append(f"{display_name}: {formatted_value}")
            elif key in ["Study Date", "Study Time", "Study Description", "Accession Number", "Referring Physician"]:
                study_section.append(f"{display_name}: {formatted_value}")
            else:
                technical_section.append(f"{display_name}: {formatted_value}")

        result = []
        if patient_section:
            result.append("=== DATE PACIENT ===")
            result.extend(patient_section)
            result.append("")

        if study_section:
            result.append("=== DATE EXAMINARE ===")
            result.extend(study_section)
            result.append("")

        if technical_section:
            result.append("=== DETALII TEHNICE ===")
            result.extend(technical_section)

        return "\n".join(result)

    @staticmethod
    def sanitize_html(text: str) -> str:
        return text.replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')