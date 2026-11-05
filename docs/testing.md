# Testes

> **O projeto ainda não tem testes automatizados**
>
> O diretório `tests/` contém apenas um `__init__.py` vazio, e o pytest não
> está entre as dependências. As regras `PT` do Ruff já estão ativas e serão
> aplicadas aos testes quando eles forem criados.

## Verificação manual

Enquanto não há testes automatizados, valide as alterações assim:

1. Rode `poetry run task lint`.
2. Inicie a API com `poetry run task run`.
3. Em <http://127.0.0.1:8000/docs>, teste o caso de sucesso e os casos de erro da
   rota alterada.

Para rotas protegidas, confira ao menos:

- Sem token, a resposta é `401`.
- Com o token de outro usuário, a resposta é `403`, quando houver regra de
  propriedade.
- Com ID inexistente, a resposta é `404`.
- Com dados inválidos, a resposta é `422`.
- Com dados duplicados, a resposta é `400`.

Para testar sem afetar o `car.db`, aponte para outro banco, já que variáveis de
ambiente têm prioridade sobre o `.env`:

```bash
export DATABASE_URL='sqlite+aiosqlite:////tmp/car_test.db'
poetry run alembic upgrade head
poetry run task run
```

## Como adicionar testes

A configuração abaixo é uma proposta. Ela foi executada contra o código atual,
com todos os testes passando, mas ainda não faz parte do repositório.

### 1. Instalar o pytest

```bash
poetry add --group dev pytest
```

Adicione a tarefa em `pyproject.toml`:

```toml
[tool.taskipy.tasks]
test = 'pytest'
```

### 2. Criar as fixtures

Cada teste usa um banco SQLite próprio, em um diretório temporário.

`tests/conftest.py`:

```python
import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from car_api.app import app
from car_api.core.database import get_session
from car_api.models import Base


@pytest.fixture
def client(tmp_path):
    engine = create_async_engine(f'sqlite+aiosqlite:///{tmp_path}/test.db')

    async def create_tables():
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        await engine.dispose()

    asyncio.run(create_tables())

    async def override_get_session():
        async with AsyncSession(engine, expire_on_commit=False) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    asyncio.run(engine.dispose())


@pytest.fixture
def auth_headers(client):
    credentials = {
        'email': 'maria@example.com',
        'password': 'senha-segura-123',
    }
    client.post('/api/v1/users/', json={'username': 'maria', **credentials})
    response = client.post('/api/v1/auth/token', json=credentials)
    token = response.json()['access_token']

    return {'Authorization': f'Bearer {token}'}
```

> **Nota:** Importar `car_api.app` lê as configurações, então o `.env` ou as variáveis
> de ambiente precisam existir ao rodar os testes.

### 3. Escrever os testes

`tests/test_brands.py`:

```python
from fastapi import status


def test_health_check(client):
    response = client.get('/health_check')

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'message': 'ok'}


def test_list_brands_requires_authentication(client):
    response = client.get('/api/v1/brands/')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_brand(client, auth_headers):
    response = client.post(
        '/api/v1/brands/',
        json={'name': 'Toyota'},
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()['name'] == 'Toyota'


def test_create_brand_with_duplicate_name(client, auth_headers):
    payload = {'name': 'Toyota'}
    client.post('/api/v1/brands/', json=payload, headers=auth_headers)

    response = client.post(
        '/api/v1/brands/',
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
```

### 4. Executar

```bash
poetry run pytest
```

A versão atual do Starlette emite um `StarletteDeprecationWarning` sobre o uso de
`httpx` no `TestClient`. O aviso não afeta os testes.

## Prioridades de cobertura

Sugestão de ordem, começando pelos pontos de maior risco:

| Prioridade | Área | O que testar |
| --- | --- | --- |
| 1 | Autenticação | Login correto e incorreto, token expirado, inválido e de usuário excluído, renovação |
| 2 | Permissões | Alterar ou excluir conta e carro de outro usuário; criar carro para outro dono |
| 3 | Regras de negócio | Duplicidades; exclusão bloqueada de marca e usuário com carros; transferência de carro |
| 4 | Validações | Limites de ano, preço, placa, cor e senha; valores de enum inválidos |
| 5 | Listagens | Paginação, limites de `limit` e cada filtro de carros |
