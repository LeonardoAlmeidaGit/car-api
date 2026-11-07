from http import HTTPStatus

import pytest

from car_api.models import Brand

URL = '/api/v1/brands/'


def test_create_brand(client, auth_headers):
    response = client.post(
        URL,
        json={'name': '  Honda  ', 'description': 'Marca japonesa'},
        headers=auth_headers,
    )

    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data['id'] == 1
    assert data['name'] == 'Honda'
    assert data['description'] == 'Marca japonesa'
    assert data['is_active'] is True
    assert {'created_at', 'updated_at'} <= data.keys()


def test_create_inactive_brand(client, auth_headers):
    response = client.post(
        URL, json={'name': 'Ford', 'is_active': False}, headers=auth_headers
    )

    assert response.status_code == HTTPStatus.CREATED
    assert response.json()['is_active'] is False
    assert response.json()['description'] is None


def test_create_brand_already_exists(client, brand, auth_headers):
    response = client.post(
        URL, json={'name': brand.name}, headers=auth_headers
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {'detail': 'Marca já cadastrada.'}


@pytest.mark.parametrize(
    'payload', [{'name': 'A'}, {'name': '   '}, {'name': 'A' * 51}, {}]
)
def test_create_brand_invalid_payload(client, auth_headers, payload):
    response = client.post(URL, json=payload, headers=auth_headers)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_create_brand_name_max_length(client, auth_headers):
    response = client.post(URL, json={'name': 'A' * 50}, headers=auth_headers)

    assert response.status_code == HTTPStatus.CREATED
    assert response.json()['name'] == 'A' * 50


def test_create_brand_requires_authentication(client):
    response = client.post(URL, json={'name': 'Honda'})

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_list_brands(client, brand, inactive_brand, auth_headers):
    response = client.get(URL, headers=auth_headers)

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['offset'] == 0
    assert data['limit'] == 100
    assert [b['name'] for b in data['brands']] == ['Toyota', 'Fiat']


def test_list_brands_empty(client, auth_headers):
    response = client.get(URL, headers=auth_headers)

    assert response.json()['brands'] == []


@pytest.mark.parametrize(
    ('params', 'expected'),
    [
        ({'search': 'toy'}, ['Toyota']),
        ({'search': 'xpto'}, []),
        ({'is_active': True}, ['Toyota']),
        ({'is_active': False}, ['Fiat']),
        ({'search': 'fi', 'is_active': True}, []),
        ({'offset': 1}, ['Fiat']),
        ({'limit': 1}, ['Toyota']),
    ],
)
def test_list_brands_filters(
    client, brand, inactive_brand, auth_headers, params, expected
):
    response = client.get(URL, params=params, headers=auth_headers)

    assert [b['name'] for b in response.json()['brands']] == expected


@pytest.mark.parametrize(
    'params', [{'offset': -1}, {'limit': 0}, {'limit': 101}]
)
def test_list_brands_invalid_pagination(client, auth_headers, params):
    response = client.get(URL, params=params, headers=auth_headers)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_get_brand(client, brand, auth_headers):
    response = client.get(f'{URL}{brand.id}', headers=auth_headers)

    assert response.status_code == HTTPStatus.OK
    assert response.json()['name'] == brand.name


def test_get_brand_not_found(client, auth_headers):
    response = client.get(f'{URL}999', headers=auth_headers)

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Marca não encontrada'}


def test_update_brand(client, brand, auth_headers):
    response = client.patch(
        f'{URL}{brand.id}',
        json={'name': 'Toyota Motors', 'is_active': False},
        headers=auth_headers,
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['name'] == 'Toyota Motors'
    assert data['is_active'] is False
    assert data['description'] == brand.description


def test_update_brand_same_name(client, brand, auth_headers):
    response = client.patch(
        f'{URL}{brand.id}',
        json={'name': brand.name, 'description': 'Nova descrição'},
        headers=auth_headers,
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json()['description'] == 'Nova descrição'


def test_update_brand_ignores_null_fields(client, brand, auth_headers):
    response = client.patch(
        f'{URL}{brand.id}', json={'name': None}, headers=auth_headers
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json()['name'] == brand.name


def test_update_brand_name_already_exists(
    client, brand, inactive_brand, auth_headers
):
    response = client.patch(
        f'{URL}{brand.id}',
        json={'name': inactive_brand.name},
        headers=auth_headers,
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {'detail': 'Nome da marca já está em uso'}


def test_update_brand_not_found(client, auth_headers):
    response = client.patch(
        f'{URL}999', json={'name': 'Qualquer'}, headers=auth_headers
    )

    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.parametrize('name', ['X', 'X' * 51])
def test_update_brand_invalid_name(client, brand, auth_headers, name):
    response = client.patch(
        f'{URL}{brand.id}', json={'name': name}, headers=auth_headers
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_update_brand_name_max_length(client, brand, auth_headers):
    response = client.patch(
        f'{URL}{brand.id}', json={'name': 'B' * 50}, headers=auth_headers
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json()['name'] == 'B' * 50


@pytest.mark.asyncio
async def test_delete_brand(client, session, brand, auth_headers):
    brand_id = brand.id

    response = client.delete(f'{URL}{brand_id}', headers=auth_headers)

    assert response.status_code == HTTPStatus.NO_CONTENT
    session.expunge_all()
    assert await session.get(Brand, brand_id) is None


def test_delete_brand_not_found(client, auth_headers):
    response = client.delete(f'{URL}999', headers=auth_headers)

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Marca não encontrada.'}


def test_delete_brand_with_cars(client, brand, car, auth_headers):
    response = client.delete(f'{URL}{brand.id}', headers=auth_headers)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {
        'detail': 'Não é possível deletar marca que possui carros associados.'
    }
