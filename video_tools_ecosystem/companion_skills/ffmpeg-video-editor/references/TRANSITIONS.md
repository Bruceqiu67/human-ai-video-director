# FFmpeg xfade Transition Reference

Complete reference for all `xfade` filter transition types.

## Syntax

```bash
ffmpeg -i clip_a.mp4 -i clip_b.mp4 \
  -filter_complex \
    "[0:v][1:v]xfade=transition=TRANSITION_NAME:duration=DURATION:offset=OFFSET[v]; \
     [0:a][1:a]acrossfade=d=DURATION[a]" \
  -map "[v]" -map "[a]" \
  -c:v libx264 -crf 23 -preset slow \
  -c:a aac output.mp4
```

**Parameters:**
- `transition` — Transition effect name (see table below)
- `duration` — Overlap duration in seconds (e.g. `1.0`)
- `offset` — Time in clip A when transition starts (seconds from beginning)

**Tip:** `offset` = clip A duration − transition duration

---

## All Transition Types

| Name | Visual Description |
|------|--------------------|
| `fade` | Classic fade through black |
| `fadeblack` | Fade to black then in from black |
| `fadewhite` | Fade to white then in from white |
| `fadegrays` | Fade through grayscale |
| `dissolve` | Standard cross-dissolve blend |
| `pixelize` | Pixelate out, then pixelate in |
| `wipeleft` | Wipe from right to left |
| `wiperight` | Wipe from left to right |
| `wipeup` | Wipe from bottom to top |
| `wipedown` | Wipe from top to bottom |
| `slideleft` | Clip B slides in from right |
| `slideright` | Clip B slides in from left |
| `slideup` | Clip B slides in from bottom |
| `slidedown` | Clip B slides in from top |
| `smoothleft` | Smooth edge wipe left |
| `smoothright` | Smooth edge wipe right |
| `smoothup` | Smooth edge wipe up |
| `smoothdown` | Smooth edge wipe down |
| `circlecrop` | Crop to expanding/contracting circle |
| `rectcrop` | Crop to expanding/contracting rectangle |
| `circleopen` | Circle iris opens from center |
| `circleclose` | Circle iris closes to center |
| `vertopen` | Vertical split opens outward |
| `vertclose` | Vertical split closes inward |
| `horzopen` | Horizontal split opens outward |
| `horzclose` | Horizontal split closes inward |
| `zoomin` | Zoom in (clip B scales up) |
| `squeezev` | Vertical squeeze transition |
| `squeezeh` | Horizontal squeeze transition |
| `hlwind` | Horizontal left wind/swipe |
| `hrwind` | Horizontal right wind/swipe |
| `vuwind` | Vertical up wind/swipe |
| `vdwind` | Vertical down wind/swipe |
| `coverleft` | Clip B covers from right to left |
| `coverright` | Clip B covers from left to right |
| `coverup` | Clip B covers from bottom to top |
| `coverdown` | Clip B covers from top to bottom |
| `revealleft` | Clip A reveals from right to left |
| `revealright` | Clip A reveals from left to right |
| `revealup` | Clip A reveals from bottom to top |
| `revealdown` | Clip A reveals from top to bottom |
| `diagtl` | Diagonal wipe top-left |
| `diagtr` | Diagonal wipe top-right |
| `diagbl` | Diagonal wipe bottom-left |
| `diagbr` | Diagonal wipe bottom-right |

---

## Quick Examples

### Dissolve
```bash
ffmpeg -i a.mp4 -i b.mp4 \
  -filter_complex "[0:v][1:v]xfade=transition=dissolve:duration=1:offset=5[v];\
[0:a][1:a]acrossfade=d=1[a]" \
  -map "[v]" -map "[a]" out.mp4
```

### Fade to Black
```bash
ffmpeg -i a.mp4 -i b.mp4 \
  -filter_complex "[0:v][1:v]xfade=transition=fadeblack:duration=1.5:offset=8[v];\
[0:a][1:a]acrossfade=d=1.5[a]" \
  -map "[v]" -map "[a]" out.mp4
```

### Wipe Left
```bash
ffmpeg -i a.mp4 -i b.mp4 \
  -filter_complex "[0:v][1:v]xfade=transition=wipeleft:duration=0.5:offset=10[v];\
[0:a][1:a]acrossfade=d=0.5[a]" \
  -map "[v]" -map "[a]" out.mp4
```

### Slide Left
```bash
ffmpeg -i a.mp4 -i b.mp4 \
  -filter_complex "[0:v][1:v]xfade=transition=slideleft:duration=0.8:offset=4[v];\
[0:a][1:a]acrossfade=d=0.8[a]" \
  -map "[v]" -map "[a]" out.mp4
```

### Circle Open (Iris)
```bash
ffmpeg -i a.mp4 -i b.mp4 \
  -filter_complex "[0:v][1:v]xfade=transition=circleopen:duration=1:offset=6[v];\
[0:a][1:a]acrossfade=d=1[a]" \
  -map "[v]" -map "[a]" out.mp4
```

### Zoom In
```bash
ffmpeg -i a.mp4 -i b.mp4 \
  -filter_complex "[0:v][1:v]xfade=transition=zoomin:duration=0.6:offset=9[v];\
[0:a][1:a]acrossfade=d=0.6[a]" \
  -map "[v]" -map "[a]" out.mp4
```

### Pixelize
```bash
ffmpeg -i a.mp4 -i b.mp4 \
  -filter_complex "[0:v][1:v]xfade=transition=pixelize:duration=1:offset=7[v];\
[0:a][1:a]acrossfade=d=1[a]" \
  -map "[v]" -map "[a]" out.mp4
```

### Diagonal (diagbr)
```bash
ffmpeg -i a.mp4 -i b.mp4 \
  -filter_complex "[0:v][1:v]xfade=transition=diagbr:duration=0.8:offset=5[v];\
[0:a][1:a]acrossfade=d=0.8[a]" \
  -map "[v]" -map "[a]" out.mp4
```

---

## Multi-Clip Transition Chain

Chain multiple transitions across three or more clips:

```bash
# Two transitions: A→B (dissolve at 5s), B→C (wipeleft at 10s)
# Clip A: 6s, Clip B: 6s, Clip C: 6s
ffmpeg -i a.mp4 -i b.mp4 -i c.mp4 \
  -filter_complex "
    [0:v][1:v]xfade=transition=dissolve:duration=1:offset=5[ab];
    [ab][2:v]xfade=transition=wipeleft:duration=1:offset=10[v];
    [0:a][1:a]acrossfade=d=1[ab_a];
    [ab_a][2:a]acrossfade=d=1[a]
  " \
  -map "[v]" -map "[a]" \
  -c:v libx264 -crf 23 out.mp4
```

---

## Calculating Offset for Multi-Clip Chains

For N clips with transition duration T:
- Offset for transition 1: `clip1_duration - T`
- Offset for transition 2: `clip1_duration + clip2_duration - 2*T`
- Offset for transition N: `sum(clip1..N_durations) - N*T`

### Batch Helper (bash)

```bash
#!/usr/bin/env bash
# Build xfade chain from array of clips
CLIPS=("a.mp4" "b.mp4" "c.mp4" "d.mp4")
TRANS="dissolve"
DUR=1.0
OFFSET=0
FILTER=""
INPUTS=""
LAST_LABEL=""

for i in "${!CLIPS[@]}"; do
  INPUTS+="-i ${CLIPS[$i]} "
  if [[ $i -gt 0 ]]; then
    if [[ $i -eq 1 ]]; then
      PREV="[0:v]"
    else
      PREV="[v$((i-1))]"
    fi
    CLIP_DUR=$(ffprobe -v error -show_entries format=duration \
      -of default=noprint_wrappers=1:nokey=1 "${CLIPS[$((i-1))]}")
    OFFSET=$(echo "$OFFSET + $CLIP_DUR - $DUR" | bc)
    # Final clip uses [vout]; intermediate clips use [v1], [v2], etc.
    if [[ $i -eq $(( ${#CLIPS[@]} - 1 )) ]]; then
      OUT="[vout]"
    else
      OUT="[v$i]"
    fi
    LAST_LABEL="$OUT"
    FILTER+="${PREV}[$((i)):v]xfade=transition=${TRANS}:duration=${DUR}:offset=${OFFSET}${OUT}; "
  fi
done

echo "Inputs: $INPUTS"
echo "Filter: $FILTER"
echo "Map with: -map \"$LAST_LABEL\""
# Full command example:
# ffmpeg $INPUTS -filter_complex "$FILTER" -map "$LAST_LABEL" -c:v libx264 -crf 23 out.mp4
```

---

## Audio: acrossfade Parameters

```
acrossfade=d=duration[:c1=curve_in][:c2=curve_out]
```

| Curve | Description |
|-------|-------------|
| `tri` | Linear (default) |
| `qsin` | Quarter sine wave |
| `hsin` | Half sine wave |
| `esin` | Exponential sine |
| `log` | Logarithmic |
| `ipar` | Inverted parabola |
| `exp` | Exponential |
| `iqsin` | Inverted quarter sine |

```bash
# Smooth logarithmic audio crossfade
[0:a][1:a]acrossfade=d=1:c1=log:c2=log[a]
```
