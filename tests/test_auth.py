from datetime import timedelta
from http import HTTPStatus
from types import SimpleNamespace

import jwt
import pytest
from fastapi import HTTPException

from car_api.core.security import (
    create_access_token,
    get_password_hash,
    settings,
    verify_car_ownership,
    verify_password,
    verify_token,
    verify_user_yourself,
)

TOKEN_URL = '/api/v1/auth/token'
REFRESH_URL = '/api/v1/auth/refresh_token'
PROTECTED_URL = '/api/v1/users/'


def test_password_hash_is_not_plain_text():
    hashed = get_password_hash('minha_senha')

    assert hashed != 'minha_senha'
    assert hashed.startswith('$argon2')


def test_verify_password():
    hashed = get_password_hash('minha_senha')

    assert verify_password('minha_senha', hashed) is True
    assert verify_password('senha_errada', hashed) is False


def test_create_access_token_payload():
    token = create_access_token({'sub': '1'})

    payload = jwt.decode(
        token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )

    assert payload['sub'] == '1'
    assert 'exp' in payload


def test_create_access_token_does_not_mutate_input():
    data = {'sub': '1'}

    create_access_token(data)

    assert data == {'sub': '1'}


def test_verify_token_valid():
    token = create_access_token({'sub': '42'})

    assert verify_token(token)['sub'] == '42'


def test_verify_token_expired(make_token):
    token = make_token({'sub': '1'}, expires_delta=timedelta(minutes=-1))

    with pytest.raises(HTTPException) as exc:
        verify_token(token)

    assert exc.value.status_code == HTTPStatus.UNAUTHORIZED
    assert exc.value.detail == 'Token has expired'


@pytest.mark.parametrize(
    'token',
    ['token-invalido', 'a.b.c', ''],
)
def test_verify_token_invalid(token):
    with pytest.raises(HTTPException) as exc:
        verify_token(token)

    assert exc.value.status_code == HTTPStatus.UNAUTHORIZED
    assert exc.value.detail == 'Could not validate credentials'


def test_verify_token_wrong_secret(make_token):
    token = make_token({'sub': '1'}, secret='outra-chave-' * 4)

    with pytest.raises(HTTPException) as exc:
        verify_token(token)

    assert exc.value.detail == 'Could not validate credentials'


def test_verify_car_ownership():
    user = SimpleNamespace(id=1)

    verify_car_ownership(user, 1)

    with pytest.raises(HTTPException) as exc:
        verify_car_ownership(user, 2)

    assert exc.value.status_code == HTTPStatus.FORBIDDEN


def test_verify_user_yourself():
    user = SimpleNamespace(id=1)

    verify_user_yourself(user, 1)

    with pytest.raises(HTTPException) as exc:
        verify_user_yourself(user, 2)

    assert exc.value.status_code == HTTPStatus.FORBIDDEN


def test_login_returns_token(client, user):
    response = client.post(
        TOKEN_URL,
        json={'email': user.email, 'password': user.clean_password},
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['token_type'] == 'bearer'
    assert verify_token(data['access_token'])['sub'] == str(user.id)


def test_login_wrong_password(client, user):
    response = client.post(
        TOKEN_URL,
        json={'email': user.email, 'password': 'senha_errada'},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Incorrect email or password'}
    assert response.headers['www-authenticate'] == 'Bearer'


def test_login_unknown_email(client, user):
    response = client.post(
        TOKEN_URL,
        json={'email': 'naoexiste@teste.com', 'password': 'qualquer123'},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Incorrect email or password'}


@pytest.mark.parametrize(
    'payload',
    [
        {'email': 'invalido', 'password': 'senha12345'},
        {'email': 'a@a.com', 'password': 'curta'},
        {'email': 'a@a.com'},
    ],
)
def test_login_invalid_payload(client, payload):
    response = client.post(TOKEN_URL, json=payload)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_refresh_token(client, user, auth_headers):
    response = client.post(REFRESH_URL, headers=auth_headers)

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['token_type'] == 'bearer'
    assert verify_token(data['access_token'])['sub'] == str(user.id)


def test_refresh_token_without_credentials(client):
    response = client.post(REFRESH_URL)

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_refresh_token_expired(client, user, make_token):
    token = make_token(
        {'sub': str(user.id)}, expires_delta=timedelta(minutes=-5)
    )

    response = client.post(
        REFRESH_URL, headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Token has expired'}


@pytest.mark.parametrize(
    'payload',
    [{}, {'sub': ''}, {'sub': 'abc'}, {'sub': '999'}],
    ids=['sem-sub', 'sub-vazio', 'sub-nao-numerico', 'usuario-inexistente'],
)
def test_protected_route_invalid_subject(client, user, make_token, payload):
    token = make_token(payload)

    response = client.get(
        PROTECTED_URL, headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Could not validate credentials'}
    assert response.headers['www-authenticate'] == 'Bearer'


def test_protected_route_malformed_token(client):
    response = client.get(
        PROTECTED_URL, headers={'Authorization': 'Bearer nao.e.jwt'}
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_protected_route_wrong_scheme(client, token):
    response = client.get(
        PROTECTED_URL, headers={'Authorization': f'Basic {token}'}
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_token_of_deleted_user_is_rejected(client, user, auth_headers):
    client.delete(f'/api/v1/users/{user.id}', headers=auth_headers)

    response = client.get(PROTECTED_URL, headers=auth_headers)

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_health_check(client):
    response = client.get('/health_check')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'ok'}
