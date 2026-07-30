// Kører krøniken igennem i flere bredder og rapporterer vandret overløb,
// kontrastfejl, for små berøringsmål og konsolfejl.
// Brug:  node tools/tjek.js [url]
const { chromium } = require('playwright');

const URL = process.argv[2] || 'http://localhost:8765/index.html';
const BREDDER = [360, 390, 430, 768, 1024, 1180, 1440, 1920];

const revision = async (page) => page.evaluate(async () => {
  const kill = document.createElement('style');
  kill.textContent = '*{transition:none!important;animation:none!important}[data-reveal]{opacity:1!important;transform:none!important}';
  document.head.appendChild(kill);
  await new Promise((r) => setTimeout(r, 500));

  const px = (v) => v.match(/[\d.]+/g).map(Number);
  const lum = (c) => {
    const f = (x) => { x /= 255; return x <= 0.04045 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4; };
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]);
  };
  const over = (fg, bg) => { const a = fg.length > 3 ? fg[3] : 1; return [0, 1, 2].map((i) => fg[i] * a + bg[i] * (1 - a)); };
  const bagved = (el) => {
    let n = el; const kæde = []; let acc = [255, 255, 255];
    while (n && n.nodeType === 1) { kæde.push(n); n = n.parentElement; }
    for (let i = kæde.length - 1; i >= 0; i--) {
      const c = px(getComputedStyle(kæde[i]).backgroundColor);
      if (!(c.length === 4 && c[3] === 0)) acc = over(c, acc);
    }
    return acc;
  };
  const iRuller = (el) => {
    let n = el.parentElement;
    while (n && n !== document.body) { if (/(auto|scroll)/.test(getComputedStyle(n).overflowX)) return true; n = n.parentElement; }
    return false;
  };
  const klippet = (el) => {
    let n = el.parentElement;
    while (n && n !== document.body) { if (getComputedStyle(n).overflow !== 'visible') return true; n = n.parentElement; }
    return false;
  };

  const vw = document.documentElement.clientWidth;
  const overløb = []; const kontrast = []; const små = [];

  document.querySelectorAll('body *').forEach((el) => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') return;
    const r = el.getBoundingClientRect();

    if (r.width > 0 && cs.position !== 'fixed' && !iRuller(el) && !klippet(el) && (r.right > vw + 1 || r.left < -1)) {
      overløb.push(`${el.tagName.toLowerCase()} ${Math.round(r.left)}–${Math.round(r.right)} «${(el.textContent || '').trim().slice(0, 30)}»`);
    }

    if ([...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim().length > 1)) {
      let op = 1; let n = el;
      while (n && n.nodeType === 1) { op *= parseFloat(getComputedStyle(n).opacity); n = n.parentElement; }
      if (op >= 0.9 && (el.offsetParent || cs.position === 'fixed')) {
        const bg = bagved(el); const fg = over(px(cs.color), bg);
        const L1 = lum(fg); const L2 = lum(bg);
        const forhold = (Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05);
        const str = parseFloat(cs.fontSize); const vægt = parseInt(cs.fontWeight, 10) || 400;
        const krav = (str >= 24 || (str >= 18.66 && vægt >= 700)) ? 3 : 4.5;
        if (forhold < krav) kontrast.push(`${forhold.toFixed(2)}:1 ${cs.color} ${str}px «${el.textContent.trim().slice(0, 30)}»`);
      }
    }
  });

  // Berøringsmål: kun frittstående kontroller — links i løbende tekst er undtaget i WCAG 2.5.8
  document.querySelectorAll('button,[role=button]').forEach((el) => {
    if (!el.offsetParent) return;
    const r = el.getBoundingClientRect();
    if (r.width === 0) return;
    const ekstra = getComputedStyle(el, '::after').width;
    const b = Math.max(r.width, parseFloat(ekstra) || 0);
    const h = Math.max(r.height, parseFloat(getComputedStyle(el, '::after').height) || 0);
    if (b < 24 || h < 24) små.push(`${Math.round(b)}x${Math.round(h)} «${el.textContent.trim().slice(0, 24)}»`);
  });

  const tæl = (a) => Object.entries(a.reduce((m, k) => (m[k] = (m[k] || 0) + 1, m), {})).map(([k, n]) => (n > 1 ? `${k} x${n}` : k));
  return { vw, overløb: tæl(overløb), kontrast: tæl(kontrast), små: tæl(små), scrollW: document.documentElement.scrollWidth };
});

(async () => {
  const browser = await chromium.launch();
  let fejl = 0;
  for (const w of BREDDER) {
    const page = await browser.newPage({ viewport: { width: w, height: 900 } });
    const konsol = [];
    page.on('console', (m) => { if (m.type() === 'error') konsol.push(m.text()); });
    page.on('pageerror', (e) => konsol.push('pageerror: ' + e.message));
    await page.goto(URL, { waitUntil: 'networkidle' });
    const r = await revision(page);
    const problemer = r.overløb.length + r.kontrast.length + r.små.length + konsol.length + (r.scrollW > w ? 1 : 0);
    fejl += problemer;
    console.log(`\n── ${w}px ${problemer ? '' : '· rent'}`);
    if (r.scrollW > w) console.log(`   vandret rullebredde ${r.scrollW} > ${w}`);
    if (r.overløb.length) console.log('   overløb:', ...r.overløb.map((x) => '\n     ' + x));
    if (r.kontrast.length) console.log('   kontrast:', ...r.kontrast.map((x) => '\n     ' + x));
    if (r.små.length) console.log('   små mål:', ...r.små.map((x) => '\n     ' + x));
    if (konsol.length) console.log('   konsol:', ...konsol.map((x) => '\n     ' + x.slice(0, 120)));
    await page.close();
  }
  await browser.close();
  console.log(`\n${fejl ? fejl + ' problemer i alt' : 'ingen problemer'}`);
  process.exit(fejl ? 1 : 0);
})();
