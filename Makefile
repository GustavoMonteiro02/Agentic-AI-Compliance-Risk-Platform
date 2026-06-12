.PHONY: test security-check ci api ui mcp migrate-db llm-smoke ingest-qdrant ingest-pinecone validate-legal-sources register-legal-source

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

ingest-qdrant:
	$(PYTHON) scripts/ingest_qdrant.py

ingest-pinecone:
	$(PYTHON) scripts/ingest_pinecone.py

validate-legal-sources:
	$(PYTHON) scripts/validate_legal_sources.py

register-legal-source:
	$(PYTHON) scripts/register_legal_source.py
