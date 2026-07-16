from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.auth.dependencies import get_current_user
from app.database import get_session
from app.models.prompt import Prompt
from app.models.user import User
from app.schemas.prompt import PromptCreate, PromptRead, PromptUpdate

router = APIRouter(prefix="/prompts", tags=["prompts"])


def get_owned_prompt_or_404(
    prompt_id: int, session: Session, current_user: User
) -> Prompt:
    prompt = session.get(Prompt, prompt_id)

    if not prompt or prompt.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt not found.",
        )

    return prompt


@router.post("/", response_model=PromptRead, status_code=status.HTTP_201_CREATED)
def create_prompt(
    prompt_data: PromptCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    new_prompt = Prompt(
        **prompt_data.model_dump(),
        owner_id=current_user.id,
    )

    session.add(new_prompt)
    session.commit()
    session.refresh(new_prompt)

    return new_prompt


@router.get("/", response_model=List[PromptRead])
def list_prompts(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    prompts = session.exec(
        select(Prompt).where(Prompt.owner_id == current_user.id)
    ).all()

    return prompts


@router.get("/{prompt_id}", response_model=PromptRead)
def get_prompt(
    prompt_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return get_owned_prompt_or_404(prompt_id, session, current_user)


@router.patch("/{prompt_id}", response_model=PromptRead)
def update_prompt(
    prompt_id: int,
    updates: PromptUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    prompt = get_owned_prompt_or_404(prompt_id, session, current_user)

    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(prompt, field, value)

    prompt.updated_at = datetime.now(timezone.utc)

    session.add(prompt)
    session.commit()
    session.refresh(prompt)

    return prompt


@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prompt(
    prompt_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    prompt = get_owned_prompt_or_404(prompt_id, session, current_user)

    session.delete(prompt)
    session.commit()