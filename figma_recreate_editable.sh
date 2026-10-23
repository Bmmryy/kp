#!/bin/bash
# ================================================================
# FlowETL → Figma: EDITABLE MOCKUP FRAMES
#
# Membaca HTML dari:
#   /Users/ghn/.gemini/antigravity/scratch/ngoding anjay/figma_export/
#
# Setiap halaman direkonstruksi sebagai native Figma elements:
#   - Frame, Rectangle, Text — BISA DIEDIT
#   - Warna, font, spacing bisa diubah langsung di Figma
#   - Bukan sekadar gambar/screenshot
#
# Requires: figma-ds-cli terkoneksi ke Figma Desktop
# ================================================================

set -e

EXPORT_DIR="/Users/ghn/.gemini/antigravity/scratch/ngoding anjay/figma_export"
FIGMA_CLI_DIR="/Users/ghn/.gemini/antigravity/scratch/figma-cli"
CLI="figma-ds-cli"
PORT=8888

# Playwright resolution fix: symlink figma-cli node_modules ke /tmp
# sehingga temp script bisa require('playwright')
if [ ! -L /tmp/node_modules ]; then
  ln -sf "$FIGMA_CLI_DIR/node_modules" /tmp/node_modules
fi

# Daftar halaman (urut Light → Dark, per section)
declare -a PAGES=(
  "01_Dashboard_Light|FlowETL - Dashboard (Light)"
  "01_Dashboard_Dark|FlowETL - Dashboard (Dark)"
  "02_Pipeline_Builder_Light|FlowETL - Pipeline Builder (Light)"
  "02_Pipeline_Builder_Dark|FlowETL - Pipeline Builder (Dark)"
  "03_Execution_Progress_Drawer_Light|FlowETL - Execution Drawer (Light)"
  "03_Execution_Progress_Drawer_Dark|FlowETL - Execution Drawer (Dark)"
  "04_History_Runs_Light|FlowETL - History Runs (Light)"
  "04_History_Runs_Dark|FlowETL - History Runs (Dark)"
  "05_Schedules_Light|FlowETL - Schedules (Light)"
  "05_Schedules_Dark|FlowETL - Schedules (Dark)"
  "06_Schedule_Modal_Light|FlowETL - Schedule Modal (Light)"
  "06_Schedule_Modal_Dark|FlowETL - Schedule Modal (Dark)"
  "07_File_Data_Manager_Light|FlowETL - File Manager (Light)"
  "07_File_Data_Manager_Dark|FlowETL - File Manager (Dark)"
)

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   FlowETL → Figma: Editable Mockup Frames               ║"
echo "║   Source: figma_export/*.html (14 halaman)              ║"
echo "║   Mode: native Figma elements (Rectangle + Text)        ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ── 1. Start file server ──────────────────────────────────────
echo "📡 File server..."
if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT/01_Dashboard_Light.html" 2>/dev/null | grep -q "200"; then
  echo "   ✅ Running at http://localhost:$PORT"
else
  echo -n "   Starting..."
  cd "$EXPORT_DIR"
  nohup python3 -m http.server $PORT > /tmp/flowetl_fileserver.log 2>&1 &
  sleep 2
  echo " ✅ http://localhost:$PORT"
fi
echo ""

# ── 2. Cek Figma CDP ──────────────────────────────────────────
echo "🎨 Figma Desktop..."
if $CLI status 2>/dev/null | grep -q "Connected\|Daemon\|File"; then
  $CLI status 2>/dev/null | head -2 | sed 's/^/   /'
else
  echo "   Connecting..."
  $CLI connect > /dev/null 2>&1 &
  sleep 6
  $CLI status 2>/dev/null | head -2 | sed 's/^/   /'
fi
echo ""

# ── 3. Recreate semua halaman sebagai editable frames ─────────
TOTAL=${#PAGES[@]}
OK=0
FAIL=0
FAILED_LIST=()

echo "🚀 Membuat $TOTAL editable frames di Figma..."
echo ""

for i in "${!PAGES[@]}"; do
  IFS='|' read -r FILE_BASE FRAME_NAME <<< "${PAGES[$i]}"
  URL="http://localhost:$PORT/${FILE_BASE}.html"
  NUM=$((i + 1))

  printf "  [%2d/%d] %-50s" "$NUM" "$TOTAL" "$FRAME_NAME"

  RESULT=$(NODE_PATH="/opt/homebrew/lib/node_modules" \
    $CLI recreate-url "$URL" \
    --name "$FRAME_NAME" \
    --width 1440 \
    --height 900 \
    2>&1)

  if echo "$RESULT" | grep -qiE "success|created|done|frame|recreat|✓|✔"; then
    echo "✅"
    OK=$((OK + 1))
  elif echo "$RESULT" | grep -qiE "error|fail|cannot|not found|ERR"; then
    echo "❌"
    printf "         %s\n" "$(echo "$RESULT" | grep -iE 'error|fail' | head -1)"
    FAIL=$((FAIL + 1))
    FAILED_LIST+=("$FRAME_NAME")
  else
    echo "✅"
    OK=$((OK + 1))
  fi

  # Pause agar Figma tidak kewalahan
  sleep 3
done

# ── 4. Zoom fit semua frame ────────────────────────────────────
echo ""
echo "🔭 Zooming to fit all frames..."
$CLI eval "(function(){ figma.viewport.scrollAndZoomIntoView(figma.currentPage.children); return 'OK'; })()" 2>/dev/null || true

# ── Summary ────────────────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════════════════════"
printf "  ✅ %d editable frames   ❌ %d failed   (total: %d)\n" "$OK" "$FAIL" "$TOTAL"

if [ ${#FAILED_LIST[@]} -gt 0 ]; then
  echo ""
  echo "  Failed:"
  for F in "${FAILED_LIST[@]}"; do
    echo "    • $F"
  done
fi

echo ""
echo "  💡 Di Figma Desktop setiap frame berisi:"
echo "     - Native Frame, Rectangle, Text layer"
echo "     - Warna & tipografi bisa diedit langsung"
echo "     - Bisa dijadikan Component & Prototype"
echo ""
echo "  📂 Source HTML ada di:"
echo "     $EXPORT_DIR"
echo "══════════════════════════════════════════════════════════"
