repo: Silkjaer/silkjaer_kroniken
branch: main

## Last sync
date: 2026-07-30T00:00:00Z

### Updated in this project
- Repo'et var tomt ved tilknytningen — intet importeret, projektet er kilden.
- Krøniken publiceres som `index.html` (kopi af `Silkjaer.dc.html`) til GitHub Pages.
- `uploads/` bør ikke pushes: rå kildefiler og GEDCOM med persondata.
- Juli 2026: redaktionel omstrukturering — Del I—V, 1896—1930-forløbet løftet ud af efterskriften til kap. 9—13, »De to navne« flyttet til appendiks A, forskningsdagbogssproget fjernet.
- Juli 2026: designgennemgang — billedvægten skåret fra 73 MB til 12 MB, mobilklipning rettet, delmarkørerne bragt på sektionernes akse, kortet flyttet til venstre kolonne, kontrasten hævet til WCAG AA, metadata og favicon tilføjet.

## Billeder
- `billeder/fuld/` rummer originalerne. De vises kun i zoom.
- `billeder/` rummer visningsfilerne: maks. 1800 px (JPG, kvalitet 82) eller 1600 px (PNG via pngquant + oxipng).
- Zoom henter originalen for de billeder, der har `data-fuld`. Attributten sættes af `tools/add-img-dims.py`, som også skriver `width`/`height` på hvert `<img>`.
- Nye billeder: læg originalen i `billeder/fuld/`, lav visningsfilen i `billeder/` med samme navn, og kør `python3 tools/add-img-dims.py`.

## Værktøjer
| Kommando | Gør |
|---|---|
| `python3 tools/add-img-dims.py` | Skriver `width`/`height` og `data-fuld` på billedtags i `Silkjaer.dc.html` |
| `node tools/tjek.js` | Kører siden igennem i otte bredder og melder overløb, kontrastfejl, små berøringsmål og konsolfejl |
| `cp Silkjaer.dc.html index.html` | Bygger den publicerede kopi |

`tools/tjek.js` kræver `npm install --no-save playwright && npx playwright install chromium` og en lokal server, fx `python3 -m http.server 8765`.

## Screen map
| Skærm | Filer |
|---|---|
| Familiekrønike (22 kapitler + appendiks A—E) | Silkjaer.dc.html · index.html (genereret kopi) |
| Kort i venstre kolonne | silkjaer-map.js |
| DC-runtime | support.js |
| Billeder | billeder/ (66 visningsfiler) · billeder/fuld/ (64 originaler) |
| Ikoner og deling | favicon.svg · favicon.ico · apple-touch-icon.png · og-billede.jpg |
