import os


class Settings:
    # Database settings
    DB_URI = "mysql+pymysql://root:admin@localhost:3306/medical_app"

    # Default PACS settings
    PACS_URL = "http://localhost:8042"
    PACS_AUTH = ("orthanc", "orthanc")
    PACS_URL_2 = "http://localhost:8052"
    PACS_AUTH_2 = ("orthanc", "orthanc")

    # File paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    STYLE_PATH = os.path.join(BASE_DIR, "app", "presentation", "styles", "style.qss")
    PDF_CSS_PATH = os.path.join(BASE_DIR, "app", "presentation", "styles", "pdf_style.css")
    HEADER_IMAGE_PATH = os.path.join(BASE_DIR, "app", "assets", "header_spital.png")

    # PDF settings
    PDF_OUTPUT_DIR = "generated_pdfs"
    PDF_PREVIEW_DIR = "tmp_pdfs"

    # Local DICOM file settings
    LOCAL_STUDIES_CACHE_DIR = "local_studies_cache"
    SUPPORTED_DICOM_EXTENSIONS = ['.dcm', '.dicom', '.dic']

    @classmethod
    def get_source_pacs_config(cls):
        try:
            from app.di.container import Container
            settings_service = Container.get_settings_service()
            config = settings_service.get_source_pacs_config()
            if config:
                return config
        except Exception as e:
            print(f"Warning: Could not load source PACS config from database: {e}")

        return cls.PACS_URL, cls.PACS_AUTH

    @classmethod
    def get_target_pacs_config(cls):
        try:
            from app.di.container import Container
            settings_service = Container.get_settings_service()
            config = settings_service.get_target_pacs_config()
            if config:
                return config
        except Exception as e:
            print(f"Warning: Could not load target PACS config from database: {e}")

        # Fallback to secondary PACS
        return cls.PACS_URL_2, cls.PACS_AUTH_2

    @classmethod
    def get_pacs_config(cls):
        return cls.get_source_pacs_config()
