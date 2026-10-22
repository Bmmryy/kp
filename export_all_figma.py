#!/usr/bin/env python3
"""
FlowETL — Figma Export Suite Generator
Generates:
1. Retina 2x Desktop Frame Screenshots (1440x900 viewport -> 2880x1800)
2. Standalone Inlined HTML Files (Ready for Figma plugin 'html.to.design')
3. Figma Design System Tokens JSON (Tokens Studio compatible)
4. Comprehensive Figma Import Guide
"""

import json
import os
import subprocess
import time
from pathlib import Path

BASE_DIR = Path("/Users/ghn/.gemini/antigravity/scratch/ngoding anjay")
OUTPUT_DIR = BASE_DIR / "figma_export"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

VIEWS = [
    {
        "name": "01_Dashboard_Light",
        "url": "http://localhost:8000/?theme=light&view=dashboard",
        "theme": "light",
        "view": "dashboard",
        "desc": "Dashboard Utama (Light Theme) — KPI Stats, Quick Start Templates, Connectors"
    },
    {
        "name": "01_Dashboard_Dark",
        "url": "http://localhost:8000/?theme=dark&view=dashboard",
        "theme": "dark",
        "view": "dashboard",
        "desc": "Dashboard Utama (Dark Theme) — Dark Slate Surface, Vibrant Blue Accent"
    },
    {
        "name": "02_Pipeline_Builder_Light",
        "url": "http://localhost:8000/?theme=light&view=builder",
        "theme": "light",
        "view": "builder",
        "desc": "Pipeline Builder 3-Kolom (Light Theme) — Source, Transform, Destination Target"
    },
    {
        "name": "02_Pipeline_Builder_Dark",
        "url": "http://localhost:8000/?theme=dark&view=builder",
        "theme": "dark",
        "view": "builder",
        "desc": "Pipeline Builder 3-Kolom (Dark Theme) — Dark Mode macOS High-Contrast Layout"
    },
    {
        "name": "03_Execution_Progress_Drawer_Light",
        "url": "http://localhost:8000/?theme=light&view=builder&drawer=progress",
        "theme": "light",
        "view": "builder",
        "desc": "Execution Progress Drawer (Light) — Terminal Log, Progress Bar, Metrics"
    },
    {
        "name": "03_Execution_Progress_Drawer_Dark",
        "url": "http://localhost:8000/?theme=dark&view=builder&drawer=progress",
        "theme": "dark",
        "view": "builder",
        "desc": "Execution Progress Drawer (Dark) — Slate Terminal Console, Semantic Colors"
    },
    {
        "name": "04_History_Runs_Light",
        "url": "http://localhost:8000/?theme=light&view=history",
        "theme": "light",
        "view": "history",
        "desc": "Riwayat Eksekusi Pipeline (Light) — macOS Compact Productivity Data Table"
    },
    {
        "name": "04_History_Runs_Dark",
        "url": "http://localhost:8000/?theme=dark&view=history",
        "theme": "dark",
        "view": "history",
        "desc": "Riwayat Eksekusi Pipeline (Dark) — High-Contrast Dark Theme Data Table"
    },
    {
        "name": "05_Schedules_Light",
        "url": "http://localhost:8000/?theme=light&view=schedules",
        "theme": "light",
        "view": "schedules",
        "desc": "Penjadwalan Otomatis (Light) — Cron/Interval Active Jobs & History Link"
    },
    {
        "name": "05_Schedules_Dark",
        "url": "http://localhost:8000/?theme=dark&view=schedules",
        "theme": "dark",
        "view": "schedules",
        "desc": "Penjadwalan Otomatis (Dark) — Background Jobs Management in Dark Slate"
    },
    {
        "name": "06_Schedule_Modal_Light",
        "url": "http://localhost:8000/?theme=light&view=schedules&modal=schedule",
        "theme": "light",
        "view": "schedules",
        "desc": "Modal Tambah Jadwal ETL (Light) — Frosted Glass Blur, Database Sync Form"
    },
    {
        "name": "06_Schedule_Modal_Dark",
        "url": "http://localhost:8000/?theme=dark&view=schedules&modal=schedule",
        "theme": "dark",
        "view": "schedules",
        "desc": "Modal Tambah Jadwal ETL (Dark) — Dark Mode Surface with Pill Badges"
    },
    {
        "name": "07_File_Data_Manager_Light",
        "url": "http://localhost:8000/?theme=light&view=files",
        "theme": "light",
        "view": "files",
        "desc": "Manajer File Dataset & Output (Light) — Excel, CSV, SQLite Downloads"
    },
    {
        "name": "07_File_Data_Manager_Dark",
        "url": "http://localhost:8000/?theme=dark&view=files",
        "theme": "dark",
        "view": "files",
        "desc": "Manajer File Dataset & Output (Dark) — Output Explorer in Dark Theme"
    },
]

def capture_screenshots():
    print("📸 1. Mengambil screenshot Retina 2x untuk frame Figma (1440x900 Desktop)...")
    for item in VIEWS:
        out_png = OUTPUT_DIR / f"{item['name']}.png"
        cmd = [
            CHROME_BIN,
            "--headless=new",
            "--disable-gpu",
            "--window-size=1440,900",
            "--force-device-scale-factor=2",
            f"--screenshot={out_png}",
            item["url"]
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if out_png.exists():
            size_kb = out_png.stat().st_size / 1024
            print(f"  ✓ {item['name']}.png ({size_kb:.1f} KB) -> {item['desc']}")
        else:
            print(f"  ✗ Gagal mengambil {item['name']}: {res.stderr}")


def generate_inlined_html_snapshots():
    print("\n🌐 2. Membuat file HTML Standalone untuk Plugin Figma (html.to.design / Builder.io)...")
    template_path = BASE_DIR / "server/templates/index.html"
    css_path = BASE_DIR / "server/static/app.css"

    raw_html = template_path.read_text(encoding="utf-8")
    raw_css = css_path.read_text(encoding="utf-8")

    # Inlined CSS injection
    css_replacement = f"<style>\n{raw_css}\n</style>"
    html_with_css = raw_html.replace(
        '<link rel="stylesheet" href="/static/app.css?v=20261022_apple">',
        css_replacement
    )

    for item in VIEWS:
        # Pre-set theme & view in the standalone HTML
        themed_html = html_with_css.replace(
            '<html lang="id">',
            f'<html lang="id" data-theme="{item["theme"]}">'
        )
        
        # Add auto-navigation script
        extra_script = f"""
        <script>
        document.addEventListener("DOMContentLoaded", function() {{
            setTimeout(function() {{
                if (typeof showView === 'function') showView('{item["view"]}');
                if (typeof setTheme === 'function') setTheme('{item["theme"]}', false);
                {'showCreateScheduleModal();' if 'Modal' in item['name'] else ''}
                {'''
                openProgressDrawer('Running Pipeline: Data Ingestion (CSV → SQLite)');
                setProgress(85, 'LOADING (85%)');
                const log = document.getElementById('log-console');
                if (log) {
                    log.innerHTML = '<div style="color:var(--success)">[ 10%] CONNECTING_SOURCE ✓ Terhubung ke database sumber (MySQL)</div><div style="color:var(--success)">[ 20%] CONNECTING_DESTINATION ✓ Terhubung ke target (PostgreSQL)</div><div style="color:var(--accent)">[ 30%] EXTRACTING (500 baris diekstraksi)</div><div style="color:var(--purple,#AF52DE)">[ 60%] TRANSFORMING (Data Cleansing: Trim, Fill Null, Capitalize)</div><div style="color:var(--accent)">[ 85%] LOADING (Menyimpan 500 baris ke tabel target)</div>';
                }
                ''' if 'Drawer' in item['name'] else ''}
            }}, 150);
        }});
        </script>
        """
        final_html = themed_html.replace("</body>", f"{extra_script}\n</body>")
        
        html_file = OUTPUT_DIR / f"{item['name']}.html"
        html_file.write_text(final_html, encoding="utf-8")
        print(f"  ✓ {html_file.name} ({html_file.stat().st_size / 1024:.1f} KB)")


def generate_tokens_json():
    print("\n🎨 3. Menghasilkan figma_tokens.json (Apple HIG Design Tokens)...")
    tokens = {
        "color": {
            "light": {
                "background": {"value": "#F5F5F7", "type": "color", "description": "Canvas background"},
                "surface": {"value": "#FFFFFF", "type": "color", "description": "Main cards surface"},
                "surfaceSecondary": {"value": "#FBFBFD", "type": "color", "description": "Secondary panels"},
                "text": {"value": "#1D1D1F", "type": "color", "description": "Primary high-contrast text"},
                "textSecondary": {"value": "#6E6E73", "type": "color", "description": "Subtitle & secondary text"},
                "textTertiary": {"value": "#86868B", "type": "color", "description": "Muted labels"},
                "border": {"value": "#D2D2D7", "type": "color", "description": "1px hairline border"},
                "accent": {"value": "#007AFF", "type": "color", "description": "Apple System Blue"},
                "success": {"value": "#248A3D", "type": "color", "description": "Apple System Green"},
                "warning": {"value": "#B76E00", "type": "color", "description": "Apple System Orange/Gold"},
                "error": {"value": "#D70015", "type": "color", "description": "Apple System Red"}
            },
            "dark": {
                "background": {"value": "#151516", "type": "color", "description": "Dark canvas background"},
                "surface": {"value": "#1C1C1E", "type": "color", "description": "Dark gray main surface"},
                "surfaceSecondary": {"value": "#242426", "type": "color", "description": "Elevated dark card"},
                "text": {"value": "#F5F5F7", "type": "color", "description": "Primary light text"},
                "textSecondary": {"value": "#A1A1A6", "type": "color", "description": "Secondary gray text"},
                "textTertiary": {"value": "#636366", "type": "color", "description": "Muted dark text"},
                "border": {"value": "#38383A", "type": "color", "description": "Dark border hairline"},
                "accent": {"value": "#0A84FF", "type": "color", "description": "Vibrant Dark Blue"},
                "success": {"value": "#30D158", "type": "color", "description": "Vibrant Green"},
                "warning": {"value": "#FFD60A", "type": "color", "description": "Vibrant Yellow"},
                "error": {"value": "#FF453A", "type": "color", "description": "Vibrant Red"}
            }
        },
        "borderRadius": {
            "card": {"value": "16px", "type": "borderRadius"},
            "input": {"value": "10px", "type": "borderRadius"},
            "button": {"value": "10px", "type": "borderRadius"},
            "pill": {"value": "9999px", "type": "borderRadius"}
        },
        "spacing": {
            "xs": {"value": "4px", "type": "spacing"},
            "sm": {"value": "8px", "type": "spacing"},
            "md": {"value": "16px", "type": "spacing"},
            "lg": {"value": "24px", "type": "spacing"},
            "xl": {"value": "32px", "type": "spacing"}
        },
        "typography": {
            "fontFamily": {"value": "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Inter', sans-serif", "type": "fontFamilies"},
            "monoFamily": {"value": "'SF Mono', Menlo, Consolas, monospace", "type": "fontFamilies"}
        }
    }
    token_file = OUTPUT_DIR / "figma_tokens.json"
    token_file.write_text(json.dumps(tokens, indent=2), encoding="utf-8")
    print(f"  ✓ {token_file.name} berhasil dibuat.")


def generate_guide_markdown():
    print("\n📖 4. Membuat Panduan Import Figma (README_FIGMA_IMPORT.md)...")
    content = """# Panduan Import FlowETL ke Figma Frame

Folder ini berisi seluruh aset siap pakai untuk memasukkan antarmuka FlowETL ke dalam **Figma** baik sebagai **Frame Gambar High-Resolution (Retina 2x)** maupun sebagai **Vector Layers & Auto-Layout yang dapat diedit langsung**.

---

## 🚀 Opsi 1: Import 100% Editable Vector & Auto-Layout via Plugin Figma (Sangat Direkomendasikan)

Jika Anda ingin tiap tombol, teks, kartu, input, dan icon di Figma menjadi **vektor dan layer teks asli** yang bisa diedit:

1. Buka file project Anda di **Figma**.
2. Masuk ke menu **Plugins** (atau tekan `Shift + I` -> pilih tab **Plugins**).
3. Cari dan jalankan plugin gratis **`html.to.design`** (dibuat oleh Divriots, plugin converter HTML ke Figma terpopuler).
   *(Alternatif lain: plugin **`Builder.io: Figma to HTML / HTML to Figma`**)*.
4. Pada jendela plugin `html.to.design`:
   - **Metode A (Drag File HTML):** Drag salah satu file `.html` mandiri dari folder `figma_export/` ini (misalnya `01_Dashboard_Light.html` atau `02_Pipeline_Builder_Light.html`) langsung ke jendela plugin.
   - **Metode B (Live URL):** Masukkan URL lokal `http://localhost:8000/?view=builder` ke kolom input plugin.
5. Klik tombol **Import**.
6. **Hasilnya:** Plugin akan secara otomatis menghasilkan **Figma Frame lengkap** berisi Auto-Layout, layer teks, warna, border radius `16px`, dan icon vektor SF Symbols!

---

## 🖼️ Opsi 2: Drag & Drop Frame Gambar High-Resolution (Retina 2x)

Untuk dokumentasi, presentasi mockup, atau review desain cepat:

1. Buat canvas baru di Figma.
2. Buat Frame Desktop (tekan `F` -> pilih **MacBook Pro 14"** atau **Desktop 1440 × 900**).
3. Drag & drop file `.png` dari folder ini langsung ke dalam Frame Figma Anda:
   - `01_Dashboard_Light.png` & `01_Dashboard_Dark.png`
   - `02_Pipeline_Builder_Light.png` & `02_Pipeline_Builder_Dark.png`
   - `03_Execution_Progress_Drawer_Light.png` & `03_Execution_Progress_Drawer_Dark.png`
   - `04_History_Runs_Light.png` & `04_History_Runs_Dark.png`
   - `05_Schedules_Light.png` & `05_Schedules_Dark.png`
   - `06_Schedule_Modal_Light.png` & `06_Schedule_Modal_Dark.png`
   - `07_File_Data_Manager_Light.png` & `07_File_Data_Manager_Dark.png`
4. Seluruh gambar diekspor dengan **Retina 2x (2880 × 1800 px)** sehingga tampil luar biasa tajam dan jernih tanpa pecah di Figma.

---

## 🎨 Opsi 3: Import Design System Tokens ke Figma

Jika Anda menggunakan plugin **Tokens Studio for Figma** (Figma Tokens):
1. Buka plugin **Tokens Studio for Figma**.
2. Klik **Load from file / Tools** -> pilih file `figma_tokens.json`.
3. Seluruh variabel warna Apple HIG (Light & Dark), spacing, border radius, dan tipografi akan langsung terdaftar di panel Styles & Variables Figma Anda!
"""
    readme = OUTPUT_DIR / "README_FIGMA_IMPORT.md"
    readme.write_text(content, encoding="utf-8")
    print(f"  ✓ {readme.name} berhasil dibuat.")


if __name__ == "__main__":
    capture_screenshots()
    generate_inlined_html_snapshots()
    generate_tokens_json()
    generate_guide_markdown()
    print("\n✨ Semua ekspor ke Figma Frame berhasil diselesaikan di folder figma_export/!")
