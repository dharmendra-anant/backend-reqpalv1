import asyncio
import logging

from fastapi import APIRouter, File, UploadFile

# from firebase_admin import storage, firestore
# from app.firebase.client import db, bucket

from app.agents.resume_processor import JobDescription, Resume, ResumeProcessorAgent
from app.models.resume_score import ResumeScoreConsolidated
# from app.firebase.upload_resume import upload_to_storage_if_not_exists

from app.utils.hash_utils import hash_file_content

router = APIRouter(prefix="/resume-filter", tags=["resume-filter"])

logger = logging.getLogger(__name__)

@router.post("/process")
async def filter_resume(
    job_description: UploadFile = File(...),
    resumes: list[UploadFile] = File(...),
) -> list[ResumeScoreConsolidated]:
    logger.debug("Started processing")
    jd_doc = JobDescription(file=job_description)
    await jd_doc.load()

    jd_hash = hash_file_content(jd_doc.content.encode("utf-8"))
    logger.debug("Job description loaded")

    processor = ResumeProcessorAgent()
    logger.debug("Processor initialized")

    # Create Resume objects
    resume_docs = [Resume(file=resume) for resume in resumes]

    # Load resumes concurrently
    await asyncio.gather(*[resume.load() for resume in resume_docs])

    async def process_resume(resume_doc: Resume, resume_file: UploadFile):
        resume_hash = hash_file_content(resume_doc.content.encode("utf-8"))
        score_key = f"{resume_hash}_{jd_hash}"

        logger.debug(f"⏳ Cache miss for {score_key}, scoring...")

        result = (await processor.execute(resumes=[resume_doc], job_description=jd_doc))[0]
        result.id = resume_hash
        result.name = resume_file.filename

        return result

    # Process all resumes concurrently
    results = await asyncio.gather(
        *[process_resume(resume_doc, resume_file) for resume_doc, resume_file in zip(resume_docs, resumes)]
    )

    return results

@router.post("/job-description")
async def create_job_description(file: UploadFile = File(...)) -> dict[str, str]:
    job_description = JobDescription(file=file)
    await job_description.load()
    logger.info(f"Job description: {job_description.file_path}")
    return {"message": "Job description created"}


@router.post("/resume")
async def create_resume(file: UploadFile = File(...)) -> dict[str, str]:
    resume = Resume(file=file)
    await resume.load()
    logger.info(f"Resume: {resume.file_path}")
    return {"message": "Resume received"}
