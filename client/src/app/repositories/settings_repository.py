from typing import Optional, List
from sqlalchemy.exc import SQLAlchemyError
from app.database.models import AppSettings
from app.repositories.base_repository import BaseRepository


class SettingsRepository(BaseRepository[AppSettings]):

    def find_by_id(self, entity_id: int) -> Optional[AppSettings]:
        session = self._get_session()
        try:
            return session.query(AppSettings).filter_by(id=entity_id).first()
        finally:
            session.close()

    def create(self, entity: AppSettings) -> AppSettings:
        session = self._get_session()
        try:
            session.add(entity)
            session.commit()
            session.refresh(entity)
            return entity
        except SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def update(self, entity: AppSettings) -> AppSettings:
        session = self._get_session()
        try:
            session.merge(entity)
            session.commit()
            return entity
        except SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete(self, entity_id: int) -> bool:
        session = self._get_session()
        try:
            setting = session.query(AppSettings).filter_by(id=entity_id).first()
            if not setting:
                return False
            session.delete(setting)
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def find_all(self) -> List[AppSettings]:
        session = self._get_session()
        try:
            return session.query(AppSettings).all()
        finally:
            session.close()

    def find_by_key(self, setting_key: str) -> Optional[AppSettings]:
        session = self._get_session()
        try:
            return session.query(AppSettings).filter_by(setting_key=setting_key).first()
        finally:
            session.close()

    def get_value(self, setting_key: str, default_value: str = None) -> Optional[str]:
        setting = self.find_by_key(setting_key)
        return setting.setting_value if setting else default_value

    def set_value(self, setting_key: str, setting_value: str, description: str = None) -> bool:
        session = self._get_session()
        try:
            setting = session.query(AppSettings).filter_by(setting_key=setting_key).first()

            if setting:
                # Update existing
                setting.setting_value = setting_value
                if description:
                    setting.description = description
            else:
                # Create new
                setting = AppSettings(
                    setting_key=setting_key,
                    setting_value=setting_value,
                    description=description
                )
                session.add(setting)

            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()
            