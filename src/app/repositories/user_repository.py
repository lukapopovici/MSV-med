from typing import Optional, List
from sqlalchemy.exc import SQLAlchemyError

from app.core.interfaces.auth_interface import IUserRepository
from app.core.entities.user import User, UserRole
from app.core.exceptions.auth_exceptions import UserNotFoundError, UserAlreadyExistsError
from app.repositories.base_repository import BaseRepository

from app.database.models import User as UserModel, RoleEnum


class UserRepository(BaseRepository[User], IUserRepository):
    def find_by_username(self, username: str) -> Optional[User]:
        session = self._get_session()
        try:
            user_model = session.query(UserModel).filter_by(username=username).first()
            if user_model:
                return self._map_to_entity(user_model)
            return None
        finally:
            session.close()

    def find_by_id(self, user_id: int) -> Optional[User]:
        session = self._get_session()
        try:
            user_model = session.query(UserModel).filter_by(id=user_id).first()
            if user_model:
                return self._map_to_entity(user_model)
            return None
        finally:
            session.close()

    def create(self, user: User) -> User:
        session = self._get_session()
        try:
            existing = session.query(UserModel).filter_by(username=user.username).first()
            if existing:
                raise UserAlreadyExistsError(f"Utilizatorul cu username-ul '{user.username}' exista deja.")

            user_model = UserModel(
                username=user.username,
                password=user.password,
                role=RoleEnum(user.role.value),
                first_name=user.first_name,
                last_name=user.last_name,
                title=user.title
            )

            session.add(user_model)
            session.commit()
            session.refresh(user_model)

            return self._map_to_entity(user_model)
        except SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def update(self, user: User) -> User:
        session = self._get_session()
        try:
            user_model = session.query(UserModel).filter_by(id=user.id).first()
            if not user_model:
                raise UserNotFoundError(f"Utilizatorul cu username-ul {user.username} nu a fost gasit.")

            user_model.username = user.username
            user_model.password = user.password
            user_model.role = RoleEnum(user.role.value)
            user_model.first_name = user.first_name
            user_model.last_name = user.last_name
            user_model.title = user.title

            session.commit()
            session.refresh(user_model)

            return self._map_to_entity(user_model)
        except SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete(self, user_id: int) -> bool:
        session = self._get_session()
        try:
            user_model = session.query(UserModel).filter_by(id=user_id).first()
            if not user_model:
                return False

            session.delete(user_model)
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def find_all(self) -> List[User]:
        session = self._get_session()
        try:
            user_models = session.query(UserModel).all()
            return [self._map_to_entity(model) for model in user_models]
        finally:
            session.close()

    def _map_to_entity(self, user_model: UserModel) -> User:
        return User(
            id=user_model.id,
            username=user_model.username,
            password=user_model.password,
            role=UserRole(user_model.role.value),
            first_name=user_model.first_name,
            last_name=user_model.last_name,
            title=user_model.title  # Map title field
        )