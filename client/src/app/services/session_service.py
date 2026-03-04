from typing import Optional
from app.core.interfaces.session_interface import ISessionService
from app.core.entities.user import User


class SessionService(ISessionService):
    def __init__(self):
        self._current_user: Optional[User] = None

    def login(self, user: User) -> None:
        self._current_user = user

    def logout(self) -> None:
        self._current_user = None

    def get_current_user(self) -> Optional[User]:
        return self._current_user

    def is_authenticated(self) -> bool:
        return self._current_user is not None

    def get_username(self) -> Optional[str]:
        return self._current_user.username if self._current_user else None

    def get_role(self) -> Optional[str]:
        return self._current_user.role.value if self._current_user else None