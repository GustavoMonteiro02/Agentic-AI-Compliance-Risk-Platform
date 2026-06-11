from pathlib import Path
import json
from typing import Any


def load_legal_sources_manifest(base_path: Path) -> dict[str, Any]:
    manifest_path = base_path / "legal_sources_manifest.json"
    if not manifest_path.exists():
        return {"version": "unversioned", "sources": []}
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def save_legal_sources_manifest(base_path: Path, manifest: dict[str, Any]) -> None:
    manifest_path = base_path / "legal_sources_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def register_legal_source(base_path: Path, source: dict[str, Any]) -> dict[str, Any]:
    required = {"id", "title", "jurisdiction", "authority", "source_url", "document_type", "local_path"}
    missing = sorted(field for field in required if not source.get(field))
    if missing:
        raise ValueError(f"Missing required legal source fields: {', '.join(missing)}")

    local_path = base_path / source["local_path"]
    if not local_path.exists():
        raise ValueError(f"Legal source local_path does not exist: {source['local_path']}")

    manifest = load_legal_sources_manifest(base_path)
    sources = [item for item in manifest.get("sources", []) if item.get("id") != source["id"]]
    registered = {
        **source,
        "ingestion_status": source.get("ingestion_status", "available"),
        "notes": source.get("notes", "Registered local official-source document."),
    }
    sources.append(registered)
    manifest["sources"] = sorted(sources, key=lambda item: item["id"])
    save_legal_sources_manifest(base_path, manifest)
    return registered
