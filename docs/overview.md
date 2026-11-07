# Visão geral

A Car API é uma API REST para cadastrar e consultar carros, suas marcas e seus
proprietários. Qualquer pessoa pode criar uma conta; as demais operações exigem
um token JWT, e cada usuário só pode alterar os próprios dados e os próprios
carros.

## Funcionalidades

- **Autenticação**: login por e-mail e senha, com emissão e renovação de token
  JWT.
- **Usuários**: cadastro público e CRUD autenticado, com senha armazenada como
  hash Argon2.
- **Marcas**: CRUD com nome único, busca por nome e filtro por status.
- **Carros**: CRUD com placa única, busca textual e filtros por marca,
  proprietário, combustível, transmissão, disponibilidade e faixa de preço.
- **Paginação**: `offset` e `limit` em todas as listagens, com até 100 registros
  por página.
- **Validação**: os schemas limitam o tamanho dos textos e a precisão do preço
  aos mesmos valores das colunas do banco. Veja
  [API Endpoints](api-endpoints.md#limites-dos-campos).
- **Documentação interativa**: Swagger UI e ReDoc gerados pelo FastAPI.
- **Ambiente em contêineres**: Docker Compose com a API, o PostgreSQL, as
  migrações e a documentação.
- **Testes automatizados**: suíte com pytest sobre um SQLite em memória, com
  cobertura acima de 80%.

## Regras de negócio

| Regra | Comportamento |
| --- | --- |
| Usuário | Só pode alterar ou excluir a própria conta |
| Carro | Só o proprietário pode alterar ou excluir |
| Criação de carro | `owner_id` precisa ser o do usuário autenticado |
| Transferência de carro | O proprietário pode alterar `owner_id` para outro usuário |
| Marca | Qualquer usuário autenticado pode criar, alterar ou excluir |
| Exclusão de marca | Bloqueada se houver carros associados |
| Exclusão de usuário | Bloqueada se houver carros associados |
| Unicidade | `username`, `email`, nome da marca e placa do carro |

## Tecnologias

| Categoria | Tecnologia | Versão |
| --- | --- | --- |
| Linguagem | Python | 3.14 (`>=3.14,<4.0`) |
| Framework web | FastAPI | 0.142.4 |
| Validação | Pydantic / pydantic-settings | 2.14.0 / 2.15.0 |
| ORM | SQLAlchemy (asyncio) | 2.1.4 |
| Banco de dados | PostgreSQL com psycopg 3 | 17.6 / 3.3.8 |
| Banco dos testes | SQLite em memória com aiosqlite | 0.22.1 (driver) |
| Migrações | Alembic | 1.20.0 |
| Hash de senha | pwdlib com Argon2 | 0.3.1 |
| Token | PyJWT | 2.15.1 |
| Contêineres | Docker e Docker Compose | Imagens `python:3.14-alpine3.24`, `postgres:17.6-bookworm` e `nginx:alpine` |
| Lint e formatação | Ruff | 0.17.3 |
| Tarefas | taskipy | 1.14.1 |
| Testes | pytest / pytest-asyncio / pytest-cov | 9.2.0 / 1.4.1.post1 / 7.1.0 |
| Documentação | MkDocs Material | 9.8.0 |

As versões das bibliotecas Python são as travadas no `poetry.lock`. As do
PostgreSQL e das imagens base vêm do `docker-compose.yml` e dos Dockerfiles.

## Situação atual do projeto

O projeto tem testes automatizados para todas as rotas, com 99% de cobertura,
e um ambiente Docker Compose que sobe a aplicação com PostgreSQL. Veja
[Testes](testing.md) e [Docker](docker.md).

Alguns itens comuns em projetos prontos para produção ainda não existem:

- **CI/CD**: não há pipeline, então os testes só rodam localmente e as imagens
  são construídas manualmente. Veja [Deploy](deployment.md).
- **Testes em PostgreSQL**: a suíte roda em SQLite, que não aplica os mesmos
  limites do banco de produção. Veja [Testes](testing.md#sqlite-nos-testes-e-postgresql-na-aplicacao).
- **Perfis de acesso**: não há papel de administrador, por isso todo usuário
  autenticado tem as mesmas permissões sobre marcas.

As limitações de segurança estão em
[Autenticação e Segurança](authentication.md#limitacoes-conhecidas).
