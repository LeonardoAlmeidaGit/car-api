# Instalação

Antes de começar, confira os [pré-requisitos](prerequisites.md).

## 1. Clonar o repositório

```bash
git clone https://github.com/LeonardoAlmeidaGit/fastapi_test.git
cd fastapi_test
```

## 2. Instalar as dependências

```bash
poetry install
```

O comando cria um ambiente virtual e instala as dependências principais e as de
desenvolvimento (Ruff, taskipy e MkDocs).

## 3. Criar o arquivo `.env`

```bash
cp .env.example .env
```

Gere uma chave aleatória e use-a em `JWT_SECRET_KEY`:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

As variáveis estão descritas em [Configuração](configuration.md).

## 4. Criar o banco de dados

```bash
poetry run alembic upgrade head
```

Isso cria o arquivo `car.db` com as tabelas `users`, `brands` e `cars`.

## 5. Iniciar a API

```bash
poetry run task run
```

O servidor sobe em modo de desenvolvimento, com recarregamento automático, em
<http://127.0.0.1:8000>.

## 6. Verificar a instalação

```bash
curl http://127.0.0.1:8000/health_check
```

Resposta esperada:

```json
{"message": "ok"}
```

## Primeiras requisições

Crie um usuário:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/users/ \
  -H 'Content-Type: application/json' \
  -d '{"username": "maria", "email": "maria@example.com", "password": "senha-segura-123"}'
```

Obtenha um token:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/token \
  -H 'Content-Type: application/json' \
  -d '{"email": "maria@example.com", "password": "senha-segura-123"}'
```

Use o valor de `access_token` nas rotas protegidas:

```bash
curl http://127.0.0.1:8000/api/v1/brands/ \
  -H 'Authorization: Bearer SEU_TOKEN'
```

## Problemas comuns

| Sintoma | Causa provável | Solução |
| --- | --- | --- |
| `ValidationError` do Pydantic ao iniciar, com `Field required` | `.env` ausente ou incompleto, ou comando executado fora da raiz do projeto | Crie o `.env` e execute os comandos na raiz |
| `no such table` ao chamar a API | Migrações não aplicadas | Execute `poetry run alembic upgrade head` |
| `The currently activated Python version ... is not supported` | Python abaixo de 3.14 | Instale o Python 3.14 e rode `poetry env use python3.14` |
| `307 Temporary Redirect` em `/api/v1/users` | Faltou a barra final nas rotas de coleção | Use `/api/v1/users/` |
