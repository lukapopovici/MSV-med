from typing import Optional, List
from sqlalchemy.exc import SQLAlchemyError

from app.repositories.base_repository import BaseRepository
from app.database.models import ReportTitle


class ReportTitleRepository(BaseRepository[ReportTitle]):

    def find_by_id(self, entity_id: int) -> Optional[ReportTitle]:
        session = self._get_session()
        try:
            return session.query(ReportTitle).filter_by(id=entity_id).first()
        finally:
            session.close()

    def create(self, entity: ReportTitle) -> ReportTitle:
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

    def update(self, entity: ReportTitle) -> ReportTitle:
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
            report_title = session.query(ReportTitle).filter_by(id=entity_id).first()
            if not report_title:
                return False
            session.delete(report_title)
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def find_all(self) -> List[ReportTitle]:
        session = self._get_session()
        try:
            return session.query(ReportTitle).order_by(ReportTitle.title_text).all()
        finally:
            session.close()

    def find_by_title_text(self, title_text: str) -> Optional[ReportTitle]:
        session = self._get_session()
        try:
            return session.query(ReportTitle).filter_by(title_text=title_text).first()
        finally:
            session.close()