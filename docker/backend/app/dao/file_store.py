import os
import uuid
import shutil

BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "files")


def save_file(file_content: bytes, original_filename: str) -> str:
    os.makedirs(BASE_DIR, exist_ok=True)
    ext = os.path.splitext(original_filename)[1]
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(BASE_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(file_content)
    return filepath


def read_file(filepath: str) -> bytes:
    with open(filepath, "rb") as f:
        return f.read()


def delete_file(filepath: str) -> None:
    if os.path.exists(filepath):
        os.remove(filepath)


def get_file_size(filepath: str) -> int:
    return os.path.getsize(filepath) if os.path.exists(filepath) else 0
