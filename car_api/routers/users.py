from typing import Optional

from fastapi import APIRouter, status, HTTPException, Query, Depends
from sqlalchemy import select, exists
from sqlalchemy.ext.asyncio import AsyncSession

from car_api.core.database import get_session
from car_api.core.security import get_password_hash
from car_api.db import USERS
from car_api.models.users import User
from car_api.schemas.users import (
    UserSchema,
    UserPublicSchema,
    UserListPublicSchema,
    UserUpdateSchema,
)

router = APIRouter()

@router.post(
    path='/',
    status_code=status.HTTP_201_CREATED,
    response_model=UserPublicSchema,
    summary='Criar novo usuário'
)
async def create_user(
    user: UserSchema,
    db: AsyncSession = Depends(get_session),
):
    username_exists = await db.scalar(
        select(exists().where(User.username == user.username))
    )
    if username_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Username já está em uso.',
        )

    email_exists = await db.scalar(
        select(exists().where(User.email == user.email))
    )
    if email_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='O email já está em uso.'
        )
    
    db_user = User(
        username=user.username,
        email=user.email,
        password=get_password_hash(user.password),
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user


@router.get(
    path='/',
    status_code=status.HTTP_200_OK,
    response_model=UserListPublicSchema,
    summary='Listar usuários'
)
async def list_users(
    offset: int = Query(0, ge=0, description='Número de registro para pular'),
    limit: int = Query(100, ge=1, le=100, description='Limite de registros'),
    search: Optional[str] = Query(None, description='Buscar por username ou email'),
    db: AsyncSession = Depends(get_session)
):
    query = select(User)

    if search:
        search_filter = f'%{search}%'
        query = query.where(
            (User.username.ilike(search_filter))
            | (User.email.ilike(search_filter))
        )

    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    users = result.scalars().all()
    
    return {'users': users, 'offset': offset, 'limit': limit}


@router.get(
        path='/{user_id}',
        status_code=status.HTTP_200_OK,
        response_model=UserPublicSchema,
        summary='Busca de usuário por ID',
)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_session),
):
    user = await db.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Usuário não encontrado',
        )

    return user


@router.put(
    path='/{user_id}',
    status_code=status.HTTP_201_CREATED,
    response_model=UserPublicSchema,
)
async def update_put_user(user_id: int, user: UserSchema):
    user_with_id = UserPublicSchema(**user.model_dump(), id=user_id)
    USERS[user_id - 1] = user_with_id
    return user_with_id


@router.delete(
    path='/{user_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Deletar usuário',
)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_session),
):
    user = await db.get(User, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Id de usuário não encontrado.'
        )

    await db.delete(user)
    await db.commit()

    return
