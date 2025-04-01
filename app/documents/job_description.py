from app.documents.base import DocumentBase
from app.intelligence.client import LLMClient


class JobDescription(DocumentBase):
    job_title: str | None = None

    async def _load_alternative(self) -> str:
        if not self.job_title:
            raise ValueError("Job title is required when generating description")

        llm_client = LLMClient(debug=True)
        messages = [
            {
                "role": "system",
                "content": "You are a job description generator. You will be given a job title and you will need to generate a job description for the job title.",
            },
            {"role": "user", "content": f"Job Title: {self.job_title}"},
        ]
        _, content = await llm_client.generate_response(messages)
        return content
