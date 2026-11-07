# Deploy

A forma suportada de publicar a aplicação é com as imagens Docker do projeto.
O `docker-compose.yml` descreve o ambiente completo e serve de base para um
servidor único. Ainda não há pipeline de CI/CD nem ambiente de produção
definido no repositório.

## Antes de publicar

1. Confira o [checklist de segurança](authentication.md#checklist-para-producao).
2. Defina a versão a publicar e rode `poetry run task test` nela. Como não há
   CI, essa verificação é manual.
3. Confira se todas as migrações estão versionadas em `migrations/versions/`.

## Banco de dados

A aplicação usa PostgreSQL 17.6, pelo driver psycopg 3. No Compose, os dados
ficam no volume nomeado `postgres_data`, que sobrevive a `docker compose down`,
mas não a `docker compose down -v`.

Também é possível usar um PostgreSQL gerenciado, fora do Compose. Nesse caso,
aponte o `DATABASE_URL` dos serviços `app` e `migrations` para ele e remova o
serviço `db`.

> **Nota:** A suíte de testes roda em SQLite em memória, não em PostgreSQL. Ela
> não detecta diferenças entre os bancos, como o limite de `String(n)`, que o
> SQLite não aplica. Esses limites estão protegidos pelos schemas, mas valide
> as mudanças de modelo também no PostgreSQL antes de publicar.

## Publicando com Docker Compose

### 1. Obter o código

```bash
git clone https://github.com/LeonardoAlmeidaGit/fastapi_test.git
cd fastapi_test
git checkout <versão>
```

### 2. Configurar o ambiente

Crie o `.env` no servidor com valores próprios:

```dotenv
DATABASE_URL='postgresql+psycopg://car_api:<senha>@localhost:5432/car_api'
JWT_SECRET_KEY='<valor gerado com secrets.token_urlsafe(64)>'
JWT_ALGORITHM='HS256'
JWT_EXPIRATION_MINUTES=30
DB_NAME='car_api'
DB_USER='car_api'
DB_PASSWORD='<senha>'
```

O `.env` não entra na imagem: o Compose o lê ao iniciar os contêineres.
Restrinja o acesso ao arquivo, por exemplo com `chmod 600 .env`.

### 3. Subir os serviços

```bash
docker compose up -d --build db migrations app
```

O serviço `mkdocs` é opcional em produção. Sem ele no comando, a documentação
não é publicada junto.

As migrações rodam automaticamente antes da API. Confira o resultado:

```bash
docker compose ps -a
docker compose logs migrations
```

### 4. Configurar HTTPS

A aplicação não trata TLS. Coloque um proxy reverso, como Nginx ou Caddy, à
frente dela, encaminhando para a porta 8000. Sem HTTPS, senhas e tokens
trafegam em texto claro.

> **Atenção:** O `docker-compose.yml` publica a API em `0.0.0.0:8000`, acessível
> por qualquer interface do servidor. Com um proxy no mesmo host, troque para
> `"127.0.0.1:8000:8000"` ou bloqueie a porta no firewall, para que o acesso
> passe sempre pelo HTTPS. O banco já é publicado apenas em `127.0.0.1`.

### 5. Verificar

```bash
curl https://seu-dominio/health_check
```

Resposta esperada: `{"message":"ok"}`.

O endpoint não consulta o banco. Ele confirma que a aplicação responde, mas não
que o banco está acessível: confira também uma rota autenticada.

### Reinício automático

Os serviços do `docker-compose.yml` não definem `restart`. Para que a API e o
banco voltem depois de uma falha ou de um reinício do servidor, adicione
`restart: unless-stopped` aos serviços `app` e `db`. Não adicione ao
`migrations`, que deve rodar uma vez e encerrar.

## Atualizando uma versão

1. Faça backup do banco, como descrito abaixo.
2. Atualize o código com `git fetch --tags` e `git checkout <versão>`.
3. Reconstrua e suba os serviços:

    ```bash
    docker compose up -d --build db migrations app
    ```

    O `migrations` roda de novo e aplica as migrações novas antes de a API
    reiniciar.

4. Verifique o `/health_check` e uma rota autenticada.

Para reverter uma versão que mudou o esquema, desfaça a migração **antes** de
voltar o código, enquanto a imagem ainda conhece a migração nova:

```bash
docker compose run --rm migrations poetry run alembic downgrade <revisão>
git checkout <versão anterior>
docker compose up -d --build db migrations app
```

Se a versão não mudou o esquema, basta voltar o código e reconstruir. Como o
downgrade pode perder dados, prefira restaurar o backup quando houver
dúvida.

## Backup e restauração

Gerar um backup:

```bash
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB"' > backup.sql
```

Restaurar em um banco vazio:

```bash
docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < backup.sql
```

Guarde os backups fora do servidor.

## Sem Docker

Também é possível rodar a aplicação diretamente em um servidor com Python 3.14
e um PostgreSQL acessível:

```bash
poetry install --without dev
poetry run alembic upgrade head
poetry run fastapi run car_api/app.py --host 127.0.0.1 --port 8000
```

Use um gerenciador de processos, como o systemd, para manter o serviço ativo.
Não use `task run` em produção: ele executa `fastapi dev`, que recarrega o
código automaticamente e é destinado ao desenvolvimento.

## Publicando a documentação

Há três opções:

| Opção | Como |
| --- | --- |
| Read the Docs | O `.readthedocs.yaml` já configura o build com Python 3.14 e `requirements_docs.txt`. Basta importar o repositório no Read the Docs |
| Contêiner | `docker compose up -d --build mkdocs` serve o site em <http://127.0.0.1:8001> |
| GitHub Pages | `poetry run mkdocs gh-deploy`, que publica o site na branch `gh-pages` |

Para gerar o site estático localmente, em `site/`:

```bash
poetry run mkdocs build --strict
```
