// Pull the data tables (PERSONER, MANDSKAB, BILLEDER, FORBEHOLD, KILDER) out of the original page's x-dc script.
const fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8');
const i = src.indexOf('<script type="text/x-dc"');
const j = src.indexOf('>', i) + 1;
const k = src.indexOf('</script>', j);
const code = src.slice(j, k);
const vm = require('vm');
const ctx = { DCLogic: class {}, window: {}, document: {} };
vm.createContext(ctx);
vm.runInContext(code + '\n;this.__C = Component;', ctx);
const C = ctx.__C;
const out = {};
for (const key of ['PERSONER', 'MANDSKAB', 'BILLEDER', 'FORBEHOLD', 'KILDER']) out[key] = C[key];
fs.writeFileSync(process.argv[3], JSON.stringify(out, null, 1));
console.log(Object.fromEntries(Object.entries(out).map(([k, v]) => [k, Array.isArray(v) ? v.length : Object.keys(v).length])));

// Optional: node extract_data.js <index.html> <data.da.json> <silkjaer-map.js> <places.da.json>
if (process.argv[4] && process.argv[5]) {
  const m = fs.readFileSync(process.argv[4], 'utf8');
  const a = m.indexOf('const PLACES = {');
  let depth = 0, e = m.indexOf('{', a);
  for (let p = e; p < m.length; p++) {
    if (m[p] === '{') depth++;
    else if (m[p] === '}' && --depth === 0) { e = p + 1; break; }
  }
  const places = vm.runInNewContext('(' + m.slice(m.indexOf('{', a), e) + ')');
  fs.writeFileSync(process.argv[5], JSON.stringify(places, null, 1));
  console.log('places', Object.keys(places).length);
}
