import re

import openai
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer

# Load the free embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Initialize Qdrant in-memory
client = QdrantClient(":memory:")


def score_resume(resume_text: str, job_desc_text: str, skill: str = None) -> float:
    """
    Score the resume against the job description. If a skill is provided, score with an emphasis on that skill.

    :param resume_text: String for the resume.
    :param job_desc: String for the job description.
    :param skill: Optional skill to emphasize.
    :return: A float score between 1 and 10 indicating matchability.
    """
    # Extract text from both PDFs
    resume_text = resume_text
    job_desc_text = job_desc_text

    # Construct the prompt based on whether a skill is provided
    if skill:
        prompt = (
            f"Job Description:\n{job_desc_text}\n\n"
            f"Resume:\n{resume_text}\n\n"
            f"Please provide only a score between 1 and 10 (decimals allowed) that indicates how well the resume "
            f'matches the job description, with a particular emphasis on the skill "{skill}".'
        )
    else:
        prompt = (
            f"Job Description:\n{job_desc_text}\n\n"
            f"Resume:\n{resume_text}\n\n"
            f"Please provide only a score between 1 and 10 (decimals allowed) that indicates how well the resume "
            f"matches the job description."
        )

    # Call the OpenAI API with the prompt
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an expert very strict Recruiter."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )

    # Extract the score from the API response
    score_text = response.choices[0].message.content
    try:
        score = float(score_text)
    except ValueError:
        # Try to extract a number using regex if the output isn't a plain number
        match = re.search(r"(\d+(\.\d+)?)", score_text)
        if match:
            score = float(match.group(1))
        else:
            raise ValueError(
                "Could not parse a numerical score from the response: " + score_text
            )
    return score


def ats_score_resume(resume_text: str, job_description_text: str) -> float:
    """
    Generate a similarity score between a resume and a job description.
    The score is based on cosine similarity between their embeddings.

    Args:
        resume_text (str): The text of the resume.
        job_description_text (str): The text of the job description.

    Returns:
        float: Similarity score (closer to 1 indicates a higher match).
    """
    # Generate embeddings for both texts
    resume_vector = model.encode(resume_text).tolist()
    jd_vector = model.encode(job_description_text).tolist()

    # Determine the dimension of the embedding
    dimension = len(jd_vector)
    collection_name = "temp_collection"

    # Recreate the collection in Qdrant (ensuring a clean slate each time)
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
    )

    # Insert the job description embedding as a point into Qdrant
    client.upsert(
        collection_name=collection_name,
        points=[
            PointStruct(id=1, vector=jd_vector, payload={"type": "job_description"})
        ],
    )

    # Use the resume embedding as a query to search in Qdrant
    search_result = client.search(
        collection_name=collection_name, query_vector=resume_vector, limit=1
    )

    # Extract and return the cosine similarity score from the search result
    score = search_result[0].score * 10
    return score
