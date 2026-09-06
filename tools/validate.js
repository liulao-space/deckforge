#!/usr/bin/env node
/* DeckForge · build all examples/presets and syntax-check every emitted <script>.
   Used by CI. Also verifies each referenced icon `<use href="#i-...">` has a
   matching `<symbol id="i-...">` in the embedded icons. */
'use strict';
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const OUT = '/tmp/df-validate';
fs.mkdirSync(OUT, { recursive: true });

function sh(cmd) { execSync(cmd, { stdio: 'inherit' }); }

// 1. build everything
const presets = ['teal', 'ocean', 'violet', 'sunset', 'rose', 'mono', 'emerald'];
for (const p of presets) sh(`python3 ${ROOT}/build.py ${ROOT}/examples/choosing-a-framework.json -o ${OUT}/${p}.html --preset ${p}`);
sh(`python3 ${ROOT}/build.py ${ROOT}/examples/orca-herdr.json -o ${OUT}/orca.html`);
sh(`python3 ${ROOT}/build.py ${ROOT}/examples/orca-herdr.json -o ${OUT}/dark.html --preset teal --dark`);

// 2. syntax-check JS + icon references
let bad = 0;
const htmls = fs.readdirSync(OUT).filter(f => f.endsWith('.html'));
for (const f of htmls) {
  const html = fs.readFileSync(path.join(OUT, f), 'utf8');
  const m = html.match(/<script>([\s\S]*?)<\/script>/);
  try { new Function(m[1]); } catch (e) { console.error(`❌ ${f}: JS error ${e.message}`); bad++; }

  const used = new Set([...html.matchAll(/href="#(i-[a-z-]+)"/g)].map(x => x[1]));
  const defd = new Set([...html.matchAll(/symbol id="(i-[a-z-]+)"/g)].map(x => x[1]));
  for (const u of used) if (!defd.has(u)) { console.error(`❌ ${f}: icon ${u} referenced but undefined`); bad++; }
}

console.log(bad === 0 ? `✔ all ${htmls.length} builds OK (JS + icons)` : `✘ ${bad} problems`);
process.exit(bad === 0 ? 0 : 1);
