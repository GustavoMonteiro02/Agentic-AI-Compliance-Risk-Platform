.PHONY: test api ui

test:
	pytest

api:
	uvicorn app.api.main:app --reload

ui:
	streamlit run frontend/streamlit_app.py

