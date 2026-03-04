from abc import ABC, abstractmethod
from typing import List, Dict, Any


class IPacsService(ABC):
    @abstractmethod
    def get_all_studies(self) -> List[str]:
        pass

    @abstractmethod
    def get_study_metadata(self, study_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_study_instances(self, study_id: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_dicom_file(self, instance_id: str) -> bytes:
        pass

    @abstractmethod
    def send_study_to_pacs(self, study_id: str, target_url: str, target_auth: str, examination_result: str = None) -> bool:
        pass

    @abstractmethod
    def get_examination_result_from_dicom(self, instance_id: str) -> str:
        pass

    def clear_local_studies(self):
        pass
