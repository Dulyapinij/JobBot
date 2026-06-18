from pydantic import BaseModel
from typing import List, Optional

class CourseGrade(BaseModel):
    code: str
    title: str
    grade: str

class ChatRequest(BaseModel):
    question: str
    transcript_data: Optional[List[CourseGrade]] = []