#!/usr/bin/env bash
# Download ASR models (GitHub releases) and Fluent 3D icons (MIT) for the shorts skill.
# usage: fetch_assets.sh PROJECT_DIR   (icons -> PROJECT_DIR/icons, models -> $SHORTS_MODELS)
set -euo pipefail
PROJ="${1:?project dir}"
MODELS="${SHORTS_MODELS:-$HOME/.cache/shorts-models}"
REL=https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models
GIGA=sherpa-onnx-nemo-transducer-giga-am-v2-russian-2025-04-19
mkdir -p "$MODELS" "$PROJ/icons" "$PROJ/photos"
pip install -q sherpa-onnx pillow numpy
[ -f "$MODELS/silero_vad.onnx" ] || curl -sSfL -o "$MODELS/silero_vad.onnx" "$REL/silero_vad.onnx"
[ -d "$MODELS/$GIGA" ] || curl -sSfL "$REL/$GIGA.tar.bz2" | tar xj -C "$MODELS"
ICONS=https://raw.githubusercontent.com/microsoft/fluentui-emoji/main/assets
fetch_icon() {  # "Display name" [variant-path]
  local name="$1" file; file="$(echo "$name" | tr 'A-Z ' 'a-z_')_3d.png"
  local url="$ICONS/${name// /%20}/3D/$file"
  [ -n "${2:-}" ] && url="$ICONS/${name// /%20}/$2"
  [ -f "$PROJ/icons/$file" ] || curl -sSf -o "$PROJ/icons/$file" "$url" || echo "missing icon: $name" >&2
}
for n in "Pot of food" "Green salad" "Cut of meat" "Steaming bowl" "Dumpling" "Spaghetti" \
         "Fork and knife with plate" "Bowl with spoon" "Bell"; do fetch_icon "$n"; done
fetch_icon "Thumbs up" "Default/3D/thumbs_up_3d_default.png"
echo "assets ready: models=$MODELS icons=$PROJ/icons"
