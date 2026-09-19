# -*- coding: utf-8 -*-
import os
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE_DIR = r"d:\video\视频3"
OUTPUT_PATH = os.path.join(BASE_DIR, "素材", "04_分幕原生画卷", "Scene02B_重磅上线_话术私教.jpg")

FONT_HEAVY = r"C:\Windows\Fonts\msyhbd.ttc"
if not os.path.exists(FONT_HEAVY):
    FONT_HEAVY = r"C:\Windows\Fonts\msyh.ttc"
FONT_REG = r"C:\Windows\Fonts\msyh.ttc"
FONT_ARIAL = r"C:\Windows\Fonts\arialbd.ttf"
if not os.path.exists(FONT_ARIAL):
    FONT_ARIAL = FONT_HEAVY

WIDTH = 1080
HEIGHT = 1920

def create_launch_image():
    # 1. 纯净杂志底板：使用无字的真实网格与折痕纸张
    clean_bg_path = os.path.join(BASE_DIR, "素材", "05_分层动画切片", "magazine_paper_bg_1080x1920.png")
    if os.path.exists(clean_bg_path):
        base_canvas = Image.open(clean_bg_path).convert("RGBA").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    else:
        base_canvas = Image.new("RGBA", (WIDTH, HEIGHT), (250, 247, 242, 255))
        
    draw = ImageDraw.Draw(base_canvas)
    
    # 2. 顶部章节标 (居中对齐杂志风)
    font_stage = ImageFont.truetype(FONT_ARIAL, 34)
    stage_text = "STAGE 02 // FEATURE UPDATE"
    bbox_stage = draw.textbbox((0, 0), stage_text, font=font_stage)
    stage_w = bbox_stage[2] - bbox_stage[0]
    draw.text(((WIDTH - stage_w) // 2, 75), stage_text, font=font_stage, fill=(60, 55, 50, 255))
    
    # 3. 左侧边缘 CASE STUDY 04 竖排文字
    font_case = ImageFont.truetype(FONT_ARIAL, 28)
    case_txt = "CASE  STUDY  04"
    case_img = Image.new("RGBA", (400, 50), (0, 0, 0, 0))
    case_draw = ImageDraw.Draw(case_img)
    case_draw.text((0, 10), case_txt, font=font_case, fill=(80, 75, 70, 255))
    rot_case = case_img.rotate(90, expand=True, resample=Image.Resampling.BICUBIC)
    base_canvas.alpha_composite(rot_case, (35, 800))
    draw = ImageDraw.Draw(base_canvas)
    
    # 4. 主标题区 (好帮手 AI 学习助手 / 重磅上线 —— 话术私教！)
    font_h1 = ImageFont.truetype(FONT_HEAVY, 68)
    font_h2 = ImageFont.truetype(FONT_HEAVY, 72)
    
    # 第一行文字
    draw.text((105, 175), "好帮手 AI 学习助手", font=font_h1, fill=(32, 30, 28, 255))
    
    # 荧光橙马克笔高亮笔触 (覆盖 话术私教！ 字样)
    hl_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    hl_draw = ImageDraw.Draw(hl_layer)
    hl_draw.rounded_rectangle([(445, 288), (965, 362)], radius=12, fill=(255, 142, 58, 195))
    base_canvas = Image.alpha_composite(base_canvas, hl_layer)
    draw = ImageDraw.Draw(base_canvas)
    
    # 第二行文字
    draw.text((105, 275), "重磅上线 —— 话术私教！", font=font_h2, fill=(32, 30, 28, 255))
    
    # 5. 手账卡片 1：平安好帮手 App 官方发布身份卡
    card1_w = 880
    card1_h = 220
    c1_x = (WIDTH - card1_w) // 2
    c1_y = 380
    
    # 柔和阴影
    shadow1 = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    s1_draw = ImageDraw.Draw(shadow1)
    s1_draw.rounded_rectangle([(c1_x + 8, c1_y + 10), (c1_x + card1_w + 8, c1_y + card1_h + 10)], radius=24, fill=(0, 0, 0, 30))
    shadow1 = shadow1.filter(ImageFilter.GaussianBlur(10))
    base_canvas = Image.alpha_composite(base_canvas, shadow1)
    draw = ImageDraw.Draw(base_canvas)
    
    # 白色微暖卡片底板
    draw.rounded_rectangle([(c1_x, c1_y), (c1_x + card1_w, c1_y + card1_h)], radius=24, fill=(255, 255, 255, 250), outline=(225, 220, 210, 220), width=2)
    
    # 贴入好帮手官方 App 图标 (圆角遮罩)
    app_icon_path = os.path.join(BASE_DIR, "素材", "03_业务界面与UI", "好帮手APP图标.png")
    if os.path.exists(app_icon_path):
        app_icon = Image.open(app_icon_path).convert("RGBA").resize((140, 140), Image.Resampling.LANCZOS)
        mask = Image.new("L", (140, 140), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([(0, 0), (140, 140)], radius=22, fill=255)
        icon_rounded = Image.new("RGBA", (140, 140), (0, 0, 0, 0))
        icon_rounded.paste(app_icon, (0, 0), mask)
        base_canvas.alpha_composite(icon_rounded, (c1_x + 35, c1_y + 40))
        
    font_app_title = ImageFont.truetype(FONT_HEAVY, 40)
    font_app_sub = ImageFont.truetype(FONT_REG, 24)
    font_tag = ImageFont.truetype(FONT_HEAVY, 21)
    
    draw = ImageDraw.Draw(base_canvas)
    draw.text((c1_x + 205, c1_y + 35), "平安好帮手 · 话术私教", font=font_app_title, fill=(32, 30, 28, 255))
    draw.text((c1_x + 205, c1_y + 92), "新一代销冠对练引擎 · 全流程智能陪练体系", font=font_app_sub, fill=(110, 105, 100, 255))
    
    # 三个胶囊小标签 (纯净文字无乱码字符)
    tags = [
        ("★ 官方重磅", (255, 236, 230), (217, 56, 58)),
        ("● 24关通关制", (235, 246, 235), (26, 110, 60)),
        ("● 拟真高压对练", (235, 242, 252), (30, 85, 175))
    ]
    cur_tag_x = c1_x + 205
    for tag_txt, tag_bg, tag_col in tags:
        bbox_t = draw.textbbox((0, 0), tag_txt, font=font_tag)
        t_w = bbox_t[2] - bbox_t[0]
        draw.rounded_rectangle([(cur_tag_x, c1_y + 140), (cur_tag_x + t_w + 22, c1_y + 180)], radius=9, fill=tag_bg)
        draw.text((cur_tag_x + 11, c1_y + 148), tag_txt, font=font_tag, fill=tag_col)
        cur_tag_x += t_w + 30
        
    # 6. 手账卡片 2：三大硬核实战模块卡片
    card2_w = 880
    card2_h = 750
    c2_x = (WIDTH - card2_w) // 2
    c2_y = 635
    
    # 阴影
    shadow2 = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    s2_draw = ImageDraw.Draw(shadow2)
    s2_draw.rounded_rectangle([(c2_x + 8, c2_y + 12), (c2_x + card2_w + 8, c2_y + card2_h + 12)], radius=28, fill=(0, 0, 0, 35))
    shadow2 = shadow2.filter(ImageFilter.GaussianBlur(12))
    base_canvas = Image.alpha_composite(base_canvas, shadow2)
    draw = ImageDraw.Draw(base_canvas)
    
    # 便签纸主体
    draw.rounded_rectangle([(c2_x, c2_y), (c2_x + card2_w, c2_y + card2_h)], radius=28, fill=(254, 252, 248, 255), outline=(225, 220, 210, 220), width=2)
    
    # 顶部红色顶条
    draw.rounded_rectangle([(c2_x, c2_y), (c2_x + card2_w, c2_y + 72)], radius=28, fill=(217, 56, 58, 245))
    draw.rectangle([(c2_x, c2_y + 45), (c2_x + card2_w, c2_y + 72)], fill=(217, 56, 58, 245))
    
    font_c2_head = ImageFont.truetype(FONT_HEAVY, 31)
    draw.text((c2_x + 35, c2_y + 20), "★ 新人销冠进阶 · 三大硬核实战模块", font=font_c2_head, fill=(255, 255, 255, 255))
    
    # 三大核心功能详情
    items = [
        {
            "num": "01",
            "tag": "24关实战异议地图",
            "tag_bg": (255, 232, 218),
            "tag_color": (205, 75, 25),
            "title": "从开场白、报价到促成，全链路排雷",
            "desc": "打破枯燥背话术，像打游戏通关一样刷满肌肉记忆！"
        },
        {
            "num": "02",
            "tag": "AI 拟真高压对练",
            "tag_bg": (225, 242, 255),
            "tag_color": (25, 90, 190),
            "title": "模拟真实挑剔客户，零风险对战安全屋",
            "desc": "瞬间化身各种刁钻性格，上战场前把所有怯场全部排空！"
        },
        {
            "num": "03",
            "tag": "深度体检残暴诊断",
            "tag_bg": (232, 248, 235),
            "tag_color": (25, 120, 55),
            "title": "骨肉级诊断解法，一秒利益前置锁死客户",
            "desc": "不给空泛的加油，直接教你第一句话切中客户痛点！"
        }
    ]
    
    font_item_num = ImageFont.truetype(FONT_HEAVY, 33)
    font_item_tag = ImageFont.truetype(FONT_HEAVY, 24)
    font_item_t = ImageFont.truetype(FONT_HEAVY, 29)
    font_item_d = ImageFont.truetype(FONT_REG, 23)
    
    item_start_y = c2_y + 105
    for i, it in enumerate(items):
        cur_y = item_start_y + i * 205
        
        # 序号黑色实心圆
        draw.ellipse([(c2_x + 40, cur_y), (c2_x + 94, cur_y + 54)], fill=(32, 30, 28, 255))
        draw.text((c2_x + 48, cur_y + 6), it["num"], font=font_item_num, fill=(255, 255, 255, 255))
        
        # 功能模块标签
        bbox_tag = draw.textbbox((0, 0), it["tag"], font=font_item_tag)
        tag_w = bbox_tag[2] - bbox_tag[0]
        draw.rounded_rectangle([(c2_x + 115, cur_y + 3), (c2_x + 115 + tag_w + 24, cur_y + 51)], radius=8, fill=it["tag_bg"])
        draw.text((c2_x + 127, cur_y + 12), it["tag"], font=font_item_tag, fill=it["tag_color"])
        
        # 主功能句
        draw.text((c2_x + 115, cur_y + 66), it["title"], font=font_item_t, fill=(32, 30, 28, 255))
        # 解释句
        draw.text((c2_x + 115, cur_y + 112), it["desc"], font=font_item_d, fill=(110, 105, 100, 255))
        
        # 分割线
        if i < 2:
            draw.line([(c2_x + 40, cur_y + 168), (c2_x + card2_w - 40, cur_y + 168)], fill=(225, 220, 210, 180), width=1)
            
    # 7. 手账卡片 3：CTA 标牌
    card3_w = 880
    card3_h = 135
    c3_x = (WIDTH - card3_w) // 2
    c3_y = 1425
    
    shadow3 = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    s3_draw = ImageDraw.Draw(shadow3)
    s3_draw.rounded_rectangle([(c3_x + 6, c3_y + 8), (c3_x + card3_w + 6, c3_y + card3_h + 8)], radius=26, fill=(0, 0, 0, 30))
    shadow3 = shadow3.filter(ImageFilter.GaussianBlur(8))
    base_canvas = Image.alpha_composite(base_canvas, shadow3)
    draw = ImageDraw.Draw(base_canvas)
    
    # 黑金质感圆角底板
    draw.rounded_rectangle([(c3_x, c3_y), (c3_x + card3_w, c3_y + card3_h)], radius=26, fill=(32, 30, 28, 245), outline=(217, 160, 60, 200), width=3)
    font_c3 = ImageFont.truetype(FONT_HEAVY, 35)
    font_c3_sub = ImageFont.truetype(FONT_REG, 23)
    
    draw.text((c3_x + 45, c3_y + 26), "即刻进入【话术私教】", font=font_c3, fill=(255, 225, 130, 255))
    draw.text((c3_x + 45, c3_y + 80), "随时随地刷满肌肉记忆 · 开启销冠之路 >>", font=font_c3_sub, fill=(215, 210, 200, 255))
    
    # 右侧复古朱红印章【重磅首发】
    stamp_layer = Image.new("RGBA", (220, 90), (0, 0, 0, 0))
    st_draw = ImageDraw.Draw(stamp_layer)
    st_draw.rounded_rectangle([(4, 4), (210, 80)], radius=12, outline=(217, 56, 58, 255), width=3)
    st_draw.rounded_rectangle([(8, 8), (206, 76)], radius=9, outline=(217, 56, 58, 255), width=1)
    font_stamp = ImageFont.truetype(FONT_HEAVY, 28)
    st_draw.text((25, 24), "★ 重磅首发 ★", font=font_stamp, fill=(217, 56, 58, 255))
    
    rot_stamp = stamp_layer.rotate(-6, resample=Image.Resampling.BICUBIC, expand=True)
    base_canvas.alpha_composite(rot_stamp, (c3_x + 620, c3_y + 18))
    
    # 保存最终高精画卷
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    final_rgb = base_canvas.convert("RGB")
    final_rgb.save(OUTPUT_PATH, quality=96)
    print(f"Successfully generated clean Scene 02B launch image: {OUTPUT_PATH}")

if __name__ == "__main__":
    create_launch_image()

