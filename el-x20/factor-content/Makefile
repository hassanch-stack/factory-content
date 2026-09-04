.PHONY: up down migrate seed test lint

up:
	docker compose -f infra/docker-compose.yml up -d

down:
	docker compose -f infra/docker-compose.yml down

migrate:
	docker compose -f infra/docker-compose.yml exec api alembic upgrade head

seed:
	docker compose -f infra/docker-compose.yml exec api python -m app.scripts.seed

test:
	docker compose -f infra/docker-compose.yml exec api pytest
	cd apps/web && npm test --if-present

lint:
	docker compose -f infra/docker-compose.yml exec api ruff check .
	docker compose -f infra/docker-compose.yml exec api mypy app
	cd apps/web && npm run lint
