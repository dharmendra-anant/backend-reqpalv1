import asyncio
import logging
from pathlib import Path

from app.documents.job_description import JobDescription
from app.documents.resume import Resume
from app.models.resume_score import ResumeScoreConsolidated
from app.tools.resume_scorer import ResumeScorer

logger = logging.getLogger(__name__)


class ResumeProcessorAgent:
    def __init__(self, test_mode: bool = False) -> None:
        self.test_mode = test_mode

    async def execute(
        self,
        resumes: list[Resume] | None = None,
        job_description: JobDescription | None = None,
        verbose: bool = False,
    ) -> list[ResumeScoreConsolidated]:
        if self.test_mode:
            resume = Resume(file_path=Path("scratch/resume.pdf"))
            job_description = JobDescription(
                file_path=Path("scratch/job_description.md")
            )
            return await self.score_resume(resume, job_description)

        tasks = [
            asyncio.create_task(self.score_resume(resume, job_description))
            for resume in resumes
            if resume is not None
        ]

        scores = await asyncio.gather(*tasks)

        # score = await self.score_resume(resume, job_description)
        logger.debug(
            "Resume Score",
            extra={
                "context": {
                    **(
                        {
                            "#resumes": len(resumes),
                            "job_description": job_description[:100],
                        }
                        if verbose
                        else {}
                    ),
                    "#scores": len(scores),
                }
            },
        )
        return scores

    async def score_resume(
        self, resume: Resume, job_description: JobDescription
    ) -> ResumeScoreConsolidated:
        # score resume using resume scorer
        scorer = ResumeScorer()
        return await scorer.score_resume(resume, job_description, explain=True)
