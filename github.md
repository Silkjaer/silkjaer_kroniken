repo: Silkjaer/silkjaer_kroniken
branch: main

## Revisionsdato
Footeren har en `data-revision`-linje (»Senest revideret …«). Opdater datoen, hver gang der publiceres indholdsændringer.

## Billeder
- `billeder/fuld/` rummer originalerne. De vises kun i zoom.
- `billeder/` rummer visningsfilerne: maks. 1800 px (JPG, kvalitet 82) eller 1600 px (PNG via pngquant + oxipng).
- Zoom henter originalen for de billeder, der har `data-fuld`. Attributten sættes af `tools/add-img-dims.py`, som også skriver `width`/`height` på hvert `<img>`.
- Nye billeder: læg originalen i `billeder/fuld/`, lav visningsfilen i `billeder/` med samme navn, og kør `python3 tools/add-img-dims.py`.

## Værktøjer
| Kommando | Gør |
|---|---|
| `python3 tools/add-img-dims.py` | Skriver `width`/`height` og `data-fuld` på billedtags i `index.html` |
| `node tools/tjek.js` | Kører siden igennem i otte bredder og melder overløb, kontrastfejl, små berøringsmål og konsolfejl |

`tools/tjek.js` kræver `npm install --no-save playwright && npx playwright install chromium` og en lokal server, fx `python3 -m http.server 8765`.
