from typing import Optional


class Validators:
    @staticmethod
    def validate_username(username: str) -> Optional[str]:
        if not username:
            return "Username is required"
        if len(username) < 3:
            return "Username must be at least 3 characters long"
        if len(username) > 50:
            return "Username must be less than 50 characters"
        return None

    @staticmethod
    def validate_password(password: str) -> Optional[str]:
        if not password:
            return "Password is required"
        return None

    @staticmethod
    def validate_name(name: str, field_name: str) -> Optional[str]:
        if name and len(name.strip()) > 0:
            if len(name.strip()) > 100:
                return f"{field_name} trebuie să aibă mai puțin de 100 de caractere"
        return None