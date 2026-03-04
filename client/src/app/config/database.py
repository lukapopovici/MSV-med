from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .settings import Settings


class DatabaseConfig:
    def __init__(self):
        self.settings = Settings()
        self.engine = create_engine(self.settings.DB_URI, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def get_session(self):
        return self.SessionLocal()