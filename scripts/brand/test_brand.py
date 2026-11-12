"""Fixtures voor pin, ratchet en PR-beleid. Geen productcode."""

from __future__ import annotations

import json
import unittest

import lint
import pin
import pr_policy


class PinTests(unittest.TestCase):
    def test_expected_sha_is_the_landed_pin(self) -> None:
        self.assertEqual(
            pin.EXPECTED_SHA,
            "7783233f1049a74b9f2fe5c00c4cb4c07a6601ec8124e9b162e691ec58ee799d",
        )

    def test_committed_copy_matches_pin(self) -> None:
        self.assertEqual(pin.verify(), [])

    def test_versions_are_both_1_1_4(self) -> None:
        data = json.loads(pin.TOKENS.read_bytes())
        self.assertEqual(data["version"], "1.1.4")
        self.assertEqual(data["custom_properties"]["brand_version"], "1.1.4")

    def test_product_ui_stays_lato_out_of_scope(self) -> None:
        data = json.loads(pin.TOKENS.read_bytes())
        self.assertEqual(data["fonts"]["web"]["product_ui"], "Lato (buiten scope)")

    def test_design_uses_ok_and_r3_naming(self) -> None:
        text = pin.DESIGN.read_text(encoding="utf-8")
        self.assertIn("OK-1 tot OK-5", text)
        self.assertIn("regel R-3", text)
        self.assertNotIn("mag (R-3)", text)
        self.assertIn(pin.EXPECTED_SHA, text)

    def test_tampered_bytes_fail(self) -> None:
        original = pin.file_sha
        try:
            pin.file_sha = lambda _path: "0" * 64  # type: ignore[assignment]
            errors = pin.verify()
        finally:
            pin.file_sha = original  # type: ignore[assignment]
        self.assertTrue(any("EXPECTED_SHA" in err for err in errors))


class LintFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = lint.load_catalog()

    def scan(self, name: str, text: str) -> list[lint.Finding]:
        return lint.scan_text(self.catalog, name, text)

    def test_product_walk_is_the_public_site(self) -> None:
        self.assertTrue(lint.is_product_path("index.html"))
        self.assertTrue(lint.is_product_path("privacy.html"))
        self.assertTrue(lint.is_product_path("css/site.css"))
        self.assertTrue(lint.is_product_path("css/site.scss"))
        self.assertTrue(lint.is_product_path("js/app.js"))
        self.assertTrue(lint.is_product_path("src/App.jsx"))
        self.assertTrue(lint.is_product_path("src/App.tsx"))
        self.assertFalse(lint.is_product_path("docs/brand/tokens.json"))
        self.assertFalse(lint.is_product_path("docs/brand/DESIGN.md"))
        self.assertFalse(lint.is_product_path("docs/page.html"))
        self.assertFalse(lint.is_product_path("scripts/brand/lint.py"))
        self.assertFalse(lint.is_product_path("scripts/brand/fixtures/bad.html"))
        self.assertFalse(lint.is_product_path(".github/workflows/brand.yml"))
        self.assertFalse(lint.is_product_path(".cursor/rules/ui-tokens.mdc"))
        self.assertFalse(lint.is_product_path("tests/page.html"))
        self.assertFalse(lint.is_product_path("js/app.test.js"))
        self.assertFalse(lint.is_product_path("js/app.spec.jsx"))
        self.assertFalse(lint.is_product_path("node_modules/pkg/index.js"))
        self.assertFalse(lint.is_product_path("AGENTS.md"))
        rels = [path.relative_to(lint.ROOT).as_posix() for path in lint.iter_product_files()]
        self.assertEqual(rels, ["index.html"])

    def test_screen_paths_match_product_paths(self) -> None:
        samples = [
            "index.html",
            "css/site.css",
            "css/site.scss",
            "js/app.js",
            "src/App.jsx",
            "src/App.tsx",
            "docs/page.html",
            "scripts/brand/lint.py",
            "scripts/brand/fixtures/bad.html",
            ".github/workflows/brand.yml",
            ".cursor/rules/ui-tokens.mdc",
            "tests/page.html",
            "test/page.js",
            "__tests__/page.js",
            "js/app.test.js",
            "js/app.spec.tsx",
            "node_modules/pkg/index.js",
            "AGENTS.md",
            "dist/app.js",
        ]
        for path in samples:
            self.assertEqual(
                lint.is_product_path(path),
                pr_policy.is_screen_path(path),
                path,
            )

    def test_html_hex_names_oker_token(self) -> None:
        found = self.scan("tijdelijke.html", '<p style="color: #C48A3F">x</p>\n')
        self.assertTrue(any(item.kind == "hex" and "colors.oker" in item.message for item in found))

    def test_css_variable_without_hex_passes(self) -> None:
        self.assertEqual(self.scan("ok.css", ".kicker { color: var(--accent); }\n"), [])

    def test_same_green_via_hex_names_semantic_ok_and_is_not_oker(self) -> None:
        found = self.scan("tijdelijke.html", '<p style="color: #1F8A5B">ok</p>\n')
        self.assertTrue(any(item.kind == "hex" and "semantic.ok" in item.message for item in found))
        self.assertFalse(any(item.kind == "oker-status" for item in found))

    def test_font_outside_tokens(self) -> None:
        found = self.scan("tijdelijke.html", '<style>body { font-family: "Comic Sans", sans-serif; }</style>\n')
        self.assertTrue(any(item.kind == "font-outside" and item.value == "comic sans" for item in found))

    def test_inter_switch_fails_even_though_it_is_web_body(self) -> None:
        found = self.scan("tijdelijke.html", "<style>body { font-family: Inter, sans-serif; }</style>\n")
        self.assertTrue(any(item.kind == "font-inter" for item in found))
        self.assertIn("wissel naar Inter", found[0].message)

    def test_interne_sentence_is_not_a_font(self) -> None:
        text = "<p>Interne should-cost, geen offerte.</p>\n"
        self.assertEqual(self.scan("tijdelijke.html", text), [])

    def test_lato_is_outside_product_ui(self) -> None:
        found = self.scan("tijdelijke.html", "<style>body { font-family: Lato, sans-serif; }</style>\n")
        self.assertTrue(any(item.kind == "font-outside" and item.value == "lato" for item in found))

    def test_font_family_attribute_inter_fails(self) -> None:
        found = self.scan("tijdelijke.html", '<text font-family="Inter">Mira</text>\n')
        self.assertTrue(any(item.kind == "font-inter" for item in found))

    def test_weight_outside_tokens(self) -> None:
        found = self.scan("weight.css", ".x { font-weight: 300; }\n")
        self.assertTrue(any(item.kind == "font-weight" and item.value == "300" for item in found))

    def test_semibold_fails_and_bold_passes(self) -> None:
        failed = self.scan("tijdelijke.html", '<p style="font-weight: 600">x</p>\n')
        self.assertTrue(any(item.kind == "font-weight" and item.value == "600" for item in failed))
        self.assertEqual(self.scan("bold.css", ".x { font-weight: 700; }\n"), [])
        self.assertEqual(self.scan("tijdelijke.html", '<p class="font-bold">x</p>\n'), [])

    def test_tailwind_weight_utility_fails(self) -> None:
        found = self.scan("tijdelijke.html", '<p class="font-semibold">x</p>\n')
        self.assertTrue(any(item.kind == "font-weight" and item.value == "600" for item in found))

    def test_oker_hex_as_status_fails(self) -> None:
        text = '<p class="status" style="color: #C48A3F">ok</p>\n'
        found = self.scan("tijdelijke.html", text)
        self.assertTrue(any(item.kind == "oker-status" and item.value == "#C48A3F" for item in found))

    def test_oker_dark_status_fails(self) -> None:
        text = '<p class="status" style="background: #8A5F28">ok</p>\n'
        found = self.scan("tijdelijke.html", text)
        self.assertTrue(any(item.kind == "oker-status" and "web_only.oker_dark" in item.message for item in found))

    def test_oker_accent_hex_is_not_status(self) -> None:
        text = '<span style="color: #C48A3F">merk</span>\n'
        found = self.scan("tijdelijke.html", text)
        self.assertTrue(any(item.kind == "hex" for item in found))
        self.assertFalse(any(item.kind == "oker-status" for item in found))

    def test_oker_accent_variable_passes(self) -> None:
        text = ":root { --gold: #C48A3F; }\n.kicker { color: var(--gold); }\n"
        found = self.scan("accent.css", text)
        self.assertTrue(any(item.kind == "hex" for item in found))
        self.assertFalse(any(item.kind == "oker-status" for item in found))

    def test_warning_variable_is_oker_status(self) -> None:
        text = ":root { --warning: #c48a3f; }\n.pill-warn { color: var(--warning); }\n"
        found = self.scan("warn.css", text)
        self.assertTrue(any(item.kind == "oker-status" and "var(--warning)" in item.value for item in found))

    def test_tailwind_arbitrary_hex_names_token(self) -> None:
        found = self.scan("tijdelijke.html", '<div class="bg-[#C48A3F]"></div>\n')
        self.assertTrue(any(item.kind == "hex" and "colors.oker" in item.message for item in found))

    def test_tailwind_inter_fails(self) -> None:
        found = self.scan("tijdelijke.html", "<div class=\"font-['Inter']\"></div>\n")
        self.assertTrue(any(item.kind == "font-inter" for item in found))

    def test_js_font_family_inter_fails(self) -> None:
        found = self.scan("app.js", "const style = { fontFamily: 'Inter' };\n")
        self.assertTrue(any(item.kind == "font-inter" for item in found))

    def test_allowlist_with_reason_suppresses(self) -> None:
        text = '<span style="color: #C48A3F">logo</span> <!-- brand-allow: logo-asset modulemark -->\n'
        self.assertEqual(self.scan("tijdelijke.html", text), [])

    def test_allowlist_without_reason_does_not_suppress(self) -> None:
        text = '<span style="color: #C48A3F">logo</span> // brand-allow:\n'
        self.assertTrue(self.scan("tijdelijke.html", text))

    def test_root_selector_is_not_hex(self) -> None:
        self.assertEqual(self.scan("root.css", "html, body, #root { height: 100%; }\n"), [])

    def test_rgba_is_outside_the_gate(self) -> None:
        self.assertEqual(self.scan("tijdelijke.html", '<circle stroke="rgba(255,255,255,0.18)"/>\n'), [])
        self.assertEqual(self.scan("tijdelijke.html", '<circle stroke="rgb(196, 138, 63)"/>\n'), [])


class RatchetTests(unittest.TestCase):
    def make(self, value: str, line: int = 1) -> lint.Finding:
        return lint.Finding("a.html", line, "hex", value, "msg")

    def test_same_count_passes_and_extra_fails_and_removal_passes(self) -> None:
        base = [self.make("#FFFFFF", 1), self.make("#FFFFFF", 2)]
        self.assertEqual(lint.excess(base, base), [])
        extra = base + [self.make("#FFFFFF", 3)]
        self.assertEqual(len(lint.excess(extra, base)), 1)
        self.assertEqual(lint.excess(base[:1], base), [])
        added = base + [self.make("#112233", 4)]
        over = lint.excess(added, base)
        self.assertEqual(over[0][0].value, "#112233")

    def test_repo_matches_baseline(self) -> None:
        self.assertEqual(pin.verify(), [])
        self.assertEqual(lint.check(), [])


class PolicyTests(unittest.TestCase):
    BODY = """## Acceptatiecriteria

- De pin klopt. index.html blijft ongewijzigd.

## Scherm

geen scherm

## Verify

`python3 scripts/brand/lint.py` — pin ok
"""

    def test_full_body_passes(self) -> None:
        self.assertEqual(pr_policy.check_body(self.BODY, []), [])

    def test_missing_section_fails(self) -> None:
        errors = pr_policy.check_body("## Acceptatiecriteria\n\niets\n")
        self.assertTrue(any("Scherm" in err for err in errors))
        self.assertTrue(any("Verify" in err for err in errors))

    def test_comment_only_section_is_empty(self) -> None:
        body = self.BODY.replace("geen scherm", "<!-- nog invullen -->")
        errors = pr_policy.check_body(body)
        self.assertTrue(any("Scherm" in err and "leeg" in err for err in errors))

    def test_feature_pr_cannot_touch_tokens(self) -> None:
        errors = pr_policy.check_sync(["docs/brand/tokens.json"], "fix formulier", [])
        self.assertTrue(errors)

    def test_tokens_sync_title_passes(self) -> None:
        self.assertEqual(
            pr_policy.check_sync(
                ["docs/brand/tokens.json", "scripts/brand/pin.py"],
                "tokens-sync: merkkopie",
                [],
            ),
            [],
        )

    def test_label_passes(self) -> None:
        self.assertEqual(
            pr_policy.check_sync(["docs/brand/DESIGN.md"], "merk", ["tokens-sync"]),
            [],
        )

    def test_tokens_sync_is_case_sensitive(self) -> None:
        self.assertTrue(pr_policy.check_sync(["docs/brand/tokens.json"], "Tokens-sync: merkkopie", []))
        self.assertTrue(pr_policy.check_sync(["docs/brand/tokens.json"], "merk", ["Tokens-sync"]))

    def test_unrelated_path_passes(self) -> None:
        self.assertEqual(pr_policy.check_sync(["index.html"], "fix", []), [])

    def _filled(self, scherm: str, verify: str, accept: str = "- De pin klopt.") -> str:
        return (
            "## Acceptatiecriteria\n\n"
            f"{accept}\n\n"
            "## Scherm\n\n"
            f"{scherm}\n\n"
            "## Verify\n\n"
            f"{verify}\n"
        )

    def test_acceptatie_placeholder_stays_allowed(self) -> None:
        body = self._filled(
            "geen scherm",
            "`python3 scripts/brand/lint.py` — pin ok",
            "TODO placeholder nog invullen",
        )
        self.assertEqual(pr_policy.check_body(body, []), [])

    def test_screen_path_without_change_fails(self) -> None:
        for scherm in ("index.html", "css/site.css"):
            errors = pr_policy.check_body(
                self._filled(scherm, "`python3 scripts/brand/lint.py` — pin ok"),
                [],
            )
            self.assertTrue(errors, scherm)
            self.assertTrue(any("geen scherm" in err for err in errors), errors)

    def test_explicit_no_screen_passes_when_diff_has_none(self) -> None:
        body = self._filled("geen scherm", "Het verify-commando is niet gedraaid.")
        self.assertEqual(pr_policy.check_body(body, []), [])

    def test_geen_scherm_plus_named_path_fails_when_diff_has_none(self) -> None:
        body = self._filled(
            "geen scherm, ook niet index.html",
            "niet gedraaid.",
        )
        errors = pr_policy.check_body(body, [])
        self.assertTrue(any("index.html" in err for err in errors), errors)

    def test_screen_mention_outside_scherm_section_is_ignored(self) -> None:
        body = self._filled(
            "geen scherm",
            "niet gedraaid.",
            "- index.html (de publieke site) is ongewijzigd.",
        )
        self.assertEqual(pr_policy.check_body(body, []), [])

    def test_niet_uitgevoerd_without_question_passes(self) -> None:
        body = self._filled("geen scherm geraakt", "De suite is niet uitgevoerd.")
        self.assertEqual(pr_policy.check_body(body, []), [])

    def test_changed_screen_must_be_named(self) -> None:
        paths = ["index.html", "docs/brand/tokens.json"]
        named = self._filled("index.html", "`python3 scripts/brand/lint.py` — exit 0")
        self.assertEqual(pr_policy.check_body(named, paths), [])
        missing = self._filled("geen scherm", "`python3 scripts/brand/lint.py` — exit 0")
        errors = pr_policy.check_body(missing, paths)
        self.assertTrue(any("index.html" in err or "geen scherm is geraakt" in err for err in errors))

    def test_other_screen_than_diff_fails(self) -> None:
        body = self._filled("contact.html", "niet gedraaid.")
        errors = pr_policy.check_body(body, ["index.html"])
        self.assertTrue(any("ander scherm" in err or "niet:" in err for err in errors))

    def test_non_screens_do_not_count(self) -> None:
        self.assertFalse(pr_policy.is_screen_path("scripts/brand/lint.py"))
        self.assertFalse(pr_policy.is_screen_path("docs/brand/DESIGN.md"))
        self.assertFalse(pr_policy.is_screen_path("docs/brand/tokens.json"))
        self.assertFalse(pr_policy.is_screen_path("docs/extra.html"))
        self.assertFalse(pr_policy.is_screen_path(".github/workflows/brand.yml"))
        self.assertFalse(pr_policy.is_screen_path(".cursor/rules/ui-tokens.mdc"))
        self.assertFalse(pr_policy.is_screen_path("AGENTS.md"))
        self.assertFalse(pr_policy.is_screen_path("js/app.test.js"))
        self.assertFalse(pr_policy.is_screen_path("tests/page.html"))
        self.assertTrue(pr_policy.is_screen_path("index.html"))
        self.assertTrue(pr_policy.is_screen_path("css/site.css"))
        self.assertTrue(pr_policy.is_screen_path("css/site.scss"))
        self.assertTrue(pr_policy.is_screen_path("js/app.js"))
        self.assertTrue(pr_policy.is_screen_path("src/App.jsx"))
        self.assertTrue(pr_policy.is_screen_path("src/App.tsx"))
        body = self._filled("geen scherm", "niet uitgevoerd.")
        paths = [
            "scripts/brand/lint.py",
            "docs/brand/DESIGN.md",
            "docs/brand/tokens.json",
            ".github/workflows/brand.yml",
            ".cursor/rules/ui-tokens.mdc",
            "AGENTS.md",
            "tests/page.html",
            "js/app.test.js",
        ]
        self.assertEqual(pr_policy.check_body(body, paths), [])

    def test_verify_command_without_result_fails(self) -> None:
        body = self._filled("geen scherm", "python3 scripts/brand/lint.py")
        errors = pr_policy.check_body(body, [])
        self.assertTrue(any("zonder resultaat" in err for err in errors))

    def test_bare_command_plus_niet_gedraaid_fails(self) -> None:
        body = self._filled(
            "geen scherm",
            "`python3 scripts/brand/lint.py`\nDit is niet gedraaid.",
        )
        errors = pr_policy.check_body(body, [])
        self.assertTrue(any("zonder resultaat" in err for err in errors), errors)

    def test_command_with_result_and_niet_gedraaid_passes(self) -> None:
        body = self._filled(
            "geen scherm",
            "`python3 scripts/brand/lint.py` — pin ok\nDeploy is niet gedraaid.",
        )
        self.assertEqual(pr_policy.check_body(body, []), [])

    def test_verify_question_fails_and_statement_passes(self) -> None:
        question = self._filled("geen scherm", "Niet gedraaid?")
        self.assertTrue(pr_policy.check_body(question, []))
        statement = self._filled("geen scherm", "Niet gedraaid.")
        self.assertEqual(pr_policy.check_body(statement, []), [])

    def test_verify_html_comment_only_is_empty(self) -> None:
        body = self._filled(
            "geen scherm",
            "<!-- Het commando dat je draaide, of: niet gedraaid, en waarom. -->",
        )
        errors = pr_policy.check_body(body, [])
        self.assertTrue(any("Verify" in err and "leeg" in err for err in errors))

    def test_template_body_is_empty(self) -> None:
        from pathlib import Path

        template = Path(pr_policy.__file__).resolve().parents[2].joinpath(
            ".github", "PULL_REQUEST_TEMPLATE.md"
        ).read_text(encoding="utf-8")
        errors = pr_policy.check_body(template, [])
        self.assertTrue(any("Acceptatiecriteria" in err and "leeg" in err for err in errors))
        self.assertTrue(any("Scherm" in err and "leeg" in err for err in errors))
        self.assertTrue(any("Verify" in err and "leeg" in err for err in errors))

    def test_tokens_sync_body_with_brand_paths(self) -> None:
        paths = [
            "docs/brand/tokens.json",
            "docs/brand/TOKENS.sha256",
            "docs/brand/DESIGN.md",
            "scripts/brand/pin.py",
        ]
        self.assertEqual(pr_policy.check_body(self.BODY, paths), [])
        self.assertEqual(
            pr_policy.check_sync(paths, "tokens-sync: merkkopie en poorten op main", []),
            [],
        )
        self.assertTrue(pr_policy.check_sync(paths, "fix: formulier opslaan", []))
        self.assertEqual(pr_policy.check_sync(paths, "fix: formulier opslaan", ["tokens-sync"]), [])


if __name__ == "__main__":
    unittest.main()
