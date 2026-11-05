# Configuração do Projeto

## Variáveis de ambiente

As configurações são carregadas pela classe `Settings`, em
`car_api/core/settings.py`, usando pydantic-settings.

| Variável | Tipo | Descrição | Exemplo |
| --- | --- | --- | --- |
| `DATABASE_URL` | `str` | URL assíncrona de conexão do SQLAlchemy | `sqlite+aiosqlite:///car.db` |
| `JWT_SECRET_KEY` | `str` | Chave usada para assinar os tokens | Valor aleatório longo |
| `JWT_ALGORITHM` | `str` | Algoritmo de assinatura | `HS256` |
| `JWT_EXPIRATION_MINUTES` | `int` | Validade do token, em minutos | `30` |

Exemplo de `.env`, igual ao `.env.example`:

```dotenv
DATABASE_URL='sqlite+aiosqlite:///car.db'
JWT_SECRET_KEY='troque-esta-chave'
JWT_ALGORITHM='HS256'
JWT_EXPIRATION_MINUTES=30
```

### Como os valores são carregados

- **Todas as variáveis são obrigatórias.** Não há valores padrão, e a aplicação
  não inicia se alguma estiver faltando.
- **Variáveis do ambiente têm prioridade** sobre o arquivo `.env`.
- **O `.env` é procurado no diretório atual.** Execute os comandos na raiz do
  projeto.
- **O caminho do SQLite também é relativo ao diretório atual.** Com
  `sqlite+aiosqlite:///car.db`, o arquivo fica onde o comando foi executado.

> **Proteja a chave JWT**
>
> Quem conhece `JWT_SECRET_KEY` consegue gerar tokens válidos para qualquer
> usuário. Nunca versione o `.env` (ele já está no `.gitignore`) e não use em
> produção o valor do `.env.example`.

## Alembic

O `alembic.ini` aponta para o diretório `migrations/`. O valor de
`sqlalchemy.url` nesse arquivo é apenas um marcador: `migrations/env.py` o
substitui por `DATABASE_URL`, então API e migrações sempre usam o mesmo banco.

`migrations/env.py` também registra `Base.metadata`, o que permite gerar
migrações automaticamente. Ao criar um modelo novo, exporte-o em
`car_api/models/__init__.py` para que o Alembic o detecte.

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

## pytest e coverage

Configurados em `[tool.pytest.ini_options]` e `[tool.coverage.run]`:

| Opção | Valor | Motivo |
| --- | --- | --- |
| `pythonpath` | `"."` | Permite importar `car_api` nos testes |
| `filterwarnings` | Ignora `StarletteDeprecationWarning` | O aviso sobre `httpx` no `TestClient` não afeta os testes |
| `asyncio_default_fixture_loop_scope` | `'function'` | Um *event loop* por teste |
| `concurrency` (coverage) | `["thread", "greenlet"]` | Mede as linhas executadas pelo SQLAlchemy assíncrono e pelo `TestClient` |

Os detalhes estão em [Testes](testing.md#configuracao).

## MkDocs

O `mkdocs.yml` define o tema Material, a navegação e o suporte a diagramas
Mermaid. Ao criar uma página em `docs/`, adicione-a também à seção `nav`.

## VS Code

O `.vscode/settings.json` define o Poetry como gerenciador de ambientes e de
pacotes da extensão Python.
