repo: Silkjaer/silkjaer_kroniken
branch: main

# Manuskriptet

`kroniken.html` er krøniken som én side — den udgave, sitet begyndte som. Sitet bygges af den (`python3 build/ny.py`),
men den vises ikke selv på sitet. `billeder` her er et link til repositoriets `billeder/`, så siden kan åbnes for sig
selv: kør `python3 -m http.server 8765` i repositoriet og åbn <http://localhost:8765/build/kilde/kroniken.html>.

Ret krønikens tekst her og byg bagefter; se `README.md` i roden.

## Billeder
- `billeder/fuld/` rummer originalerne. De vises kun i zoom.
- `billeder/` rummer visningsfilerne: maks. 1800 px (JPG, kvalitet 82) eller 1600 px (PNG via pngquant + oxipng).
- Zoom henter originalen for de billeder, der har `data-fuld`. Attributten sættes af `tools/add-img-dims.py`, som også skriver `width`/`height` på hvert `<img>`.
- Nye billeder: læg originalen i `billeder/fuld/`, lav visningsfilen i `billeder/` med samme navn, og kør `python3 build/kilde/tools/add-img-dims.py`.

## Værktøjer
| Kommando | Gør |
|---|---|
| `python3 build/kilde/tools/add-img-dims.py` | Skriver `width`/`height` og `data-fuld` på billedtags i `kroniken.html` |
| `python3 build/kilde/tools/kontrast.py` | Måler WCAG-kontrast for farverne i `kroniken.html`s inline styles |
| `node build/kilde/tools/tjek.js` | Kører manuskriptet igennem i otte bredder og melder overløb, kontrastfejl, små berøringsmål og konsolfejl |

`tools/tjek.js` kræver `npm install --no-save playwright && npx playwright install chromium` og en lokal server i repositoriets rod, fx `python3 -m http.server 8765`.
