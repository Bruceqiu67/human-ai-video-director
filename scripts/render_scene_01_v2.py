import os
import sys
import math
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE_DIR = r"d:\video\视频3"
ASSET_DIR = os.path.join(BASE_DIR, "素材", "视觉包装资产")
STICKER_DIR = os.path.join(BASE_DIR, "素材", "贴纸人素材")
DEMO_DIR = os.path.join(BASE_DIR, "素材", "视觉风格Demo")
AUDIO_FILE = os.path.join(BASE_DIR, "output", "audio", "scene1_v2_master_audio.wav")
OUTPUT_VIDEO = os.path.join(BASE_DIR, "output", "scene_01_animated.mp4")

FONT_HEAVY = r"C:\Windows\Fonts\msyhbd.ttc"
if not os.path.exists(FONT_HEAVY):
    FONT_HEAVY = r"C:\Windows\Fonts\msyh.ttc"

WIDTH = 1080
HEIGHT = 1920
FPS = 30
TOTAL_FRAMES = 345  # 11.50 seconds @ 30fps

def get_subtitle(frame):
    # 0 - 54 (0.0s - 1.8s): 刚开口，
    # 54 - 72 (1.8s - 2.4s): 就被客户秒挂
    # 72 - 126 (2.4s - 4.2s): 面对客户的‘现在忙、不需要’
    # 126 - 162 (4.2s - 5.4s): 大脑一片空白不知如何回复
    # 162 - 246 (5.4s - 8.2s): 新人缺乏异议经验，根本留不住客户
    # 246 - 345 (8.2s - 11.5s): 最后导致开单率怎么也上不去。
    if frame < 54:
        return "刚开口，"
    elif frame < 72:
        return "就被客户秒挂"
    elif frame < 126:
        return "面对客户的‘现在忙、不需要’"
    elif frame < 162:
        return "大脑一片空白不知如何回复"
    elif frame < 246:
        return "新人缺乏异议经验，根本留不住客户"
    else:
        return "最后导致开单率怎么也上不去。"

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

def rotate_image(img, angle, center=None):
    """高质量抗锯齿旋转透明 PNG"""
    return img.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True, center=center)

def main():
    print("=== 开始渲染第一幕高能动态成片 (Scene 1 V2) ===")
    print(f"规格: {WIDTH}x{HEIGHT} @ {FPS}fps, 总帧数: {TOTAL_FRAMES} (11.50s)")
    
    # 1. 载入核心素材图层
    bg_plate = Image.open(os.path.join(ASSET_DIR, "scene1_clean_background.png")).convert("RGBA")
    note_card = Image.open(os.path.join(ASSET_DIR, "sticky_note_standalone.png")).convert("RGBA")
    btn_hangup = Image.open(os.path.join(ASSET_DIR, "button_hangup_transparent.png")).convert("RGBA").resize((145, 145), Image.Resampling.LANCZOS)
    
    # 人物动作 1A：贴耳通话
    jia_calling = Image.open(os.path.join(STICKER_DIR, "动作_手持电话_半身透明.png")).convert("RGBA")
    jw_call = int(jia_calling.size[0] * (1150 / jia_calling.size[1]))
    jia_calling = jia_calling.resize((jw_call, 1150), Image.Resampling.LANCZOS)
    
    # 人物动作 1B：低头看手机发愁
    jia_down = Image.open(os.path.join(STICKER_DIR, "动作_愁眉苦脸看手机_透明.png")).convert("RGBA")
    jw_down = int(jia_down.size[0] * (1150 / jia_down.size[1]))
    jia_down = jia_down.resize((jw_down, 1150), Image.Resampling.LANCZOS)
    
    # 第二张画卷 (Scene 1B 痛点检查录)
    img_b = Image.open(os.path.join(DEMO_DIR, "方案2_第一幕B_挠头痛点.jpg")).convert("RGBA").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    
    # 启动 FFmpeg 管道
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
    
    for f in range(TOTAL_FRAMES):
        if f < 162:
            # ================= 第一阶段：电话秒挂与动作切换 (0.0s - 5.4s) =================
            frame_img = bg_plate.copy()
            
            # 1. 人物控制
            if f < 54:
                # 0.0s - 1.8s: 人物动作1A (贴耳) 从右侧滑入
                # 缓动推进: 0 -> 30 帧滑入，30 -> 54 帧稳定
                prog = min(1.0, f / 28.0)
                ease = 1.0 - math.pow(1.0 - prog, 3)
                cur_x = int(1080 - (1080 - 510) * ease)
                cur_y = 600
                frame_img.paste(jia_calling, (cur_x, cur_y), mask=jia_calling)
                
            elif f < 72:
                # 1.8s - 2.4s: 挂断声响，人物动作1A固定
                cur_x = 510
                cur_y = 600
                frame_img.paste(jia_calling, (cur_x, cur_y), mask=jia_calling)
                
            elif f < 126:
                # 2.4s - 4.2s: 人物动作瞬间切换为 1B (愁眉苦脸看手机)
                # 微呼吸漂移
                cur_x = 460
                cur_y = 600 + int(3.0 * math.sin((f - 72) * 0.15))
                frame_img.paste(jia_down, (cur_x, cur_y), mask=jia_down)
                
            else:
                # 4.2s - 5.4s: 人物向右侧左右晃动滑动退场 (Wiggle & Slide out to right)
                f_exit = f - 126
                p_exit = f_exit / 36.0
                cur_x = 460 + int(700 * math.pow(p_exit, 1.8))
                cur_y = 600 + int(6.0 * math.sin(f_exit * 0.8))
                frame_img.paste(jia_down, (cur_x, cur_y), mask=jia_down)
                
            # 2. 便利贴卡片与红色按钮控制
            if f < 126:
                # 正常静止放置
                note_x = 90
                note_y = 520
                frame_img.paste(note_card, (note_x, note_y), mask=note_card)
                
                # 红色挂断按钮晃动 (Wiggle): 在 54 - 80 帧之间 (1.8s - 2.7s)
                if 54 <= f <= 80:
                    wig_prog = (f - 54) / 26.0
                    decay = 1.0 - wig_prog
                    angle = 9.0 * math.sin((f - 54) * 1.6) * decay
                    btn_rot = rotate_image(btn_hangup, angle)
                    bw, bh = btn_rot.size
                    # 居中对齐在 (245, 860)
                    bx = 245 + 72 - bw // 2
                    by = 860 + 72 - bh // 2
                    frame_img.paste(btn_rot, (bx, by), mask=btn_rot)
                else:
                    frame_img.paste(btn_hangup, (245, 860), mask=btn_hangup)
                    
            else:
                # 4.2s - 5.4s: 便利贴被撕掉剥离飞出动效 (Peel off & Fly away)
                f_peel = f - 126
                p_peel = f_peel / 36.0
                # 旋转逐渐变大
                angle = -35.0 * math.pow(p_peel, 1.2)
                
                # 组合卡片与按钮为一个整体做撕下旋转
                temp_card = note_card.copy()
                temp_card.paste(btn_hangup, (155, 340), mask=btn_hangup)
                
                # 旋转
                card_rot = rotate_image(temp_card, angle)
                rw, rh = card_rot.size
                
                # 抛物线飞出轨迹 (向上、向左旋转加速飞出)
                note_x = 90 - int(280 * math.pow(p_peel, 1.5))
                note_y = 520 - int(800 * math.pow(p_peel, 2.0))
                frame_img.paste(card_rot, (note_x, note_y), mask=card_rot)
                
        else:
            # ================= 第二阶段：第二张图出场与痛点检查录 (5.4s - 11.5s) =================
            f_b = f - 162
            total_b = TOTAL_FRAMES - 162
            
            # 5.4s - 6.2s: 从左侧轻微阻尼滑入
            if f_b < 24:
                prog_b = f_b / 24.0
                ease_b = 1.0 - math.pow(1.0 - prog_b, 3)
                offset_x = int(-120 * (1.0 - ease_b))
            else:
                offset_x = 0
                
            # 缓慢镜头推进 (1.00x -> 1.04x)
            scale = 1.000 + 0.040 * (f_b / total_b)
            
            # 8.5s 以后 (念到 "开单率怎么也上不去"): 微镜头推向第3条痛点
            if f >= 255:
                p_focus = min(1.0, (f - 255) / 60.0)
                scale += 0.025 * p_focus
                
            new_w = int(WIDTH * scale)
            new_h = int(HEIGHT * scale)
            crop_x = int((new_w - WIDTH) * 0.5) - offset_x
            crop_y = int((new_h - HEIGHT) * 0.48)
            
            scaled_b = img_b.resize((new_w, new_h), Image.Resampling.BILINEAR)
            frame_img = scaled_b.crop((crop_x, crop_y, crop_x + WIDTH, crop_y + HEIGHT))
            
        # 绘制底部字幕
        sub_text = get_subtitle(f)
        draw_subtitle_pill(frame_img, sub_text)
        
        # 写入 FFmpeg
        proc.stdin.write(frame_img.tobytes())
        
        if f % 45 == 0 or f == TOTAL_FRAMES - 1:
            print(f"进度: {f + 1}/{TOTAL_FRAMES} 帧 ({(f + 1) / TOTAL_FRAMES * 100:.1f}%)")
            
    proc.stdin.close()
    proc.wait()
    print(f"渲染完成！输出文件: {OUTPUT_VIDEO}")

if __name__ == "__main__":
    main()
