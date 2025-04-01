from app.documents.base import DocumentBase
from app.models.resume import ResumeModel


class Resume(DocumentBase):
    schema_: type[ResumeModel] = ResumeModel

    async def _load_alternative(self) -> str:
        raise ValueError("Resume requires a file")
