---
name: verificatie
description: Verifieer een site-mira-wijziging voor je klaar bent. Welk commando, welk scherm, geen secrets.
---

# Verificatie — site-mira

Gebruik dit voor je een wijziging in deze checkout afmeldt. De schrijvende agent is niet de reviewer.

## Starten

Merkpoort, vanuit de repo-root:

- `python3 scripts/brand/lint.py`
- `python3 -m unittest discover -s scripts/brand -p 'test_*.py' -v`

De merkpoort start geen deploy, geen GitHub Pages en geen live site. Er staat geen wachtwoord in deze checkout.

## Harde grens

- Geen credential-waarden in prompt, PR, log of screenshot. Noem hoogstens een pad dat al in de repo staat, nooit een waarde.
- Geen `.env` lezen.
- `docs/brand/tokens.json` niet herschrijven en niet dump-en. De pin staat in `scripts/brand/pin.py`.

## Wat je draait

- `python3 scripts/brand/lint.py`
- `python3 -m unittest discover -s scripts/brand -p 'test_*.py' -v`

Verify is of-of. Of een zin met «niet gedraaid» of «niet uitgevoerd», zonder vraagteken. Of een commando (backtick of python/pytest/npm/npx/node/bash) én een resultaatwoord (`ok`, `passed`, `exit`, `groen`). Een commando zonder resultaatwoord faalt, ook als dezelfde sectie «niet gedraaid» zegt. Een commando mét resultaatwoord mag daarnaast zeggen dat iets anders niet gedraaid is.

## Scherm

Alleen het gewijzigde scherm, niet een willekeurig ander. Schermbestanden zijn `index.html` en andere bestanden van de publieke site met `.html`, `.css`, `.scss`, `.js`, `.tsx` of `.jsx`. Tests, `docs/`, `scripts/`, `.github/`, `.cursor/` en tokens tellen niet mee. Geen scherm geraakt: schrijf onder Scherm dat er geen scherm is geraakt (de tekst bevat `geen scherm`). `geen scherm` plus een genoemd schermpad faalt, ook als de diff geen scherm raakt. Alleen de sectie `## Scherm` telt. Deze checkout eist geen screenshot.
