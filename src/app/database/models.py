from datetime import datetime
import enum
from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class RoleEnum(enum.Enum):
    admin = "admin"
    doctor = "doctor"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    last_name = Column(String(255), nullable=False)
    first_name = Column(String(255), nullable=False)
    title = Column(String(100), nullable=True)

class PacsUrl(Base):
    __tablename__ = "pacs_urls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    url = Column(String(512), nullable=False)
    username = Column(String(100), nullable=True)
    password = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AppSettings(Base):
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    setting_key = Column(String(100), unique=True, nullable=False)
    setting_value = Column(String(500), nullable=True)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ReportTitle(Base):
    __tablename__ = "report_title"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title_text = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)