# Autenticação e Segurança

Os fluxos em diagrama estão em
[Modelagem do Sistema](system-modeling.md#fluxo-de-autenticacao).

## Como autenticar

1. Crie uma conta em `POST /api/v1/users/`.
2. Envie e-mail e senha em JSON para `POST /api/v1/auth/token`.
3. Use o token recebido no cabeçalho das próximas requisições.
4. Antes de expirar, renove-o em `POST /api/v1/auth/refresh_token`.

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/token \
  -H 'Content-Type: application/json' \
  -d '{"email": "maria@example.com", "password": "senha-segura-123"}' \
  | python3 -c 'import json, sys; print(json.load(sys.stdin)["access_token"])')

curl http://127.0.0.1:8000/api/v1/cars/ \
  -H "Authorization: Bearer $TOKEN"
```

No Swagger UI (`/docs`), clique em **Authorize** e cole apenas o token. O botão
usa o esquema HTTP Bearer, portanto não preenche usuário e senha: obtenha o token
antes, chamando `/api/v1/auth/token`.

## Token JWT

| Item | Valor |
| --- | --- |
| Tipo | Token de acesso assinado, sem estado no servidor |
| Algoritmo | Definido em `JWT_ALGORITHM` (`HS256` no `.env.example`) |
| Chave | Definida em `JWT_SECRET_KEY` |
| Validade | Definida em `JWT_EXPIRATION_MINUTES` (`30` no `.env.example`) |
| Transporte | Cabeçalho `Authorization: Bearer <token>` |

O conteúdo do token tem apenas duas informações:

```json
{"sub": "1", "exp": 1793765822}
```

| Claim | Significado |
| --- | --- |
| `sub` | ID do usuário, como string |
| `exp` | Data de expiração, em segundos desde 1970 (Unix) |

> **Atenção:** O JWT é assinado, mas não é criptografado. Qualquer pessoa com o token pode
> ler seu conteúdo, então não inclua dados sensíveis nele.

### Validação

A dependência `get_current_user` executa as seguintes etapas:

1. Lê o token do cabeçalho.
2. Verifica assinatura, algoritmo e expiração.
3. Lê o ID em `sub`.
4. Busca o usuário no banco.

Por causa da última etapa, um token deixa de funcionar assim que o usuário é
excluído.

### Renovação

`/refresh_token` aceita o próprio token de acesso, não existindo um *refresh
token* separado. Um token expirado não pode ser renovado: nesse caso, é preciso
fazer login de novo.

## Senhas

- O hash é gerado com **Argon2**, pela configuração recomendada do pwdlib
  (`PasswordHash.recommended()`).
- A senha em texto puro nunca é gravada e o hash nunca é devolvido, pois
  `UserPublicSchema` não tem esse campo.
- O tamanho mínimo é de 8 caracteres.

## Permissões

Não há perfis de usuário. As permissões dependem apenas de autenticação e de
propriedade:

| Recurso | Criar | Ler | Alterar | Excluir |
| --- | --- | --- | --- | --- |
| Usuários | Público | Autenticado | Só a própria conta | Só a própria conta |
| Marcas | Autenticado | Autenticado | Autenticado | Autenticado |
| Carros | Autenticado, para si mesmo | Autenticado | Só o dono | Só o dono |

As verificações ficam em `car_api/core/security.py`:

- `verify_user_yourself`: compara o usuário autenticado com o usuário alvo.
- `verify_car_ownership`: compara o usuário autenticado com o dono do carro.

As duas respondem `403` quando não há permissão.

## Outras proteções

- **SQL injection**: as consultas usam parâmetros do SQLAlchemy, inclusive nos
  filtros de busca.
- **Validação de entrada**: todo corpo e parâmetro passa pelo Pydantic,
  inclusive o tamanho máximo dos textos e a precisão do preço, iguais aos das
  colunas do banco.
- **Exposição de dados**: `response_model` limita os campos devolvidos.
- **Integridade**: o banco mantém restrições de unicidade e chaves estrangeiras
  declaradas no esquema.
- **Segredos**: `.env` e `*.db` estão no `.gitignore`, e o `.env` também está
  no `.dockerignore`, então não entra nas imagens.
- **Contêineres**: a API roda como o usuário sem privilégios `car_api`, e o
  PostgreSQL só é publicado em `127.0.0.1`.

## Limitações conhecidas

Estes pontos refletem o código atual e devem ser avaliados antes de usar a API
em produção.

### Controle de acesso

| Limitação | Consequência | Melhoria sugerida |
| --- | --- | --- |
| Sem perfil de administrador | Qualquer usuário autenticado pode alterar ou excluir qualquer marca | Criar papéis e restringir a escrita em marcas |
| Listagem de usuários aberta a autenticados | Qualquer conta pode consultar os e-mails de todos os usuários | Restringir a rota ou ocultar o e-mail |
| Carros expõem o proprietário | `GET /cars/` devolve o e-mail do dono | Usar um schema reduzido para o proprietário |
| Transferência sem aceite | O dono pode atribuir um carro a outro usuário sem confirmação | Exigir aceite do destinatário |

### Tokens

| Limitação | Consequência | Melhoria sugerida |
| --- | --- | --- |
| Sem revogação | Sem logout no servidor; um token vazado vale até expirar | Manter uma lista de revogação com a claim `jti` |
| Renovação sem limite | Um token vazado pode ser renovado indefinidamente | Usar *refresh tokens* separados e com rotação |
| Troca de senha não invalida tokens | Sessões antigas continuam ativas | Versionar tokens por usuário |
| Sem `iat` | Não é possível saber quando o token foi emitido | Adicionar a claim |

### Proteção contra abuso

| Limitação | Consequência | Melhoria sugerida |
| --- | --- | --- |
| Sem limite de requisições | Login e cadastro ficam sujeitos a força bruta e abuso | Aplicar *rate limit* na aplicação ou no proxy |
| Sem política de senha além do tamanho | Senhas fracas são aceitas | Validar a complexidade ou consultar senhas vazadas |
| Login retorna antes do hash se o e-mail não existe | A diferença de tempo pode revelar e-mails cadastrados | Verificar um hash fictício nesse caso |
| Cadastro informa e-mail e username em uso | Permite descobrir contas existentes | Avaliar o risco para o caso de uso |

### Infraestrutura e dados

| Limitação | Consequência | Melhoria sugerida |
| --- | --- | --- |
| HTTPS não é tratado pela aplicação | Sem TLS, token e senha trafegam em claro | Usar um proxy com TLS |
| CORS não configurado | Frontends de outra origem são bloqueados pelo navegador | Adicionar `CORSMiddleware` com origens explícitas |
| Swagger e ReDoc sempre ativos | A estrutura da API fica pública em produção | Desativá-los por configuração, se necessário |
| Unicidade checada antes de gravar, sem tratar `IntegrityError` | Requisições simultâneas podem gerar `500` em vez de `400` | Tratar a exceção na gravação |
| `email` e `password` sem tamanho máximo | Corpos muito grandes são aceitos, e calcular o Argon2 de uma senha enorme consome CPU | Definir `max_length` nos dois campos |
| API publicada em `0.0.0.0:8000` no Compose | A porta fica acessível sem passar pelo proxy com HTTPS | Publicar em `127.0.0.1` ou bloquear no firewall |
| Credenciais de exemplo no `.env.example` | Um `.env` copiado sem alteração usa senha e chave conhecidas | Trocar `JWT_SECRET_KEY` e `DB_PASSWORD` antes de subir o banco |

## Checklist para produção

- `JWT_SECRET_KEY` aleatória, longa e fora do repositório
- `DB_PASSWORD` própria, definida antes de criar o volume do banco
- `.env` com acesso restrito no servidor
- HTTPS em todo o tráfego, sem acesso direto à porta 8000
- Backup do PostgreSQL agendado e guardado fora do servidor
- `JWT_EXPIRATION_MINUTES` adequado ao risco
- *Rate limit* em `/auth/token` e no cadastro
- CORS restrito às origens necessárias
- Decisão sobre quem pode alterar marcas e ver e-mails
- `task test` passando na versão publicada

## Cobertura por testes

Os mecanismos desta página são verificados em `tests/test_auth.py` e nos testes
de permissão de cada recurso:

| Mecanismo | Cenários testados |
| --- | --- |
| Senhas | Hash Argon2, verificação correta e incorreta, hash gravado no cadastro e na troca de senha |
| Emissão de token | Claims `sub` e `exp`, login com e-mail inexistente e senha errada, cabeçalho `WWW-Authenticate` |
| Validação de token | Token expirado, malformado, com assinatura de outra chave, sem `sub`, com `sub` vazio ou não numérico, de usuário inexistente ou excluído |
| Transporte | Cabeçalho ausente e esquema diferente de `Bearer` |
| Renovação | Token válido, ausente e expirado |
| Permissões | Alterar ou excluir a conta e o carro de outro usuário; criar carro para outro dono |
| Limites dos campos | Valores no limite aceitos e acima do limite recusados com `422`, na criação e no `PATCH` |

Veja [Testes](testing.md).
