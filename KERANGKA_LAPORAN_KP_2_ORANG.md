# KERANGKA LAPORAN KERJA PRAKTIK (2 JUDUL TERPISAH)
### Proyek: FlowETL — Platform Integrasi Data Visual Berbasis Web
### Lokasi: Unit Penunjang Akademik Teknologi Informasi dan Komunikasi (UPA TIK) Universitas Lambung Mangkurat
### Format Referensi: `LaporanAkhir_KP_Muhammad Agung Permana.docx`
### Pembaruan: Sesuai Perkembangan Sistem Terkini (Revisi ke-7 — 118 Unit Test Passed)

---

## 📌 Ringkasan Pembagian Judul & Spesialisasi

| Atribut | Laporan 1 (Mahasiswa 1) | Laporan 2 (Mahasiswa 2) |
| :--- | :--- | :--- |
| **Fokus Bidang** | Backend Engineering & Database Pipeline Integration | Frontend UI/UX, Visual Builder & System QA Testing |
| **Judul Laporan** | **PENGEMBANGAN BACKEND ENGINE DAN PIPELINE INTEGRASI MULTI-DATABASE PADA APLIKASI FLOWETL DI UNIT PENUNJANG AKADEMIK TEKNOLOGI INFORMASI DAN KOMUNIKASI UNIVERSITAS LAMBUNG MANGKURAT** | **RANCANG BANGUN ANTARMUKA VISUAL PIPELINE BUILDER DAN PENGUJIAN SISTEM PADA APLIKASI FLOWETL DI UNIT PENUNJANG AKADEMIK TEKNOLOGI INFORMASI DAN KOMUNIKASI UNIVERSITAS LAMBUNG MANGKURAT** |
| **Karakter Bab III** | Arsitektur ETL, SQLAlchemy 2.0, Dialek SQL, Type Inference & Casting Engine, Structural Schema Evolution, Task Scheduler | Prinsip Desain UI/UX, DOM & Fetch API, Server-Sent Events (SSE), Desain Interaksi Form Tingkat Lanjut, Metodologi Black-Box QA |
| **Karakter Bab V.3** | Engine Konektor, Generator DDL Dinamis, Modul `CastColumnsTransformer`, Auto-Injection Pipeline Runner, Drop Column Evolution, REST API | Layouting Dashboard, Interaksi Drag-Drop, Komponen Dropdown Type Override, Tombol Aksi Cepat Mapping (1-to-1 & Ignore), Real-Time Progress Drawer |
| **Karakter Bab V.4** | Pytest Automation (118 test cases), Throughput Data, Uji Integritas Transaksi ACID, Uji Regresi Casting & Drop Column | Black-box Testing Matrix, User Simulation, Uji Pencegahan Duplikasi Mapping, Uji Validasi Override Tipe Data, Uji Kesiapan Produksi |

---
---

# 📘 LAPORAN 1 (MAHASISWA 1) — BACKEND ENGINE & DATABASE INTEGRATION

### **JUDUL:**
> **PENGEMBANGAN BACKEND ENGINE DAN PIPELINE INTEGRASI MULTI-DATABASE PADA APLIKASI FLOWETL DI UNIT PENUNJANG AKADEMIK TEKNOLOGI INFORMASI DAN KOMUNIKASI UNIVERSITAS LAMBUNG MANGKURAT**

---

### **DAFTAR ISI DAN KETERANGAN ISI (TULIS APA):**

```text
HALAMAN JUDUL
LEMBAR PENGESAHAN
ABSTRAK
KATA PENGANTAR
DAFTAR ISI
DAFTAR GAMBAR
DAFTAR TABEL
DAFTAR LAMPIRAN
```

* **ABSTRAK**
  * *Tulis apa:* Ringkasan eksekutif (maksimal 250 kata). Uraikan latar belakang tantangan integrasi data heterogen di UPA TIK ULM, tujuan pengembangan backend engine FlowETL menggunakan Python, FastAPI, dan SQLAlchemy 2.0, dukungan 6 jenis konektor (MySQL, PostgreSQL, SQLite, CSV, JSON, JSONL), implementasi fitur *Schema Evolution* adaptif termasuk *Structural Sync (DROP COLUMN)*, inferensi tipe data dinamis pada berkas teks, *type casting transformer*, ragam *load modes* (Append, Truncate, Replace, Sync/Mirror), serta capaian pengujian otomatis Pytest 100% lulus (118 test cases). Kata kunci: *FlowETL, Backend Engine, FastAPI, SQLAlchemy, Database Integration, Schema Evolution, Type Casting*.
* **KATA PENGANTAR**
  * *Tulis apa:* Ungkapan syukur dan terima kasih formal kepada Koordinator Program Studi Ilmu Komputer FMIPA ULM, Dosen Pembimbing Internal, Kepala UPA TIK ULM, Pembimbing Lapangan di UPA TIK ULM, rekan tim kerja praktik, dan keluarga.

---

### **BAB I PENDAHULUAN**

#### 1.1 Latar Belakang Masalah
* *Tulis apa:* 
  * Gambaran umum unit kerja UPA TIK ULM yang mengelola berbagai sistem informasi akademik dan administratif dengan database terpisah-pisah (*data silos*).
  * Masalah ketidaksesuaian struktur dan format data saat proses migrasi (misal migrasi data CSV/JSON ke MySQL atau PostgreSQL di mana tipe data angka atau tanggal sering terbaca sebagai teks biasa).
  * Ketiadaan engine pemrosesan data lokal yang otomatis, ringan, dan aman dari isu SQL identifier injection (nama tabel/kolom mengandung spasi atau reserved words).
  * Masalah inkonsistensi skema data tujuan saat skema sumber mengalami perubahan (penambahan atau penghapusan kolom).
  * Urgensi perancangan backend engine data integrasi modular berbasis web (FlowETL) yang handal, adaptif, dan dapat dieksekusi secara terjadwal.

#### 1.2 Rumusan Masalah
* *Tulis apa:*
  1. Bagaimana merancang arsitektur backend engine FlowETL yang mampu mengabstraksi dan menghubungkan multi-konektor database relasional serta berkas dokumen secara seragam?
  2. Bagaimana mengimplementasikan mekanisme pipeline yang mendukung *Schema Evolution* (termasuk *structural drop column* saat sinkronisasi), inferensi tipe data dinamis, dan penyesuaian tipe (*type casting*) secara otomatis?
  3. Bagaimana membangun REST API berbasis FastAPI dan modul *task scheduling* untuk mendukung orkestrasi pemrosesan data otomatis di latar belakang?

#### 1.3 Tujuan Kerja Praktik
* *Tulis apa:*
  1. Membangun modul backend konektor multi-database (MySQL, PostgreSQL, SQLite) dan berkas (CSV, JSON, JSONL) berbasis SQLAlchemy 2.0 dan iterator streaming.
  2. Mengembangkan core engine transformasi data, deteksi anomali skema (*Schema Evolution*), modul *type casting*, serta penanganan variasi mode pemuatan data (Append, Truncate, Replace, Sync/Mirror).
  3. Mengembangkan REST API modular dengan FastAPI serta *Scheduler Service* berbasis cron/interval untuk automasi eksekusi data pipeline.

#### 1.4 Manfaat Kerja Praktik
* *Tulis apa:*
  * **Bagi Instansi (UPA TIK ULM):** Memiliki mesin pengolah dan penyinkron data internal yang mandiri, adaptif, efisien, dan fleksibel tanpa ketergantungan pada lisensi perangkat lunak pihak ketiga berbayar.
  * **Bagi Mahasiswa:** Memperdalam keahlian rekayasa perangkat lunak backend, optimalisasi query database, penanganan integritas skema data tingkat lanjut, dan arsitektur REST API modern.
  * **Bagi Akademik:** Sebagai referensi karya ilmiah terapan dalam bidang data pipeline engineering dan integrasi sistem heterogen.

---

### **BAB II KEADAAN UMUM INSTITUSI TEMPAT KERJA PRAKTIK**

#### 2.1 Kondisi Umum Instansi
* *Tulis apa:* Sejarah pendirian, kedudukan, tugas pokok, dan fungsi UPA TIK Universitas Lambung Mangkurat sebagai tulang punggung infrastruktur jaringan dan pengembangan sistem informasi universitas.

#### 2.2 Visi dan Misi
* **2.2.1 Visi:** Penjelasan visi resmi UPA TIK ULM dan penjabaran prinsip operasional (*Sistematis, Informatif, Mandiri, Partisipatif, Utuh, Non-Redundansi*).
* **2.2.2 Misi:** Butir-butir misi UPA TIK ULM dalam peningkatan tata kelola TIK universitas.

#### 2.3 Struktur Organisasi
* *Tulis apa:* Bagan hierarki struktur organisasi UPA TIK ULM, posisi pimpinan, staf ahli, dan deskripsi divisi tempat mahasiswa ditempatkan (Divisi Pengembangan Sistem Informasi).

---

### **BAB III TINJAUAN PUSTAKA**

#### 3.1 Sistem Informasi dan Integrasi Data
* *Tulis apa:* Pengertian sistem informasi menurut ahli, konsep data heterogen, definisi integrasi data, dan tantangan interoperabilitas sistem.

#### 3.2 Konsep Extract, Transform, Load (ETL) dan Data Pipeline
* *Tulis apa:* Siklus hidup ETL, perbedaan paradigma ETL vs ELT, teknik pemrosesan data berbasis aliran (*streaming/chunking data*), serta manajemen memori pada pemrosesan dataset besar.

#### 3.3 Bahasa Pemrograman Python
* *Tulis apa:* Keunggulan Python untuk backend dan pemrosesan data, ekosistem pustaka (*libraries*), penanganan tipe data dinamis, dan mekanisme *type hinting*.

#### 3.4 Framework FastAPI dan Konsep Asynchronous API
* *Tulis apa:* Arsitektur ASGI, keunggulan performa FastAPI dibandingkan framework WSGI klasik, penggunaan Pydantic untuk validasi data, serta penyediaan endpoints asynchronous.

#### 3.5 Database Abstraction Layer dan SQLAlchemy 2.0
* **3.5.1 SQLAlchemy Engine & Connection Pooling:** Manajemen koneksi, pool pre-ping, dan eksekusi query raw berparameter.
* **3.5.2 Inspector API:** Mekanisme inspeksi metadata database dinamis (membaca daftar tabel, kolom, tipe data, primary key, dan nullable).
* **3.5.3 Dialek Database Relasional (MySQL, PostgreSQL, SQLite):** Karakteristik dialek SQL, sintaks *identifier quoting* (backticks vs double quotes), dan transaksi ACID.

#### 3.6 Konsep Inferensi Tipe Data dan Type Casting
* *Tulis apa:* Teori inferensi tipe data dari berkas teks tak bertipe (CSV/JSON), pemetaan nilai ke tipe kanonikal (*string, integer, float, decimal, boolean, date, datetime*), serta mekanisme *data casting* dan sanitasi nilai null/anomali sebelum dimuat ke database tujuan.

#### 3.7 Konsep Schema Evolution dan Penjadwalan Tugas (Task Scheduler)
* *Tulis apa:* Teori pendeteksian pergeseran skema (*schema drift*), perintah DDL dinamis (`ALTER TABLE ADD/MODIFY/DROP COLUMN`), pembersihan kolom *orphan* pada mode sinkronisasi cermin (*mirror sync*), serta konsep kerja penjadwalan tugas latar belakang berbasis ekspresi cron.

---

### **BAB IV METODE KERJA PRAKTIK**

#### 4.1 Waktu dan Tempat
* *Tulis apa:* Jadwal pelaksanaan kerja praktik (periode bulan pelaksanaan, hari kerja Senin–Jumat pukul 09.00–16.00 WITA), lokasi kantor UPA TIK ULM Banjarbaru, serta identitas pembimbing internal dan eksternal.

#### 4.2 Bentuk Praktik Kerja Lapangan
* *Tulis apa:* Bentuk kegiatan berupa *Project-Based Internship*, dengan penempatan spesifik sebagai *Backend & Database Engineer* pada proyek pengembangan FlowETL.

#### 4.3 Prosedur Kerja
* *Tulis apa:* Tahapan metodologi pengembangan backend:
  1. *Analisis Kebutuhan Data & Konektor:* Mengidentifikasi tipe database dan format berkas yang aktif digunakan di lingkungan UPA TIK.
  2. *Perancangan Arsitektur Backend:* Mendesain interface konektor (`SourceConnector`, `DestinationConnector`), modul pipeline runner, modul casting transformer, dan skema REST API.
  3. *Implementasi Modul:* Pengkodean komponen konektor, sanitasi identifier SQL, modul evolusi skema (termasuk structural drop column), dan penanganan inferensi tipe data berkas.
  4. *Pengujian Unit & Integrasi:* Pembuatan skrip uji otomatis menggunakan Pytest secara bertahap hingga mencakup 118 skenario uji.
  5. *Deployment & Evaluasi:* Menjalankan server aplikasi, evaluasi penggunaan resource, dan dokumentasi API.

---

### **BAB V PELAKSANAAN KERJA PRAKTIK**

#### 5.1 Evaluasi Pelaksanaan Kerja Praktik
* *Tulis apa:* Evaluasi proses pengerjaan teknis di sisi backend, adaptasi lingkungan komputasi (macOS/Linux), kolaborasi git repository, dan pembagian tugas dengan pengembang frontend.

#### 5.2 Hasil Pengamatan
* **5.2.1 Permasalahan:** Uraian rinci masalah teknis backend yang ditemukan dan diselesaikan:
  * Masalah kegagalan query akibat reserved words atau nama tabel dengan spasi (diatasi dengan dialek *identifier quoting*).
  * Error *"Column specified twice"* pada eksekusi query INSERT (diatasi dengan validasi deduplikasi kolom pada transformer dan modul konektor).
  * Penanganan tabel kosong pada mode *Sync/Mirror* yang rawan menyisakan data kadaluwarsa (diatasi dengan pembersihan tabel tujuan saat baris sumber bernilai 0).
  * Hilangnya dimensi panjang kolom (*length/precision*) saat generate tabel target (diatasi dengan ekstraksi metadata raw_type).
  * Inferensi tipe data berkas CSV/JSON yang sebelumnya kaku (*hardcoded VARCHAR(255)*) sehingga menyebabkan ketidakcocokan tipe numerik dan tanggal di database tujuan (diatasi dengan integrasi `get_schema()` inferensi dinamis dan modul `CastColumnsTransformer`).
  * Ketiadaan penyesuaian struktural saat kolom dihapus pada sumber dalam mode *Sync/Mirror* (diatasi dengan penambahan parameter `allow_drop_columns=True` pada `SchemaEvolutionVerifier` untuk mengeksekusi `ALTER TABLE DROP COLUMN`).
* **5.2.2 Teknologi:** Daftar lengkap piranti lunak backend yang digunakan: Python 3.10+, FastAPI, Uvicorn, SQLAlchemy 2.0, PyMySQL, Psycopg2, Pytest, Pydantic v2.

#### 5.3 Rancang Bangun Backend Engine FlowETL
* *Tulis apa:*
  * **Arsitektur Modular Backend:** Penjelasan modul-modul utama (`app/connectors`, `app/core`, `app/schema`, `app/transformations`, `server/api`).
  * **Desain Konektor Sumber dan Tujuan:** Implementasi kelas `SQLBaseSource`, `SQLBaseDestination`, `CSVSource/Destination`, `JSONDestination`, dan `SQLiteDestination`.
  * **Engine Inferensi Tipe & Modul Casting:** Implementasi `CastColumnsTransformer` pada `app/transformations/casting.py` dan mekanisme *auto-injection* transformer casting pada `pipeline_runner.py` berdasarkan parameter `column_types`.
  * **Engine Schema Evolution Tingkat Lanjut:** Logika deteksi pergeseran kolom baru (`ADD COLUMN`), pelebaran kapasitas tipe (`MODIFY/ALTER COLUMN`), dan penghapusan kolom usang (`DROP COLUMN`) pada mode sinkronisasi cermin.
  * **Mekanisme Pipeline Runner:** Alur kerja ekstraksi berbasis generator memori, penerapan urutan transformasi terurut, dan penyimpanan batch data secara transaksional.
  * **Layanan REST API & Server-Sent Events (SSE):** Spesifikasi endpoint `/api/pipeline/multi-run`, `/api/connector/columns` cerdas, streaming event progres (`data.percent`, `data.step`, `data.output_file`), dan integrasi Scheduler Service.

#### 5.4 Evaluasi dan Pengujian Backend
* *Tulis apa:*
  * **Hasil Pengujian Unit Test (Pytest):** Penyajian tabel lengkap hasil pengujian unit test (total **118 test cases passed** tanpa kegagalan).
  * **Pengujian Integritas Data & Transformasi:** Verifikasi keamanan quoting SQL, integritas tipe data desimal/tanggal via casting, dan ketahanan terhadap kolom yang dihapus pada sumber (EVO-03).
  * **Pengujian Fitur Structural Sync & Casting:** Pengujian skenario penyesuaian skema saat kolom dihapus pada database tujuan serta uji akurasi konversi string ke integer/date.
  * **Pengukuran Kinerja Throughput:** Waktu pemrosesan dan efisiensi memori pada operasi pemindahan ribuan baris data antar basis data.

---

### **BAB VI PENUTUP**

#### 6.1 Kesimpulan
* *Tulis apa:* Jawaban konkret atas rumusan masalah:
  1. Telah berhasil dibangun backend engine FlowETL yang mendukung integrasi 6 jenis sumber data secara modular, aman, dan efisien.
  2. Telah diimplementasikan fitur *Schema Evolution* adaptif (mencakup penambahan, modifikasi, dan penghapusan kolom pada mode sinkronisasi) serta modul *type casting* otomatis yang menjaga akurasi tipe data.
  3. Layanan REST API dan penjadwalan tugas (*Scheduler*) berhasil diintegrasikan dengan tingkat keberhasilan uji unit test 100% (**118 passed**).

#### 6.2 Saran
* *Tulis apa:* Saran untuk pengembangan backend di masa mendatang: penambahan konektor NoSQL (MongoDB), integrasi protokol *Change Data Capture (CDC)* berbasis log binari, serta optimasi *distributed task queue* (Celery/Redis).

---

### **DAFTAR PUSTAKA**
* *Tulis apa:* Referensi buku teks dan jurnal ilmiah mengenai Rekayasa Perangkat Lunak, Arsitektur Database, FastAPI, SQLAlchemy, dan Data Warehouse.

### **LAMPIRAN**
* **Lampiran A:** Potongan Source Code Backend Penting (`sql_base.py`, `pipeline.py`, `evolution.py`, `casting.py`).
* **Lampiran B:** Log Hasil Uji Unit Testing Pytest (118 Passed).
* **Lampiran C:** Dokumentasi Skema REST API (OpenAPI / Swagger).
* **Lampiran D:** Berkas Administrasi KP (Form Bimbingan dan Surat Keterangan Selesai).

---
---

# 📗 LAPORAN 2 (MAHASISWA 2) — FRONTEND, UI/UX & PENGUJIAN SISTEM

### **JUDUL:**
> **RANCANG BANGUN ANTARMUKA VISUAL PIPELINE BUILDER DAN PENGUJIAN SISTEM PADA APLIKASI FLOWETL DI UNIT PENUNJANG AKADEMIK TEKNOLOGI INFORMASI DAN KOMUNIKASI UNIVERSITAS LAMBUNG MANGKURAT**

---

### **DAFTAR ISI DAN KETERANGAN ISI (TULIS APA):**

```text
HALAMAN JUDUL
LEMBAR PENGESAHAN
ABSTRAK
KATA PENGANTAR
DAFTAR ISI
DAFTAR GAMBAR
DAFTAR TABEL
DAFTAR LAMPIRAN
```

* **ABSTRAK**
  * *Tulis apa:* Ringkasan eksekutif (maksimal 250 kata). Uraikan tingginya kebutuhan antarmuka visual yang intuitif bagi staf non-programmer untuk mengoperasikan integrasi data di UPA TIK ULM, perancangan UI/UX berbasis web menggunakan HTML5, CSS3, dan Vanilla JavaScript modern, fitur unggulan *visual pipeline builder*, drag-and-drop file upload dengan deteksi kolom dan penyesuaian tipe (*type override select*), tombol aksi cepat pemetaan kolom (*1-to-1 & Ignore*), validasi pencegahan duplikasi target pemetaan, monitoring progres live melalui *Server-Sent Events (SSE)*, serta evaluasi sistem berbasis simulasi pengguna awam (*Random User Simulator*) dan pengujian kualitas (*QA Logic Bug Hunting*) hingga mencapai status *production-ready*. Kata kunci: *FlowETL, User Interface, Visual Pipeline Builder, Server-Sent Events, Software QA, Black-box Testing, Column Mapping*.
* **KATA PENGANTAR**
  * *Tulis apa:* Ungkapan syukur dan terima kasih formal kepada Koordinator Program Studi Ilmu Komputer FMIPA ULM, Dosen Pembimbing Internal, Kepala UPA TIK ULM, Pembimbing Lapangan di UPA TIK ULM, rekan tim pengembang backend, dan keluarga.

---

### **BAB I PENDAHULUAN**

#### 1.1 Latar Belakang Masalah
* *Tulis apa:*
  * Fenomena pengolahan data di lingkungan universitas yang sebagian besar dikerjakan oleh staf non-teknis tanpa keahlian coding SQL.
  * Kompleksitas aplikasi ETL konvensional yang memiliki antarmuka membingungkan, banyak istilah teknis database, dan minim umpan balik visual saat proses berjalan.
  * Ketiadaan antarmuka visual yang menyajikan visualisasi pemetaan skema, kustomisasi tipe data kolom berkas secara langsung, serta dialog konfirmasi keamanan terhadap operasi destruktif (*Replace/Truncate*).
  * Masalah lambatnya konfigurasi pemetaan kolom jika pengguna harus memilih kolom tujuan satu per satu secara manual.
  * Kebutuhan perancangan antarmuka *Pipeline Builder* yang ramah pengguna, responsif, memiliki aksi cepat, dan teruji secara ketat terhadap perilaku acak pengguna awam.

#### 1.2 Rumusan Masalah
* *Tulis apa:*
  1. Bagaimana merancang antarmuka pengguna visual *Pipeline Builder* yang memudahkan konfigurasi sumber data, tujuan, kustomisasi tipe kolom, dan pemetaan skema secara cepat?
  2. Bagaimana mengimplementasikan komunikasi real-time pada antarmuka web untuk menyajikan visualisasi progres eksekusi dan umpan balik error yang informatif?
  3. Bagaimana menguji dan mengevaluasi keandalan fungsional antarmuka serta logika aplikasi FlowETL menggunakan perspektif *Random User Simulator* dan *QA Bug Hunting*?

#### 1.3 Tujuan Kerja Praktik
* *Tulis apa:*
  1. Merancang dan mengimplementasikan antarmuka visual berbasis web (*Single Page Application*) yang mencakup panel builder, checklist kustomisasi tipe kolom berkas, tombol aksi cepat pemetaan (*1-to-1 & Ignore*), dan manajemen jadwal.
  2. Mengembangkan modul interaksi klien untuk *auto-detect file columns*, konfigurasi transformer interaktif (filter, mask, case convert), serta visualisasi progres live via *Server-Sent Events*.
  3. Melakukan pengujian fungsionalitas dan kualitas perangkat lunak (*QA Black-box Testing*) secara komprehensif untuk memastikan aplikasi bebas bug logika dan siap digunakan pada tahap produksi.

#### 1.4 Manfaat Kerja Praktik
* *Tulis apa:*
  * **Bagi Instansi (UPA TIK ULM):** Memperoleh aplikasi integrasi data visual siap pakai yang mempermudah staf administratif memindahkan data tanpa harus menunggu antrean penanganan oleh tim programmer.
  * **Bagi Mahasiswa:** Mengasah keterampilan desain antarmuka berbasis kebutuhan pengguna (*User-Centered Design*), penguasaan arsitektur web frontend modern, dan metodologi jaminan mutu perangkat lunak (*Quality Assurance*).
  * **Bagi Akademik:** Menyediakan rujukan implementasi desain UI teknis yang dipadukan dengan metodologi pengujian perangkat lunak sistemik.

---

### **BAB II KEADAAN UMUM INSTITUSI TEMPAT KERJA PRAKTIK**

#### 2.1 Kondisi Umum Instansi
* *Tulis apa:* Sejarah pendirian, kedudukan, tugas pokok, dan fungsi UPA TIK Universitas Lambung Mangkurat sebagai penyedia layanan infrastruktur dan aplikasi terintegrasi.

#### 2.2 Visi dan Misi
* **2.2.1 Visi:** Penjelasan visi resmi UPA TIK ULM dan penjabaran prinsip operasional (*Sistematis, Informatif, Mandiri, Partisipatif, Utuh, Non-Redundansi*).
* **2.2.2 Misi:** Butir-butir misi UPA TIK ULM dalam mendukung layanan akademik berstandar mutu tinggi.

#### 2.3 Struktur Organisasi
* *Tulis apa:* Struktur organisasi UPA TIK ULM dan letak penempatan kerja praktik pada divisi pengembangan aplikasi.

---

### **BAB III TINJAUAN PUSTAKA**

#### 3.1 Teori Antarmuka Pengguna (UI) dan Pengalaman Pengguna (UX)
* *Tulis apa:* Definisi UI dan UX menurut literatur, prinsip desain antarmuka (konsistensi, affordance, visibilitas status sistem, pencegahan kesalahan/error prevention, *efficiency of use*).

#### 3.2 Teknologi Pengembangan Web Sisi Klien (Frontend)
* **3.2.1 HTML5 & Formulir Dinamis:** Struktur semantik, elemen interaktif `<select>`, atribut aksesibilitas, dan penanganan unggahan berkas.
* **3.2.2 Cascading Style Sheets (CSS3):** Sistem layout Flexbox dan CSS Grid, penataan tema responsif, styling komponen form kustom (`.column-type-select`), dan animasi transisi.
* **3.2.3 Vanilla JavaScript Modern (ES6+):** Manipulasi Document Object Model (DOM), penanganan event asynchronous, Promise, dan Fetch API.

#### 3.3 Komunikasi Real-Time Web: Server-Sent Events (SSE)
* *Tulis apa:* Prinsip kerja protokol *EventSource* di browser, perbandingan SSE dengan polling dan WebSocket, serta efisiensi transmisi data stream satu arah untuk log progres.

#### 3.4 Desain Interaksi Pemetaan Data dan Aksi Cepat (Quick Actions)
* *Tulis apa:* Pola antarmuka pemetaan relasi kolom sumber-ke-tujuan, pencegahan duplikasi target pemetaan (*duplicate target mapping prevention*), tombol aksi massal (*quick actions: 1-to-1 matching, ignore all*), dan visualisasi checklist kolom dinamis.

#### 3.5 Metodologi Pengujian dan Jaminan Mutu Perangkat Lunak (Software QA)
* **3.5.1 Black-Box Testing:** Metode pengujian berbasis spesifikasi tanpa melihat kode internal.
* **3.5.2 Simulasi Pengguna Awam (Random User Simulation):** Pengujian dengan skenario tidak ideal, input kosong, klik ganda, dan pembatalan mendadak.
* **3.5.3 Logic Bug Hunting & Uji Regresi:** Metodologi pencarian anomali logika sistem, verifikasi integritas data hasil operasi, dan uji regresi pasca-perbaikan bug.

---

### **BAB IV METODE KERJA PRAKTIK**

#### 4.1 Waktu dan Tempat
* *Tulis apa:* Rincian waktu pelaksanaan kerja praktik di UPA TIK ULM, jam kerja operasional, serta data pembimbing.

#### 4.2 Bentuk Praktik Kerja Lapangan
* *Tulis apa:* Pelaksanaan kerja praktik berupa *Project-Based Internship* dengan spesialisasi peran sebagai *Frontend Developer & Software QA Engineer*.

#### 4.3 Prosedur Kerja
* *Tulis apa:* Alur metodologi perancangan antarmuka dan pengujian:
  1. *Analisis Pengguna & Alur Kerja (User Journey):* Menentukan langkah pengguna dari memilih sumber data, menyesuaikan tipe, memetakan kolom, hingga unduh hasil.
  2. *Perancangan Wireframe & Layout UI:* Merancang tata letak halaman utama, drawer status, checklist kolom bertipe dinamis, dan kontrol pemetaan cepat.
  3. *Implementasi Antarmuka:* Pengkodean komponen visual, interaksi DOM, dan integrasi API / SSE.
  4. *Fase Pengujian QA & Simulasi Pengguna:* Menjalankan matriks pengujian acak, pencatatan bug, dan verifikasi perbaikan.
  5. *Uji Kelayakan Akhir & Dokumentasi*.

---

### **BAB V PELAKSANAAN KERJA PRAKTIK**

#### 5.1 Evaluasi Pelaksanaan Kerja Praktik
* *Tulis apa:* Analisis pelaksanaan kerja praktik dari kacamata UI/UX dan penjaminan mutu, tantangan koordinasi integrasi frontend-backend, dan proses iterasi perbaikan bug.

#### 5.2 Hasil Pengamatan
* **5.2.1 Permasalahan:** Daftar cacat antarmuka dan logika sistem yang ditemukan saat audit QA:
  * Tombol *Run Pipeline* macet dan tidak dapat ditekan kembali setelah terjadi error.
  * Tidak adanya fasilitas unduh berkas hasil untuk keluaran SQLite dan JSON Lines pada drawer penyelesaian.
  * Kolom berkas CSV/JSON tidak terdeteksi saat diunggah sehingga pengguna tidak dapat memilih kolom target.
  * Tipe data berkas yang terkunci pada `VARCHAR(255)` tanpa adanya kontrol bagi pengguna untuk mengubah tipe data kolom sebelum dimigrasi.
  * Pemetaan kolom yang lambat dan rawan salah saat pengguna harus memilih target satu per satu untuk puluhan kolom.
  * Fitur transformer filter numerik dan string tidak tersedia pada antarmuka.
  * Ketiadaan dialog peringatan bahaya saat pengguna memilih mode destruktif (*Replace/Truncate*).
  * Pemicuan jadwal otomatis yang tidak memunculkan drawer progres pemantauan real-time.
* **5.2.2 Teknologi:** Daftar piranti lunak frontend dan testing: HTML5, CSS3, Vanilla JS, Chrome DevTools, Git, Postman/cURL.

#### 5.3 Rancang Bangun Antarmuka Visual FlowETL
* *Tulis apa:*
  * **Tata Letak Antarmuka (Layout Structure):** Tampilan dashboard terbagi: Panel Konfigurasi Sumber, Panel Tujuan, Panel Transformasi, dan Header Status.
  * **Fitur Drag-and-Drop & Dropdown Penyesuaian Tipe Kolom:** Implementasi zona unggah berkas, pemanggilan API inspeksi kolom cerdas, penyajian komponen checklist kolom dinamis, dan elemen `<select class="column-type-select">` untuk pemilihan tipe data manual.
  * **Komponen Column Mapping & Tombol Aksi Cepat:** Antarmuka pemetaan visual kolom sumber ke tujuan dilengkapi tombol **"Petakan 1-ke-1"** dan **"Abaikan Semua"**, serta validasi pencegahan duplikasi target pemetaan.
  * **Komponen Real-Time Progress Drawer:** Panel geser interaktif untuk memantau progres persentase (0–100%), visualisasi pesan log langkah demi langkah, penanganan pesan error ramah pengguna, tombol *Tutup & Coba Lagi*, serta tombol unduh berkas hasil.
  * **Antarmuka Penjadwalan & Riwayat Eksekusi:** Halaman pengelolaan jadwal aktif, pemicuan manual jadwal terintegrasi drawer, dan tabel riwayat eksekusi lampau.

#### 5.4 Evaluasi dan Hasil Pengujian Sistem (QA Report)
* *Tulis apa:*
  * **Matriks Hasil Pengujian Fungsional (Black-Box Test Cases):** Tabel lengkap hasil uji fitur utama (koneksi database, upload file, type override, pemetaan 1-to-1, eksekusi pipeline, filter transformer).
  * **Hasil Pengujian Simulasi Pengguna Awam:** Pembuktian penanganan input kosong, proteksi tombol dari klik ganda, pencegahan pemilihan kolom tujuan ganda, dan responsivitas notifikasi toast.
  * **Verifikasi Perbaikan Bug Kritis:** Bukti pengujian keberhasilan perbaikan issue tombol macet, ketersediaan tombol unduh file, berfungsinya type override select, dan kebenaran eksekusi modal peringatan mode replace.
  * **Evaluasi Kesiapan Produksi:** Penilaian kesiapan rilis sistem berdasarkan stabilitas antarmuka dan konsistensi data hasil pemindahan.

---

### **BAB VI PENUTUP**

#### 6.1 Kesimpulan
* *Tulis apa:* Jawaban konkret atas rumusan masalah:
  1. Telah berhasil dibangun antarmuka visual *Pipeline Builder* FlowETL yang intuitif, responsif, dilengkapi fasilitas penyesuaian tipe data langsung dan aksi cepat pemetaan kolom.
  2. Implementasi streaming progres real-time via *Server-Sent Events* berhasil memberikan transparansi proses dan umpan balik error yang jelas tanpa perlu memuat ulang halaman.
  3. Serangkaian pengujian QA dan simulasi pengguna awam telah berhasil memvalidasi perbaikan seluruh bug logika dan antarmuka, membuktikan bahwa FlowETL telah mencapai tingkat kematangan siap produksi (*production-ready*).

#### 6.2 Saran
* *Tulis apa:* Saran untuk pengembangan antarmuka dan QA di masa mendatang: penyediaan kanvas visual berbasis node (*drag-and-drop node graph*), fitur tur panduan interaktif (*interactive onboarding*) bagi pengguna baru, serta otomatisasi pengujian antarmuka menggunakan Playwright atau Cypress.

---

### **DAFTAR PUSTAKA**
* *Tulis apa:* Referensi buku teks dan jurnal ilmiah mengenai Human-Computer Interaction (HCI), Desain UI/UX Web, Standar Pengujian Perangkat Lunak, dan Pemrograman JavaScript Modern.

### **LAMPIRAN**
* **Lampiran A:** Tangkapan Layar Lengkap Antarmuka Pengguna FlowETL (Pipeline Builder, Type Override Select, Quick Mapping, Drawer, Modal, Schedules).
* **Lampiran B:** Tabel Matriks Lengkap Pengujian Sistem (QA Test Matrix & Hasil Eksekusi).
* **Lampiran C:** Potongan Kode Frontend Kunci (`app.js` event stream, file column detector & override, column mapping quick actions).
* **Lampiran D:** Berkas Administrasi KP (Form Bimbingan dan Surat Keterangan Selesai).
