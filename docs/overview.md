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
- **Documentação interativa**: Swagger UI e ReDoc gerados pelo FastAPI.
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

| Categoria | Tecnologia | Versão travada no `poetry.lock` |
| --- | --- | --- |
| Linguagem | Python | 3.14 (`>=3.14,<4.0`) |
| Framework web | FastAPI | 0.142.4 |
| Validação | Pydantic / pydantic-settings | 2.14.0 / 2.15.0 |
| ORM | SQLAlchemy (asyncio) | 2.1.4 |
| Banco de dados | SQLite com aiosqlite | 0.22.1 (driver) |
| Migrações | Alembic | 1.20.0 |
| Hash de senha | pwdlib com Argon2 | 0.3.1 |
| Token | PyJWT | 2.15.1 |
| Lint e formatação | Ruff | 0.17.3 |
| Tarefas | taskipy | 1.14.1 |
| Testes | pytest / pytest-asyncio / pytest-cov | 9.2.0 / 1.4.1.post1 / 7.1.0 |
| Documentação | MkDocs Material | 9.8.0 |

## Situação atual do projeto

O projeto tem testes automatizados para todas as rotas, com 99% de cobertura.
Veja [Testes](testing.md).

Alguns itens comuns em projetos prontos para produção ainda não existem:

- **Docker e CI/CD**: o repositório não tem `Dockerfile` nem pipeline, então os
  testes só rodam localmente. Veja [Deploy](deployment.md).
- **Perfis de acesso**: não há papel de administrador, por isso todo usuário
  autenticado tem as mesmas permissões sobre marcas.

As limitações de segurança estão em
[Autenticação e Segurança](authentication.md#limitacoes-conhecidas).
