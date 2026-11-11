# Desenvolvimento

O fluxo recomendado é rodar a API com Poetry, para ter recarregamento
automático, e o PostgreSQL no Docker:

```bash
docker compose up -d db
poetry run alembic upgrade head
poetry run task run
```

O passo a passo completo está em
[Instalação](installation.md#opcao-2-poetry-com-o-banco-no-docker).

## Tarefas do dia a dia

| Comando | O que faz |
| --- | --- |
| `poetry run task run` | Inicia a API com recarregamento automático na porta 8000 |
| `poetry run task lint` | Verifica o código com o Ruff |
| `poetry run task format` | Aplica correções automáticas e formata o código |
| `poetry run task test` | Roda o lint, os testes com cobertura e gera `htmlcov/` |
| `poetry run task docs` | Serve a documentação na porta 8001 |
| `docker compose up -d db` | Sobe o PostgreSQL em `127.0.0.1:5432` |
| `docker compose up -d --build` | Sobe o ambiente completo em contêineres |

Para não repetir `poetry run`, ative o ambiente virtual:

```bash
eval $(poetry env activate)
task run
```

## Ciclo de trabalho

1. Crie uma branch a partir de `develop`, como descrito em
   [Contribuição](contributing.md).
2. Faça a alteração, seguindo as [guidelines](guidelines.md).
3. Escreva ou atualize os testes do comportamento alterado, como descrito em
   [Testes](testing.md#escrevendo-novos-testes).
4. Se alterou um modelo, crie a migração e ajuste os limites do schema.
5. Rode `task format` e `task test`. O `task test` já executa o lint.
6. Se a mudança afeta o banco, as dependências ou os Dockerfiles, confira o
   ambiente completo com `docker compose up -d --build`.
7. Atualize a documentação, se necessário.
8. Abra um pull request para `develop`. O [CI](ci-cd.md#ci-ciyml) roda o lint,
   os testes e o hadolint automaticamente.

## Migrações

As migrações ficam em `migrations/versions/` e são gerenciadas pelo Alembic.
Elas usam o banco de `DATABASE_URL`, então o PostgreSQL precisa estar no ar.

### Criar uma migração

Altere o modelo e gere o arquivo:

```bash
poetry run alembic revision --autogenerate -m "add color to brands"
```

Revise o arquivo gerado antes de aplicá-lo. O `--autogenerate` não detecta todas
as mudanças, como renomeações de colunas, que aparecem como uma remoção seguida
de uma criação.

Se a migração muda o tamanho de uma coluna, como `String(50)`, atualize o
`max_length` correspondente no schema. Os testes rodam em SQLite e não
detectam essa diferença. Veja [Guidelines](guidelines.md#schemas).

### Comandos úteis

| Comando | O que faz |
| --- | --- |
| `poetry run alembic upgrade head` | Aplica todas as migrações pendentes |
| `poetry run alembic downgrade -1` | Reverte a última migração |
| `poetry run alembic current` | Mostra a revisão atual do banco |
| `poetry run alembic history` | Lista o histórico de migrações |

Os mesmos comandos funcionam dentro do Docker, pelo serviço `migrations`:

```bash
docker compose build migrations
docker compose run --rm migrations poetry run alembic current
```

Reconstrua a imagem antes de rodar uma migração nova: o código, incluindo
`migrations/versions/`, é copiado para a imagem no build.

### Recriar o banco local

> **Perigo:** Este procedimento apaga todos os dados do PostgreSQL local.

```bash
docker compose down -v
docker compose up -d db
poetry run alembic upgrade head
```

## Adicionando um recurso

Exemplo de passo a passo para um recurso chamado `dealers`:

1. **Modelo**: crie `car_api/models/dealers.py` e exporte a classe em
   `car_api/models/__init__.py`.
2. **Migração**: gere e aplique, como descrito acima.
3. **Schemas**: crie `car_api/schemas/dealers.py` com `DealerSchema`,
   `DealerUpdateSchema`, `DealerPublicSchema` e `DealerListPublicSchema`. Use
   `max_length` igual ao tamanho de cada coluna `String(n)`.
4. **Rotas**: crie `car_api/routers/dealers.py`.
5. **Registro**: inclua o router em `car_api/app.py`:

    ```python
    app.include_router(
        router=dealers.router,
        prefix='/api/v1/dealers',
        tags=['dealers'],
    )
    ```

6. **Testes**: crie `tests/test_dealers.py` e, se necessário, uma fixture
   `dealer` em `tests/conftest.py`. O banco de testes é criado a partir de
   `Base.metadata`, então o novo modelo entra automaticamente, desde que esteja
   exportado em `car_api/models/__init__.py`.
7. **Documentação**: atualize [API Endpoints](api-endpoints.md) e o diagrama em
   [Modelagem do Sistema](system-modeling.md).

## Dependências

```bash
poetry add nome-do-pacote             # dependência da aplicação
poetry add --group dev nome-do-pacote # dependência de desenvolvimento
```

Versione o `pyproject.toml` e o `poetry.lock` juntos. A imagem Docker instala as
dependências a partir do `poetry.lock`, então reconstrua-a depois de alterá-lo:

```bash
docker compose build
```

As dependências de desenvolvimento não entram na imagem (`--without dev`).

## Documentação

As páginas ficam em `docs/`, em português, com nomes de arquivo em inglês. Para
gerar o site estático e detectar links quebrados:

```bash
poetry run mkdocs build --strict
```

O resultado vai para `site/`, que não é versionado. O build do serviço
`mkdocs` usa o mesmo `--strict`, então um aviso faz a imagem falhar.

Ao atualizar o MkDocs ou suas extensões, mantenha as versões do `pyproject.toml`
e do `requirements_docs.txt` iguais.

## Depuração

- **Consultas SQL**: passe `echo=True` para `create_async_engine`, em
  `car_api/core/database.py`, para exibi-las no log. Não versione essa mudança.
- **Logs dos contêineres**: `docker compose logs -f app` ou
  `docker compose logs migrations`.
- **Conteúdo do token**: rode o trecho abaixo em um shell Python, usando
  `poetry run python`:

    ```python
    import jwt

    jwt.decode('SEU_TOKEN', options={'verify_signature': False})
    ```

- **Banco de dados**: abra o `psql` no contêiner:

    ```bash
    docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
    ```

    Comandos úteis no `psql`: `\dt` lista as tabelas, `\d cars` mostra a
    estrutura de uma tabela e `\q` sai.
