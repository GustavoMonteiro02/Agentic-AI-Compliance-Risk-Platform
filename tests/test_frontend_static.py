import py_compile
from pathlib import Path


def test_streamlit_app_compiles():
    py_compile.compile(str(Path("frontend/streamlit_app.py")), doraise=True)

