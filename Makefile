.PHONY: test security-check ci api ui mcp ingest-qdrant ingest-pinecone validate-legal-sources

test:
	pytest

security-check:
	python3 scripts/security_check.py

ci: security-check test

api:
	uvicorn app.api.main:app --reload

ui:
	streamlit run frontend/streamlit_app.py

mcp:
	python3 scripts/run_mcp_server.py

ingest-qdrant:
	python3 scripts/ingest_qdrant.py

ingest-pinecone:
	python3 scripts/ingest_pinecone.py

validate-legal-sources:
	python3 scripts/validate_legal_sources.py
