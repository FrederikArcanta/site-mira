"""Pin van docs/brand/tokens.json.

Een latere tokens-sync werkt tokens.json, TOKENS.sha256, DESIGN.md en
EXPECTED_SHA samen bij. Dit bestand herschrijft de tokens niet.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOKENS = ROOT / "docs" / "brand" / "tokens.json"
SHA_FILE = ROOT / "docs" / "brand" / "TOKENS.sha256"
DESIGN = ROOT / "docs" / "brand" / "DESIGN.md"

# Bij een tokens-sync samen bijwerken met tokens.json, TOKENS.sha256 en DESIGN.md.
EXPECTED_SHA = "7783233f1049a74b9f2fe5c00c4cb4c07a6601ec8124e9b162e691ec58ee799d"


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify() -> list[str]:
    errors: list[str] = []
    if not TOKENS.is_file():
        return ["pin: docs/brand/tokens.json ontbreekt"]
    got = file_sha(TOKENS)
    if got != EXPECTED_SHA:
        errors.append(f"pin: tokens.json sha256 {got} != EXPECTED_SHA")
    if not SHA_FILE.is_file():
        errors.append("pin: docs/brand/TOKENS.sha256 ontbreekt")
    else:
        raw = SHA_FILE.read_bytes()
        text = raw.decode("utf-8")
        field = text.split()[0] if text.split() else ""
        if field != EXPECTED_SHA:
            errors.append("pin: TOKENS.sha256 wijkt af van EXPECTED_SHA")
        if not raw.endswith(b"\n"):
            errors.append("pin: TOKENS.sha256 moet op een newline eindigen")
    if not DESIGN.is_file():
        errors.append("pin: docs/brand/DESIGN.md ontbreekt")
    elif EXPECTED_SHA not in DESIGN.read_text(encoding="utf-8"):
        errors.append("pin: DESIGN.md noemt EXPECTED_SHA niet")
    return errors
