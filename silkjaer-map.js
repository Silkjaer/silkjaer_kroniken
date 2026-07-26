/* <silkjaer-map> — locator map for the Silkjær chronicle.
   Leaflet + OSM tiles are loaded by the host page (helmet). The element waits for window.L. */
(function () {
  const PLACES = {
    oversigt:      { c: [56.15, 8.55], z: 7,  navn: "Vestjylland",              note: "Slægtens landskab" },
    silkjaer:      { c: [56.2716, 8.1320], z: 12, navn: "Silkjær, Øhusevej",     note: "Gården, navnet kom fra" },
    husby:         { c: [56.2818, 8.17633], z: 11, navn: "Husby Kirke",          note: "Døbt, viet, begravet" },
    husbyklit:     { c: [56.2830, 8.1050], z: 11, navn: "Husby Klit",            note: "Havbjergene og stranden" },
    oekjaer:       { c: [56.2740, 8.1360], z: 12, navn: "Økjær",                 note: "Husmandsstedet" },
    tarp:          { c: [56.1620, 8.1950], z: 11, navn: "Tarp, Vedersø",         note: "Anne Marie Jansdatters hjem" },
    havet:         { c: [56.2400, 7.9600], z: 9, navn: "Ud for Husby",          note: "9. november 1878" },
    vedersoe:      { c: [56.1590, 8.0980], z: 10, navn: "Vedersø Redningsstation", note: "Mandskabet 1915" },
    landting:      { c: [56.5167, 8.7333], z: 9, navn: "Landting Mark",         note: "Ane Jensens fødested" },
    raekkermoelle: { c: [55.9539, 8.5322], z: 10, navn: "Rækker Mølle, Sædding", note: "Murermesterens by" },
    ikast:         { c: [56.1394, 9.1547], z: 9, navn: "Ikast-egnen",           note: "Sporet fortsætter" },
    esbjerg:       { c: [55.4640, 8.4400], z: 10, navn: "Havnegade, Esbjerg",    note: "Fiskeskipperens hjem" },
    nordsoen:      { c: [55.7000, 7.2000], z: 7,  navn: "Nordsøen",              note: "16. marts 1945" },
    holmsland:     { c: [56.0500, 8.1300], z: 9, navn: "Holmslands Klit",       note: "Tarbensen-grenen" },
    vejlby:        { c: [56.4550, 10.0700], z: 8, navn: "Vejlby ved Allingåbro", note: "Graveren og navnet mod øst" },
    aargab:        { c: [55.9700, 8.1250], z: 11, navn: "Årgab, Holmsland Klit", note: "Enken fra Årgab" },
    hartlepool:    { c: [54.6900, -1.2100], z: 7, navn: "Hartlepool, England",  note: "Grundstødningen 1948" }
  };

  class SilkjaerMap extends HTMLElement {
    connectedCallback() {
      if (this._built) return;
      this._built = true;
      this.style.display = "block";
      this.innerHTML =
        '<div data-map style="position:absolute;inset:0;background:#e6e1d5;"></div>' +
        '<div data-veil style="position:absolute;inset:0;pointer-events:none;' +
        'box-shadow:inset 0 0 40px rgba(20,24,28,.28);"></div>';
      this._el = this.querySelector("[data-map]");
      this._wait();
    }

    _wait(tries) {
      tries = tries || 0;
      if (window.L) return this._init();
      if (tries > 200) return;
      setTimeout(() => this._wait(tries + 1), 50);
    }

    _init() {
      const L = window.L;
      const map = L.map(this._el, {
        zoomControl: false, attributionControl: true, scrollWheelZoom: false,
        dragging: true, doubleClickZoom: true, keyboard: false
      }).setView(PLACES.oversigt.c, PLACES.oversigt.z);
      L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "© OpenStreetMap contributors", maxZoom: 18
      }).addTo(map);
      this._el.querySelector(".leaflet-tile-pane").style.filter =
        "grayscale(1) sepia(.38) brightness(1.04) contrast(.9)";
      const attr = this._el.querySelector(".leaflet-control-attribution");
      if (attr) {
        attr.style.font = "9px/1.4 'IBM Plex Mono',monospace";
        attr.style.background = "rgba(242,239,232,.75)";
      }
      this._map = map;
      this._markers = {};
      Object.keys(PLACES).forEach((k) => {
        const p = PLACES[k];
        const m = L.circleMarker(p.c, {
          radius: 4, color: "#2f5d6e", weight: 1.5, fillColor: "#f2efe8", fillOpacity: 1, opacity: .55
        }).addTo(map);
        m.bindTooltip(p.navn, { direction: "top", offset: [0, -6] });
        this._markers[k] = m;
      });
      this._ready = true;
      if (this._pending) this.setPlace(this._pending);
    }

    setPlace(key) {
      if (!PLACES[key]) return;
      if (!this._ready) { this._pending = key; return; }
      if (this._current === key) return;
      this._current = key;
      const p = PLACES[key];
      this._map.flyTo(p.c, p.z, { duration: 1.6 });
      Object.keys(this._markers).forEach((k) => {
        const on = k === key;
        this._markers[k].setStyle({
          radius: on ? 8 : 4,
          color: on ? "#8a5a3c" : "#2f5d6e",
          weight: on ? 3 : 1.5,
          opacity: on ? 1 : .45,
          fillColor: on ? "#8a5a3c" : "#f2efe8"
        });
        if (on) this._markers[k].bringToFront();
      });
      this.dispatchEvent(new CustomEvent("placechange", {
        bubbles: true, detail: { key: key, navn: p.navn, note: p.note }
      }));
    }
  }

  if (!customElements.get("silkjaer-map")) customElements.define("silkjaer-map", SilkjaerMap);
})();
