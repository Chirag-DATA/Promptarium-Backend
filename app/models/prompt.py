from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import Column, JSON, Text
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.user import User


class Prompt(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    prompt_text: str = Field(sa_column=Column(Text))
    category: str
    tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    description: Optional[str] = Field(default="", sa_column=Column(Text))
    ai_model: str = Field(default="Other")

    is_favorite: bool = Field(default=False)
    is_pinned: bool = Field(default=False)
    is_archived: bool = Field(default=False)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    owner_id: Optional[int] = Field(default=None, foreign_key="user.id")
    owner: Optional["User"] = Relationship(back_populates="prompts")