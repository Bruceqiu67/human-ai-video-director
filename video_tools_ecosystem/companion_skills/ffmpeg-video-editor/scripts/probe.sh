#!/usr/bin/env bash
# probe.sh — Inspect a media file using ffprobe
# Usage: probe.sh [OPTIONS] <input_file>
#
# Options:
#   -j, --json        Full JSON output (default: summary)
#   -v, --video       Video stream info only
#   -a, --audio       Audio stream info only
#   -f, --format      Container/format info only
#   -s, --streams     All streams summary
#   -h, --help        Show this help

set -euo pipefail

usage() {
  sed -n '2,12p' "$0" | sed 's/^# //'
  exit 0
}

JSON=0
MODE="summary"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -j|--json)   JSON=1; shift ;;
    -v|--video)  MODE="video"; shift ;;
    -a|--audio)  MODE="audio"; shift ;;
    -f|--format) MODE="format"; shift ;;
    -s|--streams) MODE="streams"; shift ;;
    -h|--help)   usage ;;
    -*)          echo "Unknown option: $1" >&2; exit 1 ;;
    *)           INPUT="$1"; shift ;;
  esac
done

if [[ -z "${INPUT:-}" ]]; then
  echo "Error: No input file specified." >&2
  echo "Usage: probe.sh [OPTIONS] <input_file>" >&2
  exit 1
fi

if [[ ! -f "$INPUT" ]]; then
  echo "Error: File not found: $INPUT" >&2
  exit 1
fi

if ! command -v ffprobe &>/dev/null; then
  echo "Error: ffprobe not found. Install FFmpeg first." >&2
  exit 1
fi

# ── Full JSON mode ───────────────────────────────────────────────────────────
if [[ $JSON -eq 1 ]]; then
  ffprobe -v error \
    -show_streams \
    -show_format \
    -of json \
    "$INPUT"
  exit 0
fi

# ── Format / container info ──────────────────────────────────────────────────
show_format() {
  ffprobe -v error \
    -show_entries format=filename,nb_streams,format_name,format_long_name,duration,size,bit_rate \
    -of default=noprint_wrappers=1 \
    "$INPUT"
}

# ── Video stream info ────────────────────────────────────────────────────────
show_video() {
  ffprobe -v error \
    -select_streams v:0 \
    -show_entries stream=index,codec_name,codec_long_name,profile,width,height,\
r_frame_rate,avg_frame_rate,pix_fmt,bit_rate,nb_frames,duration \
    -of default=noprint_wrappers=1 \
    "$INPUT"
}

# ── Audio stream info ────────────────────────────────────────────────────────
show_audio() {
  ffprobe -v error \
    -select_streams a \
    -show_entries stream=index,codec_name,codec_long_name,sample_rate,channels,\
channel_layout,bit_rate,duration,nb_frames \
    -of default=noprint_wrappers=1 \
    "$INPUT"
}

# ── All streams summary ──────────────────────────────────────────────────────
show_streams() {
  ffprobe -v error \
    -show_entries stream=index,codec_type,codec_name,width,height,sample_rate,channels,bit_rate,duration \
    -of default=noprint_wrappers=1 \
    "$INPUT"
}

# ── Human-friendly summary (default) ────────────────────────────────────────
show_summary() {
  echo "════════════════════════════════════════════════════"
  echo " File: $INPUT"
  echo "════════════════════════════════════════════════════"

  echo ""
  echo "── Container ──────────────────────────────────────"
  ffprobe -v error \
    -show_entries format=format_long_name,duration,size,bit_rate \
    -of default=noprint_wrappers=1 \
    "$INPUT" | while IFS='=' read -r key val; do
      case "$key" in
        format_long_name) printf "  Format   : %s\n" "$val" ;;
        duration)         printf "  Duration : %s s (%.2f min)\n" "$val" "$(echo "$val/60" | bc -l 2>/dev/null || echo '?')" ;;
        size)             printf "  Size     : %s bytes (%.1f MB)\n" "$val" "$(echo "$val/1048576" | bc -l 2>/dev/null || echo '?')" ;;
        bit_rate)         printf "  Bit rate : %s bps\n" "$val" ;;
      esac
    done

  echo ""
  echo "── Video ───────────────────────────────────────────"
  local vinfo
  vinfo=$(ffprobe -v error -select_streams v:0 \
    -show_entries stream=codec_name,profile,width,height,r_frame_rate,pix_fmt,bit_rate \
    -of default=noprint_wrappers=1 "$INPUT" 2>/dev/null)
  if [[ -z "$vinfo" ]]; then
    echo "  (no video stream)"
  else
    echo "$vinfo" | while IFS='=' read -r key val; do
      case "$key" in
        codec_name)   printf "  Codec    : %s\n" "$val" ;;
        profile)      printf "  Profile  : %s\n" "$val" ;;
        width)        printf "  Width    : %s px\n" "$val" ;;
        height)       printf "  Height   : %s px\n" "$val" ;;
        r_frame_rate) printf "  Frame rate: %s\n" "$val" ;;
        pix_fmt)      printf "  Pixel fmt: %s\n" "$val" ;;
        bit_rate)     printf "  Bit rate : %s bps\n" "$val" ;;
      esac
    done
  fi

  echo ""
  echo "── Audio ───────────────────────────────────────────"
  local acount
  acount=$(ffprobe -v error -select_streams a \
    -show_entries stream=index -of csv=p=0 "$INPUT" 2>/dev/null | wc -l)
  if [[ "$acount" -eq 0 ]]; then
    echo "  (no audio stream)"
  else
    echo "  Streams  : $acount"
    ffprobe -v error -select_streams a:0 \
      -show_entries stream=codec_name,sample_rate,channels,channel_layout,bit_rate \
      -of default=noprint_wrappers=1 "$INPUT" 2>/dev/null | while IFS='=' read -r key val; do
        case "$key" in
          codec_name)     printf "  Codec    : %s\n" "$val" ;;
          sample_rate)    printf "  Sample rate: %s Hz\n" "$val" ;;
          channels)       printf "  Channels : %s\n" "$val" ;;
          channel_layout) printf "  Layout   : %s\n" "$val" ;;
          bit_rate)       printf "  Bit rate : %s bps\n" "$val" ;;
        esac
      done
  fi
  echo "════════════════════════════════════════════════════"
}

case "$MODE" in
  summary) show_summary ;;
  video)   show_video ;;
  audio)   show_audio ;;
  format)  show_format ;;
  streams) show_streams ;;
esac
