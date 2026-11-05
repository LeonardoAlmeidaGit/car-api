# Release Notes

O formato é inspirado no [Keep a Changelog](https://keepachangelog.com/pt-BR/), e
as versões seguem o [Versionamento Semântico](https://semver.org/lang/pt-BR/). As
informações vêm das tags e do histórico do Git.

## Não lançado

Alterações já feitas depois do commit que define a versão 0.3.0.

### Adicionado

- Ruff para lint e formatação, e taskipy para tarefas (#20).
- MkDocs Material e extensões para a documentação (#21).
- Configuração do MkDocs (`mkdocs.yml`) e tarefa `task docs` (#21).
- Documentação do projeto em `docs/` (#21).
- Suíte de testes com pytest, pytest-asyncio e pytest-cov, executada em um
  SQLite em memória: 163 testes e 99% de cobertura (#22).
- Tarefa `task test`, que roda o lint antes dos testes e gera o relatório HTML
  de cobertura depois (#22).
- Configuração do pytest e do coverage no `pyproject.toml` (#22).

### Alterado

- O aviso `StarletteDeprecationWarning` do `TestClient` passa a ser filtrado na
  configuração do pytest (#23).
- Documentação revisada para refletir a suíte de testes.

### Corrigido

- Espaço ausente nas mensagens de erro ao excluir usuário ou marca com carros
  associados, que exibiam "usuárioque" e "marcaque" (#22).

## 0.3.0 (2026-11-03)

Autenticação JWT.

### Adicionado

- Login em `POST /api/v1/auth/token` e renovação em
  `POST /api/v1/auth/refresh_token` (#17).
- Proteção das rotas de usuários, marcas e carros, exceto o cadastro de usuário.
- Regras de propriedade: cada usuário só altera a própria conta e os próprios
  carros.
- Configurações `JWT_SECRET_KEY`, `JWT_ALGORITHM` e `JWT_EXPIRATION_MINUTES`.

### Mudanças incompatíveis

- Rotas antes públicas passam a exigir o cabeçalho `Authorization: Bearer`.
- Novas variáveis de ambiente obrigatórias: atualize o `.env` com base no
  `.env.example`.

### Corrigido

- Erro `500` ao excluir usuário que possui carros: agora a API responde `400`
  (#17).

## 0.2.0 (2026-11-01)

CRUD de marcas e carros.

### Adicionado

- CRUD de marcas, com busca por nome e filtro por status (#12).
- CRUD de carros, com busca textual, filtros e faixa de preço (#14).

### Corrigido

- Import circular entre os modelos (#13).

## 0.1.0 (2026-10-28)

Primeira versão, com CRUD de usuários persistido em banco.

### Adicionado

- Estrutura inicial do projeto com FastAPI.
- Endpoint `GET /health_check` (#1).
- Rotas e schemas de usuários (#3, #4, #5).
- Banco de dados com SQLAlchemy assíncrono e migrações com Alembic (#6).
- Modelos de carro e marca (#7).
- Persistência dos usuários no banco, com hash de senha (#8).

### Corrigido

- Endpoint de atualização de usuário (#9).
