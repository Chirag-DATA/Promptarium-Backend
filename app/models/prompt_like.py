from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field, UniqueConstraint


class PromptLike(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("user_id", "prompt_id", name="unique_user_prompt_like"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    prompt_id: int = Field(foreign_key="prompt.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))