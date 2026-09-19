import os
import sys
import math
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = r"d:\video\视频3"
DEMO_DIR = os.path.join(BASE_DIR, "素材", "04_分幕原生画卷")
AUDIO_FILE = os.path.join(BASE_DIR, "output", "audio", "scene2_v3_master_audio.wav")
OUTPUT_VIDEO = os.path.join(BASE_DIR, "output", "video", "scene_02_animated_v2.mp4")
QA_DIR = os.path.join(BASE_DIR, "output", "qa_frames", "scene_02")

os.makedirs(QA_DIR, exist_ok=True)
os.makedirs(os.path.dirname(OUTPUT_VIDEO), exist_ok=True)

FONT_HEAVY = r"C:\Windows\Fonts\msyhbd.ttc"
if not os.path.exists(FONT_HEAVY):
    FONT_HEAVY = r"C:\Windows\Fonts\msyh.ttc"

WIDTH = 1080
HEIGHT = 1920
FPS = 30
TOTAL_FRAMES = 426  # 14.200 seconds @ 30fps

def get_subtitle(frame):
    # 0 - 57 (0.00s - 1.90s): 别担心，只是你练少了！
    # 57 - 66: 气口空白
    # 66 - 105 (2.20s - 3.50s): 主管忙、没空教？
    # 105 - 123: 气口与翻页过渡
    # 123 - 215 (4.10s - 7.17s): 好帮手 AI 学习助手重磅上线——话术私教！
    # 215 - 223: 气口空白
    # 223 - 330 (7.45s - 11.02s): 从开场白、报价到促成，24 关实战异议地图
    # 330 - 336: 气口空白
    # 336 - 418 (11.20s - 13.93s): 随时随地像打游戏一样刷满肌肉记忆。
    if frame <= 57:
        return "别担心，只是你练少了！"
    elif frame < 66:
        return ""
    elif frame <= 105:
        return "主管忙、没空教？"
    elif frame < 123:
        return ""
    elif frame <= 215:
        return "好帮手 AI 学习助手重磅上线——话术私教！"
    elif frame < 223:
        return ""
    elif frame <= 330:
        return "从开场白、报价到促成，24 关实战异议地图"
    elif frame < 336:
        return ""
    elif frame <= 418:
        return "随时随地像打游戏一样刷满肌肉记忆。"
    else:
        return ""

def draw_subtitle_pill(canvas, text):
    if not text:
        return
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(FONT_HEAVY, 36)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    
    pad_x = 32
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
        
        # 阴影层
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

def apply_orange_sweep(img, progress, y_top, y_bot, x_start=125, x_end=416):
    """
    荧光橙扫掠划线高光动效 (Fluorescent Marker Sweep)
    """
    if progress <= 0.0:
        return img
    
    sweep_x = int(x_start + (x_end - x_start) * min(1.0, progress))
    overlay = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    
    # 荧光黄色/橙色高亮笔刷 (#FFD732)
    d.rounded_rectangle([(x_start, y_top), (sweep_x, y_bot)], radius=8, fill=(255, 215, 50, 80))
    
    # 扫掠高光边缘
    if sweep_x < x_end:
        edge_w = 20
        d.rectangle([(max(x_start, sweep_x - edge_w), y_top), (sweep_x, y_bot)], fill=(255, 255, 255, 130))
        
    return Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')

def main():
    print("=== 开始渲染全新第二幕 (Scene 02 v2 · 双大画卷递进 + 恒定自然语速) ===")
    print(f"规格: {WIDTH}x{HEIGHT} @ {FPS}fps, 总帧数: {TOTAL_FRAMES} (严格 14.200s)")
    print(f"音频: {AUDIO_FILE}")
    print(f"成片输出: {OUTPUT_VIDEO}")
    
    # 1. 载入核心画卷资产 (全部 1080x1920 高清 LANCZOS)
    # 上一幕收尾原画 (用于开头翻页)
    prev_plate = Image.open(os.path.join(DEMO_DIR, "Scene01B_危机清单_挠后脑勺.jpg")).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    
    # 画卷 2A：现实痛点共鸣 (别担心，只是你练少了！主管忙、没空教？)
    plate_2a = Image.open(os.path.join(DEMO_DIR, "Scene02A_破局共鸣_主管没空教.jpg")).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    
    # 画卷 2B：重磅功能发布卡 (用户确认无人物高精手账卡：好帮手AI学习助手重磅上线——话术私教！)
    plate_2b_launch = Image.open(os.path.join(DEMO_DIR, "Scene02B_重磅上线_话术私教.jpg")).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    
    # 画卷 2C：姿态 1 (24关地图 · 食指点划)
    plate_2c_point = Image.open(os.path.join(DEMO_DIR, "Scene02_破局重塑_24关地图.jpg")).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    
    # 画卷 2C：姿态 2 (24关地图 · 握拳打满收尾)
    plate_2c_fist = Image.open(os.path.join(DEMO_DIR, "Scene02_破局重塑_Pose5_握拳打满.jpg")).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    
    # 启动 FFmpeg 写入管道
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
    
    qa_frames_to_save = {10, 50, 90, 124, 180, 233, 290, 370, 420}
    
    for f in range(TOTAL_FRAMES):
        # ================= 阶段 1：上一幕翻入 2A (0 - 20 帧 / 0.00s - 0.67s) =================
        if f < 20:
            p_turn = f / 20.0
            frame_base = create_page_turn(prev_plate, plate_2a, p_turn)
            
        # ================= 阶段 2：画卷 2A 痛点共鸣主段 (20 - 114 帧 / 0.67s - 3.80s) =================
        # 别担心，只是你练少了！主管忙、没空教？
        elif f < 114:
            frame_base = plate_2a.copy()
            
        # ================= 阶段 3：画卷 2A 翻入 画卷 2B (114 - 134 帧 / 3.80s - 4.47s) =================
        elif f < 134:
            p_turn2 = (f - 114) / 20.0
            frame_base = create_page_turn(plate_2a, plate_2b_launch, p_turn2)
            
        # ================= 阶段 4：画卷 2B 纯功能重磅发布卡 (134 - 223 帧 / 4.47s - 7.45s) =================
        # 好帮手 AI 学习助手重磅上线——话术私教！ (用户指定无人物专属图)
        elif f < 223:
            frame_base = plate_2b_launch.copy()
            
        # ================= 阶段 5：画卷 2B 翻入 画卷 2C (223 - 243 帧 / 7.45s - 8.10s) =================
        elif f < 243:
            p_turn3 = (f - 223) / 20.0
            frame_base = create_page_turn(plate_2b_launch, plate_2c_point, p_turn3)
            
        # ================= 阶段 6：画卷 2C 实战异议地图展开 (243 - 426 帧 / 8.10s - 14.20s) =================
        else:
            # 243 - 336 (8.10s - 11.20s) "从开场白、报价到促成，24 关实战异议地图" -> 食指点划
            # 336 - 426 (11.20s - 14.20s) "随时随地像打游戏一样刷满肌肉记忆。" -> 握拳打满收尾
            if f < 336:
                cur_plate = plate_2c_point
            else:
                cur_plate = plate_2c_fist
                
            frame_base = cur_plate.copy()
            
            # 荧光橙马克笔动态扫掠动效：
            # 在 250 - 306 帧 (8.33s - 10.20s) 念到 "从开场白、报价到促成" 时扫过
            if 250 <= f <= 276:
                # 扫过 "开场白训练" (Y: 674~723)
                prog1 = (f - 250) / 26.0
                frame_base = apply_orange_sweep(frame_base, prog1, 674, 723, 125, 416)
            elif 276 < f <= 306:
                # 开场白保持亮显，促成开始扫光
                frame_base = apply_orange_sweep(frame_base, 1.0, 674, 723, 125, 416)
                prog2 = (f - 276) / 30.0
                frame_base = apply_orange_sweep(frame_base, prog2, 1258, 1306, 125, 416)
            elif f > 306:
                # 扫过后的常驻亮显
                frame_base = apply_orange_sweep(frame_base, 1.0, 674, 723, 125, 416)
                frame_base = apply_orange_sweep(frame_base, 1.0, 1258, 1306, 125, 416)

        # 镜头平滑缓推 (1.000x -> 1.035x)，稳健聚焦，0 伪摇摆，纯正实体定格
        scale = 1.000 + 0.035 * (f / TOTAL_FRAMES)
        new_w = int(WIDTH * scale)
        new_h = int(HEIGHT * scale)
        
        crop_x = int((new_w - WIDTH) * 0.5)
        crop_y = int((new_h - HEIGHT) * 0.5)
        
        scaled_frame = frame_base.resize((new_w, new_h), Image.Resampling.BILINEAR)
        frame_img = scaled_frame.crop((crop_x, crop_y, crop_x + WIDTH, crop_y + HEIGHT)).convert("RGBA")
        
        # 绘制居中圆角胶囊字幕
        sub_text = get_subtitle(f)
        draw_subtitle_pill(frame_img, sub_text)
        
        # 写入视频流管道
        proc.stdin.write(frame_img.tobytes())
        
        # 抽取 QA 关键帧
        if f in qa_frames_to_save:
            qa_path = os.path.join(QA_DIR, f"frame_{f:03d}.png")
            frame_img.convert("RGB").save(qa_path)
            print(f"[QA] 抽取关键走查帧 {f} -> {qa_path}")
            
        if (f + 1) % 50 == 0 or f == TOTAL_FRAMES - 1:
            print(f"渲染进度: {f + 1}/{TOTAL_FRAMES} 帧 ({(f + 1) / TOTAL_FRAMES * 100:.1f}%)")
            
    proc.stdin.close()
    proc.wait()
    print(f"\n[SUCCESS] Scene 02 Master Render Completed! Saved to: {OUTPUT_VIDEO}")

if __name__ == "__main__":
    main()
