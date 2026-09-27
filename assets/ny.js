/* Silkjær — ny udgave. The reading engine: a generated sound score (Web Audio, no files), page-to-page navigation that
   keeps the sound playing, the timeline rail, contents, person cards, source popovers, notes, lightbox, print, reveals
   and the chapter scenes. No libraries. Everything here is an enhancement: without it every page is complete. */
(() => {
  'use strict';
  const d = document, root = d.documentElement;
  let body = d.body;
  const $ = (s, r = d) => r.querySelector(s);
  const $$ = (s, r = d) => Array.from(r.querySelectorAll(s));
  const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  // phones, and tablets held upright: pictures keep the top of the screen and the text passes under them
  const SPLITQ = 'screen and (max-width: 719.98px), screen and (max-width: 1100px) and (orientation: portrait)';
  const splitNow = () => { try { return matchMedia(SPLITQ).matches; } catch (e) { return innerWidth < 720; } };
  const lerp = (a, b, t) => a + (b - a) * t;
  const ease = (t) => (t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
  const readJSON = (sel) => { try { return JSON.parse(($(sel) || {}).textContent || '{}'); } catch (e) { return {}; } };
  const SCRIPT = d.currentScript;
  const ASSETS = SCRIPT && SCRIPT.src ? new URL('.', SCRIPT.src).href : new URL('assets/', location.href).href;
  const EDITION = new URL('..', ASSETS).href;
  let LANG = root.lang === 'en' ? 'en' : 'da';
  let UI = readJSON('#silk-ui');
  const RM = root.classList.contains('rm');
  let BOOK = body.classList.contains('bookpage');
  const FRAMED = (() => { try { return window.self !== window.top; } catch (e) { return true; } })();
  const store = {
    get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* storage unavailable */ } },
    del(k) { try { localStorage.removeItem(k); } catch (e) { /* storage unavailable */ } },
  };
  root.classList.add('ny');
  /* =====================================================================================
     SOUND — wind, surf, rain, thunder, organ, birds, foghorn, archive room tone with a clock and a pen,
     and small paper, stamp, seal and telegraph sounds. Off until the reader turns it on.
     ===================================================================================== */
  const Sound = (() => {
    let ctx = null, master, bus, on = false, hushed = false, amb = body.dataset.amb || 'room';
    const beds = {};
    let buf = {};
    const BED = { wind: .55, surf: .7, rain: .5, drone: .22, deep: .5, birds: .35, room: .32 };
    const AMB = {
      shore: { wind: .45, surf: .6 }, marsh: { wind: .55, birds: .4 }, dune: { wind: .75, surf: .35 },
      storm: { wind: 1, surf: .9, rain: .85, thunder: 1 }, sea: { surf: .65, wind: .35, deep: .25 },
      surf: { surf: .75, wind: .35 }, hymn: { drone: .8, wind: .15 }, harbour: { surf: .3, wind: .25, deep: .45 },
      inland: { wind: .35, birds: .55 }, fog: { surf: .4, deep: .6, horn: 1 }, morning: { wind: .3, birds: .6, drone: .35 },
      archive: { room: .75, clock: 1, pen: 1 }, room: { room: .45 }, silence: {},
    };
    function noise(type) {
      const len = ctx.sampleRate * 5, b = ctx.createBuffer(2, len, ctx.sampleRate);
      for (let c = 0; c < 2; c++) {
        const data = b.getChannelData(c);
        let last = 0, b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0, b6 = 0;
        for (let i = 0; i < len; i++) {
          const w = Math.random() * 2 - 1;
          if (type === 'white') data[i] = w * .5;
          else if (type === 'pink') {
            b0 = .99886 * b0 + w * .0555179; b1 = .99332 * b1 + w * .0750759; b2 = .969 * b2 + w * .153852;
            b3 = .8665 * b3 + w * .3104856; b4 = .55 * b4 + w * .5329522; b5 = -.7616 * b5 - w * .016898;
            data[i] = (b0 + b1 + b2 + b3 + b4 + b5 + b6 + w * .5362) * .11; b6 = w * .115926;
          } else { last = (last + .02 * w) / 1.02; data[i] = last * 3.5; }
        }
      }
      return b;
    }
    const loop = (b) => { const s = ctx.createBufferSource(); s.buffer = b; s.loop = true; s.start(0, Math.random() * 4); return s; };
    const gain = (v = 0) => { const g = ctx.createGain(); g.gain.value = v; return g; };
    const filt = (type, f, q = .7) => { const n = ctx.createBiquadFilter(); n.type = type; n.frequency.value = f; n.Q.value = q; return n; };
    const lfo = (freq, depth, target) => { const o = ctx.createOscillator(); o.frequency.value = freq; const g = gain(depth); o.connect(g); g.connect(target); o.start(); return o; };

    function build() {
      buf = { white: noise('white'), pink: noise('pink'), brown: noise('brown') };
      master = gain(0);
      const comp = ctx.createDynamicsCompressor(); comp.threshold.value = -18; comp.ratio.value = 3;
      master.connect(comp); comp.connect(ctx.destination);
      bus = gain(hushed ? 0 : 1); bus.connect(master);
      const bed = (name) => { const g = gain(0); g.connect(bus); beds[name] = g; return g; };
      { const out = bed('wind'); const s = loop(buf.pink); const bp = filt('bandpass', 520, .8); const g = gain(.6);
        s.connect(bp); bp.connect(g); g.connect(out); lfo(.07, 260, bp.frequency); lfo(.13, .32, g.gain); lfo(.031, 120, bp.frequency); }
      { const out = bed('surf'); const s = loop(buf.brown); const lp = filt('lowpass', 750); const sw = gain(.2);
        s.connect(lp); lp.connect(sw); sw.connect(out); beds.swell = sw;
        const f = loop(buf.white); const hp = filt('highpass', 2600); const fg = gain(0); f.connect(hp); hp.connect(fg); fg.connect(out); beds.foam = fg; }
      { const out = bed('rain'); const s = loop(buf.white); const bp = filt('bandpass', 3600, .45); const g = gain(.5); s.connect(bp); bp.connect(g); g.connect(out);
        const s2 = loop(buf.pink); const lp = filt('lowpass', 900); const g2 = gain(.45); s2.connect(lp); lp.connect(g2); g2.connect(out); }
      { const out = bed('drone'); const lp = filt('lowpass', 1300); lp.connect(out); const trem = gain(.85); trem.connect(lp); lfo(.18, .12, trem.gain);
        [146.83, 220, 293.66, 369.99, 440].forEach((f, i) => { const o = ctx.createOscillator(); o.type = i % 2 ? 'triangle' : 'sine'; o.frequency.value = f; o.detune.value = (Math.random() - .5) * 6; const g = gain([.3, .22, .2, .12, .08][i]); o.connect(g); g.connect(trem); o.start(); }); }
      { const out = bed('deep'); const s = loop(buf.brown); const lp = filt('lowpass', 170); const g = gain(.9); s.connect(lp); lp.connect(g); g.connect(out);
        const o = ctx.createOscillator(); o.frequency.value = 52; const og = gain(.05); o.connect(og); og.connect(out); o.start(); lfo(.4, .02, og.gain); }
      // room tone: a large quiet room — low air, a faint hum of the building
      { const out = bed('room'); const s = loop(buf.pink); const lp = filt('lowpass', 340); const g = gain(.55); s.connect(lp); lp.connect(g); g.connect(out);
        const o = ctx.createOscillator(); o.frequency.value = 100; const og = gain(.012); o.connect(og); og.connect(out); o.start(); lfo(.05, .006, og.gain); }
      bed('birds');
      setInterval(schedule, 150);
      setAmb(amb, true);
    }

    let nSwell = 0, nThunder = 0, nBird = 0, nHorn = 0, nClock = 0, nPen = 0, tick = 0;
    function schedule() {
      if (!ctx || !on) return;
      const t = ctx.currentTime, A = AMB[amb] || {};
      if (A.surf && t > nSwell) {
        const peak = .55 + Math.random() * .45;
        beds.swell.gain.setTargetAtTime(peak, t, .9); beds.swell.gain.setTargetAtTime(.18, t + 2.4, 1.6);
        beds.foam.gain.setTargetAtTime(.22 * peak, t + 1.9, .25); beds.foam.gain.setTargetAtTime(0, t + 2.6, 1.1);
        nSwell = t + 6 + Math.random() * 4;
      }
      if (A.thunder && t > nThunder) { thunder(.6 + Math.random() * .4); nThunder = t + 9 + Math.random() * 12; }
      if (A.birds && t > nBird) { chirp(A.birds); nBird = t + 1.8 + Math.random() * 5.5; }
      if (A.horn && t > nHorn) { horn(); nHorn = t + 24 + Math.random() * 14; }
      if (A.clock) {
        if (nClock < t) nClock = t + .1;
        while (nClock < t + .3) { clockAt(nClock, tick++ % 2 === 0); nClock += 1; }
      }
      if (A.pen && t > nPen) { if (nPen && !hushed) pen(.55); nPen = t + 11 + Math.random() * 17; }
    }
    function setAmb(name, instant) {
      if (name in AMB) amb = name;
      if (!ctx) return;
      const A = AMB[amb] || {}, t = ctx.currentTime;
      Object.keys(BED).forEach((b) => {
        const v = (A[b] || 0) * BED[b];
        if (instant) beds[b].gain.setValueAtTime(v, t); else beds[b].gain.setTargetAtTime(v, t, 1.4);
      });
      if (A.thunder) nThunder = t + 2.5;
    }
    function setHush(v) {
      v = !!v;
      if (v === hushed) return;
      hushed = v;
      if (ctx) bus.gain.setTargetAtTime(v ? 0 : 1, ctx.currentTime, v ? .7 : 1.6);
      d.dispatchEvent(new CustomEvent('silk:sound'));
    }

    /* one-shots */
    function env(g, t, a, peak, dec) { g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(peak, t + a); g.gain.setTargetAtTime(0, t + a, dec); }
    function shot(type, ftype, f, q, peak, a, dec, when = 0) {
      const t = ctx.currentTime + when; const s = ctx.createBufferSource(); s.buffer = buf[type];
      const fl = filt(ftype, f, q); const g = gain(0); s.connect(fl); fl.connect(g); g.connect(bus); env(g, t, a, peak, dec);
      s.start(t, Math.random() * 3); s.stop(t + a + dec * 7 + .05); return { fl, g, t };
    }
    function tone(f, type, peak, a, dec, detune = 0, when = 0) {
      const t = ctx.currentTime + when; const o = ctx.createOscillator(); o.type = type; o.frequency.value = f; o.detune.value = detune;
      const g = gain(0); o.connect(g); g.connect(bus); env(g, t, a, peak, dec); o.start(t); o.stop(t + a + dec * 7 + .05); return { o, g, t };
    }
    function clockAt(at, hi) {
      const w = Math.max(0, at - ctx.currentTime);
      tone(hi ? 2400 : 1750, 'sine', .012, .001, .01, 0, w);
      shot('white', 'bandpass', hi ? 5200 : 4200, 3, .018, .001, .006, w);
    }
    function thunder(k = 1) {
      const t = ctx.currentTime, d0 = .25 + Math.random() * .9;
      const s = ctx.createBufferSource(); s.buffer = buf.brown; const lp = filt('lowpass', 150); const g = gain(0);
      s.connect(lp); lp.connect(g); g.connect(bus);
      g.gain.setValueAtTime(0, t + d0); g.gain.linearRampToValueAtTime(1.1 * k, t + d0 + .12); g.gain.setTargetAtTime(.35 * k, t + d0 + .5, .6); g.gain.setTargetAtTime(0, t + d0 + 1.4, 1.3);
      lp.frequency.setValueAtTime(420, t + d0); lp.frequency.setTargetAtTime(110, t + d0 + .2, .8);
      s.start(t, Math.random() * 3); s.stop(t + d0 + 8);
    }
    function chirp(k) {
      const t = ctx.currentTime, n = 2 + (Math.random() * 5 | 0), base = 2600 + Math.random() * 1800;
      const pan = ctx.createStereoPanner ? ctx.createStereoPanner() : null; const out = gain(.05 * k);
      if (pan) { pan.pan.value = Math.random() * 1.6 - .8; out.connect(pan); pan.connect(beds.birds); } else out.connect(beds.birds);
      beds.birds.gain.setTargetAtTime(BED.birds * ((AMB[amb] || {}).birds || 0), t, .3);
      for (let i = 0; i < n; i++) {
        const o = ctx.createOscillator(); o.type = 'sine'; const g = gain(0); o.connect(g); g.connect(out);
        const st = t + i * (.09 + Math.random() * .07);
        o.frequency.setValueAtTime(base, st); o.frequency.exponentialRampToValueAtTime(base * (1.25 + Math.random() * .4), st + .06);
        g.gain.setValueAtTime(0, st); g.gain.linearRampToValueAtTime(1, st + .01); g.gain.exponentialRampToValueAtTime(.001, st + .08);
        o.start(st); o.stop(st + .1);
      }
    }
    function horn() {
      const t = ctx.currentTime; const lp = filt('lowpass', 380); const g = gain(0); lp.connect(g); g.connect(bus);
      [98, 98.6, 196.4].forEach((f, i) => { const o = ctx.createOscillator(); o.type = 'sawtooth'; o.frequency.value = f; const og = gain(i === 2 ? .15 : .5); o.connect(og); og.connect(lp); o.start(t); o.stop(t + 6); });
      g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(.08, t + .6); g.gain.setValueAtTime(.08, t + 2.6); g.gain.linearRampToValueAtTime(0, t + 3.8);
    }
    function pen(k = 1) {
      let when = 0; const n = 2 + (Math.random() * 3 | 0);
      for (let i = 0; i < n; i++) {
        const t0 = ctx.currentTime + when, dur = .09 + Math.random() * .16;
        const s = ctx.createBufferSource(); s.buffer = buf.white; const bp = filt('bandpass', 3600 + Math.random() * 1800, 2.4); const g = gain(0);
        s.connect(bp); bp.connect(g); g.connect(bus);
        g.gain.setValueAtTime(0, t0); g.gain.linearRampToValueAtTime(.045 * k, t0 + .02);
        g.gain.linearRampToValueAtTime(.045 * k * (.5 + Math.random() * .5), t0 + dur * .6); g.gain.linearRampToValueAtTime(0, t0 + dur);
        bp.frequency.setValueAtTime(bp.frequency.value, t0); bp.frequency.linearRampToValueAtTime(bp.frequency.value * (.8 + Math.random() * .4), t0 + dur);
        s.start(t0, Math.random() * 3); s.stop(t0 + dur + .05);
        when += dur + .05 + Math.random() * .14;
      }
    }
    function sounderClick(when, k) {
      tone(1900, 'square', .012 * k, .001, .005, 0, when);
      tone(420, 'sine', .07 * k, .001, .018, 0, when);
      shot('white', 'bandpass', 2400, 3, .07 * k, .001, .008, when);
    }
    const SFX = {
      tick() { tone(1850, 'sine', .07, .002, .03); shot('white', 'highpass', 5000, .7, .03, .001, .01); },
      tock() { tone(980, 'sine', .06, .002, .035); },
      odo() { tone(3100, 'square', .006, .001, .008); },
      page() { const n = shot('white', 'bandpass', 1400, 1.1, .12, .02, .09); n.fl.frequency.setTargetAtTime(3600, n.t, .12); },
      act() {
        const t = ctx.currentTime; const o = ctx.createOscillator(); o.type = 'sine'; o.frequency.setValueAtTime(62, t); o.frequency.exponentialRampToValueAtTime(41, t + 2.2);
        const g = gain(0); o.connect(g); g.connect(bus); env(g, t, .5, .3, .9); o.start(t); o.stop(t + 6);
        const n = shot('pink', 'lowpass', 260, .7, .2, .9, .9); n.fl.frequency.setTargetAtTime(900, n.t, 1);
      },
      chime() { [587.33, 880, 1174.66].forEach((f, i) => tone(f, 'sine', .05, .004, 1.4, 0, i * .09)); },
      bell() {
        const f0 = 196; [[.5, .32, 9], [1, .45, 7], [1.19, .26, 5.5], [1.5, .2, 4.5], [2, .24, 4], [2.51, .1, 3], [2.66, .08, 2.5], [3.01, .07, 2], [4.17, .04, 1.2]]
          .forEach(([r, a, dec]) => tone(f0 * r, 'sine', a * .5, .004, dec / 3, (Math.random() - .5) * 8));
        shot('white', 'bandpass', 2400, 2, .06, .002, .04);
      },
      thunder: () => thunder(1),
      // a rubber stamp on paper: a short low thump and a dry slap
      stamp() {
        const t = ctx.currentTime; const o = ctx.createOscillator(); o.frequency.setValueAtTime(150, t); o.frequency.exponentialRampToValueAtTime(46, t + .12);
        const g = gain(0); o.connect(g); g.connect(bus); env(g, t, .003, .42, .05); o.start(t); o.stop(t + .5);
        shot('pink', 'lowpass', 1300, .7, .32, .002, .045); shot('white', 'bandpass', 3200, 1.3, .06, .001, .015, .012);
      },
      // warm sealing wax pressed down: a soft thud, then the crackle of cooling wax
      seal() {
        shot('brown', 'lowpass', 280, .7, .55, .03, .16);
        for (let i = 0; i < 9; i++) shot('white', 'bandpass', 2400 + Math.random() * 3600, 3.5, .03 + Math.random() * .05, .001, .006, .2 + Math.random() * 1.1);
      },
      // a telegraph sounder: each mark is a down-click and a softer up-click
      telegraph() {
        const U = .07; let when = 0;
        for (const ch of '-.. . -. ... -') { if (ch === ' ') { when += U * 2.5; continue; } const len = ch === '-' ? U * 3 : U; sounderClick(when, 1); sounderClick(when + len, .5); when += len + U; }
      },
      pen: () => pen(1),
      breaker() {
        const n = shot('brown', 'lowpass', 300, .7, .9, .35, .9); n.fl.frequency.setTargetAtTime(1400, n.t, .25); n.fl.frequency.setTargetAtTime(380, n.t + .5, .6);
        shot('white', 'highpass', 2200, .7, .16, .4, .5, .15);
      },
      whoosh() { const n = shot('white', 'bandpass', 320, 1.4, .26, .5, .35); n.fl.frequency.setTargetAtTime(2800, n.t, .35); },
      toll() { const f0 = 146.8; [[.5, .3, 10], [1, .42, 8], [1.19, .22, 6], [1.5, .16, 5], [2, .2, 4], [2.51, .08, 3]].forEach(([r, a, dec]) => tone(f0 * r, 'sine', a * .45, .004, dec / 3, (Math.random() - .5) * 6)); },
      strip() { shot('white', 'bandpass', 2200, 4, .05, .001, .02); tone(420, 'square', .012, .001, .015); },
    };
    let scratchG = null;
    function scratch(v) {
      if (!ctx || !on || hushed) return;
      if (!scratchG) { const s = loop(buf.white); const bp = filt('bandpass', 4200, 1.6); scratchG = gain(0); s.connect(bp); bp.connect(scratchG); scratchG.connect(bus); }
      scratchG.gain.setTargetAtTime(clamp(v) * .07, ctx.currentTime, .05);
    }
    function setOn(v) {
      if (v && !ctx) {
        const AC = window.AudioContext || window.webkitAudioContext;
        if (!AC) return false;
        ctx = new AC(); build();
      }
      on = v;
      if (!ctx) return on;
      if (on) ctx.resume();
      master.gain.setTargetAtTime(on ? .85 : 0, ctx.currentTime, .4);
      if (!on) setTimeout(() => { if (!on && ctx) ctx.suspend(); }, 1600);
      d.dispatchEvent(new CustomEvent('silk:sound'));
      return on;
    }
    d.addEventListener('visibilitychange', () => { if (!ctx) return; if (d.hidden) ctx.suspend(); else if (on) ctx.resume(); });
    return {
      toggle() { return setOn(!on); },
      start() { return setOn(true); },
      get on() { return on; },
      get hushed() { return hushed; },
      amb(name) { if (name && name !== amb) setAmb(name); },
      hush: setHush,
      sfx(name) { if (!ctx || !on || hushed || !SFX[name]) return; try { SFX[name](); } catch (e) { /* ignore */ } },
      scratch,
    };
  })();

  function paintSound() {
    $$('[data-act="sound"]').forEach((b) => {
      b.setAttribute('aria-pressed', Sound.on ? 'true' : 'false');
      b.classList.toggle('hush', Sound.on && Sound.hushed);
      b.title = Sound.on ? (Sound.hushed ? UI.hush_title : UI.sound_on) : UI.sound_off;
    });
  }
  d.addEventListener('silk:sound', paintSound);

  /* =====================================================================================
     PAGE — everything that belongs to one page is mounted here and torn down before the next
     ===================================================================================== */
  let chap = null;           // the chapters on this page (one, or several short ones sharing the page)
  let arts = [], curArt = null;
  let live = [];             // scenes updated from the scroll loop: { el, u }
  let cleanups = [];         // observers and listeners to drop when the page is left
  const onPage = (fn) => cleanups.push(fn);
  const observe = (cb, opts) => { const io = new IntersectionObserver(cb, opts); onPage(() => io.disconnect()); return io; };
  const listen = (el, ev, fn, o) => { el.addEventListener(ev, fn, o); onPage(() => el.removeEventListener(ev, fn, o)); };
  const later = (fn, ms) => { const t = setTimeout(fn, ms); onPage(() => clearTimeout(t)); return t; };


  /* KINETIC HEADS — a chapter's title is set letter by letter as the page opens (and as a second chapter on the same
     page comes up); the number is engraved in from its foot, the neat line drawn across. Without script it simply stands. */
  /* KINETIC TYPE — every opening is printed as it comes into view. The numeral is a type sort: it turns from its
     mirrored face to the reader and lands. The title stands first as a blind impression, pressed into the paper
     without ink; then a roller passes over it from left to right and leaves it inked. */
  function kinetic() {
    const heads = $$('main .ch-head, main .part-in, main .cartouche');
    if (!heads.length) return;
    heads.forEach((hd) => {
      const t = $('.ch-title, .part-t, .cover-t', hd);
      if (t && !$('.ink-top', t)) {
        const inner = t.innerHTML;
        t.innerHTML = `<span class="ink-base">${inner}</span><span class="ink-top" aria-hidden="true">${inner}</span><span class="ink-roll" aria-hidden="true"></span>`;
      }
    });
    if (RM || BOOK) { heads.forEach((hd) => hd.classList.add('kin', 'set')); return; }
    heads.forEach((hd) => hd.classList.add('kin'));
    const io = observe((es) => es.forEach((e) => {
      if (!e.isIntersecting) return;
      const hd = e.target; io.unobserve(hd);
      hd.classList.add('set');
      later(() => Sound.sfx('page'), 420);
    }), { rootMargin: '0px 0px -14% 0px' });
    heads.forEach((hd) => requestAnimationFrame(() => io.observe(hd)));
  }

  /* REVEALS — only what lies below the first screen waits for the reader; the first frame is complete */
  function reveals() {
    const items = $$('main [data-rv]');
    if (RM || BOOK || !('IntersectionObserver' in window)) { items.forEach((x) => x.classList.add('in')); return; }
    const io = observe((es) => es.forEach((e) => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }), { rootMargin: '0px 0px -8% 0px' });
    const vh = innerHeight;
    items.forEach((x) => { if (x.getBoundingClientRect().top < vh * .96) x.classList.add('in'); else io.observe(x); });
    root.classList.add('rv');
  }

  /* THE RAIL — the year being read, on the timeline 1680—2030 in the top bar */
  const A0 = 1680, A1 = 2030;
  const Rail = { frame() {} };
  function rail() {
    const r = $('.rail');
    Rail.frame = () => {};
    if (!r) return;
    const odo = $('.odo', r), dot = $('.rail-dot', r), cols = [];
    for (let i = 0; i < 4; i++) {
      const c = d.createElement('span'); c.className = 'dg';
      for (let n = 0; n < 10; n++) { const x = d.createElement('i'); x.textContent = n; c.appendChild(x); }
      odo.appendChild(c); cols.push(c);
    }
    let year = null;
    const setYear = (y) => {
      y = parseInt(y, 10);
      if (!y || y === year) return;
      const s = String(y).padStart(4, '0');
      cols.forEach((c, i) => { const n = +s[i]; Array.from(c.children).forEach((x) => { x.style.transform = `translateY(${-n * 100}%)`; }); });
      dot.style.setProperty('--x', `${clamp((y - A0) / (A1 - A0)) * 100}%`);
      if (year !== null) Sound.sfx('odo');
      year = y;
    };
    if (!chap) { odo.parentElement.hidden = true; dot.style.opacity = 0; return; }
    const marks = $$('[data-y]', chap).filter((m) => /^\d{4}$/.test(m.dataset.y || '') && !m.classList.contains('stage-step') && !m.closest('details:not([open]), .note, figure, .stage-vis'));
    const span = (body.dataset.span || '').split(' ').map((x) => parseInt(x, 10)).filter(Boolean);
    const kick = $('.ch-kick', chap);
    const ky = kick && (kick.textContent.match(/\b(1[6-9]\d\d|20[0-2]\d)\b/) || [])[1];
    const baseY = body.dataset.y || ky || span[0] || (marks[0] && marks[0].dataset.y);
    if (baseY) setYear(baseY); else { odo.parentElement.hidden = true; dot.style.opacity = 0; }
    Rail.frame = (vh) => {
      const mid = vh * .5;
      let y = baseY;
      for (const m of marks) { if (m.getBoundingClientRect().top < mid) y = m.dataset.y; else break; }
      if (y) setYear(y);
    };
  }

  /* =====================================================================================
     SCENES — each [data-scene] gets an update(p, rect, vh) with p = progress through the viewport (0…1)
     ===================================================================================== */
  const SCENES = {
    part(el) {
      let fired = false;
      const img = $('.part-bg img', el), L = liveImg($('.part-bg', el), img, { tone: .45, br: .56, vig: .3 });
      return (p) => {
        el.style.setProperty('--p', p.toFixed(4));
        if (L) L.set(p);
        if (!fired && p > .2 && p < .8) { fired = true; Sound.sfx('act'); }
        if (p < .05 || p > .97) fired = false;
      };
    },
  };
  const DPR = Math.min(window.devicePixelRatio || 1, 1.6);
  const fitCanvas = (cv) => { const r = cv.getBoundingClientRect(); const w = Math.max(1, r.width * DPR | 0), h = Math.max(1, r.height * DPR | 0); if (cv.width !== w || cv.height !== h) { cv.width = w; cv.height = h; } return [w, h]; };
  /* chapter 12: the light table — each transcript beside the photographed pages. The paragraph being read is lit on
     the original; a tap in the text lights the exact place, a tap on the original finds the text. */
  function caretFrac(p, x, y) {
    let r = null;
    if (d.caretRangeFromPoint) r = d.caretRangeFromPoint(x, y);
    else if (d.caretPositionFromPoint) { const c = d.caretPositionFromPoint(x, y); if (c) { r = d.createRange(); r.setStart(c.offsetNode, c.offset); } }
    if (!r || !p.contains(r.startContainer)) return null;
    const pre = d.createRange(); pre.selectNodeContents(p); pre.setEnd(r.startContainer, r.startOffset);
    return clamp(pre.toString().length / Math.max(1, p.textContent.length));
  }
  /* the words of a transcript that stand where the lit strip stands on the original: the same place, found in both */
  const LT_HL = (() => { try { if (!CSS.highlights || typeof Highlight === 'undefined') return null; const now = new Highlight(), hot = new Highlight(); CSS.highlights.set('lt-now', now); CSS.highlights.set('lt-hot', hot); return { now, hot }; } catch (e) { return null; } })();
  const readText = (p) => {
    if (p._rt) return p._rt;
    const nodes = []; let n = 0;
    const w = d.createTreeWalker(p, NodeFilter.SHOW_TEXT, { acceptNode: (t) => (t.parentElement.closest('.srefs,.note,button,.sn') ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT) });
    for (let t = w.nextNode(); t; t = w.nextNode()) { nodes.push([t, n]); n += t.data.length; }
    return (p._rt = { nodes, len: n, txt: nodes.map(([t]) => t.data).join('') });
  };
  const wordsAt = (p, f, span) => {
    const R = readText(p);
    if (!R.len) return null;
    const c = clamp(f) * R.len;
    let a = Math.max(0, Math.round(c - span / 2)), b = Math.min(R.len, Math.round(c + span / 2));
    while (a > 0 && /\S/.test(R.txt[a - 1])) a--;
    while (b < R.len && /\S/.test(R.txt[b])) b++;
    while (a < b && /\s/.test(R.txt[a])) a++;
    const at = (k) => { for (let i = R.nodes.length - 1; i >= 0; i--) { const [t, o] = R.nodes[i]; if (k >= o) return [t, Math.min(k - o, t.data.length)]; } return [R.nodes[0][0], 0]; };
    const r = d.createRange();
    try { r.setStart(...at(a)); r.setEnd(...at(b)); } catch (e) { return null; }
    return r;
  };
  SCENES.lighttable = (el) => {
    const dt = el.closest('details');
    let D; try { D = JSON.parse(el.dataset.lt); } catch (e) { return null; }
    const paras = $$('[data-lp]', el), figs = {}, tabs = $$('.lt-tab', el), stage = $('.lt-stage', el);
    $$('.lt-page', el).forEach((f) => { figs[f.dataset.pg] = f; });
    const P = D.pages;
    const slant = (pid, y) => { const m = P[pid]; const t = m.b > m.t ? clamp((y - m.t) / (m.b - m.t)) : 0; return m.sl[0] + (m.sl[1] - m.sl[0]) * t; };
    const XL = 2, XR = 98, REF = 10;
    const band = (pid, y0, y1) => {
      const a = y0, b = y1, sa = slant(pid, a), sb = slant(pid, b);
      const y = (yy, sl, x) => (yy + sl * (x - REF) / 100).toFixed(2);
      return `${XL},${y(a, sa, XL)} ${XR},${y(a, sa, XR)} ${XR},${y(b, sb, XR)} ${XL},${y(b, sb, XL)}`;
    };
    // a paragraph's place, as a fraction of its length, on the pages it covers
    const locate = (i, f) => {
      const segs = D.paras[i];
      const w = segs.map(([pid, y0, y1]) => (y1 - y0) / P[pid].pi + 1), tot = w.reduce((x, y) => x + y, 0);
      let acc = 0;
      for (let k = 0; k < segs.length; k++) {
        if (f * tot <= acc + w[k] || k === segs.length - 1) {
          const [pid, y0, y1] = segs[k], ff = clamp((f * tot - acc) / w[k]);
          return { pid, y: y0 + (y1 - y0) * ff, seg: segs[k] };
        }
        acc += w[k];
      }
      return null;
    };
    const tween = new WeakMap();
    // the lamp: everything on the page but the paragraph is dimmed — the hole follows the paragraph's outline
    const lamp = (poly, pts) => { if (!poly.classList.contains('hl-p')) return; const dd = poly.parentNode.querySelector('.hl-d'); if (dd) dd.setAttribute('d', 'M-1,-1H101V101H-1Z M' + pts.trim().replace(/ /g, ' L') + 'Z'); };
    const setPoly = (poly, pts) => {
      const to = pts.split(/[ ,]/).map(Number), from = (poly.getAttribute('points') || '').split(/[ ,]/).map(Number);
      if (RM || from.length !== to.length || from.some(isNaN)) { poly.setAttribute('points', pts); lamp(poly, pts); return; }
      const t0 = performance.now(); tween.set(poly, t0);
      const step = (t) => {
        if (tween.get(poly) !== t0) return;
        const e = ease(clamp((t - t0) / 320));
        const v = to.map((x, j) => (from[j] + (x - from[j]) * e).toFixed(2));
        let out = ''; for (let j = 0; j < v.length; j += 2) out += (j ? ' ' : '') + v[j] + ',' + v[j + 1];
        poly.setAttribute('points', out); lamp(poly, out);
        if (e < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    };
    let curPg = null, curI = -1, pinnedUntil = 0, myRange = null, hotT = 0;
    const view = $('.lt-view', el);
    // where the eye is: under the original when it sits on top of the text (phones), otherwise a little above the middle
    const readLine = (vh) => { if (stage && getComputedStyle(stage).display === 'block' && view) { const vb = view.getBoundingClientRect().bottom; return vb + (vh - vb) * .24; } return vh * .42; };
    const showPage = (pid) => {
      if (pid === curPg) return;
      curPg = pid;
      Object.entries(figs).forEach(([k, f]) => { f.hidden = k !== pid; });
      tabs.forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.pg === pid)));
      Sound.sfx('page');
    };
    const show = (i, f, strong) => {
      const loc = locate(i, f);
      if (!loc) return;
      showPage(loc.pid);
      const fig = figs[loc.pid], pi = P[loc.pid].pi;
      const segHere = D.paras[i].filter((s) => s[0] === loc.pid);
      const hp = $('.hl-p', fig), hs = $('.hl-s', fig);
      if (segHere.length) setPoly(hp, band(loc.pid, segHere[0][1] - .62 * pi, segHere[segHere.length - 1][2] + .62 * pi));
      setPoly(hs, band(loc.pid, loc.y - .95 * pi, loc.y + .95 * pi));
      hs.style.opacity = strong ? '.5' : '.3';
      if (i !== curI) { paras.forEach((p, k) => p.classList.toggle('on', k === i)); curI = i; }
      // the same strip in the transcription: about as many words as the lit lines of the original hold
      if (LT_HL) {
        const lines = D.paras[i].reduce((sum, [q, a0, a1]) => sum + (a1 - a0) / P[q].pi + 1, 0);
        const R = readText(paras[i]), r = wordsAt(paras[i], f, 1.9 * R.len / Math.max(1, lines));
        if (myRange) { LT_HL.now.delete(myRange); LT_HL.hot.delete(myRange); }
        myRange = r;
        if (r) {
          (strong ? LT_HL.hot : LT_HL.now).add(r);
          if (strong) { clearTimeout(hotT); hotT = setTimeout(() => { if (myRange === r) { LT_HL.hot.delete(r); LT_HL.now.add(r); } }, 1100); }
        }
      }
      // phones: the strip of the page follows the place being read
      const sheet = $('.lt-sheet', fig);
      if (stage && sheet && getComputedStyle(stage).display === 'block') {
        const h = sheet.offsetHeight, sh = stage.clientHeight;
        sheet.style.setProperty('--ty', `${clamp(sh / 2 - h * loc.y / 100, sh - h, 0)}px`);
      } else if (sheet) sheet.style.removeProperty('--ty');
    };
    // tap in the transcription
    paras.forEach((p, i) => listen(p, 'click', (e) => {
      if (e.target.closest('a,button')) return;
      const f = caretFrac(p, e.clientX, e.clientY);
      const r = p.getBoundingClientRect();
      show(i, f == null ? clamp((e.clientY - r.top) / r.height) : f, true);
      pinnedUntil = performance.now() + 2200; Sound.sfx('tick');
    }));
    // tap on the original
    Object.values(figs).forEach((fig) => listen($('img', fig), 'click', (e) => {
      e.preventDefault(); e.stopPropagation();
      const r = e.currentTarget.getBoundingClientRect(), x = (e.clientX - r.left) / r.width * 100, y = (e.clientY - r.top) / r.height * 100;
      const pid = fig.dataset.pg;
      let best = null;
      D.paras.forEach((segs, i) => segs.forEach(([p2, y0, y1], j) => {
        if (p2 !== pid) return;
        const sl = slant(pid, y), yy = y - sl * (x - REF) / 100, pi = P[pid].pi;
        const dd = yy < y0 - pi ? y0 - pi - yy : yy > y1 + pi ? yy - y1 - pi : 0;
        if (!best || dd < best.d) best = { d: dd, i, j, f0: clamp((yy - y0) / Math.max(.01, y1 - y0)), segs };
      }));
      if (!best) return;
      // fraction of the whole paragraph: the pages before this piece of it, then the place within the piece
      const w = best.segs.map(([q, a0, a1]) => (a1 - a0) / P[q].pi + 1), tot = w.reduce((a, b2) => a + b2, 0);
      let acc = 0; for (let k2 = 0; k2 < best.j; k2++) acc += w[k2];
      const f = clamp((acc + best.f0 * w[best.j]) / Math.max(.01, tot));
      show(best.i, f, true); pinnedUntil = performance.now() + 2600;
      const p = paras[best.i], rr = myRange ? myRange.getBoundingClientRect() : null, pr = p.getBoundingClientRect();
      const yAt = rr && rr.height ? rr.top + rr.height / 2 : pr.top + pr.height * f, top = readLine(innerHeight);
      const to = scrollY + yAt - top;
      if (isFinite(to) && (yAt < top - 10 || yAt > innerHeight * .88)) scrollTo({ top: to, behavior: RM ? 'auto' : 'smooth' });
      Sound.sfx('tick');
    }, true));
    Object.values(figs).forEach((fig) => listen($('img', fig), 'dblclick', (e) => { e.preventDefault(); openLightbox(e.currentTarget); }));
    tabs.forEach((b) => listen(b, 'click', () => { showPage(b.dataset.pg); pinnedUntil = performance.now() + 4000; }));
    if (paras.length) show(0, 0);
    el.classList.add('live');
    return (p, r, vh) => {
      if (!dt || !dt.open || performance.now() < pinnedUntil) return;
      const line = readLine(vh);
      for (let i = 0; i < paras.length; i++) {
        const q = paras[i].getBoundingClientRect();
        if (q.top <= line && q.bottom >= line) { show(i, clamp((line - q.top) / Math.max(1, q.height))); return; }
        if (q.top > line) { if (i === 0) show(0, 0); return; }
      }
    };
  };
  /* chapter 12: the case, day by day — the calendar follows the reading */
  SCENES.calendar = (el) => {
    const days = $$('p[data-day]', chap || d);
    const links = $$('a[data-day]', el), list = $('.cal-list', el);
    let cur = null;
    return (p, r, vh) => {
      let k = null;
      for (const x of days) {
        const q = x.getBoundingClientRect();
        if (q.top >= vh * .5) break;
        const keys = x.dataset.day.split(' ');
        k = keys[Math.min(keys.length - 1, Math.floor(clamp((vh * .5 - q.top) / Math.max(1, q.height)) * keys.length))];
      }
      if (k === cur) return;
      cur = k;
      links.forEach((a) => a.classList.toggle('on', a.dataset.day === k));
      el.dataset.mo = k ? k.slice(0, 2) : '02';
      days.forEach((x) => x.classList.toggle('day-on', x.dataset.day.split(' ').includes(k)));
      const now = $('.cal-now', el), a = k && $(`.cal-list a[data-day="${k}"]`, el);
      if (now) now.innerHTML = a ? `<b>${$('.d', a).textContent} 1913</b>${$('.t', a).textContent}` : '';
      const on = $('.cal-list a.on', el);
      if (on && list) {
        if (list.scrollWidth > list.clientWidth + 4) list.scrollTo({ left: on.offsetLeft - list.clientWidth / 2 + on.offsetWidth / 2, behavior: RM ? 'auto' : 'smooth' });
        else if (list.scrollHeight > list.clientHeight + 4) list.scrollTo({ top: on.offsetTop - list.clientHeight / 2, behavior: RM ? 'auto' : 'smooth' });
      }
      if (k) Sound.sfx('tick');
    };
  };
  /* chapter 12: the road from Årgab to Vridsløselille, drawn leg by leg as the paragraphs that tell it are read */
  SCENES.route = (el) => {
    const legs = $$('.leg', el), stops = $$('.stop', el), items = $$('.route-legs li', el), here = $('.here', el);
    const marks = [];
    $$('[data-leg]', chap || d).forEach((p) => p.dataset.leg.split(' ').forEach((k, j, arr) => marks.push({ p, k: +k, off: arr.length > 1 ? j / arr.length : 0, span: 1 / arr.length })));
    marks.sort((a, b) => a.k - b.k);
    if (!marks.length) return null;
    el.classList.add('armed');
    let last = -2;
    // in the text (narrow screens) the map draws itself while it is in view; beside the text it follows the paragraphs
    const INLINE = el.classList.contains('route-inline'), svg = $('svg', el);
    return (p, r, vh) => {
      const line = vh * .55;
      let n = -1, t = 0;
      let prog;
      if (INLINE) {
        const q = svg.getBoundingClientRect(), g = RM ? 1 : clamp((vh * .92 - q.top) / Math.max(1, vh * .92 - Math.max(0, (vh - q.height) / 2)));
        prog = legs.map((_, i) => clamp(g * legs.length - i));
      } else prog = marks.map((m) => {
        const q = m.p.getBoundingClientRect(), top = q.top + q.height * m.off, h = Math.max(120, q.height * m.span * .8);
        return RM ? 1 : clamp((line - top) / h);
      });
      prog.forEach((v, i) => { const k = INLINE ? i : marks[i].k; legs[k] && (legs[k].style.strokeDashoffset = (1 - v).toFixed(3)); if (v > 0) { n = k; t = v; } });
      stops.forEach((sn, i) => sn.classList.toggle('on', i === 0 || (prog[i - 1] || 0) >= .98));
      items.forEach((li, i) => li.classList.toggle('on', (prog[i] || 0) > 0));
      if (n >= 0 && legs[n]) {
        const L = legs[n].getTotalLength(), pt = legs[n].getPointAtLength(L * t);
        here.setAttribute('cx', pt.x.toFixed(1)); here.setAttribute('cy', pt.y.toFixed(1));
      } else { const c = $('circle', stops[0]); here.setAttribute('cx', c.getAttribute('cx')); here.setAttribute('cy', c.getAttribute('cy')); }
      const k = n + (t >= .98 ? 1 : 0);
      if (k !== last) { if (last > -2 && k > last) Sound.sfx('pen'); last = k; }
    };
  };

  /* a scene that animates on its own clock while it is on screen (waves, rain), not only when the page scrolls */
  function loop(el, fn) {
    if (RM || !('IntersectionObserver' in window)) return;
    let running = false, last = 0;
    const frame = (now) => { if (!running) return; const dt = Math.min(64, now - last || 16); last = now; fn(now / 1000, dt); requestAnimationFrame(frame); };
    observe((es) => { const v = es[0].isIntersecting; if (v && !running) { running = true; last = performance.now(); requestAnimationFrame(frame); } else if (!v) running = false; }).observe(el);
    onPage(() => { running = false; });
  }
  /* rain on a canvas: two depths of drops driven slant by the wind, and now and then lightning */
  function Rain(cv, o = {}) {
    const g = cv.getContext('2d'), N = o.n || 360;
    const drops = Array.from({ length: N }, () => ({ x: Math.random() * 1.4 - .4, y: Math.random(), l: .5 + Math.random(), v: .7 + Math.random() * .7, z: Math.random() < .35 }));
    let flash = 0, next = 0;
    return {
      k: 1, wind: .38,
      bolt() { flash = 1; },
      frame(now, dt) {
        const [w, h] = fitCanvas(cv), k = this.k;
        g.clearRect(0, 0, w, h);
        if (k <= .002) return;
        if (flash > .01) { g.fillStyle = `rgba(222,232,236,${(flash * .2 * k).toFixed(3)})`; g.fillRect(0, 0, w, h); flash *= Math.pow(.84, dt / 16); }
        const n = (N * (.2 + .8 * k)) | 0, W = this.wind;
        for (const near of [false, true]) {
          g.strokeStyle = near ? `rgba(214,224,228,${(.1 + .26 * k).toFixed(3)})` : `rgba(180,196,202,${(.06 + .14 * k).toFixed(3)})`;
          g.lineWidth = (near ? 1.3 : .8) * DPR;
          g.beginPath();
          for (let i = 0; i < n; i++) {
            const r = drops[i];
            if (r.z !== near) continue;
            const sp = r.v * (near ? 1.35 : .8);
            r.y += sp * dt * .0012; r.x += sp * dt * .0012 * W * h / w;
            if (r.y > 1.05) { r.y = -.08; r.x = Math.random() * 1.4 - .4; }
            const L = r.l * (near ? 34 : 18) * DPR, x = r.x * w, y = r.y * h;
            g.moveTo(x, y); g.lineTo(x + L * W, y + L);
          }
          g.stroke();
        }
        if (o.thunder && k > .35 && now > next) { if (next) { flash = 1; o.thunder(); } next = now + 4.2 + Math.random() * 5.5; }
      },
    };
  }
  /* chapter 5: rain and lightning over the top of the chapter */
  SCENES.storm = (el) => {
    if (RM) return null;
    const R = Rain($('canvas', el), { n: 260 });
    loop(el, (now, dt) => R.frame(now, dt));
    return (p) => { R.k = 1 - clamp((p - .25) / .6); };
  };

  /* STAGES — a picture that stays on screen while the chronicle's own paragraphs pass over it as cards. The scroll
     sets a continuous time t (0 → number of steps); the picture eases towards it on its own clock. */
  const VIS = {};
  SCENES.stage = (el) => {
    const steps = $$('.stage-step', el), vis = $('.stage-vis', el);
    const V = VIS[el.dataset.vis] ? VIS[el.dataset.vis](vis, el, steps.length) : null;
    let target = 0, T = 0;
    const cards = steps.map((x) => $('.stage-card', x) || x);
    const isSplit = () => splitNow() && !!el.closest('.chap') && !BOOK;
    const measure = (vh) => { const sp = isSplit(), nar = sp || innerWidth < 720, top = sp ? vis.getBoundingClientRect().height / vh : 0, a = nar ? 1 : .63, b = sp ? Math.max(.25, 1 - top) : nar ? .5 : .4; return cards.reduce((s, x) => s + clamp((vh * a - x.getBoundingClientRect().top) / (vh * b)), 0); };
    if (V) V.draw(RM || BOOK ? steps.length : 0, 0, 16);
    // the camera eases on its own clock, and rests when it has arrived: a still picture costs nothing
    let drawn = -1, dirty = true;
    listen(window, 'resize', () => { dirty = true; });
    loop(el, (now, dt) => {
      T += (target - T) * (1 - Math.pow(.9, dt / 16));
      if (Math.abs(target - T) < .0004) T = target;
      if (V && (V.always || T !== drawn || dirty)) { V.draw(T, now, dt); drawn = T; dirty = false; }
    });
    return (p, r, vh) => {
      target = RM ? steps.length : measure(vh);
      const sp = isSplit(), vb = sp ? vis.getBoundingClientRect().bottom : 0;
      steps.forEach((x) => { const q = (sp ? cards[steps.indexOf(x)] : x).getBoundingClientRect(); x.classList.toggle('on', sp ? q.top < vh * .92 && q.bottom > vb + 40 : q.top < vh * .72 && q.bottom > vh * .28); });
      if (RM && V) V.draw(target, 0, 16);
    };
  };

  /* a full-screen shader on a canvas: the uniforms are set by name */
  function glFull(canvas, FS, res = 1.25) {
    const gl = canvas.getContext('webgl', { alpha: false, antialias: false, premultipliedAlpha: false });
    if (!gl) return null;
    const sh = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); return s; };
    const pr = gl.createProgram();
    gl.attachShader(pr, sh(gl.VERTEX_SHADER, 'attribute vec2 p;varying vec2 v;void main(){v=p*.5+.5;v.y=1.-v.y;gl_Position=vec4(p,0.,1.);}'));
    gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, FS)); gl.linkProgram(pr);
    if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) return null;
    gl.useProgram(pr);
    const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    const loc = gl.getAttribLocation(pr, 'p'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    const U = {};
    const u = (k) => (k in U ? U[k] : (U[k] = gl.getUniformLocation(pr, k)));
    return {
      draw(vals, w, h) {
        const r = Math.min(window.devicePixelRatio || 1, res), W = Math.max(1, Math.round(w * r)), H = Math.max(1, Math.round(h * r));
        if (canvas.width !== W || canvas.height !== H) { canvas.width = W; canvas.height = H; }
        gl.viewport(0, 0, W, H);
        gl.uniform2f(u('res'), W, H);
        for (const k in vals) { const v = vals[k]; if (typeof v === 'number') gl.uniform1f(u(k), v); else if (v.length === 2) gl.uniform2f(u(k), v[0], v[1]); else if (v.length === 4) gl.uniform4f(u(k), v[0], v[1], v[2], v[3]); }
        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      },
      free() { const x = gl.getExtension('WEBGL_lose_context'); if (x) x.loseContext(); },
    };
  }
  /* chapter 5: the North Sea on the 9th of November 1878 — the same wave the drawing uses, painted: a night sky
     driven with cloud and spray, the water deepening under it, and the surf churned white where the bars break it */
  const SEA_FS = `precision mediump float;
uniform vec2 res;uniform vec4 vb;uniform float t,A,flash;varying vec2 v;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float noise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(hash(i),hash(i+vec2(1.,0.)),f.x),mix(hash(i+vec2(0.,1.)),hash(i+vec2(1.,1.)),f.x),f.y);}
float fbm(vec2 p){float s=0.,a=.5;for(int i=0;i<4;i++){s+=a*noise(p);p=p*2.03+vec2(1.7,9.2);a*=.5;}return s+a*.5;}
float bump(float x,float c,float w){float q=(x-c)/w;return exp(-q*q);}
float amp(float x){return A*(1.+.7*bump(x,900.,90.)+1.1*bump(x,1180.,80.))*clamp((1340.-x)/140.,0.,1.);}
float H(float x){return 470.+amp(x)*(sin(x*.021-t*1.9)*.6+sin(x*.0083+t*.8)*.4);}
void main(){
 vec2 w=vec2(vb.x+v.x*vb.z,vb.y+v.y*vb.w);
 float h=H(w.x);vec3 col;
 if(w.y<h){
  float k=clamp((w.y-vb.y)/(470.-vb.y),0.,1.);
  col=mix(vec3(.018,.03,.04),vec3(.11,.16,.18),pow(k,1.5));
  float c=fbm(vec2(w.x*.0021+t*.025,w.y*.0042-t*.008));
  float c2=fbm(vec2(w.x*.006-t*.05,w.y*.01));
  col+=vec3(.07,.09,.1)*smoothstep(.42,.92,c)*(1.-k*.4)+vec3(.03,.04,.045)*c2;
  float sp=fbm(vec2(w.x*.018-t*1.1,w.y*.04+t*.3))*exp(-(h-w.y)/28.);
  col+=vec3(.28,.32,.34)*sp*.45;
  col+=flash*vec3(.2,.23,.26)*(1.-k*.55)*(.5+.5*c);
 }else{
  float dd=w.y-h;
  col=mix(vec3(.12,.22,.26),vec3(.012,.035,.05),clamp(dd/240.,0.,1.));
  float n=fbm(vec2(w.x*.011-t*.3,dd*.028+t*.18));
  col+=vec3(.05,.08,.09)*n*exp(-dd/110.);
  float br=bump(w.x,900.,75.)*.65+bump(w.x,1180.,75.)+bump(w.x,1262.,95.)*.75;
  float fo=exp(-dd/(3.5+br*18.))*(.45+.55*fbm(vec2(w.x*.045-t*1.3,dd*.22-t)));
  col=mix(col,vec3(.84,.88,.87),clamp(fo*(.32+br*.85),0.,.92));
  col+=flash*vec3(.14,.17,.19)*exp(-dd/70.);
 }
 col+=(hash(v*res+fract(t))-.5)*.028;
 gl_FragColor=vec4(col,1.);
}`;
  /* chapter 5: the beach in cross-section. Step 1: the boat comes in from the sea, over the outer bar, and capsizes
     on the inner at eleven. Step 2: it is seen from land, the crew bring the lifeboat and the rocket apparatus down,
     two rockets are fired at the man on the oar, who never takes the line. Step 3: the helmsman comes ashore on his
     oar. The labels are pinned to what they name and keep their size on every screen. */
  VIS.xsec = (vis, stageEl) => {
    // three layers on one camera: the moving sea behind, the drawn beach (still, so it is painted once), the boat and the men in front
    const svg = $('svg.xs:not(.xs-back):not(.xs-front)', vis), layers = $$('svg.xs', vis), q = (s) => $(s, vis), qa = (s) => $$(s, vis);
    if (!svg) return null;
    const setVB = (v) => layers.forEach((l) => l.setAttribute('viewBox', v));
    const D = svg.dataset, OUT = +D.out || 900, INN = +D.inn || 1180, SHORE = +D.shore || 1340, B0 = +D.b0 || 560;
    const ASH = +D.ashore || 1346, AGY = +D.ground || 466, SURF = 470, PRINT_VB = svg.getAttribute('viewBox');
    const boat = q('.xs-boat'), crewOn = q('.xs-boat .crew'), heads = q('.xs-boat .heads'), lost = q('.xs-lost');
    const lostM = lost ? $$('.lm', lost) : [];
    lostM.forEach((m) => { m.dataset.t = m.getAttribute('transform') || ''; });
    const brk = q('.xs-breaker'), surf = q('.xs-surf'), sea = q('.xs-seafill'), foam = qa('.xs-foam'), flashEl = q('.xs-flash');
    const s1 = q('.xs-swim.s1'), s2 = q('.xs-swim.s2'), man = q('.xs-man'), crew = q('.xs-crew'), flag = q('.xs-mast .flag');
    const rk = qa('.xs-rocket'), sp = qa('.xs-spark');
    const Q = rk.map((r) => (r.getAttribute('d').match(/-?[\d.]+/g) || []).map(Number));
    const LIE = rk.map((r) => (r.dataset.lie ? r.dataset.lie.split(',').map(Number) : null));
    const qpt = (a, f) => { const u = 1 - f; return [u * u * a[0] + 2 * u * f * a[2] + f * f * a[4], u * u * a[1] + 2 * u * f * a[3] + f * f * a[5]]; };
    const box = $('.xs-tags', vis);
    const mk = (el) => (el ? { el, b: $('b', el) || el, w: 0, x: +el.dataset.x, y: +el.dataset.y } : null);
    const pins = box ? $$('.xs-tag[data-x]', box).map(mk) : [];
    const tN1 = box && mk($('.xs-tag.n1', box)), tN2 = box && mk($('.xs-tag.n2', box)), tRk = box && mk($('.xs-tag.rk', box)), tCl = box && mk($('.xs-clock', box));
    const all = [...pins, tN1, tN2, tRk, tCl].filter(Boolean);
    if (d.fonts && d.fonts.ready) d.fonts.ready.then(() => all.forEach((T) => { T.w = 0; }));
    let SEA = null;
    if (LIVE) {
      const sc = d.createElement('canvas');
      sc.className = 'sv-gl';
      vis.insertBefore(sc, vis.firstChild);
      SEA = glFull(sc, SEA_FS, .6);   // cloud and spray are soft: two thirds of a pixel is enough, and the sea keeps its pace
      if (SEA) { vis.classList.add('gl-on'); onPage(() => SEA.free()); } else sc.remove();
    }
    const cv = $('canvas.stage-rain', vis);
    const R = cv && !RM ? Rain(cv, { n: 220 }) : null;
    let flashT = 0, cam = null, fired = {}, lastW = 0, cardR = null, printing = false, lastVB = '';
    const onBP = () => { printing = true; setVB(PRINT_VB); }, onAP = () => { printing = false; };
    addEventListener('beforeprint', onBP); addEventListener('afterprint', onAP);
    onPage(() => { removeEventListener('beforeprint', onBP); removeEventListener('afterprint', onAP); });
    /* a label: the dot sits on the feature, the line and the words stand off it; near an edge only the words slide */
    const pin = (T, X, Y, a, s, vx, vy, W, Hh) => {
      if (!T) return;
      const px = (X - vx) * s, py = (Y - vy) * s;
      const o = a * clamp(Math.min(px, W - px) / 28) * clamp(Math.min(py, Hh - py) / 28);
      T.el.style.opacity = o.toFixed(3);
      if (o <= .002) return;
      if (!T.w) T.w = T.b.offsetWidth || 1;
      const half = T.w / 2, m = 12;
      let dx = 0;
      if (px - half < m) dx = m - (px - half);
      if (px + half + dx > W - m) dx = W - m - (px + half);
      T.el.style.transform = `translate(${px.toFixed(1)}px,${py.toFixed(1)}px)`;
      T.b.style.setProperty('--dx', dx.toFixed(1) + 'px');
    };
    const bump = (x, c, w) => Math.exp(-(((x - c) / w) ** 2));
    const amp = (x, A) => A * (1 + .7 * bump(x, OUT, 90) + 1.1 * bump(x, INN, 80)) * clamp((SHORE - x) / 140);
    const H = (x, now, A) => SURF + amp(x, A) * (Math.sin(x * .021 - now * 1.9) * .6 + Math.sin(x * .0083 + now * .8) * .4);
    const line = (x0, x1, now, A, dy = 0, stepX = 20) => { let dd = ''; for (let x = x0; x <= x1; x += stepX) dd += (dd ? ' L' : 'M') + x + ',' + (H(x, now, A) + dy).toFixed(1); return dd; };
    const fire = (k, on, fn) => { if (on && !fired[k]) { fired[k] = true; fn(); } else if (!on) fired[k] = false; };
    let gf = 0;
    return {
      always: true,   // the sea moves on its own
      draw(t, now, dt) {
        const A = 13;
        // the sea
        const top = line(-1200, SHORE, now, A, 0, 20);
        surf.setAttribute('d', top);
        sea.setAttribute('d', top + ` L${SHORE},700 L2800,700 L2800,1900 L-1200,1900 Z`);
        // step 1 — in over the outer bar, capsized on the inner
        const u1 = clamp(t), cap = ease(clamp((u1 - .8) / .14));
        const bx = B0 + (INN - B0) * clamp(u1 / .8);
        const slope = (H(bx + 6, now, A) - H(bx - 6, now, A)) / 12;
        const by = H(bx, now, A) - 4 + cap * 14;
        boat.setAttribute('transform', `translate(${bx.toFixed(1)},${by.toFixed(1)}) rotate(${(Math.atan(slope) * 57 * .8 + cap * 168).toFixed(1)}) scale(1.25)`);
        crewOn.style.opacity = heads.style.opacity = (1 - clamp(cap * 3)).toFixed(3);
        // the upturned hull is lost to sight in the surf while the men are still in the water
        const drift = clamp((t - .98) / .45);
        boat.style.opacity = (1 - drift).toFixed(3);
        const b1 = clamp((u1 - .58) / .24), b2 = clamp((u1 - .86) / .1);
        brk.style.transform = `translateX(${(b2 * 30).toFixed(1)}px) scaleY(${(ease(b1) * (1 - .8 * b2) + .06 * Math.sin(now * 2)).toFixed(3)})`;
        foam[0].setAttribute('d', line(OUT - 90, OUT + 90, now, A, -2, 12));
        foam[0].style.opacity = (.25 + .45 * Math.max(0, Math.sin(now * 1.9 - OUT * .021))).toFixed(3);
        foam[1].setAttribute('d', line(INN - 80, INN + 100, now, A, -2, 12));
        foam[1].style.opacity = (.2 + .35 * Math.max(0, Math.sin(now * 1.9 - INN * .021)) + b2 * .5).toFixed(3);
        foam[2].setAttribute('d', line(SHORE - 150, SHORE - 8, now, A * .6, -1, 14));
        foam[2].style.opacity = (.35 + .3 * Math.sin(now * 1.3)).toFixed(3);
        // the men in the water after the capsizing
        const inW = clamp((u1 - .9) / .06);
        const sink = clamp((t - .98) / .3);
        lost.style.opacity = inW.toFixed(3);
        lost.setAttribute('transform', `translate(${(bx - 10 - sink * 26).toFixed(1)},${(H(bx, now, A) + 1).toFixed(1)})`);
        lostM.forEach((m, k) => { const g = clamp((sink - k * .18) / .22); m.style.opacity = (1 - g).toFixed(3); m.setAttribute('transform', m.dataset.t + ` translate(0,${(g * 6).toFixed(1)})`); });
        const aClock = clamp((u1 - .88) / .08) * (1 - clamp((t - 1.25) / .2));
        // step 2 — seen from land; the crew with the lifeboat and the rocket apparatus; two rockets; the man on the oar
        const u2 = clamp(t - 1);
        svg.classList.toggle('lit', t > 1.02);
        crew.style.opacity = clamp((u2 - .02) / .18).toFixed(3);
        const r1 = ease(clamp((u2 - .3) / .18)), r2 = ease(clamp((u2 - .52) / .18));
        [r1, r2].forEach((f, i) => {
          rk[i].style.strokeDashoffset = (1 - f).toFixed(4);
          const [x, y] = qpt(Q[i], f);
          sp[i].setAttribute('cx', x.toFixed(1)); sp[i].setAttribute('cy', y.toFixed(1));
          sp[i].style.opacity = f > 0 && f < 1 ? 1 : 0;
          // once it has fallen, the line sinks from its arc on to the water, from the stand out past the man
          const lie = ease(clamp((u2 - (i ? .72 : .5)) / .16)), c = Q[i], L = LIE[i];
          if (L) rk[i].setAttribute('d', `M${c[0]},${c[1]} Q${lerp(c[2], L[0], lie).toFixed(1)},${lerp(c[3], L[1], lie).toFixed(1)} ${c[4]},${(c[5] + lie * 2).toFixed(1)}`);
        });
        const aRk = clamp((u2 - .36) / .12) * (1 - clamp((t - 1.9) / .15));
        const a1 = inW * (1 - clamp((u2 - .8) / .16));
        const x1 = bx - 8 + Math.sin(now * .7) * 6, y1 = H(x1, now, A) + clamp((u2 - .8) / .16) * 18;
        s1.style.opacity = a1.toFixed(3);
        s1.setAttribute('transform', `translate(${x1.toFixed(1)},${y1.toFixed(1)}) rotate(${(Math.sin(now * 1.6) * 8).toFixed(1)}) scale(1.15)`);
        // step 3 — the helmsman comes ashore on his oar
        const u3 = clamp(t - 2), go = ease(clamp((u3 - .05) / .6)), up = clamp((u3 - .66) / .1);
        const x2 = lerp(bx + 34, ASH - 18, go), y2 = H(x2, now, A) - 1;
        s2.style.opacity = (inW * (1 - up)).toFixed(3);
        s2.setAttribute('transform', `translate(${x2.toFixed(1)},${y2.toFixed(1)}) rotate(${(Math.sin(now * 1.4 + 1) * 9).toFixed(1)}) scale(1.15)`);
        man.style.opacity = up.toFixed(3);
        // the pennant on the signal mast, in the gale
        if (flag && !RM) { const w = now * 7; flag.setAttribute('d', `M1612,137 Q1623,${(139 + Math.sin(w) * 2.4).toFixed(1)} 1636,${(141 + Math.sin(w - 1.3) * 3.2).toFixed(1)} Q1623,${(145 + Math.sin(w - .7) * 2).toFixed(1)} 1612,147 Z`); }
        // lightning
        if (flashT > .01) { flashEl.setAttribute('opacity', (flashT * .5).toFixed(3)); flashT *= Math.pow(.8, dt / 16); } else flashEl.setAttribute('opacity', 0);
        // the camera: on a wide screen the whole beach stands beside the text; on a narrow one it follows what happens
        const r = vis.getBoundingClientRect();
        if (r.width !== lastW) { lastW = r.width; cardR = null; all.forEach((T) => { T.w = 0; }); }
        let vx, vy, s;
        if (BOOK || printing) {
          const v = PRINT_VB.split(/\s+/).map(Number);
          vx = v[0]; vy = v[1]; s = r.width / v[2];
        } else {
          const wide = r.width >= 760 && r.height >= innerHeight * .8;
          if (wide) {
            if (cardR === null) { const c = stageEl && $('.stage-card', stageEl), cr = c && c.getBoundingClientRect(); cardR = cr && cr.width < r.width * .62 ? cr.right - r.left : 0; }
            // beside the text: first the sea and the two bars, then — as the men are seen from land — the beach and the station
            const fl = cardR + 28, fr = r.width - 34, span = 760;
            s = clamp((fr - fl) / span, .6, 1.2);
            const a = OUT - 130 - fl / s, b = 1905 - fr / s, want = b <= a ? (a + b) / 2 : lerp(a, b, ease(clamp((t - .95) / .45)));
            cam = cam === null || RM ? want : cam + (want - cam) * (1 - Math.pow(.94, dt / 16));
            vx = cam;
            vy = SURF - (r.height / s) * .6;
          } else {
            // close on the boat; then, seen from land, pulled back to hold the man in the water, the rockets and the station
            const asp = Math.max(.3, r.width / Math.max(1, r.height)), L2 = 1140, R2 = 1890, k = ease(clamp((t - 1) / .35));
            const w1 = clamp(700 * asp, 520, 1400), vbW = lerp(w1, Math.max(w1, R2 - L2 + 40), k);
            s = r.width / vbW;
            const want = clamp(lerp(bx + 110, (L2 + R2) / 2, k), vbW / 2 - 300, 2500 - vbW / 2);
            cam = cam === null || RM ? want : cam + (want - cam) * (1 - Math.pow(.93, dt / 16));
            vx = cam - vbW / 2;
            vy = SURF - (r.height / s) * .62;
          }
          { const vbs = `${vx.toFixed(1)} ${vy.toFixed(1)} ${(r.width / s).toFixed(1)} ${(r.height / s).toFixed(1)}`; if (vbs !== lastVB) { lastVB = vbs; setVB(vbs); } }
        }
        if (SEA) SEA.draw({ vb: [vx, vy, r.width / s, r.height / s], t: now, A, flash: flashT }, r.width, r.height);
        // the labels
        if (box && !BOOK && !printing) {
          const W = r.width, Hh = r.height;
          pins.forEach((T) => pin(T, T.x, T.y, 1, s, vx, vy, W, Hh));
          pin(tN1, x1, y1 - 12, a1 * clamp((u2 - .55) / .12), s, vx, vy, W, Hh);
          pin(tN2, up > 0 ? ASH : x2, up > 0 ? AGY - 30 : y2 - 12, inW * clamp((u3 - .1) / .12), s, vx, vy, W, Hh);
          const ap = qpt(Q[0], .5);
          pin(tRk, ap[0], ap[1] - 4, aRk, s, vx, vy, W, Hh);
          pin(tCl, INN, 300, aClock, s, vx, vy, W, Hh);
        }
        // sound at the moments
        fire('cap', cap > .4, () => Sound.sfx('breaker'));
        fire('r1', r1 > .02, () => Sound.sfx('whoosh'));
        fire('r2', r2 > .02, () => Sound.sfx('whoosh'));
        if (R) { R.k = .9 - .3 * clamp(t - 2); R.frame(now, dt); }
      },
    };
  };

  /* =====================================================================================
     LIVING PICTURES — WebGL. A photograph is drawn with its depth map (computed for this edition), so what is near
     and what is far move apart as the reader moves: the camera seems to stand in the picture. Without WebGL, or with
     reduced motion, the pictures are the plain images underneath.
     ===================================================================================== */
  const GLX = (() => {
    const VS = 'attribute vec2 p;varying vec2 v;void main(){v=p*.5+.5;v.y=1.-v.y;gl_Position=vec4(p,0.,1.);}';
    const FS = `precision mediump float;
uniform sampler2D ti,td;uniform vec2 res;uniform vec4 rc;uniform vec2 par;uniform float dz,a,t,tone,gr,hasd,vig,br;
varying vec2 v;
float h(vec2 q){return fract(sin(dot(q,vec2(12.9898,78.233)))*43758.5453);}
float dp(vec2 q){vec2 e=vec2(.006,0.);return (texture2D(td,q).r*2.+texture2D(td,q+e.xy).r+texture2D(td,q-e.xy).r+texture2D(td,q+e.yx).r+texture2D(td,q-e.yx).r)/6.;}
void main(){
 vec2 px=v*res;vec2 uv=(px-rc.xy)/rc.zw;
 if(uv.x<0.||uv.y<0.||uv.x>1.||uv.y>1.)discard;
 float d=hasd>.5?dp(uv):.5;
 vec2 o=par*(d-.5)+(uv-.5)*dz*(d-.5);
 float d2=hasd>.5?dp(clamp(uv-o,0.,1.)):.5;
 o=par*(d2-.5)+(uv-.5)*dz*(d2-.5);
 vec3 c=texture2D(ti,clamp(uv-o,.001,.999)).rgb;
 float l=dot(c,vec3(.299,.587,.114));
 c=mix(c,vec3(l)*vec3(1.08,1.,.84),tone);c*=br;
 vec2 q=v-.5;c*=1.-vig*dot(q,q)*1.6;
 c+=(h(px+fract(t)*97.)-.5)*gr;
 gl_FragColor=vec4(c*a,a);
}`;
    let ok = null;
    const support = () => { if (ok !== null) return ok; try { const c = d.createElement('canvas'); ok = !!(c.getContext('webgl') || c.getContext('experimental-webgl')); } catch (e) { ok = false; } return ok; };
    function make(canvas) {
      const gl = canvas.getContext('webgl', { premultipliedAlpha: true, alpha: true, antialias: false, preserveDrawingBuffer: false });
      if (!gl) return null;
      const sh = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); return s; };
      const pr = gl.createProgram();
      gl.attachShader(pr, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, FS)); gl.linkProgram(pr);
      if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) return null;
      gl.useProgram(pr);
      const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
      const loc = gl.getAttribLocation(pr, 'p'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
      const U = {}; ['ti', 'td', 'res', 'rc', 'par', 'dz', 'a', 't', 'tone', 'gr', 'hasd', 'vig', 'br'].forEach((k) => { U[k] = gl.getUniformLocation(pr, k); });
      gl.uniform1i(U.ti, 0); gl.uniform1i(U.td, 1);
      gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
      const cache = new Map();
      const upload = (src) => {
        const t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
        try { gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, gl.RGB, gl.UNSIGNED_BYTE, src); } catch (e) { return null; }
        return t;
      };
      const tex = (url, el) => {
        let e = cache.get(url);
        if (e) return e.t;
        e = { t: null }; cache.set(url, e);
        const im = el && el.complete && el.naturalWidth ? el : new Image();
        const go = () => { e.t = upload(im); request(); };
        if (im === el) go(); else { im.decoding = 'async'; im.onload = go; im.src = url; }
        return null;
      };
      let lost = false;
      canvas.addEventListener('webglcontextlost', (ev) => { ev.preventDefault(); lost = true; });
      return {
        size(w, h) { const r = Math.min(window.devicePixelRatio || 1, 1.5), W = Math.max(1, Math.round(w * r)), H = Math.max(1, Math.round(h * r)); if (canvas.width !== W || canvas.height !== H) { canvas.width = W; canvas.height = H; } return r; },
        /* items: { img, depth, rect: [x, y, w, h] in css px, a, tone }; o: { par, dz, t, gr, vig } */
        draw(items, o) {
          if (lost) return false;
          const r = Math.min(window.devicePixelRatio || 1, 1.5);
          gl.viewport(0, 0, canvas.width, canvas.height); gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
          gl.uniform2f(U.res, canvas.width, canvas.height);
          gl.uniform2f(U.par, o.par[0], o.par[1]); gl.uniform1f(U.dz, o.dz || 0); gl.uniform1f(U.t, o.t || 0);
          gl.uniform1f(U.gr, o.gr === undefined ? .035 : o.gr); gl.uniform1f(U.vig, o.vig === undefined ? .35 : o.vig);
          let drew = true;
          for (const it of items) {
            if (!it || it.a <= .002) continue;
            let ti = tex(it.img.currentSrc || it.img.src, it.img);
            if (!ti && it.img._prev) ti = tex(it.img._prev);
            const td = it.depth ? tex(it.depth) : null;
            if (!ti) { drew = false; continue; }
            gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, ti);
            gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, td || ti);
            gl.uniform1f(U.hasd, td ? 1 : 0);
            gl.uniform4f(U.rc, it.rect[0] * r, it.rect[1] * r, it.rect[2] * r, it.rect[3] * r);
            gl.uniform1f(U.a, it.a); gl.uniform1f(U.tone, it.tone || 0); gl.uniform1f(U.br, it.br || 1);
            gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
          }
          return drew;
        },
        free() { cache.forEach((e) => e.t && gl.deleteTexture(e.t)); cache.clear(); const x = gl.getExtension('WEBGL_lose_context'); if (x) x.loseContext(); lost = true; },
      };
    }
    /* a pointer over the page gives the pictures a little more of the room */
    const ptr = { x: 0, y: 0 };
    addEventListener('pointermove', (e) => { if (e.pointerType === 'mouse') { ptr.x = (e.clientX / innerWidth) * 2 - 1; ptr.y = (e.clientY / innerHeight) * 2 - 1; } }, { passive: true });
    return { support, make, ptr };
  })();
  const LIVE = !RM && GLX.support();
  // the depth maps are not used: a photograph is shown as itself, sharp and still
  const DEPTH = false;
  const TONE = { sepia: .62, paper: .12, dim: .08 };
  /* one living picture in a box: the canvas lies over the image, which stays underneath for the reader who cannot
     have the canvas, for zoom and for print. rect() says where the image is in the box. */
  /* a sharper copy of a picture, fetched only when the camera goes closer than the picture can carry */
  const hires = (img) => {
    if (!img || img._hi || !img.dataset.hi) return;
    img._hi = 1;
    const im = new Image();
    im.decoding = 'async';
    im.onload = () => { img._prev = img.currentSrc || img.src; img.removeAttribute('srcset'); img.src = im.src; request(); };
    im.src = img.dataset.hi;
  };
  /* how far a picture may be enlarged (css px per pixel of the file on the page), counting its sharper copy */
  const maxScale = (img, iw) => 1.5 * (+(img.dataset.fw || 0) || iw) / iw;
  function liveImg(host, img, o = {}) {
    if (!LIVE || !DEPTH || !host || !img) return null;
    const cv = d.createElement('canvas');
    cv.className = 'live-gl';
    img.after(cv);
    const G = GLX.make(cv);
    if (!G) { cv.remove(); return null; }
    onPage(() => G.free());
    let st = { p: 0 };
    loop(host, (now) => {
      const r = host.getBoundingClientRect();
      G.size(r.width, r.height);
      const q = o.rect ? o.rect(r) : coverRect(img, r);
      const k = o.move ? o.move(st.p, now) : { par: [Math.sin(now * .2) * .0025 + GLX.ptr.x * .008, Math.cos(now * .17) * .0018 + GLX.ptr.y * .005], dz: 0 };
      const drew = G.draw([{ img, depth: img.dataset.depth, rect: q, a: 1, tone: o.tone || 0, br: o.br || 1 }], Object.assign({ t: now, gr: .03, vig: o.vig === undefined ? .25 : o.vig }, k));
      host.classList.toggle('gl-on', drew);
    });
    return { set(p) { st.p = p; } };
  }
  function coverRect(img, r) {
    const iw = +img.getAttribute('width') || img.naturalWidth || 1600, ih = +img.getAttribute('height') || img.naturalHeight || 1000;
    const s = Math.max(r.width / iw, r.height / ih), w = iw * s, h = ih * s;
    const pos = (getComputedStyle(img).objectPosition || '50% 50%').split(' ').map((x) => parseFloat(x) / 100);
    return [(r.width - w) * (isNaN(pos[0]) ? .5 : pos[0]), (r.height - h) * (isNaN(pos[1]) ? .5 : pos[1]), w, h];
  }
  const relRect = (img) => (r) => { const q = img.getBoundingClientRect(); return [q.left - r.left, q.top - r.top, q.width, q.height]; };

  /* PHOTO STAGES — the chronicle's own pictures, large, with the camera moving to what the paragraph is about.
     Each step names a picture, a point on it (x, y in %) and a zoom; between steps the camera travels. */
  VIS.photos = (vis, el) => {
    const shots = $$('.sv-shot', vis).map((sh) => ({ el: sh, pic: $('.sv-pic', sh), img: $('img', sh), mode: sh.dataset.mode || 'cover', mk: $$('.sv-mk', sh) }));
    const steps = $$('.stage-step', el).map((x) => ({ shot: +(x.dataset.shot || 0), x: +(x.dataset.x || 50) / 100, y: +(x.dataset.y || 50) / 100, z: +(x.dataset.z || 1), vw: +(x.dataset.vw || 0), vh: +(x.dataset.vh || 0), fit: x.dataset.fit || null, mark: x.dataset.mark || '', slip: (x.dataset.slip || '').split(' ').filter(Boolean), legs: (x.dataset.legs || '').split(' ').filter(Boolean).map(Number), stops: (x.dataset.stops || '').split(' ').filter(Boolean), done: (x.dataset.done || '').split(' ').filter(Boolean).map(Number) }));
    const RT = $('.sv-route', vis) ? routeCtl(vis, steps) : null;
    const slips = $$('.sv-slip', vis), labs = $$('.sv-lab', vis);
    let lf = 0;
    if (!shots.length || !steps.length) return null;
    const nat = (sh) => [+sh.img.getAttribute('width') || sh.img.naturalWidth || 1600, +sh.img.getAttribute('height') || sh.img.naturalHeight || 1000];
    shots.forEach((sh) => { const [w, h] = nat(sh); sh.pic.style.width = w + 'px'; sh.pic.style.height = h + 'px'; });
    const R = el.dataset.side === 'right';
    let edge = null, SPL = false;
    const fitSplit = () => {
      const cs = $$('.stage-card', el).map((c) => c.getBoundingClientRect()).filter((q) => q.width > 0);
      edge = cs.length ? { l: Math.min(...cs.map((q) => q.left)), r: Math.max(...cs.map((q) => q.right)) } : null;
      SPL = !!el.closest('.chap') && splitNow() && !BOOK;
      if (!SPL) { vis.style.height = ''; return; }
      const W = vis.getBoundingClientRect().width || innerWidth, allC = steps.every((st) => (st.fit || shots[st.shot].mode) === 'contain' && !st.vw && st.z <= 1.05);
      const isMap = !!$('.sv-route', vis);
      const need = allC ? Math.max(...shots.map((sh) => { const [iw, ih] = nat(sh); return (W - 16) * ih / iw / .9; }))
        : isMap ? innerHeight * .58 : Math.max(...shots.map((sh) => { const [iw, ih] = nat(sh); return W * ih / iw / .86; }));
      vis.style.height = Math.round(clamp(need, innerHeight * .44, innerHeight * .6)) + 'px';
    };
    fitSplit(); listen(window, 'resize', fitSplit);
    // a picture is never blown up past what its pixels carry: an old small print that cannot fill the screen is shown
    // whole, as a print on the table, at the size it holds — not stretched into a blur
    const LIM = 1;
    const small = (sh, W, H) => { const [iw, ih] = nat(sh); return Math.max(W / iw, H / ih) > LIM * (+(sh.img.dataset.fw || 0) || iw) / iw; };
    const fitOf0 = (st, W, H) => { const sh = shots[st.shot], f = st.fit || sh.mode; return f === 'cover' && !sh.el.closest('.stage-map') && !sh.el.classList.contains('paper') && small(sh, W, H) ? 'contain' : f; };
    function place(k, zk, W, H) {
      const st = steps[k], sh = shots[st.shot], [iw, ih] = nat(sh), fit = fitOf0(st, W, H), split = SPL, wide = !split && W >= 760;
      let rx = 0, ry = 0, rw = W, rh = H;
      if (fit === 'contain') { if (wide) { rx = R ? W * .03 : W * .37; rw = W * .6; ry = H * .1; rh = H * .82;
          // a picture shown whole stays clear of the text cards beside it
          if (edge) { if (R) rw = Math.max(W * .3, Math.min(rw, edge.l - rx - 28)); else { const x0 = Math.max(rx, edge.r + 28); rw = Math.max(W * .3, W * .97 - x0); rx = x0; } } } else if (split) { rx = 8; rw = W - 16; ry = H * .05; rh = H * .9; } else { ry = 64; rh = H * .5; } }
      // on a phone a photograph is not cut to fill the frame: it may leave a thin dark edge rather than lose its people
      const cap = LIM * (+(sh.img.dataset.fw || 0) || iw) / iw;
      const s0 = fit === 'contain' ? Math.min(rw / iw, rh / ih, cap) : split && !sh.el.closest('.stage-map') ? Math.max(W / iw, H * .86 / ih) : Math.max(W / iw, H / ih);
      // a print shown whole stays whole: only a real close-up (a word on a document) goes nearer
      let z = fit === 'contain' && st.z < 1.5 ? 1 : st.z;
      if (st.vw) z = Math.max(1, Math.min((W * (wide ? .55 : .92) / s0) / st.vw, (H * (wide ? .8 : split ? .84 : .42) / s0) / st.vh));
      const sc = Math.min(s0 * z, Math.max(s0, fit === 'contain' ? cap : maxScale(sh.img, iw))) * zk, w = iw * sc, h = ih * sc;
      const tx = fit === 'contain' ? rx + rw / 2 : W * (wide ? (R ? .34 : st.vw ? .68 : .6) : .5), ty = fit === 'contain' ? ry + rh / 2 : H * (wide ? .5 : split ? .5 : st.vw ? .3 : .34);
      // a whole print is centred in its place; the focus point only matters when the camera goes close
      const fx = fit === 'contain' && z === 1 ? .5 : st.x, fy = fit === 'contain' && z === 1 ? .5 : st.y;
      let left = tx - fx * w, top = ty - fy * h;
      left = w >= W ? clamp(left, W - w, 0) : clamp(left, 0, W - w);
      top = h >= H ? clamp(top, H - h, 0) : clamp(top, 0, H - h);
      return { left, top, sc };
    }
    let lastI = -1, G = null;
    if (LIVE && DEPTH) {
      const cv = d.createElement('canvas');
      cv.className = 'sv-gl';
      vis.insertBefore(cv, vis.firstChild);
      G = GLX.make(cv);
      if (G) { el.classList.add('gl'); onPage(() => G.free()); }
    }
    return {
      draw(t, now, dt) {
        const r = vis.getBoundingClientRect(), W = r.width, H = r.height, n = steps.length;
        const items = [];
        const i = clamp(Math.floor(t), 0, n - 1), f = clamp(t - i), e = ease(clamp(f / .5)), p0 = Math.max(0, i - 1);
        const a = place(p0, 1 + .03, W, H), b = place(i, 1 + .035 * f, W, H);
        const same = steps[p0].shot === steps[i].shot;
        const fitOf = (st) => fitOf0(st, W, H), dip = !same && fitOf(steps[p0]) !== fitOf(steps[i]);
        if (b.sc * (window.devicePixelRatio || 1) > 1.1) hires(shots[steps[i].shot].img);
        const nx = steps[Math.min(n - 1, i + 1)];
        if (f > .5 && nx && place(Math.min(n - 1, i + 1), 1, W, H).sc * (window.devicePixelRatio || 1) > 1.1) hires(shots[nx.shot].img);
        shots.forEach((sh, k) => {
          let o = 0, q = null;
          if (k === steps[i].shot) { o = same ? 1 : dip ? clamp(e * 2 - 1) : e; q = same ? { left: lerp(a.left, b.left, e), top: lerp(a.top, b.top, e), sc: lerp(a.sc, b.sc, e) } : b; const ft = fitOf(steps[i]); if (sh.el.dataset.fit !== ft) sh.el.dataset.fit = ft; }
          else if (k === steps[p0].shot) { o = dip ? 1 - clamp(e * 2) : 1 - e; q = a; const ft = fitOf(steps[p0]); if (sh.el.dataset.fit !== ft) sh.el.dataset.fit = ft; }
          sh.el.style.opacity = o.toFixed(3);
          sh.el.style.visibility = o > .002 ? 'visible' : 'hidden';
          if (q) {
            sh.pic.style.transform = `translate3d(${q.left.toFixed(1)}px,${q.top.toFixed(1)}px,0) scale(${q.sc.toFixed(4)})`; sh.pic.style.setProperty('--k', (1 / q.sc).toFixed(4));
            if (G && o > .002) { const [iw, ih] = nat(sh); items.push({ img: sh.img, depth: sh.img.dataset.depth, rect: [q.left, q.top, iw * q.sc, ih * q.sc], a: o, tone: TONE[sh.el.classList[1]] || 0 }); }
          }
        });
        if (G) {
          G.size(W, H);
          const sway = Math.sin(now * .21) * .0025, bob = Math.cos(now * .17) * .0018;
          el.classList.toggle('gl-on', G.draw(items, { par: [sway + GLX.ptr.x * .008, bob + GLX.ptr.y * .005], dz: 0, t: now, gr: .03, vig: .28 }));
        }
        slips.forEach((x) => x.classList.toggle('on', steps[i].slip.includes(x.dataset.k) && (f > .12 || lastI === i && x.classList.contains('on'))));
        if (RT) RT(i, f, lerp(a.sc, b.sc, e));
        if (labs.length && ++lf % 12 === 0) labs.forEach((x) => {
          if (!x.classList.contains('on')) return;
          const q = x.getBoundingClientRect(), vr = vis.getBoundingClientRect();
          if (x.classList.contains('end') && q.left < vr.left + 6) { x.classList.remove('end'); x.classList.add('start', 'flipped'); }
          else if (x.classList.contains('start') && q.right > vr.right - 6) { x.classList.remove('start'); x.classList.add('end', 'flipped'); }
        });
        if (i !== lastI) {
          lastI = i;
          const m = steps[i].mark, set = m === 'all' ? null : m.split(' ').filter(Boolean);
          shots.forEach((sh) => sh.mk.forEach((x) => { x.classList.toggle('on', !!m && (set === null || set.includes(x.dataset.n))); x.classList.toggle('hi', !!set && set.includes(x.dataset.n)); }));
          if (t > .05) Sound.sfx('page');
        }
      },
    };
  };

  /* the route over a map picture: each leg drawn as its paragraph is read, the places named as they are reached */
  function routeCtl(vis, steps) {
    const legs = $$('.sv-route .leg', vis), here = $('.sv-route .here', vis), dots = $$('.sv-dot', vis), labs = $$('.sv-lab', vis);
    const done = steps[0] ? steps[0].done : [];
    const legStep = legs.map((_, k) => (done.includes(k) ? -2 : steps.findIndex((s) => s.legs.includes(k))));
    const stopStep = {};
    steps.forEach((s, k) => s.stops.forEach((key) => { if (!(key in stopStep)) stopStep[key] = k; }));
    const ends = {};
    legs.forEach((lg, k) => { (ends[lg.dataset.b] = ends[lg.dataset.b] || []).push(k); });
    const TL = legs.map((lg) => lg.getTotalLength());
    let last = -1;
    return (i, f, sc) => {
      const k = 1 / Math.max(.01, sc);
      const prog = legs.map((lg, q) => {
        const st = legStep[q];
        if (st === -2) return 1;
        if (st < 0 || st > i) return 0;
        if (st < i) return 1;
        const mine = steps[i].legs, j = mine.indexOf(q), m = mine.length, a0 = .12 + j * .6 / m;
        return ease(clamp((f - a0) / (.6 / m)));
      });
      let tip = null, tot = 0;
      legs.forEach((lg, q) => { lg.style.strokeDashoffset = (1 - prog[q]).toFixed(4); lg.style.strokeWidth = (3 * k).toFixed(2); lg.classList.toggle('old', legStep[q] >= 0 && legStep[q] < i && steps[i].legs.length > 0); if (prog[q] > 0 && prog[q] < 1) tip = q; tot += prog[q]; });
      const on = (key) => { const s = stopStep[key]; let v = s !== undefined && (s < i || (s === i && f > .06)); if (ends[key]) { const reached = ends[key].some((q) => prog[q] > .97); const pending = ends[key].some((q) => legStep[q] >= i && prog[q] <= .97); if (pending && !reached) v = false; if (reached) v = true; } return v; };
      dots.forEach((x) => x.classList.toggle('on', on(x.dataset.k)));
      labs.forEach((x) => x.classList.toggle('on', on(x.dataset.k)));
      if (tip !== null) { const pt = legs[tip].getPointAtLength(TL[tip] * prog[tip]); here.setAttribute('cx', pt.x.toFixed(1)); here.setAttribute('cy', pt.y.toFixed(1)); here.setAttribute('r', (6 * k).toFixed(2)); here.style.opacity = 1; }
      else here.style.opacity = 0;
      const kk = Math.round(tot * 4);
      if (kk !== last) { if (last >= 0 && kk > last && tip !== null) Sound.sfx('pen'); last = kk; }
    };
  }

  /* MAP STAGES — the journey drawn on the map of the country as the paragraphs that tell it are read */
  VIS.map = (vis, el) => {
    const svg = $('svg.sv-map', vis);
    if (!svg) return null;
    const legs = $$('.leg', svg), stops = $$('.stop', svg), here = $('.here', svg), land = $('.land', svg), wls = $$('.wl, .wl-gap', svg);
    const steps = $$('.stage-step', el).map((x) => ({ v: (x.dataset.view || '700 400 200').split(' ').map(Number), legs: (x.dataset.legs || '').split(' ').filter(Boolean).map(Number), stops: (x.dataset.stops || '').split(' ').filter(Boolean) }));
    const done = (el.querySelector('.stage-step') || {}).dataset ? ($('.stage-step', el).dataset.done || '').split(' ').filter(Boolean).map(Number) : [];
    const legStep = legs.map((_, k) => (done.includes(k) ? -2 : steps.findIndex((s) => s.legs.includes(k))));
    const stopStep = {};
    steps.forEach((s, k) => s.stops.forEach((key) => { if (!(key in stopStep)) stopStep[key] = k; }));
    const ends = {};
    legs.forEach((lg, k) => { ends[lg.dataset.b] = ends[lg.dataset.b] || []; ends[lg.dataset.b].push(k); });
    const TL = legs.map((lg) => lg.getTotalLength());
    const circ = stops.map((g) => [$('circle', g), $('text', g), +$('circle', g).getAttribute('cx'), +$('circle', g).getAttribute('cy')]);
    let lastK = -1;
    return {
      draw(t) {
        const r = vis.getBoundingClientRect(), asp = Math.max(.3, r.width / Math.max(1, r.height)), wide = r.width >= 760, n = steps.length;
        const i = clamp(Math.floor(t), 0, n - 1), f = clamp(t - i), e = ease(clamp(f / .45));
        const A = steps[Math.max(0, i - 1)].v, Bv = steps[i].v;
        const cx = lerp(A[0], Bv[0], e), cy = lerp(A[1], Bv[1], e), w = Math.exp(lerp(Math.log(A[2]), Math.log(Bv[2]), e)) * (wide ? 1 : 1.25), h = w / asp;
        const x0 = cx - w * (wide ? .62 : .5), y0 = cy - h * (wide ? .5 : .36);
        svg.setAttribute('viewBox', `${x0.toFixed(2)} ${y0.toFixed(2)} ${w.toFixed(2)} ${h.toFixed(2)}`);
        const px = w / Math.max(1, r.width);
        land.style.strokeWidth = (.9 * px).toFixed(3);
        wls.forEach((x) => { const k = +x.dataset.k, dd = k * 5.5 * px; x.style.strokeWidth = (x.classList.contains('wl') ? 2 * dd + .9 * px : 2 * dd - .9 * px).toFixed(3); });
        legs.forEach((lg) => { lg.style.strokeWidth = (2.6 * px).toFixed(3); });
        const prog = legs.map((lg, k) => {
          const s = legStep[k];
          if (s === -2) return 1;
          if (s < 0 || s > i) return 0;
          if (s < i) return 1;
          const mine = steps[i].legs, j = mine.indexOf(k), m = mine.length, a0 = .12 + j * .6 / m;
          return ease(clamp((f - a0) / (.6 / m)));
        });
        let tip = null, k2 = 0;
        legs.forEach((lg, k) => { lg.style.strokeDashoffset = (1 - prog[k]).toFixed(4); if (prog[k] > 0 && prog[k] < 1) tip = [lg, prog[k]]; k2 += prog[k]; });
        stops.forEach((g, k) => {
          const key = g.dataset.k, s = stopStep[key];
          let on = s !== undefined && (s < i || (s === i && f > .06));
          if (ends[key]) on = on && ends[key].some((q) => prog[q] > .97) || (s !== undefined && s < i && !ends[key].some((q) => legStep[q] >= i));
          if (ends[key] && ends[key].some((q) => prog[q] > .97)) on = true;
          g.classList.toggle('on', on);
          const [c, tx, x, y] = circ[k];
          c.setAttribute('r', (3.6 * px).toFixed(3));
          tx.setAttribute('x', (x + (+tx.dataset.dx) * 9 * px).toFixed(2)); tx.setAttribute('y', (y + (+tx.dataset.dy) * 15 * px + 4 * px).toFixed(2));
          tx.style.fontSize = (14 * px).toFixed(3) + 'px';
        });
        if (tip) { const [lg, q] = tip, pt = lg.getPointAtLength(TL[legs.indexOf(lg)] * q); here.setAttribute('cx', pt.x.toFixed(2)); here.setAttribute('cy', pt.y.toFixed(2)); here.setAttribute('r', (5 * px).toFixed(3)); here.style.opacity = 1; }
        else here.style.opacity = 0;
        const kk = Math.round(k2 * 4);
        if (kk !== lastK) { if (lastK >= 0 && kk > lastK && tip) Sound.sfx('pen'); lastK = kk; }
      },
    };
  };

  /* a paragraph read slowly: its sentences come up one at a time as they reach the reading line */
  SCENES.sentences = (el) => {
    const ss = $$('.sent', el);
    if (RM || BOOK || !ss.length || el.getBoundingClientRect().top < innerHeight * .8) return null;
    el.classList.add('armed');
    return (p, r, vh) => { ss.forEach((x) => { const q = x.getBoundingClientRect(); x.classList.toggle('on', q.top < vh * .86); }); };
  };
  /* figures that count up to themselves */
  SCENES.count = (el) => {
    const hs = $$('[data-count]', el);
    if (RM || BOOK || !hs.length || el.getBoundingClientRect().top < innerHeight * .9) return null;
    hs.forEach((h) => { h.textContent = '0'; });
    let done = false;
    return (p, r, vh) => {
      if (done || r.top > vh * .8) return;
      done = true;
      const t0 = performance.now();
      const step = (now) => { const k = ease(clamp((now - t0) / 1600)); hs.forEach((h, j) => { const v = +h.dataset.count; h.textContent = String(Math.round(v * clamp(k * (1 + j * .08)))); }); if (k < 1 && chap) requestAnimationFrame(step); };
      requestAnimationFrame(step); Sound.sfx('page');
    };
  };
  /* a flock of children on the years: each birth lights as the card is read, and a card points at its year */
  SCENES.births = (el) => {
    const dots = $$('.bt-d', el), cells = $$('[data-b]:not(.bt-d)', el);
    const by = {};
    dots.forEach((d) => { by[d.dataset.b] = d; });
    cells.forEach((c) => { const d = by[c.dataset.b]; if (!d) return; listen(c, 'pointerenter', () => d.classList.add('hi')); listen(c, 'pointerleave', () => d.classList.remove('hi')); listen(c, 'focusin', () => d.classList.add('hi')); listen(c, 'focusout', () => d.classList.remove('hi')); });
    if (RM || BOOK) { dots.forEach((d) => d.classList.add('on')); return null; }
    el.classList.add('armed');
    return (p, r, vh) => { cells.forEach((c) => { const d = by[c.dataset.b]; if (d) d.classList.toggle('on', c.getBoundingClientRect().top < vh * .86); }); };
  };
  /* lives drawn to scale, one after the other */
  /* the lives drawn to scale — and a year line that walks across them: each life begins as it is reached, and the
     two strandfogeds, grandfather and grandson, are joined by the years between them */
  SCENES.lives = (el) => {
    const L = $('.lives', el);
    if (RM || BOOK || !L || !L.dataset.a0) { el.classList.add('grown'); return null; }
    const a0 = +L.dataset.a0, a1 = +L.dataset.a1;
    const st = d.createElement('div'), tr = d.createElement('div');
    st.className = 'lv-stage'; tr.className = 'lv-track';
    const keep = $$(':scope > *', el).filter((x) => !x.matches('p'));
    el.insertBefore(tr, keep[0] || null);
    tr.appendChild(st);
    keep.forEach((x) => st.appendChild(x));
    const cur = d.createElement('div');
    cur.className = 'lv-cur'; cur.setAttribute('aria-hidden', 'true'); cur.innerHTML = '<b></b>';
    L.appendChild(cur);
    const yl = cur.firstChild;
    const pc = (x, k) => parseFloat(x.style.getPropertyValue(k)) || 0;
    const rows = $$(':scope > div', L).filter((x) => $('.life', x)).map((x) => { const lf = $('.life', x); return { x, i: $('i', lf), a: pc(lf, '--a'), b: pc(lf, '--b') }; });
    const marks = $$('.lv-m', L).map((m) => ({ m, x: pc(m, '--x') })), arcs = $$('.lv-arc', L).map((m) => ({ m, x: +m.dataset.at }));
    el.classList.add('sweep');
    let pinned = false, lastC = -1;
    const fit = () => {
      tr.style.height = '';
      const top = ($('.top') || {}).offsetHeight || 60;
      pinned = st.offsetHeight < innerHeight - top - 40;
      el.classList.toggle('pinned', pinned);
      if (pinned) tr.style.height = Math.round(st.offsetHeight + innerHeight * 1.1) + 'px';
    };
    fit(); listen(window, 'resize', () => { fit(); request(); });
    return (p, r, vh) => {
      let q;
      if (pinned) { const t = tr.getBoundingClientRect(); q = clamp((st.getBoundingClientRect().top - t.top) / Math.max(1, tr.clientHeight - st.offsetHeight)); }
      else { const t = st.getBoundingClientRect(); q = clamp((vh * .85 - t.top) / Math.max(1, t.height + vh * .2)); }
      const c = q * 100;
      L.style.setProperty('--c', c.toFixed(2) + '%');
      yl.textContent = Math.round(a0 + q * (a1 - a0));
      yl.style.transform = `translate(${(-q * 100).toFixed(1)}%, -100%)`;
      rows.forEach((w) => {
        const g = clamp((c - w.a) / Math.max(.01, w.b - w.a));
        w.i.style.transform = `scaleX(${g.toFixed(4)})`;
        w.x.classList.toggle('pre', c < w.a); w.x.classList.toggle('gone', c > w.b); w.x.classList.toggle('now', c >= w.a && c <= w.b);
        if (lastC >= 0 && lastC < w.a && c >= w.a) Sound.sfx('pen');
      });
      marks.forEach((w) => w.m.classList.toggle('on', c >= w.x));
      arcs.forEach((w) => { const on = c >= w.x; if (on && lastC >= 0 && lastC < w.x) Sound.sfx('toll'); w.m.classList.toggle('on', on); });
      el.classList.toggle('done', q > .995);
      lastC = c;
    };
  };
  /* a sequence of lines on a tall track: each comes up as the one before steps back */
  SCENES.ladder = (el) => {
    const rungs = $$(':scope > .rung', el);
    if (RM || BOOK || rungs.length < 2) return null;
    const stage = d.createElement('div');
    stage.className = 'rung-stage';
    rungs[0].before(stage);
    rungs.forEach((x) => stage.appendChild(x));
    el.classList.add('armed');
    let last = -1;
    return (p, r, vh) => {
      const n = rungs.length, q = clamp((vh * .55 - r.top) / Math.max(1, r.height - vh * .5)) * (n - .15), idx = Math.min(n - 1, Math.floor(q));
      rungs.forEach((x, j) => { const dd = j - q; x.style.setProperty('--d', dd.toFixed(3)); x.classList.toggle('now', j === idx); x.classList.toggle('past', j < idx); x.classList.toggle('next', j > idx); });
      if (idx !== last) { if (last >= 0 && idx > last) Sound.sfx('page'); last = idx; }
    };
  };
  /* chapter 6: the name's forms, set in motion. The father is Niels Thomsen; the farm name comes in from below,
     through the children, rises into his name, and the patronymic falls away letter by letter. The reader's scroll
     is the time between the papers. */
  SCENES.namemorph = (el) => {
    if (RM || BOOK) return null;
    let st;
    try { st = JSON.parse(el.dataset.states); } catch (e) { return null; }
    const N = st.length, base = st.find((x) => !x.kids) || st[0], kid = st.find((x) => x.kids);
    const farm = (st.find((x) => x.f) || {}).f || '';
    if (!farm || !kid || N < 3) return null;
    const stage = $('.nm-stage', el), whenEl = $('.nm-when', el), noteEl = $('.nm-note', el), stepsEl = $('.nm-steps', el);
    el.classList.add('on');
    const T = {};
    const mk = (id, text, cls) => {
      const t = d.createElement('span'); t.className = 'nm-tk ' + cls;
      Array.from(text).forEach((ch) => { const l = d.createElement('span'); l.className = 'nm-l'; l.textContent = ch; t.appendChild(l); });
      stage.appendChild(t); T[id] = { el: t, text, L: $$('.nm-l', t), w: 0 };
    };
    mk('G', base.g, 'g'); mk('P', base.p, 'p'); mk('KG', kid.g, 'kg'); mk('KP', kid.p, 'kp'); mk('F', farm, 'f');
    const ids = Object.keys(T);
    const lab = st.map((x) => { const e = d.createElement('span'); e.textContent = x.k; whenEl.appendChild(e); return e; });
    const nts = st.map((x) => { const e = d.createElement('span'); e.textContent = x.n || ''; noteEl.appendChild(e); return e; });
    const tks = st.map((x) => { const e = d.createElement('span'); e.innerHTML = `<i></i><b>${x.k.replace(/[<&]/g, '')}</b>`; stepsEl.appendChild(e); return e; });
    // which words stand on the father's line (A) and on the children's line (B) at each form
    let prevA = ['G', 'P'];
    const lines = st.map((x) => {
      if (x.kids) return { A: prevA.filter((q) => q !== 'F'), B: ['KG', 'KP', 'F'] };
      const A = ['G'].concat(x.p ? ['P'] : []).concat(x.f ? ['F'] : []); prevA = A; return { A, B: [] };
    });
    let FS = 80, KB = .42, Lay = [];
    const layout = () => {
      const W = stage.getBoundingClientRect().width;
      if (W < 10) return;
      const m = d.createElement('span'); m.className = 'nm-tk nm-meas'; m.style.fontSize = '100px'; stage.appendChild(m);
      ids.forEach((id) => { m.textContent = T[id].text; T[id].w = m.getBoundingClientRect().width / 100; });
      m.textContent = 'n n'; const two = m.getBoundingClientRect().width; m.textContent = 'nn'; const SP = (two - m.getBoundingClientRect().width) / 100 * 1.05;
      m.remove();
      const wide = Math.max(...lines.map((ln) => ln.A.reduce((a, id) => a + T[id].w, 0) + SP * (ln.A.length - 1)));
      FS = Math.min(W < 640 ? 64 : 124, (W * (W < 640 ? .985 : .94)) / wide); KB = W < 640 ? .56 : .42;
      stage.style.height = (FS * 1.95) + 'px';
      stage.style.setProperty('--u', (FS * 1.1).toFixed(1) + 'px');
      ids.forEach((id) => { T[id].el.style.fontSize = FS + 'px'; });
      Lay = lines.map((ln) => {
        const pos = {};
        const row = (list, k, y) => {
          const tot = list.reduce((a, id) => a + T[id].w * FS * k, 0) + SP * FS * k * (list.length - 1);
          let x = (W - tot) / 2;
          list.forEach((id) => { pos[id] = { x, y, k, o: 1 }; x += (T[id].w + SP) * FS * k; });
        };
        row(ln.A, 1, 0); row(ln.B, KB, FS * 1.2);
        return pos;
      });
      // the rule under the final form runs exactly under its words
      const last = Lay[N - 1], la = lines[N - 1].A, x0 = last[la[0]].x, x1 = last[la[la.length - 1]].x + T[la[la.length - 1]].w * FS;
      stage.style.setProperty('--ul', x0.toFixed(1) + 'px'); stage.style.setProperty('--uw', (x1 - x0).toFixed(1) + 'px');
      // a word not on the page at a given form waits where it will be (below, unseen) or stays where it was (gone)
      ids.forEach((id) => {
        for (let i = 0; i < N; i++) {
          if (Lay[i][id]) continue;
          let j = -1;
          for (let q = i + 1; q < N; q++) if (Lay[q][id] && Lay[q][id].o) { j = q; break; }
          if (j >= 0 && !(i > 0 && Lay[i - 1][id] && Lay[i - 1][id].o)) { const q = Lay[j][id]; Lay[i][id] = { x: q.x, y: q.y + FS * .55 * q.k, k: q.k, o: 0, wait: 1 }; continue; }
          for (let q = i - 1; q >= 0; q--) if (Lay[q][id]) { const z = Lay[q][id]; Lay[i][id] = { x: z.x, y: z.y + (id === 'P' ? 0 : FS * .3 * z.k), k: z.k, o: 0, gone: 1 }; break; }
          if (!Lay[i][id]) Lay[i][id] = { x: 0, y: 0, k: 1, o: 0 };
        }
      });
    };
    let P = 0, target = 0, fin = false;
    const draw = (p) => {
      if (!Lay.length) return;
      const k = Math.min(N - 2, Math.floor(p)), f = clamp(p - k), e = ease(f);
      ids.forEach((id) => {
        const t = T[id], a = Lay[k][id], b = Lay[k + 1][id];
        let fx = e, fy = e;
        const rising = Lay[k].F && Lay[k + 1].F && Lay[k].F.k !== Lay[k + 1].F.k;
        if (rising && (id === 'G' || id === 'P')) fx = fy = ease(clamp(f / .5));  // the father's name makes room first
        if (id === 'F' && rising) { fx = ease(clamp((f - .08) / .55)); fy = ease(clamp((f - .38) / .62)); }  // along under the line, then up into the place
        if (id === 'F' && a.k === b.k && Lay[k].P && Lay[k].P.o && !(Lay[k + 1].P && Lay[k + 1].P.o)) { fx = fy = ease(clamp((f - .38) / .62)); }  // it closes the gap once the patronymic has gone
        const x = lerp(a.x, b.x, fx), y = lerp(a.y, b.y, fy), sc = lerp(a.k, b.k, fx);
        let o = lerp(a.o, b.o, id === 'F' ? clamp(f * 1.6) : e);
        if (id === 'P') {
          const drop = a.o && b.gone, down = a.gone;
          t.L.forEach((l, i) => {
            const dd = drop ? clamp(f * 1.9 - i * .12) : down ? 1 : 0;
            l.style.transform = dd ? `translate3d(0,${(dd * dd * 1.1).toFixed(3)}em,0) rotate(${(dd * (i % 2 ? 16 : -12)).toFixed(1)}deg)` : '';
            l.style.opacity = (1 - dd).toFixed(3);
          });
          o = drop ? 1 : down ? 0 : o;
        }
        t.el.style.transform = `translate3d(${x.toFixed(1)}px,${y.toFixed(1)}px,0) scale(${sc.toFixed(4)})`;
        t.el.style.opacity = o.toFixed(3);
      });
      st.forEach((x, i) => {
        const o = clamp(1 - Math.abs(p - i) * 2.4);
        lab[i].style.opacity = o.toFixed(3); lab[i].style.transform = `translateY(${((i - p) * 10).toFixed(1)}px)`;
        nts[i].style.opacity = x.n ? o.toFixed(3) : 0;
        tks[i].classList.toggle('on', Math.round(p) === i); tks[i].classList.toggle('past', i < Math.round(p));
      });
      const f2 = p > N - 1.08;
      if (f2 !== fin) { fin = f2; el.classList.toggle('fin', fin); if (fin) Sound.sfx('page'); }
    };
    const relayout = () => { layout(); draw(P); };
    if (d.fonts && d.fonts.ready) d.fonts.ready.then(relayout); else relayout();
    listen(window, 'resize', relayout);
    loop(el, (now, dt) => {
      const nP = P + (target - P) * (1 - Math.pow(.86, dt / 16));
      if (Math.abs(nP - P) > .0005 || !Lay.length) { P = Math.abs(target - nP) < .001 ? target : nP; if (!Lay.length) layout(); draw(P); }
    });
    return (p, r, vh) => { target = clamp((vh * .22 - r.top) / Math.max(1, r.height - vh * .8)) * (N - 1); };
  };
  /* the name comes apart into its two words */
  SCENES.split = (el) => {
    if (RM || BOOK) { el.style.setProperty('--k', 1); return null; }
    return (p) => el.style.setProperty('--k', ease(clamp((p - .32) / .3)).toFixed(3));
  };
  /* the words of the deed are written out as they are read */
  SCENES.ink = (el) => {
    const box = $('img', el) && $('img', el).parentElement;
    if (!box || RM || BOOK || el.getBoundingClientRect().top < innerHeight * .8) return null;
    el.classList.add('armed');
    let fired = false;
    return (p) => { const k = clamp((p - .22) / .34); box.style.setProperty('--ink', k.toFixed(4)); if (k > .02 && !fired) { fired = true; Sound.sfx('pen'); } };
  };
  /* nine days in November */
  SCENES.days = (el) => {
    const on = $$('.dd.on', el);
    if (RM || BOOK || el.getBoundingClientRect().top < innerHeight * .8) { el.classList.add('lit'); return null; }
    el.classList.add('armed');
    let done = false;
    return (p, r, vh) => { if (done || r.top > vh * .66) return; done = true; el.classList.add('lit'); on.forEach((x, j) => later(() => { x.classList.add('hit'); Sound.sfx('toll'); }, 250 + j * 900)); };
  };
  /* a panorama walked along */
  SCENES.pano = (el) => {
    const img = $('.pano-in img', el);
    if (!img || RM || BOOK) return null;
    const L = liveImg($('.pano-in', el), img, { rect: relRect(img), vig: .15, move: (p, now) => ({ par: [Math.sin(now * .2) * .0025 + GLX.ptr.x * .006, GLX.ptr.y * .005], dz: 0 }) });
    return (p) => { const W = el.getBoundingClientRect().width, w = img.getBoundingClientRect().width; img.style.transform = `translate3d(${(-(w - W) * ease(clamp((p - .05) / .8))).toFixed(1)}px,0,0)`; if (L) L.set(p); };
  };

  /* a small odometer: four digit wheels */
  function makeOdo(el) {
    const cols = [];
    el.textContent = '';
    for (let i = 0; i < 4; i++) { const c = d.createElement('span'); c.className = 'dg'; for (let n = 0; n < 10; n++) { const x = d.createElement('i'); x.textContent = n; c.appendChild(x); } el.appendChild(c); cols.push(c); }
    let cur = null;
    return (y) => { y = Math.round(y); if (y === cur) return false; const s = String(y).padStart(4, '0'); cols.forEach((c, i) => { const n = +s[i]; Array.from(c.children).forEach((x) => { x.style.transform = `translateY(${-n * 100}%)`; }); }); cur = y; return true; };
  }
  /* ten years pass: the years run on beside the line that says so */
  SCENES.tick = (el) => {
    const o = $('.odo', el), a = +el.dataset.from, b = +el.dataset.to;
    if (!o) return null;
    const set = makeOdo(o);
    if (RM || BOOK) { set(b); return null; }
    set(a);
    return (p) => { if (set(lerp(a, b, ease(clamp((p - .3) / .35))))) Sound.sfx('odo'); };
  };
  /* the story winds back: the years run backwards as the chapter opens */
  SCENES.rewind = (el) => {
    const o = $('.odo', el), a = +el.dataset.from, b = +el.dataset.to;
    if (!o) return null;
    const set = makeOdo(o);
    if (RM || BOOK) { set(b); return null; }
    set(a);
    const t0 = performance.now() + 500;
    const step = (now) => { const k = ease(clamp((now - t0) / 2200)); if (set(lerp(a, b, k)) && k > 0) Sound.sfx('odo'); if (k < 1 && o.isConnected) requestAnimationFrame(step); };
    requestAnimationFrame(step);
    return null;
  };
  /* the quiet moment: when it is read, the rest of the page steps back */
  SCENES.spot = (el) => {
    if (RM || BOOK) return null;
    let on = false;
    onPage(() => root.classList.remove('spotlit'));
    const set = (v) => { if (v !== on) { on = v; el.classList.toggle('lit', v); root.classList.toggle('spotlit', v); } };
    const u = (p, r, vh) => { const c = r.top + r.height / 2; set(c > vh * .3 && c < vh * .66); };
    u.off = () => set(false);
    return u;
  };
  /* the breaking sea drawn under the heading */
  SCENES.wave = (el) => {
    const pa = $('path', el);
    if (!pa || RM || BOOK) return null;
    let fired = false;
    return (p) => { const k = ease(clamp((p - .2) / .35)); pa.style.strokeDashoffset = (1 - k).toFixed(4); if (k > .6 && !fired) { fired = true; Sound.sfx('breaker'); } };
  };
  /* three portraits side by side, one after the other */
  SCENES.triptych = (el) => {
    const fs = $$('figure', el);
    if (RM || BOOK || el.getBoundingClientRect().top < innerHeight * .8) return null;
    el.classList.add('armed');
    return (p, r, vh) => fs.forEach((f, i) => f.classList.toggle('on', r.top < vh * (.72 - i * .08)));
  };
  /* chapter 13: the record beside its columns — a field in the transcript lights its column on the page */
  SCENES.ltstrip = (el) => {
    const hl = $$('.lts-hl', el), fl = $$('.fld[data-c]', el), fig = $('.lts-fig', el);
    if (!hl.length || !fl.length) return null;
    let pinned = null, cur = -1;
    const show = (c) => { if (c === cur) return; cur = c; hl.forEach((x) => x.classList.toggle('on', +x.dataset.c === c)); fl.forEach((x) => x.classList.toggle('on', +x.dataset.c === c)); fig.classList.toggle('lit', c >= 0); };
    fl.forEach((x) => {
      listen(x, 'pointerenter', () => show(+x.dataset.c));
      listen(x, 'pointerleave', () => show(pinned === null ? -1 : pinned));
      listen(x, 'click', () => { pinned = pinned === +x.dataset.c ? null : +x.dataset.c; show(pinned === null ? -1 : pinned); Sound.sfx('page'); });
      listen(x, 'focus', () => show(+x.dataset.c));
    });
    hl.forEach((h) => listen(h, 'click', () => { const f = fl.find((x) => x.dataset.c === h.dataset.c); if (f) { f.scrollIntoView({ behavior: RM ? 'auto' : 'smooth', block: 'center' }); pinned = +h.dataset.c; show(pinned); } }));
    if (BOOK) return null;
    return (p, r, vh) => {
      if (pinned !== null || matchMedia('(hover:hover)').matches && fl.some((x) => x.matches(':hover'))) return;
      let c = -1;
      for (const x of fl) { const q = x.getBoundingClientRect(); if (q.top < vh * .62 && q.bottom > vh * .3) c = +x.dataset.c; }
      show(c);
    };
  };
  /* chapter 16: the name lights in the two of five who carry it */
  SCENES.glow = (el) => {
    if (RM || BOOK || el.getBoundingClientRect().top < innerHeight * .8) { el.classList.add('lit'); return null; }
    el.classList.add('armed');
    return (p, r, vh) => { if (r.top < vh * .6 && !el.classList.contains('lit')) { el.classList.add('lit'); Sound.sfx('chime'); } };
  };
  /* chapter 18: the name on the stern, as the owners changed it */
  SCENES.nameboard = (el) => {
    const ns = $$('.nb-n', el), ys = $$('.nb-years em', el), stern = $('.nb-stern', el), box = el.closest('.b') || el;
    if (!ns.length || !stern) return null;
    const N = ys.length;
    let cur = -1, t1 = null, t2 = null;
    const show = (i, fresh) => {
      ns.forEach((x, j) => { x.classList.toggle('on', j === i); x.classList.toggle('fresh', j === i && fresh); });
      ys.forEach((x, j) => x.classList.toggle('on', j === i));
      stern.classList.toggle('gone', i >= ns.length);
    };
    if (RM || BOOK) { show(0, false); return null; }
    show(0, false); cur = 0;
    // forwards, the old name is painted over and the new one lettered on; backwards it simply stands there again
    const go = (i) => {
      if (i === cur) return;
      clearTimeout(t1); clearTimeout(t2);
      const fwd = i > cur; cur = i;
      if (!fwd) { stern.classList.remove('sweep'); show(i, false); return; }
      stern.classList.remove('sweep'); void stern.offsetWidth; stern.classList.add('sweep');
      t1 = later(() => { show(i, true); Sound.sfx(i >= ns.length ? 'toll' : 'stamp'); }, 480);
      t2 = later(() => stern.classList.remove('sweep'), 1100);
    };
    return (p, r, vh) => {
      const q = box.getBoundingClientRect(), k = clamp((vh * .8 - q.top) / Math.max(1, q.height * .85));
      go(Math.min(N - 1, Math.floor(k * N)));
    };
  };
  /* chapter 18: the log of the grounding, the entries coming in at their times */
  SCENES.log = (el) => {
    const es = $$(':scope > div, :scope > p', el).slice(1);
    if (RM || BOOK || el.getBoundingClientRect().top < innerHeight * .8) return null;
    el.classList.add('armed');
    return (p, r, vh) => es.forEach((x) => { if (!x.classList.contains('in') && x.getBoundingClientRect().top < vh * .78) { x.classList.add('in'); Sound.sfx('telegraph'); } });
  };
  /* chapter 19: the postcard, turned over */
  SCENES.flip = (el) => {
    const fs = $$('figure', el);
    if (fs.length !== 2) return null;
    const card = d.createElement('div');
    card.className = 'pc-card';
    const inner = d.createElement('div');
    inner.className = 'pc-in';
    card.appendChild(inner);
    const faces = fs.map((f) => { const b = $('img', f).parentElement; return b; });
    const caps = fs.map((f) => $('figcaption', f));
    faces.forEach((b, i) => { b.classList.add('pc-face', i ? 'pc-back' : 'pc-front'); inner.appendChild(b); });
    const btn = d.createElement('button');
    btn.type = 'button'; btn.className = 'tool pc-turn'; btn.textContent = el.dataset.turn || '↻';
    fs[0].before(card); card.after(btn);
    const capBox = d.createElement('div'); capBox.className = 'pc-caps'; caps.forEach((c) => c && capBox.appendChild(c)); btn.after(capBox);
    fs.forEach((f) => f.remove());
    el.classList.add('armed');
    let manual = null, sh = false;
    const set = (k) => { inner.style.setProperty('--r', (k * 180).toFixed(1) + 'deg'); caps.forEach((c, i) => c && c.classList.toggle('on', i === (k > .5 ? 1 : 0))); if ((k > .5) !== sh) { sh = k > .5; Sound.sfx('page'); } };
    listen(btn, 'click', () => { manual = manual === null ? (sh ? 0 : 1) : 1 - manual; set(manual); });
    set(0);
    if (RM || BOOK) return null;
    return (p) => { if (manual === null) set(ease(clamp((p - .42) / .2))); };
  };
  /* chapter 20: the branches from Husby */
  SCENES.branches = (el) => {
    const ls = $$('.br-l', el), ps = $$('.br-p', el);
    if (RM || BOOK) { el.classList.add('done'); return null; }
    return (p) => { const k = clamp((p - .25) / .4); ls.forEach((l, i) => { const q = clamp(k * ls.length - i); l.style.strokeDashoffset = (1 - ease(q)).toFixed(3); ps[i + 1] && ps[i + 1].classList.toggle('on', q > .95); }); ps[0] && ps[0].classList.toggle('on', k > 0); };
  };
  /* chapter 21: three names line up on the one they share */
  SCENES.align = (el) => {
    if (RM || BOOK || el.getBoundingClientRect().top < innerHeight * .8) { el.classList.add('lit'); return null; }
    el.classList.add('armed');
    return (p, r, vh) => { if (r.top < vh * .55 && !el.classList.contains('lit')) { el.classList.add('lit'); Sound.sfx('chime'); } };
  };
  /* chapter 9: how far the two men drifted along the beach */
  SCENES.drift = (el) => {
    const d1 = $('.d1', el), d2 = $('.d2', el), walk = $('.walk', el), line = $('.line', el), gone = $('.gone', el);
    const tag = (k) => $('.dr-tag.' + k, el);
    const t0 = tag('t0'), t1 = tag('t1'), t2 = tag('t2'), t3 = tag('t3');
    if (RM || BOOK) { el.classList.add('done'); return null; }
    el.classList.add('armed');
    let rung = false;
    return (p) => {
      // the shorter drift ends first; the longer one runs on, the fishermen keeping pace along the beach
      const k2 = ease(clamp((p - .18) / .26)), k1 = ease(clamp((p - .18) / .5)), kl = ease(clamp((p - .7) / .1));
      d2.style.strokeDashoffset = (1 - k2).toFixed(4); d1.style.strokeDashoffset = (1 - k1).toFixed(4);
      walk.style.setProperty('--k', clamp(k1 * 1.02).toFixed(4));
      line.style.strokeDashoffset = (1 - kl).toFixed(4);
      gone.style.opacity = k2 > .98 ? 1 : 0;
      t0.classList.toggle('on', p > .1); t2.classList.toggle('on', k2 > .98); t1.classList.toggle('on', k1 > .98); t3.classList.toggle('on', kl > .9);
      if (kl > .9 && !rung) { rung = true; Sound.sfx('page'); } else if (kl < .5) rung = false;
    };
  };

  /* appendix B: one name at a time */
  SCENES.filter = (el) => {
    const grid = el.nextElementSibling, chips = $$('.chip', el);
    if (!grid) return null;
    const cells = $$('[data-f]', grid);
    chips.forEach((c) => listen(c, 'click', () => {
      const f = c.dataset.f;
      chips.forEach((x) => { x.classList.toggle('on', x === c); x.setAttribute('aria-pressed', x === c ? 'true' : 'false'); });
      cells.forEach((x) => { x.hidden = f !== '*' && x.dataset.f !== f; });
      Sound.sfx('page');
    }));
    return null;
  };
  /* appendix D: a search through the caveats and the whole catalogue of sources */
  SCENES.seek = (el) => {
    const inp = $('input', el), out = $('.seek-n', el), chap_ = el.closest('section') || d;
    const items = $$('.caveat, .src-row', chap_);
    const cat = $('details', chap_.querySelector('.src-row') ? chap_.querySelector('.src-row').closest('details') : chap_);
    const plain = new Map(items.map((x) => [x, x.textContent.toLowerCase()]));
    let t = null;
    const run = () => {
      const q = inp.value.trim().toLowerCase();
      $$('mark.seek-m', chap_).forEach((m) => m.replaceWith(d.createTextNode(m.textContent)));
      items.forEach((x) => x.normalize());
      if (!q) { items.forEach((x) => { x.hidden = false; }); out.textContent = ''; return; }
      let n = 0;
      items.forEach((x) => {
        const hit = plain.get(x).includes(q);
        x.hidden = !hit;
        if (!hit) return;
        n++;
        const w = d.createTreeWalker(x, NodeFilter.SHOW_TEXT);
        const hits = [];
        while (w.nextNode()) { const tn = w.currentNode, i = tn.textContent.toLowerCase().indexOf(q); if (i >= 0) hits.push([tn, i]); }
        hits.forEach(([tn, i]) => { const r = d.createRange(); r.setStart(tn, i); r.setEnd(tn, i + q.length); const m = d.createElement('mark'); m.className = 'seek-m'; try { r.surroundContents(m); } catch (e) { /* across elements */ } });
      });
      const det = $$('.src-row', chap_).some((x) => !x.hidden) && $$('.src-row', chap_)[0].closest('details');
      if (det && !det.open) det.open = true;
      out.textContent = (el.dataset.tpl || '{n}').replace('{n}', n);
    };
    listen(inp, 'input', () => { clearTimeout(t); t = setTimeout(run, 140); });
    return null;
  };
  /* a picture on a tall track: from one place on it back to the whole (chapter 5, the 1878 atlas sheet) — or in to one place */
  SCENES.zoomout = (el) => {
    const img = $('.pan-in img', el);
    if (!img) return null;
    const Z0 = parseFloat(el.dataset.z || '3'), ox = el.dataset.ox || '88', oy = el.dataset.oy || '46', IN = el.dataset.dir === 'in', CUT = el.dataset.cut === '1';
    const pin = $('.pan-in', el), track = $('.pan-track', el), iw = +img.getAttribute('width') || 1600, ihh = +img.getAttribute('height') || 1000;
    // the picture keeps its size before it has loaded, so nothing jumps when it arrives
    img.style.aspectRatio = iw + ' / ' + ihh;
    img.style.width = `min(94vw, 1500px, ${iw}px, calc((100svh - var(--top) - 40px) * ${(iw / ihh).toFixed(4)}))`;
    // a small picture is not held on a dark screen: like on a phone, it closes in while it passes
    let passing = false;
    el.style.setProperty('--ox', ox + '%'); el.style.setProperty('--oy', oy + '%');
    // phone: the frame is as tall as the picture needs, not a whole dark screen around a small print
    const fitH = () => {
      pin.style.height = ''; if (track) track.style.height = '';
      const ih = +img.getAttribute('height') || 1000, w0 = Math.min(innerWidth * .94, 1500, iw, (innerHeight - 100) * iw / ih);
      passing = !BOOK && !RM && (splitNow() || Math.min(Z0, maxScale(img, iw) * iw / w0) * w0 < innerWidth * .62);
      if (!passing) return;
      const h0 = img.offsetHeight > 10 ? img.offsetHeight : w0 * ih / iw;
      const h = Math.round(Math.min(h0 + 36, innerHeight));
      pin.style.height = h + 'px'; if (track) track.style.height = h + 'px';
    };
    if (!img.complete) listen(img, 'load', () => { fitH(); request(); });
    // on a phone the picture is not held: it closes in on its place while it passes up through the screen
    const phoneP = () => { const q = pin.getBoundingClientRect(), vh = innerHeight; return clamp((vh - q.top) / (vh * .9)); };
    fitH(); listen(window, 'resize', () => { fitH(); request(); });
    const set = (p, live) => {
      const w = img.offsetWidth || 1, h = img.offsetHeight || 1, W = pin.clientWidth, H = pin.clientHeight;
      const Z = Math.max(1, Math.min(Z0, maxScale(img, iw) * iw / w));
      const e = ease(clamp((p - .05) / .7));
      // a cut instead of a zoom: the whole picture, then — through a short dip — the place itself (no face passes by on the way)
      let z = IN ? lerp(1, Z, e) : lerp(Z, 1, e);
      if (CUT) { const a = clamp((p - .05) / .7); z = a < .5 ? lerp(1, 1.06, a / .5) : lerp(Z * .93, Z, (a - .5) / .5); pin.style.setProperty('--dip', clamp(1 - Math.abs(a - .5) / .07).toFixed(3)); }
      const k = Z > 1 ? (z - 1) / (Z - 1) : 0;
      const L0 = img.offsetLeft, T0 = img.offsetTop, fx = L0 + w * ox / 100, fy = T0 + h * oy / 100;
      let tx = (W / 2 - fx) * k, ty = (H * .52 - fy) * k;
      const sw = w * z, shh = h * z, left = fx - (fx - L0) * z + tx, top = fy - (fy - T0) * z + ty;
      // smaller than the frame: wholly inside it; larger: covering it — never cut on one side and open on the other
      tx += (sw >= W ? clamp(left, W - sw, 0) : clamp(left, 0, W - sw)) - left;
      ty += (shh >= H ? clamp(top, H - shh, 0) : clamp(top, 0, H - shh)) - top;
      img.style.setProperty('--z', z.toFixed(4)); img.style.setProperty('--tx', tx.toFixed(1) + 'px'); img.style.setProperty('--ty', ty.toFixed(1) + 'px');
      el.classList.toggle('done', e > .97);
      if (live && z * w / iw * (window.devicePixelRatio || 1) > 1.1) hires(img);
    };
    if (RM || BOOK) { set(1); return null; }
    set(0);
    const L = img.dataset.depth ? liveImg(pin, img, { rect: relRect(img), vig: 0 }) : null;
    return (p) => { if (passing) p = phoneP(); set(p, true); if (L) L.set(p); };
  };
  /* chapter 5: the five names, read out one at a time */
  SCENES.register = (el) => {
    const nm = $$('.nm', el);
    if (RM || BOOK || el.getBoundingClientRect().top < innerHeight) return null;
    el.classList.add('reg');
    let done = false;
    return (p, r, vh) => {
      if (done || r.top > vh * .6) return;
      done = true;
      nm.forEach((x, i) => later(() => { x.classList.add('on'); Sound.sfx('toll'); }, 300 + i * 1500));
    };
  };
  /* chapter 17: the crossing, drawn as the dated entries are read */
  SCENES.chart = (el) => {
    const run = el.parentElement, legs = $$('[data-leg]', run);
    const map = $('.sc-map', el), frame = $('.sc-frame', el), sheet = $('.sc-sheet', el);
    const out = $('.leg.out', el), back = $('.leg.back', el), boat = $('.boat', el);
    const P = { plan: $('.plan', el), e: $('.pt-e', el), h: $('.pt-h', el), t: $('.pt-t', el), o: $('.pt-o', el), storm: $('.sc-storm', el), p16: $('.p16', el), p31: $('.p31', el) };
    if (!map || !out) return null;
    const L0 = out.getTotalLength(), L1 = back.getTotalLength();
    const ds = el.dataset, LON0 = +ds.lon0, LAT1 = +ds.lat1, SX = +ds.sx, W = +ds.w, H = +ds.h;
    const merc = (lat) => Math.log(Math.tan(Math.PI / 4 + lat * Math.PI / 360)) * 180 / Math.PI;
    const imerc = (m) => (2 * Math.atan(Math.exp(m * Math.PI / 180)) - Math.PI / 2) * 180 / Math.PI;
    const MY1 = merc(LAT1);
    const px = (lon, lat) => [(lon - LON0) * SX, (MY1 - merc(lat)) * SX];
    const V = ds.views.split(';').map((v) => { const [a, b, c, e] = v.split(',').map(Number); const p0 = px(a, e), p1 = px(c, b); return [p0[0], p0[1], p1[0] - p0[0], p1[1] - p0[1]]; });
    const NS = 'http://www.w3.org/2000/svg';
    let last = '', st = -1, cw = 0, ch = 0;
    const measure = () => { cw = sheet.clientWidth; ch = sheet.clientHeight; };
    // a view to the box's own proportions, kept on the sheet
    const fit = (v) => {
      let [x, y, w, h] = v; const ar = cw / Math.max(1, ch);
      if (w / h > ar) { const nh = w / ar; y -= (nh - h) / 2; h = nh; } else { const nw = h * ar; x -= (nw - w) / 2; w = nw; }
      if (w > W) { x = (W - w) / 2; } else x = clamp(x, 0, W - w);
      if (h > H) { y = (H - h) / 2; } else y = clamp(y, 0, H - h);
      return [x, y, w, h];
    };
    const lerp = (a, b, t) => a.map((x, k) => x + (b[k] - x) * t);
    // the border of the sheet, drawn for the part of the sea in view: degrees at the lines, a bar for every ten minutes
    const drawFrame = (x, y, w, h) => {
      const s = cw / w, lonL = LON0 + x / SX, lonR = LON0 + (x + w) / SX, latT = imerc(MY1 - y / SX), latB = imerc(MY1 - (y + h) / SX);
      const B = 7, parts = [];
      const X = (lon) => ((lon - LON0) * SX - x) * s, Y = (lat) => ((MY1 - merc(lat)) * SX - y) * s;
      const pd = SX * s;                            // screen pixels to a degree of longitude
      const step = pd > 360 ? 1 / 12 : pd > 60 ? 1 / 6 : 1 / 2;   // five, ten or thirty minutes a bar
      const every = pd < 34 ? 2 : 1;
      for (let m = Math.floor(lonL / step) * step, k = Math.floor(lonL / step); m < lonR; m += step, k++) {
        const a = Math.max(0, X(m)), b = Math.min(cw, X(m + step));
        if (b > a && k % 2 === 0) parts.push(`<rect x="${a.toFixed(1)}" y="0" width="${(b - a).toFixed(1)}" height="${B}"/><rect x="${a.toFixed(1)}" y="${ch - B}" width="${(b - a).toFixed(1)}" height="${B}"/>`);
      }
      for (let m = Math.floor(latB / step) * step, k = Math.floor(latB / step); m < latT; m += step, k++) {
        const a = Math.max(0, Y(m + step)), b = Math.min(ch, Y(m));
        if (b > a && k % 2 === 0) parts.push(`<rect x="0" y="${a.toFixed(1)}" width="${B}" height="${(b - a).toFixed(1)}"/><rect x="${cw - B}" y="${a.toFixed(1)}" width="${B}" height="${(b - a).toFixed(1)}"/>`);
      }
      const deg = (v, pos, neg) => `${Math.abs(Math.round(v))}°${v < 0 ? ' ' + neg : v > 0 ? ' ' + pos : ''}`;
      for (let d0 = Math.ceil(lonL); d0 <= Math.floor(lonR); d0++) { if (d0 % every) continue; const xx = X(d0); if (xx > 24 && xx < cw - 24) parts.push(`<text x="${xx.toFixed(1)}" y="${B + 12}" text-anchor="middle">${deg(d0, ds.lonLbl, ds.lonLbl === 'Ø' ? 'V' : 'W')}</text>`); }
      for (let d0 = Math.ceil(latB); d0 <= Math.floor(latT); d0++) { const yy = Y(d0); if (yy > 20 && yy < ch - 20) parts.push(`<text x="${B + 4}" y="${(yy - 4).toFixed(1)}">${deg(d0, ds.latLbl, 'S')}</text>`); }
      parts.push(`<rect class="nl" x=".5" y=".5" width="${(cw - 1).toFixed(1)}" height="${(ch - 1).toFixed(1)}"/><rect class="nl" x="${B}" y="${B}" width="${(cw - 2 * B).toFixed(1)}" height="${(ch - 2 * B).toFixed(1)}"/>`);
      frame.setAttribute('viewBox', `0 0 ${cw.toFixed(1)} ${ch.toFixed(1)}`);
      frame.innerHTML = parts.join('');
    };
    const camera = (v) => {
      const [x, y, w, h] = fit(v);
      const key = [x, y, w, h].map((n) => n.toFixed(1)).join(' ');
      if (key === last) return;
      last = key;
      map.setAttribute('viewBox', key);
      map.style.setProperty('--k', (w / Math.max(1, cw)).toFixed(4));
      drawFrame(x, y, w, h);
    };
    measure();
    listen(window, 'resize', () => { measure(); last = ''; });
    const place = (i, f) => {
      el.dataset.st = i;
      P.plan.classList.toggle('on', i >= 0);
      P.storm.classList.toggle('on', i >= 0 && i < 2);
      P.h.classList.toggle('on', i >= 1); P.t.classList.toggle('on', i >= 1);
      const go = i < 2 ? 0 : i === 2 ? f : 1, ret = i < 4 ? 0 : i === 4 ? f : 1;
      out.style.strokeDashoffset = (1 - go).toFixed(4);
      back.style.strokeDashoffset = (1 - ret).toFixed(4);
      P.p16.classList.toggle('on', go > .12); P.p31.classList.toggle('on', ret > .5);
      P.o.classList.toggle('on', i >= 2 && go > .95);
      P.o.classList.toggle('meet', i === 3);
      P.e.classList.toggle('on', i >= 5);
      let pt;
      if (i >= 4) pt = back.getPointAtLength(L1 * ret); else if (i >= 2) pt = out.getPointAtLength(L0 * go); else pt = out.getPointAtLength(0);
      boat.setAttribute('transform', `translate(${pt.x.toFixed(1)},${pt.y.toFixed(1)})`);
      boat.classList.toggle('on', i >= 2);
      // the camera: from the view of the entry before to the view of this one, in the first part of its reading
      const a = V[Math.max(0, i - 1)], b = V[Math.max(0, i)];
      let v = lerp(a, b, ease(clamp(f / .45)));
      // at sea the camera keeps the boat in view
      if ((i === 2 || i === 4) && f > .45) { const c = [pt.x - v[2] / 2, pt.y - v[3] / 2, v[2], v[3]]; v = lerp(v, c, .35); }
      camera(v);
      if (i !== st) { if (st >= 0 && i > st) Sound.sfx(i === 3 ? 'chime' : 'page'); st = i; }
    };
    el._print = () => { measure(); last = ''; place(legs.length - 1, 1); camera(V[0]); };
    if (RM || BOOK) { el._print(); el.classList.add('done'); return null; }
    return (p, r, vh) => {
      if (sheet.clientWidth !== Math.round(cw) || sheet.clientHeight !== Math.round(ch)) { measure(); last = ''; }
      let i = -1, f = 0;
      for (let k = 0; k < legs.length; k++) {
        const q = legs[k].getBoundingClientRect();
        if (q.top < vh * .5) { i = k; const nx = legs[k + 1] ? legs[k + 1].getBoundingClientRect().top : q.top + 400; f = clamp((vh * .5 - q.top) / Math.max(1, nx - q.top)); } else break;
      }
      place(i, f);
    };
  };


  function scenes() {
    // pictures in the big scenes are fetched a little before they are reached, so none of them arrives blank
    if ('IntersectionObserver' in window) {
      const io = new IntersectionObserver((es) => es.forEach((en) => {
        if (!en.isIntersecting) return;
        io.unobserve(en.target);
        $$('img[loading="lazy"]', en.target).forEach((im) => { im.loading = 'eager'; if (im.decode) im.decode().catch(() => {}); });
      }), { rootMargin: '160% 0px 160% 0px' });
      $$('.stage, .pan-fig, .pano-fig, .cards, .nextprev').forEach((x) => io.observe(x));
      onPage(() => io.disconnect());
    }
    $$('[data-scene]').forEach((el) => {
      const f = SCENES[el.dataset.scene];
      if (!f) return;
      try { const u = f(el); if (u) live.push({ el, u }); } catch (e) { /* a scene must never break the page */ }
    });
  }

  /* one-shot sounds tied to places in the text, and the silences */
  function cues() {
    if (!('IntersectionObserver' in window)) return;
    const fired = new WeakSet();
    const io = observe((es) => es.forEach((e) => {
      if (!e.isIntersecting || fired.has(e.target)) return;
      fired.add(e.target); Sound.sfx(e.target.dataset.sfx);
    }), { rootMargin: '-38% 0px -38% 0px' });
    $$('main [data-sfx]').forEach((x) => io.observe(x));
    const hushEls = $$('main [data-hush]');
    Sound.hush(false);
    if (!hushEls.length) return;
    const seen = new Set();
    const judge = () => Sound.hush(Array.from(seen).some((x) => x.tagName !== 'DETAILS' || x.open));
    const ho = observe((es) => { es.forEach((e) => { if (e.isIntersecting) seen.add(e.target); else seen.delete(e.target); }); judge(); }, { rootMargin: '-30% 0px -30% 0px' });
    hushEls.forEach((x) => { ho.observe(x); if (x.tagName === 'DETAILS') listen(x, 'toggle', judge); });
  }

  /* =====================================================================================
     SCROLL LOOP
     ===================================================================================== */
  let ticking = false, lastY = scrollY, lastSave = 0;
  function update() {
    ticking = false;
    const y = scrollY, vh = innerHeight, dy = y - lastY;
    root.classList.toggle('scrolled', y > 40);
    const pm = $('#printmenu');
    if (!root.classList.contains('lock') && !(pm && !pm.hidden)) {
      if (y > 520 && dy > 8) root.classList.add('hide-top');
      else if (dy < -8 || y < 300) root.classList.remove('hide-top');
    }
    lastY = y;
    let p;
    if (chap) { const r = chap.getBoundingClientRect(); p = clamp((vh * .25 - r.top) / Math.max(1, r.height - vh * .5)); }
    else { const H = root.scrollHeight - vh; p = H > 0 ? clamp(y / H) : 0; }
    const prog = $('.prog');
    if (prog) prog.style.setProperty('--p', p.toFixed(4));
    if (arts.length > 1) {
      let a = arts[0];
      for (const x of arts) if (x.getBoundingClientRect().top < vh * .4) a = x;
      if (a !== curArt) {
        curArt = a;
        const n = $('.crumb .n'), t = $('.crumb .t');
        if (n && a.dataset.cn) n.textContent = a.dataset.cn;
        if (t && a.dataset.ct) t.textContent = a.dataset.ct;
        if (a.dataset.amb) Sound.amb(a.dataset.amb);
        root.dataset.world = a.dataset.world || root.dataset.world;
      }
    }
    Rail.frame(vh);
    // every scene's place is read in one pass before any of them writes, so the page is laid out once a frame
    const rs = live.map((s) => s.el.getBoundingClientRect());
    live.forEach((s, k) => {
      const r = rs[k];
      if (r.bottom < -60 || r.top > vh + 60) { if (s.u.off) s.u.off(); return; }
      const span = r.height - vh;
      s.u(span > 10 ? clamp(-r.top / span) : clamp((vh - r.top) / (vh + r.height)), r, vh);
    });
    if (chap && !BOOK && p > .02 && performance.now() - lastSave > 1500) {
      lastSave = performance.now();
      const lab = $('.crumb .n'), t = $('.crumb .t');
      store.set('silk-last-' + LANG, JSON.stringify({ u: location.pathname, l: [lab && lab.textContent, t && t.textContent].filter(Boolean).join(' · '), p: +p.toFixed(3) }));
      try { history.replaceState(Object.assign({}, history.state, { y: scrollY }), ''); } catch (e) { /* ignore */ }
    }
  }
  const request = () => { if (!ticking) { ticking = true; requestAnimationFrame(update); } };

  /* =====================================================================================
     DIALOGS AND READING TOOLS
     ===================================================================================== */
  let lastFocus = null;
  function openDialog(el) { lastFocus = d.activeElement; el.hidden = false; root.classList.add('lock'); const c = $('[data-close].tool', el) || $('[data-close]', el); c && c.focus({ preventScroll: true }); }
  function closeDialog(el) { if (!el || el.hidden) return; el.hidden = true; if (!isMenuOpen()) root.classList.remove('lock'); if (lastFocus) lastFocus.focus({ preventScroll: true }); }
  const isMenuOpen = () => { const m = $('#menu'); return !!(m && !m.hidden); };

  function setTab(k) {
    const menu = $('#menu'); if (!menu) return;
    $$('[data-tab]', menu).forEach((b) => b.setAttribute('aria-selected', String(b.dataset.tab === k)));
    $$('.mpanel', menu).forEach((p) => { p.hidden = p.id !== 'mp-' + k; });
    store.set('silk-tab', k);
  }
  let menuFocus = null;
  function setMenu(open, tab) {
    const menu = $('#menu'), btn = $('[data-act="menu"]');
    if (!menu) return;
    if (open === undefined) open = menu.hidden;
    if (open) setTab(tab || store.get('silk-tab') || 'tl');
    menu.hidden = !open;
    if (btn) btn.setAttribute('aria-expanded', String(open));
    root.classList.toggle('lock', open);
    root.classList.toggle('menu-open', open);
    if (open) {
      menuFocus = d.activeElement; root.classList.remove('hide-top');
      const panel = $('.mpanel:not([hidden])', menu);
      const cur = panel && ($('[aria-current="page"]', panel) || $('a', panel));
      if (cur) { cur.focus({ preventScroll: true }); cur.scrollIntoView({ block: 'center' }); }
      Sound.sfx('page');
    } else if (menuFocus && d.contains(menuFocus)) menuFocus.focus({ preventScroll: true });
  }
  function setPM(open) {
    const pm = $('#printmenu'), btn = $('[data-act="print"]');
    if (!pm) return;
    if (open === undefined) open = pm.hidden;
    pm.hidden = !open;
    if (btn) btn.setAttribute('aria-expanded', String(open));
    if (open) { const f = $('button:not([hidden]),a', pm); f && f.focus({ preventScroll: true }); }
  }

  const cache = {};
  function data(name) {
    const k = name + '.' + LANG;
    if (!cache[k]) cache[k] = fetch(ASSETS + 'data/' + k + '.json').then((r) => { if (!r.ok) throw new Error(String(r.status)); return r.json(); });
    return cache[k];
  }
  function openPerson(a) {
    const key = a.dataset.person, drawer = $('#drawer');
    const here = d.getElementById('person-' + key);
    if (here && !(drawer && drawer.contains(here)) && !a.closest('#menu')) return false; // the card is on this page: let the link go there
    if (!drawer) return false;
    const box = $('.drawer-body', drawer);
    box.innerHTML = `<p class="m-s uc c-mut">${UI.loading || '…'}</p>`;
    openDialog(drawer); Sound.sfx('page');
    data('personer').then((P) => {
      if (!P[key]) throw new Error('missing');
      box.innerHTML = P[key];
      const art = $('article', box); if (art) art.removeAttribute('id');
      if (UI.person_all) { const more = d.createElement('a'); more.className = 'pop-more'; more.href = a.getAttribute('href'); more.textContent = UI.person_all + ' →'; box.appendChild(more); }
      $('.drawer-panel', drawer).scrollTop = 0;
    }).catch(() => { closeDialog(drawer); location.href = a.href; });
    return true;
  }

  let popFor = null;
  function placePop(a) {
    const pop = $('#pop');
    const r = a.getBoundingClientRect(), w = pop.offsetWidth, h = pop.offsetHeight;
    const x = clamp(r.left + scrollX + r.width / 2 - w / 2, scrollX + 12, scrollX + innerWidth - w - 12);
    let y = r.bottom + scrollY + 10;
    if (r.bottom + h + 24 > innerHeight && r.top - h - 12 > 0) y = r.top + scrollY - h - 10;
    pop.style.left = x + 'px'; pop.style.top = y + 'px';
  }
  function openSource(a) {
    const pop = $('#pop');
    if (!pop) return false;
    const id = a.dataset.s, b = $('.pop-body', pop), more = $('.pop-more', pop);
    b.innerHTML = `<b class="sid">${id}</b><span class="m-s c-mut">${UI.loading || '…'}</span>`;
    more.href = a.getAttribute('href');
    pop.hidden = false; placePop(a); popFor = a; Sound.sfx('tick');
    data('kilder').then((K) => { if (popFor !== a) return; b.innerHTML = `<b class="sid">${id}</b>` + (K[id] || ''); placePop(a); })
      .catch(() => { if (popFor === a) { pop.hidden = true; popFor = null; location.href = a.href; } });
    return true;
  }
  function closePop() { const pop = $('#pop'); if (pop && !pop.hidden) { pop.hidden = true; popFor = null; } }

  /* THE PICTURE VIEWER — a picture lifts off the page into the dark and is shown whole, at the size its file can carry;
     the wheel, a pinch or a tap takes it closer, down to the grain of the paper, and a drag moves over it. The arrows
     turn through the chapter's pictures in order. The sharpest copy there is is fetched while the picture opens. */
  const LB = (() => {
    let lb = null, stage, big, capEl, numEl, list = [], idx = 0, cur = null, nw = 1, nh = 1, s = 1, sFit = 1, sMax = 2, x = 0, y = 0, token = 0;
    const ptrs = new Map();
    let pinch = null, drag = null, moved = 0, downAt = 0, keysOn = false, onPic = false;
    const box = () => { const r = stage.getBoundingClientRect(); return { W: r.width, H: r.height, L: r.left, T: r.top }; };
    const put = (smooth) => {
      big.classList.toggle('anim', !!smooth && !RM);
      big.style.transform = `translate3d(${x.toFixed(1)}px,${y.toFixed(1)}px,0) scale(${s.toFixed(5)})`;
      stage.classList.toggle('zoomed', s > sFit * 1.02);
    };
    const bound = () => {
      const { W, H } = box(), w = nw * s, h = nh * s;
      x = w <= W ? (W - w) / 2 : clamp(x, W - w, 0);
      y = h <= H ? (H - h) / 2 : clamp(y, H - h, 0);
    };
    const fit = () => {
      const { W, H } = box(), m = W < 640 ? 10 : 44;
      // whole on the screen, never blown up past half again what the file holds
      sFit = Math.min((W - 2 * m) / nw, (H - 2 * m) / nh, 1.5);
      sMax = Math.max(sFit * 3.2, 2);
    };
    const zoomAt = (cx, cy, ns, smooth) => {
      const { L, T } = box();
      ns = clamp(ns, sFit, sMax);
      const px = cx - L, py = cy - T;
      x = px - (px - x) * ns / s; y = py - (py - y) * ns / s; s = ns;
      bound(); put(smooth);
    };
    const toggleAt = (cx, cy) => { if (s > sFit * 1.02) { s = sFit; bound(); put(true); } else zoomAt(cx, cy, Math.max(sFit * 2.6, Math.min(1, sMax)), true); Sound.sfx('tick'); };
    const size = (w, h) => { nw = w; nh = h; big.style.width = w + 'px'; big.style.height = h + 'px'; };
    const capOf = (img) => {
      const fig = img.closest('figure'), c = fig && $('figcaption', fig);
      const t = c ? c.textContent : (img.closest('.stage') && img.alt) || img.alt || '';
      return t.replace(/\s+/g, ' ').trim();
    };
    const best = (img) => img.dataset.fuld || img.dataset.hi || img.currentSrc || img.src;
    function show(img, from) {
      cur = img; const my = ++token;
      const n0 = img.naturalWidth || +img.getAttribute('width') || 1600, h0 = img.naturalHeight || +img.getAttribute('height') || 1000;
      const fw = +(img.dataset.fw || 0);
      if (fw && !img.dataset.fuld) size(fw, fw * h0 / n0); else size(n0, h0);
      big.src = img.currentSrc || img.src; big.alt = img.alt || '';
      const want = best(img);
      if (want && !big.src.endsWith(want.replace(/^\.\.?\//, ''))) {
        const hi = new Image(); hi.decoding = 'async';
        hi.onload = () => {
          if (my !== token || lb.hidden) return;
          const r = hi.naturalWidth / nw;
          if (Math.abs(r - 1) > .01) { const cx = x + nw * s / 2, cy = y + nh * s / 2; size(hi.naturalWidth, hi.naturalHeight); s /= r; fit(); x = cx - nw * s / 2; y = cy - nh * s / 2; bound(); put(false); }
          big.src = hi.src;
        };
        hi.src = want;
      }
      capEl.textContent = capOf(img);
      numEl.textContent = list.length > 1 ? `${idx + 1} / ${list.length}` : '';
      lb.classList.toggle('one', list.length < 2);
      fit(); s = sFit; bound();
      const r = from && img.getBoundingClientRect();
      if (r && r.width > 4 && r.bottom > 0 && r.top < innerHeight && !RM) {
        // it lifts off from where it lies on the page
        const b = box(), fs = x, ft = y, fsc = s;
        s = r.width / nw; x = r.left - b.L; y = r.top - b.T + (r.height - nh * s) / 2; put(false);
        void big.offsetWidth;
        s = fsc; x = fs; y = ft; put(true);
      } else put(false);
      // the neighbours are fetched now, so the arrows are quick
      [list[idx + 1], list[idx - 1]].forEach((q) => { if (q) { const im = new Image(); im.src = best(q); } });
    }
    function go(dir) {
      if (list.length < 2) return;
      idx = (idx + dir + list.length) % list.length;
      big.classList.add('swap');
      later(() => { show(list[idx], false); big.classList.remove('swap'); }, RM ? 0 : 160);
      Sound.sfx('page');
    }
    function open(img) {
      if (!lb) return;
      list = $$('main img[data-zoom]').filter((q) => q.getBoundingClientRect().width > 0 || q === img);
      idx = Math.max(0, list.indexOf(img));
      openDialog(lb);
      lb.classList.remove('on'); void lb.offsetWidth; lb.classList.add('on');
      show(img, true);
      Sound.sfx('page');
    }
    function close() {
      if (!lb || lb.hidden) return;
      const img = cur, r = img && img.getBoundingClientRect();
      lb.classList.remove('on');
      if (r && r.width > 4 && r.bottom > 0 && r.top < innerHeight && !RM) {
        const b = box(); s = r.width / nw; x = r.left - b.L; y = r.top - b.T + (r.height - nh * s) / 2; put(true);
      }
      token++;
      later(() => { closeDialog(lb); big.removeAttribute('src'); big.classList.remove('anim'); }, RM ? 0 : 380);
    }
    function init() {
      lb = $('#lb');
      if (!lb || lb.dataset.v) return;
      lb.dataset.v = '1';
      stage = $('.lb-stage', lb); big = $('img', stage); capEl = $('.lb-cap', lb); numEl = $('.lb-n', lb);
      $$('[data-lb]', lb).forEach((bt) => bt.addEventListener('click', (e) => { e.stopPropagation(); go(+bt.dataset.lb); }));
      stage.addEventListener('wheel', (e) => { e.preventDefault(); zoomAt(e.clientX, e.clientY, s * Math.exp(-e.deltaY * (e.ctrlKey ? .01 : .0018)), false); }, { passive: false });
      stage.addEventListener('pointerdown', (e) => {
        stage.setPointerCapture(e.pointerId); ptrs.set(e.pointerId, [e.clientX, e.clientY]);
        if (ptrs.size === 1) { drag = { x0: e.clientX, y0: e.clientY, x, y }; moved = 0; downAt = performance.now(); onPic = e.target === big; }
        if (ptrs.size === 2) { const [a, b2] = [...ptrs.values()]; pinch = { d: Math.hypot(a[0] - b2[0], a[1] - b2[1]), m: [(a[0] + b2[0]) / 2, (a[1] + b2[1]) / 2], s, x, y }; drag = null; moved = 99; }
      });
      stage.addEventListener('pointermove', (e) => {
        if (!ptrs.has(e.pointerId)) return;
        ptrs.set(e.pointerId, [e.clientX, e.clientY]);
        if (pinch && ptrs.size >= 2) {
          const [a, b2] = [...ptrs.values()], dd = Math.hypot(a[0] - b2[0], a[1] - b2[1]), m = [(a[0] + b2[0]) / 2, (a[1] + b2[1]) / 2];
          const { L, T } = box(), ns = clamp(pinch.s * dd / Math.max(1, pinch.d), sFit * .9, sMax);
          x = m[0] - L - (pinch.m[0] - L - pinch.x) * ns / pinch.s; y = m[1] - T - (pinch.m[1] - T - pinch.y) * ns / pinch.s; s = ns;
          bound(); put(false);
        } else if (drag) {
          const dx = e.clientX - drag.x0, dy = e.clientY - drag.y0; moved = Math.max(moved, Math.abs(dx) + Math.abs(dy));
          if (s > sFit * 1.02) { x = drag.x + dx; y = drag.y + dy; bound(); put(false); stage.classList.add('grab'); }
          else if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy) * 1.5 && e.pointerType !== 'mouse') { drag = null; go(dx < 0 ? 1 : -1); }
        }
      });
      const up = (e) => {
        if (!ptrs.has(e.pointerId)) return;
        ptrs.delete(e.pointerId); stage.classList.remove('grab');
        if (ptrs.size < 2 && pinch) { pinch = null; if (s < sFit) { s = sFit; bound(); put(true); } return; }
        if (ptrs.size === 0 && drag && moved < 7 && performance.now() - downAt < 400) {
          if (onPic) toggleAt(e.clientX, e.clientY); else close();
        }
        drag = null;
      };
      stage.addEventListener('pointerup', up); stage.addEventListener('pointercancel', up);
      if (keysOn) return;
      keysOn = true;
      d.addEventListener('keydown', (e) => {
        if (!lb || lb.hidden) return;
        if (e.key === 'ArrowRight') { e.preventDefault(); go(1); }
        else if (e.key === 'ArrowLeft') { e.preventDefault(); go(-1); }
        else if (e.key === '+' || e.key === '=') { const b = box(); zoomAt(b.L + b.W / 2, b.T + b.H / 2, s * 1.4, true); }
        else if (e.key === '-') { const b = box(); zoomAt(b.L + b.W / 2, b.T + b.H / 2, s / 1.4, true); }
        else if (e.key === '0') { s = sFit; bound(); put(true); }
      });
      addEventListener('resize', () => { if (lb && !lb.hidden) { const k = s / sFit; fit(); s = clamp(sFit * k, sFit, sMax); bound(); put(false); } });
    }
    return { open, close, init };
  })();
  const openLightbox = (img) => LB.open(img);
  function lightbox() { LB.init(); }

  /* open a closed <details> (and reveal) around an anchor target */
  function uncover(id) {
    const t = id && d.getElementById(id);
    if (!t) return null;
    for (let p = t; p; p = p.parentElement) if (p.tagName === 'DETAILS' && !p.open) p.open = true;
    for (let p = t; p; p = p.parentElement) if (p.hasAttribute && p.hasAttribute('data-rv')) p.classList.add('in');
    return t;
  }
  function hashTarget(smooth) {
    const id = decodeURIComponent(location.hash.slice(1));
    if (!id) return false;
    const t = uncover(id);
    if (t) setTimeout(() => t.scrollIntoView({ block: 'start', behavior: smooth && !RM ? 'smooth' : 'auto' }), 40);
    return !!t;
  }
  addEventListener('hashchange', () => hashTarget(true));

  /* print: every note and every "read more" open, every reveal shown */
  let openedForPrint = [];
  /* on paper a picture stage becomes a run of pictures, each in front of the passage it belongs to; where the camera
     went close to a document, the paper shows the same detail cut out beneath it */
  function flattenStages() {
    $$('.stage[data-vis="photos"]:not(.stage-map)').forEach((st) => {
      const shots = $$('.sv-shot', st), seen = new Set();
      if (!shots.length) return;
      $$('.stage-step', st).forEach((step) => {
        const i = +(step.dataset.shot || 0), sh = shots[i], img = sh && $('.sv-pic img', sh);
        if (!img) return;
        const src = img.currentSrc || img.src, z = +(step.dataset.z || 1);
        let fig = null;
        if (!seen.has(i)) {
          seen.add(i);
          fig = d.createElement('figure'); fig.className = 'pr-shot pr-only' + (sh.classList.contains('sepia') ? ' sepia' : '');
          const im = d.createElement('img'); im.src = src; im.alt = img.alt || ''; fig.appendChild(im);
        } else if (sh.classList.contains('paper') && z >= 1.8 && img.naturalWidth) {
          // a strip of the page at the camera's own scale, centred where it looked
          const AR = 2.6, ai = img.naturalWidth / img.naturalHeight, zz = Math.min(z, 4);
          const x = +(step.dataset.x || 50) / 100, y = +(step.dataset.y || 50) / 100, hf = zz * AR / ai;
          const L = Math.min(0, Math.max(1 - zz, .5 - x * zz)), T = Math.min(0, Math.max(1 - hf, .5 - y * hf));
          fig = d.createElement('figure'); fig.className = 'pr-detail pr-only';
          fig.style.aspectRatio = String(AR);
          const im = d.createElement('img'); im.src = src; im.alt = '';
          im.style.cssText = `width:${(zz * 100).toFixed(2)}%;left:${(L * 100).toFixed(2)}%;top:${(T * 100).toFixed(2)}%`;
          fig.appendChild(im);
        }
        if (fig) step.prepend(fig);
      });
      st.classList.add('pr-flat');
    });
  }
  function unflattenStages() { $$('.pr-only').forEach((x) => x.remove()); $$('.pr-flat').forEach((x) => x.classList.remove('pr-flat')); }
  function prepPrint() {
    if (!$('.pr-flat')) flattenStages();
    $$('.sea-chart').forEach((x) => { if (x._print) x._print(); });
    // a family tree wider than the sheet is set smaller so it fits between the margins (otherwise the browser shrinks every page)
    $$('[data-pan]').forEach((el) => { const w = el.scrollWidth; if (w > 640) { el.dataset.przoom = '1'; el.style.zoom = (640 / w).toFixed(3); } });
    openedForPrint = $$('details:not([open])'); openedForPrint.forEach((x) => { x.open = true; });
    $$('[data-rv]').forEach((x) => x.classList.add('in'));
    $$('.route .leg, .route .stop, .reg .nm').forEach((x) => x.classList.add('on'));
    root.classList.add('printing');
    // on paper a chapter is set exactly as it is in the printable book: every scene at rest, every picture flat on the page
    if (!BOOK) { body.classList.add('bookpage', 'as-book'); }
    $$('img[loading="lazy"]').forEach((x) => { x.loading = 'eager'; });
  }
  function afterPrint() { unflattenStages(); $$('[data-przoom]').forEach((el) => { el.style.zoom = ''; delete el.dataset.przoom; }); openedForPrint.forEach((x) => { x.open = false; }); openedForPrint = []; root.classList.remove('printing'); body.classList.remove('as-book'); if (!body.classList.contains('as-book') && !BOOK) body.classList.remove('bookpage'); }
  addEventListener('beforeprint', prepPrint);
  addEventListener('afterprint', afterPrint);

  /* the language switch keeps the reader's place */
  function currentAnchor() {
    const el = d.elementFromPoint(innerWidth / 2, innerHeight * .4);
    let x = el && el.closest('[id]');
    while (x && (/^(main|titel|title)$/.test(x.id) || x === chap || x.matches('article, section[data-chap]'))) x = x.parentElement && x.parentElement.closest('[id]');
    return x && x !== chap && !x.matches('main, body') ? x.id : '';
  }

  /* the family tree is wider than the screen: centre it, let it be dragged */
  function pans() {
    const els = $$('main [data-pan]');
    if (!els.length) return;
    const centre = () => els.forEach((el) => { if (el.dataset.touched) return; const max = el.scrollWidth - el.clientWidth; if (max > 0) el.scrollLeft = max / 2; });
    centre(); later(centre, 600); listen(window, 'load', centre); listen(window, 'resize', centre);
    els.forEach((el) => {
      let down = false, x0 = 0, l0 = 0, moved = false;
      listen(el, 'pointerdown', (e) => { if (e.pointerType !== 'mouse') return; down = true; moved = false; x0 = e.clientX; l0 = el.scrollLeft; el.dataset.touched = '1'; });
      listen(window, 'pointerup', () => { down = false; el.classList.remove('drag'); });
      listen(el, 'pointermove', (e) => { if (!down) return; if (Math.abs(e.clientX - x0) > 4) { moved = true; el.classList.add('drag'); } el.scrollLeft = l0 - (e.clientX - x0); });
      listen(el, 'click', (e) => { if (moved) { e.preventDefault(); e.stopPropagation(); moved = false; } }, true);
      listen(el, 'touchstart', () => { el.dataset.touched = '1'; }, { passive: true });
    });
    $$('main [data-pan-btn]').forEach((b) => listen(b, 'click', () => {
      const t = $(b.getAttribute('data-pan-btn'), b.closest('section') || d); if (!t) return;
      t.dataset.touched = '1'; t.scrollBy({ left: b.dataset.dir === 'r' ? 460 : -460, behavior: RM ? 'auto' : 'smooth' }); Sound.sfx('tick');
    }));
  }

  /* 1948 ⟷ 2025 */
  function fades() {
    $$('main img[data-fade]').forEach((img) => {
      const box = img.parentElement && img.parentElement.parentElement;
      const inp = box && $('input[type=range]', box), lab = box && $('[data-fade-label]', box);
      if (!inp) return;
      const yrs = (inp.getAttribute('aria-label') || '').match(/\d{4}/g) || [];
      let last = +inp.value;
      const set = () => {
        const v = +inp.value;
        img.style.opacity = (v / 100).toFixed(2);
        if (lab && yrs.length === 2) lab.textContent = v < 50 ? yrs[0] : yrs[1];
        Sound.scratch(clamp(Math.abs(v - last) / 6)); last = v;
        clearTimeout(inp._t); inp._t = setTimeout(() => Sound.scratch(0), 120);
      };
      listen(inp, 'input', set); set();
    });
  }

  /* the cover: pick up where the reader left off */
  /* the other language opens at the same place: the same block of the same chapter, the same line of it at the same height */
  function langPos() {
    const el = d.elementFromPoint(innerWidth / 2, innerHeight * .4), sec = el && el.closest('section[data-chap]');
    if (!sec || !sec.id) return null;
    let b = el.closest('.b');
    while (b && b.parentElement && b.parentElement.closest('.b') && sec.contains(b.parentElement.closest('.b'))) b = b.parentElement.closest('.b');
    const bs = $$('.b', sec), i = b ? bs.indexOf(b) : -1, r = (i >= 0 ? b : sec).getBoundingClientRect();
    const q = { s: sec.id, i, f: +((innerHeight * .4 - r.top) / Math.max(1, r.height)).toFixed(4) };
    if (b) {
      // the nearest named place before this block, and how many blocks after it: stable when the two languages differ in length
      const F = Node.DOCUMENT_POSITION_FOLLOWING;
      const ids = $$('[id]', sec).filter((x) => x === b || (!x.contains(b) && (x.compareDocumentPosition(b) & F)));
      const an = ids[ids.length - 1];
      if (an) { q.a = an.id; q.k = an === b ? 0 : bs.filter((x) => (an.compareDocumentPosition(x) & F) && !an.contains(x) && (x === b || (x.compareDocumentPosition(b) & F))).length; }
    }
    return q;
  }
  function langRestore() {
    let q = null;
    try { q = JSON.parse(store.get('silk-langpos') || 'null'); } catch (e) { q = null; }
    if (!q || q.u !== location.pathname) return false;
    store.del('silk-langpos');
    const sec = d.getElementById(q.s);
    if (!sec) return false;
    const pick = () => {
      const bs = $$('.b', sec), an = q.a && d.getElementById(q.a);
      if (an && sec.contains(an)) {
        if (!q.k) return an.closest('.b') || an;
        const F = Node.DOCUMENT_POSITION_FOLLOWING, after = bs.filter((x) => (an.compareDocumentPosition(x) & F) && !an.contains(x));
        if (after[q.k - 1]) return after[q.k - 1];
      }
      return q.i >= 0 && bs[q.i] ? bs[q.i] : sec;
    };
    const put = () => { const t = pick(), r = t.getBoundingClientRect(); scrollTo(0, scrollY + r.top + r.height * clamp(q.f, 0, 1) - innerHeight * .4); };
    put(); later(put, 80); later(put, 400);
    return true;
  }
  function resume() {
    let s = null;
    try { s = JSON.parse(store.get('silk-last-' + LANG) || 'null'); } catch (e) { s = null; }
    const cont = $('main [data-continue]');
    if (cont && s && s.u && s.p > .02 && s.p < .985) {
      cont.href = s.u; cont.hidden = false;
      if (s.l) { const sp = d.createElement('span'); sp.className = 'go-sub'; sp.textContent = s.l; cont.appendChild(sp); }
    }
    let r = null;
    try { r = JSON.parse(store.get('silk-resume') || 'null'); } catch (e) { r = null; }
    if (r && chap && r.u === location.pathname && !location.hash) {
      store.del('silk-resume');
      const go = () => { const rect = chap.getBoundingClientRect(), vh = innerHeight; scrollTo(0, scrollY + rect.top - vh * .25 + r.p * Math.max(1, rect.height - vh * .5)); };
      later(go, 60);
      return true;
    }
    return false;
  }

  /* =====================================================================================
     NAVIGATION — chapters open inside the same page, so the sound and the reader's settings carry on
     ===================================================================================== */
  const pages = new Map();
  const isPage = (u) => {
    if (u.origin !== location.origin || !u.href.startsWith(EDITION)) return false;
    const rest = u.pathname.slice(new URL(EDITION).pathname.length);
    if (/^(en\/)?print\//.test(rest)) return false;              // the print edition is its own kind of page
    return /(\/|index\.html)$/.test(u.pathname) || rest === '';
  };
  function fetchPage(href) {
    const key = href.split('#')[0];
    if (!pages.has(key)) {
      const p = fetch(key, { credentials: 'same-origin' }).then((r) => { if (!r.ok) throw new Error(String(r.status)); return r.text(); });
      p.catch(() => pages.delete(key));
      pages.set(key, p);
      if (pages.size > 12) pages.delete(pages.keys().next().value);
    }
    return pages.get(key);
  }
  function headSwap(doc) {
    d.title = doc.title || d.title;
    const sel = 'meta[name="description"],link[rel="canonical"],link[rel="alternate"],meta[property^="og:"],meta[name="robots"],script[type="application/ld+json"]';
    $$(sel, d.head).forEach((x) => x.remove());
    $$(sel, doc.head).forEach((x) => d.head.appendChild(d.importNode(x, true)));
  }
  function attrs(doc) {
    const j = doc.getElementById('silk-attrs');
    if (j) { try { return JSON.parse(j.textContent); } catch (e) { /* fall through */ } }
    const a = (el) => Object.fromEntries(Array.from(el.attributes).map((x) => [x.name, x.value]));
    return { html: a(doc.documentElement), body: a(doc.body) };
  }
  let navigating = 0;
  /* THE CURTAIN — between two pages a sheet of the next page's ground comes up over the old one, carrying where the
     reader is going, and lifts off the new page. The sound goes on underneath. */
  const WORLD_BG = { paper: '#f2ebdc', dune: '#f1e2d7', sea: '#e2eae8', storm: '#0e1c26', night: '#0f1624', archive: '#17191a' };
  function curtain(label) {
    if (RM) return null;
    let c = $('#curtain');
    if (!c) { c = d.createElement('div'); c.id = 'curtain'; c.setAttribute('aria-hidden', 'true'); c.innerHTML = '<div class="cu-in"><span class="cu-k"></span><span class="cu-t"></span></div>'; d.documentElement.appendChild(c); }
    const [k, t] = label || ['', ''];
    $('.cu-k', c).textContent = k || ''; $('.cu-t', c).textContent = t || '';
    c.className = ''; void c.offsetWidth; c.className = 'in';
    return c;
  }
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));
  async function go(href, opt = {}) {
    const u = new URL(href, location.href), id = ++navigating;
    const link = opt.link;
    const lab = link ? [($('.m-s', link) || {}).textContent || '', ($('.np-t, .tl-t, .t, .card-t', link) || link).textContent.trim()] : null;
    const cu = opt.push !== false ? curtain(lab) : null;
    if (cu) cu.style.background = WORLD_BG[root.dataset.world] || WORLD_BG.paper;
    Sound.sfx('page');
    let text;
    try { text = await fetchPage(u.href); } catch (e) { location.href = u.href; return; }
    if (id !== navigating) return;
    const doc = new DOMParser().parseFromString(text, 'text/html');
    if (!doc.getElementById('main')) { location.href = u.href; return; }
    if (cu) {
      const w = (attrs(doc).html || {})['data-world'];
      cu.style.background = WORLD_BG[w] || WORLD_BG.paper;
      cu.dataset.world = w || 'paper';
      if (!lab) { const tt = (doc.title || '').split(' — ')[0].split(': '); $('.cu-k', cu).textContent = tt.length > 1 ? tt[0] : ''; $('.cu-t', cu).textContent = tt[tt.length - 1]; }
      await wait(520);
      if (id !== navigating) return;
    }
    if (opt.push !== false) {
      try { history.replaceState(Object.assign({}, history.state, { y: scrollY }), ''); history.pushState({ y: 0 }, '', u.href); } catch (e) { location.href = u.href; return; }
    }
    const swap = () => {
      unmount();
      headSwap(doc);
      const A = attrs(doc);
      ['lang', 'data-world'].forEach((k) => { if (A.html && A.html[k] != null) root.setAttribute(k, A.html[k]); });
      Array.from(body.attributes).forEach((x) => body.removeAttribute(x.name));
      Object.entries(A.body || {}).forEach(([k, v]) => body.setAttribute(k, v));
      // the page's own script and its styles stay (where a host puts the head into the body, the stylesheet lives there)
      const keep = (n) => n.nodeType === 1 && ((n.tagName === 'SCRIPT' && /ny\.js/.test(n.src || '')) || n.tagName === 'LINK' || n.tagName === 'STYLE' || n.tagName === 'META' || n.tagName === 'TITLE');
      Array.from(body.childNodes).forEach((n) => { if (!keep(n)) n.remove(); });
      const mine = $('script[src*="ny.js"]', body);
      Array.from(doc.body.childNodes).forEach((n) => {
        if (n.nodeType === 1 && n.tagName === 'SCRIPT' && (/ny\.js/.test(n.getAttribute('src') || '') || !n.type || n.type === 'text/javascript')) return;
        if (n.nodeType === 1 && (n.tagName === 'LINK' || n.tagName === 'STYLE' || n.tagName === 'META' || n.tagName === 'TITLE')) return;
        body.insertBefore(d.importNode(n, true), mine);
      });
      root.classList.remove('swap-out', 'hide-top');
      if (cu) { cu.className = 'out'; later(() => { cu.className = ''; }, 900); }
      const y = opt.y || 0;
      scrollTo(0, y);
      if (!y && !u.hash) { const m = $('#main'); if (m && FRAMED) try { m.scrollIntoView({ block: 'start' }); } catch (e) { /* ignore */ } }
      mount(u.hash ? true : false);

      const h = $('h1', $('#main'));
      if (h) { h.setAttribute('tabindex', '-1'); h.focus({ preventScroll: true }); }
    };
    swap();
  }
  addEventListener('popstate', (e) => { go(location.href, { push: false, y: (e.state && e.state.y) || 0 }); });
  try { history.scrollRestoration = 'manual'; } catch (e) { /* ignore */ }
  const warm = (e) => {
    const a = e.target.closest && e.target.closest('a[href]');
    if (!a || a.target || a.hasAttribute('download')) return;
    const u = new URL(a.href, location.href);
    if (isPage(u) && u.href.split('#')[0] !== location.href.split('#')[0]) fetchPage(u.href);
  };
  d.addEventListener('pointerover', warm, { passive: true });
  d.addEventListener('touchstart', warm, { passive: true });

  /* =====================================================================================
     CLICKS AND KEYS
     ===================================================================================== */
  d.addEventListener('click', (e) => {
    const mod = e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button > 0;
    const q = e.target.closest('button.q');
    if (q) {
      const n = d.getElementById(q.getAttribute('aria-controls'));
      if (!n) return;
      const open = q.getAttribute('aria-expanded') !== 'true';
      q.setAttribute('aria-expanded', open ? 'true' : 'false'); n.classList.toggle('open', open);
      Sound.sfx(open ? 'tick' : 'tock'); request();
      return;
    }
    const tab = e.target.closest('[data-tab]');
    if (tab) { setTab(tab.dataset.tab); Sound.sfx('tick'); return; }
    const act = e.target.closest('[data-act]');
    if (act) {
      const a = act.dataset.act;
      if (a === 'sound') { Sound.toggle(); store.set('silk-sound', Sound.on ? '1' : '0'); Sound.amb(body.dataset.amb); if (Sound.on) Sound.sfx('chime'); paintSound(); return; }
      if (a === 'menu') { setPM(false); setMenu(); return; }
      if (a === 'timeline') { setPM(false); setMenu(true, 'tl'); return; }
      if (a === 'print') { setPM(); return; }
      if (a === 'print-now') {
        setPM(false); prepPrint();
        // every picture is on the page before the print dialog opens (or after six seconds, whichever comes first)
        const wait = $$('img').filter((x) => !x.complete).map((x) => new Promise((ok) => { x.addEventListener('load', ok, { once: true }); x.addEventListener('error', ok, { once: true }); }));
        Promise.race([Promise.all(wait), new Promise((ok) => setTimeout(ok, 6000))]).then(() => { try { window.print(); } catch (err) { /* printing unavailable */ } });
        return;
      }
      if (a === 'overlay') {
        const fig = act.closest('figure') || act.parentElement.parentElement, ov = fig && $('[data-overlay]', fig);
        if (!ov) return;
        const shown = ov.style.opacity === '1';
        ov.style.opacity = shown ? '0' : '1';
        ov.style.transition = 'opacity .5s';
        if (UI.overlay_on) act.textContent = shown ? UI.overlay_on : UI.overlay_off;
        act.setAttribute('aria-pressed', String(!shown)); Sound.sfx('tick');
        return;
      }
    }
    if (e.target.closest('[data-close]')) { const dlg = e.target.closest('.drawer,.lb'); if (dlg) (dlg.id === 'lb' ? LB.close() : closeDialog(dlg)); else if (e.target.closest('#menu')) setMenu(false); return; }
    const pm = $('#printmenu'), pop = $('#pop');
    if (pm && !pm.hidden && !e.target.closest('#printmenu')) setPM(false);
    if (pop && !pop.hidden && !e.target.closest('#pop') && !e.target.closest('a.sref')) closePop();
    if (mod || BOOK) return;
    const sref = e.target.closest('a.sref');
    if (sref && openSource(sref)) { e.preventDefault(); return; }
    const pn = e.target.closest('a[data-person]');
    if (pn && openPerson(pn)) { e.preventDefault(); return; }
    const img = e.target.closest('img[data-zoom]');
    if (img && !img.closest('a')) { e.preventDefault(); openLightbox(img); return; }
    const a = e.target.closest('a[href]');
    if (!a || a.target || a.hasAttribute('download')) return;
    const raw = a.getAttribute('href');
    if (a.hasAttribute('data-lang-link')) {
      const q = langPos(), id = currentAnchor() || (q && q.s) || '';
      a.href = raw.split('#')[0] + (id ? '#' + id : '');
      if (q) { q.u = new URL(a.href, location.href).pathname; store.set('silk-langpos', JSON.stringify(q)); }
    }
    if (a.hasAttribute('data-continue')) { try { const s = JSON.parse(store.get('silk-last-' + LANG) || 'null'); if (s) store.set('silk-resume', JSON.stringify(s)); } catch (err) { /* ignore */ } }
    const u = new URL(a.href, location.href);
    if (u.href.split('#')[0] === location.href.split('#')[0]) {
      // a place on this page
      if (u.hash.length > 1) {
        const id = decodeURIComponent(u.hash.slice(1)), t = d.getElementById(id);
        if (t && t.closest('details:not([open])')) { e.preventDefault(); uncover(id); history.pushState(history.state, '', '#' + id); t.scrollIntoView({ block: 'start', behavior: RM ? 'auto' : 'smooth' }); }
      }
      if (e.target.closest('#menu')) setMenu(false);
      return;
    }
    if (isPage(u)) { e.preventDefault(); if (isMenuOpen()) setMenu(false); go(u.href); }
  });
  d.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    const pop = $('#pop'), lb = $('#lb'), drawer = $('#drawer'), pm = $('#printmenu');
    if (pop && !pop.hidden) { const a = popFor; closePop(); a && a.focus({ preventScroll: true }); }
    else if (lb && !lb.hidden) LB.close();
    else if (drawer && !drawer.hidden) closeDialog(drawer);
    else if (isMenuOpen()) setMenu(false);
    else if (pm && !pm.hidden) { setPM(false); const b = $('[data-act="print"]'); b && b.focus(); }
  });

  /* =====================================================================================
     MOUNT / UNMOUNT / BOOT
     ===================================================================================== */
  function unmount() {
    cleanups.forEach((f) => { try { f(); } catch (e) { /* ignore */ } });
    cleanups = []; live = []; closePop();
    root.classList.remove('lock', 'menu-open', 'rv', 'printing');
  }
  function mount(hasHash) {
    body = d.body;
    LANG = root.lang === 'en' ? 'en' : 'da';
    UI = readJSON('#silk-ui');
    BOOK = body.classList.contains('bookpage');
    chap = $('.chaps') || $('article.chap');
    arts = $$('article.chap');
    curArt = null;
    if (BOOK) $$('details').forEach((x) => { x.open = true; });
    reveals();
    kinetic();
    rail();
    scenes();
    cues();
    pans();
    fades();
    lightbox();
    $$('main details').forEach((x) => listen(x, 'toggle', () => { if (!root.classList.contains('printing')) Sound.sfx('page'); request(); }));
    if (FRAMED) $$('[data-act="print-now"]').forEach((b) => { b.hidden = true; });
    paintSound();
    Sound.amb(body.dataset.amb);
    const resumed = resume() || langRestore();
    if (hasHash !== false && !resumed) hashTarget(false);
    lastY = scrollY;
    request();
  }
  function boot() {
    mount(true);
    if (store.get('silk-sound') === '1') {
      // sound was on last time; browsers only allow it to start from a gesture
      const arm = (e) => {
        if (e && e.target && e.target.closest && e.target.closest('[data-act="sound"]')) return;
        removeEventListener('pointerdown', arm); removeEventListener('keydown', arm);
        if (!Sound.on) { Sound.start(); Sound.amb(body.dataset.amb); paintSound(); }
      };
      addEventListener('pointerdown', arm); addEventListener('keydown', arm);
    }
    try { history.replaceState(Object.assign({}, history.state, { y: scrollY }), ''); } catch (e) { /* ignore */ }
    addEventListener('scroll', request, { passive: true });
    addEventListener('resize', request);
    addEventListener('load', request);
  }
  if (d.readyState === 'loading') d.addEventListener('DOMContentLoaded', boot); else boot();
  window.SilkNy = { Sound, SCENES, request, go };
})();
