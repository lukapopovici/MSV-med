import pydicom
from io import BytesIO
import hashlib


class DicomAnonymizer:
    def __init__(self):
        pass

    def anonymize_dicom(self, dicom_data: bytes) -> bytes:
        try:
            dataset = pydicom.dcmread(BytesIO(dicom_data))

            # Genereaza ID anonim unic
            anonymous_id = self.generate_anonymous_id(dataset)

            dataset.PatientName = f"ANONYMOUS^{anonymous_id[-6:]}"
            dataset.PatientID = anonymous_id
            dataset.PatientBirthDate = ""
            dataset.PatientSex = ""
            dataset.PatientAge = ""

            if hasattr(dataset, 'InstitutionName'):
                dataset.InstitutionName = "ANONYMOUS_HOSPITAL"
            if hasattr(dataset, 'ReferringPhysicianName'):
                dataset.ReferringPhysicianName = "ANONYMOUS^DOCTOR"
            if hasattr(dataset, 'AccessionNumber'):
                dataset.AccessionNumber = f"ACC{anonymous_id[-6:]}"
            if hasattr(dataset, 'StudyID'):
                dataset.StudyID = f"STUDY{anonymous_id[-6:]}"

            personal_fields = [
                'PatientAddress', 'PatientTelephoneNumbers', 'EthnicGroup',
                'PatientComments', 'OtherPatientIDs', 'OtherPatientNames'
            ]

            for field in personal_fields:
                if hasattr(dataset, field):
                    setattr(dataset, field, "")

            # Salvez DICOM in memorie si retunrez datele ca bytes
            output = BytesIO()
            dataset.save_as(output, write_like_original=False)
            return output.getvalue()

        except Exception as e:
            print(f"Error anonymizing DICOM: {e}")
            return dicom_data

    def generate_anonymous_id(self, dataset) -> str:
        try:
            patient_name = str(getattr(dataset, 'PatientName', '')).strip()
            patient_id = str(getattr(dataset, 'PatientID', '')).strip()
            birth_date = str(getattr(dataset, 'PatientBirthDate', '')).strip()

            unique_string = f"{patient_name}|{patient_id}|{birth_date}"
            hash_value = hashlib.sha256(unique_string.encode('utf-8')).hexdigest()
            return f"ANON{abs(int(hash_value[:8], 16)) % 999999:06d}"

        except Exception:
            import uuid
            return f"ANON{abs(hash(str(uuid.uuid4()))) % 999999:06d}"