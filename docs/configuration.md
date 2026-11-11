# Configuração do Projeto

## Variáveis de ambiente

As variáveis ficam no `.env`, criado a partir do `.env.example`. Há dois grupos:
as lidas pela aplicação e as usadas apenas pelo Docker Compose.

### Aplicação

Carregadas pela classe `Settings`, em `car_api/core/settings.py`, usando
pydantic-settings.

| Variável | Tipo | Descrição | Exemplo |
| --- | --- | --- | --- |
| `DATABASE_URL` | `str` | URL assíncrona de conexão do SQLAlchemy | `postgresql+psycopg://car_api:senha@localhost:5432/car_api` |
| `JWT_SECRET_KEY` | `str` | Chave usada para assinar os tokens, com pelo menos 32 caracteres | Valor aleatório, gerado como em [Gerando o `JWT_SECRET_KEY`](#gerando-o-jwt_secret_key) |
| `JWT_ALGORITHM` | `str` | Algoritmo de assinatura | `HS256` |
| `JWT_EXPIRATION_MINUTES` | `int` | Validade do token, em minutos | `30` |

### Docker Compose

Usadas pelo `docker-compose.yml` para criar o banco e montar a URL de conexão
dos contêineres. A aplicação não as lê: `Settings` usa `extra='ignore'`, então
elas podem ficar no mesmo `.env` sem causar erro.

| Variável | Descrição | Exemplo |
| --- | --- | --- |
| `DB_NAME` | Nome do banco criado no PostgreSQL | `car_api` |
| `DB_USER` | Usuário do banco | `car_api` |
| `DB_PASSWORD` | Senha do usuário | Valor próprio |

Exemplo de `.env`, igual ao `.env.example`:

```dotenv
DATABASE_URL='postgresql+psycopg://car_api:troque-esta-senha@localhost:5432/car_api'
JWT_SECRET_KEY='troque-por-uma-chave-aleatoria-com-32-ou-mais-caracteres'
JWT_ALGORITHM='HS256'
JWT_EXPIRATION_MINUTES=30
DB_NAME='car_api'
DB_USER='car_api'
DB_PASSWORD='troque-esta-senha'
```

> **Mantenha as duas configurações do banco iguais**
>
> O usuário, a senha e o nome do banco aparecem tanto em `DATABASE_URL` quanto
> em `DB_USER`, `DB_PASSWORD` e `DB_NAME`. Ao alterar um, altere o outro.

### Como os valores são carregados

- **As quatro variáveis da aplicação são obrigatórias.** Não há valores padrão,
  e a aplicação não inicia se alguma estiver faltando.
- **Variáveis do ambiente têm prioridade** sobre o arquivo `.env`.
- **O `.env` é procurado no diretório atual.** Execute os comandos na raiz do
  projeto.
- **No Docker, o host do banco é `db`.** O Compose redefine `DATABASE_URL` nos
  serviços `app` e `migrations`, trocando `localhost` por `db`. O valor do
  `.env` vale para a API rodando fora do Docker. Veja
  [Docker](docker.md#variaveis-de-ambiente-no-compose).

### Formato do `DATABASE_URL`

```text
postgresql+psycopg://<usuário>:<senha>@<host>:<porta>/<banco>
```

O prefixo `postgresql+psycopg` seleciona o driver psycopg 3, que funciona no
modo assíncrono do SQLAlchemy. Caracteres especiais na senha, como `@`, `:` ou
`/`, precisam ser codificados na URL (por exemplo, `@` vira `%40`).

Para rodar a API com SQLite, sem PostgreSQL, use
`sqlite+aiosqlite:///car.db`. O driver já está instalado, porque os testes o
usam, mas o projeto é validado no PostgreSQL.

> **Proteja os segredos**
>
> Quem conhece `JWT_SECRET_KEY` consegue gerar tokens válidos para qualquer
> usuário. Nunca versione o `.env` (ele já está no `.gitignore` e no
> `.dockerignore`) e não use em produção os valores do `.env.example`.

### Gerando o `JWT_SECRET_KEY`

O algoritmo `HS256` usa uma chave de 256 bits, ou seja, 32 bytes. Com uma chave
menor, o PyJWT emite um `InsecureKeyLengthWarning` a cada token criado. Gere um
valor aleatório com:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

O comando gera 86 caracteres, bem acima do mínimo. O valor do `.env.example` só
tem o tamanho certo para não gerar o aviso: troque-o no seu `.env`.

## Alembic

O `alembic.ini` aponta para o diretório `migrations/`. O valor de
`sqlalchemy.url` nesse arquivo é apenas um marcador: `migrations/env.py` o
substitui por `DATABASE_URL`, então API e migrações sempre usam o mesmo banco.

`migrations/env.py` também registra `Base.metadata`, o que permite gerar
migrações automaticamente. Ao criar um modelo novo, exporte-o em
`car_api/models/__init__.py` para que o Alembic o detecte.

## Docker

Os arquivos de contêiner ficam na raiz:

| Arquivo | Uso |
| --- | --- |
| `Dockerfile` | Imagem da API, usada pelos serviços `app` e `migrations` |
| `Dockerfile.mkdocs` | Imagem da documentação, servida pelo Nginx |
| `docker-compose.yml` | Serviços `db`, `migrations`, `app` e `mkdocs` |
| `.dockerignore` | Arquivos que não entram no contexto de build |

Os detalhes estão em [Docker](docker.md).

## Ruff

Configurado em `pyproject.toml`:

| Opção | Valor |
| --- | --- |
| Tamanho máximo de linha | 79 caracteres |
| Regras ativas | `I` (imports), `F` (Pyflakes), `E` e `W` (pycodestyle), `PL` (Pylint), `PT` (pytest) |
| Regras ignoradas | `PLR2004`, `PLR0913`, `PLR0917` |
| Aspas | Simples |
| Modo `preview` | Ativo no lint e na formatação |
| Excluídos | `migrations/`, ambientes virtuais e diretórios de cache e build, entre outros |

As regras `PT` (flake8-pytest-style) se aplicam aos arquivos em `tests/`.

## taskipy

Atalhos definidos em `[tool.taskipy.tasks]`:

| Tarefa | Comando executado |
| --- | --- |
| `task run` | `fastapi dev car_api/app.py` |
| `task lint` | `ruff check` |
| `task pre_format` | `ruff check --fix` |
| `task format` | `ruff format` |
| `task pre_test` | `task lint` |
| `task test` | `pytest -s -x --cov=car_api -vv` |
| `task post_test` | `coverage html` |
| `task docs` | `mkdocs serve -a 127.0.0.1:8001` |

O taskipy executa automaticamente as tarefas com os prefixos `pre_` e `post_`:

- `task format` roda antes o `pre_format`, que aplica as correções do Ruff.
- `task test` roda antes o `pre_test`, que executa o lint, e depois o
  `post_test`, que gera o relatório HTML de cobertura. Se o lint falhar, os
  testes não são executados.

> **Nota:** `task docs` e o serviço `mkdocs` do Compose usam a mesma porta,
> 8001. Rode apenas um deles por vez.

## pytest e coverage

Configurados em `[tool.pytest.ini_options]` e `[tool.coverage.run]`:

| Opção | Valor | Motivo |
| --- | --- | --- |
| `pythonpath` | `"."` | Permite importar `car_api` nos testes |
| `filterwarnings` | Ignora `StarletteDeprecationWarning` | O aviso sobre `httpx` no `TestClient` não afeta os testes |
| `asyncio_default_fixture_loop_scope` | `'function'` | Um *event loop* por teste |
| `concurrency` (coverage) | `["thread", "greenlet"]` | Mede as linhas executadas pelo SQLAlchemy assíncrono e pelo `TestClient` |

Os detalhes estão em [Testes](testing.md#configuracao).

## Documentação

| Arquivo | Uso |
| --- | --- |
| `mkdocs.yml` | Tema Material, navegação e suporte a diagramas Mermaid |
| `requirements_docs.txt` | Versões fixas de `mkdocs`, `mkdocs-material` e `pymdown-extensions`, usadas pelo `Dockerfile.mkdocs` e pelo Read the Docs |
| `.readthedocs.yaml` | Build no Read the Docs, com Ubuntu 24.04 e Python 3.14 |

Ao criar uma página em `docs/`, adicione-a também à seção `nav` do
`mkdocs.yml`. Ao atualizar o MkDocs no `pyproject.toml`, atualize também o
`requirements_docs.txt`, para manter as versões iguais.

## VS Code

O `.vscode/settings.json` define o Poetry como gerenciador de ambientes e de
pacotes da extensão Python.
