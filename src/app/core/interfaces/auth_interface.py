from abc import ABC, abstractmethod
from typing import Optional
from app.core.entities.user import User


class IAuthService(ABC):
    @abstractmethod
    def authenticate(self, username: str, password: str) -> Optional[User]:
        pass

    @abstractmethod
    def hash_password(self, password: str) -> str:
        pass

    @abstractmethod
    def verify_password(self, password: str, hashed_password: str) -> bool:
        pass


class IUserRepository(ABC):
    @abstractmethod
    def find_by_username(self, username: str) -> Optional[User]:
        pass

    @abstractmethod
    def create(self, user: User) -> User:
        pass