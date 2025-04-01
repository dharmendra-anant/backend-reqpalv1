from abc import ABC, abstractmethod
from pathlib import Path

from fastapi import UploadFile
from pydantic import BaseModel

from app.tools.pdf_extractor import PDFExtractor
from app.utils.temp_file_manager import temporary_file_context_manager


class DocumentBase(BaseModel, ABC):
    _content: str | None = None
    file_path: Path | None = None
    file: UploadFile | None = None
    _is_loaded: bool = False

    @property
    def content(self) -> str:
        if not self._is_loaded:
            raise ValueError(
                f"{self.__class__.__name__} must be loaded before accessing content"
            )
        if self._content is None:
            raise ValueError(
                f"{self.__class__.__name__} content is None despite being loaded"
            )
        return self._content

    @content.setter
    def content(self, value: str | None) -> None:
        self._content = value

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    async def load(self) -> None:
        if self._is_loaded:
            return

        if self.file:
            print("Loading file")
            async with temporary_file_context_manager(self.file) as temp_path:
                self.file_path = temp_path
                self._content = self._load_file_content(temp_path.suffix.lower())
        elif self.file_path:
            self._content = self._load_file_content(self.file_path.suffix.lower())
        else:
            self._content = await self._load_alternative()

        if not self._content:
            raise ValueError(f"Failed to load {self.__class__.__name__} content")

        self._is_loaded = True

    def _load_file_content(self, file_type: str) -> str:
        """Load content from a file based on its type."""
        if file_type == ".pdf":
            return self._load_pdf()
        elif file_type in (".txt", ".md", ".rtf"):
            return self._load_txt()
        else:
            raise ValueError("Unsupported file type")

    def _load_txt(self) -> str:
        """Read content from a text file."""
        with open(self.file_path, "r") as f:
            return f.read()

    def _load_pdf(self) -> str:
        """Extract content from a PDF file."""
        pdf_extractor = PDFExtractor()
        content = pdf_extractor.extract_content(self.file_path, debug=False)
        return "\n".join(content.text)

    @abstractmethod
    async def _load_alternative(self) -> str:
        """Load content when no file is provided."""
        pass

    def __repr__(self) -> str:
        content_preview = self.content[:50] + "..." if self.content else None
        file_path_str = str(self.file_path) if self.file_path else None
        return f"{self.__class__.__name__}(content={content_preview}, file_path={file_path_str})"
