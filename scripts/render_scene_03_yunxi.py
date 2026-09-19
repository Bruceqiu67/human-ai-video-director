import json
import math
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = r"d:\video\视频3"
DEMO_DIR = os.path.join(BASE_DIR, "素材", "04_分幕原生画卷")
AUDIO_FILE = os.path.join(BASE_DIR, "output", "audio", "scene_03_yunxi_master.wav")
MANIFEST_FILE = os.path.join(BASE_DIR, "output", "audio", "manifest_yunxi.json")
OUTPUT_VIDEO = os.path.join(BASE_DIR, "output", "video", "scene_03_yunxi.mp4")
QA_DIR = os.path.join(BASE_DIR, "output", "qa_frames", "scene_03_yunxi")

os.makedirs(QA_DIR, exist_ok=True)
os.makedirs(os.path.dirname(OUTPUT_VIDEO), exist_ok=True)

FONT_HEAVY = r"C:\Windows\Fonts\msyhbd.ttc"
if not os.path.exists(FONT_HEAVY):
    FONT_HEAVY = r"C:\Windows\Fonts\msyh.ttc"

WIDTH = 1080
HEIGHT = 1920
FPS = 30

with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
    manifest = json.load(f)["scene_03"]

TOTAL_DURATION = manifest[-1]["end"] + manifest[-1]["pause_after"]
TOTAL_FRAMES = int(math.ceil(TOTAL_DURATION * FPS))

def get_subtitle(f):
    t = f / float(FPS)
    for seg in manifest:
        if seg["start"] <= t <= seg["end"]:
            return seg["text"]
    return ""

def draw_subtitle_pill(canvas, text):
    if not text:
        return
    draw = ImageDraw.Draw(canvas)
    font_size = 36
    font = ImageFont.truetype(FONT_HEAVY, font_size)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    while (tw + 68) > 940 and font_size > 24:
        font_size -= 2
        font = ImageFont.truetype(FONT_HEAVY, font_size)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

    pad_x = 34
    pad_y = 16
    cx = (WIDTH - tw) // 2
    cy = 1675

    x1 = cx - pad_x
    y1 = cy - pad_y
    x2 = cx + tw + pad_x
    y2 = cy + th + pad_y + 4

    draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=18, fill=(32, 30, 28, 230))
    draw.text((cx, cy), text, font=font, fill=(255, 255, 255, 255))

def create_page_turn(img_a, img_b, progress):
    p = progress * progress * (3.0 - 2.0 * progress)
    out = img_b.copy()
    curl_w = int(140 * math.sin(math.pi * progress) + 30)
    fold_x = int((1.0 - p) * (WIDTH + curl_w * 2) - curl_w)
    if fold_x > 0:
        mask = Image.new('L', (WIDTH, HEIGHT), 0)
        draw_mask = ImageDraw.Draw(mask)
        tilt = int(45 * math.sin(math.pi * progress))
        pts = [(0, 0), (fold_x - tilt, 0), (fold_x + tilt, HEIGHT), (0, HEIGHT)]
        draw_mask.polygon(pts, fill=255)
        out.paste(img_a, (0, 0), mask=mask)
    return out

def main():
    print(f"=== 渲染第三幕 Scene 03 (云希 Yunxi · {TOTAL_DURATION:.2f}s · {TOTAL_FRAMES}帧) ===")

    prev_plate_path = os.path.join(DEMO_DIR, "Scene02_结尾最后一帧_yunxi.png")
    if not os.path.exists(prev_plate_path):
        prev_plate_path = os.path.join(DEMO_DIR, "Scene02_破局重塑_Pose5_握拳打满.jpg")
    prev_plate = Image.open(prev_plate_path).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)

    p1 = Image.open(os.path.join(DEMO_DIR, "Scene03_拟真对攻_Pose1_食指指向.jpg")).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    p2 = Image.open(os.path.join(DEMO_DIR, "Scene03_拟真对攻_Pose2_扶眼镜吃惊.jpg")).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    p3 = Image.open(os.path.join(DEMO_DIR, "Scene03_拟真对攻_Pose3_双手抱胸自信.jpg")).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "rgba",
        "-r", str(FPS),
        "-i", "-",
        "-i", AUDIO_FILE,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "320k",
        "-shortest",
        OUTPUT_VIDEO
    ]
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

    f_p2_start = int(manifest[1]["start"] * FPS)
    f_p3_start = int(manifest[2]["start"] * FPS)

    qa_frames_to_save = {15, f_p2_start - 5, f_p2_start + 10, f_p3_start + 10, TOTAL_FRAMES - 1}
    last_frame_img = None

    for f in range(TOTAL_FRAMES):
        if f < 18:
            p_turn = f / 18.0
            frame_bg = create_page_turn(prev_plate, p1, p_turn).convert("RGBA")
        elif f < f_p2_start:
            frame_bg = p1.copy().convert("RGBA")
        elif f < f_p3_start:
            frame_bg = p2.copy().convert("RGBA")
        else:
            frame_bg = p3.copy().convert("RGBA")

        # 胶囊字幕
        sub_text = get_subtitle(f)
        draw_subtitle_pill(frame_bg, sub_text)

        if f in qa_frames_to_save:
            qa_path = os.path.join(QA_DIR, f"frame_{f:03d}.png")
            frame_bg.save(qa_path)

        if f == TOTAL_FRAMES - 1:
            last_frame_img = frame_bg.copy()

        proc.stdin.write(frame_bg.tobytes())

    proc.stdin.close()
    proc.wait()

    anchor_path = os.path.join(DEMO_DIR, "Scene03_结尾最后一帧_yunxi.png")
    if last_frame_img:
        last_frame_img.convert("RGB").save(anchor_path)
    print(f"[SUCCESS] Scene 03 云希成片完成: {OUTPUT_VIDEO}")
    print(f"[ANCHOR] 结尾锚点已存: {anchor_path}")

if __name__ == "__main__":
    main()
