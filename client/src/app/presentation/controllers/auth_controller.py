from app.core.interfaces.auth_interface import IAuthService
from app.core.interfaces.session_interface import ISessionService
from app.services.notification_service import NotificationService
from app.core.exceptions.auth_exceptions import AuthenticationError


class AuthController:
    def __init__(self, auth_service: IAuthService, session_service: ISessionService):
        self._auth_service = auth_service
        self._session_service = session_service
        self._notification_service = NotificationService()

    def login(self, username: str, password: str, parent_widget) -> bool:
        try:
            user = self._auth_service.authenticate(username, password)
            self._session_service.login(user)
            return True
        except AuthenticationError as e:
            self._notification_service.show_error(parent_widget, "Logarea a esuat", str(e))
            return False
        except Exception as e:
            self._notification_service.show_error(parent_widget, "Eroare", f"Eroare la logare: {e}")
            return False

    def logout(self, parent_widget) -> bool:
        if self._notification_service.ask_confirmation(
                parent_widget, "Confirm Logout", "Esti sigur ca vrei sa te deloghezi?"
        ):
            self._session_service.logout()
            return True
        return False

    def get_current_user(self):
        return self._session_service.get_current_user()

    def is_authenticated(self) -> bool:
        return self._session_service.is_authenticated()