"""PR-beleid: acceptatiecriteria, scherm, verify, tokens-sync en baseline-telling.

Een PR die het aantal findings in docs/brand/baseline.txt laat stijgen,
faalt. Uitzondering: het label baseline-raise staat er (hoofdlettergevoelig,
zoals tokens-sync) én ## Baseline-reden heeft een niet-lege reden.
Dalen of gelijk blijven mag zonder dat label. Commentaarregels tellen
niet mee. De verify-regel blijft zoals ze is.

Volgt AGENTS.md «Klaar als»:
- Verify: een zin met niet gedraaid / niet uitgevoerd zonder vraagteken,
  of een commando én een resultaatwoord. Een vraag telt niet.
  Een commando zonder resultaatwoord faalt ook als dezelfde sectie
  zegt dat iets niet gedraaid is. Een commando mét resultaatwoord mag
  daarnaast zeggen dat iets anders niet gedraaid is.
- Scherm: het gewijzigde scherm, of expliciet dat er geen scherm is geraakt.
  Schermbestanden zijn index.html en elk ander bestand van de publieke site
  met .html, .css, .scss, .js, .tsx of .jsx.
  Tests, docs, scripts, CI, rules en tokens zijn geen scherm.
  check_screen bekijkt alleen de sectie ## Scherm.

Een feature-PR die de merkkopie of de pin wijzigt, faalt.
Titel of label moet exact `tokens-sync` bevatten (hoofdlettergevoelig).
Acceptatiecriteria is alleen niet-leeg. Geen screenshot-eis.

`geen scherm` plus een genoemd schermpad faalt ook als de diff geen scherm raakt.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

import lint

SYNC_PATHS = (
    "docs/brand/tokens.json",
    "docs/brand/TOKENS.sha256",
    "docs/brand/DESIGN.md",
    "scripts/brand/pin.py",
)
SECTIONS = ("Acceptatiecriteria", "Scherm", "Verify")
SCREEN_SUFFIXES = (".html", ".css", ".scss", ".jsx", ".tsx", ".js")
SKIP_ROOTS = {"docs", "scripts", ".github", ".cursor"}
SKIP_PARTS = {
    ".git",
    "node_modules",
    ".venv",
    "__pycache__",
    "tests",
    "test",
    "__tests__",
    "spec",
    "specs",
}
_TEST_FILE = re.compile(r"\.(?:test|spec)\.[^.]+$")
_MENTIONED_SCREEN = re.compile(
    r"(?<![\w./-])([\w./-]+\.(?:html|css|scss|jsx|tsx|js))"
)
_NO_SCREEN = re.compile(r"geen\s+scherm", re.IGNORECASE)
_NOT_RUN = re.compile(r"niet\s+(?:gedraaid|uitgevoerd)", re.IGNORECASE)
_COMMAND = re.compile(
    r"`[^`\n]+`|\b(?:python3?|pytest|npm|npx|node|bash)\b",
    re.IGNORECASE,
)
_RESULT = re.compile(
    r"\b(?:ok|geslaagd|passed|pass|fail|failed|faalde|gefaald|exit|resultaat|groen|rood|succes|success)\b"
    r"|\b\d+\s+(?:passed|tests?|fouten|errors)\b"
    r"|exit\s*(?:code\s*)?\d+",
    re.IGNORECASE,
)


def section_text(body: str, name: str) -> str | None:
    body = (body or "").replace("\r\n", "\n").replace("\r", "\n")
    match = re.search(rf"^##\s+{re.escape(name)}\s*$", body, re.MULTILINE)
    if not match:
        return None
    rest = body[match.end() :]
    nxt = re.search(r"^##\s+", rest, re.MULTILINE)
    chunk = rest[: nxt.start()] if nxt else rest
    chunk = re.sub(r"<!--.*?-->", "", chunk, flags=re.DOTALL)
    return chunk.strip()


def is_screen_path(path: str) -> bool:
    normal = path.strip().replace("\\", "/").lstrip("./")
    parts = [part for part in normal.split("/") if part]
    if not parts or any(part in SKIP_PARTS for part in parts):
        return False
    if parts[0] in SKIP_ROOTS:
        return False
    if _TEST_FILE.search(normal):
        return False
    return normal.endswith(SCREEN_SUFFIXES)


def _sentences(text: str) -> list[str]:
    parts = re.split(r"\n+|(?<=[.!?])\s+", text.strip())
    return [part.strip() for part in parts if part.strip()]


def explicit_not_run(text: str) -> bool:
    for sentence in _sentences(text):
        if _NOT_RUN.search(sentence) and "?" not in sentence:
            return True
    return False


def check_verify(text: str) -> list[str]:
    has_command = _COMMAND.search(text) is not None
    has_result = _RESULT.search(text) is not None
    if has_command and has_result:
        return []
    if has_command:
        return [
            "PR-beleid: Verify noemt een commando zonder resultaat. "
            "Zet het resultaat erbij. «niet gedraaid» in dezelfde sectie dekt een kaal commando niet."
        ]
    if explicit_not_run(text):
        return []
    return [
        "PR-beleid: Verify zegt niet dat het commando gedraaid is "
        "(commando én resultaat) en zegt niet expliciet dat het niet gedraaid is."
    ]


def check_screen(text: str, paths: list[str]) -> list[str]:
    changed = [path for path in paths if is_screen_path(path)]
    mentioned: list[str] = []
    for found in _MENTIONED_SCREEN.findall(text):
        if is_screen_path(found) and found not in mentioned:
            mentioned.append(found)
    claims_none = _NO_SCREEN.search(text) is not None
    if not changed:
        if claims_none and mentioned:
            listed = ", ".join(mentioned)
            return [
                "PR-beleid: Scherm zegt dat er geen scherm is geraakt, "
                f"maar noemt ook {listed}."
            ]
        if claims_none:
            return []
        if mentioned:
            listed = ", ".join(mentioned)
            return [
                f"PR-beleid: Scherm noemt {listed}, maar de diff wijzigt geen scherm. "
                "Zeg expliciet dat er geen scherm is geraakt."
            ]
        return ["PR-beleid: Scherm zegt niet expliciet dat er geen scherm is geraakt."]
    errors: list[str] = []
    if claims_none:
        errors.append(
            "PR-beleid: de diff wijzigt een scherm, maar Scherm zegt dat er geen scherm is geraakt."
        )
    missing = [path for path in changed if path not in text]
    extra = [path for path in mentioned if path not in changed]
    if missing:
        errors.append(
            "PR-beleid: Scherm noemt het gewijzigde scherm niet: " + ", ".join(missing)
        )
    if extra:
        errors.append(
            "PR-beleid: Scherm noemt een ander scherm dan de diff: " + ", ".join(extra)
        )
    return errors


def check_body(body: str, paths: list[str] | None = None) -> list[str]:
    errors: list[str] = []
    for name in SECTIONS:
        content = section_text(body or "", name)
        if content is None:
            errors.append(f"PR-beleid: sectie '## {name}' ontbreekt")
        elif not content:
            errors.append(f"PR-beleid: sectie '## {name}' is leeg")
        elif name == "Verify":
            errors.extend(check_verify(content))
        elif name == "Scherm" and paths is not None:
            errors.extend(check_screen(content, paths))
    return errors


def check_sync(paths: list[str], title: str, labels: list[str]) -> list[str]:
    hit = [path for path in paths if path in SYNC_PATHS]
    if not hit:
        return []
    blob = (title or "") + "\n" + "\n".join(labels)
    if "tokens-sync" in blob:
        return []
    listed = ", ".join(hit)
    return [f"PR-beleid: {listed} wijzigt alleen in een PR met titel of label tokens-sync"]


BASELINE_PATH = "docs/brand/baseline.txt"
BASELINE_LABEL = "baseline-raise"


def check_baseline_raise(
    base_text: str,
    head_text: str,
    labels: list[str],
    body: str,
) -> list[str]:
    before = len(lint.parse_baseline(base_text or ""))
    after = len(lint.parse_baseline(head_text or ""))
    if after <= before:
        return []
    reason = section_text(body or "", "Baseline-reden")
    if BASELINE_LABEL in labels and reason:
        return []
    if BASELINE_LABEL not in labels:
        return [
            "PR-beleid: docs/brand/baseline.txt stijgt "
            f"van {before} naar {after} findings. "
            "Dat mag alleen met het label baseline-raise (hoofdlettergevoelig) "
            "én een niet-lege reden in ## Baseline-reden."
        ]
    return [
        "PR-beleid: label baseline-raise staat er, maar ## Baseline-reden ontbreekt of is leeg."
    ]


def file_at(rev: str, path: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "show", f"{rev}:{path}"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return ""


def changed_paths(base: str, head: str) -> list[str]:
    out = subprocess.check_output(
        ["git", "diff", "--name-only", base, head],
        text=True,
    )
    return [line.strip() for line in out.splitlines() if line.strip()]


def main() -> int:
    title = os.environ.get("PR_TITLE", "")
    body = os.environ.get("PR_BODY", "")
    labels = [part for part in os.environ.get("PR_LABELS", "").split(",") if part]
    base = os.environ.get("BASE_SHA", "")
    head = os.environ.get("HEAD_SHA", "")
    paths: list[str] | None = None
    errors: list[str] = []
    if not base or not head:
        errors.append("PR-beleid: BASE_SHA en HEAD_SHA ontbreken")
    else:
        paths = changed_paths(base, head)
        errors.extend(check_sync(paths, title, labels))
        if BASELINE_PATH in paths:
            errors.extend(
                check_baseline_raise(
                    file_at(base, BASELINE_PATH),
                    file_at(head, BASELINE_PATH),
                    labels,
                    body,
                )
            )
    errors = check_body(body, paths) + errors
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    print("PR-beleid ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
