from dataclasses import dataclass
from enum import Enum
from typing import Optional


class UserRole(Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"


@dataclass
class User:
    id: int
    username: str
    password: str
    role: UserRole
    first_name: str
    last_name: str
    title: Optional[str] = None

    def has_admin_privileges(self) -> bool:
        return self.role == UserRole.ADMIN

    def can_access_pacs(self) -> bool:
        return self.role in [UserRole.ADMIN, UserRole.DOCTOR]

    def get_full_name(self) -> str:
        return f"{self.last_name} {self.first_name}"

    def get_full_name_with_title(self) -> str:
        if self.title and self.role == UserRole.DOCTOR:
            return f"{self.title} {self.first_name} {self.last_name.upper()}"
        return f"{self.first_name} {self.last_name.upper()}"
