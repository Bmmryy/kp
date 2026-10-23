#!/bin/bash
# ============================================================
# FlowETL → Figma: Import All 14 PNG Frames
# Uses figma-ds-cli eval (CDP → Figma Plugin API)
# No Playwright needed — uses existing PNG screenshots
# ============================================================

set -e

EXPORT_DIR="/Users/ghn/.gemini/antigravity/scratch/ngoding anjay/figma_export"
CLI="figma-ds-cli"

# Frame layout: 2880px wide, 120px gap, stacked in 2 rows (Light / Dark)
FRAME_W=2880
FRAME_H=1800
GAP=200

# [index, file_base, display_name, row(0=Light,1=Dark), col]
declare -a FILES=(
  "01_Dashboard_Light|FlowETL - Dashboard (Light)|0|0"
  "01_Dashboard_Dark|FlowETL - Dashboard (Dark)|1|0"
  "02_Pipeline_Builder_Light|FlowETL - Pipeline Builder (Light)|0|1"
  "02_Pipeline_Builder_Dark|FlowETL - Pipeline Builder (Dark)|1|1"
  "03_Execution_Progress_Drawer_Light|FlowETL - Execution Drawer (Light)|0|2"
  "03_Execution_Progress_Drawer_Dark|FlowETL - Execution Drawer (Dark)|1|2"
  "04_History_Runs_Light|FlowETL - History Runs (Light)|0|3"
  "04_History_Runs_Dark|FlowETL - History Runs (Dark)|1|3"
  "05_Schedules_Light|FlowETL - Schedules (Light)|0|4"
  "05_Schedules_Dark|FlowETL - Schedules (Dark)|1|4"
  "06_Schedule_Modal_Light|FlowETL - Schedule Modal (Light)|0|5"
  "06_Schedule_Modal_Dark|FlowETL - Schedule Modal (Dark)|1|5"
  "07_File_Data_Manager_Light|FlowETL - File Manager (Light)|0|6"
  "07_File_Data_Manager_Dark|FlowETL - File Manager (Dark)|1|6"
)

echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║    FlowETL → Figma: Import 14 PNG Frames           ║"
echo "║    via figma-ds-cli CDP                            ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

# Verify Figma connection
echo "⚡ Checking Figma connection..."
$CLI status > /dev/null 2>&1 && echo "✅ Connected" || { echo "❌ Not connected. Run: figma-ds-cli connect"; exit 1; }
echo ""

TOTAL=${#FILES[@]}
OK=0
FAIL=0
FAILED_LIST=()

for i in "${!FILES[@]}"; do
  IFS='|' read -r FILE_BASE FRAME_NAME ROW COL <<< "${FILES[$i]}"
  PNG_PATH="$EXPORT_DIR/${FILE_BASE}.png"
  NUM=$((i + 1))

  echo -n "[$NUM/$TOTAL] $FRAME_NAME ... "

  if [ ! -f "$PNG_PATH" ]; then
    echo "❌ PNG not found: $PNG_PATH"
    FAIL=$((FAIL + 1))
    FAILED_LIST+=("$FRAME_NAME (file not found)")
    continue
  fi

  # Calculate position: grid layout (row × col)
  X=$(( COL * (FRAME_W + GAP) ))
  Y=$(( ROW * (FRAME_H + GAP) ))

  # Encode PNG to base64
  B64=$(base64 -i "$PNG_PATH")

  # Write eval script to temp file
  TMPJS="/tmp/figma_import_${i}.js"

  cat > "$TMPJS" << JSEOF
(async () => {
  try {
    const dataUrl = "data:image/png;base64,${B64}";
    const image = await figma.createImageAsync(dataUrl);
    const { width, height } = await image.getSizeAsync();

    const frame = figma.createFrame();
    frame.name = "${FRAME_NAME}";
    frame.resize(width, height);
    frame.x = ${X};
    frame.y = ${Y};
    frame.fills = [{ type: 'IMAGE', scaleMode: 'FILL', imageHash: image.hash }];

    figma.currentPage.selection = [frame];

    return "OK " + width + "x" + height + " at (" + ${X} + "," + ${Y} + ")";
  } catch (e) {
    return "ERR: " + e.message;
  }
})()
JSEOF

  # Run via figma-ds-cli eval
  RESULT=$($CLI eval --file "$TMPJS" 2>&1)

  if echo "$RESULT" | grep -q "^OK"; then
    echo "✅  $RESULT"
    OK=$((OK + 1))
  else
    echo "❌  $RESULT"
    FAIL=$((FAIL + 1))
    FAILED_LIST+=("$FRAME_NAME")
  fi

  # Cleanup temp file
  rm -f "$TMPJS"

  # Brief pause between imports
  sleep 1
done

# Zoom to fit all frames
echo ""
echo "🔭 Zooming to fit all frames..."
$CLI eval "(function(){ figma.viewport.scrollAndZoomIntoView(figma.currentPage.children); return 'Zoomed'; })()" 2>/dev/null || true

echo ""
echo "════════════════════════════════════════════════════"
echo "✅ $OK imported   ❌ $FAIL failed   (total: $TOTAL)"
if [ ${#FAILED_LIST[@]} -gt 0 ]; then
  echo ""
  echo "Failed frames:"
  for F in "${FAILED_LIST[@]}"; do
    echo "  • $F"
  done
fi
echo ""
echo "🎨 Open Figma Desktop to see all FlowETL frames!"
