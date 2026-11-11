"""Merklint voor de publieke site: hex, font buiten tokens, wissel naar Inter, oker-als-status.

De walk scant index.html en elk ander bestand van de publieke site met
.html, .css, .scss, .js, .tsx of .jsx. Tests, docs/, scripts/, .github/
en .cursor/ tellen niet mee. Tekst in die bestanden volgt dezelfde regels
als de webpoort, inclusief Tailwind-arbitrary values als die vorm in een
gescand bestand staat. Er is geen Tailwind-dependency in deze repo.

Bestaande overtredingen staan in de nulmeting. Een hogere telling faalt.
Verwijderen telt niet als fail. Dit script wijzigt de site niet.

Bekend gat: rgba(...) en rgb(...) vallen buiten de hex-poort. Een #hex
valt erbinnen. De lint is regelgebonden; een font-weight over meerdere
regels telt niet mee.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import pin

ROOT = pin.ROOT
BASELINE = ROOT / "docs" / "brand" / "baseline.txt"
BASE_COMMIT = "e0a72f79e1aee245b9017c9cf481a9a2d660dcc1"
SKIP_DIRS = {".git", "node_modules", ".venv", "__pycache__"}
SKIP_ROOTS = {"docs", "scripts", ".github", ".cursor"}
SKIP_PARTS = {"tests", "test", "__tests__", "spec", "specs"}
SCREEN_SUFFIXES = (".html", ".css", ".scss", ".jsx", ".tsx", ".js")
FIXTURE_PREFIX = "scripts/brand/fixtures/"
_TEST_FILE = re.compile(r"\.(?:test|spec)\.[^.]+$")

GENERICS = {
    "serif",
    "sans-serif",
    "monospace",
    "system-ui",
    "ui-sans-serif",
    "ui-serif",
    "ui-monospace",
    "emoji",
    "math",
    "fangsong",
    "cursive",
    "fantasy",
    "inherit",
    "initial",
    "unset",
    "revert",
    "revert-layer",
    "-apple-system",
    "blinkmacsystemfont",
}
ALLOWED_WEIGHTS = {"400", "700", "normal", "bold", "regular"}
SWIFT_WEIGHT_NUM = {
    "ultralight": "100",
    "thin": "200",
    "light": "300",
    "regular": "400",
    "medium": "500",
    "semibold": "600",
    "bold": "700",
    "heavy": "800",
    "black": "900",
}

OKER_VARS = {"--gold", "--oker", "--oker-dark"}
STATUS_WORD = re.compile(
    r"status|success|warning|danger|error|badge|pill-good|pill-warn|pill-bad|toast-ok|toast-err|banner-warn|banner-bad|(?:^|[^A-Za-z0-9])ok(?:[^A-Za-z0-9]|$)",
    re.IGNORECASE,
)
HEX_RE = re.compile(r"#([0-9A-Fa-f]{3,8})")
VAR_RE = re.compile(r"var\(\s*(--[A-Za-z0-9_-]+)")
PROP_RE = re.compile(r"(--[A-Za-z0-9_-]+)\s*:\s*([^;}{]+)")
FONT_FAMILY_RE = re.compile(r"font-family\s*:\s*([^;}{]+)", re.IGNORECASE)
FONT_FAMILY_ATTR_RE = re.compile(
    r"font-family\s*=\s*([\"'])(.*?)\1",
    re.IGNORECASE,
)
FONT_WEIGHT_RE = re.compile(r"font-weight\s*:\s*([^;}{]+)", re.IGNORECASE)
FONT_FAMILY_JS_RE = re.compile(
    r"fontFamily\s*:\s*(?:'([^']*)'|\"([^\"]*)\"|`([^`]*)`)"
)
FONT_WEIGHT_JS_RE = re.compile(r"fontWeight\s*:\s*([^,}\n]+)")
FAMILY_URL_RE = re.compile(r"family=([A-Za-z0-9+]+)")
WEIGHT_URL_RE = re.compile(r"wght@([0-9;]+)")
TW_FAMILY_RE = re.compile(r"font-\[(?:['\"])?([A-Za-z][^]\"]*?)(?:['\"])?\]")
TW_WEIGHT_RE = re.compile(r"(?<![\w-])font-\[([0-9]{3})\](?![\w-])")
TW_UTIL_RE = re.compile(
    r"(?<![\w-])font-(thin|extralight|light|normal|medium|semibold|bold|extrabold|black)(?![\w-])"
)
WEIGHT_TOKEN_RE = re.compile(
    r"\b(100|200|300|400|500|600|700|800|900|normal|bold|regular|lighter|bolder)\b",
    re.IGNORECASE,
)
ALLOW_RE = re.compile(r"brand-allow:\s*(\S.{2,})")
SWIFT_FONT_CALL = re.compile(
    r"(?:Font\.custom|\.custom|UIFont)\s*\(\s*(?:name:\s*)?([\"'])(.*?)\1"
)
SWIFT_WEIGHT_CALL = re.compile(
    r"\.(?:fontWeight|weight)\s*\(([^)]*)\)|Font\.Weight\.([A-Za-z]+)"
)
SWIFT_WEIGHT_NAME = re.compile(
    r"\b(ultraLight|thin|light|regular|medium|semibold|bold|heavy|black)\b",
    re.IGNORECASE,
)
SWIFT_OKER_REF = re.compile(
    r"(?<![\w-])((?:Theme\.)?oker(?:Dark|_dark)?|gold)(?![\w-])",
    re.IGNORECASE,
)
TW_WEIGHTS = {
    "thin": "100",
    "extralight": "200",
    "light": "300",
    "normal": "400",
    "medium": "500",
    "semibold": "600",
    "bold": "700",
    "extrabold": "800",
    "black": "900",
}


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    kind: str
    value: str
    message: str

    def key(self) -> tuple[str, str, str]:
        return (self.path, self.kind, self.value)


def load_catalog() -> dict:
    data = json.loads(pin.TOKENS.read_text(encoding="utf-8"))
    hex_to_name: dict[str, str] = {}

    def add(name: str, value: object) -> None:
        if isinstance(value, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
            hex_to_name.setdefault(value[1:].upper(), name)

    for group in ("colors", "semantic", "chart", "web_only", "hyperlink"):
        block = data.get(group) or {}
        if isinstance(block, dict):
            for key, value in block.items():
                add(f"{group}.{key}", value)

    web = (data.get("fonts") or {}).get("web") or {}
    allowed = {
        str(web.get("body") or ""),
        str(web.get("tcc_display") or ""),
        str(web.get("arcanta_display") or ""),
        str((data.get("fonts") or {}).get("office") or ""),
    }
    fonts = data.get("fonts") or {}
    for key in ("office_whitelist", "render_substitute", "glyph_whitelist_numbering_only"):
        for item in fonts.get(key) or []:
            allowed.add(str(item))
    allowed.discard("")
    banned = {str(item) for item in fonts.get("banned") or []}
    return {
        "hex_to_name": hex_to_name,
        "allowed_families": {name.casefold() for name in allowed},
        "banned": {name.casefold() for name in banned},
    }


def is_product_path(rel: str) -> bool:
    normal = rel.strip().replace("\\", "/").lstrip("./")
    if normal.startswith(FIXTURE_PREFIX):
        return False
    parts = [part for part in normal.split("/") if part]
    if not parts or any(part in SKIP_DIRS or part in SKIP_PARTS for part in parts):
        return False
    if parts[0] in SKIP_ROOTS:
        return False
    if _TEST_FILE.search(normal):
        return False
    return normal.endswith(SCREEN_SUFFIXES)


def expand_hex(body: str) -> str | None:
    raw = body.upper()
    if len(raw) == 3 and all(c in "0123456789ABCDEF" for c in raw):
        return "".join(c * 2 for c in raw)
    if len(raw) == 4 and any(c.isdigit() for c in raw):
        return "".join(c * 2 for c in raw[:3])
    if len(raw) == 6:
        return raw
    if len(raw) == 8:
        return raw[:6]
    return None


def color_context(line: str, start: int) -> bool:
    i = start - 1
    while i >= 0 and line[i] in " \t":
        i -= 1
    if i < 0:
        return False
    return line[i] in ":=\"'`([,"


def hex_message(catalog: dict, original: str, expanded: str) -> str:
    name = catalog["hex_to_name"].get(expanded)
    shown = f"#{expanded}"
    if name:
        return f"hardcoded {original} is token {name}; gebruik de token"
    return f"hardcoded {original} ({shown}) heeft geen token in tokens.json; geen losse hex"


def font_kind_message(catalog: dict, family: str) -> tuple[str, str] | None:
    key = family.casefold()
    if key in GENERICS or key.startswith("var("):
        return None
    if key == "inter":
        return (
            "font-inter",
            "fonts.web.body is Inter, maar een wissel naar Inter in de product-UI faalt tot UI/UX en Designer de spanning sluiten",
        )
    if key == "lato":
        return (
            "font-outside",
            "Lato staat als fonts.web.product_ui buiten scope; niet gebruiken in de product-UI",
        )
    if key in catalog["banned"]:
        return ("font-outside", f"{family} staat op fonts.banned")
    if key in catalog["allowed_families"]:
        return None
    return (
        "font-outside",
        f"{family} staat niet in de tokens. Geen eigen lettertype. Een wissel naar Inter faalt ook.",
    )


def weight_finding(value: str) -> tuple[str, str] | None:
    norm = value.casefold()
    if norm in ALLOWED_WEIGHTS or norm in {"inherit", "initial", "unset", "revert"}:
        return None
    shown = f"{norm} ({SWIFT_WEIGHT_NUM[norm]})" if norm in SWIFT_WEIGHT_NUM else norm
    return (
        "font-weight",
        f"font-weight {shown} staat niet in de tokens; alleen regular (400) en bold (700)",
    )


def status_context(text: str) -> bool:
    return STATUS_WORD.search(text) is not None


def oker_hexes() -> set[str]:
    return {"C48A3F", "8A5F28"}


def allowlisted(lines: list[str], index: int) -> bool:
    line = lines[index]
    prev = lines[index - 1] if index else ""
    return bool(ALLOW_RE.search(line) or ALLOW_RE.search(prev))


def families_from(value: str) -> list[str]:
    found: list[str] = []
    for part in value.split(","):
        name = part.strip().strip("'\"").replace("+", " ")
        name = name.replace("!important", "").strip()
        if name:
            found.append(name)
    return found


def add_family(findings: list[Finding], catalog: dict, rel: str, line_no: int, family: str) -> None:
    parsed = font_kind_message(catalog, family)
    if not parsed:
        return
    kind, message = parsed
    findings.append(Finding(rel, line_no, kind, family.casefold(), message))


def add_weight(findings: list[Finding], rel: str, line_no: int, raw: str) -> None:
    parsed = weight_finding(raw)
    if not parsed:
        return
    _kind, message = parsed
    norm = raw.casefold()
    findings.append(Finding(rel, line_no, "font-weight", norm, message))


def findings_for_line(
    catalog: dict,
    rel: str,
    line_no: int,
    line: str,
    context: str,
    oker_vars: dict[str, str],
) -> list[Finding]:
    findings: list[Finding] = []
    oker = oker_hexes()
    prop_match = PROP_RE.search(line)
    prop_name = prop_match.group(1) if prop_match else ""
    prop_is_status = bool(prop_name) and status_context(prop_name)
    line_status = status_context(context) or prop_is_status

    for match in HEX_RE.finditer(line):
        body = match.group(1)
        start = match.start()
        end = match.end()
        if start > 0 and (line[start - 1].isalnum() or line[start - 1] in "_-"):
            continue
        if end < len(line) and (line[end].isalnum() or line[end] in "_-"):
            continue
        if len(body) not in (3, 4, 6, 8):
            continue
        if len(body) == 4 and not any(c.isdigit() for c in body):
            continue
        if not color_context(line, start):
            continue
        expanded = expand_hex(body)
        if not expanded:
            continue
        original = "#" + body
        findings.append(
            Finding(rel, line_no, "hex", f"#{expanded}", hex_message(catalog, original, expanded))
        )
        if expanded in oker and line_status:
            token = "colors.oker" if expanded == "C48A3F" else "web_only.oker_dark"
            findings.append(
                Finding(
                    rel,
                    line_no,
                    "oker-status",
                    f"#{expanded}",
                    f"oker als status ({original}, {token}) faalt; semantisch groen voor status mag (semantic.ok)",
                )
            )

    for match in VAR_RE.finditer(line):
        name = match.group(1).lower()
        valued = oker_vars.get(name)
        if name not in OKER_VARS and not valued:
            continue
        named_status = status_context(name)
        if not named_status and not line_status:
            continue
        label = f"var({match.group(1)})"
        findings.append(
            Finding(
                rel,
                line_no,
                "oker-status",
                label.lower(),
                f"oker als status via {label} faalt; oker zonder statusbetekenis mag, semantisch groen voor status mag (semantic.ok)",
            )
        )

    if line_status:
        for match in SWIFT_OKER_REF.finditer(line):
            label = match.group(0)
            findings.append(
                Finding(
                    rel,
                    line_no,
                    "oker-status",
                    label.casefold(),
                    f"oker als status via {label} faalt; oker zonder statusbetekenis mag, semantisch groen voor status mag (semantic.ok)",
                )
            )

    for match in FONT_FAMILY_RE.finditer(line):
        for family in families_from(match.group(1)):
            add_family(findings, catalog, rel, line_no, family)
    for match in FONT_FAMILY_ATTR_RE.finditer(line):
        for family in families_from(match.group(2)):
            add_family(findings, catalog, rel, line_no, family)
    for match in FONT_FAMILY_JS_RE.finditer(line):
        value = next(group for group in match.groups() if group is not None)
        for family in families_from(value):
            add_family(findings, catalog, rel, line_no, family)
    for match in FAMILY_URL_RE.finditer(line):
        add_family(findings, catalog, rel, line_no, match.group(1).replace("+", " "))
    for match in TW_FAMILY_RE.finditer(line):
        raw = match.group(1).strip().strip("'\"")
        if raw and not raw.isdigit():
            add_family(findings, catalog, rel, line_no, raw)
    for match in SWIFT_FONT_CALL.finditer(line):
        for family in families_from(match.group(2)):
            add_family(findings, catalog, rel, line_no, family)

    weight_blobs: list[str] = []
    for match in FONT_WEIGHT_RE.finditer(line):
        weight_blobs.append(match.group(1))
    for match in FONT_WEIGHT_JS_RE.finditer(line):
        weight_blobs.append(match.group(1))
    for match in WEIGHT_URL_RE.finditer(line):
        weight_blobs.append(match.group(1).replace(";", " "))
    for blob in weight_blobs:
        for token in WEIGHT_TOKEN_RE.findall(blob):
            add_weight(findings, rel, line_no, token)
    for match in TW_WEIGHT_RE.finditer(line):
        add_weight(findings, rel, line_no, match.group(1))
    for match in TW_UTIL_RE.finditer(line):
        add_weight(findings, rel, line_no, TW_WEIGHTS[match.group(1)])
    for match in SWIFT_WEIGHT_CALL.finditer(line):
        blob = match.group(1) if match.group(1) is not None else match.group(2) or ""
        for name in SWIFT_WEIGHT_NAME.findall(blob):
            add_weight(findings, rel, line_no, name)
    return findings


def collect_oker_vars(text: str) -> dict[str, str]:
    found: dict[str, str] = {}
    oker = oker_hexes()
    for match in PROP_RE.finditer(text):
        name = match.group(1).lower()
        for hex_match in HEX_RE.finditer(match.group(2)):
            expanded = expand_hex(hex_match.group(1))
            if expanded in oker:
                found[name] = expanded
    return found


def css_contexts(lines: list[str]) -> list[tuple[str, str]]:
    depth = 0
    pending = ""
    selector = ""
    out: list[tuple[str, str]] = []
    for line in lines:
        if depth == 0:
            pending += line + "\n"
            if "{" in line:
                selector = pending
                depth = pending.count("{") - pending.count("}")
                if depth < 0:
                    depth = 0
                out.append((line, selector))
                if depth == 0:
                    pending = ""
                    selector = ""
            else:
                out.append((line, pending))
        else:
            depth += line.count("{") - line.count("}")
            out.append((line, selector + line))
            if depth <= 0:
                depth = 0
                pending = ""
                selector = ""
    return out


def scan_text(catalog: dict, rel: str, text: str) -> list[Finding]:
    lines = text.splitlines()
    oker_vars = collect_oker_vars(text)
    track = rel.endswith((".css", ".scss"))
    contexts = css_contexts(lines) if track else []
    findings: list[Finding] = []
    prev = ""
    for index, line in enumerate(lines):
        if allowlisted(lines, index):
            prev = line
            continue
        if track:
            context = contexts[index][1]
        else:
            context = prev + "\n" + line
        findings.extend(
            findings_for_line(catalog, rel, index + 1, line, context, oker_vars)
        )
        prev = line
    return findings


def iter_product_files() -> list[Path]:
    found: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        rel = path.relative_to(ROOT).as_posix()
        if is_product_path(rel):
            found.append(path)
    return sorted(found)


def scan_repo(catalog: dict | None = None) -> list[Finding]:
    catalog = catalog or load_catalog()
    findings: list[Finding] = []
    for path in iter_product_files():
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        findings.extend(scan_text(catalog, rel, text))
    return findings


def parse_baseline(text: str) -> list[Finding]:
    rows: list[Finding] = []
    for raw in text.splitlines():
        if not raw.strip() or raw.startswith("#"):
            continue
        path, line, kind, value, message = raw.split("\t", 4)
        rows.append(Finding(path, int(line), kind, value, message))
    return rows


def format_baseline(findings: list[Finding], header: str) -> str:
    lines = [header.rstrip(), ""]
    for item in sorted(findings, key=lambda f: (f.path, f.line, f.kind, f.value)):
        lines.append(f"{item.path}\t{item.line}\t{item.kind}\t{item.value}\t{item.message}")
    lines.append("")
    return "\n".join(lines)


def excess(current: list[Finding], baseline: list[Finding]) -> list[tuple[Finding, int, int]]:
    base = Counter(item.key() for item in baseline)
    cur = Counter(item.key() for item in current)
    over: list[tuple[Finding, int, int]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in current:
        key = item.key()
        if key in seen:
            continue
        if cur[key] > base[key]:
            seen.add(key)
            over.append((item, cur[key], base[key]))
    return over


def write_baseline(findings: list[Finding]) -> None:
    header = (
        f"# Nulmeting merkovertredingen in de publieke site op main {BASE_COMMIT}.\n"
        "# Sleutel is path + kind + value. Een hogere telling faalt. Lager mag (opruimen is een andere PR).\n"
        "# Dezelfde regel kan vaker staan als die waarde er vaker op staat.\n"
        "# Buiten deze poort, niet opgeruimd: rgba/rgb. Een #hex valt erbinnen.\n"
        "# path, line, kind, value, message"
    )
    BASELINE.write_text(format_baseline(findings, header), encoding="utf-8")


def check(findings: list[Finding] | None = None) -> list[str]:
    errors = pin.verify()
    if errors:
        return errors
    if not BASELINE.is_file():
        return ["ratchet: docs/brand/baseline.txt ontbreekt"]
    current = scan_repo() if findings is None else findings
    baseline = parse_baseline(BASELINE.read_text(encoding="utf-8"))
    messages: list[str] = []
    for item, now, was in excess(current, baseline):
        messages.append(
            f"ratchet: {item.path}:{item.line} {item.kind} {item.value} "
            f"telling {now} > baseline {was}. {item.message}"
        )
    return messages


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Merklint site-mira")
    parser.add_argument("--write-baseline", action="store_true")
    args = parser.parse_args(argv)
    pin_errors = pin.verify()
    if pin_errors:
        for err in pin_errors:
            print(err, file=sys.stderr)
        return 1
    findings = scan_repo()
    if args.write_baseline:
        write_baseline(findings)
        print(f"baseline geschreven: {BASELINE.relative_to(ROOT)} ({len(findings)} regels)")
        return 0
    errors = check(findings)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    print(f"pin ok {pin.EXPECTED_SHA}")
    print(f"ratchet ok ({len(findings)} bestaande, 0 nieuw)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
