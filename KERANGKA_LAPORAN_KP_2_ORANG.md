# KERANGKA LAPORAN KERJA PRAKTIK (2 JUDUL TERPISAH)
### Proyek: FlowETL — Platform Integrasi Data Visual Berbasis Web
### Lokasi: Unit Penunjang Akademik Teknologi Informasi dan Komunikasi (UPA TIK) Universitas Lambung Mangkurat
### Format Referensi: `LaporanAkhir_KP_Muhammad Agung Permana.docx`

---

## 📌 Ringkasan Pembagian Judul & Spesialisasi

| Atribut | Laporan 1 (Mahasiswa 1) | Laporan 2 (Mahasiswa 2) |
| :--- | :--- | :--- |
| **Fokus Bidang** | Backend Engineering & Database Pipeline Integration | Frontend UI/UX, Visual Builder & System QA Testing |
| **Judul Laporan** | **PENGEMBANGAN BACKEND ENGINE DAN PIPELINE INTEGRASI MULTI-DATABASE PADA APLIKASI FLOWETL DI UNIT PENUNJANG AKADEMIK TEKNOLOGI INFORMASI DAN KOMUNIKASI UNIVERSITAS LAMBUNG MANGKURAT** | **RANCANG BANGUN ANTARMUKA VISUAL PIPELINE BUILDER DAN PENGUJIAN SISTEM PADA APLIKASI FLOWETL DI UNIT PENUNJANG AKADEMIK TEKNOLOGI INFORMASI DAN KOMUNIKASI UNIVERSITAS LAMBUNG MANGKURAT** |
| **Karakter Bab III** | Arsitektur ETL, SQLAlchemy, Dialek SQL, Schema Evolution, Task Scheduler | Teori UI/UX, DOM & Fetch API, Server-Sent Events (SSE), Metodologi Black-Box QA |
| **Karakter Bab V.3** | Engine Konektor, Generator DDL, Pydantic Schema, Sanitasi Data, REST API | Layouting Dashboard, Interaksi Drag-Drop, Real-Time Progress Drawer, Mapping UI |
| **Karakter Bab V.4** | Pytest Automation (112 test cases), Throughput Data, Integritas Transaksi ACID | Black-box Testing Matrix, User Simulation, Uji Regresi Bug Integritas Data |

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
  * *Tulis apa:* Ringkasan eksekutif (maksimal 250 kata). Uraikan latar belakang tantangan integrasi data heterogen di UPA TIK ULM, tujuan pengembangan backend engine FlowETL menggunakan Python, FastAPI, dan SQLAlchemy, dukungan 6 jenis konektor (MySQL, PostgreSQL, SQLite, CSV, JSON, JSONL), implementasi fitur *Schema Evolution*, ragam *load modes* (Append, Truncate, Replace, Sync/Mirror), serta capaian pengujian unit test 100% lulus (112 test cases). Kata kunci: *FlowETL, Backend Engine, FastAPI, SQLAlchemy, Database Integration, Schema Evolution*.
* **KATA PENGANTAR**
  * *Tulis apa:* Ungkapan syukur dan terima kasih formal kepada Koordinator Program Studi Ilmu Komputer FMIPA ULM, Dosen Pembimbing Internal, Kepala UPA TIK ULM, Pembimbing Lapangan di UPA TIK ULM, rekan tim kerja praktik, dan keluarga.

---

### **BAB I PENDAHULUAN**

#### 1.1 Latar Belakang Masalah
* *Tulis apa:* 
  * Gambaran umum unit kerja UPA TIK ULM yang mengelola berbagai sistem informasi akademik dan administratif dengan database terpisah-pisah (*data silos*).
  * Masalah ketidaksesuaian struktur dan format data saat proses migrasi (misal migrasi data CSV/JSON ke MySQL atau PostgreSQL).
  * Ketiadaan engine pemrosesan data lokal yang otomatis, ringan, dan aman dari isu SQL identifier injection (nama tabel/kolom mengandung spasi atau reserved words).
  * Urgensi perancangan backend engine data integrasi modular berbasis web (FlowETL) yang handal dan dapat dieksekusi secara terjadwal.

#### 1.2 Rumusan Masalah
* *Tulis apa:*
  1. Bagaimana merancang arsitektur backend engine FlowETL yang mampu mengabstraksi dan menghubungkan multi-konektor database relasional serta berkas dokumen secara seragam?
  2. Bagaimana mengimplementasikan mekanisme pipeline yang mendukung *Schema Evolution*, sanitasi kolom, dan variasi mode pemuatan data (*load modes*) secara aman?
  3. Bagaimana membangun REST API berbasis FastAPI dan modul *task scheduling* untuk mendukung orkestrasi pemrosesan data otomatis di latar belakang?

#### 1.3 Tujuan Kerja Praktik
* *Tulis apa:*
  1. Membangun modul backend konektor multi-database (MySQL, PostgreSQL, SQLite) dan file (CSV, JSON, JSONL) berbasis SQLAlchemy 2.0 dan iterator streaming.
  2. Mengimplementasikan core engine transformasi data, deteksi anomali struktur skema (*Schema Evolution*), dan penanganan mode sinkronisasi (Append, Truncate, Replace, Sync/Mirror).
  3. Mengembangkan REST API modular dengan FastAPI serta *Scheduler Service* berbasis cron/interval untuk automasi eksekusi data pipeline.

#### 1.4 Manfaat Kerja Praktik
* *Tulis apa:*
  * **Bagi Instansi (UPA TIK ULM):** Memiliki mesin pengolah dan penyinkron data internal yang mandiri, efisien, dan fleksibel tanpa ketergantungan pada lisensi perangkat lunak pihak ketiga berbayar.
  * **Bagi Mahasiswa:** Memperdalam keahlian rekayasa perangkat lunak backend, optimalisasi query database, penanganan konkurensi data tingkat lanjut, dan arsitektur REST API modern.
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

#### 3.6 Format Berkas Data (CSV, JSON, JSONL)
* *Tulis apa:* Karakteristik teknis berkas CSV (*delimiter, quoting, header*), JSON terstruktur, dan JSON Lines untuk data berorientasi *stream*.

#### 3.7 Konsep Schema Evolution dan Penjadwalan Tugas (Task Scheduler)
* *Tulis apa:* Teori pendeteksian pergeseran skema (*schema drift*), perintah DDL dinamis (`ALTER TABLE`, pelebaran kapasitas VARCHAR ke TEXT), serta konsep kerja penjadwalan berbasis cron ekspresi.

---

### **BAB IV METODE KERJA PRAKTIK**

#### 4.1 Waktu dan Tempat
* *Tulis apa:* Jadwal pelaksanaan kerja praktik (periode bulan pelaksanaan, hari kerja Senin–Jumat pukul 09.00–16.00 WITA), lokasi kantor UPA TIK ULM Banjarbaru, serta identitas pembimbing internal dan eksternal.

#### 4.2 Bentuk Praktik Kerja Lapangan
* *Tulis apa:* Bentuk kegiatan berupa *Project-Based Internship*, dengan penempatan spesifik sebagai *Backend & Database Engineer* pada proyek pengembangan FlowETL.

#### 4.3 Prosedur Kerja
* *Tulis apa:* Tahapan metodologi pengembangan backend:
  1. *Analisis Kebutuhan Data & Konektor:* Mengidentifikasi tipe database dan file yang aktif digunakan di UPA TIK.
  2. *Perancangan Arsitektur Backend:* Mendesain interface konektor (`SourceConnector`, `DestinationConnector`), modul pipeline runner, dan skema REST API.
  3. *Implementasi Modul:* Pengkodean komponen konektor, sanitasi identifier SQL, modul evolusi skema, dan transformer data.
  4. *Pengujian Unit & Integrasi:* Pembuatan skrip uji otomatis menggunakan Pytest.
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
* **5.2.2 Teknologi:** Daftar lengkap piranti lunak backend yang digunakan: Python 3.10+, FastAPI, Uvicorn, SQLAlchemy 2.0, PyMySQL, Psycopg2, Pytest, Pydantic v2.

#### 5.3 Rancang Bangun Backend Engine FlowETL
* *Tulis apa:*
  * **Arsitektur Modular Backend:** Penjelasan modul-modul utama (`app/connectors`, `app/core`, `app/schema`, `app/transformations`, `server/api`).
  * **Desain Konektor Sumber dan Tujuan:** Implementasi kelas `SQLBaseSource`, `SQLBaseDestination`, `CSVSource/Destination`, `JSONDestination`, dan `SQLiteDestination`.
  * **Mekanisme Pipeline Runner:** Alur kerja ekstraksi berbasis generator memori, penerapan urutan transformasi, dan penyimpanan batch data.
  * **Engine Schema Evolution:** Logika perbandingan skema sumber dan tujuan, pemetaan tipe data kanonikal (`TypeRegistry`), dan eksekusi otomatis perintah DDL penyesuaian kolom.
  * **Layanan REST API & Server-Sent Events (SSE):** Spesifikasi endpoint `/api/pipeline/multi-run`, streaming event progres (`data.percent`, `data.step`, `data.output_file`), dan integrasi Scheduler Service.

#### 5.4 Evaluasi dan Pengujian Backend
* *Tulis apa:*
  * **Hasil Pengujian Unit Test (Pytest):** Penyajian tabel lengkap hasil pengujian unit test (112 test cases passed tanpa kegagalan).
  * **Pengujian Integritas Data:** Verifikasi keamanan quoting SQL, integritas tipe data desimal/tanggal, dan ketahanan terhadap kolom yang dihapus pada sumber (EVO-03).
  * **Pengukuran Kinerja Throughput:** Waktu pemrosesan dan efisiensi memori pada operasi pemindahan ribuan baris data antar basis data.

---

### **BAB VI PENUTUP**

#### 6.1 Kesimpulan
* *Tulis apa:* Jawaban konkret atas rumusan masalah:
  1. Telah berhasil dibangun backend engine FlowETL yang mendukung integrasi 6 jenis sumber data secara modular dan aman.
  2. Telah diimplementasikan fitur *Schema Evolution* dan penanganan ragam mode muat data (*Append, Truncate, Replace, Sync*) yang menjaga integritas data secara konsisten.
  3. Layanan REST API dan penjadwalan tugas (*Scheduler*) berhasil diintegrasikan dengan tingkat keberhasilan uji unit test 100% (112 passed).

#### 6.2 Saran
* *Tulis apa:* Saran untuk pengembangan backend di masa mendatang: penambahan konektor NoSQL (MongoDB), integrasi protokol *Change Data Capture (CDC)* berbasis log binari, serta optimasi *distributed task queue* (Celery/Redis).

---

### **DAFTAR PUSTAKA**
* *Tulis apa:* Referensi buku teks dan jurnal ilmiah mengenai Rekayasa Perangkat Lunak, Arsitektur Database, FastAPI, SQLAlchemy, dan Data Warehouse.

### **LAMPIRAN**
* **Lampiran A:** Potongan Source Code Backend Penting (`sql_base.py`, `pipeline.py`, `evolution.py`).
* **Lampiran B:** Log Hasil Uji Unit Testing Pytest (112 Passed).
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
  * *Tulis apa:* Ringkasan eksekutif (maksimal 250 kata). Uraikan tingginya kebutuhan antarmuka visual yang intuitif bagi staf non-programmer untuk mengoperasikan integrasi data di UPA TIK ULM, perancangan UI/UX berbasis web menggunakan HTML5, CSS3, dan Vanilla JavaScript, fitur unggulan *visual pipeline builder*, drag-and-drop file upload dengan deteksi kolom otomatis, pemetaan relasi kolom (*column mapping*), monitoring progres live melalui *Server-Sent Events (SSE)*, serta evaluasi sistem berbasis simulasi pengguna awam (*Random User Simulator*) dan pengujian kualitas (*QA Logic Bug Hunting*) hingga mencapai status *production-ready*. Kata kunci: *FlowETL, User Interface, Visual Pipeline Builder, Server-Sent Events, Software QA, Black-box Testing*.
* **KATA PENGANTAR**
  * *Tulis apa:* Ungkapan syukur dan terima kasih formal kepada Koordinator Program Studi Ilmu Komputer FMIPA ULM, Dosen Pembimbing Internal, Kepala UPA TIK ULM, Pembimbing Lapangan di UPA TIK ULM, rekan tim pengembang backend, dan keluarga.

---

### **BAB I PENDAHULUAN**

#### 1.1 Latar Belakang Masalah
* *Tulis apa:*
  * Fenomena pengolahan data di lingkungan universitas yang sebagian besar dikerjakan oleh staf non-teknis tanpa keahlian coding SQL.
  * Kompleksitas aplikasi ETL konvensional yang memiliki antarmuka membingungkan, banyak istilah teknis database, dan minim umpan balik visual saat proses berjalan.
  * Ketiadaan antarmuka visual yang menyajikan visualisasi pemetaan skema, auto-detect struktur berkas unggahan, serta dialog konfirmasi keamanan terhadap operasi destruktif (*Replace/Truncate*).
  * Kebutuhan perancangan antarmuka *Pipeline Builder* yang ramah pengguna, responsif, dan teruji secara ketat terhadap perilaku acak pengguna awam.

#### 1.2 Rumusan Masalah
* *Tulis apa:*
  1. Bagaimana merancang antarmuka pengguna visual *Pipeline Builder* yang memudahkan konfigurasi sumber data, tujuan, dan transformasi secara interaktif?
  2. Bagaimana mengimplementasikan komunikasi real-time pada antarmuka web untuk menyajikan visualisasi progres eksekusi dan umpan balik error yang informatif?
  3. Bagaimana menguji dan mengevaluasi keandalan fungsional antarmuka serta logika aplikasi FlowETL menggunakan perspektif *Random User Simulator* dan *QA Bug Hunting*?

#### 1.3 Tujuan Kerja Praktik
* *Tulis apa:*
  1. Merancang dan mengimplementasikan antarmuka visual berbasis web (*Single Page Application*) yang mencakup panel builder, pemetaan skema, dan manajemen jadwal.
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
* *Tulis apa:* Definisi UI dan UX menurut literatur, prinsip desain antarmuka (konsistensi, affordance, visibilitas status sistem, pencegahan kesalahan/error prevention).

#### 3.2 Teknologi Pengembangan Web Sisi Klien (Frontend)
* **3.2.1 HTML5 & Formulir Dinamis:** Struktur semantik, elemen interaktif, atribut aksesibilitas, dan penanganan unggahan berkas.
* **3.2.2 Cascading Style Sheets (CSS3):** Sistem layout Flexbox dan CSS Grid, penataan tema responsif, styling card, dan animasi transisi.
* **3.2.3 Vanilla JavaScript Modern (ES6+):** Manipulasi Document Object Model (DOM), penanganan event asynchronous, Promise, dan Fetch API.

#### 3.3 Komunikasi Real-Time Web: Server-Sent Events (SSE)
* *Tulis apa:* Prinsip kerja protokol *EventSource* di browser, perbandingan SSE dengan polling dan WebSocket, serta efisiensi transmisi data stream satu arah untuk log progres.

#### 3.4 Desain Interaksi Pemetaan Data (Visual Data Mapping)
* *Tulis apa:* Pola antarmuka pemetaan relasi kolom, visualisasi seleksi checklist kolom, dan formulir aturan transformasi data bersyarat (*conditional form rules*).

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
  1. *Analisis Pengguna & Alur Kerja (User Journey):* Menentukan langkah pengguna dari memilih sumber data hingga unduh hasil.
  2. *Perancangan Wireframe & Layout UI:* Merancang tata letak halaman utama, drawer status, checklist kolom, dan modal dialog.
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
  * Fitur transformer filter numerik dan string tidak tersedia pada antarmuka.
  * Ketiadaan dialog peringatan bahaya saat pengguna memilih mode destruktif (*Replace/Truncate*).
  * Pemicuan jadwal otomatis yang tidak memunculkan drawer progres pemantauan real-time.
* **5.2.2 Teknologi:** Daftar piranti lunak frontend dan testing: HTML5, CSS3, Vanilla JS, Chrome DevTools, Git, Postman/cURL.

#### 5.3 Rancang Bangun Antarmuka Visual FlowETL
* *Tulis apa:*
  * **Tata Letak Antarmuka (Layout Structure):** Tampilan dashboard terbagi: Panel Konfigurasi Sumber, Panel Tujuan, Panel Transformasi, dan Header Status.
  * **Fitur Drag-and-Drop & Auto-Detection Kolom:** Implementasi zona unggah berkas, pemanggilan API inspeksi kolom otomatis, dan penyajian komponen checklist kolom dinamis.
  * **Komponen Column Mapping & Transformer:** Antarmuka pemetaan visual kolom sumber ke tujuan dan form konfigurasi filter bersyarat.
  * **Komponen Real-Time Progress Drawer:** Panel geser interaktif untuk memantau progres persentase (0–100%), visualisasi pesan log langkah demi langkah, penanganan pesan error ramah pengguna, tombol *Tutup & Coba Lagi*, serta tombol unduh berkas hasil.
  * **Antarmuka Penjadwalan & Riwayat Eksekusi:** Halaman pengelolaan jadwal aktif, pemicuan manual jadwal terintegrasi drawer, dan tabel riwayat eksekusi lampau.

#### 5.4 Evaluasi dan Hasil Pengujian Sistem (QA Report)
* *Tulis apa:*
  * **Matriks Hasil Pengujian Fungsional (Black-Box Test Cases):** Tabel lengkap hasil uji fitur utama (koneksi database, upload file, eksekusi pipeline, filter transformer).
  * **Hasil Pengujian Simulasi Pengguna Awam:** Pembuktian penanganan input kosong, proteksi tombol dari klik ganda, dan responsivitas notifikasi toast.
  * **Verifikasi Perbaikan Bug Kritis:** Bukti pengujian keberhasilan perbaikan issue tombol macet, ketersediaan tombol unduh file, berfungsinya filter transformer, dan kebenaran eksekusi modal peringatan mode replace.
  * **Evaluasi Kesiapan Produksi:** Penilaian kesiapan rilis sistem berdasarkan stabilitas antarmuka dan konsistensi data hasil pemindahan.

---

### **BAB VI PENUTUP**

#### 6.1 Kesimpulan
* *Tulis apa:* Jawaban konkret atas rumusan masalah:
  1. Telah berhasil dibangun antarmuka visual *Pipeline Builder* FlowETL yang intuitif, responsif, dan mudah dipahami oleh staf non-teknis.
  2. Implementasi streaming progres real-time via *Server-Sent Events* berhasil memberikan transparansi proses dan umpan balik error yang jelas tanpa perlu memuat ulang halaman.
  3. Serangkaian pengujian QA dan simulasi pengguna awam telah berhasil memvalidasi perbaikan seluruh bug logika dan antarmuka, membuktikan bahwa FlowETL telah mencapai tingkat kematangan siap produksi (*production-ready*).

#### 6.2 Saran
* *Tulis apa:* Saran untuk pengembangan antarmuka dan QA di masa mendatang: penyediaan kanvas visual berbasis node (*drag-and-drop node graph*), fitur tur panduan interaktif (*interactive onboarding*) bagi pengguna baru, serta otomatisasi pengujian antarmuka menggunakan Playwright atau Cypress.

---

### **DAFTAR PUSTAKA**
* *Tulis apa:* Referensi buku teks dan jurnal ilmiah mengenai Human-Computer Interaction (HCI), Desain UI/UX Web, Standar Pengujian Perangkat Lunak, dan Pemrograman JavaScript Modern.

### **LAMPIRAN**
* **Lampiran A:** Tangkapan Layar Lengkap Antarmuka Pengguna FlowETL (Pipeline Builder, Drawer, Modal, Schedules).
* **Lampiran B:** Tabel Matriks Lengkap Pengujian Sistem (QA Test Matrix & Hasil Eksekusi).
* **Lampiran C:** Potongan Kode Frontend Kunci (`app.js` event stream, file column detector, drawer handler).
* **Lampiran D:** Berkas Administrasi KP (Form Bimbingan dan Surat Keterangan Selesai).
