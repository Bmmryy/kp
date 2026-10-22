# Panduan Import FlowETL ke Figma Frame

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
