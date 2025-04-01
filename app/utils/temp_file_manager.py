import logging
import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator
from uuid import uuid4

from fastapi import UploadFile

logger = logging.getLogger(__name__)

# Default values
DEFAULT_ALLOWED_TYPES: set[str] = {".txt", ".md", ".rtf", ".pdf", ".doc", ".docx"}
DEFAULT_MAX_SIZE = 1024 * 1024  # 1mb in bytes


@asynccontextmanager
async def temporary_file_context_manager(
    file: UploadFile,
    allowed_types: set[str] = DEFAULT_ALLOWED_TYPES,
    max_size: int = DEFAULT_MAX_SIZE,
) -> AsyncGenerator[Path, None]:
    """Create a temporary file that's automatically cleaned up when done.

    Args:
        file: The uploaded file to process
        allowed_types: Set of allowed file extensions (default: DEFAULT_ALLOWED_TYPES)
        max_size: Maximum file size in bytes (default: DEFAULT_MAX_SIZE)

    Raises:
        ValueError: If file type is not allowed or file size exceeds limit
    """
    # Validate file type
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_types:
        raise ValueError(
            f"Unsupported file type. Allowed types: {', '.join(allowed_types)}"
        )

    temp_dir = tempfile.gettempdir()
    temp_file_path = os.path.join(temp_dir, f"upload_{uuid4().hex}_{file.filename}")

    try:
        # Read entire file content
        content = await file.read()
        if len(content) > max_size:
            raise ValueError(
                f"File size exceeds maximum limit of {max_size/1024/1024:.1f}MB"
            )

        # Write to temporary file
        with open(temp_file_path, "wb") as f:
            f.write(content)

        yield Path(temp_file_path)
    finally:
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
            logger.debug(f"Cleaned up temporary file: {temp_file_path}")
