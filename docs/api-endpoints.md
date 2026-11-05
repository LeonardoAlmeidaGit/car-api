# API Endpoints

URL base em desenvolvimento: `http://127.0.0.1:8000`.

A documentação interativa está em `/docs` (Swagger UI) e `/redoc` (ReDoc), e o
esquema OpenAPI em `/openapi.json`.

## Resumo

| Método | Rota | Descrição | Autenticação |
| --- | --- | --- | --- |
| `GET` | `/health_check` | Verifica se a API está no ar | Não |
| `POST` | `/api/v1/auth/token` | Gera um token de acesso | Não |
| `POST` | `/api/v1/auth/refresh_token` | Gera um novo token | Sim |
| `POST` | `/api/v1/users/` | Cria um usuário | Não |
| `GET` | `/api/v1/users/` | Lista usuários | Sim |
| `GET` | `/api/v1/users/{user_id}` | Busca um usuário | Sim |
| `PATCH` | `/api/v1/users/{user_id}` | Atualiza a própria conta | Sim |
| `DELETE` | `/api/v1/users/{user_id}` | Exclui a própria conta | Sim |
| `POST` | `/api/v1/brands/` | Cria uma marca | Sim |
| `GET` | `/api/v1/brands/` | Lista marcas | Sim |
| `GET` | `/api/v1/brands/{brand_id}` | Busca uma marca | Sim |
| `PATCH` | `/api/v1/brands/{brand_id}` | Atualiza uma marca | Sim |
| `DELETE` | `/api/v1/brands/{brand_id}` | Exclui uma marca | Sim |
| `POST` | `/api/v1/cars/` | Cria um carro próprio | Sim |
| `GET` | `/api/v1/cars/` | Lista carros | Sim |
| `GET` | `/api/v1/cars/{car_id}` | Busca um carro | Sim |
| `PATCH` | `/api/v1/cars/{car_id}` | Atualiza um carro próprio | Sim |
| `DELETE` | `/api/v1/cars/{car_id}` | Exclui um carro próprio | Sim |

## Convenções

### Autenticação

Envie o token no cabeçalho `Authorization`:

```http
Authorization: Bearer SEU_TOKEN
```

### Barra final

As rotas de coleção terminam com `/`, como `/api/v1/cars/`. Sem a barra, a API
responde `307 Temporary Redirect` para a URL correta.

### Paginação

As listagens aceitam:

| Parâmetro | Tipo | Padrão | Limites |
| --- | --- | --- | --- |
| `offset` | inteiro | `0` | Mínimo 0 |
| `limit` | inteiro | `100` | De 1 a 100 |

A resposta devolve os registros junto com `offset` e `limit`, mas não informa o
total de registros.

### Atualização parcial

Nas rotas `PATCH`, envie apenas os campos que deseja alterar. Campos enviados
com `null` são **ignorados**, portanto não é possível limpar um campo opcional,
como `description`, enviando `null`.

### Erros

Erros de negócio têm o formato:

```json
{"detail": "Carro não encontrado"}
```

Erros de validação (`422`) detalham o campo com problema:

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "username"],
      "msg": "Value error, Username deve ter pelo menos 5 caracteres",
      "input": "abc",
      "ctx": {"error": {}}
    }
  ]
}
```

Erros comuns a todas as rotas protegidas:

| Status | `detail` | Causa |
| --- | --- | --- |
| `401` | `Not authenticated` | Cabeçalho `Authorization` ausente |
| `401` | `Could not validate credentials` | Token inválido ou usuário inexistente |
| `401` | `Token has expired` | Token expirado |

---

## Health check

### `GET /health_check`

Resposta `200`:

```json
{"message": "ok"}
```

---

## Autenticação

### `POST /api/v1/auth/token`

Autentica o usuário com um corpo JSON.

| Campo | Tipo | Obrigatório | Regras |
| --- | --- | --- | --- |
| `email` | string | Sim | E-mail válido |
| `password` | string | Sim | Mínimo de 8 caracteres |

```json
{"email": "maria@example.com", "password": "senha-segura-123"}
```

Resposta `200`:

```json
{"access_token": "eyJhbGciOiJIUzI1NiIs...", "token_type": "bearer"}
```

| Status | Causa |
| --- | --- |
| `401` | `Incorrect email or password` |
| `422` | Dados inválidos |

### `POST /api/v1/auth/refresh_token`

Não tem corpo. Exige um token ainda válido e devolve um novo, com a validade
reiniciada e o mesmo formato de resposta de `/token`.

---

## Usuários

Formato de resposta (`UserPublicSchema`):

```json
{
  "id": 1,
  "username": "maria",
  "email": "maria@example.com",
  "created_at": "2026-11-04T03:47:02",
  "updated_at": "2026-11-04T03:47:02"
}
```

### `POST /api/v1/users/`

Rota pública. Resposta `201`.

| Campo | Tipo | Obrigatório | Regras |
| --- | --- | --- | --- |
| `username` | string | Sim | Mínimo de 5 caracteres, único |
| `email` | string | Sim | E-mail válido, único |
| `password` | string | Sim | Mínimo de 8 caracteres |

```json
{
  "username": "maria",
  "email": "maria@example.com",
  "password": "senha-segura-123"
}
```

| Status | `detail` |
| --- | --- |
| `400` | `Username já está em uso.` |
| `400` | `O email já está em uso.` |
| `422` | Dados inválidos |

### `GET /api/v1/users/`

Além da paginação, aceita:

| Parâmetro | Descrição |
| --- | --- |
| `search` | Busca parcial em `username` e `email`, sem diferenciar maiúsculas |

Resposta `200`:

```json
{"users": [{"id": 1, "username": "maria", "...": "..."}], "offset": 0, "limit": 100}
```

### `GET /api/v1/users/{user_id}`

Resposta `200` ou `404` (`Usuário não encontrado`).

### `PATCH /api/v1/users/{user_id}`

Só altera a própria conta. Campos opcionais: `username`, `email` e `password`,
com as mesmas regras da criação. Uma nova senha é armazenada como hash.

| Status | `detail` |
| --- | --- |
| `400` | `Username já está em uso` |
| `400` | `O email já está em uso` |
| `403` | `Not enough permissions to access this user` |
| `404` | `Id de usuário não encontrado.` |
| `422` | Dados inválidos |

Enviar o próprio `username` ou `email` atual não é considerado duplicidade.

### `DELETE /api/v1/users/{user_id}`

Só exclui a própria conta. Resposta `204`, sem corpo. Depois da exclusão, os
tokens emitidos para a conta deixam de ser aceitos.

| Status | `detail` |
| --- | --- |
| `400` | `Não é possível deletar usuário que possui carros associados.` |
| `403` | `Not enough permissions to access this user` |
| `404` | `Id de usuário não encontrado.` |

---

## Marcas

Qualquer usuário autenticado pode criar, alterar e excluir marcas.

Formato de resposta (`BrandPublicSchema`):

```json
{
  "id": 1,
  "name": "Toyota",
  "description": "Marca japonesa",
  "is_active": true,
  "created_at": "2026-11-04T03:47:02",
  "updated_at": "2026-11-04T03:47:02"
}
```

### `POST /api/v1/brands/`

Resposta `201`.

| Campo | Tipo | Obrigatório | Padrão | Regras |
| --- | --- | --- | --- | --- |
| `name` | string | Sim | | Mínimo de 2 caracteres após remover espaços nas pontas, único |
| `description` | string | Não | `null` | |
| `is_active` | booleano | Não | `true` | |

```json
{"name": "Toyota", "description": "Marca japonesa"}
```

| Status | `detail` |
| --- | --- |
| `400` | `Marca já cadastrada.` |
| `422` | Dados inválidos |

### `GET /api/v1/brands/`

Além da paginação, aceita:

| Parâmetro | Descrição |
| --- | --- |
| `search` | Busca parcial no nome, sem diferenciar maiúsculas |
| `is_active` | `true` ou `false` |

Resposta `200`:

```json
{"brands": [{"id": 1, "name": "Toyota", "...": "..."}], "offset": 0, "limit": 100}
```

### `GET /api/v1/brands/{brand_id}`

Resposta `200` ou `404` (`Marca não encontrada`).

### `PATCH /api/v1/brands/{brand_id}`

Campos opcionais: `name`, `description` e `is_active`, com as mesmas regras da
criação. Manter o nome atual não é considerado duplicidade.

| Status | `detail` |
| --- | --- |
| `400` | `Nome da marca já está em uso` |
| `404` | `Marca não encontrada` |
| `422` | Dados inválidos |

### `DELETE /api/v1/brands/{brand_id}`

Resposta `204`, sem corpo.

| Status | `detail` |
| --- | --- |
| `400` | `Não é possível deletar marca que possui carros associados.` |
| `404` | `Marca não encontrada.` |

---

## Carros

Formato de resposta (`CarPublicSchema`), que inclui a marca e o proprietário:

```json
{
  "id": 1,
  "model": "Corolla",
  "factory_year": 2023,
  "model_year": 2024,
  "color": "Prata",
  "plate": "ABC1D23",
  "fuel_type": "flex",
  "transmission_type": "automatic",
  "price": "129900.50",
  "description": null,
  "is_available": true,
  "brand_id": 1,
  "owner_id": 1,
  "created_at": "2026-11-04T03:47:03",
  "updated_at": "2026-11-04T03:47:03",
  "brand": {
    "id": 1,
    "name": "Toyota",
    "description": "Marca japonesa",
    "is_active": true,
    "created_at": "2026-11-04T03:47:02",
    "updated_at": "2026-11-04T03:47:02"
  },
  "owner": {
    "id": 1,
    "username": "maria",
    "email": "maria@example.com",
    "created_at": "2026-11-04T03:47:02",
    "updated_at": "2026-11-04T03:47:02"
  }
}
```

> **Nota:** O campo `price` é devolvido como **string**, o que preserva a precisão
> decimal.

### Valores aceitos

| Campo | Valores |
| --- | --- |
| `fuel_type` | `gasoline`, `ethanol`, `flex`, `diesel`, `electric`, `hybrid` |
| `transmission_type` | `manual`, `automatic`, `semi_automatic`, `cvt` |

### `POST /api/v1/cars/`

Resposta `201`.

| Campo | Tipo | Obrigatório | Padrão | Regras |
| --- | --- | --- | --- | --- |
| `model` | string | Sim | | Mínimo de 2 caracteres após remover espaços nas pontas |
| `factory_year` | inteiro | Sim | | De 1900 a 2030 |
| `model_year` | inteiro | Sim | | De 1900 a 2030 |
| `color` | string | Sim | | Mínimo de 4 caracteres após remover espaços nas pontas |
| `plate` | string | Sim | | De 7 a 10 caracteres, convertida para maiúsculas, única |
| `fuel_type` | enum | Sim | | Veja os valores aceitos |
| `transmission_type` | enum | Sim | | Veja os valores aceitos |
| `price` | decimal | Sim | | Maior que zero |
| `description` | string | Não | `null` | |
| `is_available` | booleano | Não | `true` | |
| `brand_id` | inteiro | Sim | | Marca existente |
| `owner_id` | inteiro | Sim | | Deve ser o ID do usuário autenticado |

```json
{
  "model": "Corolla",
  "factory_year": 2023,
  "model_year": 2024,
  "color": "Prata",
  "plate": "ABC1D23",
  "fuel_type": "flex",
  "transmission_type": "automatic",
  "price": "129900.50",
  "brand_id": 1,
  "owner_id": 1
}
```

| Status | `detail` |
| --- | --- |
| `400` | `Placa já está em uso` |
| `403` | `Not enough permissions to access this car` |
| `404` | `Marca não encontrada` |
| `422` | Dados inválidos |

> **Nota:** O código também verifica se o proprietário existe e responde
> `404 Proprietário não encontrado`, mas esse caso não ocorre na prática: a
> verificação de `403` vem antes e exige que `owner_id` seja o usuário
> autenticado.

### `GET /api/v1/cars/`

Lista os carros de todos os usuários. Além da paginação, aceita os filtros
abaixo, que podem ser combinados:

| Parâmetro | Tipo | Descrição |
| --- | --- | --- |
| `search` | string | Busca parcial em modelo, cor e placa, sem diferenciar maiúsculas |
| `brand_id` | inteiro | Filtra por marca |
| `owner_id` | inteiro | Filtra por proprietário |
| `fuel_type` | enum | Filtra por combustível |
| `transmission_type` | enum | Filtra por transmissão |
| `is_available` | booleano | Filtra por disponibilidade |
| `min_price` | número | Preço mínimo (maior ou igual a 0) |
| `max_price` | número | Preço máximo (maior ou igual a 0) |

Exemplo:

```bash
curl 'http://127.0.0.1:8000/api/v1/cars/?fuel_type=flex&min_price=50000&limit=10' \
  -H 'Authorization: Bearer SEU_TOKEN'
```

Resposta `200`:

```json
{"cars": [{"id": 1, "model": "Corolla", "...": "..."}], "offset": 0, "limit": 10}
```

### `GET /api/v1/cars/{car_id}`

Resposta `200` ou `404` (`Carro não encontrado`).

### `PATCH /api/v1/cars/{car_id}`

Só o proprietário pode alterar. Todos os campos de criação são opcionais, com as
mesmas regras, exceto `owner_id`: aqui ele aceita qualquer usuário existente, o
que **transfere o carro**. Depois da transferência, o antigo dono perde o acesso
de escrita.

| Status | `detail` |
| --- | --- |
| `400` | `Placa já está em uso` |
| `403` | `Not enough permissions to access this car` |
| `404` | `Carro não encontrado` |
| `404` | `Marca não encontrada` |
| `404` | `Proprietário não encontrado` |
| `422` | Dados inválidos |

### `DELETE /api/v1/cars/{car_id}`

Só o proprietário pode excluir. Resposta `204`, sem corpo.

| Status | `detail` |
| --- | --- |
| `403` | `Not enough permissions to access this car` |
| `404` | `Carro não encontrado` |
