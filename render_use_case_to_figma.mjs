/**
 * Render Use Case Diagram directly into Figma Desktop canvas as native vector nodes
 * (Frame, Ellipse, Line, Text).
 */

import { execSync } from 'child_process';
import { readFileSync, writeFileSync } from 'fs';

const figmaScript = `
(async () => {
  try {
    await figma.loadFontAsync({ family: "Inter", style: "Regular" });
    await figma.loadFontAsync({ family: "Inter", style: "Bold" });
    await figma.loadFontAsync({ family: "Inter", style: "Medium" });

    // 1. Main Canvas Frame
    const mainFrame = figma.createFrame();
    mainFrame.name = "Use Case Diagram - Sistem Integrasi Data Berbasis Web";
    mainFrame.resize(1100, 2500);
    mainFrame.fills = [{ type: "SOLID", color: { r: 1, g: 1, b: 1 } }];
    mainFrame.x = 0;
    mainFrame.y = 0;

    // 2. System Boundary Box
    const boundary = figma.createRectangle();
    boundary.name = "System Boundary";
    boundary.resize(790, 2380);
    boundary.x = 230;
    boundary.y = 40;
    boundary.fills = [];
    boundary.strokes = [{ type: "SOLID", color: { r: 0.11, g: 0.11, b: 0.12 } }];
    boundary.strokeWeight = 2;
    mainFrame.appendChild(boundary);

    // Boundary Title
    const bTitle = figma.createText();
    bTitle.fontName = { family: "Inter", style: "Bold" };
    bTitle.fontSize = 15;
    bTitle.characters = "SISTEM INTEGRASI DATA BERBASIS WEB";
    bTitle.textAlignHorizontal = "CENTER";
    bTitle.resize(790, 30);
    bTitle.x = 230;
    bTitle.y = 65;
    mainFrame.appendChild(bTitle);

    // Helper: Create Oval Use Case
    function createOval(name, text, x, y, w, h, isBold = false) {
      const ellipse = figma.createEllipse();
      ellipse.name = "Oval: " + name;
      ellipse.resize(w, h);
      ellipse.x = x - w/2;
      ellipse.y = y - h/2;
      ellipse.fills = [{ type: "SOLID", color: { r: 1, g: 1, b: 1 } }];
      ellipse.strokes = [{ type: "SOLID", color: { r: 0.11, g: 0.11, b: 0.12 } }];
      ellipse.strokeWeight = isBold ? 1.6 : 1.3;
      mainFrame.appendChild(ellipse);

      const label = figma.createText();
      label.fontName = { family: "Inter", style: isBold ? "Bold" : "Regular" };
      label.fontSize = isBold ? 11.5 : 10.5;
      label.characters = text;
      label.textAlignHorizontal = "CENTER";
      label.textAlignVertical = "CENTER";
      label.resize(w - 20, h - 10);
      label.x = x - (w - 20)/2;
      label.y = y - (h - 10)/2;
      mainFrame.appendChild(label);
    }

    // Helper: Create Stick Figure Actor
    function createActor(name, x, y) {
      const head = figma.createEllipse();
      head.resize(28, 28);
      head.x = x + 35 - 14;
      head.y = y + 8;
      head.fills = [{ type: "SOLID", color: { r: 1, g: 1, b: 1 } }];
      head.strokes = [{ type: "SOLID", color: { r: 0.11, g: 0.11, b: 0.12 } }];
      head.strokeWeight = 1.8;
      mainFrame.appendChild(head);

      const body = figma.createLine();
      body.resize(46, 0);
      body.rotation = -90;
      body.x = x + 35;
      body.y = y + 82;
      body.strokes = [{ type: "SOLID", color: { r: 0.11, g: 0.11, b: 0.12 } }];
      body.strokeWeight = 1.8;
      mainFrame.appendChild(body);

      const arms = figma.createLine();
      arms.resize(54, 0);
      arms.x = x + 8;
      arms.y = y + 52;
      arms.strokes = [{ type: "SOLID", color: { r: 0.11, g: 0.11, b: 0.12 } }];
      arms.strokeWeight = 1.8;
      mainFrame.appendChild(arms);

      const leg1 = figma.createLine();
      leg1.resize(50, 0);
      leg1.rotation = -65;
      leg1.x = x + 14;
      leg1.y = y + 128;
      leg1.strokes = [{ type: "SOLID", color: { r: 0.11, g: 0.11, b: 0.12 } }];
      leg1.strokeWeight = 1.8;
      mainFrame.appendChild(leg1);

      const leg2 = figma.createLine();
      leg2.resize(50, 0);
      leg2.rotation = -115;
      leg2.x = x + 56;
      leg2.y = y + 128;
      leg2.strokes = [{ type: "SOLID", color: { r: 0.11, g: 0.11, b: 0.12 } }];
      leg2.strokeWeight = 1.8;
      mainFrame.appendChild(leg2);

      const textNode = figma.createText();
      textNode.fontName = { family: "Inter", style: "Bold" };
      textNode.fontSize = 13;
      textNode.characters = name;
      textNode.textAlignHorizontal = "CENTER";
      textNode.resize(130, 20);
      textNode.x = x + 35 - 65;
      textNode.y = y + 145;
      mainFrame.appendChild(textNode);
    }

    createActor("Operator Data", 60, 420);
    createActor("Administrator Sistem", 60, 1420);

    // Render Hubs
    createOval("Engine", "Lihat Status Engine & Metrik", 390, 115, 240, 50, true);
    createOval("Template", "Pilih Template Pipeline Siap Pakai", 390, 185, 240, 50, true);
    createOval("Source", "Konfigurasi Sumber Data", 390, 396, 240, 52, true);
    createOval("Transform", "Konfigurasi Transformasi\\n& Pemetaan Kolom", 390, 746, 240, 52, true);
    createOval("Dest", "Konfigurasi Tujuan Data\\n& Mode Muat", 390, 1126, 240, 52, true);
    createOval("Run", "Eksekusi Pipeline Data", 390, 1466, 240, 52, true);
    createOval("Schedule", "Kelola Penjadwalan Tugas\\n(Task Scheduler)", 390, 1786, 240, 52, true);
    createOval("History", "Lihat Riwayat Eksekusi & Log", 390, 2005, 240, 50, true);
    createOval("Files", "Kelola & Unduh Berkas Data", 390, 2085, 240, 50, true);

    // Render Subs
    createOval("SubUpload", "Upload Berkas Dokumen\\n(CSV, Excel, JSON, SQLite)", 775, 295, 270, 50);
    createOval("SubDB", "Koneksi Basis Data Relasional\\n(MySQL, PostgreSQL, Oracle)", 775, 365, 270, 50);
    createOval("SubInspect", "Inspeksi Struktur Kolom Otomatis", 775, 434, 270, 48);
    createOval("SubOverride", "Override Tipe Kolom Data\\n(Type Casting)", 775, 499, 270, 48);

    createOval("SubMapping", "Pemetaan Kolom Sumber-Tujuan\\n(Aksi 1-ke-1 & Ignore)", 775, 604, 270, 48);
    createOval("SubClean", "Pembersihan & Format Teks\\n(Trim & Case Convert)", 775, 669, 270, 48);
    createOval("SubNull", "Penanganan Nilai Kosong\\n(Fill Null & Drop Null)", 775, 734, 270, 48);
    createOval("SubMask", "Penyensoran Data Sensitif\\n(Masking Telepon / NIK)", 775, 799, 270, 48);
    createOval("SubFilter", "Penyaringan Baris Data (Filter)", 775, 864, 270, 48);

    createOval("SubFileDest", "Format Berkas Ekspor Target\\n(CSV, Excel .xlsx, SQLite, JSONL)", 775, 995, 270, 50);
    createOval("SubDBDest", "Basis Data Relasional Target\\n(MySQL, PostgreSQL, Oracle)", 775, 1065, 270, 50);
    createOval("SubLoadMode", "Pemilihan Mode Muat Data\\n(Sync, Append, Truncate, Replace)", 775, 1135, 270, 50);
    createOval("SubDanger", "Konfirmasi Peringatan\\nOperasi Destruktif", 775, 1204, 270, 48);

    createOval("SubSchemaEvo", "Verifikasi Evolusi Skema\\n(ADD / DROP Column)", 775, 1394, 270, 48);
    createOval("SubSSE", "Pemantauan Progres Real-Time\\n(SSE Stream 0-100%)", 775, 1459, 270, 48);
    createOval("SubDrawerDL", "Unduh Berkas Hasil Langsung\\ndari Progress Drawer", 775, 1524, 270, 48);

    createOval("SubCron", "Tambah Jadwal Cron Baru &\\nPicu Eksekusi Manual", 775, 1785, 270, 50);

    figma.currentPage.selection = [mainFrame];
    figma.viewport.scrollAndZoomIntoView([mainFrame]);

    return "SUCCESS: Use Case Diagram rendered into Figma Desktop!";
  } catch (err) {
    return "ERROR: " + err.message;
  }
})()
`;

writeFileSync("/tmp/render_usecase.js", figmaScript);

try {
  const result = execSync(
    'figma-ds-cli eval --file "/tmp/render_usecase.js"',
    { encoding: "utf8" }
  );
  console.log(result);
} catch (e) {
  console.log("Could not auto-render to Figma (ensure a design file is open in Figma Desktop).", e.message);
}
