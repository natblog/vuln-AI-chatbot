COMPOSE := docker compose

.PHONY: help up up-build down restart build logs ps test test-live backend-shell reseed

help:
	@echo "Available commands:"
	@echo "  make up             Start all services in the background"
	@echo "  make up-build       Build images and start all services"
	@echo "  make down           Stop and remove services"
	@echo "  make restart        Restart all services"
	@echo "  make build          Build service images"
	@echo "  make logs           Follow logs from all services"
	@echo "  make ps             Show service status"
	@echo "  make test           Run backend tests"
	@echo "  make test-live      Run live tests against the Compose stack"
	@echo "  make backend-shell  Open a shell in the backend container"
	@echo "  make reseed         Reseed the database"

up:
	$(COMPOSE) up -d
	@echo "  Backend:  http://localhost:8000/docs"
	@echo "  Frontend: http://localhost:3000"
	@echo "  MailHog:  http://localhost:8025"

up-build:
	$(COMPOSE) up --build -d
	@echo "  Backend:  http://localhost:8000/docs"
	@echo "  Frontend: http://localhost:3000"
	@echo "  MailHog:  http://localhost:8025"

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) restart

build:
	$(COMPOSE) build

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

test:
	cd backend && PYTHONPATH=. pytest tests/ -v

test-live:
	cd backend && LIVE=1 PYTHONPATH=. pytest tests/ -v

backend-shell:
	$(COMPOSE) exec backend sh

reseed:
	curl -X POST http://localhost:8000/api/reseed