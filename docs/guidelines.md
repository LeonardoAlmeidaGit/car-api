# Guidelines e padrões

Estas convenções foram extraídas do código atual. Siga-as ao adicionar novos
recursos.

## Estilo de código

- Linhas com até **79 caracteres**.
- **Aspas simples** em strings.
- Imports organizados pelo Ruff.
- Nomes de código em inglês: variáveis, funções, classes e tabelas.
- Mensagens ao usuário e `summary` das rotas em português.

Antes de abrir um pull request:

```bash
poetry run task format
poetry run task test   # executa o lint antes dos testes
```

## Organização em camadas

| Camada | Diretório | Responsabilidade |
| --- | --- | --- |
| Rotas | `car_api/routers/` | Recebem a requisição, aplicam as regras e respondem |
| Schemas | `car_api/schemas/` | Validam a entrada e definem o formato da saída |
| Modelos | `car_api/models/` | Mapeiam as tabelas do banco |
| Núcleo | `car_api/core/` | Configurações, sessão do banco e segurança |

Não há camada de serviços: as regras de negócio ficam nas funções das rotas.

## Schemas

Cada recurso segue o mesmo padrão de nomes:

| Sufixo | Uso | Exemplo |
| --- | --- | --- |
| `Schema` | Corpo da criação | `CarSchema` |
| `UpdateSchema` | Corpo da atualização parcial, com campos opcionais | `CarUpdateSchema` |
| `PublicSchema` | Resposta com um registro | `CarPublicSchema` |
| `ListPublicSchema` | Resposta paginada | `CarListPublicSchema` |

Validações usam `@field_validator` e ficam no schema, não na rota. Em
`UpdateSchema`, o validador precisa aceitar `None`:

```python
@field_validator('model')
def model_min_length(cls, v):
    if v is None:
        return v
    if len(v.strip()) < 2:
        raise ValueError('Modelo deve ter pelo menos 2 caracteres')
    return v.strip()
```

Nunca inclua `password` em um `PublicSchema`.

## Modelos

- Use o estilo tipado do SQLAlchemy 2: `Mapped[...]` e `mapped_column(...)`.
- Inclua `created_at` e `updated_at` com `server_default=func.now()`.
- Tabelas no plural: `users`, `brands`, `cars`.
- Declare os dois lados dos relacionamentos com `back_populates`.
- Importe tipos de outros módulos sob `TYPE_CHECKING` para evitar import
  circular.
- Exporte novos modelos em `car_api/models/__init__.py`.

## Rotas

- Funções assíncronas que recebem a sessão por `Depends(get_session)`.
- Proteja a rota com `current_user: User = Depends(get_current_user)`.
- Declare `path`, `status_code`, `response_model` e `summary` no decorador.
- Registre novos routers em `car_api/app.py`, com prefixo `/api/v1/<recurso>`.

Exemplo:

```python
@router.get(
    path='/{brand_id}',
    status_code=status.HTTP_200_OK,
    response_model=BrandPublicSchema,
    summary='Buscar marca por ID',
)
async def get_brand(
    brand_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
```

### Convenções REST

| Operação | Método | Status de sucesso |
| --- | --- | --- |
| Criar | `POST /recurso/` | `201` |
| Listar | `GET /recurso/` | `200` |
| Buscar | `GET /recurso/{id}` | `200` |
| Atualizar parcialmente | `PATCH /recurso/{id}` | `200` |
| Excluir | `DELETE /recurso/{id}` | `204` |

### Erros

| Status | Quando usar |
| --- | --- |
| `400` | Conflito de regra de negócio, como duplicidade ou exclusão bloqueada |
| `401` | Token ausente, inválido ou expirado; credenciais incorretas |
| `403` | Usuário autenticado sem permissão |
| `404` | Registro não encontrado |
| `422` | Falha de validação (gerado pelo FastAPI) |

### Padrões recorrentes

Verifique a duplicidade antes de gravar:

```python
plate_exists = await db.scalar(select(exists().where(Car.plate == car.plate)))
```

Em atualizações, aplique somente os campos enviados:

```python
update_data = car_update.model_dump(exclude_unset=True, exclude_none=True)

for field, value in update_data.items():
    setattr(car, field, value)
```

Carregue os relacionamentos antes de serializar, pois o acesso preguiçoso não
funciona em sessão assíncrona:

```python
select(Car).options(selectinload(Car.brand), selectinload(Car.owner))
```

Toda listagem aceita `offset` (mínimo 0) e `limit` (de 1 a 100, padrão 100) e
devolve esses valores na resposta.

## Migrações

- Toda mudança em modelo exige uma migração.
- Revise o arquivo gerado antes de aplicá-lo.
- Não edite uma migração que já foi publicada; crie outra.

O passo a passo está em [Desenvolvimento](development.md#migracoes).

## Testes

- Toda rota nova ou alterada precisa de testes para o sucesso e para cada erro
  que ela pode devolver.
- Testes ficam em `tests/test_<recurso>.py`, com fixtures compartilhadas em
  `tests/conftest.py`.
- Use `http.HTTPStatus` nas asserções de status e compare a mensagem de erro
  exata em `detail`.
- Mantenha a cobertura acima de 80%. A meta não é verificada automaticamente:
  confira o total no final de `task test`.
- Ao mudar uma mensagem de erro, atualize também os testes e a página
  [API Endpoints](api-endpoints.md).

As convenções completas e exemplos estão em
[Testes](testing.md#escrevendo-novos-testes).

## Commits e branches

As regras estão em [Contribuição](contributing.md).
