# Pré-requisitos

## Obrigatórios

| Ferramenta | Versão | Observação |
| --- | --- | --- |
| [Python](https://www.python.org/downloads/) | 3.14 ou superior (abaixo de 4.0) | Versões anteriores não funcionam (veja abaixo) |
| [Poetry](https://python-poetry.org/docs/#installation) | 2.2 ou superior | O projeto usa `[dependency-groups]`. Testado com a 2.5.1 |
| [Git](https://git-scm.com/downloads) | Qualquer versão recente | Para clonar o repositório |

> **Python 3.14 é obrigatório**
>
> Além da restrição em `requires-python`, o código usa a sintaxe
> `except ValueError, TypeError:` em `car_api/core/security.py`, válida apenas
> a partir do Python 3.14 (PEP 758). Em versões anteriores, ela causa
> `SyntaxError`.

Para conferir o que está instalado:

```bash
python3 --version
poetry --version
git --version
```

## Banco de dados

Nenhuma instalação é necessária. O projeto usa SQLite por padrão, e o arquivo
`car.db` é criado na raiz do projeto ao rodar as migrações.

## Opcionais

- **curl**, **HTTPie** ou **Postman**, para chamar a API. O Swagger UI em `/docs`
  também resolve.
- **VS Code** com a extensão Python. O arquivo `.vscode/settings.json` já define
  o Poetry como gerenciador de ambientes.

## Sistema operacional

O projeto foi desenvolvido no Ubuntu via WSL 2. Os comandos desta documentação
usam a sintaxe do Bash; no Windows, recomenda-se executá-los dentro do WSL.
