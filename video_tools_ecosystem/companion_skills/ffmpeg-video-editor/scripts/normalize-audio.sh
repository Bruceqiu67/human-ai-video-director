#!/usr/bin/env bash
# normalize-audio.sh — Two-pass EBU R128 loudness normalization
# Usage: normalize-audio.sh [OPTIONS] <input> <output>
#
# Options:
#   -I, --integrated  Target integrated loudness in LUFS (default: -16)
#   -T, --true-peak   Max true peak in dBTP (default: -1.5)
#   -L, --lra         Loudness range target in LU (default: 11)
#   -s, --stereo      Force stereo downmix (default: preserve channels)
#   -r, --sample-rate Output sample rate in Hz (default: preserve)
#   --no-video        Drop video stream (default: copy if present)
#   --acodec          Output audio codec (default: aac)
#   --abitrate        Output audio bitrate (default: 192k)
#   -h, --help        Show this help
#
# This script performs the standard two-pass EBU R128 normalization:
#   Pass 1: Analyze the file, capture loudnorm measurements
#   Pass 2: Apply linear normalization using the measured values

set -euo pipefail

usage() {
  sed -n '2,22p' "$0" | sed 's/^# //'
  exit 0
}

TARGET_I="-16"
TARGET_TP="-1.5"
TARGET_LRA="11"
STEREO=0
SAMPLE_RATE=""
PRESERVE_VIDEO=1
ACODEC="aac"
ABITRATE="192k"
INPUT=""
OUTPUT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -I|--integrated)  TARGET_I="$2"; shift 2 ;;
    -T|--true-peak)   TARGET_TP="$2"; shift 2 ;;
    -L|--lra)         TARGET_LRA="$2"; shift 2 ;;
    -s|--stereo)      STEREO=1; shift ;;
    -r|--sample-rate) SAMPLE_RATE="$2"; shift 2 ;;
    --no-video)       PRESERVE_VIDEO=0; shift ;;
    --acodec)         ACODEC="$2"; shift 2 ;;
    --abitrate)       ABITRATE="$2"; shift 2 ;;
    -h|--help)        usage ;;
    -*)               echo "Unknown option: $1" >&2; exit 1 ;;
    *)
      if [[ -z "$INPUT" ]];  then INPUT="$1"
      elif [[ -z "$OUTPUT" ]]; then OUTPUT="$1"
      else echo "Unexpected argument: $1" >&2; exit 1
      fi
      shift
      ;;
  esac
done

# ── Validation ───────────────────────────────────────────────────────────────
if [[ -z "$INPUT" || -z "$OUTPUT" ]]; then
  echo "Error: Input and output files are required." >&2
  echo "Usage: normalize-audio.sh [OPTIONS] <input> <output>" >&2
  exit 1
fi

if [[ ! -f "$INPUT" ]]; then
  echo "Error: Input file not found: $INPUT" >&2
  exit 1
fi

if ! command -v ffmpeg &>/dev/null; then
  echo "Error: ffmpeg not found. Install FFmpeg first." >&2
  exit 1
fi

# ── Build audio filter chain prefix ─────────────────────────────────────────
AF_PREFIX=""
if [[ $STEREO -eq 1 ]]; then
  AF_PREFIX="aformat=channel_layouts=stereo,"
fi
if [[ -n "$SAMPLE_RATE" ]]; then
  AF_PREFIX="${AF_PREFIX}aresample=${SAMPLE_RATE},"
fi

# ── Pass 1: Analyze ──────────────────────────────────────────────────────────
echo "════════════════════════════════════════════════════"
echo " EBU R128 Loudness Normalization"
echo " Input : $INPUT"
echo " Output: $OUTPUT"
echo " Target: I=${TARGET_I} LUFS  TP=${TARGET_TP} dBTP  LRA=${TARGET_LRA} LU"
echo "════════════════════════════════════════════════════"
echo ""
echo "Pass 1/2: Analyzing audio levels..."
echo ""

PASS1_FILTER="${AF_PREFIX}loudnorm=I=${TARGET_I}:TP=${TARGET_TP}:LRA=${TARGET_LRA}:print_format=json"

# Capture pass 1 output (loudnorm prints to stderr)
PASS1_OUTPUT=$(ffmpeg -hide_banner -i "$INPUT" \
  -af "$PASS1_FILTER" \
  -vn -f null - 2>&1 || true)

# Extract JSON block from stderr output
JSON_BLOCK=$(echo "$PASS1_OUTPUT" | awk '/^\{/,/^\}/' | head -20)

if [[ -z "$JSON_BLOCK" ]]; then
  echo "Error: Pass 1 failed to produce loudnorm measurements." >&2
  echo "FFmpeg output:" >&2
  echo "$PASS1_OUTPUT" >&2
  exit 1
fi

echo "Pass 1 measurements:"
echo "$JSON_BLOCK"
echo ""

# Parse measured values using grep/sed (no jq dependency)
parse_json_field() {
  echo "$JSON_BLOCK" | grep "\"$1\"" | sed 's/.*: *"\([^"]*\)".*/\1/' | head -1
}

MEASURED_I=$(parse_json_field "input_i")
MEASURED_TP=$(parse_json_field "input_tp")
MEASURED_LRA=$(parse_json_field "input_lra")
MEASURED_THRESH=$(parse_json_field "input_thresh")
OFFSET=$(parse_json_field "target_offset")

echo "Measured:  I=${MEASURED_I}  TP=${MEASURED_TP}  LRA=${MEASURED_LRA}  Thresh=${MEASURED_THRESH}"
echo "Offset   : ${OFFSET}"
echo ""

if [[ -z "$MEASURED_I" || "$MEASURED_I" == "-inf" ]]; then
  echo "Error: Could not parse loudnorm measurements. Is this a silent file?" >&2
  exit 1
fi

# ── Pass 2: Normalize ────────────────────────────────────────────────────────
echo "Pass 2/2: Applying normalization..."
echo ""

PASS2_FILTER="${AF_PREFIX}loudnorm=I=${TARGET_I}:TP=${TARGET_TP}:LRA=${TARGET_LRA}\
:measured_I=${MEASURED_I}\
:measured_TP=${MEASURED_TP}\
:measured_LRA=${MEASURED_LRA}\
:measured_thresh=${MEASURED_THRESH}\
:offset=${OFFSET}\
:linear=true\
:print_format=summary"

# Build output arguments
FFMPEG_OUT_ARGS=(-c:a "$ACODEC" -b:a "$ABITRATE")

# Check for video streams
HAS_VIDEO=$(ffprobe -v error -select_streams v -show_entries stream=index \
  -of csv=p=0 "$INPUT" 2>/dev/null | wc -l)

if [[ $PRESERVE_VIDEO -eq 1 && $HAS_VIDEO -gt 0 ]]; then
  FFMPEG_OUT_ARGS+=(-c:v copy)
else
  FFMPEG_OUT_ARGS+=(-vn)
fi

# Add faststart for MP4
if [[ "$OUTPUT" == *.mp4 || "$OUTPUT" == *.m4v ]]; then
  FFMPEG_OUT_ARGS+=(-movflags +faststart)
fi

ffmpeg -hide_banner \
  -i "$INPUT" \
  -af "$PASS2_FILTER" \
  "${FFMPEG_OUT_ARGS[@]}" \
  -y "$OUTPUT"

echo ""
echo "════════════════════════════════════════════════════"
echo " Normalization complete!"
echo " Output: $OUTPUT"
echo "════════════════════════════════════════════════════"

# ── Verify output levels ─────────────────────────────────────────────────────
echo ""
echo "Verifying output levels (quick analysis)..."
ffmpeg -hide_banner -i "$OUTPUT" \
  -af "loudnorm=I=${TARGET_I}:TP=${TARGET_TP}:LRA=${TARGET_LRA}:print_format=summary" \
  -vn -f null - 2>&1 | grep -E "Input Integrated|Input True Peak|Input LRA" || true
