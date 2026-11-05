from datetime import datetime, timedelta, timezone
from decimal import Decimal

import jwt
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from car_api.app import app
from car_api.core.database import get_session
from car_api.core.security import (
    create_access_token,
    get_password_hash,
    settings,
)
from car_api.models import Base, Brand, Car, User
from car_api.models.cars import FuelType, TransmissionType

USER_PASSWORD = 'senha_segura_123'
OTHER_USER_PASSWORD = 'outra_senha_456'


@pytest_asyncio.fixture
async def engine():
    """Engine assíncrona apontando para um SQLite em memória.

    O StaticPool garante que todas as conexões compartilhem o mesmo banco
    em memória (cada nova conexão em ``:memory:`` criaria um banco vazio).
    """
    engine = create_async_engine(
        url='sqlite+aiosqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def session(engine):
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture
def client(session):
    def get_session_override():
        return session

    with TestClient(app) as client:
        app.dependency_overrides[get_session] = get_session_override
        yield client

    app.dependency_overrides.clear()


async def _create_user(session, username, email, password):
    user = User(
        username=username,
        email=email,
        password=get_password_hash(password),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    user.clean_password = password
    return user


@pytest_asyncio.fixture
async def user(session):
    return await _create_user(
        session, 'usuario_teste', 'usuario@teste.com', USER_PASSWORD
    )


@pytest_asyncio.fixture
async def other_user(session):
    return await _create_user(
        session, 'outro_usuario', 'outro@teste.com', OTHER_USER_PASSWORD
    )


@pytest.fixture
def token(client, user):
    response = client.post(
        '/api/v1/auth/token',
        json={'email': user.email, 'password': user.clean_password},
    )
    return response.json()['access_token']


@pytest.fixture
def auth_headers(token):
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def other_auth_headers(other_user):
    token = create_access_token(data={'sub': str(other_user.id)})
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def make_token():
    """Fábrica de tokens JWT arbitrários (payload/expiração/chave)."""

    def _make_token(
        payload=None,
        expires_delta=timedelta(minutes=30),
        secret=None,
    ):
        to_encode = dict(payload or {})
        to_encode['exp'] = datetime.now(timezone.utc) + expires_delta
        return jwt.encode(
            to_encode,
            secret or settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

    return _make_token


@pytest_asyncio.fixture
async def brand(session):
    brand = Brand(name='Toyota', description='Marca japonesa')
    session.add(brand)
    await session.commit()
    await session.refresh(brand)
    return brand


@pytest_asyncio.fixture
async def inactive_brand(session):
    brand = Brand(name='Fiat', description='Marca italiana', is_active=False)
    session.add(brand)
    await session.commit()
    await session.refresh(brand)
    return brand


@pytest.fixture
def car_payload(user, brand):
    """Payload válido para criação de carro via API."""
    return {
        'model': 'Corolla',
        'factory_year': 2022,
        'model_year': 2023,
        'color': 'Prata',
        'plate': 'abc1d23',
        'fuel_type': 'flex',
        'transmission_type': 'automatic',
        'price': '120000.00',
        'description': 'Carro muito conservado',
        'brand_id': brand.id,
        'owner_id': user.id,
    }


async def _create_car(session, **fields):
    car = Car(**fields)
    session.add(car)
    await session.commit()
    await session.refresh(car)
    return car


@pytest_asyncio.fixture
async def car(session, user, brand):
    return await _create_car(
        session,
        model='Corolla',
        factory_year=2022,
        model_year=2023,
        color='Prata',
        plate='ABC1D23',
        fuel_type=FuelType.FLEX,
        transmission_type=TransmissionType.AUTOMATIC,
        price=Decimal('120000.00'),
        brand_id=brand.id,
        owner_id=user.id,
    )


@pytest_asyncio.fixture
async def other_car(session, other_user, inactive_brand):
    return await _create_car(
        session,
        model='Uno',
        factory_year=2010,
        model_year=2010,
        color='Branco',
        plate='XYZ9876',
        fuel_type=FuelType.GASOLINE,
        transmission_type=TransmissionType.MANUAL,
        price=Decimal('25000.00'),
        is_available=False,
        brand_id=inactive_brand.id,
        owner_id=other_user.id,
    )
