from abc import ABC, abstractmethod
from typing import Dict, Any


class IPdfService(ABC):
    @abstractmethod
    def generate_pdf(self, content: str, metadata: Dict[str, Any], output_path: str, doctor_name: str = None,
                     selected_title: str = None, header_image_path: str = None) -> str:
        pass

    @abstractmethod
    def preview_pdf(self, content: str, metadata: Dict[str, Any], doctor_name: str = None,
                    selected_title: str = None, header_image_path: str = None) -> str:
        pass
