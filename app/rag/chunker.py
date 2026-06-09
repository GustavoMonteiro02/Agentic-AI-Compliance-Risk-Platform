from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentChunk:
    requirement_id: str
    title: str
    source: str
    category: str
    text: str


def parse_markdown_requirements(source: str, text: str) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    current_id = ""
    current_title = ""
    current_category = "general"
    buffer: list[str] = []

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            if current_title and buffer:
                chunks.append(
                    DocumentChunk(current_id, current_title, source, current_category, "\n".join(buffer).strip())
                )
                buffer = []
            current_title = stripped.removeprefix("## ").strip()
            current_id = current_title.upper().replace(" ", "_").replace("-", "_")
        elif stripped.startswith("Category:"):
            current_category = stripped.removeprefix("Category:").strip().lower()
        elif current_title and stripped and not stripped.startswith("# "):
            buffer.append(stripped)

    if current_title and buffer:
        chunks.append(DocumentChunk(current_id, current_title, source, current_category, "\n".join(buffer).strip()))
    return chunks
