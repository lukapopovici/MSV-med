from typing import Optional, Tuple
from app.repositories.settings_repository import SettingsRepository


class SettingsService:
    # Setting keys constants
    SOURCE_PACS_ID_KEY = "source_pacs_id"
    TARGET_PACS_ID_KEY = "target_pacs_id"

    def __init__(self, settings_repository: SettingsRepository):
        self._settings_repository = settings_repository

    def get_source_pacs_id(self) -> Optional[int]:
        value = self._settings_repository.get_value(self.SOURCE_PACS_ID_KEY)
        return int(value) if value and value.isdigit() else None

    def set_source_pacs_id(self, pacs_id: Optional[int]) -> bool:
        try:
            value = str(pacs_id) if pacs_id is not None else ""
            return self._settings_repository.set_value(
                self.SOURCE_PACS_ID_KEY,
                value,
                "ID-ul PACS-ului sursă pentru citirea studiilor"
            )
        except Exception as e:
            print(f"Error setting source PACS ID: {e}")
            return False

    def get_target_pacs_id(self) -> Optional[int]:
        value = self._settings_repository.get_value(self.TARGET_PACS_ID_KEY)
        return int(value) if value and value.isdigit() else None

    def set_target_pacs_id(self, pacs_id: Optional[int]) -> bool:
        try:
            value = str(pacs_id) if pacs_id is not None else ""
            return self._settings_repository.set_value(
                self.TARGET_PACS_ID_KEY,
                value,
                "ID-ul PACS-ului țintă pentru trimiterea studiilor"
            )
        except Exception as e:
            print(f"Error setting target PACS ID: {e}")
            return False

    def get_source_pacs_config(self) -> Optional[Tuple[str, Tuple[str, str]]]:
        source_id = self.get_source_pacs_id()
        if source_id:
            try:
                from app.di.container import Container
                pacs_url_service = Container.get_pacs_url_service()
                return pacs_url_service.get_pacs_config_by_id(source_id)
            except Exception as e:
                print(f"Error getting source PACS config: {e}")
        return None

    def get_target_pacs_config(self) -> Optional[Tuple[str, Tuple[str, str]]]:
        target_id = self.get_target_pacs_id()
        if target_id:
            try:
                from app.di.container import Container
                pacs_url_service = Container.get_pacs_url_service()
                return pacs_url_service.get_pacs_config_by_id(target_id)
            except Exception as e:
                print(f"Error getting target PACS config: {e}")
        return None

    def get_pacs_settings_summary(self) -> dict:
        try:
            from app.di.container import Container
            pacs_url_service = Container.get_pacs_url_service()

            source_id = self.get_source_pacs_id()
            target_id = self.get_target_pacs_id()

            source_pacs = pacs_url_service.get_pacs_by_id(source_id) if source_id else None
            target_pacs = pacs_url_service.get_pacs_by_id(target_id) if target_id else None

            return {
                'source_pacs_id': source_id,
                'target_pacs_id': target_id,
                'source_pacs_name': source_pacs.name if source_pacs else None,
                'source_pacs_url': source_pacs.url if source_pacs else None,
                'target_pacs_name': target_pacs.name if target_pacs else None,
                'target_pacs_url': target_pacs.url if target_pacs else None,
            }
        except Exception as e:
            print(f"Error getting PACS settings summary: {e}")
            return {
                'source_pacs_id': None,
                'target_pacs_id': None,
                'source_pacs_name': None,
                'source_pacs_url': None,
                'target_pacs_name': None,
                'target_pacs_url': None,
            }

    def reset_pacs_settings(self) -> bool:
        try:
            success1 = self.set_source_pacs_id(None)
            success2 = self.set_target_pacs_id(None)
            return success1 and success2
        except Exception as e:
            print(f"Error resetting PACS settings: {e}")
            return False

    def validate_pacs_settings(self) -> Tuple[bool, str]:
        try:
            source_id = self.get_source_pacs_id()
            target_id = self.get_target_pacs_id()

            if not source_id:
                return False, "PACS sursă nu este setat"

            if not target_id:
                return False, "PACS țintă nu este setat"

            # Check if PACS exist and are accessible
            from app.di.container import Container
            pacs_url_service = Container.get_pacs_url_service()

            source_pacs = pacs_url_service.get_pacs_by_id(source_id)
            if not source_pacs:
                return False, f"PACS sursă cu ID {source_id} nu mai există"

            target_pacs = pacs_url_service.get_pacs_by_id(target_id)
            if not target_pacs:
                return False, f"PACS țintă cu ID {target_id} nu mai există"

            return True, "Setările PACS sunt valide"

        except Exception as e:
            return False, f"Eroare la validarea setărilor: {e}"