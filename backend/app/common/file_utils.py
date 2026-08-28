import os
import uuid
from pathlib import Path
from datetime import datetime
from fastapi import UploadFile
from app.config import settings


def get_temp_dir() -> str:
    temp_dir = settings.temp_dir
    Path(temp_dir).mkdir(parents=True, exist_ok=True)
    return temp_dir


def save_upload_to_temp(file: UploadFile, sub_dir: str = "") -> str:
    temp_base = get_temp_dir()
    if sub_dir:
        target_dir = os.path.join(temp_base, sub_dir)
    else:
        target_dir = temp_base
    Path(target_dir).mkdir(parents=True, exist_ok=True)

    original_name = file.filename or "upload"
    ext = Path(original_name).suffix
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    safe_name = f"{timestamp}_{unique_id}{ext}"
    file_path = os.path.join(target_dir, safe_name)

    content = file.file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    file.file.seek(0)
    return file_path


def cleanup_temp_file(file_path: str) -> bool:
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception:
        pass
    return False


def get_file_extension(filename: str) -> str:
    return Path(filename).suffix.lower() if filename else ""


def is_allowed_image(filename: str) -> bool:
    ext = get_file_extension(filename)
    return ext in settings.allowed_image_extensions


def is_allowed_document(filename: str) -> bool:
    ext = get_file_extension(filename)
    return ext in settings.allowed_document_extensions
