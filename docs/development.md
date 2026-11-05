# Desenvolvimento

## Tarefas do dia a dia

| Comando | O que faz |
| --- | --- |
| `poetry run task run` | Inicia a API com recarregamento automático na porta 8000 |
| `poetry run task lint` | Verifica o código com o Ruff |
| `poetry run task format` | Aplica correções automáticas e formata o código |
| `poetry run task test` | Roda o lint, os testes com cobertura e gera `htmlcov/` |
| `poetry run task docs` | Serve a documentação na porta 8001 |

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
4. Se alterou um modelo, crie a migração.
5. Rode `task format` e `task test`. O `task test` já executa o lint.
6. Atualize a documentação, se necessário.
7. Abra um pull request para `develop`.

## Migrações

As migrações ficam em `migrations/versions/` e são gerenciadas pelo Alembic.

### Criar uma migração

Altere o modelo e gere o arquivo:

```bash
poetry run alembic revision --autogenerate -m "add color to brands"
```

Revise o arquivo gerado antes de aplicá-lo. O `--autogenerate` não detecta todas
as mudanças, como renomeações de colunas, que aparecem como uma remoção seguida
de uma criação.

### Comandos úteis

| Comando | O que faz |
| --- | --- |
| `poetry run alembic upgrade head` | Aplica todas as migrações pendentes |
| `poetry run alembic downgrade -1` | Reverte a última migração |
| `poetry run alembic current` | Mostra a revisão atual do banco |
| `poetry run alembic history` | Lista o histórico de migrações |

### Limitação do SQLite

O SQLite tem suporte limitado a `ALTER TABLE`, e `migrations/env.py` não ativa o
modo `render_as_batch` do Alembic. Migrações que alteram ou removem colunas podem
exigir `op.batch_alter_table`, escrito manualmente.

### Recriar o banco local

> **Perigo:** Este procedimento apaga todos os dados locais.

```bash
rm car.db
poetry run alembic upgrade head
```

## Adicionando um recurso

Exemplo de passo a passo para um recurso chamado `dealers`:

1. **Modelo**: crie `car_api/models/dealers.py` e exporte a classe em
   `car_api/models/__init__.py`.
2. **Migração**: gere e aplique, como descrito acima.
3. **Schemas**: crie `car_api/schemas/dealers.py` com `DealerSchema`,
   `DealerUpdateSchema`, `DealerPublicSchema` e `DealerListPublicSchema`.
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

Versione o `pyproject.toml` e o `poetry.lock` juntos.

## Documentação

As páginas ficam em `docs/`, em português, com nomes de arquivo em inglês. Para
gerar o site estático e detectar links quebrados:

```bash
poetry run mkdocs build --strict
```

O resultado vai para `site/`, que não é versionado.

## Depuração

- **Consultas SQL**: passe `echo=True` para `create_async_engine`, em
  `car_api/core/database.py`, para exibi-las no log. Não versione essa mudança.
- **Conteúdo do token**: rode o trecho abaixo em um shell Python, usando
  `poetry run python`:

    ```python
    import jwt

    jwt.decode('SEU_TOKEN', options={'verify_signature': False})
    ```

- **Banco de dados**: se tiver o cliente SQLite instalado, abra o banco com
  `sqlite3 car.db`.
