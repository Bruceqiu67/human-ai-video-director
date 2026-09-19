# -*- coding: utf-8 -*-
import os
import sys
import math
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = r"d:\video\视频3"
AUDIO_FILE = os.path.join(BASE_DIR, "output", "audio", "scene5_v2_master_audio.wav")
OUTPUT_VIDEO = os.path.join(BASE_DIR, "output", "video", "scene_05_animated_v2.mp4")
QA_DIR = os.path.join(BASE_DIR, "output", "qa_frames", "scene_05")
DEMO_DIR = os.path.join(BASE_DIR, "素材", "04_分幕原生画卷")

os.makedirs(QA_DIR, exist_ok=True)
os.makedirs(os.path.dirname(OUTPUT_VIDEO), exist_ok=True)

FONT_HEAVY = r"C:\Windows\Fonts\msyhbd.ttc"
if not os.path.exists(FONT_HEAVY):
    FONT_HEAVY = r"C:\Windows\Fonts\msyh.ttc"

WIDTH = 1080
HEIGHT = 1920
FPS = 30
TOTAL_FRAMES = 330  # 严格 11.000 秒 @ 30fps

def get_subtitle(f):
    # 0 - 14: 翻书转场
    # 15 - 76 (0.50s - 2.53s): 哪里卡壳，就一键“再练一次”，
    # 77 - 85: 气口
    # 86 - 154 (2.85s - 5.14s): 直到把金牌话术化作你的本能应变。
    # 155 - 164: 气口
    # 165 - 205 (5.50s - 6.85s): 现在就打开好帮手 APP，
    # 206 - 212: 气口
    # 213 - 246 (7.10s - 8.22s): 进入【话术私教】，
    # 247 - 254: 气口
    # 255 - 309 (8.50s - 10.31s): 开启你的销冠通关之旅吧！
    # 310 - 330: 收尾留白定格
    if f < 15:
        return ""
    elif f <= 76:
        return "哪里卡壳，就一键“再练一次”，"
    elif f < 86:
        return ""
    elif f <= 154:
        return "直到把金牌话术化作你的本能应变。"
    elif f < 165:
        return ""
    elif f <= 205:
        return "现在就打开好帮手 APP，"
    elif f < 213:
        return ""
    elif f <= 246:
        return "进入【话术私教】，"
    elif f < 255:
        return ""
    elif f <= 309:
        return "开启你的销冠通关之旅吧！"
    else:
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
    
    # 屏幕安全保护：如果文字总宽加上内边距超过 940px，自动降字号保证绝不出界
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
    """
    2.5D 手账折页/翻书物理动效 (Magazine Page Flip Physics)
    progress: 0.0 -> 1.0 (从 img_a 翻到 img_b)
    """
    p = progress * progress * (3.0 - 2.0 * progress)
    out = img_b.copy()
    
    curl_w = int(140 * math.sin(math.pi * progress) + 30)
    fold_x = int((1.0 - p) * (WIDTH + curl_w * 2) - curl_w)
    
    if fold_x > 0:
        mask = Image.new('L', (WIDTH, HEIGHT), 0)
        draw_mask = ImageDraw.Draw(mask)
        
        tilt = int(45 * math.sin(math.pi * progress))
        top_x = fold_x - tilt
        bot_x = fold_x + tilt
        
        pts = [(0, 0), (top_x, 0), (bot_x, HEIGHT), (0, HEIGHT)]
        draw_mask.polygon(pts, fill=255)
        out.paste(img_a, (0, 0), mask=mask)
        
        shadow_img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
        s_draw = ImageDraw.Draw(shadow_img)
        
        shadow_dist = int(curl_w * 1.6)
        for s in range(shadow_dist):
            ratio = s / max(1, shadow_dist)
            alpha = int(160 * ((1.0 - ratio) ** 2.0) * math.sin(math.pi * progress))
            s_draw.line([(top_x + s, 0), (bot_x + s, HEIGHT)], fill=(20, 15, 10, alpha), width=2)
            
        for c in range(curl_w):
            ratio = c / max(1, curl_w)
            crest = max(0.0, 1.0 - abs(ratio - 0.35) * 4.0)
            h_alpha = int(90 * crest * math.sin(math.pi * progress))
            s_alpha = int(100 * (1.0 - ratio) * math.sin(math.pi * progress))
            
            if h_alpha > 0:
                s_draw.line([(top_x - c, 0), (bot_x - c, HEIGHT)], fill=(255, 255, 255, h_alpha), width=2)
            if s_alpha > 0:
                s_draw.line([(top_x - c, 0), (bot_x - c, HEIGHT)], fill=(40, 30, 20, s_alpha), width=2)
                
        out = Image.alpha_composite(out.convert('RGBA'), shadow_img).convert('RGB')
        
    return out

def main():
    print("=== 开始渲染全新第五幕 (Scene 05 v2 · 恒定从容语速 + 终极通关行动号召) ===")
    print(f"规格: {WIDTH}x{HEIGHT} @ {FPS}fps, 总帧数: {TOTAL_FRAMES} (严格 11.000s)")
    print(f"音频: {AUDIO_FILE}")
    print(f"成片输出: {OUTPUT_VIDEO}")
    
    # 1. 载入画卷资产 (严格使用 Scene 04 真实末帧作为翻页起始页，确保 100% 像素级无缝衔接)
    prev_scene_path = os.path.join(DEMO_DIR, "Scene04_结尾最后一帧.png")
    if not os.path.exists(prev_scene_path):
        prev_scene_path = os.path.join(DEMO_DIR, "Scene04_深度诊断_Pose3_OK自信.jpg")
    prev_scene_img = Image.open(prev_scene_path).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    
    p1_path = os.path.join(DEMO_DIR, "Scene05_通关升华_Pose1_握拳蓄力.jpg")
    p2_path = os.path.join(DEMO_DIR, "Scene05_通关升华_Pose2_开掌邀请.jpg")
    p3_path = os.path.join(DEMO_DIR, "Scene05_通关升华_Pose3_点赞通关.jpg")
    
    p1_img = Image.open(p1_path).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    p2_img = Image.open(p2_path).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    p3_img = Image.open(p3_path).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    
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
    
    qa_frames_to_save = {10, 50, 120, 185, 230, 280, 320}
    
    for f in range(TOTAL_FRAMES):
        # 1. 翻书转场与三姿态定格瞬切
        if f < 21:
            # 0.0s - 0.70s: 从上一幕 (Scene 04) 片尾最后一帧翻入 Scene 05
            p_turn = f / 21.0
            frame_bg = create_page_turn(prev_scene_img, p1_img, p_turn).convert("RGBA")
        else:
            if f < 165:
                # 0.70s - 5.50s: Pose 1 握拳蓄力 (哪里卡壳就再练一次，金牌话术化作本能应变)
                frame_bg = p1_img.copy().convert("RGBA")
            elif f < 255:
                # 5.50s - 8.50s: Pose 2 开掌邀请 (现在就打开好帮手 APP，进入【话术私教】)
                frame_bg = p2_img.copy().convert("RGBA")
            else:
                # 8.50s - 11.00s: Pose 3 点赞通关 (大拇指点赞，开启你的销冠通关之旅吧！)
                frame_bg = p3_img.copy().convert("RGBA")
                
        # 2. 镜头微距平滑缓推 (1.000x -> 1.035x)
        scale = 1.000 + 0.035 * (f / TOTAL_FRAMES)
        new_w = int(WIDTH * scale)
        new_h = int(HEIGHT * scale)
        
        crop_x = int((new_w - WIDTH) * 0.5)
        crop_y = int((new_h - HEIGHT) * 0.5)
        
        scaled = frame_bg.resize((new_w, new_h), Image.Resampling.BILINEAR)
        crop_x = max(0, min(new_w - WIDTH, crop_x))
        crop_y = max(0, min(new_h - HEIGHT, crop_y))
        frame_final = scaled.crop((crop_x, crop_y, crop_x + WIDTH, crop_y + HEIGHT)).convert("RGBA")
        
        # 3. 绘制自适应居中圆角胶囊字幕
        sub_text = get_subtitle(f)
        draw_subtitle_pill(frame_final, sub_text)
        
        # 4. 提取 QA 走查关键帧
        if f in qa_frames_to_save:
            qa_out = os.path.join(QA_DIR, f"frame_{f:03d}.png")
            frame_final.save(qa_out)
            print(f"[QA] 提取关键帧 {f} -> {qa_out}")
            
        proc.stdin.write(frame_final.tobytes())
        
        if (f + 1) % 50 == 0 or f == TOTAL_FRAMES - 1:
            pct = (f + 1) / TOTAL_FRAMES * 100
            print(f"渲染进度: {f + 1}/{TOTAL_FRAMES} 帧 ({pct:.1f}%)")
            
    proc.stdin.close()
    proc.wait()
    print(f"\n[SUCCESS] Scene 05 v2 Render Completed! Saved to: {OUTPUT_VIDEO}")

if __name__ == "__main__":
    main()
