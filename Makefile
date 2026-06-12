.PHONY: test security-check ci api ui mcp migrate-db llm-smoke prod-up prod-down prod-ingest-qdrant prod-smoke ingest-qdrant ingest-pinecone validate-legal-sources register-legal-source

PYTHON ?= python3.11

test:
	pytest

security-check:
	$(PYTHON) scripts/security_check.py

ci: security-check test

api:
	uvicorn app.api.main:app --reload

ui:
	streamlit run frontend/streamlit_app.py

mcp:
	$(PYTHON) scripts/run_mcp_server.py

migrate-db:
	$(PYTHON) scripts/migrate_db.py

llm-smoke:
	$(PYTHON) scripts/smoke_llm.py

prod-up:
	docker compose --env-file .env -f docker-compose.production.yml up --build

prod-down:
	docker compose --env-file .env -f docker-compose.production.yml down

prod-ingest-qdrant:
	docker compose --env-file .env -f docker-compose.production.yml exec -e PYTHONPATH=/app api python scripts/ingest_qdrant.py

prod-smoke:
	set -a; . ./.env; set +a; API_BASE_URL=http://127.0.0.1:8000 $(PYTHON) scripts/smoke_production_stack.py

ingest-qdrant:
	$(PYTHON) scripts/ingest_qdrant.py

ingest-pinecone:
	$(PYTHON) scripts/ingest_pinecone.py

validate-legal-sources:
	$(PYTHON) scripts/validate_legal_sources.py

register-legal-source:
	$(PYTHON) scripts/register_legal_source.py
