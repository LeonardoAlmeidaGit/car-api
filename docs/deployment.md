# Deploy

> **Ainda não há infraestrutura de deploy no repositório**
>
> O projeto não tem `Dockerfile`, pipeline de CI/CD nem ambiente de produção
> definido. Esta página descreve os passos genéricos para publicar a aplicação
> em um servidor com Python 3.14.

## Antes de publicar

1. Confira o [checklist de segurança](authentication.md#checklist-para-producao).
2. Defina a versão a publicar.
3. Avalie o banco de dados, como descrito a seguir.

## Banco de dados

O SQLite é adequado para desenvolvimento e para instalações pequenas em um único
servidor. Ele permite apenas uma escrita por vez, e o arquivo precisa estar em
disco persistente, com backup.

Para usar outro banco, como PostgreSQL:

1. Instale um driver assíncrono: `poetry add asyncpg`.
2. Ajuste a URL: `postgresql+asyncpg://usuario:senha@host:5432/car_api`.
3. Valide as migrações e a aplicação nesse banco.

> **Nota:** O projeto só foi executado com SQLite até agora. Outros bancos exigem testes
> próprios.

## Passos

### 1. Obter o código e instalar

```bash
git clone https://github.com/LeonardoAlmeidaGit/fastapi_test.git
cd fastapi_test
git checkout <versão>
poetry install --without dev
```

### 2. Configurar o ambiente

Defina as variáveis no gerenciador de segredos da plataforma ou no ambiente do
serviço:

```bash
DATABASE_URL='sqlite+aiosqlite:////var/lib/car_api/car.db'
JWT_SECRET_KEY='<valor gerado com secrets.token_urlsafe(64)>'
JWT_ALGORITHM='HS256'
JWT_EXPIRATION_MINUTES=30
```

No SQLite, quatro barras indicam um caminho absoluto.

### 3. Aplicar as migrações

```bash
poetry run alembic upgrade head
```

Faça backup do banco antes de aplicar migrações em produção.

### 4. Iniciar a aplicação

```bash
poetry run fastapi run car_api/app.py --host 127.0.0.1 --port 8000
```

Não use `task run` em produção: ele executa `fastapi dev`, que recarrega o código
automaticamente e é destinado ao desenvolvimento.

Com banco cliente-servidor, é possível adicionar `--workers N`. Com SQLite,
prefira um único processo, para evitar disputa de escrita.

### 5. Manter o serviço ativo

Use um gerenciador de processos, como o systemd. Exemplo de
`/etc/systemd/system/car-api.service`:

```ini
[Unit]
Description=Car API
After=network.target

[Service]
User=carapi
WorkingDirectory=/opt/car_api
EnvironmentFile=/etc/car_api/env
ExecStart=/usr/local/bin/poetry run fastapi run car_api/app.py --host 127.0.0.1 --port 8000
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Ajuste os caminhos ao seu servidor.

### 6. Configurar HTTPS

A aplicação não trata TLS. Coloque um proxy reverso, como Nginx ou Caddy, à frente
dela, encaminhando para `127.0.0.1:8000`. Sem HTTPS, senhas e tokens trafegam em
texto claro.

### 7. Verificar

```bash
curl https://seu-dominio/health_check
```

Resposta esperada: `{"message":"ok"}`.

O endpoint não consulta o banco. Ele confirma que a aplicação responde, mas não
que o banco está acessível.

## Atualizando uma versão

1. Faça backup do banco.
2. Atualize o código com `git fetch --tags` e `git checkout <versão>`.
3. Rode `poetry install --without dev`.
4. Rode `poetry run alembic upgrade head`.
5. Reinicie o serviço.
6. Verifique o `/health_check` e uma rota autenticada.

Para reverter, volte à versão anterior do código e rode
`poetry run alembic downgrade <revisão>` se houve mudança de esquema. Como o
downgrade pode perder dados, prefira restaurar o backup quando houver dúvida.

## Publicando a documentação

Para gerar o site estático em `site/`:

```bash
poetry run mkdocs build --strict
```

O conteúdo pode ser servido por qualquer hospedagem estática. Para o GitHub Pages:

```bash
poetry run mkdocs gh-deploy
```

> **Nota:** `mkdocs gh-deploy` publica o site na branch `gh-pages` do
> repositório remoto.
