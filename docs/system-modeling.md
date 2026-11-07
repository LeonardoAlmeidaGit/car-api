# Modelagem do Sistema

## Modelos de Dados

```mermaid
erDiagram
    USERS ||--o{ CARS : "possui"
    BRANDS ||--o{ CARS : "classifica"

    USERS {
        int id PK
        string username UK "até 30 caracteres na API"
        string password "hash Argon2"
        string email UK
        datetime created_at
        datetime updated_at
    }

    BRANDS {
        int id PK
        string name UK "até 50 caracteres"
        boolean is_active "padrão true"
        text description "opcional"
        datetime created_at
        datetime updated_at
    }

    CARS {
        int id PK
        string model "até 100 caracteres"
        int factory_year
        int model_year
        string color "até 30 caracteres"
        string plate UK "até 10 caracteres, indexada"
        string fuel_type "até 20 caracteres"
        string transmission_type "até 20 caracteres"
        decimal price "Numeric(10, 2)"
        text description "opcional"
        boolean is_available "padrão true"
        int brand_id FK
        int owner_id FK
        datetime created_at
        datetime updated_at
    }
```

### Tamanho das colunas

No PostgreSQL, `String(n)` vira `VARCHAR(n)`, e o banco recusa valores maiores.
Os schemas repetem esses limites com `max_length` e `max_digits`, para que a API
responda `422` em vez de deixar o erro chegar ao banco como `500`:

| Coluna | Banco | Schema |
| --- | --- | --- |
| `users.username` | `VARCHAR`, sem limite | `max_length=30` |
| `brands.name` | `VARCHAR(50)` | `max_length=50` |
| `cars.model` | `VARCHAR(100)` | `max_length=100` |
| `cars.color` | `VARCHAR(30)` | `max_length=30` |
| `cars.plate` | `VARCHAR(10)` | Validador de 7 a 10 caracteres |
| `cars.price` | `NUMERIC(10, 2)` | `max_digits=10`, `decimal_places=2` |

`users.email` e `users.password` não têm limite no banco nem no schema. O
`username` tem limite apenas na API.

### Relacionamentos

| Relação | Cardinalidade | Regra |
| --- | --- | --- |
| Usuário e carros | Um usuário tem zero ou mais carros; todo carro tem um dono | A API bloqueia a exclusão de usuário com carros |
| Marca e carros | Uma marca tem zero ou mais carros; todo carro tem uma marca | A API bloqueia a exclusão de marca com carros |

### Enumerações

`fuel_type` e `transmission_type` são armazenados como texto. Os valores
permitidos são validados pelo Pydantic na API, não por uma restrição no banco.

| Enum | Valores |
| --- | --- |
| `FuelType` | `gasoline`, `ethanol`, `flex`, `diesel`, `electric`, `hybrid` |
| `TransmissionType` | `manual`, `automatic`, `semi_automatic`, `cvt` |

## Arquitetura do Sistema

A aplicação é um monólito em camadas. Cada requisição passa pelas rotas, que
usam os schemas para validar os dados, as dependências de segurança para
identificar o usuário e os modelos para acessar o banco.

```mermaid
flowchart TB
    Client["Cliente HTTP<br/>(Swagger, curl, frontend)"]

    subgraph App["Aplicação FastAPI (car_api/app.py)"]
        direction TB

        subgraph Routers["Rotas (routers/)"]
            AuthR["auth"]
            UsersR["users"]
            BrandsR["brands"]
            CarsR["cars"]
        end

        Schemas["Schemas Pydantic (schemas/)<br/>validação e serialização"]

        subgraph Core["Núcleo (core/)"]
            Security["security.py<br/>Argon2, JWT e permissões"]
            Database["database.py<br/>engine e get_session"]
            Settings["settings.py<br/>variáveis de ambiente"]
        end

        Models["Modelos SQLAlchemy (models/)<br/>User, Brand e Car"]
    end

    Env[(".env")]
    DB[("PostgreSQL 17.6")]
    Alembic["Alembic<br/>(migrations/)"]

    Client -->|"HTTP/JSON"| Routers
    Routers --> Schemas
    Routers --> Security
    Routers --> Models
    Routers --> Database
    Security --> Database
    Security --> Settings
    Database --> Settings
    Settings --> Env
    Models --> Database
    Database -->|"psycopg 3"| DB
    Alembic -->|"aplica o esquema"| DB
    Alembic --> Settings
    Alembic --> Models
```

## Implantação em contêineres

No Docker Compose, a aplicação e as migrações usam a mesma imagem e falam com o
banco pela rede interna do Compose, pelo host `db`.

```mermaid
flowchart LR
    Client["Cliente HTTP"]
    Browser["Navegador"]

    subgraph Host["Host"]
        direction LR

        subgraph Compose["Rede do Docker Compose"]
            App["app<br/>fastapi run"]
            Mig["migrations<br/>alembic upgrade head"]
            DB[("db<br/>PostgreSQL 17.6")]
            Docs["mkdocs<br/>Nginx"]
        end

        Vol[("volume<br/>postgres_data")]
        Env[(".env")]
    end

    Client -->|"0.0.0.0:8000"| App
    Browser -->|":8001"| Docs
    App -->|"db:5432"| DB
    Mig -->|"db:5432"| DB
    DB --- Vol
    Env -.->|"env_file e interpolação"| App
    Env -.-> Mig
    Env -.-> DB
```

A porta 5432 também é publicada, mas só em `127.0.0.1`, para a API rodando
fora do Docker e para clientes de banco locais. Os detalhes estão em
[Docker](docker.md).

## Fluxo de Autenticação

### Login e renovação do token

```mermaid
sequenceDiagram
    actor C as Cliente
    participant R as routers/auth.py
    participant S as core/security.py
    participant D as Banco de dados

    Note over C,D: Login
    C->>R: POST /api/v1/auth/token (email, password)
    R->>R: Valida o corpo com LoginRequest
    alt Dados inválidos
        R-->>C: 422 Unprocessable Entity
    end
    R->>S: authenticate_user(email, password)
    S->>D: SELECT usuário por e-mail
    D-->>S: Usuário ou nenhum resultado
    opt Usuário encontrado
        S->>S: verify_password (Argon2)
    end
    alt Usuário inexistente ou senha incorreta
        S-->>R: None
        R-->>C: 401 Incorrect email or password
    else Credenciais corretas
        S-->>R: Usuário
        R->>S: create_access_token(sub = ID do usuário)
        S-->>R: JWT com sub e exp
        R-->>C: 200 access_token e token_type
    end

    Note over C,D: Renovação
    C->>R: POST /api/v1/auth/refresh_token (Bearer)
    R->>S: get_current_user
    S->>S: verify_token
    S->>D: SELECT usuário por ID
    alt Token inválido ou usuário inexistente
        S-->>C: 401 Unauthorized
    else Token válido
        S-->>R: Usuário
        R->>S: create_access_token(sub = ID do usuário)
        S-->>R: Novo JWT
        R-->>C: 200 access_token e token_type
    end
```

### Validação do token em rotas protegidas

```mermaid
flowchart TD
    Start["Requisição em rota protegida"] --> Header{"Cabeçalho Bearer<br/>presente?"}
    Header -->|Não| E1["401 Not authenticated"]
    Header -->|Sim| Decode{"Assinatura e<br/>formato válidos?"}
    Decode -->|Token expirado| E2["401 Token has expired"]
    Decode -->|Token inválido| E3["401 Could not validate credentials"]
    Decode -->|Sim| Sub{"sub presente<br/>e numérico?"}
    Sub -->|Não| E3
    Sub -->|Sim| Find{"Usuário existe<br/>no banco?"}
    Find -->|Não| E3
    Find -->|Sim| OK["current_user disponível na rota"]
```

## Fluxo CRUD de Carros

Todas as operações passam antes pela
[validação do token](#validacao-do-token-em-rotas-protegidas).

### Criar

```mermaid
sequenceDiagram
    actor C as Cliente
    participant R as routers/cars.py
    participant S as core/security.py
    participant D as Banco de dados

    C->>R: POST /api/v1/cars/ (Bearer e CarSchema)
    R->>R: Valida o corpo, incluindo tamanhos e precisão do preço
    alt Dados inválidos
        R-->>C: 422 Unprocessable Entity
    end
    R->>S: verify_car_ownership(usuário, owner_id)
    alt owner_id diferente do usuário
        S-->>C: 403 Forbidden
    end
    R->>D: A placa já existe?
    alt Placa em uso
        R-->>C: 400 Placa já está em uso
    end
    R->>D: A marca existe?
    alt Marca inexistente
        R-->>C: 404 Marca não encontrada
    end
    R->>D: O proprietário existe?
    alt Proprietário inexistente
        R-->>C: 404 Proprietário não encontrado
    end
    R->>D: INSERT e COMMIT
    R->>D: SELECT com marca e proprietário
    D-->>R: Carro completo
    R-->>C: 201 CarPublicSchema
```

> **Nota:** A checagem de proprietário existe no código, mas nunca devolve
> `404`: como `verify_car_ownership` já exige que `owner_id` seja o usuário
> autenticado, o proprietário sempre existe. Por isso essa é a única linha das
> rotas sem cobertura de testes.

### Listar e buscar

```mermaid
sequenceDiagram
    actor C as Cliente
    participant R as routers/cars.py
    participant D as Banco de dados

    C->>R: GET /api/v1/cars/ com filtros e paginação
    alt Parâmetros inválidos
        R-->>C: 422 Unprocessable Entity
    end
    R->>R: Monta a consulta com os filtros informados
    R->>D: SELECT com marca e proprietário, OFFSET e LIMIT
    D-->>R: Carros
    R-->>C: 200 cars, offset e limit

    C->>R: GET /api/v1/cars/{car_id}
    R->>D: SELECT por ID com marca e proprietário
    alt Carro inexistente
        R-->>C: 404 Carro não encontrado
    else Carro encontrado
        R-->>C: 200 CarPublicSchema
    end
```

### Atualizar

```mermaid
sequenceDiagram
    actor C as Cliente
    participant R as routers/cars.py
    participant S as core/security.py
    participant D as Banco de dados

    C->>R: PATCH /api/v1/cars/{car_id} (Bearer e CarUpdateSchema)
    R->>D: Busca o carro
    alt Carro inexistente
        R-->>C: 404 Carro não encontrado
    end
    R->>S: verify_car_ownership(usuário, car.owner_id)
    alt Usuário não é o dono
        S-->>C: 403 Forbidden
    end
    R->>R: Mantém só os campos enviados e não nulos
    opt plate foi alterada
        R->>D: A placa já existe em outro carro?
        Note right of R: Em uso: 400
    end
    opt brand_id foi alterado
        R->>D: A marca existe?
        Note right of R: Inexistente: 404
    end
    opt owner_id foi enviado
        R->>D: O novo proprietário existe?
        Note right of R: Inexistente: 404
    end
    R->>D: UPDATE e COMMIT
    R->>D: SELECT com marca e proprietário
    D-->>R: Carro atualizado
    R-->>C: 200 CarPublicSchema
```

### Excluir

```mermaid
sequenceDiagram
    actor C as Cliente
    participant R as routers/cars.py
    participant S as core/security.py
    participant D as Banco de dados

    C->>R: DELETE /api/v1/cars/{car_id} (Bearer)
    R->>D: Busca o carro
    alt Carro inexistente
        R-->>C: 404 Carro não encontrado
    end
    R->>S: verify_car_ownership(usuário, car.owner_id)
    alt Usuário não é o dono
        S-->>C: 403 Forbidden
    end
    R->>D: DELETE e COMMIT
    R-->>C: 204 No Content
```

## Fluxo de Segurança

O diagrama mostra as camadas de proteção de uma requisição até a resposta.

```mermaid
flowchart TD
    Req["Requisição HTTP"] --> Public{"Rota pública?"}

    Public -->|"Sim: health check, login ou cadastro"| Val
    Public -->|Não| Auth["Autenticação<br/>get_current_user"]

    Auth -->|"Token ausente, inválido ou expirado"| E401["401 Unauthorized"]
    Auth -->|"Usuário do token não existe mais"| E401
    Auth -->|Usuário identificado| Val

    Val["Validação<br/>Pydantic, com limites das colunas"] -->|Dados inválidos| E422["422 Unprocessable Entity"]
    Val -->|Dados válidos| Exists{"Registro alvo existe?"}

    Exists -->|Não| E404["404 Not Found"]
    Exists -->|"Sim ou não se aplica"| Owner{"Rota exige ser o dono?<br/>carros: escrita<br/>usuários: PATCH e DELETE"}

    Owner -->|"Sim, e não é o dono"| E403["403 Forbidden"]
    Owner -->|"Não exige ou é o dono"| Rules["Regras de negócio<br/>duplicidade e vínculos"]

    Rules -->|Conflito| E400["400 Bad Request"]
    Rules -->|OK| Data["Acesso ao banco<br/>consultas parametrizadas pelo ORM"]

    Data --> Output["Resposta filtrada por response_model<br/>sem o hash da senha"]
```

> **Ordem real das etapas**
>
> O diagrama simplifica a ordem. O FastAPI resolve as dependências e valida o
> corpo antes de executar a função da rota, por isso `401` e `422` ocorrem
> antes das demais verificações. Na criação de carro, a verificação de
> proprietário (`403`) vem antes das checagens de placa e marca.

Os detalhes de cada mecanismo estão em
[Autenticação e Segurança](authentication.md).
