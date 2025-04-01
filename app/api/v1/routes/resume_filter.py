import asyncio
import logging

from fastapi import APIRouter, File, UploadFile

# from firebase_admin import storage, firestore
# from app.firebase.client import db, bucket

from app.agents.resume_processor import JobDescription, Resume, ResumeProcessorAgent
from app.models.resume_score import ResumeScoreConsolidated
from app.firebase.upload_resume import upload_to_storage_if_not_exists

from app.utils.hash_utils import hash_file_content

router = APIRouter(prefix="/resume-filter", tags=["resume-filter"])

logger = logging.getLogger(__name__)


# @router.post("/process")
# async def filter_resume(
#     job_description: UploadFile = File(...),
#     resumes: list[UploadFile] = File(...),
# ) -> list[ResumeScoreConsolidated]:
#     logger.debug("Started processing")
#     jd_doc = JobDescription(file=job_description)
#     await jd_doc.load()
#     logger.debug("Job description loaded")

#     # Create Resume objects and load them concurrently
#     resume_docs = [Resume(file=resume) for resume in resumes]
#     await asyncio.gather(*[resume.load() for resume in resume_docs])
#     logger.debug("Resumes loaded")

#     processor = ResumeProcessorAgent()
#     logger.debug("Processor initialized")
#     return await processor.execute(resumes=resume_docs, job_description=jd_doc)

@router.post("/process")
async def filter_resume(
    job_description: UploadFile = File(...),
    resumes: list[UploadFile] = File(...),
) -> list[ResumeScoreConsolidated]:
    logger.debug("Started processing")
    jd_doc = JobDescription(file=job_description)
    await jd_doc.load()

    jd_hash = hash_file_content(jd_doc.content.encode("utf-8"))
    # upload_to_storage_if_not_exists(f"job_descriptions/{jd_hash}/{job_description.filename}", jd_doc.content.encode("utf-8"))
    logger.debug("Job description loaded")

    processor = ResumeProcessorAgent()
    logger.debug("Processor initialized")

    results = []

    for resume_file in resumes:
        resume_doc = Resume(file=resume_file)
        await resume_doc.load()

        resume_hash = hash_file_content(resume_doc.content.encode("utf-8"))
        score_key = f"{resume_hash}_{jd_hash}"

        # doc_ref = db.collection("resume_scores").document(score_key)
        # cached_doc = doc_ref.get()

        # if cached_doc.exists:
        #     logger.debug(f"✅ Cache hit for {score_key}")
        #     score = ResumeScoreConsolidated(**cached_doc.to_dict())
        # else:
        if 1==1: # This will be removed once the firebase storage is fixed
            logger.debug(f"⏳ Cache miss for {score_key}, scoring...")

            # upload_to_storage_if_not_exists(
            #     f"resumes/{resume_hash}/{resume_file.filename}",
            #     resume_doc.content.encode("utf-8")
            # )
            result = (await processor.execute(resumes=[resume_doc], job_description=jd_doc))[0]

            result.id = resume_hash
            result.name = resume_file.filename

            # doc_ref.set(result.model_dump(by_alias=True))
            score = result

        results.append(score)

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
