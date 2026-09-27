# Silkjær — en slægt fra kær, klit og hav

The family chronicle of the Silkjær family, published at <https://silkjaerkroniken.dk/>. The site is built by
`build/ny.py` from the manuscript in `build/kilde/kroniken.html`, the one-page edition the site began as.

```
index.html                  Danish cover and contents
kapitel/NN-…/index.html     one page per chapter; short chapters share a page (1+2, 3+4, 14+15+16, 21+22)
                            and the old address of the second one forwards to its place on the shared page
appendiks/x-…/index.html    one page per appendix (5)
print/index.html            the whole chronicle on one print-friendly page
en/…                        the same pages in English
assets/                     ny.css, ny.js, fonts (Bodoni Moda, Source Serif 4 — OFL), favicon, OG images,
                            data/ (sources and person cards for the pop-ups),
                            depth/ (depth maps for the living pictures), maps/ (the map of Denmark and the survey
                            sheets), thumbs/ (index pictures), hi/ (sharper copies, fetched only when the camera
                            goes close)
billeder/                   the pictures (display size); billeder/fuld/ the originals for the zoomed view;
                            billeder/1913/ the photographed pages of the 1913 court records, cropped to the case
sitemap.xml                 written by the build
build/                      everything needed to regenerate the pages (not published, see _config.yml)
  kilde/kroniken.html       the manuscript: the chronicle as one page, with support.js and silkjaer-map.js
  NYE-TEKSTER.md            every piece of new text the edition adds around the chronicle (for review)
```

The old one-page edition had an anchor per chapter. Those links still work: `/#kap5`, `/#kilder` and the rest lead on
from the cover to the chapter's own page.

## What is new

- **An identity from the survey sheets.** The Generalstab sheets of 1872/1878 give the edition its look: map lettering,
  cartouches, paper slips; Bodoni Moda for display and Source Serif 4 for reading. Every chapter has a colour world
  (paper, dune, sea, storm, night, archive).
- **One address per chapter**, in both languages, with its own title, description and share card. The language switch
  keeps the reader's place; page changes are a short curtain, and the sound carries on across them.
- **Scenes that move with the reading.** A picture or a map holds the screen while the paragraphs pass over it and the
  camera travels to what each paragraph is about (on a phone and an upright tablet the picture keeps the top of the
  screen and the text passes under it). Photographs are drawn in WebGL with a depth map, so near and far move apart.
  Among them: the cover (the survey sheet, the five *kær*, the name lifting out of the deed), chapter 1 (the deed),
  chapter 3 (a year line walking across four generations on the Klit), chapter 5 (the capsizing on the night sea),
  chapter 7 (the crew photo and the name list), chapter 10 (the lights along the coast, Harboøre 1893 to Ebenezer
  1910), chapters 11, 15 and 19 (the journeys drawn on the map), chapter 12 (the case in the court records),
  chapter 22 (the stone with the name).
- **Reading tools.** Source references open the source in a pop-up; person names open their card in a drawer; notes,
  "læs mere" and images work as before; a small instrument shows the year and place the text is at; the contents open
  over the page; the cover remembers where the reader left off; appendix D can be searched and appendix E shows each
  picture beside its entry.
- **Sound** (off until the reader turns it on) is generated with the Web Audio API — no audio files.
- **Print.** "Print" prints the chapter in view with every note open; the print page holds the whole chronicle.
- **Without JavaScript or with reduced motion** every page is complete: scenes are decoration on the chronicle's own
  markup, and all text is in the HTML.

## Building

Requirements: Python 3 with BeautifulSoup and Pillow (`pip install beautifulsoup4 pillow`). Node is used, when
present, to re-read the data tables from the manuscript whenever it is newer than the extracted copy.

```sh
cd build
python3 ny.py                                        # writes the site at the root of the repository
python3 ny.py --draft --out /tmp/preview             # a copy marked noindex, without sitemap
python3 ny.py --target artifact --out /tmp/ny_art    # a self-contained copy for previewing elsewhere
```

The pages are written indexable, with their addresses at the root, and `sitemap.xml` lists both languages for every
page (`robots.txt` points at it). The footer's »Senest revideret« is the date of the build; set `SILK_REVISED=YYYY-MM-DD`
to build with another date.

The build ends with a **content check**: the manuscript is rendered afresh, and every text block in it must be
found in the Danish pages. If a sentence is missing, the build stops. It also reports English segments that are not
yet translated.

### When the chronicle changes

Edit `build/kilde/kroniken.html` and rebuild. Every piece of text is a *segment* keyed by a hash of its Danish
wording, so a changed sentence shows in Danish on the English page until it is translated. The build lists what is
missing:

```sh
python3 ny.py                        # reports "english untranslated: N"
python3 tr.py show untranslated      # the Danish of those segments, in the translation format
# write the English into i18n/en/<anything>.txt: a line "@<id>" followed by the text, keeping the
# <tN>…</tN>, <nK/> and <br/> placeholders exactly as in the Danish
python3 tr.py compile                # checks the placeholders and writes the .json the build reads
python3 ny.py
```

The manuscript can be opened on its own: serve the repository (`python3 -m http.server 8765`) and open
<http://localhost:8765/build/kilde/kroniken.html>. `build/kilde/README.md` describes its picture tools.
