# Factor Content — ERD inicial (V1)

Todas las tablas usan UUID como PK, y todas tienen `created_at`/`updated_at`
(omitidos abajo por brevedad salvo donde son el foco).

```mermaid
erDiagram
    USERS ||--o{ AUDIT_LOGS : "genera"

    SOURCES ||--o{ SOURCE_CHECKS : "tiene"
    SOURCES ||--o{ CONTENT_ITEMS : "origina"

    CONTENT_ITEMS ||--o{ MEDIA_ASSETS : "tiene"
    CONTENT_ITEMS ||--o{ RENDER_JOBS : "genera"
    CONTENT_ITEMS ||--o{ AI_GENERATIONS : "tiene"
    CONTENT_ITEMS ||--o{ POSTS : "publicado_como"

    TEMPLATES ||--o{ RENDER_JOBS : "usado_en"

    MEDIA_ASSETS ||--o{ RENDER_JOBS : "input_de"
    RENDER_JOBS ||--o| MEDIA_ASSETS : "produce_output"

    ACCOUNTS ||--o{ POSTS : "publica_en"
    ACCOUNTS ||--o{ PLATFORM_CREDENTIALS : "tiene"

    POSTS ||--o{ POST_EVENTS : "tiene"
    POSTS ||--o{ POST_METRICS : "acumula"
    POSTS ||--o| SCHEDULES : "programado_por"

    USERS {
        uuid id PK
        string email
        string role
    }

    SOURCES {
        uuid id PK
        string name
        string platform
        string source_url
        string external_identifier
        string category
        string language
        string country
        int priority
        enum permission_status "UNKNOWN|AUTHORIZED|LICENSED|PUBLIC_DOMAIN|PLATFORM_SUPPORTED|RESTRICTED|REJECTED"
        bool active
        int polling_interval
        timestamp last_checked_at
    }

    SOURCE_CHECKS {
        uuid id PK
        uuid source_id FK
        timestamp checked_at
        int items_found
        string status
    }

    CONTENT_ITEMS {
        uuid id PK
        uuid source_id FK
        string source_url
        string external_id
        string title
        string description
        string category
        string language
        timestamp published_at
        timestamp discovered_at
        int factor_score "0-100"
        enum status "DISCOVERED..ARCHIVED (13 estados)"
        string rights_status
        string checksum
        jsonb metadata_json
    }

    MEDIA_ASSETS {
        uuid id PK
        uuid content_item_id FK
        string storage_key
        string asset_type "original|working|rendered|thumbnail|subtitle"
        string mime_type
        int width
        int height
        int duration_ms
        bigint file_size
        string checksum
    }

    TEMPLATES {
        uuid id PK
        string name
        int version
        bool active
        jsonb configuration_json
    }

    RENDER_JOBS {
        uuid id PK
        uuid content_item_id FK
        uuid template_id FK
        uuid input_asset_id FK
        uuid output_asset_id FK
        enum status "QUEUED|RUNNING|SUCCEEDED|FAILED|CANCELLED"
        int progress
        timestamp started_at
        timestamp completed_at
        string error_code
        string error_message
        string worker_id
    }

    AI_GENERATIONS {
        uuid id PK
        uuid source_content_id FK
        string model
        string prompt_version
        jsonb output_json "hook|caption|hashtags|title|category|posting_window"
        timestamp generated_at
        bool edited_by_user
    }

    ACCOUNTS {
        uuid id PK
        string name
        string platform
        string username
        string timezone
        bool active
        bool publishing_enabled
        string credential_reference
    }

    PLATFORM_CREDENTIALS {
        uuid id PK
        uuid account_id FK
        string platform
        string encrypted_payload "tokens cifrados, nunca en claro"
        timestamp expires_at
        timestamp refreshed_at
    }

    SCHEDULES {
        uuid id PK
        uuid post_id FK
        timestamp scheduled_at
        string timezone
        string recurrence_rule "null en V1, reservado"
    }

    POSTS {
        uuid id PK
        uuid content_item_id FK
        uuid account_id FK
        string platform
        timestamp scheduled_at
        enum status "DRAFT..MANUAL_ACTION_REQUIRED (7 estados)"
        string external_post_id
        timestamp published_at
        string failure_reason
        int retry_count
    }

    POST_EVENTS {
        uuid id PK
        uuid post_id FK
        string event_type "state_transition|publish_attempt|error"
        jsonb payload
        timestamp created_at
    }

    POST_METRICS {
        uuid id PK
        uuid post_id FK
        timestamp collected_at
        bigint views
        bigint likes
        bigint comments
        bigint shares
        bigint saves
        bigint watch_time_ms
        float completion_rate
        int followers_gained
        jsonb raw_platform_data "métricas específicas de plataforma, sin normalizar"
    }

    AUDIT_LOGS {
        uuid id PK
        uuid user_id FK
        string action
        string entity_type
        uuid entity_id
        jsonb before_json
        jsonb after_json
        timestamp created_at
    }

    SYSTEM_SETTINGS {
        uuid id PK
        string key
        jsonb value
    }
```

## Notas de diseño
- `POST_METRICS.raw_platform_data` (JSONB) guarda la respuesta cruda de cada
  plataforma; las columnas normalizadas (`views`, `likes`, etc.) son la
  capa común para el dashboard. Esto cumple el punto 16 del spec: "keep raw
  platform data and normalized metrics separate".
- `PLATFORM_CREDENTIALS.encrypted_payload` nunca se expone vía API; se
  descifra solo en memoria dentro de `publishers/<adapter>.py`.
- Los estados de `CONTENT_ITEMS.status` (13) y `POSTS.status` (7) se listan
  completos en el spec original (secciones 5.2 y 15); aquí se referencian
  por brevedad — deben implementarse como `Enum` de Python + `CHECK
  constraint` en la migración, no como string libre.

## Índices críticos (a crear en la primera migración)
```sql
CREATE INDEX ix_content_items_status ON content_items(status);
CREATE INDEX ix_content_items_source_published ON content_items(source_id, published_at);
CREATE INDEX ix_posts_status_scheduled ON posts(status, scheduled_at);
CREATE INDEX ix_posts_account_scheduled ON posts(account_id, scheduled_at);
CREATE INDEX ix_post_metrics_post_collected ON post_metrics(post_id, collected_at);
CREATE INDEX ix_render_jobs_status ON render_jobs(status);
CREATE INDEX ix_source_checks_source_checked ON source_checks(source_id, checked_at);
```
