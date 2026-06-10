from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentChunk:
    requirement_id: str
    title: str
    source: str
    category: str
    text: str
    jurisdiction: str = "internal"
    document_type: str = "unknown"
    authority: str = "Internal"
    source_url: str | None = None
    effective_date: str | None = None
    tags: tuple[str, ...] = ()

    @property
    def metadata(self) -> dict[str, str | list[str] | None]:
        return {
            "jurisdiction": self.jurisdiction,
            "document_type": self.document_type,
            "authority": self.authority,
            "source_url": self.source_url,
            "effective_date": self.effective_date,
            "tags": list(self.tags),
        }


METADATA_KEYS = {
    "category",
    "jurisdiction",
    "document type",
    "authority",
    "source url",
    "effective date",
    "tags",
}


def _source_defaults(source: str) -> dict[str, str | None]:
    lowered = source.lower()
    if lowered.startswith("regulations/"):
        return {"jurisdiction": "EU", "document_type": "regulation", "authority": "European Union"}
    if lowered.startswith("policies/"):
        return {"jurisdiction": "internal", "document_type": "policy", "authority": "Internal AI governance policy"}
    if lowered.startswith("controls/"):
        return {"jurisdiction": "internal", "document_type": "control", "authority": "Internal control library"}
    return {"jurisdiction": "internal", "document_type": "unknown", "authority": "Internal"}


def _empty_metadata(source: str) -> dict[str, str | None]:
    defaults = _source_defaults(source)
    return {
        "category": "general",
        "jurisdiction": defaults["jurisdiction"],
        "document_type": defaults["document_type"],
        "authority": defaults["authority"],
        "source_url": None,
        "effective_date": None,
        "tags": "",
    }


def _parse_metadata_line(line: str) -> tuple[str, str] | None:
    if ":" not in line:
        return None
    key, value = line.split(":", 1)
    normalized = key.strip().lower()
    if normalized not in METADATA_KEYS:
        return None
    return normalized, value.strip()


def _build_chunk(
    requirement_id: str,
    title: str,
    source: str,
    metadata: dict[str, str | None],
    buffer: list[str],
) -> DocumentChunk:
    tags = tuple(
        tag.strip().lower()
        for tag in (metadata.get("tags") or "").split(",")
        if tag.strip()
    )
    return DocumentChunk(
        requirement_id=requirement_id,
        title=title,
        source=source,
        category=(metadata.get("category") or "general").lower(),
        text="\n".join(buffer).strip(),
        jurisdiction=metadata.get("jurisdiction") or "internal",
        document_type=metadata.get("document_type") or "unknown",
        authority=metadata.get("authority") or "Internal",
        source_url=metadata.get("source_url") or None,
        effective_date=metadata.get("effective_date") or None,
        tags=tags,
    )


def parse_markdown_requirements(source: str, text: str) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    current_id = ""
    current_title = ""
    current_metadata = _empty_metadata(source)
    buffer: list[str] = []

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            if current_title and buffer:
                chunks.append(_build_chunk(current_id, current_title, source, current_metadata, buffer))
                buffer = []
            current_title = stripped.removeprefix("## ").strip()
            current_id = current_title.upper().replace(" ", "_").replace("-", "_")
            current_metadata = _empty_metadata(source)
        elif current_title and (metadata_line := _parse_metadata_line(stripped)):
            key, value = metadata_line
            normalized_key = key.replace(" ", "_")
            current_metadata[normalized_key] = value
        elif current_title and stripped and not stripped.startswith("# "):
            buffer.append(stripped)

    if current_title and buffer:
        chunks.append(_build_chunk(current_id, current_title, source, current_metadata, buffer))
    return chunks
