import hashlib
from pathlib import Path
from typing import List, Tuple

from models import Meeting
from database import meeting_exists_by_checksum


def scan_folder(folder_path: str) -> Tuple[List[Path], List[Path]]:
    folder = Path(folder_path)
    if not folder.is_dir():
        print(f"Error: {folder_path} is not a valid directory")
        return [], []

    new_files = []
    modified_files = []

    for f in sorted(folder.iterdir()):
        if f.suffix.lower() in (".txt", ".vtt") and f.is_file():
            checksum = compute_checksum(f)
            existing_id = meeting_exists_by_checksum(checksum)
            title = f.stem

            if existing_id is None:
                new_files.append(f)
            else:
                modified_files.append(f)

    return new_files, modified_files


def compute_checksum(filepath: Path) -> str:
    hasher = hashlib.sha256()
    hasher.update(filepath.read_bytes())
    return hasher.hexdigest()


def read_file(filepath: Path) -> str:
    return filepath.read_text(encoding="utf-8-sig")
