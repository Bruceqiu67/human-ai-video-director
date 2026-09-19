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

BASE_DIR = r'd:\video\视频3'
DEMO_DIR = os.path.join(BASE_DIR, '素材', '04_分幕原生画卷')
AUDIO_FILE = os.path.join(BASE_DIR, 'output', 'audio', 'scene1_v3_master_audio.wav')
OUTPUT_VIDEO = os.path.join(BASE_DIR, 'output', 'video', 'scene_01_animated_v3.mp4')
QA_DIR = os.path.join(BASE_DIR, 'output', 'qa_frames', 'scene_01')

FONT_HEAVY = r'C:\Windows\Fonts\msyhbd.ttc'
if not os.path.exists(FONT_HEAVY):
    FONT_HEAVY = r'C:\Windows\Fonts\msyh.ttc'

WIDTH = 1080
HEIGHT = 1920
FPS = 30
TOTAL_FRAMES = 360  # 12.000s @ 30fps

def get_subtitle(frame):
    # 0 - 9 (0.00s - 0.30s): 静音专注开场，无字幕
    # 9 - 68 (0.30s - 2.25s): 刚开口，就被客户秒挂
    # 68 - 74 (2.25s - 2.45s): 秒挂忙音，无字幕
    # 74 - 132 (2.45s - 4.40s): 面对客户的‘现在忙、不需要’
    # 132 - 198 (4.40s - 6.60s): 大脑一片空白不知如何回复
    # 198 - 219 (6.60s - 7.30s): 翻书折页转场，无字幕
    # 219 - 293 (7.30s - 9.77s): 新人缺乏异议经验，根本留不住客户
    # 293 - 298 (9.77s - 9.95s): 气口微歇，无字幕
    # 298 - 360 (9.95s - 12.00s): 最后导致开单率怎么也上不去。
    if frame < 9:
        return None
    elif frame < 68:
        return "刚开口，就被客户秒挂"
    elif frame < 74:
        return None
    elif frame < 132:
        return "面对客户的‘现在忙、不需要’"
    elif frame < 198:
        return "大脑一片空白不知如何回复"
    elif frame < 219:
        return None
    elif frame < 293:
        return "新人缺乏异议经验，根本留不住客户"
    elif frame < 298:
        return None
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
    print('=== 开始渲染全新第一幕 (Scene 01 v3 · 纯正手账定格原画) ===')
    os.makedirs(QA_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_VIDEO), exist_ok=True)
    
    p_a_call = os.path.join(DEMO_DIR, 'Scene01A_秒挂痛点_手持电话.jpg')
    p_a_down = os.path.join(DEMO_DIR, 'Scene01A_秒挂痛点_愁眉苦脸看手机.jpg')
    p_a_nose = os.path.join(DEMO_DIR, 'Scene01A_秒挂痛点_捏鼻梁揉眉心.jpg')
    p_a_sigh = os.path.join(DEMO_DIR, 'Scene01A_秒挂痛点_扶额叹气.jpg')
    p_a_pain = os.path.join(DEMO_DIR, 'Scene01A_秒挂痛点_痛苦后仰.jpg')
    
    img_a1_raw = Image.open(p_a_call).convert('RGB').resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    img_a2_raw = Image.open(p_a_down).convert('RGB').resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    img_a3_raw = Image.open(p_a_nose).convert('RGB').resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    img_a4_raw = Image.open(p_a_sigh).convert('RGB').resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    img_a5_raw = Image.open(p_a_pain).convert('RGB').resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    
    # 彻底废除代码切分与羽化缝合，100% 采用大模型同底原生画卷，彻底根除文字错位与半透明重影！
    img_a_pose1 = img_a1_raw  # 1. 专注通话
    img_a_pose2 = img_a2_raw  # 2. 愣住看手机（秒挂发生）
    img_a_pose3 = img_a3_raw  # 3. 捏鼻梁揉眉心发愁
    img_a_pose4 = img_a4_raw  # 4. 扶额深深叹气
    img_a_pose5 = img_a5_raw  # 5. 痛苦后仰生无可恋
    
    p_b1_path = os.path.join(DEMO_DIR, 'Scene01B_危机清单_挠头苦笑.jpg')
    p_b2_path = os.path.join(DEMO_DIR, 'Scene01B_危机清单_挠后脑勺.jpg')
    
    img_b1_raw = Image.open(p_b1_path).convert('RGB').resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    img_b2_raw = Image.open(p_b2_path).convert('RGB').resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    
    img_b_pose1 = img_b1_raw  # 危机清单：挠侧面苦笑
    img_b_pose2 = img_b2_raw  # 危机清单：挠后脑勺发愁
    
    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-s', f'{WIDTH}x{HEIGHT}',
        '-pix_fmt', 'rgba',
        '-r', str(FPS),
        '-i', '-',
        '-i', AUDIO_FILE,
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-preset', 'fast',
        '-crf', '18',
        '-c:a', 'aac',
        '-b:a', '320k',
        '-shortest',
        OUTPUT_VIDEO
    ]
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
    
    print('正在逐帧生成纯正定格动画（已去除一切人物动效，字音毫秒级同步）...')
    
    for f in range(TOTAL_FRAMES):
        shake_x = 0
        shake_y = 0
        
        if f < 198:
            # ================= 阶段 1：01A 秒挂痛点 (0.0s - 6.6s / 198帧) =================
            if f < 68:
                # 0.0s - 2.25s (0 ~ 67帧): 嘉彬专注贴耳打电话（台词：刚开口，就被客户秒挂）
                curr_pose = img_a_pose1
            elif f < 108:
                # 2.25s - 3.60s (68 ~ 107帧): 秒挂忙音响，定格抽帧瞬切至【低头看手机发愁】（台词：面对客户的‘现在忙、不需要’）
                curr_pose = img_a_pose2
                # 68 ~ 74 帧：秒挂扎心惊愕小震颤
                if 68 <= f <= 74:
                    decay = math.exp(-(f - 68) * 0.4)
                    shake_x = int(math.sin((f - 68) * 2.2) * 5.0 * decay)
                    shake_y = int(math.cos((f - 68) * 1.8) * 3.0 * decay)
            elif f < 148:
                # 3.60s - 4.93s (108 ~ 147帧): 定格抽帧瞬切至【捏鼻梁揉眉心发愁】（新图1）
                curr_pose = img_a_pose3
            elif f < 180:
                # 4.93s - 6.00s (148 ~ 179帧): 定格抽帧瞬切至【右手扶额深深叹气】（新图2，台词：大脑一片空白）
                curr_pose = img_a_pose4
            else:
                # 6.00s - 6.60s (180 ~ 197帧): 定格抽帧瞬切至【痛苦闭眼微后仰，生无可恋】（台词：不知如何回复）
                curr_pose = img_a_pose5
                
            frame_base = curr_pose.copy()
            
            if shake_x != 0 or shake_y != 0:
                shaken = Image.new('RGB', (WIDTH, HEIGHT), (242, 238, 229))
                shaken.paste(frame_base, (shake_x, shake_y))
                frame_base = shaken
                
        elif f < 219:
            # ================= 阶段 2：01A 翻书转场进入 01B (6.6s - 7.3s / 21帧) =================
            p_turn = (f - 198) / 21.0
            frame_base = create_page_turn(img_a_pose5, img_b_pose1, p_turn)
            
        else:
            # ================= 阶段 3：01B 危机清单 (7.3s - 12.0s / 141帧) =================
            f_rel = f - 219
            # 严格按照每 30 帧 (1.0 秒) 定格交替一次挠头姿态
            cycle_phase = (f_rel // 30) % 2
            if cycle_phase == 0:
                curr_b_pose = img_b_pose1  # 挠侧面苦笑
            else:
                curr_b_pose = img_b_pose2  # 挠后脑勺发愁
                
            frame_base = curr_b_pose.copy()
            
        frame_final = frame_base.convert('RGBA')
        
        # 底部居中胶囊字幕
        sub_text = get_subtitle(f)
        draw_subtitle_pill(frame_final, sub_text)
        
        if f in [30, 72, 120, 160, 190, 208, 230, 260, 290, 320, 350]:
            qa_out = os.path.join(QA_DIR, f'frame_{str(f).zfill(3)}.png')
            frame_final.save(qa_out)
            print(f'[QA] 提取关键走查帧 {f} -> {qa_out}')
            
        proc.stdin.write(frame_final.tobytes())
        
        if f % 45 == 0 or f == TOTAL_FRAMES - 1:
            pct = (f + 1) / TOTAL_FRAMES * 100
            print(f'渲染进度: {f + 1}/{TOTAL_FRAMES} 帧 ({pct:.1f}%)')
            
    proc.stdin.close()
    proc.wait()
    print(f'🎉 第一幕独立成片渲染完成！保存在: {OUTPUT_VIDEO}')

if __name__ == '__main__':
    main()
