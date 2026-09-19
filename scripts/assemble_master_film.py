import os
import sys
import subprocess

# Reconfigure stdout to utf-8 for Windows console emojis
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
BASE_DIR = r'd:\video\视频3'
VIDEO_DIR = os.path.join(BASE_DIR, 'output', 'video')
QA_DIR = os.path.join(BASE_DIR, 'output', 'qa_frames', 'master_film')
OUTPUT_MASTER = os.path.join(VIDEO_DIR, '好帮手AI话术私教_终极宣传大片_1080P.mp4')

SCENES = [
    ('Scene 01 (秒挂痛点 · 真实开场)', os.path.join(VIDEO_DIR, 'scene_01_animated_v3.mp4')),
    ('Scene 02 (破局重塑 · 重磅上线+24关地图)', os.path.join(VIDEO_DIR, 'scene_02_animated_v2.mp4')),
    ('Scene 03 (拟真对攻 · 安全屋高压排雷)', os.path.join(VIDEO_DIR, 'scene_03_animated_v2.mp4')),
    ('Scene 04 (深度诊断 · 45分体检与利益前置)', os.path.join(VIDEO_DIR, 'scene_04_animated_v2.mp4')),
    ('Scene 05 (通关升华 · 再练一次与行动号召)', os.path.join(VIDEO_DIR, 'scene_05_animated_v2.mp4')),
]

def check_scenes():
    print('=== 检查分幕视频就绪状态 ===')
    all_ready = True
    total_expected_dur = 0.0
    for name, path in SCENES:
        if os.path.exists(path):
            size_mb = os.path.getsize(path) / (1024 * 1024)
            cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', path]
            dur = float(subprocess.check_output(cmd, text=True).strip())
            total_expected_dur += dur
            print(f'✅ {name}: 已就绪 ({size_mb:.2f} MB, 时长: {dur:.3f}s) -> {os.path.basename(path)}')
        else:
            print(f'⏳ {name}: 未找到文件 -> {os.path.basename(path)}')
            all_ready = False
    print(f'预估全片总时长: {total_expected_dur:.3f} 秒 (约 {total_expected_dur/60:.2f} 分钟)')
    return all_ready

def assemble():
    if not check_scenes():
        print('\n⚠️ 仍有分幕未就绪，请核对文件路径后再执行合成！')
        return False

    print('\n=== 开始全片无损拼接合成 (Master Assembly) ===')
    concat_list_path = os.path.join(VIDEO_DIR, 'concat_list.txt')
    with open(concat_list_path, 'w', encoding='utf-8') as f:
        for _, path in SCENES:
            escaped_path = path.replace(chr(92), '/')
            f.write(f"file '{escaped_path}'\n")

    cmd = [
        'ffmpeg', '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', concat_list_path,
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-preset', 'medium',
        '-crf', '18',
        '-c:a', 'aac',
        '-b:a', '320k',
        '-movflags', '+faststart',
        OUTPUT_MASTER
    ]
    print('执行 FFmpeg 合成命令...')
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print('合成失败:', res.stderr)
        return False

    total_size = os.path.getsize(OUTPUT_MASTER) / (1024 * 1024)
    dur_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', OUTPUT_MASTER]
    total_dur = float(subprocess.check_output(dur_cmd, text=True).strip())
    print(f'\n🎉 全片大合流交付成功！')
    print(f'总时长: {total_dur:.3f} 秒 ({total_dur/60:.2f} 分钟)')
    print(f'总大小: {total_size:.2f} MB')
    print(f'成片路径: {OUTPUT_MASTER}')

    os.makedirs(QA_DIR, exist_ok=True)
    # 采样点涵盖全片 5 幕核心关键帧：
    # S1: 5.0s (秒挂痛点), S2: 18.0s (无人物重磅上线卡), S2: 23.0s (24关地图划线),
    # S3: 33.0s (拟真对攻安全屋), S4: 48.0s (45分体检与利益前置), S5: 63.0s (通关升华点赞)
    sample_timestamps = [
        (1, 5.0, 'Scene01_秒挂痛点'),
        (2, 18.0, 'Scene02_重磅发布卡'),
        (3, 23.0, 'Scene02_24关实战地图'),
        (4, 33.0, 'Scene03_拟真对攻对练'),
        (5, 48.0, 'Scene04_45分体检与利益前置'),
        (6, 63.0, 'Scene05_通关升华点赞')
    ]
    for idx, ts, desc in sample_timestamps:
        qa_out = os.path.join(QA_DIR, f'master_qa_{idx:02d}_{desc}.jpg')
        cmd_qa = ['ffmpeg', '-y', '-ss', str(ts), '-i', OUTPUT_MASTER, '-vframes', '1', '-q:v', '2', qa_out]
        subprocess.run(cmd_qa, capture_output=True)
        print(f'已提取全片验收关键帧 {idx} ({ts}s - {desc}): {qa_out}')

    return True

if __name__ == '__main__':
    assemble()
