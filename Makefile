.PHONY: test api ui ingest-qdrant

test:
	pytest

api:
	uvicorn app.api.main:app --reload

ui:
	streamlit run frontend/streamlit_app.py

ingest-qdrant:
	python scripts/ingest_qdrant.py
