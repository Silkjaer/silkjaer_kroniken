repo: Silkjaer/silkjaer_kroniken
branch: main

## Last sync
date: 2026-07-30T00:00:00Z

### Updated in this project
- Repo'et var tomt ved tilknytningen — intet importeret, projektet er kilden.
- Krøniken publiceres som `index.html` til GitHub Pages. August 2026: `Silkjaer.dc.html` slettet — `index.html` er nu den eneste kildefil.
- `uploads/` bør ikke pushes: rå kildefiler og GEDCOM med persondata.
- Juli 2026: redaktionel omstrukturering — Del I—V, 1896—1930-forløbet løftet ud af efterskriften til kap. 9—13, »De to navne« flyttet til appendiks A, forskningsdagbogssproget fjernet.
- Juli 2026: folketællingerne 1880, 1890, 1901 og 1911 placerer husstanden på matr. 13b i Øe — appendiks A, kapitel 1 og kapitel 6 skrevet om efter det, med nyt forbehold nr. 21 og kilde S60.
- Juli 2026: designgennemgang — billedvægten skåret fra 73 MB til 12 MB, mobilklipning rettet, delmarkørerne bragt på sektionernes akse, kortet flyttet til venstre kolonne, kontrasten hævet til WCAG AA, metadata og favicon tilføjet.
- August 2026: genealogisk orienteringslag — hovedlinje-blok efter introen (forfatterens linje, klikbare navne), overgangssætninger ved gren-skift (kap. 9, 17, 19, 20), »Kapitler«-linje i alle 18 personkort, flere klikbare første omtaler i brødteksten. Vridsløselille føjet til kortet med stedskift midt i kapitel 12 (kapitelstriben slår nu op via nærmeste sektion). `parsed.json` slettet: ubrugt, forældet og indeholdt persondata på nulevende; nu gitignoret.
- August 2026: Gudum-grenen fortalt færdig efter modtaget slægtsoptegnelse (ny kilde S149, krydstjekket mod opdateret GEDCOM) — Espers ni børn på Nørre Tangshus i kap. 20, slægtstavlen og personkortet, heriblandt Knud Vognsgaard (omkom ved eksplosionen på Stålvalseværket 1959) og Otto (udvandret til Australien). Navnenøglen er nu »Syv Niels'er« — Espers søn Niels (f. 17.11.1914) er navnefælle til Jens Klaus' søn (f. 28.2.1914). Børnebørns-statistikken 53→58.

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

## Screen map
| Skærm | Filer |
|---|---|
| Familiekrønike (22 kapitler + appendiks A—E) | index.html |
| Kort i venstre kolonne | silkjaer-map.js |
| DC-runtime | support.js |
| Billeder | billeder/ (66 visningsfiler) · billeder/fuld/ (64 originaler) |
| Ikoner og deling | favicon.svg · favicon.ico · apple-touch-icon.png · og-billede.jpg |
