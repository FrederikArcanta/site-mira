# AGENTS.md — site-mira

Publieke site, statische HTML. Eigen silo. Alleen deze repo.

## Merk

Tokens: `docs/brand/tokens.json`. Pin: `docs/brand/TOKENS.sha256` en `EXPECTED_SHA` in `scripts/brand/pin.py`. Grenzen: `docs/brand/DESIGN.md` en `.cursor/rules/ui-tokens.mdc`.

De lint scant de publieke site: `index.html` en elk ander bestand met `.html`, `.css`, `.scss`, `.js`, `.tsx` of `.jsx`. Tests, `docs/`, `scripts/`, `.github/` en `.cursor/` tellen niet mee. Bestaande overtredingen staan in `docs/brand/baseline.txt`. Die nulmeting niet opruimen in een feature-PR.

Bekend gat: `rgba(...)` en `rgb(...)` vallen buiten de hex-poort. Een `#hex` valt erbinnen. De lint herkent Tailwind-arbitrary values in gescande tekst; deze repo heeft geen Tailwind-dependency.

Merkpoort: `python3 scripts/brand/lint.py`

Fixtures: `python3 -m unittest discover -s scripts/brand -p 'test_*.py' -v`

## Klaar als

- De PR heeft Acceptatiecriteria (niet leeg), Scherm en Verify.
- Verify: een zin met `niet gedraaid` of `niet uitgevoerd` zonder vraagteken, of een commando én een resultaatwoord. «Niet gedraaid?» faalt. «Niet gedraaid.» slaagt. Een commando zonder resultaatwoord faalt, ook als dezelfde sectie `niet gedraaid` zegt. Een commando mét resultaatwoord mag daarnaast zeggen dat iets anders niet gedraaid is.
- Bij een schermwijziging: dat scherm, niet een ander. Geen scherm geraakt: de tekst bevat `geen scherm`. `geen scherm` plus een genoemd schermpad faalt, ook als de diff geen scherm raakt. Alleen de sectie `## Scherm` telt.
- Scherm is `index.html` of een ander bestand van de publieke site met `.html`, `.css`, `.scss`, `.js`, `.tsx` of `.jsx`. Tests, docs, scripts, CI, rules en tokens zijn geen scherm.
- Geen nieuwe hex, geen font buiten de tokens, geen wissel naar Inter, geen oker als status.

Verificatie: `.cursor/skills/verificatie/SKILL.md`. Deze checkout eist geen screenshot.

## Don'ts

- `docs/brand/tokens.json` niet herschrijven. Alleen een tokens-sync (titel of label `tokens-sync`, hoofdlettergevoelig) samen met `TOKENS.sha256`, `DESIGN.md` en `EXPECTED_SHA`. `fonts.web.product_ui` blijft «Lato (buiten scope)».
- Geen typografiewissel in de publieke site. Lato niet nieuw gebruiken. Een wissel naar Inter faalt, ook via een token.
- `index.html` en de rest van de publieke site niet wijzigen om bestaande kleuren of fonts op te ruimen.
- Geen credential-waarden in prompt, PR, log of screenshot.
- Geen deploy, geen GitHub Pages-wijziging en geen live site vanuit een merk-PR.
