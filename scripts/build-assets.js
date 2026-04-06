#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const STATIC = path.join(ROOT, 'onepageblog', 'static');
const FONTS_DIR = path.join(STATIC, 'fonts');

fs.mkdirSync(FONTS_DIR, { recursive: true });

function copy(src, dest) {
  fs.copyFileSync(src, dest);
  console.log(`  ${path.relative(ROOT, src)} → ${path.relative(ROOT, dest)}`);
}

console.log('Copying JS bundles...');
copy(
  path.join(ROOT, 'node_modules', 'htmx.org', 'dist', 'htmx.min.js'),
  path.join(STATIC, 'htmx.min.js')
);
copy(
  path.join(ROOT, 'node_modules', 'alpinejs', 'dist', 'cdn.min.js'),
  path.join(STATIC, 'alpinejs.min.js')
);

console.log('Copying font files...');
const fonts = [
  { pkg: 'lora',   family: 'Lora',   weight: '400', style: 'normal' },
  { pkg: 'lora',   family: 'Lora',   weight: '400', style: 'italic' },
  { pkg: 'lora',   family: 'Lora',   weight: '700', style: 'normal' },
  { pkg: 'nunito', family: 'Nunito', weight: '400', style: 'normal' },
  { pkg: 'nunito', family: 'Nunito', weight: '600', style: 'normal' },
];

for (const { pkg, weight, style } of fonts) {
  const filename = `${pkg}-latin-${weight}-${style}.woff2`;
  copy(
    path.join(ROOT, 'node_modules', `@fontsource/${pkg}`, 'files', filename),
    path.join(FONTS_DIR, filename)
  );
}

console.log('Generating fonts.css...');
const fontFaces = fonts.map(({ family, pkg, weight, style }) => {
  const filename = `${pkg}-latin-${weight}-${style}.woff2`;
  return `@font-face {
  font-family: '${family}';
  font-style: ${style};
  font-weight: ${weight};
  font-display: swap;
  src: url('./fonts/${filename}') format('woff2');
}`;
}).join('\n\n');

fs.writeFileSync(path.join(STATIC, 'fonts.css'), fontFaces + '\n');
console.log('  Done.');
