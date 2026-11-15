# Merkgrenzen voor product-UI

Korte do’s en don’ts. Geen tweede merkboek. Tokens: `docs/brand/tokens.json` (alleen-lezen kopie, ongewijzigd gecommit uit het aangeleverde bestand).

## Do

- Kleur in product-UI via gedeelde tokens: `@arcanta/ui` of CSS-variabelen.
- Oker als merkkleur of accent, zonder statusbetekenis, mag, binnen de toegelaten accentvormen OK-1 tot OK-5 (`oker_rule.allowed` in tokens.json). Semantisch groen voor status mag.

## Don’t

- Oker nooit als statuskleur (success, OK; regel R-3), noch als hex, noch via de oker-token of een CSS-variabele.
- Geen hardcoded hex in product-UI.
- `docs/brand/tokens.json` wijzigt alleen in een benoemde tokens-sync PR (titel of label `tokens-sync`). Niet herschrijven. Proces-eigenaars: Designer en Product Lead. GitHub dwingt op dat pad `@FrederikArcanta` af (geen usernames voor Designer of Product Lead op dit account).

## Typografie (bindend, tussentijd)

Bindende tussenregel, tot UI/UX en Designer de Inter/Lato-spanning sluiten: web-body is Inter; Lato niet gebruiken; typografie in de product-UI niet wijzigen. Een wissel naar Inter in de product-UI is daarmee ook een fail.

Een typografiewijziging in de product-UI die een bekende token gebruikt (bijvoorbeeld een wissel naar Inter) faalt ook, tot UI/UX en Designer de spanning sluiten. Agents kiezen in de tussentijd geen eigen lettertype.

## Pin van tokens.json

sha256: `82cfa9698cba74e52198708ce87647bc44931b4c4060321f10b4807a2049a527`

Dezelfde pin staat in `docs/brand/TOKENS.sha256`.
