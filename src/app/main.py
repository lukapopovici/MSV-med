import sys
import os

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication
from app.presentation.views.login_view import LoginView
from app.di.container import Container
from app.config.settings import Settings


def setup_application():
    settings = Settings()

    os.makedirs(settings.PDF_OUTPUT_DIR, exist_ok=True)
    os.makedirs(settings.PDF_PREVIEW_DIR, exist_ok=True)
    os.makedirs("tmp_pdfs/preview", exist_ok=True)

    print("Application directories created successfully")


def log_session_info():
    try:
        session_service = Container.get_session_service()
        user = session_service.get_current_user()

        if user:
            print(f"[Session] User: {user.username} | Role: {user.role.value}")
        else:
            print("[Session] No user logged in")
    except Exception as e:
        print(f"[Session] Error getting session info: {e}")


def main():
    print("Starting Medical PACS Application...")

    app = QApplication(sys.argv)
    app.setApplicationName("Medical PACS System")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Medical Solutions Inc.")

    try:
        setup_application()

        print("Initializing services...")
        auth_controller = Container.get_auth_controller()

        print("Opening login window...")
        login_window = LoginView(auth_controller)
        login_window.show()

        session_timer = QTimer()
        session_timer.timeout.connect(log_session_info)
        session_timer.start(10000)

        print("Application started successfully")

        sys.exit(app.exec())

    except Exception as e:
        print(f"Fatal error starting application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()