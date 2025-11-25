import os
from typing import Dict, Any
from datetime import datetime
from app.core.interfaces.pdf_interface import IPdfService
from app.infrastructure.pdf_generator import PdfGenerator
from app.core.exceptions.pdf_exceptions import PdfGenerationError


class PdfService(IPdfService):
    def __init__(self, pdf_generator: PdfGenerator, output_dir: str = "generated_pdfs"):
        self._pdf_generator = pdf_generator
        self._output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_pdf(self, content: str, metadata: Dict[str, Any], output_path: str, doctor_name: str = None,
                 selected_title: str = None, header_image_path: str = None) -> str:
        try:
            self._pdf_generator.create_pdf(content, metadata, output_path, doctor_name, selected_title, header_image_path)
            return output_path
        except Exception as e:
            raise PdfGenerationError(f"Nu am putut genera fisierul PDF: {e}")

    def preview_pdf(self, content: str, metadata: Dict[str, Any], doctor_name: str = None,
                    selected_title: str = None, header_image_path: str = None) -> str:
        try:
            preview_dir = os.path.join("tmp_pdfs", "preview")
            os.makedirs(preview_dir, exist_ok=True)

            filename = f"preview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            preview_path = os.path.join(preview_dir, filename)

            self._pdf_generator.create_pdf(content, metadata, preview_path, doctor_name, selected_title, header_image_path)
            return preview_path
        except Exception as e:
            raise PdfGenerationError(f"Nu am putut genera fisierul PDF pentru previzualizare: {e}")