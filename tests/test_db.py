from decimal import Decimal

import pytest
from sqlalchemy import func, inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from car_api.core.database import get_session
from car_api.models import Brand, Car, User
from car_api.models.cars import FuelType, TransmissionType


@pytest.mark.asyncio
async def test_database_connection(session):
    result = await session.execute(text('SELECT 1'))

    assert result.scalar() == 1


@pytest.mark.asyncio
async def test_database_is_in_memory(engine):
    assert engine.url.database == ':memory:'
    assert engine.url.drivername == 'sqlite+aiosqlite'


@pytest.mark.asyncio
async def test_tables_are_created(engine):
    async with engine.connect() as conn:
        tables = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_table_names()
        )

    assert set(tables) == {'users', 'brands', 'cars'}


@pytest.mark.asyncio
async def test_database_starts_empty(session):
    for model in (User, Brand, Car):
        count = await session.scalar(select(func.count()).select_from(model))
        assert count == 0


@pytest.mark.asyncio
async def test_get_session_yields_async_session():
    generator = get_session()
    db = await anext(generator)

    assert db.__class__.__name__ == 'AsyncSession'

    await generator.aclose()


@pytest.mark.asyncio
async def test_create_user(session):
    new_user = User(
        username='pycode',
        email='test@test.com',
        password='secret1234',
    )

    session.add(new_user)
    await session.commit()

    user = await session.scalar(
        select(User).where(User.email == 'test@test.com')
    )

    new_user_data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'password': user.password,
    }

    assert new_user_data == {
        'id': 1,
        'username': 'pycode',
        'email': 'test@test.com',
        'password': 'secret1234',
    }


@pytest.mark.asyncio
async def test_user_timestamps_are_filled_by_server(session):
    user = User(username='pycode', email='t@t.com', password='secret1234')
    session.add(user)
    await session.commit()
    await session.refresh(user)

    assert user.created_at is not None
    assert user.updated_at is not None


@pytest.mark.asyncio
async def test_user_username_must_be_unique(session, user):
    session.add(
        User(username=user.username, email='novo@x.com', password='x' * 8)
    )

    with pytest.raises(IntegrityError):
        await session.commit()

    await session.rollback()


@pytest.mark.asyncio
async def test_user_email_must_be_unique(session, user):
    session.add(User(username='novousuario', email=user.email, password='x'))

    with pytest.raises(IntegrityError):
        await session.commit()

    await session.rollback()


@pytest.mark.asyncio
async def test_create_brand_with_defaults(session):
    brand = Brand(name='Honda')
    session.add(brand)
    await session.commit()
    await session.refresh(brand)

    assert brand.id == 1
    assert brand.is_active is True
    assert brand.description is None
    assert brand.created_at is not None


@pytest.mark.asyncio
async def test_brand_name_must_be_unique(session, brand):
    session.add(Brand(name=brand.name))

    with pytest.raises(IntegrityError):
        await session.commit()

    await session.rollback()


@pytest.mark.asyncio
async def test_car_plate_must_be_unique(session, car):
    session.add(
        Car(
            model='Civic',
            factory_year=2020,
            model_year=2020,
            color='Preto',
            plate=car.plate,
            fuel_type=FuelType.FLEX,
            transmission_type=TransmissionType.CVT,
            price=Decimal('100000'),
            brand_id=car.brand_id,
            owner_id=car.owner_id,
        )
    )

    with pytest.raises(IntegrityError):
        await session.commit()

    await session.rollback()


@pytest.mark.asyncio
async def test_car_relationships(session, car, user, brand):
    result = await session.execute(
        select(Car)
        .options(selectinload(Car.brand), selectinload(Car.owner))
        .where(Car.id == car.id)
    )
    db_car = result.scalar_one()

    assert db_car.brand.name == brand.name
    assert db_car.owner.username == user.username
    assert db_car.is_available is True
    assert db_car.price == Decimal('120000.00')


@pytest.mark.asyncio
async def test_back_populates_relationships(session, car, user, brand):
    db_user = await session.scalar(
        select(User).options(selectinload(User.cars)).where(User.id == user.id)
    )
    db_brand = await session.scalar(
        select(Brand)
        .options(selectinload(Brand.cars))
        .where(Brand.id == brand.id)
    )

    assert [c.plate for c in db_user.cars] == [car.plate]
    assert [c.plate for c in db_brand.cars] == [car.plate]


@pytest.mark.asyncio
async def test_rollback_discards_changes(session):
    session.add(Brand(name='Temporaria'))
    await session.flush()
    await session.rollback()

    count = await session.scalar(select(func.count()).select_from(Brand))

    assert count == 0
