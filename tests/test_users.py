from http import HTTPStatus

import pytest
from sqlalchemy import select

from car_api.core.security import verify_password
from car_api.models import User

URL = '/api/v1/users/'


def test_create_user(client):
    response = client.post(
        URL,
        json={
            'username': 'novousuario',
            'email': 'novo@teste.com',
            'password': 'senha12345',
        },
    )

    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data['id'] == 1
    assert data['username'] == 'novousuario'
    assert data['email'] == 'novo@teste.com'
    assert 'password' not in data
    assert {'created_at', 'updated_at'} <= data.keys()


@pytest.mark.asyncio
async def test_create_user_stores_hashed_password(client, session):
    client.post(
        URL,
        json={
            'username': 'novousuario',
            'email': 'novo@teste.com',
            'password': 'senha12345',
        },
    )

    db_user = await session.scalar(
        select(User).where(User.username == 'novousuario')
    )

    assert db_user.password != 'senha12345'
    assert verify_password('senha12345', db_user.password)


def test_create_user_username_already_exists(client, user):
    response = client.post(
        URL,
        json={
            'username': user.username,
            'email': 'diferente@teste.com',
            'password': 'senha12345',
        },
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {'detail': 'Username já está em uso.'}


def test_create_user_email_already_exists(client, user):
    response = client.post(
        URL,
        json={
            'username': 'diferente',
            'email': user.email,
            'password': 'senha12345',
        },
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {'detail': 'O email já está em uso.'}


@pytest.mark.parametrize(
    'payload',
    [
        {'username': 'abc', 'email': 'a@a.com', 'password': 'senha12345'},
        {'username': 'valido', 'email': 'invalido', 'password': 'senha12345'},
        {'username': 'valido', 'email': 'a@a.com', 'password': 'curta'},
        {'username': 'valido', 'email': 'a@a.com'},
    ],
    ids=['username-curto', 'email-invalido', 'senha-curta', 'sem-senha'],
)
def test_create_user_invalid_payload(client, payload):
    response = client.post(URL, json=payload)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_list_users(client, user, other_user, auth_headers):
    response = client.get(URL, headers=auth_headers)

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['offset'] == 0
    assert data['limit'] == 100
    assert [u['username'] for u in data['users']] == [
        user.username,
        other_user.username,
    ]


def test_list_users_pagination(client, user, other_user, auth_headers):
    response = client.get(
        URL, params={'offset': 1, 'limit': 1}, headers=auth_headers
    )

    data = response.json()
    assert data['offset'] == 1
    assert data['limit'] == 1
    assert [u['id'] for u in data['users']] == [other_user.id]


@pytest.mark.parametrize(
    ('search', 'expected'),
    [
        ('outro', ['outro_usuario']),
        ('USUARIO@', ['usuario_teste']),
        ('teste.com', ['usuario_teste', 'outro_usuario']),
        ('inexistente', []),
    ],
)
def test_list_users_search(
    client, user, other_user, auth_headers, search, expected
):
    response = client.get(URL, params={'search': search}, headers=auth_headers)

    assert [u['username'] for u in response.json()['users']] == expected


@pytest.mark.parametrize(
    'params', [{'offset': -1}, {'limit': 0}, {'limit': 101}]
)
def test_list_users_invalid_pagination(client, auth_headers, params):
    response = client.get(URL, params=params, headers=auth_headers)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_list_users_requires_authentication(client):
    response = client.get(URL)

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_get_user(client, user, other_user, auth_headers):
    response = client.get(f'{URL}{other_user.id}', headers=auth_headers)

    assert response.status_code == HTTPStatus.OK
    assert response.json()['username'] == other_user.username


def test_get_user_not_found(client, auth_headers):
    response = client.get(f'{URL}999', headers=auth_headers)

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Usuário não encontrado'}


def test_update_user(client, user, auth_headers):
    response = client.patch(
        f'{URL}{user.id}',
        json={'username': 'nome_novo', 'email': 'novo@email.com'},
        headers=auth_headers,
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['username'] == 'nome_novo'
    assert data['email'] == 'novo@email.com'


def test_update_user_keeping_same_values(client, user, auth_headers):
    response = client.patch(
        f'{URL}{user.id}',
        json={'username': user.username, 'email': user.email},
        headers=auth_headers,
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json()['username'] == user.username


@pytest.mark.asyncio
async def test_update_user_password(client, session, user, auth_headers):
    response = client.patch(
        f'{URL}{user.id}',
        json={'password': 'nova_senha_789'},
        headers=auth_headers,
    )

    assert response.status_code == HTTPStatus.OK

    await session.refresh(user)
    assert verify_password('nova_senha_789', user.password)

    login = client.post(
        '/api/v1/auth/token',
        json={'email': user.email, 'password': 'nova_senha_789'},
    )
    assert login.status_code == HTTPStatus.OK


def test_update_user_username_already_exists(
    client, user, other_user, auth_headers
):
    response = client.patch(
        f'{URL}{user.id}',
        json={'username': other_user.username},
        headers=auth_headers,
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {'detail': 'Username já está em uso'}


def test_update_user_email_already_exists(
    client, user, other_user, auth_headers
):
    response = client.patch(
        f'{URL}{user.id}',
        json={'email': other_user.email},
        headers=auth_headers,
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {'detail': 'O email já está em uso'}


def test_update_other_user_forbidden(client, other_user, auth_headers):
    response = client.patch(
        f'{URL}{other_user.id}',
        json={'username': 'hackeado'},
        headers=auth_headers,
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {
        'detail': 'Not enough permissions to access this user'
    }


def test_update_user_not_found(client, auth_headers):
    response = client.patch(
        f'{URL}999', json={'username': 'qualquer'}, headers=auth_headers
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Id de usuário não encontrado.'}


@pytest.mark.parametrize(
    'payload', [{'username': 'abc'}, {'password': '123'}, {'email': 'x'}]
)
def test_update_user_invalid_payload(client, user, auth_headers, payload):
    response = client.patch(
        f'{URL}{user.id}', json=payload, headers=auth_headers
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_delete_user(client, session, user, auth_headers):
    user_id = user.id

    response = client.delete(f'{URL}{user_id}', headers=auth_headers)

    assert response.status_code == HTTPStatus.NO_CONTENT
    session.expunge_all()
    assert await session.get(User, user_id) is None


def test_delete_other_user_forbidden(client, other_user, auth_headers):
    response = client.delete(f'{URL}{other_user.id}', headers=auth_headers)

    assert response.status_code == HTTPStatus.FORBIDDEN


def test_delete_user_not_found(client, auth_headers):
    response = client.delete(f'{URL}999', headers=auth_headers)

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Id de usuário não encontrado.'}


def test_delete_user_with_cars(client, user, car, auth_headers):
    response = client.delete(f'{URL}{user.id}', headers=auth_headers)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {
        'detail': 'Não é possível deletar usuário '
        'que possui carros associados.'
    }
