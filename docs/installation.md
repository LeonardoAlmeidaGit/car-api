# Instalação

Antes de começar, confira os [pré-requisitos](prerequisites.md).

Há duas formas de rodar o projeto:

| Opção | Quando usar |
| --- | --- |
| [1. Tudo no Docker](#opcao-1-tudo-no-docker) | Para usar a API ou conferir o ambiente completo, sem instalar Python |
| [2. Poetry com o banco no Docker](#opcao-2-poetry-com-o-banco-no-docker) | Para desenvolver, com recarregamento automático e testes |

## Passos comuns

### Clonar o repositório

```bash
git clone https://github.com/LeonardoAlmeidaGit/car-api.git
cd car-api
```

### Criar o arquivo `.env`

```bash
cp .env.example .env
```

Troque `JWT_SECRET_KEY` por uma chave aleatória e `DB_PASSWORD` por uma senha
própria. Para gerar a chave:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

Se mudar `DB_USER`, `DB_PASSWORD` ou `DB_NAME`, ajuste também o `DATABASE_URL`
com os mesmos valores. As variáveis estão descritas em
[Configuração](configuration.md).

> **Defina a senha do banco antes de subir o `db`**
>
> O PostgreSQL grava o usuário e a senha na primeira vez que o volume é criado.
> Trocar os valores no `.env` depois disso não altera o banco existente.

## Opção 1: tudo no Docker

```bash
docker compose up -d --build
```

O Compose sobe o PostgreSQL, aplica as migrações, inicia a API e serve a
documentação. Confira se tudo subiu:

```bash
docker compose ps -a
```

O `migrations` deve aparecer como `Exited (0)`, e os demais como `Up`. Siga para
[Verificar a instalação](#verificar-a-instalacao).

Os comandos para logs, migrações e acesso ao banco estão em [Docker](docker.md).

## Opção 2: Poetry com o banco no Docker

### 1. Instalar as dependências

```bash
poetry install
```

O comando cria um ambiente virtual e instala as dependências principais e as de
desenvolvimento: Ruff, taskipy, MkDocs, pytest-asyncio e pytest-cov. O pytest
é instalado como dependência desses dois últimos.

### 2. Subir só o banco

```bash
docker compose up -d db
```

O banco fica disponível em `127.0.0.1:5432`, que é o endereço usado pelo
`DATABASE_URL` do `.env.example`.

### 3. Aplicar as migrações

```bash
poetry run alembic upgrade head
```

Isso cria as tabelas `users`, `brands` e `cars` no PostgreSQL.

### 4. Iniciar a API

```bash
poetry run task run
```

O servidor sobe em modo de desenvolvimento, com recarregamento automático, em
<http://127.0.0.1:8000>.

> **Nota:** Se o serviço `app` do Compose estiver no ar, ele já ocupa a porta
> 8000. Pare-o com `docker compose stop app` antes de rodar `task run`.

### 5. Rodar os testes (opcional)

```bash
poetry run task test
```

Todos os testes devem passar. Eles usam um SQLite em memória e não precisam do
PostgreSQL. Detalhes em [Testes](testing.md).

## Verificar a instalação

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
| `Connection refused` na porta 5432 | O banco não está no ar | `docker compose up -d db` e confira com `docker compose ps` |
| `password authentication failed for user` | `DATABASE_URL` ou `DB_PASSWORD` diferente da senha com que o volume foi criado | Corrija o `.env` ou recrie o banco com `docker compose down -v` |
| `relation "users" does not exist` | Migrações não aplicadas | `poetry run alembic upgrade head` |
| `The currently activated Python version ... is not supported` | Python abaixo de 3.14 | Instale o Python 3.14 e rode `poetry env use python3.14` |
| `address already in use` na porta 8000 | O serviço `app` do Compose já está no ar | `docker compose stop app` |
| `307 Temporary Redirect` em `/api/v1/users` | Faltou a barra final nas rotas de coleção | Use `/api/v1/users/` |

Problemas específicos dos contêineres estão em
[Docker](docker.md#problemas-comuns).
