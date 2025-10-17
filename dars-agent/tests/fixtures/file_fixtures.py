"""File upload and file-related fixtures for testing."""
from __future__ import annotations

import base64
from typing import Dict, Optional
from tests.fixtures.factories import DataFactory


def file_upload_factory(
    filename: Optional[str] = None,
    content: Optional[bytes] = None,
    content_type: Optional[str] = None,
    **kwargs,
) -> Dict:
    """Create a mock file upload."""
    if filename is None:
        extensions = [".txt", ".py", ".json", ".csv", ".log", ".md"]
        filename = DataFactory.random_string(12) + DataFactory.random_choice(extensions)

    if content is None:
        content = DataFactory.random_string(500).encode("utf-8")

    if content_type is None:
        content_type_map = {
            ".txt": "text/plain",
            ".py": "text/x-python",
            ".json": "application/json",
            ".csv": "text/csv",
            ".log": "text/plain",
            ".md": "text/markdown",
            ".html": "text/html",
            ".js": "application/javascript",
            ".xml": "application/xml",
        }
        extension = filename[filename.rfind("."):] if "." in filename else ".txt"
        content_type = content_type_map.get(extension, "application/octet-stream")

    upload = {
        "filename": filename,
        "content": content,
        "content_type": content_type,
        "size": len(content),
        "uploaded_at": DataFactory.random_datetime().isoformat(),
        "uploaded_by": DataFactory.random_string(10),
    }

    upload.update(kwargs)
    return upload


def image_upload_factory(
    filename: Optional[str] = None,
    **kwargs,
) -> Dict:
    """Create a mock image upload."""
    if filename is None:
        extensions = [".jpg", ".png", ".gif", ".svg"]
        filename = DataFactory.random_string(12) + DataFactory.random_choice(extensions)

    # Generate fake image data (1x1 pixel placeholder)
    content = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )

    content_type_map = {
        ".jpg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
    }
    extension = filename[filename.rfind("."):]
    content_type = content_type_map.get(extension, "image/png")

    return file_upload_factory(
        filename=filename,
        content=content,
        content_type=content_type,
        **kwargs,
    )


def csv_file_factory(
    filename: Optional[str] = None,
    rows: int = 10,
    **kwargs,
) -> Dict:
    """Create a mock CSV file upload."""
    if filename is None:
        filename = DataFactory.random_string(12) + ".csv"

    # Generate CSV content
    headers = ["id", "name", "email", "status", "created_at"]
    csv_lines = [",".join(headers)]

    for i in range(rows):
        row = [
            str(i + 1),
            DataFactory.random_string(10),
            DataFactory.random_email(),
            DataFactory.random_choice(["active", "inactive"]),
            DataFactory.random_datetime().isoformat(),
        ]
        csv_lines.append(",".join(row))

    content = "\n".join(csv_lines).encode("utf-8")

    return file_upload_factory(
        filename=filename,
        content=content,
        content_type="text/csv",
        **kwargs,
    )


def json_file_factory(
    filename: Optional[str] = None,
    data: Optional[Dict] = None,
    **kwargs,
) -> Dict:
    """Create a mock JSON file upload."""
    if filename is None:
        filename = DataFactory.random_string(12) + ".json"

    if data is None:
        data = {
            "id": DataFactory.random_int(1, 1000),
            "name": DataFactory.random_string(15),
            "items": [
                {
                    "id": i,
                    "value": DataFactory.random_string(20),
                }
                for i in range(1, 6)
            ],
        }

    import json

    content = json.dumps(data, indent=2).encode("utf-8")

    return file_upload_factory(
        filename=filename,
        content=content,
        content_type="application/json",
        **kwargs,
    )


def log_file_factory(
    filename: Optional[str] = None,
    lines: int = 20,
    **kwargs,
) -> Dict:
    """Create a mock log file upload."""
    if filename is None:
        filename = DataFactory.random_string(12) + ".log"

    log_levels = ["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"]
    log_lines = []

    for _ in range(lines):
        timestamp = DataFactory.random_datetime().strftime("%Y-%m-%d %H:%M:%S")
        level = DataFactory.random_choice(log_levels)
        message = DataFactory.random_string(50)
        log_lines.append(f"{timestamp} [{level}] {message}")

    content = "\n".join(log_lines).encode("utf-8")

    return file_upload_factory(
        filename=filename,
        content=content,
        content_type="text/plain",
        **kwargs,
    )


def python_file_factory(
    filename: Optional[str] = None,
    **kwargs,
) -> Dict:
    """Create a mock Python file upload."""
    if filename is None:
        filename = DataFactory.random_string(12) + ".py"

    content = f'''"""Module docstring."""
from __future__ import annotations

from typing import List, Dict


class {DataFactory.random_string(10).capitalize()}:
    """Class for testing."""

    def __init__(self, name: str):
        self.name = name

    def process(self, data: List[Dict]) -> Dict:
        """Process some data."""
        result = {{"status": "success", "count": len(data)}}
        return result


def {DataFactory.random_string(10)}() -> str:
    """Test function."""
    return "{DataFactory.random_string(20)}"


if __name__ == "__main__":
    obj = {DataFactory.random_string(10).capitalize()}("test")
    print(obj.process([{{"id": 1}}]))
'''.encode("utf-8")

    return file_upload_factory(
        filename=filename,
        content=content,
        content_type="text/x-python",
        **kwargs,
    )


def patch_file_factory(
    filename: Optional[str] = None,
    **kwargs,
) -> Dict:
    """Create a mock patch/diff file."""
    if filename is None:
        filename = DataFactory.random_string(12) + ".patch"

    content = f'''--- a/src/module.py
+++ b/src/module.py
@@ -10,7 +10,7 @@ class Module:
         self.value = value

     def process(self):
-        return self.value
+        return self.value * 2

     def update(self, new_value):
         self.value = new_value
'''.encode("utf-8")

    return file_upload_factory(
        filename=filename,
        content=content,
        content_type="text/x-diff",
        **kwargs,
    )


# Predefined file fixtures
MOCK_FILE_UPLOADS = [
    {
        "filename": "test_data.csv",
        "content": b"id,name,value\n1,test1,100\n2,test2,200\n3,test3,300",
        "content_type": "text/csv",
        "size": 52,
        "uploaded_at": "2024-10-15T10:00:00Z",
        "uploaded_by": "test_user",
    },
    {
        "filename": "config.json",
        "content": b'{"setting1": "value1", "setting2": 42, "enabled": true}',
        "content_type": "application/json",
        "size": 57,
        "uploaded_at": "2024-10-16T14:30:00Z",
        "uploaded_by": "admin_user",
    },
    {
        "filename": "application.log",
        "content": b"2024-10-17 08:00:00 [INFO] Application started\n2024-10-17 08:00:05 [DEBUG] Loading configuration\n2024-10-17 08:00:10 [ERROR] Connection failed",
        "content_type": "text/plain",
        "size": 150,
        "uploaded_at": "2024-10-17T08:15:00Z",
        "uploaded_by": "system",
    },
]
