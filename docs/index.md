# Car API

API REST para gerenciamento de carros, marcas e usuários, construída com
FastAPI, SQLAlchemy assíncrono e autenticação JWT.

> **Versão documentada**
>
> Esta documentação descreve a versão **0.3.0** (`pyproject.toml`).

## Início rápido

Com Python 3.14 e Poetry instalados:

```bash
git clone https://github.com/LeonardoAlmeidaGit/fastapi_test.git
cd fastapi_test
poetry install
cp .env.example .env        # depois, troque o valor de JWT_SECRET_KEY
poetry run alembic upgrade head
poetry run task run
```

Com o servidor no ar:

| Recurso | URL |
| --- | --- |
| API | <http://127.0.0.1:8000/api/v1> |
| Swagger UI | <http://127.0.0.1:8000/docs> |
| ReDoc | <http://127.0.0.1:8000/redoc> |
| Health check | <http://127.0.0.1:8000/health_check> |

O passo a passo completo está em [Instalação](installation.md).

## Conteúdo

### Primeiros passos

- [Visão geral](overview.md): objetivo, funcionalidades e tecnologias.
- [Pré-requisitos](prerequisites.md): o que instalar antes de começar.
- [Instalação](installation.md): como colocar o projeto para rodar.
- [Configuração](configuration.md): variáveis de ambiente e ferramentas.

### Referência

- [API Endpoints](api-endpoints.md): rotas, parâmetros, respostas e erros.
- [Modelagem do Sistema](system-modeling.md): modelo de dados, arquitetura e
  fluxos em diagramas.
- [Autenticação e Segurança](authentication.md): JWT, senhas, permissões e
  limitações conhecidas.
- [Estrutura](structure.md): diretórios e arquivos do projeto.

### Trabalhando no projeto

- [Guidelines e padrões](guidelines.md): convenções de código e de API.
- [Desenvolvimento](development.md): tarefas do dia a dia e migrações.
- [Testes](testing.md): situação atual e como escrever os primeiros testes.
- [Deploy](deployment.md): como publicar a aplicação.
- [Contribuição](contributing.md): branches, commits e pull requests.
- [Release Notes](release-notes.md): histórico de versões.

## Visualizando esta documentação

A documentação é gerada com MkDocs Material:

```bash
poetry run task docs
```

O site fica disponível em <http://127.0.0.1:8001>.
