import json
import math
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = r"d:\video\视频3"
DEMO_DIR = os.path.join(BASE_DIR, "素材", "04_分幕原生画卷")
AUDIO_FILE = os.path.join(BASE_DIR, "output", "audio", "scene_02_yunxi_master.wav")
MANIFEST_FILE = os.path.join(BASE_DIR, "output", "audio", "manifest_yunxi.json")
OUTPUT_VIDEO = os.path.join(BASE_DIR, "output", "video", "scene_02_yunxi.mp4")
QA_DIR = os.path.join(BASE_DIR, "output", "qa_frames", "scene_02_yunxi")

os.makedirs(QA_DIR, exist_ok=True)
os.makedirs(os.path.dirname(OUTPUT_VIDEO), exist_ok=True)

FONT_HEAVY = r"C:\Windows\Fonts\msyhbd.ttc"
if not os.path.exists(FONT_HEAVY):
    FONT_HEAVY = r"C:\Windows\Fonts\msyh.ttc"

WIDTH = 1080
HEIGHT = 1920
FPS = 30

with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
    manifest = json.load(f)["scene_02"]

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

def apply_orange_sweep(img, progress, y_top=650, y_bot=715, x_start=125, x_end=416):
    if progress <= 0.0:
        return img
    sweep_x = int(x_start + (x_end - x_start) * min(1.0, progress))
    overlay = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.rounded_rectangle([(x_start, y_top), (sweep_x, y_bot)], radius=8, fill=(255, 215, 50, 80))
    return Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')

def main():
    print(f"=== 渲染第二幕 Scene 02 (云希 Yunxi · 合规修补版 · {TOTAL_DURATION:.2f}s · {TOTAL_FRAMES}帧) ===")

    prev_plate_path = os.path.join(DEMO_DIR, "Scene01_结尾最后一帧_yunxi.png")
    if not os.path.exists(prev_plate_path):
        prev_plate_path = os.path.join(DEMO_DIR, "Scene01B_危机清单_挠后脑勺.jpg")
    prev_plate = Image.open(prev_plate_path).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)

    # 载入合规修补版画卷 2A (剔除主管负面评价)
    plate_2a = Image.open(os.path.join(BASE_DIR, "素材", "04_分幕原生画卷", "Scene02A_破局共鸣_合规修补版.jpg")).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    plate_2b = Image.open(os.path.join(DEMO_DIR, "Scene02B_重磅上线_话术私教.jpg")).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    plate_2c_point = Image.open(os.path.join(DEMO_DIR, "Scene02_破局重塑_24关地图.jpg")).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    plate_2c_fist = Image.open(os.path.join(DEMO_DIR, "Scene02_破局重塑_Pose5_握拳打满.jpg")).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)

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

    # 节奏划分：
    # s2_1 (0.0s - 1.54s) & s2_2 (1.79s - 4.012s): 画卷 2A (找不到人随时陪练？)
    # 4.01s - 4.36s: 2.5D 折页翻入 2B (重磅上线)
    # s2_3 (4.362s - 7.515s): 画卷 2B
    # 7.51s - 7.86s: 折页翻入 2C
    # s2_4 (7.865s - 11.446s): 2C (食指点划 + 荧光扫掠)
    # s2_5 (11.746s - 14.238s): 2C (握拳打满)
    f_flip1_start = int(manifest[1]["end"] * FPS)
    f_flip1_end = f_flip1_start + 15
    f_s2_3_start = int(manifest[2]["start"] * FPS)
    f_flip2_start = int(manifest[2]["end"] * FPS)
    f_flip2_end = f_flip2_start + 15
    f_fist_start = int(manifest[4]["start"] * FPS)

    qa_frames_to_save = {15, f_flip1_start - 5, f_s2_3_start + 10, f_flip2_end + 10, f_fist_start + 10, TOTAL_FRAMES - 1}
    last_frame_img = None

    for f in range(TOTAL_FRAMES):
        t = f / float(FPS)
        # 转场与画卷切换
        if f < 18:
            # 承接上幕翻页
            p_turn = f / 18.0
            frame_bg = create_page_turn(prev_plate, plate_2a, p_turn).convert("RGBA")
        elif f < f_flip1_start:
            frame_bg = plate_2a.copy().convert("RGBA")
        elif f < f_flip1_end:
            p_turn = (f - f_flip1_start) / float(f_flip1_end - f_flip1_start)
            frame_bg = create_page_turn(plate_2a, plate_2b, p_turn).convert("RGBA")
        elif f < f_flip2_start:
            frame_bg = plate_2b.copy().convert("RGBA")
        elif f < f_flip2_end:
            p_turn = (f - f_flip2_start) / float(f_flip2_end - f_flip2_start)
            frame_bg = create_page_turn(plate_2b, plate_2c_point, p_turn).convert("RGBA")
        elif f < f_fist_start:
            # 2C 食指点划 + 荧光扫掠
            sweep_p = (t - manifest[3]["start"]) / max(0.1, manifest[3]["duration"])
            swept = apply_orange_sweep(plate_2c_point, sweep_p)
            frame_bg = swept.copy().convert("RGBA")
        else:
            frame_bg = plate_2c_fist.copy().convert("RGBA")

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

    anchor_path = os.path.join(DEMO_DIR, "Scene02_结尾最后一帧_yunxi.png")
    if last_frame_img:
        last_frame_img.convert("RGB").save(anchor_path)
    print(f"[SUCCESS] Scene 02 云希成片完成: {OUTPUT_VIDEO}")
    print(f"[ANCHOR] 结尾锚点已存: {anchor_path}")

if __name__ == "__main__":
    main()
