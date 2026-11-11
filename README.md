# Car API

[![CI](https://github.com/LeonardoAlmeidaGit/car-api/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/LeonardoAlmeidaGit/car-api/actions/workflows/ci.yml)
![Versão](https://img.shields.io/badge/vers%C3%A3o-1.0.0-green)
![Python](https://img.shields.io/badge/python-3.14-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.142-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17.6-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Ruff](https://img.shields.io/badge/lint-Ruff-D7FF64?logo=ruff&logoColor=black)

API REST para gerenciamento de carros, marcas e usuários, construída com
**FastAPI**, **SQLAlchemy assíncrono**, **PostgreSQL** e autenticação **JWT**.
O ambiente completo (API, banco, migrações e documentação) sobe com um único
comando do Docker Compose, e um pipeline no GitHub Actions testa cada pull
request e publica cada versão como imagem Docker.

## Sumário

- [Funcionalidades](#funcionalidades)
- [Tecnologias](#tecnologias)
- [Arquitetura](#arquitetura)
- [Início rápido com Docker](#início-rápido-com-docker)
- [Desenvolvimento local](#desenvolvimento-local)
- [Variáveis de ambiente](#variáveis-de-ambiente)
- [Endpoints](#endpoints)
- [Exemplo de uso](#exemplo-de-uso)
- [Testes e qualidade](#testes-e-qualidade)
- [CI/CD](#cicd)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Documentação](#documentação)
- [Limitações conhecidas](#limitações-conhecidas)
- [Contribuição](#contribuição)
- [Autor](#autor)

## Funcionalidades

- **Autenticação JWT**: login por e-mail e senha, com emissão e renovação de
  token.
- **Usuários**: cadastro público e CRUD autenticado, com senha armazenada como
  hash Argon2.
- **Marcas**: CRUD com nome único, busca por nome e filtro por status.
- **Carros**: CRUD com placa única, busca textual e filtros por marca,
  proprietário, combustível, transmissão, disponibilidade e faixa de preço.
- **Regras de propriedade**: cada usuário só altera a própria conta e os
  próprios carros; exclusões de usuário e marca com carros associados são
  bloqueadas.
- **Paginação** com `offset` e `limit` em todas as listagens (até 100 registros
  por página).
- **Validação** com Pydantic, com limites de tamanho e precisão iguais aos das
  colunas do banco.
- **Documentação interativa** com Swagger UI e ReDoc.
- **Ambiente em contêineres** com Docker Compose: API, PostgreSQL, migrações e
  documentação.
- **181 testes automatizados** com 99% de cobertura.
- **CI/CD com GitHub Actions**: lint, testes e lint dos Dockerfiles em todo
  pull request; a cada versão, imagens publicadas no GitHub Container Registry,
  smoke test com PostgreSQL e GitHub Release automática.

## Tecnologias

| Categoria | Tecnologia |
| --- | --- |
| Linguagem | Python 3.14 |
| Framework web | FastAPI 0.142 |
| Validação e configuração | Pydantic 2 e pydantic-settings |
| ORM | SQLAlchemy 2.1 (asyncio) |
| Banco de dados | PostgreSQL 17.6, com o driver psycopg 3 |
| Migrações | Alembic |
| Autenticação | PyJWT e pwdlib (Argon2) |
| Testes | pytest, pytest-asyncio e pytest-cov, sobre SQLite em memória (aiosqlite) |
| Lint e formatação | Ruff |
| Tarefas | taskipy |
| Dependências | Poetry 2 |
| Contêineres | Docker e Docker Compose |
| CI/CD | GitHub Actions, GitHub Container Registry (GHCR) e hadolint |
| Documentação | MkDocs Material, servido por Nginx no contêiner |

As versões exatas estão no `poetry.lock`, nos Dockerfiles e no
`docker-compose.yml`.

## Arquitetura

A aplicação segue uma organização em camadas: as **rotas** recebem a
requisição, os **schemas** validam a entrada e formatam a saída, o módulo de
**segurança** identifica o usuário e verifica permissões, e os **modelos** do
SQLAlchemy persistem os dados no PostgreSQL.

```mermaid
flowchart LR
    Client["Cliente HTTP"] --> Routers["Routers<br/>auth, users, brands, cars"]
    Routers --> Schemas["Schemas<br/>Pydantic"]
    Routers --> Security["Security<br/>JWT, Argon2, permissões"]
    Routers --> Session["AsyncSession<br/>get_session"]
    Security --> Session
    Session --> Models["Models<br/>SQLAlchemy"]
    Models --> DB[("PostgreSQL")]
```

### Modelo de dados

```mermaid
erDiagram
    USERS ||--o{ CARS : "possui"
    BRANDS ||--o{ CARS : "fabrica"

    USERS {
        int id PK
        string username UK
        string email UK
        string password "hash Argon2"
    }
    BRANDS {
        int id PK
        string name UK "até 50"
        bool is_active
        text description
    }
    CARS {
        int id PK
        string model "até 100"
        int factory_year
        int model_year
        string color "até 30"
        string plate UK "até 10"
        string fuel_type
        string transmission_type
        numeric price "10,2"
        bool is_available
        int brand_id FK
        int owner_id FK
    }
```

Todas as tabelas têm também `created_at` e `updated_at`, preenchidos pelo
banco.

### Serviços do Docker Compose

| Serviço | Imagem | Porta no host | Função |
| --- | --- | --- | --- |
| `db` | `postgres:17.6-bookworm` | `127.0.0.1:5432` | PostgreSQL, com dados no volume `postgres_data` |
| `migrations` | `car_api:latest` | Nenhuma | Roda `alembic upgrade head` e encerra |
| `app` | `car_api:latest` | `8000` | API com `fastapi run` |
| `mkdocs` | `car-api-mkdocs:latest` | `8001` | Documentação estática servida pelo Nginx |

O `app` só sobe depois que o `db` passa no *healthcheck* e o `migrations`
termina com sucesso. A imagem da API roda com um usuário sem privilégios e não
inclui segredos, testes nem dependências de desenvolvimento.

## Início rápido com Docker

**Pré-requisitos:** Git e Docker com o plugin Compose v2.

```bash
git clone https://github.com/LeonardoAlmeidaGit/car-api.git
cd car-api
cp .env.example .env
```

Antes de subir os serviços, edite o `.env` e troque `JWT_SECRET_KEY` e
`DB_PASSWORD` (mantendo o `DATABASE_URL` com a mesma senha). Para gerar uma
chave:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

> O PostgreSQL grava o usuário e a senha na primeira vez que o volume é criado.
> Alterar esses valores depois não muda o banco existente.

Suba tudo:

```bash
docker compose up -d --build
docker compose ps -a
```

O `db` deve aparecer como `healthy`, o `migrations` como `Exited (0)` e o `app`
e o `mkdocs` como `Up`.

| Recurso | URL |
| --- | --- |
| API | <http://127.0.0.1:8000/api/v1> |
| Swagger UI | <http://127.0.0.1:8000/docs> |
| ReDoc | <http://127.0.0.1:8000/redoc> |
| Health check | <http://127.0.0.1:8000/health_check> |
| Documentação do projeto | <http://127.0.0.1:8001> |

### Comandos úteis

| Comando | O que faz |
| --- | --- |
| `docker compose logs -f app` | Acompanha os logs da API |
| `docker compose logs migrations` | Mostra a saída das migrações |
| `docker compose up -d --build app` | Reconstrói a API após alterar o código |
| `docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'` | Abre o `psql` no banco |
| `docker compose down` | Remove os contêineres, mantendo os dados |
| `docker compose down -v` | Remove os contêineres **e os dados** do banco |

## Desenvolvimento local

Para desenvolver com recarregamento automático, rode a API com Poetry e apenas
o banco no Docker.

**Pré-requisitos adicionais:** Python 3.14 e Poetry 2.2 ou superior. O Python
3.14 é obrigatório: o código usa a sintaxe `except A, B:` da PEP 758.

```bash
poetry install                    # dependências da aplicação e de desenvolvimento
docker compose up -d db           # só o PostgreSQL, em 127.0.0.1:5432
poetry run alembic upgrade head   # aplica as migrações
poetry run task run               # fastapi dev, com reload, em :8000
```

### Tarefas disponíveis (taskipy)

| Tarefa | Comando | Descrição |
| --- | --- | --- |
| `task run` | `fastapi dev car_api/app.py` | Servidor de desenvolvimento com reload |
| `task lint` | `ruff check` | Verifica o código |
| `task format` | `ruff check --fix` e `ruff format` | Corrige e formata o código |
| `task test` | `ruff check`, `pytest` e `coverage html` | Lint, testes com cobertura e relatório HTML |
| `task docs` | `mkdocs serve -a 127.0.0.1:8001` | Documentação com recarregamento |

Execute com `poetry run task <nome>`.

### Migrações

```bash
poetry run alembic revision --autogenerate -m "descrição da mudança"
poetry run alembic upgrade head
```

Ao alterar o tamanho de uma coluna, ajuste também o `max_length` ou o
`max_digits` do schema correspondente.

## Variáveis de ambiente

Definidas no `.env`, a partir do `.env.example`.

| Variável | Uso | Exemplo |
| --- | --- | --- |
| `DATABASE_URL` | URL assíncrona do SQLAlchemy, usada fora do Docker | `postgresql+psycopg://car_api:senha@localhost:5432/car_api` |
| `JWT_SECRET_KEY` | Chave de assinatura dos tokens, com pelo menos 32 caracteres | Valor aleatório, gerado como no início rápido |
| `JWT_ALGORITHM` | Algoritmo de assinatura | `HS256` |
| `JWT_EXPIRATION_MINUTES` | Validade do token, em minutos | `30` |
| `DB_NAME` | Nome do banco criado pelo Compose | `car_api` |
| `DB_USER` | Usuário do banco | `car_api` |
| `DB_PASSWORD` | Senha do banco | Valor próprio |

Dentro do Compose, o `DATABASE_URL` é redefinido para usar o host `db`, então o
valor do `.env` só vale quando a API roda fora dos contêineres.

## Endpoints

Todas as rotas, exceto as marcadas como públicas, exigem o cabeçalho
`Authorization: Bearer <token>`.

| Método | Rota | Acesso | Descrição |
| --- | --- | --- | --- |
| `GET` | `/health_check` | Público | Verifica se a API está no ar |
| `POST` | `/api/v1/auth/token` | Público | Gera o token de acesso |
| `POST` | `/api/v1/auth/refresh_token` | Autenticado | Renova o token |
| `POST` | `/api/v1/users/` | Público | Cria um usuário |
| `GET` | `/api/v1/users/` | Autenticado | Lista usuários, com busca por username ou e-mail |
| `GET` | `/api/v1/users/{user_id}` | Autenticado | Busca um usuário |
| `PATCH` | `/api/v1/users/{user_id}` | Própria conta | Atualiza o usuário |
| `DELETE` | `/api/v1/users/{user_id}` | Própria conta | Exclui o usuário, se não tiver carros |
| `POST` | `/api/v1/brands/` | Autenticado | Cria uma marca |
| `GET` | `/api/v1/brands/` | Autenticado | Lista marcas, com busca por nome e filtro `is_active` |
| `GET` | `/api/v1/brands/{brand_id}` | Autenticado | Busca uma marca |
| `PATCH` | `/api/v1/brands/{brand_id}` | Autenticado | Atualiza a marca |
| `DELETE` | `/api/v1/brands/{brand_id}` | Autenticado | Exclui a marca, se não tiver carros |
| `POST` | `/api/v1/cars/` | Autenticado | Cria um carro em nome do próprio usuário |
| `GET` | `/api/v1/cars/` | Autenticado | Lista carros, com busca e filtros |
| `GET` | `/api/v1/cars/{car_id}` | Autenticado | Busca um carro |
| `PATCH` | `/api/v1/cars/{car_id}` | Proprietário | Atualiza ou transfere o carro |
| `DELETE` | `/api/v1/cars/{car_id}` | Proprietário | Exclui o carro |

A listagem de carros aceita `search`, `brand_id`, `owner_id`, `fuel_type`,
`transmission_type`, `is_available`, `min_price` e `max_price`, além de
`offset` e `limit`.

| Campo | Valores aceitos |
| --- | --- |
| `fuel_type` | `gasoline`, `ethanol`, `flex`, `diesel`, `electric`, `hybrid` |
| `transmission_type` | `manual`, `automatic`, `semi_automatic`, `cvt` |

Os detalhes de cada rota, os limites dos campos e as mensagens de erro estão em
[`docs/api-endpoints.md`](docs/api-endpoints.md).

## Exemplo de uso

```bash
# 1. Criar um usuário
curl -X POST http://127.0.0.1:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{"username": "leonardo", "email": "leo@exemplo.com", "password": "senha_segura_123"}'

# 2. Obter o token
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"email": "leo@exemplo.com", "password": "senha_segura_123"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# 3. Criar uma marca
curl -X POST http://127.0.0.1:8000/api/v1/brands/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Toyota", "description": "Marca japonesa"}'

# 4. Cadastrar um carro (owner_id deve ser o id do usuário autenticado)
curl -X POST http://127.0.0.1:8000/api/v1/cars/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "Corolla", "factory_year": 2022, "model_year": 2023,
       "color": "Prata", "plate": "ABC1D23", "fuel_type": "flex",
       "transmission_type": "automatic", "price": "120000.00",
       "brand_id": 1, "owner_id": 1}'

# 5. Listar carros flex até R$ 150.000
curl "http://127.0.0.1:8000/api/v1/cars/?fuel_type=flex&max_price=150000" \
  -H "Authorization: Bearer $TOKEN"
```

O mesmo fluxo pode ser feito pelo Swagger UI, em
<http://127.0.0.1:8000/docs>, usando o botão **Authorize** com o token.

## Testes e qualidade

A suíte usa **pytest** sobre um **SQLite em memória**, recriado a cada teste,
e não precisa do PostgreSQL nem do Docker. As quatro variáveis da aplicação
precisam estar definidas, no `.env` ou no ambiente, porque a aplicação lê as
configurações ao ser importada.

```bash
poetry run task test
```

A tarefa roda o lint do Ruff, executa os testes com cobertura e gera o
relatório HTML em `htmlcov/`.

| Item | Valor |
| --- | --- |
| Testes | 181, em 5 arquivos (incluindo os casos de `parametrize`) |
| Cobertura | 99% das linhas de `car_api/` |
| Meta mínima | 80% |
| Lint | Ruff com as regras `I`, `F`, `E`, `W`, `PL` e `PT`, linhas de até 79 caracteres e aspas simples |

Para rodar parte da suíte:

```bash
poetry run pytest tests/test_cars.py
poetry run pytest -k "delete and not forbidden"
```

Os testes não rodam dentro do contêiner: a imagem da API não inclui `tests/`
nem as dependências de desenvolvimento.

## CI/CD

Dois workflows do GitHub Actions automatizam a verificação e a publicação:

```mermaid
flowchart LR
    PR["Pull request ou push<br/>em develop/main"] --> CI["CI<br/>Ruff + pytest + hadolint"]
    Tag["Push da tag vX.Y.Z"] --> Check["Confere a versão<br/>com o pyproject.toml"]
    Check --> Test["Roda o CI"]
    Test --> Build["Publica as imagens<br/>no GHCR"]
    Build --> Smoke["Smoke test<br/>com PostgreSQL"]
    Smoke --> Rel["GitHub Release"]
```

| Workflow | Quando roda | O que faz |
| --- | --- | --- |
| [`ci.yml`](.github/workflows/ci.yml) | Pull requests e pushes para `develop` e `main` | `task test` (Ruff, pytest e cobertura) e hadolint nos dois Dockerfiles |
| [`release.yml`](.github/workflows/release.yml) | Push de uma tag `v*` | Confere a versão, reusa o CI, publica as imagens, sobe a stack com elas e cria a release |

O smoke test sobe a API, as migrações e o PostgreSQL com as imagens recém
publicadas e chama o `/health_check`. Ele cobre o que a suíte, em SQLite, não
alcança: a imagem real conectando no banco real.

Cada versão publicada fica disponível como imagem:

```bash
docker pull ghcr.io/leonardoalmeidagit/car-api:vX.Y.Z
```

Para subir a stack com as imagens publicadas, sem construir nada:

```bash
export COMPOSE_FILE=docker-compose.yml:docker-compose.release.yml
IMAGE_TAG=vX.Y.Z docker compose pull app migrations mkdocs
IMAGE_TAG=vX.Y.Z docker compose up -d --no-build
```

Os detalhes de cada job, as permissões e o que fazer se uma release falhar
estão em [`docs/ci-cd.md`](docs/ci-cd.md).

## Estrutura do projeto

```text
.
├── .github/workflows/      # CI (ci.yml) e release (release.yml)
├── car_api/
│   ├── app.py              # Aplicação FastAPI, routers e health check
│   ├── core/               # Banco (engine e sessão), segurança e configurações
│   ├── models/             # Modelos SQLAlchemy: User, Brand e Car
│   ├── routers/            # Rotas: auth, users, brands e cars
│   └── schemas/            # Schemas Pydantic de entrada e saída
├── docs/                   # Documentação completa (MkDocs)
├── migrations/             # Migrações do Alembic
├── tests/                  # Testes automatizados (pytest)
├── .env.example            # Modelo das variáveis de ambiente
├── .dockerignore
├── .readthedocs.yaml       # Build da documentação no Read the Docs
├── alembic.ini
├── docker-compose.yml      # Serviços db, migrations, app e mkdocs
├── docker-compose.release.yml  # Usa as imagens publicadas no GHCR
├── Dockerfile              # Imagem da API
├── Dockerfile.mkdocs       # Imagem da documentação (MkDocs + Nginx)
├── mkdocs.yml
├── poetry.lock
├── pyproject.toml          # Dependências, Ruff, pytest, coverage e tarefas
└── requirements_docs.txt   # Dependências da documentação
```

A descrição de cada arquivo está em [`docs/structure.md`](docs/structure.md).

## Documentação

A documentação completa fica em [`docs/`](docs/) e é gerada com MkDocs
Material. Para visualizá-la em <http://127.0.0.1:8001>:

```bash
poetry run task docs                      # com Poetry, recarregando ao editar
docker compose up -d --build mkdocs      # em contêiner, servida pelo Nginx
```

| Página | Conteúdo |
| --- | --- |
| [Visão geral](docs/overview.md) | Objetivo, funcionalidades, regras de negócio e tecnologias |
| [Pré-requisitos](docs/prerequisites.md) | O que instalar antes de começar |
| [Instalação](docs/installation.md) | Como rodar, com ou sem Docker |
| [Configuração](docs/configuration.md) | Variáveis de ambiente, Alembic, Ruff e taskipy |
| [Docker](docs/docker.md) | Serviços, imagens, comandos e problemas comuns |
| [Guidelines e padrões](docs/guidelines.md) | Convenções de código e de API |
| [Estrutura](docs/structure.md) | Diretórios e arquivos |
| [API Endpoints](docs/api-endpoints.md) | Rotas, parâmetros, limites, respostas e erros |
| [Modelagem do Sistema](docs/system-modeling.md) | Modelo de dados, arquitetura e fluxos |
| [Autenticação e Segurança](docs/authentication.md) | JWT, senhas, permissões e limitações |
| [Desenvolvimento](docs/development.md) | Tarefas do dia a dia e migrações |
| [Testes](docs/testing.md) | Suíte, fixtures, cobertura e como escrever testes |
| [CI/CD](docs/ci-cd.md) | Workflows, imagens publicadas e processo de release |
| [Deploy](docs/deployment.md) | Publicação com imagens publicadas ou build, atualização e backup |
| [Contribuição](docs/contributing.md) | Branches, commits, pull requests e versionamento |
| [Release Notes](docs/release-notes.md) | Histórico de versões |

## Limitações conhecidas

- Não há deploy automático: as versões são publicadas como imagens, mas o
  deploy em um servidor é manual.
- Os testes usam SQLite, que não aplica todos os limites do PostgreSQL; por
  isso os limites são validados nos schemas. O smoke test da release usa
  PostgreSQL, mas só confere se a aplicação sobe e responde.
- Não há perfil de administrador: todo usuário autenticado pode gerenciar
  marcas.
- Não há revogação de tokens nem limite de tentativas de login.

Os detalhes e o checklist para produção estão em
[`docs/authentication.md`](docs/authentication.md) e
[`docs/deployment.md`](docs/deployment.md).

## Contribuição

1. Crie uma branch a partir de `develop` (`feature/`, `fix/`, `docs/`,
   `test/`, `chore/`).
2. Faça a alteração, com testes e, se mudar um modelo, a migração.
3. Rode `poetry run task format` e `poetry run task test`.
4. Use [Conventional Commits](https://www.conventionalcommits.org/pt-br/), em
   inglês, como `feat: add car search by year`.
5. Abra um pull request para `develop`. O merge só entra com o CI verde.

Para publicar uma versão, basta enviar a tag depois do merge em `main`: o
workflow de release faz o resto. O fluxo completo, incluindo o processo de
release e tags, está em
[`docs/contributing.md`](docs/contributing.md). As mudanças de cada versão
estão em [`docs/release-notes.md`](docs/release-notes.md).

## Autor

Desenvolvido por **Leonardo Almeida**
([@LeonardoAlmeidaGit](https://github.com/LeonardoAlmeidaGit)).
