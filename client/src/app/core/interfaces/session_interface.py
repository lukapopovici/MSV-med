from abc import ABC, abstractmethod
from typing import Optional
from app.core.entities.user import User


class ISessionService(ABC):
    @abstractmethod
    def login(self, user: User) -> None:
        pass

    @abstractmethod
    def logout(self) -> None:
        pass

    @abstractmethod
    def get_current_user(self) -> Optional[User]:
        pass

    @abstractmethod
    def is_authenticated(self) -> bool:
        pass