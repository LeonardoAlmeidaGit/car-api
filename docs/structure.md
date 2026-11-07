# Estrutura do Projeto

```text
.
├── car_api/                  # Código da aplicação
│   ├── __init__.py
│   ├── app.py                # Instância do FastAPI, routers e health check
│   ├── core/                 # Infraestrutura compartilhada
│   │   ├── database.py       # Engine assíncrona e dependência get_session
│   │   ├── security.py       # Senhas, JWT e verificações de permissão
│   │   └── settings.py       # Leitura das variáveis de ambiente
│   ├── models/               # Modelos do SQLAlchemy
│   │   ├── __init__.py       # Exporta Base, Brand, Car e User
│   │   ├── base.py           # Classe DeclarativeBase
│   │   ├── cars.py           # Brand, Car, FuelType e TransmissionType
│   │   └── users.py          # User
│   ├── routers/              # Rotas da API
│   │   ├── auth.py           # /api/v1/auth
│   │   ├── brands.py         # /api/v1/brands
│   │   ├── cars.py           # /api/v1/cars
│   │   └── users.py          # /api/v1/users
│   └── schemas/              # Schemas do Pydantic
│       ├── auth.py           # LoginRequest e Token
│       ├── brands.py         # Entrada e saída de marcas
│       ├── cars.py           # Entrada e saída de carros
│       └── users.py          # Entrada e saída de usuários
├── docs/                     # Esta documentação (MkDocs)
├── migrations/               # Migrações do Alembic
│   ├── README
│   ├── env.py                # Conecta o Alembic às configurações e modelos
│   ├── script.py.mako        # Modelo de novas migrações
│   └── versions/
│       ├── a22b0e6036d8_create_users_table.py
│       └── 00b46928ad50_create_car_and_brand_tables.py
├── tests/                    # Testes automatizados (pytest)
│   ├── __init__.py
│   ├── conftest.py           # Banco em memória, TestClient e fixtures de dados
│   ├── test_auth.py          # Senhas, JWT, login, renovação e permissões
│   ├── test_brands.py        # CRUD de marcas
│   ├── test_cars.py          # CRUD de carros
│   ├── test_db.py            # Conexão, tabelas e restrições do banco
│   └── test_users.py         # CRUD de usuários
├── .vscode/settings.json     # Gerenciador de ambientes no VS Code
├── .coverage                 # Dados de cobertura (não versionado)
├── .dockerignore             # Arquivos fora do contexto de build do Docker
├── .env                      # Configuração local (não versionado)
├── .env.example              # Modelo do .env
├── .gitignore
├── .readthedocs.yaml         # Build da documentação no Read the Docs
├── Dockerfile                # Imagem da API (serviços app e migrations)
├── Dockerfile.mkdocs         # Imagem da documentação (MkDocs + Nginx)
├── README.md                 # Apresentação do projeto, com link para esta documentação
├── alembic.ini               # Configuração do Alembic
├── car.db                    # Banco SQLite antigo, não usado com PostgreSQL (não versionado)
├── docker-compose.yml        # Serviços db, migrations, app e mkdocs
├── htmlcov/                  # Relatório HTML de cobertura (não versionado)
├── mkdocs.yml                # Configuração da documentação
├── poetry.lock               # Versões travadas das dependências
├── pyproject.toml            # Metadados, dependências, Ruff, pytest, coverage e taskipy
└── requirements_docs.txt     # Dependências da documentação, com versões fixas
```

Os diretórios `core/`, `routers/` e `schemas/` não têm `__init__.py`. Eles
funcionam como *namespace packages* do Python, e os imports absolutos, como
`from car_api.core.settings import Settings`, funcionam normalmente.

O `car.db` é o banco da época em que o projeto usava SQLite. Desde a mudança
para o PostgreSQL, ele não é mais lido nem criado e pode ser apagado.

## Arquivos principais

### `car_api/app.py`

Cria a aplicação, registra os quatro routers e define `GET /health_check`. É o
ponto de entrada usado por `fastapi dev` e `fastapi run`.

### `car_api/core/database.py`

Cria a engine assíncrona a partir de `DATABASE_URL` e expõe `get_session`, que
abre uma `AsyncSession` por requisição. O driver é escolhido pelo prefixo da
URL: `postgresql+psycopg` na aplicação e `sqlite+aiosqlite` nos testes.

### `car_api/core/security.py`

| Função | Responsabilidade |
| --- | --- |
| `get_password_hash` | Gera o hash da senha |
| `verify_password` | Compara a senha com o hash |
| `create_access_token` | Gera o JWT com a data de expiração |
| `verify_token` | Valida o JWT e trata expiração e token inválido |
| `authenticate_user` | Verifica e-mail e senha no login |
| `get_current_user` | Dependência que identifica o usuário pelo token |
| `verify_car_ownership` | Exige que o usuário seja o dono do carro |
| `verify_user_yourself` | Exige que o usuário esteja alterando a própria conta |

### `car_api/core/settings.py`

Define a classe `Settings`. Veja [Configuração](configuration.md).

### `migrations/versions/`

| Revisão | Depende de | Descrição |
| --- | --- | --- |
| `a22b0e6036d8` | Nenhuma | Cria a tabela `users` |
| `00b46928ad50` | `a22b0e6036d8` | Cria as tabelas `brands` e `cars` e o índice único `ix_cars_plate` |

### `tests/conftest.py`

Cria o banco SQLite em memória, substitui a dependência `get_session` no
`TestClient` e define as fixtures de usuários, tokens, marcas e carros usadas
pelos testes. Veja [Testes](testing.md#fixtures-disponiveis).

### Arquivos do Docker

| Arquivo | Conteúdo |
| --- | --- |
| `Dockerfile` | Imagem Alpine com Python 3.14 e Poetry, que roda a API como usuário `car_api` |
| `Dockerfile.mkdocs` | Build em dois estágios: compila o site com MkDocs e o serve com Nginx |
| `docker-compose.yml` | Serviços, dependências entre eles, portas e o volume `postgres_data` |
| `.dockerignore` | Exclui segredos, caches, testes e o `car.db` da imagem |

Veja [Docker](docker.md).

## Onde alterar cada coisa

| Para... | Altere |
| --- | --- |
| Adicionar uma rota | `car_api/routers/` e, se for um recurso novo, `car_api/app.py` |
| Mudar uma validação | `car_api/schemas/` |
| Mudar uma tabela | `car_api/models/`, crie uma migração e ajuste o `max_length` no schema |
| Adicionar uma configuração | `car_api/core/settings.py`, `.env.example` e, se o contêiner precisar dela, `docker-compose.yml` |
| Mudar uma regra de permissão | `car_api/core/security.py` |
| Adicionar um teste | `tests/test_<recurso>.py`; fixtures compartilhadas em `tests/conftest.py` |
| Adicionar uma tarefa | `[tool.taskipy.tasks]` em `pyproject.toml` |
| Mudar a imagem ou os serviços | `Dockerfile`, `docker-compose.yml` e `.dockerignore` |
| Adicionar uma página de documentação | `docs/` e `nav` em `mkdocs.yml` |
| Atualizar o MkDocs | `pyproject.toml` e `requirements_docs.txt` |
