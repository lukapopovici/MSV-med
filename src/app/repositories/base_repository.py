from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List
from sqlalchemy.orm import Session

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    def __init__(self, db_config):
        self._db_config = db_config

    def _get_session(self) -> Session:
        return self._db_config.get_session()

    @abstractmethod
    def find_by_id(self, entity_id: int) -> Optional[T]:
        pass

    @abstractmethod
    def create(self, entity: T) -> T:
        pass

    @abstractmethod
    def update(self, entity: T) -> T:
        pass

    @abstractmethod
    def delete(self, entity_id: int) -> bool:
        pass

    @abstractmethod
    def find_all(self) -> List[T]:
        pass