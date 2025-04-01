from fastapi import APIRouter

from app.api.v1.routes import resume_filter

# Main v1 API router
router = APIRouter(prefix="/v1")

# Include all route modules
router.include_router(resume_filter.router)
