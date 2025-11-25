import bcrypt
from typing import Optional
from app.core.interfaces.auth_interface import IAuthService, IUserRepository
from app.core.entities.user import User
from app.core.exceptions.auth_exceptions import AuthenticationError


class AuthService(IAuthService):
    def __init__(self, user_repository: IUserRepository):
        self._user_repository = user_repository

    def authenticate(self, username: str, password: str) -> Optional[User]:
        if not username or not password:
            raise AuthenticationError("Introduceti username si parola.")

        user = self._user_repository.find_by_username(username)
        if not user:
            raise AuthenticationError(f"Utilizatorul {user} este inexistent.")

        if not self.verify_password(password, user.password):
            raise AuthenticationError("Username-ul sau parola sunt gresite.")

        return user

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))