from typing import Optional

from fastapi import APIRouter, status, HTTPException, Query, Depends
from sqlalchemy import select, exists, func
from sqlalchemy.ext.asyncio import AsyncSession

from car_api.models.cars import Brand, Car
from car_api.core.database import get_session 
from car_api.schemas.brands import (
    BrandSchema,
    BrandPublicSchema,
    BrandListPublicSchema,
    BrandUpdateSchema,
)


router = APIRouter()

@router.post(
        path='/',
        status_code=status.HTTP_201_CREATED,
        response_model=BrandPublicSchema,
        summary='Criar nova marca'
)
async def create_brand(
        brand: BrandSchema,
        db: AsyncSession = Depends(get_session),
):
    brand_name_exists = await db.scalar(
        select(exists().where(Brand.name == brand.name))
    )
    if brand_name_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Marca já cadastrada.'
        )

    db_brand = Brand(
        name=brand.name,
        description=brand.description,
        is_active=brand.is_active,
    )

    db.add(db_brand)
    await db.commit()
    await db.refresh(db_brand)

    return db_brand


@router.get(
    path='/',
    status_code=status.HTTP_200_OK,
    response_model=BrandListPublicSchema,
    summary='Listar marcas',
)
async def list_brands(
    offset: int = Query(0, ge=0, description='Número de registros para pular'),
    limit: int = Query(100, ge=1, le=100, description='Limite de registros'),
    search: Optional[str] = Query(None, description='Buscar por nome da marca'),
    is_active: Optional[bool] = Query(None, description='Filtrar por marcas ativas'),
    db: AsyncSession = Depends(get_session),    
):
    query = select(Brand)

    if search:
        search_filter = f'%{search}%'
        query = query.where(Brand.name.ilike(search_filter))

    if is_active is not None:
        query = query.where(Brand.is_active == is_active)

    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    brands = result.scalars().all()

    return {
        'brands': brands,
        'offset': offset,
        'limit': limit,
    }


@router.get(
    path='/{brand_id}',
    status_code=status.HTTP_200_OK,
    response_model=BrandPublicSchema,
    summary='Buscar marca por ID',
)
async def get_brand(
    brand_id: int,
    db: AsyncSession = Depends(get_session),    
):
    brand = await db.get(Brand, brand_id)

    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Marca não encontrada'
        )

    return brand


@router.patch(
    path='/{brand_id}',
    status_code=status.HTTP_200_OK,
    response_model=BrandPublicSchema,
    summary='Atualizar marca',
)
async def update_brand(
    brand_id: int,
    brand_update: BrandUpdateSchema,
    db: AsyncSession = Depends(get_session),        
):
    brand = await db.get(Brand, brand_id)

    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Marca não encontrada'
        )

    update_data = brand_update.model_dump(exclude_unset=True, exclude_none=True)

    if 'name' in update_data and update_data['name'] != brand.name:
        name_exists = await db.scalar(
            select(exists().where((Brand.name == update_data['name']) &
            (Brand.id != brand_id)
        ))
    )

        if name_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Nome da marca já está em uso',
            )

    for field, value in update_data.items():
        setattr(brand, field, value)

    await db.commit()
    await db.refresh(brand)

    return brand


@router.delete(
        path='/{brand_id}',
        status_code=status.HTTP_204_NO_CONTENT,
        summary='Deletar marca'
)
async def delete_brand(
    brand_id: int,
    db: AsyncSession = Depends(get_session),
):

    brand = await db.get(Brand, brand_id)

    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Marca não encontrada.'
        )

    cars_count = await db.scalar(
        select(func.count()).select_from(Car).where(Car.brand_id == brand_id)
    )

    if cars_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Não é possível deletar marca que possui carros associados.',
        )

    await db.delete(brand)
    await db.commit()

    return
