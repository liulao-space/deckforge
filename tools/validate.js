#!/usr/bin/env node
/* DeckForge · build all examples × all presets and syntax-check every emitted <script>.
   Used by CI. Also verifies each referenced icon `<use href="#i-...">` has a
   matching `<symbol id="i-...">` in the embedded icons, and smoke-tests the
   non-interactive scaffolds (--init / --new). */
'use strict';
const { execSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(os.tmpdir(), 'df-validate');
fs.rmSync(OUT, { recursive: true, force: true });
fs.mkdirSync(OUT, { recursive: true });

function sh(cmd, opts = {}) { execSync(cmd, { stdio: 'inherit', ...opts }); }

// 1. build every example with every preset
const presets = ['teal', 'ocean', 'violet', 'sunset', 'rose', 'mono', 'emerald'];
const examples = fs.readdirSync(path.join(ROOT, 'examples')).filter(f => f.endsWith('.json'));
for (const ex of examples) {
  const base = path.basename(ex, '.json');
  for (const p of presets) {
    sh(`python3 ${ROOT}/build.py ${ROOT}/examples/${ex} -o ${OUT}/${base}-${p}.html --preset ${p}`);
  }
}
sh(`python3 ${ROOT}/build.py ${ROOT}/examples/orca-herdr.json -o ${OUT}/dark.html --preset teal --dark`);
sh(`python3 ${ROOT}/build.py ${ROOT}/examples/orca-herdr.json -o ${OUT}/bold.html --frame bold --preset violet`);

// 2. non-interactive scaffolds must not need a TTY
sh(`python3 ${ROOT}/build.py --init -o init.json`, { cwd: OUT });
sh(`python3 ${ROOT}/build.py --new "CI 骨架" -o new.json`, { cwd: OUT });

// 3. syntax-check JS + icon references
let bad = 0;
const htmls = fs.readdirSync(OUT).filter(f => f.endsWith('.html'));
for (const f of htmls) {
  const html = fs.readFileSync(path.join(OUT, f), 'utf8');
  const m = html.match(/<script>([\s\S]*?)<\/script>/);
  try { new Function(m[1]); } catch (e) { console.error(`❌ ${f}: JS error ${e.message}`); bad++; }

  const used = new Set([...html.matchAll(/href="#(i-[a-z0-9-]+)"/g)].map(x => x[1]));
  const defd = new Set([...html.matchAll(/symbol id="(i-[a-z0-9-]+)"/g)].map(x => x[1]));
  for (const u of used) if (!defd.has(u)) { console.error(`❌ ${f}: icon ${u} referenced but undefined`); bad++; }
}

// 4. scaffolds produce valid JSON decks
for (const jf of ['init.json', 'new.json']) {
  try {
    JSON.parse(fs.readFileSync(path.join(OUT, jf), 'utf8'));
  } catch (e) {
    console.error(`❌ scaffold ${jf}: invalid JSON ${e.message}`);
    bad++;
  }
}

console.log(bad === 0 ? `✔ all ${htmls.length} builds OK (JS + icons + scaffolds)` : `✘ ${bad} problems`);
process.exit(bad === 0 ? 0 : 1);
