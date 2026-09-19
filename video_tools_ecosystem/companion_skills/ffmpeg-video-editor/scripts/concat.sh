#!/usr/bin/env bash
# concat.sh — Concatenate video files using FFmpeg concat demuxer
# Usage: concat.sh [OPTIONS] <output_file> <input1> [input2 ...]
#
# Options:
#   -r, --reencode    Re-encode output (default: stream copy)
#   -v, --vcodec      Video codec for re-encode (default: libx264)
#   -a, --acodec      Audio codec for re-encode (default: aac)
#   --crf             CRF value for re-encode (default: 23)
#   --preset          x264/x265 preset (default: slow)
#   -k, --keep-list   Keep the temporary concat list file
#   -h, --help        Show this help
#
# Examples:
#   concat.sh out.mp4 a.mp4 b.mp4 c.mp4
#   concat.sh --reencode -v libx265 --crf 28 out.mp4 a.mp4 b.mp4

set -euo pipefail

usage() {
  sed -n '2,16p' "$0" | sed 's/^# //'
  exit 0
}

REENCODE=0
VCODEC="libx264"
ACODEC="aac"
CRF=23
PRESET="slow"
KEEP_LIST=0
OUTPUT=""
INPUTS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    -r|--reencode)   REENCODE=1; shift ;;
    -v|--vcodec)     VCODEC="$2"; shift 2 ;;
    -a|--acodec)     ACODEC="$2"; shift 2 ;;
    --crf)           CRF="$2"; shift 2 ;;
    --preset)        PRESET="$2"; shift 2 ;;
    -k|--keep-list)  KEEP_LIST=1; shift ;;
    -h|--help)       usage ;;
    -*)              echo "Unknown option: $1" >&2; exit 1 ;;
    *)
      if [[ -z "$OUTPUT" ]]; then
        OUTPUT="$1"
      else
        INPUTS+=("$1")
      fi
      shift
      ;;
  esac
done

# ── Validation ───────────────────────────────────────────────────────────────
if [[ -z "$OUTPUT" ]]; then
  echo "Error: No output file specified." >&2
  echo "Usage: concat.sh [OPTIONS] <output_file> <input1> [input2 ...]" >&2
  exit 1
fi

if [[ ${#INPUTS[@]} -lt 2 ]]; then
  echo "Error: At least two input files are required." >&2
  exit 1
fi

if ! command -v ffmpeg &>/dev/null; then
  echo "Error: ffmpeg not found. Install FFmpeg first." >&2
  exit 1
fi

for f in "${INPUTS[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "Error: Input file not found: $f" >&2
    exit 1
  fi
done

# ── Build concat list ────────────────────────────────────────────────────────
LIST_FILE=$(mktemp /tmp/concat_list_XXXXXX.txt)

cleanup() {
  if [[ $KEEP_LIST -eq 0 && -f "$LIST_FILE" ]]; then
    rm -f "$LIST_FILE"
  else
    echo "Concat list kept at: $LIST_FILE"
  fi
}
trap cleanup EXIT

for f in "${INPUTS[@]}"; do
  # Use absolute paths to avoid issues with working directory
  abs_path=$(realpath "$f")
  # Escape single quotes in file paths
  escaped="${abs_path//\'/\'\\\'\'}"
  printf "file '%s'\n" "$escaped" >> "$LIST_FILE"
done

echo "Concat list:"
cat "$LIST_FILE"
echo ""
echo "Output: $OUTPUT"
echo "Inputs: ${#INPUTS[@]} files"
echo ""

# ── Build ffmpeg command ─────────────────────────────────────────────────────
FFMPEG_ARGS=(
  -f concat
  -safe 0
  -i "$LIST_FILE"
)

if [[ $REENCODE -eq 0 ]]; then
  echo "Mode: stream copy (no re-encode)"
  FFMPEG_ARGS+=(
    -c copy
  )
else
  echo "Mode: re-encode  (${VCODEC}, CRF=${CRF}, preset=${PRESET})"
  FFMPEG_ARGS+=(
    -c:v "$VCODEC"
    -crf "$CRF"
    -preset "$PRESET"
    -c:a "$ACODEC"
    -b:a 128k
  )
  # Add faststart for MP4 outputs
  if [[ "$OUTPUT" == *.mp4 || "$OUTPUT" == *.m4v ]]; then
    FFMPEG_ARGS+=(-movflags +faststart)
  fi
fi

FFMPEG_ARGS+=(-y "$OUTPUT")

echo ""
echo "Running: ffmpeg ${FFMPEG_ARGS[*]}"
echo ""

ffmpeg "${FFMPEG_ARGS[@]}"

echo ""
echo "Done! Output: $OUTPUT"

# Print output file info
if command -v ffprobe &>/dev/null; then
  echo ""
  ffprobe -v error \
    -show_entries format=duration,size,bit_rate \
    -of default=noprint_wrappers=1 \
    "$OUTPUT"
fi
