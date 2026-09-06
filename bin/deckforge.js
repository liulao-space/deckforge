#!/usr/bin/env node
/* DeckForge · npm/npx entry point.
   Delegates to the Python CLI. If Python 3 is missing, we announce it clearly.
   Args are passed straight through: npx deckforge content.json -o out.html --preset violet */
'use strict';
const { spawnSync } = require('child_process');
const path = require('path');

const HERE = path.resolve(__dirname, '..');
const PY = path.join(HERE, 'build.py');
const args = process.argv.slice(2);

// always show help quickly
if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
  console.log('DeckForge — build an animated HTML slide deck from a JSON spec.');
  console.log('\n  npx deckforge <content.json> [-o out.html] [options]\n');
  console.log('Options:');
  console.log('  -o, --out <file>      output path (default dist/index.html)');
  console.log('  --preset <name>       teal|ocean|violet|sunset|rose|mono|emerald');
  console.log('  --frame <name>        clean|bold|minimal (layout, not just color)');
  console.log('  --accent <hex>        override accent color');
  console.log('  --dark                dark theme');
  console.log('  --watch               re-render on file change');
  console.log('  --list-presets        list available presets');
  console.log('  --init                interactive new-deck scaffold');
  console.log('  --new <Title>         scaffold a fresh content.json from a title');
  process.exit(0);
}

const r = spawnSync('python3', [PY].concat(args), { stdio: 'inherit' });
if (r.error && r.error.code === 'ENOENT') {
  console.error('\n⚠️  DeckForge needs Python 3 (stdlib only, no deps). Install it then retry.');
  console.error('   macOS: brew install python3 · Ubuntu: sudo apt install python3 · Windows: python.org');
  process.exit(1);
}
process.exit(r.status ?? 0);
