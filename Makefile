.PHONY: test security-check ci api ui ingest-qdrant

test:
	pytest

security-check:
	python3 scripts/security_check.py

ci: security-check test

api:
	uvicorn app.api.main:app --reload

ui:
	streamlit run frontend/streamlit_app.py

ingest-qdrant:
	python3 scripts/ingest_qdrant.py
