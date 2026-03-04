from dataclasses import dataclass
from typing import Optional


@dataclass
class Patient:
    name: str
    birth_date: Optional[str] = None
    sex: Optional[str] = None


@dataclass
class Study:
    id: str
    patient: Patient
    study_date: str
    description: str
    study_instance_uid: str
    series_status: Optional[str] = None

    def get_display_text(self) -> str:
        return f"{self.patient.name} - {self.study_date} - {self.description}"