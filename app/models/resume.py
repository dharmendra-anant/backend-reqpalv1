from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


class PersonalDetails(BaseModel):
    """Basic personal information"""

    name: str
    location: str
    email: str
    phone: Optional[str] = None
    portfolio_url: Optional[HttpUrl] = None


class Education(BaseModel):
    """Educational background"""

    institution: str
    degree: str
    location: str
    graduation_date: str
    highlights: Optional[List[str]] = None


class CompanyInfo(BaseModel):
    """Company details"""

    name: str
    description: Optional[str] = None
    url: Optional[HttpUrl] = None
    funding_info: Optional[str] = None
    size_info: Optional[str] = None


class Experience(BaseModel):
    """Professional experience"""

    company: CompanyInfo
    title: str
    location: str
    start_date: str
    end_date: Optional[str] = Field(default="Present")
    highlights: List[str]
    core_thesis: Optional[str] = None
    seniority_level: Optional[str] = Field(
        description="Inferred seniority level based on title and responsibilities"
    )


class InfluentialContent(BaseModel):
    """Content that has influenced the person"""

    title: str
    url: Optional[HttpUrl] = None
    type: str = Field(description="Type of content (book, video, concept, etc.)")
    description: str
    impact_statement: Optional[str] = None


class Interest(BaseModel):
    """Personal and professional interests"""

    category: str
    description: str
    is_professional: bool = Field(
        description="Whether this is a professional or personal interest"
    )


class Investment(BaseModel):
    """Investment and advisory roles"""

    company_name: str
    company_url: Optional[HttpUrl] = None
    role: str
    investment_type: str
    company_achievements: Optional[List[str]] = None
    advisory_areas: Optional[List[str]] = None


class Skills(BaseModel):
    """Professional skills"""

    technical: List[str] = Field(default_factory=list)
    business: List[str] = Field(default_factory=list)
    leadership: List[str] = Field(default_factory=list)
    domain_knowledge: List[str] = Field(default_factory=list)


class ResumeModel(BaseModel):
    """Complete resume model"""

    personal_details: PersonalDetails
    education: List[Education]
    experiences: List[Experience]
    skills: Skills = Field(description="Both explicitly mentioned and derived skills")
    influential_content: Optional[List[InfluentialContent]] = None
    interests: Optional[List[Interest]] = None
    investments: Optional[List[Investment]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "personal_details": {
                    "name": "John Doe",
                    "location": "New York, USA",
                    "email": "john.doe@example.com",
                    "phone": "555-123-4567",
                    "portfolio_url": "http://example.com/portfolio",
                },
                "education": [
                    {
                        "institution": "University of California, Berkeley",
                        "degree": "Bachelor of Science in Computer Science",
                        "location": "Berkeley, CA",
                        "graduation_date": "2020",
                        "highlights": ["Dean's List", "Honor Society"],
                    }
                ],
                "experiences": [
                    {
                        "company": {
                            "name": "Tech Corp",
                            "description": "A leading tech company",
                            "url": "http://techcorp.com",
                            "funding_info": "$100M Series A",
                            "size_info": "1000 employees",
                        },
                        "title": "Software Engineer",
                        "location": "San Francisco, CA",
                        "start_date": "2018",
                        "end_date": "2022",
                        "highlights": ["Achieved 2x revenue growth", "Led team of 5"],
                    }
                ],
                "skills": {
                    "technical": ["Python", "SQL", "AWS"],
                    "business": ["Project Management", "Team Leadership"],
                    "leadership": ["Team Building", "Stakeholder Management"],
                    "domain_knowledge": ["AI", "Machine Learning", "Data Science"],
                },
                "influential_content": [
                    {
                        "title": "The Lean Startup",
                        "url": "https://theleanstartup.com",
                        "type": "book",
                        "description": "A book about building startups",
                        "impact_statement": "This book changed my life",
                    }
                ],
                "interests": [
                    {
                        "category": "Technology",
                        "description": "I love to code and build startups",
                        "is_professional": True,
                    }
                ],
                "investments": [
                    {
                        "company_name": "Tech Corp",
                        "company_url": "http://techcorp.com",
                        "role": "Investor",
                        "investment_type": "Venture Capital",
                        "company_achievements": ["Raised $100M Series A"],
                        "advisory_areas": ["AI", "Machine Learning"],
                    }
                ],
            }
        }
