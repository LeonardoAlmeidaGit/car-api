# Release Notes

O formato é inspirado no [Keep a Changelog](https://keepachangelog.com/pt-BR/), e
as versões seguem o [Versionamento Semântico](https://semver.org/lang/pt-BR/). As
informações vêm das tags e do histórico do Git.

## 1.0.0 (2026-11-11)

Primeira versão estável: CI/CD com GitHub Actions e imagens publicadas no
GitHub Container Registry.

### Adicionado

- Workflow de CI (`ci.yml`): Ruff, pytest com cobertura e hadolint nos dois
  Dockerfiles em todo pull request e push para `develop` e `main` (#33).
- Workflow de release (`release.yml`): no push de uma tag, confere a versão
  com o `pyproject.toml`, reusa o CI, publica as imagens no GHCR, roda um smoke
  test com PostgreSQL e cria a GitHub Release (#34).
- `docker-compose.release.yml`, que sobe a stack com as imagens publicadas, na
  versão definida em `IMAGE_TAG` (#34).
- Página [CI/CD](ci-cd.md) na documentação e seção de CI/CD no README, com o
  badge de status do CI.
- Deploy com as imagens publicadas e rollback trocando o `IMAGE_TAG`, em
  [Deploy](deployment.md).

### Alterado

- `Dockerfile` com a versão do `curl` fixada e `pipefail` no shell `ash`, como
  exige o hadolint (#32).
- `.dockerignore` exclui também `.github/` (#33).
- `JWT_SECRET_KEY` do `.env.example` com mais de 32 caracteres, o mínimo para o
  HS256 sem avisos do PyJWT.
- Repositório renomeado de `fastapi_test` para `car-api`.
- Versionamento a partir da 1.0.0 e processo de release pelo workflow, em
  [Contribuição](contributing.md#versionamento).

### Corrigido

- A documentação dizia que uma página fora do `nav` faz o build do MkDocs
  falhar; ela só não aparece no menu.

### Mudanças incompatíveis

- Nenhuma na API. A versão 1.0.0 marca a API como estável: a partir dela, uma
  mudança incompatível exige uma nova versão `MAJOR`.

## 0.4.0 (2026-11-07)

Docker, PostgreSQL e limites de tamanho nos schemas.

### Adicionado

- Ambiente Docker: `Dockerfile` da API, `Dockerfile.mkdocs` da documentação e
  `docker-compose.yml` com os serviços `db`, `migrations`, `app` e `mkdocs`
  (#27).
- `.dockerignore`, que mantém segredos, caches, testes e o `car.db` fora das
  imagens (#27).
- Configuração do Read the Docs (`.readthedocs.yaml`) e `requirements_docs.txt`
  com as versões da documentação (#27).
- Variáveis `DB_NAME`, `DB_USER` e `DB_PASSWORD` no `.env.example`, usadas pelo
  Compose (#27).
- Testes dos limites de tamanho e de precisão nos schemas: 181 testes no total
  (#28).
- Página [Docker](docker.md) na documentação.
- README do projeto, com resumo, tecnologias e como rodar.

### Alterado

- Banco de dados da aplicação passa de SQLite para **PostgreSQL 17.6**, com o
  driver psycopg 3 (#27). Os testes continuam em SQLite em memória.
- Documentação revisada para o PostgreSQL e o Docker: instalação, configuração,
  deploy, desenvolvimento, testes, estrutura e diagramas.

### Corrigido

- Textos e preços acima do tamanho das colunas eram enviados ao banco e, no
  PostgreSQL, resultavam em `500`. Agora os schemas aplicam os limites e a API
  responde `422`: `username` até 30 caracteres, nome da marca até 50, modelo
  até 100, cor até 30 e preço com até 10 dígitos e 2 casas decimais (#28).

### Mudanças incompatíveis

- `DATABASE_URL` passa a apontar para o PostgreSQL. Atualize o `.env` com base
  no `.env.example`. Os dados do `car.db` não são migrados automaticamente.
- Requisições com valores acima dos novos limites, antes aceitas no SQLite,
  passam a receber `422`.

## 0.3.1 (2026-11-05)

Ferramentas de qualidade, documentação e testes automatizados.

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
- Documentação revisada para refletir a suíte de testes (#24).
- Versão atualizada para 0.3.1 (#25).

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
