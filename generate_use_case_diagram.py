#!/usr/bin/env python3
"""
Generator script for:
1. USE_CASE_DIAGRAM_SISTEM_INTEGRASI_DATA.drawio (Native editable draw.io XML)
2. USE_CASE_DIAGRAM_SISTEM_INTEGRASI_DATA.svg (High-res vector diagram)
"""

import xml.etree.ElementTree as ET
import os

OUTPUT_DIR = "/Users/ghn/.gemini/antigravity/scratch/ngoding anjay"

def create_drawio_xml():
    mxfile = ET.Element('mxfile', host='app.diagrams.net', agent='Antigravity', version='24.0.0')
    diagram = ET.SubElement(mxfile, 'diagram', id='usecase-diagram', name='Use Case Diagram')
    model = ET.SubElement(diagram, 'mxGraphModel', dx='1200', dy='1200', grid='1', gridSize='10',
                          guides='1', tooltips='1', connect='1', arrows='1', fold='1',
                          page='1', pageScale='1', pageWidth='1100', pageHeight='2500')
    root = ET.SubElement(model, 'root')

    # Root layers
    ET.SubElement(root, 'mxCell', id='0')
    ET.SubElement(root, 'mxCell', id='1', parent='0')

    # 1. System Boundary Box
    boundary_style = (
        "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1D1D1F;strokeWidth=2;"
        "verticalAlign=top;fontStyle=1;fontSize=14;fontFamily=Times New Roman;fontColor=#1D1D1F;"
        "spacingTop=15;"
    )
    b_cell = ET.SubElement(root, 'mxCell', id='boundary_1',
                           value='SISTEM INTEGRASI DATA BERBASIS WEB',
                           style=boundary_style, parent='1', vertex='1')
    ET.SubElement(b_cell, 'mxGeometry', x='230', y='40', width='780', height='2360', as_='geometry')

    # 2. Actors
    actor_style = (
        "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;"
        "fillColor=#FFFFFF;strokeColor=#1D1D1F;strokeWidth=1.5;fontFamily=Times New Roman;"
        "fontSize=12;fontStyle=1;fontColor=#1D1D1F;"
    )

    # Actor 1: Operator Data
    act1 = ET.SubElement(root, 'mxCell', id='actor_operator', value='Operator Data',
                         style=actor_style, parent='1', vertex='1')
    ET.SubElement(act1, 'mxGeometry', x='60', y='420', width='70', height='130', as_='geometry')

    # Actor 2: Administrator Sistem
    act2 = ET.SubElement(root, 'mxCell', id='actor_admin', value='Administrator Sistem',
                         style=actor_style, parent='1', vertex='1')
    ET.SubElement(act2, 'mxGeometry', x='60', y='1420', width='70', height='130', as_='geometry')

    # Use Case Oval Styles
    hub_style = (
        "ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1D1D1F;strokeWidth=1.5;"
        "fontFamily=Times New Roman;fontSize=11;fontStyle=1;fontColor=#1D1D1F;align=center;"
    )
    sub_style = (
        "ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1D1D1F;strokeWidth=1.2;"
        "fontFamily=Times New Roman;fontSize=10.5;fontColor=#1D1D1F;align=center;"
    )

    # Solid Connector (Actor to Use Case)
    solid_edge_style = (
        "endArrow=none;html=1;strokeColor=#1D1D1F;strokeWidth=1.5;rounded=0;entryX=0;entryY=0.5;"
    )

    # Dashed <<include>> Connector
    include_edge_style = (
        "endArrow=open;dashed=1;html=1;strokeColor=#1D1D1F;strokeWidth=1.2;rounded=0;endFill=0;"
        "fontFamily=Times New Roman;fontSize=9;fontStyle=2;fontColor=#1D1D1F;labelBackgroundColor=#FFFFFF;"
    )

    # Dashed <<extend>> Connector
    extend_edge_style = (
        "endArrow=open;dashed=1;html=1;strokeColor=#1D1D1F;strokeWidth=1.2;rounded=0;endFill=0;"
        "fontFamily=Times New Roman;fontSize=9;fontStyle=2;fontColor=#1D1D1F;labelBackgroundColor=#FFFFFF;"
    )

    # Data structures for nodes
    hubs = [
        # Top
        ("uc_engine", "Lihat Status Engine & Metrik Sistem", 270, 90, 240, 50, True, True),
        ("uc_template", "Pilih Template Pipeline Siap Pakai", 270, 160, 240, 50, True, True),
        # Source
        ("uc_source", "Konfigurasi Sumber Data", 270, 370, 240, 52, True, True),
        # Transform
        ("uc_transform", "Konfigurasi Transformasi dan Pemetaan", 270, 720, 240, 52, True, True),
        # Destination
        ("uc_dest", "Konfigurasi Tujuan Data & Mode Muat", 270, 1100, 240, 52, True, True),
        # Execution
        ("uc_run", "Eksekusi Pipeline Data", 270, 1440, 240, 52, True, True),
        # Schedule
        ("uc_schedule", "Kelola Penjadwalan Tugas (Scheduler)", 270, 1760, 240, 52, False, True),
        # History & Files
        ("uc_history", "Lihat Riwayat Eksekusi & Audit Log", 270, 1980, 240, 50, True, True),
        ("uc_files", "Kelola & Unduh Berkas Data (File Manager)", 270, 2060, 240, 50, True, True),
    ]

    for uid, label, x, y, w, h, conn_op, conn_adm in hubs:
        cell = ET.SubElement(root, 'mxCell', id=uid, value=label, style=hub_style, parent='1', vertex='1')
        ET.SubElement(cell, 'mxGeometry', x=str(x), y=str(y), width=str(w), height=str(h), as_='geometry')

        # Connect to Operator
        if conn_op:
            edge = ET.SubElement(root, 'mxCell', id=f"edge_op_{uid}", style=solid_edge_style,
                                 parent='1', source='actor_operator', target=uid, edge='1')
            ET.SubElement(edge, 'mxGeometry', relative='1', as_='geometry')

        # Connect to Admin
        if conn_adm:
            edge = ET.SubElement(root, 'mxCell', id=f"edge_adm_{uid}", style=solid_edge_style,
                                 parent='1', source='actor_admin', target=uid, edge='1')
            ET.SubElement(edge, 'mxGeometry', relative='1', as_='geometry')

    # Sub-Use Cases & Relationships
    # (id, label, x, y, w, h, target_hub, relation_type)
    subs = [
        # Source sub-nodes
        ("sub_upload", "Upload Berkas Dokumen\n(CSV, Excel, JSON, SQLite)", 640, 270, 270, 50, "uc_source", "extend"),
        ("sub_db_conn", "Koneksi Basis Data Relasional\n(MySQL, PostgreSQL, Oracle)", 640, 340, 270, 50, "uc_source", "extend"),
        ("sub_inspect", "Inspeksi Struktur Kolom Otomatis", 640, 410, 270, 48, "uc_source", "include"),
        ("sub_override", "Override Tipe Kolom Data\n(Type Casting)", 640, 475, 270, 48, "uc_source", "include"),

        # Transform sub-nodes
        ("sub_mapping", "Pemetaan Kolom Sumber ke Tujuan\n(1-ke-1 & Ignore)", 640, 580, 270, 48, "uc_transform", "include"),
        ("sub_text_clean", "Pembersihan & Format Teks\n(Trim & Case Convert)", 640, 645, 270, 48, "uc_transform", "include"),
        ("sub_null", "Penanganan Nilai Kosong\n(Fill Null & Drop Null)", 640, 710, 270, 48, "uc_transform", "include"),
        ("sub_mask", "Penyensoran Data Sensitif\n(Masking Telepon/NIK)", 640, 775, 270, 48, "uc_transform", "include"),
        ("sub_filter", "Penyaringan Baris Data\n(Row Filtering)", 640, 840, 270, 48, "uc_transform", "include"),

        # Destination sub-nodes
        ("sub_file_dest", "Format Berkas Ekspor Target\n(CSV, Excel, SQLite, JSONL)", 640, 970, 270, 50, "uc_dest", "extend"),
        ("sub_db_dest", "Basis Data Target\n(MySQL, PostgreSQL, Oracle)", 640, 1040, 270, 50, "uc_dest", "extend"),
        ("sub_load_mode", "Pemilihan Mode Muat Data\n(Sync, Append, Truncate, Replace)", 640, 1110, 270, 50, "uc_dest", "include"),
        ("sub_danger_modal", "Konfirmasi Peringatan\nOperasi Destruktif", 640, 1180, 270, 48, "uc_dest", "include"),

        # Run sub-nodes
        ("sub_schema_evo", "Verifikasi Evolusi Skema\n(ADD / DROP Column)", 640, 1370, 270, 48, "uc_run", "include"),
        ("sub_sse_monitor", "Pemantauan Progres Real-Time\n(SSE Stream 0-100%)", 640, 1435, 270, 48, "uc_run", "include"),
        ("sub_drawer_dl", "Unduh Berkas Hasil Langsung\ndari Progress Drawer", 640, 1500, 270, 48, "uc_run", "include"),

        # Schedule sub-nodes
        ("sub_sched_cron", "Tambah Jadwal Cron Baru &\nPicu Eksekusi Manual", 640, 1760, 270, 50, "uc_schedule", "include"),
    ]

    for sid, slabel, sx, sy, sw, sh, hub_id, rel_type in subs:
        scell = ET.SubElement(root, 'mxCell', id=sid, value=slabel, style=sub_style, parent='1', vertex='1')
        ET.SubElement(scell, 'mxGeometry', x=str(sx), y=str(sy), width=str(sw), height=str(sh), as_='geometry')

        if rel_type == "include":
            # Panah dari Hub -> Sub dengan label <<include>>
            edge = ET.SubElement(root, 'mxCell', id=f"rel_{hub_id}_{sid}", value='&lt;&lt;include&gt;&gt;',
                                 style=include_edge_style, parent='1', source=hub_id, target=sid, edge='1')
            ET.SubElement(edge, 'mxGeometry', relative='1', as_='geometry')
        elif rel_type == "extend":
            # Panah dari Sub -> Hub dengan label <<extend>>
            edge = ET.SubElement(root, 'mxCell', id=f"rel_{sid}_{hub_id}", value='&lt;&lt;extend&gt;&gt;',
                                 style=extend_edge_style, parent='1', source=sid, target=hub_id, edge='1')
            ET.SubElement(edge, 'mxGeometry', relative='1', as_='geometry')

    tree = ET.ElementTree(mxfile)
    drawio_path = os.path.join(OUTPUT_DIR, "USE_CASE_DIAGRAM_SISTEM_INTEGRASI_DATA.drawio")
    tree.write(drawio_path, encoding='utf-8', xml_declaration=True)
    print(f"File .drawio berhasil dibuat: {drawio_path}")

create_drawio_xml()
