#!/usr/bin/env node
/**
 * FlowETL → Figma PNG Import
 * 
 * Imports existing PNG screenshots directly into Figma as frames
 * using figma-ds-cli CDP connection (no Playwright needed).
 * 
 * Uses: figma-ds-cli eval (Plugin API JS execution in Figma)
 */

import { readFileSync, readdirSync } from 'fs';
import { execSync } from 'child_process';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const EXPORT_DIR = join(__dirname, 'figma_export');
const CLI = 'figma-ds-cli';

// Pages in order: [filename_base, display_name]
const PAGES = [
  ['01_Dashboard_Light',                 'FlowETL – Dashboard (Light)'],
  ['01_Dashboard_Dark',                  'FlowETL – Dashboard (Dark)'],
  ['02_Pipeline_Builder_Light',          'FlowETL – Pipeline Builder (Light)'],
  ['02_Pipeline_Builder_Dark',           'FlowETL – Pipeline Builder (Dark)'],
  ['03_Execution_Progress_Drawer_Light', 'FlowETL – Execution Drawer (Light)'],
  ['03_Execution_Progress_Drawer_Dark',  'FlowETL – Execution Drawer (Dark)'],
  ['04_History_Runs_Light',              'FlowETL – History Runs (Light)'],
  ['04_History_Runs_Dark',               'FlowETL – History Runs (Dark)'],
  ['05_Schedules_Light',                 'FlowETL – Schedules (Light)'],
  ['05_Schedules_Dark',                  'FlowETL – Schedules (Dark)'],
  ['06_Schedule_Modal_Light',            'FlowETL – Schedule Modal (Light)'],
  ['06_Schedule_Modal_Dark',             'FlowETL – Schedule Modal (Dark)'],
  ['07_File_Data_Manager_Light',         'FlowETL – File Manager (Light)'],
  ['07_File_Data_Manager_Dark',          'FlowETL – File Manager (Dark)'],
];

// Frame size: 1440x900 (Figma Desktop standard)
const FRAME_W = 1440;
const FRAME_H = 900;
// Horizontal gap between frames
const GAP = 120;

function buildFigmaCode(base64, name, index) {
  // Escape name for JS string
  const safeName = name.replace(/"/g, '\\"').replace(/–/g, '-');
  const x = index * (FRAME_W + GAP);

  return `
(async () => {
  try {
    const dataUrl = "data:image/png;base64,${base64}";
    const image = await figma.createImageAsync(dataUrl);
    const { width, height } = await image.getSizeAsync();

    // Create frame
    const frame = figma.createFrame();
    frame.name = "${safeName}";
    frame.resize(${FRAME_W}, ${FRAME_H});
    frame.x = ${x};
    frame.y = 0;
    frame.fills = [{ type: 'IMAGE', scaleMode: 'FILL', imageHash: image.hash }];
    frame.cornerRadius = 0;

    figma.currentPage.selection = [frame];
    figma.viewport.scrollAndZoomIntoView([frame]);

    return "OK: ${safeName}";
  } catch (e) {
    return "ERR: " + e.message;
  }
})()
`.trim();
}

async function importAll() {
  console.log('\n╔════════════════════════════════════════════════════╗');
  console.log('║    FlowETL → Figma PNG Import (figma-ds-cli)       ║');
  console.log('╚════════════════════════════════════════════════════╝\n');

  // Check Figma connection
  try {
    execSync(`${CLI} status`, { stdio: 'pipe' });
    console.log('✅ Figma Desktop connected\n');
  } catch {
    console.error('❌ Figma Desktop not connected. Run: figma-ds-cli connect');
    process.exit(1);
  }

  const results = { ok: 0, fail: 0, errors: [] };

  for (let i = 0; i < PAGES.length; i++) {
    const [base, name] = PAGES[i];
    const pngPath = join(EXPORT_DIR, `${base}.png`);
    const label = `[${i + 1}/${PAGES.length}]`;

    process.stdout.write(`${label} ${name} ... `);

    try {
      // Read PNG → base64
      const buffer = readFileSync(pngPath);
      const base64 = buffer.toString('base64');

      // Build Plugin API code
      const jsCode = buildFigmaCode(base64, name, i);

      // Write to temp file and eval via figma-cli
      const tmpFile = `/tmp/figma_import_${i}.js`;
      import('fs').then(fs => fs.writeFileSync(tmpFile, jsCode));

      // Use figma-ds-cli eval --file to run the code
      const result = execSync(
        `${CLI} eval --file "${tmpFile}"`,
        { encoding: 'utf8', timeout: 30000 }
      ).trim();

      console.log(`✅  ${result || 'Done'}`);
      results.ok++;
    } catch (err) {
      const msg = err.message?.split('\n')[0] || 'Unknown error';
      console.log(`❌  ${msg}`);
      results.fail++;
      results.errors.push({ name, msg });
    }

    // Small pause to not overwhelm Figma CDP
    await new Promise(r => setTimeout(r, 1500));
  }

  // Summary
  console.log('\n════════════════════════════════════════════════════');
  console.log(`✅ ${results.ok} imported  ❌ ${results.fail} failed  (total: ${PAGES.length})`);
  if (results.errors.length > 0) {
    console.log('\nFailed:');
    results.errors.forEach(e => console.log(`  • ${e.name}: ${e.msg}`));
  }
  console.log('');
}

importAll().catch(console.error);
