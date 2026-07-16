from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class PromptCreate(BaseModel):
    title: str
    prompt_text: str
    category: str
    tags: List[str] = []
    description: Optional[str] = ""
    ai_model: str = "Other"


class PromptUpdate(BaseModel):
    title: Optional[str] = None
    prompt_text: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    description: Optional[str] = None
    ai_model: Optional[str] = None
    is_favorite: Optional[bool] = None
    is_pinned: Optional[bool] = None
    is_archived: Optional[bool] = None


class PromptRead(BaseModel):
    id: int
    title: str
    prompt_text: str
    category: str
    tags: List[str]
    description: Optional[str]
    ai_model: str
    is_favorite: bool
    is_pinned: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    owner_id: int

    class Config:
        from_attributes = True