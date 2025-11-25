from typing import List, Dict, Any, Optional
from app.core.interfaces.pacs_interface import IPacsService
from app.services.local_file_service import LocalFileService
from app.services.pacs_service import PacsService


class HybridPacsService(IPacsService):
    def __init__(self, pacs_service: PacsService, local_file_service: LocalFileService):
        self._pacs_service = pacs_service
        self._local_file_service = local_file_service

    def get_all_studies(self) -> List[str]:
        studies = []

        # Get PACS studies
        try:
            pacs_studies = self._pacs_service.get_all_studies()
            studies.extend(pacs_studies)
        except Exception as e:
            print(f"Warning: Could not load PACS studies: {e}")

        # Get local studies
        try:
            local_studies = self._local_file_service.get_all_local_studies()
            studies.extend(local_studies)
        except Exception as e:
            print(f"Warning: Could not load local studies: {e}")

        return studies

    def get_study_metadata(self, study_id: str) -> Dict[str, Any]:
        if self._is_local_study(study_id):
            return self._local_file_service.get_local_study_metadata(study_id)
        else:
            return self._pacs_service.get_study_metadata(study_id)

    def get_study_instances(self, study_id: str) -> List[Dict[str, Any]]:
        if self._is_local_study(study_id):
            return self._local_file_service.get_local_study_instances(study_id)
        else:
            return self._pacs_service.get_study_instances(study_id)

    def get_dicom_file(self, instance_id: str) -> bytes:
        if self._is_local_instance(instance_id):
            return self._local_file_service.get_local_dicom_file(instance_id)
        else:
            return self._pacs_service.get_dicom_file(instance_id)

    def send_study_to_pacs(self, study_id: str, target_url: str, target_auth: tuple,
                           examination_result: str = None) -> bool:
        if self._is_local_study(study_id):
            print(f"HybridPacsService: Sending local study {study_id} (anonymized)")
            return self._local_file_service.send_local_study_to_pacs(
                study_id=study_id,
                target_url=target_url,
                target_auth=target_auth,
                examination_result=examination_result
            )
        else:
            return self._pacs_service.send_study_to_pacs(
                study_id, target_url, target_auth, examination_result, anonymize=True
            )

    def get_examination_result_from_dicom(self, instance_id: str) -> str:
        if self._is_local_instance(instance_id):
            # Try to read from DICOM file first, fallback to cache
            result = self._local_file_service.get_examination_result_from_local_dicom_file(instance_id)

            if not result:
                study_id = self._get_study_id_for_local_instance(instance_id)
                if study_id:
                    result = self._local_file_service.get_examination_result_from_local_study(study_id)

            return result
        else:
            return self._pacs_service.get_examination_result_from_dicom(instance_id)

    def load_local_dicom_file(self, file_path: str) -> Dict[str, Any]:
        return self._local_file_service.load_dicom_file(file_path)

    def load_local_dicom_folder(self, folder_path: str) -> List[Dict[str, Any]]:
        return self._local_file_service.load_dicom_folder(folder_path)

    def clear_local_studies(self):
        self._local_file_service.clear_local_studies()

    def remove_local_study(self, study_id: str) -> bool:
        if self._is_local_study(study_id):
            return self._local_file_service.remove_local_study(study_id)
        return False

    def get_local_studies_count(self) -> int:
        return len(self._local_file_service.get_all_local_studies())

    def add_examination_result_to_study(self, study_id: str, examination_result: str):
        if self._is_local_study(study_id):
            self._local_file_service.add_examination_result_to_local_study(study_id, examination_result)

    def get_examination_result_from_study(self, study_id: str) -> str:
        if self._is_local_study(study_id):
            return self._local_file_service.get_examination_result_from_local_study(study_id)
        else:
            # For PACS studies, try to get from first instance
            try:
                instances = self.get_study_instances(study_id)
                for instance in instances:
                    instance_id = instance.get("ID")
                    if instance_id:
                        result = self._pacs_service.get_examination_result_from_dicom(instance_id)
                        if result:
                            return result
            except Exception as e:
                print(f"Error getting examination result from PACS study {study_id}: {e}")

            return ""

    def _is_local_study(self, study_id: str) -> bool:
        return study_id.startswith("local_")

    def _is_local_instance(self, instance_id: str) -> bool:
        return instance_id.startswith("local_")

    def _get_study_id_for_local_instance(self, instance_id: str) -> Optional[str]:
        for study_id in self._local_file_service.get_all_local_studies():
            instances = self._local_file_service.get_local_study_instances(study_id)
            for instance in instances:
                if instance.get("ID") == instance_id:
                    return study_id
        return None