import py_compile
import json
from pathlib import Path


def test_streamlit_app_compiles():
    py_compile.compile(str(Path("frontend/streamlit_app.py")), doraise=True)


def test_react_saas_ui_scaffold_is_present():
    package = json.loads(Path("frontend/react_app/package.json").read_text(encoding="utf-8"))
    app = Path("frontend/react_app/src/App.tsx").read_text(encoding="utf-8")
    styles = Path("frontend/react_app/src/styles.css").read_text(encoding="utf-8")

    assert package["scripts"]["dev"].startswith("vite")
    assert "lucide-react" in package["dependencies"]
    assert "Governance command center" in app
    assert "grid-template-columns: 280px minmax(0, 1fr)" in styles
