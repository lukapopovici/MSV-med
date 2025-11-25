from typing import List, Optional, Tuple
from app.repositories.pacs_url_repository import PacsUrlRepository
from app.database.models import PacsUrl


class PacsUrlService:
    def __init__(self, pacs_url_repository: PacsUrlRepository):
        self._pacs_url_repository = pacs_url_repository

    def get_all_pacs_urls(self) -> List[PacsUrl]:
        return self._pacs_url_repository.find_all()

    def get_pacs_by_id(self, pacs_id: int) -> Optional[PacsUrl]:
        return self._pacs_url_repository.find_by_id(pacs_id)

    def get_pacs_config_by_id(self, pacs_id: int) -> Optional[Tuple[str, Tuple[str, str]]]:
        pacs = self.get_pacs_by_id(pacs_id)
        if pacs:
            return pacs.url, (pacs.username, pacs.password)
        return None

    def create_pacs_url(self, name: str, url: str, username: str, password: str) -> PacsUrl:
        if not all([name.strip(), url.strip(), username.strip(), password.strip()]):
            raise ValueError("All fields (name, url, username, password) are required")

        if not url.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")

        pacs_url = PacsUrl(
            name=name.strip(),
            url=url.strip().rstrip('/'),
            username=username.strip(),
            password=password.strip()
        )

        return self._pacs_url_repository.create(pacs_url)

    def update_pacs_url(self, pacs_id: int, name: str, url: str, username: str, password: str) -> bool:
        pacs_url = self._pacs_url_repository.find_by_id(pacs_id)
        if not pacs_url:
            return False

        if not all([name.strip(), url.strip(), username.strip(), password.strip()]):
            raise ValueError("All fields (name, url, username, password) are required")

        if not url.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")

        pacs_url.name = name.strip()
        pacs_url.url = url.strip().rstrip('/')
        pacs_url.username = username.strip()
        pacs_url.password = password.strip()

        self._pacs_url_repository.update(pacs_url)
        return True

    def delete_pacs_url(self, pacs_id: int) -> bool:
        pacs_url = self._pacs_url_repository.find_by_id(pacs_id)

        if not pacs_url:
            return False

        return self._pacs_url_repository.delete(pacs_id)

    def test_pacs_connection(self, pacs_id: int) -> bool:
        pacs_config = self.get_pacs_config_by_id(pacs_id)
        if not pacs_config:
            return False

        url, (username, password) = pacs_config

        try:
            from app.infrastructure.http_client import HttpClient
            client = HttpClient(timeout=10)
            response = client.get(f"{url}/system", auth=(username, password))
            return response.status_code == 200
        except Exception:
            return False

    def get_target_pacs_options(self) -> List[Tuple[int, str]]:
        all_pacs = self.get_all_pacs_urls()
        return [(pacs.id, f"{pacs.name} ({pacs.url})") for pacs in all_pacs]

    def validate_pacs_data(self, name: str, url: str, username: str, password: str) -> List[str]:
        errors = []

        if not name.strip():
            errors.append("Name is required")
        elif len(name.strip()) > 255:
            errors.append("Name must be less than 255 characters")

        if not url.strip():
            errors.append("URL is required")
        elif not url.startswith(('http://', 'https://')):
            errors.append("URL must start with http:// or https://")
        elif len(url.strip()) > 512:
            errors.append("URL must be less than 512 characters")

        if not username.strip():
            errors.append("Username is required")
        elif len(username.strip()) > 100:
            errors.append("Username must be less than 100 characters")

        if not password.strip():
            errors.append("Password is required")
        elif len(password.strip()) > 255:
            errors.append("Password must be less than 255 characters")

        return errors

    def get_pacs_statistics(self) -> dict:
        all_pacs = self.get_all_pacs_urls()
        return {
            'total_pacs': len(all_pacs)
        }
