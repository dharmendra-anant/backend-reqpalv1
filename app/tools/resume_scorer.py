import asyncio
import logging
import re
from typing import Optional

import numpy as np

from app.documents.job_description import JobDescription
from app.documents.resume import Resume
from app.intelligence.client import LLMClient, Models
from app.models.resume_score import (
    ResumeScoreConsolidated,
    Score,
    ScoreExplained,
)

logger = logging.getLogger(__name__)


class ResumeScorer:
    """
    Scores a resume against a job description using OpenAI's models.

    Scoring scale:
    - 9-10: Top 10th percentile candidate
    - 7-8.9: Above average candidate
    - <7: Bottom 50th percentile candidate
    """

    def __init__(
        self, model: Models = Models.GPT4o, temperature: float = 0, debug: bool = False
    ) -> None:
        """
        Initialize the ResumeScorer with configurable model and temperature.

        Args:
            model: The OpenAI model to use for scoring
            temperature: The temperature setting for API calls
        """
        self.model = model
        self.temperature = temperature
        self.system_prompt = "You are an expert very strict Recruiter."
        self.client = LLMClient(debug=debug)
        self.debug = debug

    async def score_resume(
        self,
        resume: Resume,
        job_description: JobDescription,
        skill: Optional[str] = None,
        explain: bool = False,
    ) -> ResumeScoreConsolidated:
        """
        Score the resume against the job description.

        Args:
            resume_text: String content of the resume
            job_desc_text: String content of the job description
            skill: Optional skill to emphasize in the scoring
            explain: Whether to return detailed explanation with scores

        Returns:
            A ResumeScore or ResumeScoreExplained object containing the scores
        """
        resume_text = self._get_resume_content(resume)
        job_desc_text = self._get_job_desc_content(job_description)
        tasks = [
            asyncio.create_task(
                self.generate_ai_score(resume_text, job_desc_text, explain, skill)
            ),
            asyncio.create_task(
                self.generate_ats_score(resume_text, job_desc_text, explain, skill)
            ),
        ]
        ai_score, ats_score = await asyncio.gather(*tasks)

        if explain:
            # Ensure both scores are ScoreExplained objects
            if not isinstance(ats_score, ScoreExplained):
                ats_score = ScoreExplained(
                    score=ats_score, explanation=f"ATS score is {ats_score}"
                )
            return ResumeScoreConsolidated(ai_score=ai_score, ats_score=ats_score)
        return ResumeScoreConsolidated(ai_score=ai_score, ats_score=ats_score)

    async def generate_ats_score(
        self,
        resume_text: str,
        job_desc_text: str,
        explain: bool,
        skill: Optional[str] = None,
    ) -> Score | ScoreExplained:
        # generate embeddings for resume and job description
        tasks = [
            asyncio.create_task(self.client.generate_embedding(resume_text)),
            asyncio.create_task(self.client.generate_embedding(job_desc_text)),
        ]

        # get embeddings
        resume_embedding, job_desc_embedding = await asyncio.gather(*tasks)

        # convert to np array
        resume_embedding = np.array(resume_embedding)
        job_desc_embedding = np.array(job_desc_embedding)

        # calculate cosine similarity
        cosine_similarity = np.dot(resume_embedding, job_desc_embedding) / (
            np.linalg.norm(resume_embedding) * np.linalg.norm(job_desc_embedding)
        )
        ats_score = round(cosine_similarity * 100, 2)

        if explain:
            return ScoreExplained(
                score=ats_score,
                explanation=f"ATS score is {ats_score}",
            )

        return Score(score=ats_score)

    async def generate_ai_score(
        self,
        resume_text: str,
        job_desc_text: str,
        explain: bool,
        skill: Optional[str] = None,
        normalize: bool = False,
    ) -> Score | ScoreExplained:
        prompt = self._build_scoring_prompt(resume_text, job_desc_text, explain, skill)

        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ]
            _, response_text = await self.client.generate_response(
                messages=messages,
                model=self.model,
                temperature=self.temperature,
            )
            score = await self._parse_score_from_response(response_text, explain)
            if normalize:
                return round(score * 10, 2)
            else:
                return score
        except Exception as e:
            logger.error(f"Error scoring resume: {e}")
            raise

    def _get_resume_content(self, resume: Resume) -> str:
        # can be extended to handle structured data
        return resume.content

    def _get_job_desc_content(self, job_desc: JobDescription) -> str:
        # can be extended to handle structured data
        return job_desc.content

    def _build_scoring_prompt(
        self,
        resume_text: str,
        job_desc_text: str,
        explain: bool,
        skill: Optional[str] = None,
    ) -> str:
        """
        Build the prompt to send to OpenAI API.

        Args:
            resume_text: String content of the resume
            job_desc_text: String content of the job description
            skill: Optional skill to emphasize in the scoring

        Returns:
            The formatted prompt string
        """
        base_prompt = (
            f"Job Description:\n{job_desc_text}\n\n"
            f"Resume:\n{resume_text}\n\n"
            # f"Please provide only a score between 1 and 10 (decimals allowed) that indicates how well the resume"
            f"Please provide only a score between 1 and 100 that indicates how well the resume"
        )

        if skill:
            constructed_prompt = f'{base_prompt} matches the job description, with a particular emphasis on the skill "{skill}".'
        else:
            constructed_prompt = f"{base_prompt} matches the job description."

        if explain:
            return (
                f"{constructed_prompt} Please explain the reason you deducted points."
            )
        else:
            return constructed_prompt

    async def _parse_score_from_response(
        self, response_text: str, explain: bool
    ) -> Score | ScoreExplained:
        """
        Extract a numerical score from the API response text.

        Args:
            response_text: The API response content

        Returns:
            The parsed score as a float

        Raises:
            ValueError: If no numerical score can be extracted
        """
        if explain:
            logger.debug("Getting score with explanation")
            resume_score = await self.client.extract_structured_data(
                messages=[
                    {"role": "user", "content": response_text},
                ],
                schema=ScoreExplained,
            )
            if self.debug:
                logger.debug(f"Resume score: {resume_score}")
            return resume_score
        try:
            # First try direct conversion
            float_score = float(response_text)
            return Score(score=float_score)
        except ValueError:
            # Try to extract a number using regex if the output isn't a plain number
            match = re.search(r"(\d+(\.\d+)?)", response_text)
            if match:
                float_score = float(match.group(1))
                return Score(score=float_score)
            else:
                error_msg = f"Could not parse a numerical score from the response: {response_text}"
                logger.error(error_msg)
                raise ValueError(error_msg)


# Convenience function to maintain backward compatibility
async def score_resume(
    resume_text: str, job_desc_text: str, skill: Optional[str] = None
) -> float:
    """
    Score the resume against the job description.

    Args:
        resume_text: String for the resume
        job_desc_text: String for the job description
        skill: Optional skill to emphasize

    Returns:
        A float score between 1 and 10 indicating matchability
    """
    scorer = ResumeScorer()
    return await scorer.score_resume(resume_text, job_desc_text, skill)
