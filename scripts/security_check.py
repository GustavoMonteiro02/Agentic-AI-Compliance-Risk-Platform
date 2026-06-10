from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKED_SUFFIXES = {".py", ".md", ".yml", ".yaml", ".toml", ".txt", ".example", ".env"}
SKIP_DIRS = {".git", ".pytest_cache", "__pycache__", ".ruff_cache"}

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"(?i)openai_api_key\s*=\s*['\"]?sk-"),
    re.compile(r"(?im)^platform_api_key\s*=\s*(?!change-me\s*$)[A-Za-z0-9_\-]{16,}\s*$"),
]

REQUIRED_ENV_LINES = {
    "AUTH_MODE=disabled",
    "PLATFORM_API_KEY=",
    "DEFAULT_TENANT_ID=default",
}


def iter_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path == Path(__file__).resolve():
            continue
        if path.is_file() and (path.suffix in CHECKED_SUFFIXES or path.name == ".env.example"):
            files.append(path)
    return files


def scan_for_secrets() -> list[str]:
    findings: list[str] = []
    for path in iter_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(f"{path.relative_to(ROOT)} matches {pattern.pattern}")
    return findings


def validate_env_example() -> list[str]:
    env_path = ROOT / ".env.example"
    text = env_path.read_text(encoding="utf-8")
    return [f".env.example missing {line}" for line in REQUIRED_ENV_LINES if line not in text]


def main() -> None:
    findings = scan_for_secrets() + validate_env_example()
    if findings:
        print("Security check failed:")
        for finding in findings:
            print(f"- {finding}")
        raise SystemExit(1)
    print("Security check passed.")


if __name__ == "__main__":
    main()
