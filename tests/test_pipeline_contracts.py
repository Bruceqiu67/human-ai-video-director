"""Behavioral contracts for the studio pipeline (no network TTS required)."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import traceback
import wave

from PIL import Image

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)


def _fail(message: str) -> None:
    raise AssertionError(message)


def test_pose_matching_scene_numbers() -> None:
    from studio.engine.assets import filename_belongs_to_scene, match_pose_filename

    assert filename_belongs_to_scene("Scene01_手持电话.jpg", "scene_01")
    assert filename_belongs_to_scene("scene_01_pose1.jpg", "scene_01")
    assert not filename_belongs_to_scene("Scene10_map.jpg", "scene_01")
    assert filename_belongs_to_scene("Scene10_map.jpg", "scene_10")
    assert not filename_belongs_to_scene("Scene01B_结尾最后一帧.png", "scene_02")

    files = [
        "Scene02_破局重塑_Pose1_摆手安慰.jpg",
        "Scene02A_破局共鸣_主管没空教.jpg",
    ]
    assert match_pose_filename("主管没空教", 1, files) == "Scene02A_破局共鸣_主管没空教.jpg"
    files_pose_first = [
        "scene_02_pose1.jpg",
        "Scene02A_破局共鸣_主管没空教.jpg",
    ]
    assert match_pose_filename("主管没空教", 1, files_pose_first) == "Scene02A_破局共鸣_主管没空教.jpg"
    patched = [
        "Scene04_Pose1_耸肩错愕.jpg",
        "Scene04_Pose1_耸肩错愕_合规修补版.jpg",
    ]
    assert match_pose_filename("耸肩错愕", 1, patched) == "Scene04_Pose1_耸肩错愕_合规修补版.jpg"
    assert match_pose_filename("missing_pose", 9, files) is None


def test_ducking_filter_order() -> None:
    from studio.assembly.ducking_mixer import DuckingMixer

    filt = DuckingMixer.build_filter_complex(0.12, 0.25)
    assert "volume=0.25" in filt
    assert "[bgm][voice]sidechaincompress" in filt
    assert "[0:a][sc]sidechaincompress" not in filt
    assert "normalize=0" in filt
    try:
        DuckingMixer.build_filter_complex(0.3, 0.2)
        _fail("expected ducked >= idle to raise")
    except ValueError:
        pass


def test_amix_and_tail_pad_filter() -> None:
    from studio.audio.audio_builder import AudioBuilder

    filt = AudioBuilder.build_mix_filter([0, 1200, 3000], 0.5)
    assert "normalize=0" in filt
    assert "apad=pad_dur=0.500" in filt
    assert "amix=inputs=3" in filt
    single = AudioBuilder.build_mix_filter([300], 0.4)
    assert "amix=" not in single
    assert "apad=pad_dur=0.400" in single


def test_concat_list_utf8_and_quotes() -> None:
    from studio.assembly.concatenator import SceneConcatenator

    line = SceneConcatenator.format_concat_line(r"D:\video\视频3\out.mp4")
    assert line.startswith("file '")
    assert "视频3" in line or "video" in line
    quoted = SceneConcatenator.format_concat_line(r"C:\o'reilly\a.mp4")
    assert r"'\''" in quoted


def test_find_config_path_no_cwd_fallback() -> None:
    from studio.cli import find_config_path

    missing = os.path.join(WORKSPACE_ROOT, "does_not_exist_project_xyz")
    try:
        find_config_path(missing)
        _fail("missing --project should not fall back to cwd")
    except FileNotFoundError:
        pass
    template = os.path.join(WORKSPACE_ROOT, "templates", "default_project")
    path = find_config_path(template)
    assert path.endswith("storyboard.yaml")


def test_yaml_none_and_missing_id() -> None:
    from studio.core.config import StoryboardConfig

    try:
        StoryboardConfig(None, "x.yaml")  # type: ignore[arg-type]
        _fail("None root should raise")
    except ValueError:
        pass
    try:
        StoryboardConfig({"project": {}, "scenes": [{"headline": "x"}]}, "x.yaml")
        _fail("missing id should raise")
    except ValueError:
        pass
    cfg = StoryboardConfig.load(
        os.path.join(WORKSPACE_ROOT, "templates", "default_project", "storyboard.yaml")
    )
    assert cfg.get_scene(1)["id"] == "scene_01"


def test_style_unknown_and_subtitle_colors() -> None:
    from studio.styles import get_style

    tech = get_style("modern_tech")
    assert tech.subtitle_bg[0] == 15
    try:
        get_style("not-a-style")
        _fail("unknown style should raise")
    except ValueError:
        pass
    hyphen = get_style("journal-scrapbook")
    assert hyphen.name == "journal_scrapbook"


def test_prompt_not_locked_to_black_tshirt() -> None:
    from studio.core.config import StoryboardConfig
    from studio.prompt.prompt_builder import PromptBuilder

    cfg = StoryboardConfig.load(
        os.path.join(WORKSPACE_ROOT, "templates", "default_project", "storyboard.yaml")
    )
    md = PromptBuilder(cfg).generate_markdown()
    assert "Background & Layout Lock" in md
    assert "black crewneck t-shirt" not in md.lower()
    tech_data = dict(cfg.raw)
    tech_data["project"] = dict(cfg.raw["project"])
    tech_data["project"]["style_preset"] = "modern_tech"
    tech_cfg = StoryboardConfig(tech_data, cfg.config_path)
    tech_md = PromptBuilder(tech_cfg).generate_markdown()
    assert "navy" in tech_md.lower() or "SaaS" in tech_md


def test_manifest_storyboard_mismatch() -> None:
    from studio.core.manifest import TimestampManifest

    man = TimestampManifest({
        "scene_01": {
            "total_duration": 2.0,
            "segments": [{"id": "s1_1", "text": "old", "pose": "a", "start": 0, "end": 1}],
        }
    })
    scene = {
        "id": "scene_01",
        "dialogue_segments": [{"id": "s1_1", "text": "new", "pose": "a"}],
    }
    try:
        man.assert_matches_storyboard(scene)
        _fail("text mismatch should raise")
    except ValueError as exc:
        assert "mismatch" in str(exc).lower() or "Re-run" in str(exc)


def test_subtitle_fits_and_uses_style_color() -> None:
    from studio.engine.subtitles import AdaptiveCapsuleSubtitle

    canvas = Image.new("RGBA", (1080, 1920), (250, 247, 242, 255))
    engine = AdaptiveCapsuleSubtitle(
        default_font_size=40,
        max_width=920,
        fill=(15, 23, 42, 220),
        text_fill=(248, 250, 252, 255),
    )
    long_text = "这是一句没有逗号的超长中文标题用来验证字幕不会画出画面两侧之外并且必须被缩小或折行"
    out = engine.render(canvas, long_text, y_center=1680)
    assert out.size == (1080, 1920)


def test_stopmotion_half_open_interval() -> None:
    from studio.engine.stopmotion import StopMotionSequencer

    red = Image.new("RGBA", (8, 8), (255, 0, 0, 255))
    blue = Image.new("RGBA", (8, 8), (0, 0, 255, 255))
    seq = StopMotionSequencer(
        [{"id": "a", "start": 0.0, "end": 1.0, "pose": "A"},
         {"id": "b", "start": 1.2, "end": 2.0, "pose": "B"}],
        {"A": red, "B": blue},
        red,
    )
    assert seq.get_frame(0.5).getpixel((0, 0))[0] == 255
    # gap keeps previous pose
    assert seq.get_frame(1.1).getpixel((0, 0))[0] == 255
    assert seq.get_frame(1.5).getpixel((0, 0))[2] == 255


def test_empty_tts_text() -> None:
    import asyncio

    from studio.audio.tts_engine import TTSEngine

    async def _run():
        try:
            await TTSEngine().synthesize("  ", "x.mp3")
            _fail("empty TTS should raise")
        except ValueError:
            pass

    asyncio.run(_run())


def _write_silence_wav(path: str, seconds: float = 0.4, rate: int = 44100) -> None:
    frames = int(rate * seconds)
    with wave.open(path, "w") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(b"\x00\x00" * frames)


def test_missing_masterframe_raises() -> None:
    from studio.core.config import StoryboardConfig
    from studio.core.manifest import TimestampManifest
    from studio.engine.renderer import SceneRenderer

    with tempfile.TemporaryDirectory() as tmp:
        yaml_path = os.path.join(tmp, "storyboard.yaml")
        with open(yaml_path, "w", encoding="utf-8") as handle:
            handle.write(
                """project:
  name: t
  title: t
  resolution: [64, 64]
  fps: 30
  style_preset: journal_scrapbook
  audio:
    voice: zh-CN-YunxiNeural
    rate: "+20%"
scenes:
  - id: scene_01
    headline: h
    dialogue_segments:
      - id: s1_1
        text: hello
        pose: Pose1
"""
            )
        cfg = StoryboardConfig.load(yaml_path)
        man = TimestampManifest({
            "scene_01": {
                "total_duration": 0.4,
                "segments": [{"id": "s1_1", "text": "hello", "pose": "Pose1", "start": 0.0, "end": 0.3, "fx": []}],
            }
        }, os.path.join(tmp, "audio", "timestamps_manifest.json"))
        os.makedirs(os.path.join(tmp, "audio"), exist_ok=True)
        _write_silence_wav(os.path.join(tmp, "audio", "scene_01_master.wav"))
        renderer = SceneRenderer(cfg, man)
        try:
            renderer.render_scene(1)
            _fail("missing masterframe should raise")
        except FileNotFoundError:
            pass


def test_one_frame_render_if_ffmpeg() -> None:
    import shutil

    if shutil.which("ffmpeg") is None:
        print("  skip test_one_frame_render_if_ffmpeg (no ffmpeg)")
        return

    from studio.core.config import StoryboardConfig
    from studio.core.manifest import TimestampManifest
    from studio.engine.renderer import SceneRenderer

    with tempfile.TemporaryDirectory() as tmp:
        yaml_path = os.path.join(tmp, "storyboard.yaml")
        with open(yaml_path, "w", encoding="utf-8") as handle:
            handle.write(
                """project:
  name: t
  title: t
  resolution: [64, 64]
  fps: 30
  style_preset: journal_scrapbook
  audio:
    voice: zh-CN-YunxiNeural
    rate: "+20%"
scenes:
  - id: scene_01
    headline: h
    transition:
      type: none
    dialogue_segments:
      - id: s1_1
        text: hi
        pose: Pose1
        fx: ["highlighter_sweep"]
"""
            )
        mf = os.path.join(tmp, "assets", "masterframes")
        os.makedirs(mf, exist_ok=True)
        Image.new("RGBA", (64, 64), (250, 247, 242, 255)).save(
            os.path.join(mf, "scene_01_pose1.png")
        )
        os.makedirs(os.path.join(tmp, "audio"), exist_ok=True)
        _write_silence_wav(os.path.join(tmp, "audio", "scene_01_master.wav"), 0.4)
        cfg = StoryboardConfig.load(yaml_path)
        man = TimestampManifest({
            "scene_01": {
                "total_duration": 0.4,
                "segments": [{
                    "id": "s1_1", "text": "hi", "pose": "Pose1",
                    "start": 0.0, "end": 0.3, "fx": ["highlighter_sweep"],
                }],
            }
        })
        out = SceneRenderer(cfg, man).render_scene(1)
        assert os.path.isfile(out)
        assert os.path.isfile(os.path.join(tmp, "assets", "anchors", "scene_01_end.png"))


def test_stop_motion_bounce_and_camera_director() -> None:
    from PIL import Image
    from studio.engine.camera import CameraDirector, KenBurnsZoom, StopMotionBounce

    cut_times = [1.5, 3.0]
    # Before cut: scale is 1.0
    assert abs(StopMotionBounce.get_scale(1.0, cut_times) - 1.0) < 0.001
    # Right inside the cut window (1.54s): scale punches out (> 1.01)
    scale_punch = StopMotionBounce.get_scale(1.55, cut_times)
    assert scale_punch > 1.01
    # After cut window (1.80s): scale returns to 1.0
    assert abs(StopMotionBounce.get_scale(1.80, cut_times) - 1.0) < 0.001

    # Test CameraDirector.apply_combined
    img = Image.new("RGBA", (100, 200), (255, 0, 0, 255))
    res = CameraDirector.apply_combined(img, push_progress=0.5, t=1.55, cut_times=cut_times)
    assert res.size == (100, 200)


def test_prompt_builder_tripod_lock() -> None:
    from studio.core.config import StoryboardConfig
    from studio.prompt.prompt_builder import PromptBuilder

    cfg = StoryboardConfig.load(
        os.path.join(WORKSPACE_ROOT, "templates", "default_project", "storyboard.yaml")
    )
    md = PromptBuilder(cfg).generate_markdown()
    assert "TRIPOD" in md
    assert "DELTA POSE" in md or "微动姿态" in md


def test_cinematic_multi_pose_and_relative_paths() -> None:
    from studio.prompt.cinematic import CinematicPromptEngine

    segments = [
        {"text": "第一句话", "pose": "正面微笑", "duration": 3.0},
        {"text": "第二句话很长超出了五秒钟的平台时间限制", "pose": "抬手讲解", "duration": 8.0},
    ]
    prompts = CinematicPromptEngine.generate_scene_video_prompts(
        scene_idx=1,
        stage_tag="STAGE 01",
        headline="测试多姿态",
        segments=segments,
        total_scenes=1,
        character_prompt="测试人物",
    )
    assert len(prompts) == 2
    # Issue 37: Multi-pose clips must have pose index to avoid overwriting
    assert prompts[0]["output_ai_name"] == "scene_01_p01.mp4"
    assert prompts[1]["output_ai_name"] == "scene_01_p02.mp4"

    # Issue 38: Relative paths without hardcoded projects/ prefix
    assert prompts[0]["first_frame_path"] == "assets/masterframes/Scene01_pose_1.jpg"
    assert prompts[0]["end_frame_path"] == "assets/anchors/scene_01_end.png"
    assert "projects/" not in prompts[0]["first_frame_path"]

    # Issue 39: Duration descriptions in SOP
    class DummyConfig:
        name = "test_proj"
        title = "测试项目"
        character_prompt = "测试人物"
        scenes = [{
            "id": "scene_01",
            "stage_tag": "STAGE 01",
            "headline": "测试",
            "dialogue_segments": segments,
        }]

    sop_md = CinematicPromptEngine.generate_full_sop_markdown(DummyConfig())
    assert "建议平台选择 5s 档位" in sop_md
    assert "单句时长超 5s，平台需选择 10s 档位或使用 Extend 功能延展" in sop_md
    assert "projects/test_proj/assets/raw_video" not in sop_md


def test_style_registry_expanded() -> None:
    from studio.styles import STYLE_REGISTRY, get_style

    for style_name in ["clay_3d", "clay", "minimal_black", "minimal", "custom"]:
        profile = get_style(style_name)
        assert profile is not None
        assert profile.name in ("clay_3d", "minimal_black", "journal_scrapbook")
        assert len(profile.prompt_background_lines()) > 0


def test_audio_builder_user_voice_takeover() -> None:
    import asyncio
    import math
    import struct
    import wave
    from studio.audio.audio_builder import AudioBuilder
    from studio.core.config import StoryboardConfig

    with tempfile.TemporaryDirectory() as tmp_dir:
        user_audio_dir = os.path.join(tmp_dir, "assets", "audio")
        os.makedirs(user_audio_dir, exist_ok=True)
        # Create a dummy user wav of 1.0 second (44100Hz, mono sine)
        user_wav_path = os.path.join(user_audio_dir, "scene_01_1.wav")
        with wave.open(user_wav_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(44100)
            data = bytearray()
            for i in range(44100):
                val = int(3000 * math.sin(2 * math.pi * 440 * i / 44100))
                data.extend(struct.pack("<h", val))
            wf.writeframes(data)

        cfg_dict = {
            "project": {"name": "test_audio", "title": "Test", "voice": "zh-CN-YunxiNeural", "rate": "+20%"},
            "scenes": [{
                "id": "scene_01",
                "stage_tag": "STAGE 01",
                "headline": "测试真人音频接管",
                "dialogue_segments": [{"id": "scene_01_1", "text": "这段文字不应该走TTS，因为有真人音频"}],
            }]
        }
        cfg = StoryboardConfig(cfg_dict, tmp_dir)
        builder = AudioBuilder(cfg)

        async def fail_tts(*args, **kwargs):
            raise AssertionError("TTS synthesize should NOT be called when user audio is present!")
        builder.tts.synthesize = fail_tts

        master_wav, segs, total_dur = asyncio.run(builder.build_scene_audio(cfg.scenes[0]))
        assert os.path.isfile(master_wav)
        assert len(segs) == 1
        assert segs[0]["duration"] > 0.5


def test_ai_conformer_video_and_audio_sync() -> None:
    from studio.assembly.ai_conformer import AIConformer
    from studio.audio.silence_trimmer import SilenceTrimmer
    from studio.core.proc import run_command

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create 1.0s video (320x240)
        short_video = os.path.join(tmp_dir, "short_ai.mp4")
        run_command([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", "color=c=blue:s=320x240:d=1.0:r=24",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            short_video,
        ])
        # Create 2.0s audio
        long_audio = os.path.join(tmp_dir, "master.wav")
        run_command([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=2.0",
            "-c:a", "pcm_s16le",
            long_audio,
        ])

        output_mp4 = os.path.join(tmp_dir, "conformed.mp4")
        AIConformer.conform_and_remux(
            video_clips=[short_video],
            output_path=output_mp4,
            master_audio=long_audio,
            width=1080,
            height=1920,
            fps=30,
        )

        assert os.path.isfile(output_mp4)
        out_dur = SilenceTrimmer.get_duration(output_mp4)
        # Verify video was NOT cut to 1.0s; it must match the 2.0s audio
        assert abs(out_dur - 2.0) < 0.2

        # Verify resolution
        res = run_command([
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=p=0",
            output_mp4,
        ])
        assert "1080,1920" in res.stdout


def all_tests() -> list:
    return [
        test_pose_matching_scene_numbers,
        test_ducking_filter_order,
        test_amix_and_tail_pad_filter,
        test_concat_list_utf8_and_quotes,
        test_find_config_path_no_cwd_fallback,
        test_yaml_none_and_missing_id,
        test_style_unknown_and_subtitle_colors,
        test_prompt_not_locked_to_black_tshirt,
        test_manifest_storyboard_mismatch,
        test_subtitle_fits_and_uses_style_color,
        test_stopmotion_half_open_interval,
        test_empty_tts_text,
        test_missing_masterframe_raises,
        test_one_frame_render_if_ffmpeg,
        test_stop_motion_bounce_and_camera_director,
        test_prompt_builder_tripod_lock,
        test_cinematic_multi_pose_and_relative_paths,
        test_style_registry_expanded,
        test_audio_builder_user_voice_takeover,
        test_ai_conformer_video_and_audio_sync,
    ]


def run_contract_tests() -> int:
    passed = 0
    failed = 0
    for fn in all_tests():
        try:
            fn()
            print(f"  ✓ {fn.__name__}")
            passed += 1
        except Exception as exc:
            print(f"  ❌ {fn.__name__}: {type(exc).__name__}: {exc}")
            traceback.print_exc()
            failed += 1
    print(f"Contract tests: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_contract_tests())
