"""CLI for the human-ai-video-director studio pipeline."""

from __future__ import annotations

import argparse
import asyncio
import os
import shutil
import sys

from studio.assembly.concatenator import SceneConcatenator
from studio.assembly.ducking_mixer import DuckingMixer
from studio.audio.audio_builder import AudioBuilder
from studio.core.config import StoryboardConfig
from studio.core.proc import require_ffmpeg
from studio.engine.renderer import SceneRenderer
from studio.prompt.prompt_builder import PromptBuilder

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


STORYBOARD_NAMES = ("storyboard.yaml", "storyboard.yml", "storyboard.json")
AUDIO_EXTS = (".mp3", ".wav", ".aac", ".m4a")


def find_config_path(project_arg: str = "") -> str:
    """Locate storyboard.yaml. A given --project never falls back to cwd."""
    if project_arg:
        path = os.path.abspath(project_arg)
        if os.path.isfile(path):
            return path
        if os.path.isdir(path):
            for name in STORYBOARD_NAMES:
                candidate = os.path.join(path, name)
                if os.path.exists(candidate):
                    return os.path.abspath(candidate)
            raise FileNotFoundError(
                f"No storyboard.yaml/yml/json in --project directory: {path}"
            )
        raise FileNotFoundError(f"--project path does not exist: {path}")

    cwd = os.getcwd()
    for name in STORYBOARD_NAMES:
        candidate = os.path.join(cwd, name)
        if os.path.exists(candidate):
            return os.path.abspath(candidate)
    raise FileNotFoundError(
        "Could not find storyboard.yaml or storyboard.json. "
        "Pass --project <dir_or_file> or run inside a project root."
    )


def resolve_project_path(project_dir: str, maybe_relative: str) -> str:
    if not maybe_relative:
        return ""
    if os.path.isabs(maybe_relative) and os.path.exists(maybe_relative):
        return maybe_relative
    joined = os.path.abspath(os.path.join(project_dir, maybe_relative))
    if os.path.exists(joined):
        return joined
    if os.path.exists(maybe_relative):
        return os.path.abspath(maybe_relative)
    return joined


def cmd_init(args) -> None:
    target_dir = os.path.abspath(args.name)
    if os.path.exists(target_dir) and os.listdir(target_dir):
        print(f"Error: Target directory '{target_dir}' already exists and is not empty.")
        sys.exit(1)

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(repo_root, "templates", "default_project")
    os.makedirs(target_dir, exist_ok=True)
    if os.path.isdir(template_dir):
        shutil.copytree(template_dir, target_dir, dirs_exist_ok=True)
    else:
        dest_yaml = os.path.join(target_dir, "storyboard.yaml")
        with open(dest_yaml, "w", encoding="utf-8") as handle:
            handle.write(
                """project:
  name: "my_video"
  title: "我的高品质短视频"
  resolution: [1080, 1920]
  fps: 30
  style_preset: "journal_scrapbook"
  audio:
    voice: "zh-CN-YunxiNeural"
    rate: "+20%"
    bgm_volume_active: 0.12
    bgm_volume_idle: 0.25
    bgm_file: ""

scenes:
  - id: "scene_01"
    stage_tag: "STAGE 01 // 痛点觉醒"
    headline: "第一幕痛点标题"
    transition:
      type: "none"
    dialogue_segments:
      - id: "s1_1"
        text: "这里填写第一幕第一句核心台词。"
        pose: "Pose1_初始姿态"
    timing:
      initial_delay: 0.30
      pause_between: 0.28
      tail_pad: 0.50
"""
            )

    for rel in (
        os.path.join("assets", "masterframes"),
        os.path.join("assets", "anchors"),
        os.path.join("assets", "bgm"),
        "audio",
        os.path.join("output", "video"),
        os.path.join("output", "qa_frames"),
    ):
        os.makedirs(os.path.join(target_dir, rel), exist_ok=True)
    for sub in ("masterframes", "anchors", "bgm"):
        keep = os.path.join(target_dir, "assets", sub, ".gitkeep")
        if not os.path.exists(keep):
            with open(keep, "w", encoding="utf-8") as handle:
                handle.write("")

    try:
        require_ffmpeg()
    except RuntimeError as exc:
        print(f"Warning: {exc}")

    print(f"\nSuccessfully initialized project at: {target_dir}")
    print("Next steps:")
    print(f"  1. Edit '{os.path.join(target_dir, 'storyboard.yaml')}'")
    print(f"  2. python -m studio audio build --project {target_dir}")
    print(f"  3. python -m studio prompt generate --project {target_dir}")


def cmd_audio(args) -> None:
    require_ffmpeg()
    config = StoryboardConfig.load(find_config_path(args.project))
    builder = AudioBuilder(config)
    scene = getattr(args, "scene", "") or None
    asyncio.run(builder.build_all(scene_id=scene))


def cmd_prompt(args) -> None:
    config = StoryboardConfig.load(find_config_path(args.project))
    PromptBuilder(config).export()


def cmd_render(args) -> None:
    require_ffmpeg()
    config = StoryboardConfig.load(find_config_path(args.project))
    renderer = SceneRenderer(config)
    action = getattr(args, "action", None)
    render_all = bool(args.all) or action == "all"
    scene = args.scene or ""
    if action and action not in ("scene", "all") and not scene:
        scene = action

    if render_all and scene:
        print("Error: --scene and --all are mutually exclusive.")
        sys.exit(1)
    if render_all:
        print(f"Rendering all {len(config.scenes)} scenes sequentially...")
        rendered = []
        for idx in range(1, len(config.scenes) + 1):
            rendered.append(renderer.render_scene(idx))
        print(f"\nAll {len(rendered)} scenes successfully rendered!")
        return
    if not scene:
        print("Please specify --scene <id_or_number> or --all to render.")
        sys.exit(1)
    renderer.render_scene(scene)


def cmd_assemble(args) -> None:
    require_ffmpeg()
    config = StoryboardConfig.load(find_config_path(args.project))
    project_dir = config.project_dir
    video_dir = os.path.join(project_dir, "output", "video")

    scene_mp4s = []
    for sc in config.scenes:
        sc_id = sc.get("id")
        mp4_path = os.path.join(video_dir, f"{sc_id}.mp4")
        if not os.path.exists(mp4_path):
            raise FileNotFoundError(f"Required scene file not found: {mp4_path}. Render it first.")
        scene_mp4s.append(mp4_path)

    concat_output = os.path.join(video_dir, f"{config.name}_raw_concat.mp4")
    final_output = os.path.join(video_dir, f"{config.name}_1080P_Final.mp4")
    print(f"Concatenating {len(scene_mp4s)} scenes...")
    SceneConcatenator.concat(scene_mp4s, concat_output)
    print(f"Scenes concatenated to: {concat_output}")

    configured = args.bgm or config.bgm_file
    bgm_file = ""
    if configured:
        bgm_file = resolve_project_path(project_dir, configured)
        if not os.path.isfile(bgm_file):
            raise FileNotFoundError(
                f"BGM file not found: {configured} (resolved: {bgm_file})"
            )
    else:
        bgm_dir = os.path.join(project_dir, "assets", "bgm")
        candidates = []
        if os.path.isdir(bgm_dir):
            candidates = [
                os.path.join(bgm_dir, name)
                for name in sorted(os.listdir(bgm_dir))
                if name.lower().endswith(AUDIO_EXTS)
            ]
        if len(candidates) > 1:
            listing = "\n  ".join(candidates)
            raise FileNotFoundError(
                "Multiple BGM files in assets/bgm; pass --bgm or set project.audio.bgm_file:\n  "
                + listing
            )
        if len(candidates) == 1:
            bgm_file = candidates[0]

    if bgm_file:
        print(f"Mixing BGM with dynamic sidechain ducking ({bgm_file})...")
        DuckingMixer.mix(
            concat_output,
            bgm_file,
            final_output,
            ducked_volume=config.bgm_volume_active,
            idle_volume=config.bgm_volume_idle,
        )
        if os.path.exists(concat_output):
            os.remove(concat_output)
        print(f"\nFinal masterpiece with BGM delivered to: {final_output}")
        return

    print("Notice: No BGM file provided or found. Delivering raw assembled video.")
    if os.path.exists(final_output):
        os.remove(final_output)
    os.rename(concat_output, final_output)
    print(f"\nFinal masterpiece delivered to: {final_output}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="studio",
        description="human-ai-video-director: Industrial-grade short-video production pipeline.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    p_init = subparsers.add_parser("init", help="Initialize a new project scaffold")
    p_init.add_argument("name", help="Name of project directory to create")

    p_audio = subparsers.add_parser("audio", help="Build voice master and timestamp manifest")
    p_audio.add_argument("action", choices=["build"], help="Action to perform")
    p_audio.add_argument("--project", "-p", default="", help="Project directory or storyboard file")
    p_audio.add_argument("--scene", "-s", default="", help="Optional scene id to rebuild only that scene")

    p_prompt = subparsers.add_parser("prompt", help="Generate in-context prompts")
    p_prompt.add_argument("action", choices=["generate"], help="Action to perform")
    p_prompt.add_argument("--project", "-p", default="", help="Project directory or storyboard file")

    p_render = subparsers.add_parser("render", help="Render scenes to MP4")
    p_render.add_argument(
        "action",
        nargs="?",
        default=None,
        help="Optional: scene | all | <scene id or number>",
    )
    p_render.add_argument("--project", "-p", default="", help="Project directory or storyboard file")
    p_render.add_argument("--scene", "-s", default="", help="Scene ID or number (e.g. 1 or scene_01)")
    p_render.add_argument("--all", "-a", action="store_true", help="Render all scenes")

    p_assemble = subparsers.add_parser("assemble", help="Concatenate scenes and mix BGM")
    p_assemble.add_argument("--project", "-p", default="", help="Project directory or storyboard file")
    p_assemble.add_argument("--bgm", default="", help="Path to background music file")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "init":
        cmd_init(args)
    elif args.command == "audio":
        cmd_audio(args)
    elif args.command == "prompt":
        cmd_prompt(args)
    elif args.command == "render":
        cmd_render(args)
    elif args.command == "assemble":
        cmd_assemble(args)


if __name__ == "__main__":
    main()
