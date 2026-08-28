import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    app_name: str = os.getenv("APP_NAME", "AI美学导师")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))

    llm_api_base: str = os.getenv("LLM_API_BASE", "https://api.openai.com/v1")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")

    vision_api_base: str = os.getenv("VISION_API_BASE", "https://api.openai.com/v1")
    vision_api_key: str = os.getenv("VISION_API_KEY", "")
    vision_model: str = os.getenv("VISION_MODEL", "gpt-4o")

    max_upload_size: int = int(os.getenv("MAX_UPLOAD_SIZE", str(20 * 1024 * 1024)))
    max_image_size: int = int(os.getenv("MAX_IMAGE_SIZE", str(10 * 1024 * 1024)))
    max_pdf_size: int = int(os.getenv("MAX_PDF_SIZE", str(50 * 1024 * 1024)))

    _backend_root: str = str(Path(__file__).resolve().parent.parent)
    _data_root: str = str(Path(_backend_root) / "data")

    data_dir: str = os.getenv("DATA_DIR", _data_root)
    temp_dir: str = os.getenv("TEMP_DIR", str(Path(_data_root) / "temp"))
    knowledge_base_dir: str = os.getenv("KNOWLEDGE_BASE_DIR", str(Path(_data_root) / "knowledge_base"))
    chroma_db_dir: str = os.getenv("CHROMA_DB_DIR", str(Path(_data_root) / "chroma_db"))

    allowed_image_types: list = ["image/jpeg", "image/png", "image/webp"]
    allowed_image_extensions: list = [".jpg", ".jpeg", ".png", ".webp"]
    allowed_document_types: list = ["application/pdf"]
    allowed_document_extensions: list = [".pdf"]

    cors_origins: list = ["*"]

    @property
    def mock_mode(self) -> bool:
        return not self.llm_api_key or self.llm_api_key.strip() == ""

    def ensure_directories(self):
        dirs = [
            self.data_dir,
            self.temp_dir,
            self.knowledge_base_dir,
            self.chroma_db_dir,
        ]
        for d in dirs:
            Path(d).mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()
