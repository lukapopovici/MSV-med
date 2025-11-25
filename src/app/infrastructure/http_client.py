import requests
from typing import Optional, Dict, Any
from app.core.exceptions.pacs_exceptions import PacsConnectionError


class HttpClient:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def get(self, url: str, auth: Optional[tuple] = None, headers: Optional[Dict[str, str]] = None):
        try:
            response = requests.get(url, auth=auth, headers=headers, timeout=self.timeout)
            self._validate_response(response)
            return response
        except requests.exceptions.RequestException as e:
            raise PacsConnectionError(f"HTTP GET failed: {e}")

    def post(self, url: str, data: Any = None, auth: Optional[tuple] = None, headers: Optional[Dict[str, str]] = None):
        try:
            response = requests.post(url, data=data, auth=auth, headers=headers, timeout=self.timeout)
            self._validate_response(response)
            return response
        except requests.exceptions.RequestException as e:
            raise PacsConnectionError(f"HTTP POST failed: {e}")

    def delete(self, url: str, auth: Optional[tuple] = None, headers: Optional[Dict[str, str]] = None):
        try:
            response = requests.delete(url, auth=auth, headers=headers, timeout=self.timeout)
            self._validate_response(response)
            return response
        except requests.exceptions.RequestException as e:
            raise PacsConnectionError(f"HTTP DELETE failed: {e}")

    def _validate_response(self, response):
        if response.status_code == 200:
            return
        elif response.status_code == 400:
            raise ValueError("Bad Request (400)")
        elif response.status_code == 401:
            raise PermissionError("Unauthorized (401)")
        elif response.status_code == 403:
            raise PermissionError("Forbidden (403)")
        elif response.status_code == 404:
            raise FileNotFoundError("Not Found (404)")
        elif response.status_code == 500:
            raise RuntimeError("Internal Server Error (500)")
        elif response.status_code == 503:
            raise RuntimeError("Service Unavailable (503)")
        else:
            raise RuntimeError(f"Unexpected error: {response.status_code}")