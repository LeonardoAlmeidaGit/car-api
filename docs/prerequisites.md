# Pré-requisitos

O que instalar depende da forma de rodar o projeto, descrita em
[Instalação](installation.md).

| Ferramenta | Versão | Só Docker | Desenvolvimento |
| --- | --- | --- | --- |
| [Git](https://git-scm.com/downloads) | Qualquer versão recente | Sim | Sim |
| [Docker Engine](https://docs.docker.com/engine/install/) ou [Docker Desktop](https://docs.docker.com/desktop/) | Com o plugin Compose v2 (`docker compose`) | Sim | Sim, para o PostgreSQL |
| [Python](https://www.python.org/downloads/) | 3.14 ou superior (abaixo de 4.0) | Não | Sim |
| [Poetry](https://python-poetry.org/docs/#installation) | 2.2 ou superior | Não | Sim |

O Poetry precisa ser 2.2 ou superior porque o projeto usa `[dependency-groups]`.
A imagem Docker usa a versão 2.5.1.

> **Python 3.14 é obrigatório**
>
> Além da restrição em `requires-python`, o código usa a sintaxe
> `except ValueError, TypeError:` em `car_api/core/security.py`, válida apenas
> a partir do Python 3.14 (PEP 758). Em versões anteriores, ela causa
> `SyntaxError`.

Para conferir o que está instalado:

```bash
git --version
docker --version
docker compose version
python3 --version
poetry --version
```

O comando `docker compose`, com espaço, é o Compose v2. O antigo
`docker-compose`, com hífen, não é usado nesta documentação.

## Banco de dados

A aplicação usa **PostgreSQL 17.6**, que roda no contêiner `db` do Compose. Não
é preciso instalar o PostgreSQL na máquina.

Se já houver um PostgreSQL local usando a porta 5432, pare-o ou altere a porta
publicada em `docker-compose.yml`.

Os testes automatizados usam um SQLite em memória, pelo driver `aiosqlite`, que
o `poetry install` já instala.

## Opcionais

- **curl**, **HTTPie** ou **Postman**, para chamar a API. O Swagger UI em `/docs`
  também resolve.
- **DBeaver**, **pgAdmin** ou outro cliente PostgreSQL, para inspecionar o banco
  em `127.0.0.1:5432`.
- **VS Code** com a extensão Python. O arquivo `.vscode/settings.json` já define
  o Poetry como gerenciador de ambientes.

## Sistema operacional

O projeto foi desenvolvido no Ubuntu via WSL 2, com o Docker disponível dentro
do WSL. Os comandos desta documentação usam a sintaxe do Bash; no Windows,
recomenda-se executá-los dentro do WSL.
