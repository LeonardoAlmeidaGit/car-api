from decimal import Decimal
from http import HTTPStatus

import pytest

from car_api.models import Car

URL = '/api/v1/cars/'


def test_create_car(client, user, brand, car_payload, auth_headers):
    response = client.post(URL, json=car_payload, headers=auth_headers)

    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data['id'] == 1
    assert data['model'] == 'Corolla'
    assert data['plate'] == 'ABC1D23'
    assert data['fuel_type'] == 'flex'
    assert data['transmission_type'] == 'automatic'
    assert Decimal(data['price']) == Decimal('120000.00')
    assert data['is_available'] is True
    assert data['brand']['name'] == brand.name
    assert data['owner']['username'] == user.username
    assert 'password' not in data['owner']


def test_create_car_for_other_owner_forbidden(
    client, other_user, car_payload, auth_headers
):
    car_payload['owner_id'] = other_user.id

    response = client.post(URL, json=car_payload, headers=auth_headers)

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {
        'detail': 'Not enough permissions to access this car'
    }


def test_create_car_plate_already_exists(
    client, car, car_payload, auth_headers
):
    response = client.post(URL, json=car_payload, headers=auth_headers)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {'detail': 'Placa já está em uso'}


def test_create_car_brand_not_found(client, car_payload, auth_headers):
    car_payload['brand_id'] = 999

    response = client.post(URL, json=car_payload, headers=auth_headers)

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Marca não encontrada'}


@pytest.mark.parametrize(
    ('field', 'value'),
    [
        ('model', 'A'),
        ('color', 'Az'),
        ('plate', 'AB12'),
        ('plate', 'ABCDEFGHIJK'),
        ('factory_year', 1899),
        ('model_year', 2031),
        ('price', '0'),
        ('fuel_type', 'nuclear'),
        ('transmission_type', 'teleporte'),
    ],
)
def test_create_car_invalid_payload(
    client, car_payload, auth_headers, field, value
):
    car_payload[field] = value

    response = client.post(URL, json=car_payload, headers=auth_headers)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_create_car_requires_authentication(client, car_payload):
    response = client.post(URL, json=car_payload)

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_list_cars(client, car, other_car, auth_headers):
    response = client.get(URL, headers=auth_headers)

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['offset'] == 0
    assert data['limit'] == 100
    assert [c['plate'] for c in data['cars']] == [car.plate, other_car.plate]
    assert data['cars'][0]['brand']['name'] == 'Toyota'


@pytest.mark.parametrize(
    ('params', 'expected'),
    [
        ({'search': 'coro'}, ['ABC1D23']),
        ({'search': 'branco'}, ['XYZ9876']),
        ({'search': 'xyz'}, ['XYZ9876']),
        ({'brand_id': 1}, ['ABC1D23']),
        ({'owner_id': 2}, ['XYZ9876']),
        ({'fuel_type': 'gasoline'}, ['XYZ9876']),
        ({'transmission_type': 'automatic'}, ['ABC1D23']),
        ({'is_available': True}, ['ABC1D23']),
        ({'is_available': False}, ['XYZ9876']),
        ({'min_price': 50000}, ['ABC1D23']),
        ({'max_price': 50000}, ['XYZ9876']),
        ({'min_price': 20000, 'max_price': 200000}, ['ABC1D23', 'XYZ9876']),
        ({'offset': 1}, ['XYZ9876']),
        ({'limit': 1}, ['ABC1D23']),
        ({'search': 'inexistente'}, []),
    ],
)
def test_list_cars_filters(
    client, car, other_car, auth_headers, params, expected
):
    response = client.get(URL, params=params, headers=auth_headers)

    assert response.status_code == HTTPStatus.OK
    assert [c['plate'] for c in response.json()['cars']] == expected


@pytest.mark.parametrize(
    'params',
    [
        {'offset': -1},
        {'limit': 0},
        {'limit': 101},
        {'min_price': -1},
        {'fuel_type': 'nuclear'},
    ],
)
def test_list_cars_invalid_params(client, auth_headers, params):
    response = client.get(URL, params=params, headers=auth_headers)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_get_car(client, car, auth_headers):
    response = client.get(f'{URL}{car.id}', headers=auth_headers)

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['plate'] == car.plate
    assert data['owner']['id'] == car.owner_id


def test_get_car_of_other_user_is_allowed(client, other_car, auth_headers):
    response = client.get(f'{URL}{other_car.id}', headers=auth_headers)

    assert response.status_code == HTTPStatus.OK


def test_get_car_not_found(client, auth_headers):
    response = client.get(f'{URL}999', headers=auth_headers)

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Carro não encontrado'}


def test_update_car(client, car, auth_headers):
    response = client.patch(
        f'{URL}{car.id}',
        json={'color': 'Vermelho', 'price': '99999.90', 'plate': 'new1a23'},
        headers=auth_headers,
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['color'] == 'Vermelho'
    assert Decimal(data['price']) == Decimal('99999.90')
    assert data['plate'] == 'NEW1A23'
    assert data['model'] == car.model


def test_update_car_same_plate(client, car, auth_headers):
    response = client.patch(
        f'{URL}{car.id}', json={'plate': car.plate}, headers=auth_headers
    )

    assert response.status_code == HTTPStatus.OK


def test_update_car_plate_already_exists(client, car, other_car, auth_headers):
    response = client.patch(
        f'{URL}{car.id}', json={'plate': other_car.plate}, headers=auth_headers
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {'detail': 'Placa já está em uso'}


def test_update_car_brand(client, car, inactive_brand, auth_headers):
    response = client.patch(
        f'{URL}{car.id}',
        json={'brand_id': inactive_brand.id},
        headers=auth_headers,
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json()['brand']['name'] == inactive_brand.name


def test_update_car_brand_not_found(client, car, auth_headers):
    response = client.patch(
        f'{URL}{car.id}', json={'brand_id': 999}, headers=auth_headers
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Marca não encontrada'}


def test_update_car_transfer_owner(client, car, other_user, auth_headers):
    response = client.patch(
        f'{URL}{car.id}',
        json={'owner_id': other_user.id},
        headers=auth_headers,
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json()['owner']['id'] == other_user.id


def test_update_car_owner_not_found(client, car, auth_headers):
    response = client.patch(
        f'{URL}{car.id}', json={'owner_id': 999}, headers=auth_headers
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Proprietário não encontrado'}


def test_update_car_of_other_user_forbidden(client, other_car, auth_headers):
    response = client.patch(
        f'{URL}{other_car.id}', json={'color': 'Preto'}, headers=auth_headers
    )

    assert response.status_code == HTTPStatus.FORBIDDEN


def test_update_car_not_found(client, auth_headers):
    response = client.patch(
        f'{URL}999', json={'color': 'Preto'}, headers=auth_headers
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Carro não encontrado'}


@pytest.mark.parametrize(
    'payload',
    [
        {'model': 'X'},
        {'color': 'Az'},
        {'plate': 'AB'},
        {'factory_year': 1800},
        {'price': '-10'},
    ],
)
def test_update_car_invalid_payload(client, car, auth_headers, payload):
    response = client.patch(
        f'{URL}{car.id}', json=payload, headers=auth_headers
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_delete_car(client, session, car, auth_headers):
    car_id = car.id

    response = client.delete(f'{URL}{car_id}', headers=auth_headers)

    assert response.status_code == HTTPStatus.NO_CONTENT
    session.expunge_all()
    assert await session.get(Car, car_id) is None


def test_delete_car_of_other_user_forbidden(client, other_car, auth_headers):
    response = client.delete(f'{URL}{other_car.id}', headers=auth_headers)

    assert response.status_code == HTTPStatus.FORBIDDEN


def test_delete_car_not_found(client, auth_headers):
    response = client.delete(f'{URL}999', headers=auth_headers)

    assert response.status_code == HTTPStatus.NOT_FOUND
