from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func

from app.auth.dependencies import get_current_user, get_optional_user
from app.database import get_session
from app.models.prompt import Prompt
from app.models.prompt_like import PromptLike
from app.models.user import User
from app.schemas.prompt import LikeResponse, PromptCreate, PromptRead, PromptUpdate, PublicPromptRead

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


@router.get("/public", response_model=List[PublicPromptRead])
def list_public_prompts(
    skip: int = 0,
    limit: int = 20,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_user),
):
    prompts = session.exec(
        select(Prompt)
        .where(Prompt.is_public == True, Prompt.is_archived == False)
        .order_by(Prompt.created_at.desc())
        .offset(skip)
        .limit(limit)
    ).all()

    results = []
    for prompt in prompts:
        author = session.get(User, prompt.owner_id)

        like_count = session.exec(
            select(func.count()).select_from(PromptLike).where(PromptLike.prompt_id == prompt.id)
        ).one()

        is_liked = False
        if current_user:
            existing_like = session.exec(
                select(PromptLike).where(
                    PromptLike.prompt_id == prompt.id,
                    PromptLike.user_id == current_user.id,
                )
            ).first()
            is_liked = existing_like is not None

        results.append(
            PublicPromptRead(
                id=prompt.id,
                title=prompt.title,
                prompt_text=prompt.prompt_text,
                category=prompt.category,
                tags=prompt.tags,
                ai_model=prompt.ai_model,
                created_at=prompt.created_at,
                author_username=author.username if author else None,
                author_photo=author.profile_image_url if author else None,
                like_count=like_count,
                is_liked=is_liked,
            )
        )

    return results


@router.post("/{prompt_id}/like", response_model=LikeResponse)
def toggle_like(
    prompt_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    prompt = session.get(Prompt, prompt_id)

    if not prompt or not prompt.is_public:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found.")

    existing_like = session.exec(
        select(PromptLike).where(
            PromptLike.prompt_id == prompt_id,
            PromptLike.user_id == current_user.id,
        )
    ).first()

    if existing_like:
        session.delete(existing_like)
        session.commit()
        is_liked = False
    else:
        new_like = PromptLike(user_id=current_user.id, prompt_id=prompt_id)
        session.add(new_like)
        session.commit()
        is_liked = True

    like_count = session.exec(
        select(func.count()).select_from(PromptLike).where(PromptLike.prompt_id == prompt_id)
    ).one()

    return LikeResponse(like_count=like_count, is_liked=is_liked)


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