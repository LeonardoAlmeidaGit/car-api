# Car API

API REST para gerenciamento de carros, marcas e usuários, construída com
FastAPI, SQLAlchemy assíncrono, PostgreSQL e autenticação JWT.

> **Versão documentada**
>
> Esta documentação descreve a versão **0.4.0** (`pyproject.toml`).

## Início rápido

Com Docker e o plugin Compose instalados:

```bash
git clone https://github.com/LeonardoAlmeidaGit/car-api.git
cd car-api
cp .env.example .env        # depois, troque JWT_SECRET_KEY e DB_PASSWORD
docker compose up -d --build
```

O Compose sobe o PostgreSQL, aplica as migrações e inicia a API. Para
desenvolver com Poetry e recarregamento automático, veja a
[opção 2 da Instalação](installation.md#opcao-2-poetry-com-o-banco-no-docker).

Para rodar a suíte de testes, que usa um SQLite em memória e não precisa do
PostgreSQL:

```bash
poetry install
poetry run task test
```

Com o servidor no ar:

| Recurso | URL |
| --- | --- |
| API | <http://127.0.0.1:8000/api/v1> |
| Swagger UI | <http://127.0.0.1:8000/docs> |
| ReDoc | <http://127.0.0.1:8000/redoc> |
| Health check | <http://127.0.0.1:8000/health_check> |
| Esta documentação | <http://127.0.0.1:8001> |

## Conteúdo

### Primeiros passos

- [Visão geral](overview.md): objetivo, funcionalidades e tecnologias.
- [Pré-requisitos](prerequisites.md): o que instalar antes de começar.
- [Instalação](installation.md): como colocar o projeto para rodar, com ou sem
  Docker.
- [Configuração](configuration.md): variáveis de ambiente e ferramentas.
- [Docker](docker.md): serviços, imagens e comandos do Compose.

### Referência

- [API Endpoints](api-endpoints.md): rotas, parâmetros, limites dos campos,
  respostas e erros.
- [Modelagem do Sistema](system-modeling.md): modelo de dados, arquitetura e
  fluxos em diagramas.
- [Autenticação e Segurança](authentication.md): JWT, senhas, permissões e
  limitações conhecidas.
- [Estrutura](structure.md): diretórios e arquivos do projeto.

### Trabalhando no projeto

- [Guidelines e padrões](guidelines.md): convenções de código e de API.
- [Desenvolvimento](development.md): tarefas do dia a dia e migrações.
- [Testes](testing.md): como rodar a suíte, fixtures, cobertura e como
  escrever novos testes.
- [CI/CD](ci-cd.md): workflows do GitHub Actions, imagens publicadas e
  processo de release.
- [Deploy](deployment.md): como publicar a aplicação.
- [Contribuição](contributing.md): branches, commits e pull requests.
- [Release Notes](release-notes.md): histórico de versões.

## Visualizando esta documentação

A documentação é gerada com MkDocs Material. Com Poetry:

```bash
poetry run task docs
```

Ou em contêiner, com o site já compilado e servido pelo Nginx:

```bash
docker compose up -d --build mkdocs
```

Nos dois casos, o site fica disponível em <http://127.0.0.1:8001>.
