"""
Audio Generation Engine for Full Film using zh-CN-YunxiNeural
Generates master audio and timestamps manifest for all 5 scenes.
Voice: zh-CN-YunxiNeural (rate=+16%, volume=+0%)
"""

import asyncio
import json
import os
import subprocess
import edge_tts

VOICE = "zh-CN-YunxiNeural"
RATE = "+16%"
BASE_DIR = r"d:\video\视频3"
AUDIO_OUT_DIR = os.path.join(BASE_DIR, "output", "audio")
os.makedirs(AUDIO_OUT_DIR, exist_ok=True)

# 5 幕标准台词（已合规化更新）
SCRIPTS = {
    "scene_01": [
        {"id": "s1_1", "text": "刚开口，就被客户秒挂！", "pause_after": 0.30, "pose": "Pose1_通话"},
        {"id": "s1_2", "text": "面对客户的现在忙、不需要，大脑一片空白不知如何回复。", "pause_after": 0.35, "pose": "Pose2_看手机"},
        {"id": "s1_3", "text": "新人缺乏异议经验，根本留不住客户，", "pause_after": 0.25, "pose": "Pose3_揉眉心"},
        {"id": "s1_4", "text": "导致开单率怎么也上不去。", "pause_after": 0.40, "pose": "Pose4_叹气"}
    ],
    "scene_02": [
        {"id": "s2_1", "text": "别担心，只是你练少了！", "pause_after": 0.28, "pose": "2A_练少了"},
        {"id": "s2_2", "text": "找不到人随时陪练、怕拿客户试错？", "pause_after": 0.40, "pose": "2A_找不到人陪练"},
        {"id": "s2_3", "text": "好帮手 AI 学习助手重磅上线——话术私教！", "pause_after": 0.35, "pose": "2B_重磅上线"},
        {"id": "s2_4", "text": "从开场白、报价到促成，24 关实战异议地图，", "pause_after": 0.30, "pose": "2C_食指点划"},
        {"id": "s2_5", "text": "随时随地像打游戏一样刷满肌肉记忆。", "pause_after": 0.50, "pose": "2C_握拳打满"}
    ],
    "scene_03": [
        {"id": "s3_1", "text": "点击挑战，你的对手比真实客户更挑剔！", "pause_after": 0.35, "pose": "Pose1_食指指向"},
        {"id": "s3_2", "text": "AI 瞬间化身各种刁钻性格的客户，逼真模拟高压通话。", "pause_after": 0.38, "pose": "Pose2_扶眼镜吃惊"},
        {"id": "s3_3", "text": "在零风险的安全屋里，把所有怯场和大脑空白，在正式开单前全部排雷！", "pause_after": 0.50, "pose": "Pose3_双手抱胸"}
    ],
    "scene_04": [
        {"id": "s4_1", "text": "一通练完，AI立刻输出深度体检单！", "pause_after": 0.30, "pose": "Pose1_体检单"},
        {"id": "s4_2", "text": "第一次只有45分？", "pause_after": 0.35, "pose": "Pose1_耸肩错愕"},
        {"id": "s4_3", "text": "别慌，它给的可不是泛泛的加油，", "pause_after": 0.25, "pose": "Pose2_托腮思考"},
        {"id": "s4_4", "text": "而是指骨到肉的解法：", "pause_after": 0.30, "pose": "Pose2_托腮思考"},
        {"id": "s4_5", "text": "开场白太冗长？直接教你‘利益前置’——", "pause_after": 0.35, "pose": "Pose2_利益前置"},
        {"id": "s4_6", "text": "第一句话抛出‘为您定制了专属免费道路救援权益’，", "pause_after": 0.30, "pose": "Pose3_道路救援"},
        {"id": "s4_7", "text": "一秒锁死客户注意力！", "pause_after": 0.50, "pose": "Pose3_OK自信"}
    ],
    "scene_05": [
        {"id": "s5_1", "text": "刻意练习肌肉记忆，每一次通关都在给你的钱包充值！", "pause_after": 0.35, "pose": "Pose1_握拳蓄力"},
        {"id": "s5_2", "text": "练透 24 关实战异议地图，新手也能蜕变销售冠军。", "pause_after": 0.35, "pose": "Pose2_开掌邀请"},
        {"id": "s5_3", "text": "现在就打开好帮手 APP，点击学习助手开启话术私教，开启你的销冠之旅！", "pause_after": 0.60, "pose": "Pose3_点赞通关"}
    ]
}

def get_audio_duration(file_path):
    cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{file_path}"'
    res = subprocess.check_output(cmd, shell=True).decode().strip()
    return float(res)

async def build_scene(scene_key, lines):
    print(f"\n--- 生成 {scene_key} (云希 Yunxi · {RATE}) ---")
    seg_files = []
    manifest = []
    cur_time = 0.0

    for idx, item in enumerate(lines):
        seg_name = f"temp_{scene_key}_{idx}.mp3"
        seg_path = os.path.join(AUDIO_OUT_DIR, seg_name)
        text = item["text"]
        pause = item.get("pause_after", 0.3)
        pose = item.get("pose", "")

        comm = edge_tts.Communicate(text, VOICE, rate=RATE)
        await comm.save(seg_path)
        dur = get_audio_duration(seg_path)

        manifest.append({
            "id": item["id"],
            "text": text,
            "start": round(cur_time, 3),
            "end": round(cur_time + dur, 3),
            "duration": round(dur, 3),
            "pause_after": pause,
            "pose": pose
        })
        cur_time += dur + pause
        seg_files.append((seg_path, dur, pause))

    total_target = round(cur_time, 3)
    print(f"[{scene_key}] 总时长: {total_target} 秒")

    # 使用 ffmpeg 拼接加静音
    concat_txt = os.path.join(AUDIO_OUT_DIR, f"concat_{scene_key}.txt")
    temp_wavs = []

    for i, (f_mp3, dur, pause) in enumerate(seg_files):
        # 转成 wav 并加末尾静音
        seg_wav = os.path.join(AUDIO_OUT_DIR, f"seg_{scene_key}_{i}.wav")
        if pause > 0.02:
            # apad
            cmd = f'ffmpeg -y -i "{f_mp3}" -af "apad=pad_dur={pause}" -ar 44100 -ac 1 "{seg_wav}"'
        else:
            cmd = f'ffmpeg -y -i "{f_mp3}" -ar 44100 -ac 1 "{seg_wav}"'
        subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        temp_wavs.append(seg_wav)

    with open(concat_txt, "w", encoding="utf-8") as f:
        for w in temp_wavs:
            abs_w = os.path.abspath(w).replace("\\", "/")
            f.write(f"file '{abs_w}'\n")

    out_master_wav = os.path.join(AUDIO_OUT_DIR, f"{scene_key}_yunxi_master.wav")
    cmd_merge = f'ffmpeg -y -f concat -safe 0 -i "{concat_txt}" -c:a pcm_s16le -ar 44100 -ac 1 "{out_master_wav}"'
    subprocess.run(cmd_merge, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 清理临时文件
    for f_mp3, _, _ in seg_files:
        if os.path.exists(f_mp3):
            os.remove(f_mp3)
    for w in temp_wavs:
        if os.path.exists(w):
            os.remove(w)
    if os.path.exists(concat_txt):
        os.remove(concat_txt)

    actual_dur = get_audio_duration(out_master_wav)
    print(f"[{scene_key}] 母带就绪: {out_master_wav} (实际时长: {actual_dur:.3f}s)")
    return manifest

async def main():
    all_manifests = {}
    for sc, lines in SCRIPTS.items():
        m = await build_scene(sc, lines)
        all_manifests[sc] = m

    manifest_json = os.path.join(AUDIO_OUT_DIR, "manifest_yunxi.json")
    with open(manifest_json, "w", encoding="utf-8") as f:
        json.dump(all_manifests, f, ensure_ascii=False, indent=2)
    print(f"\n[ALL DONE] 全片 5 幕云希母带与时间戳清单已保存: {manifest_json}")

if __name__ == "__main__":
    asyncio.run(main())
