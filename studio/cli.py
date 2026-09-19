import os
import sys
import argparse
import asyncio
import shutil

from studio.core.config import StoryboardConfig
from studio.core.manifest import TimestampManifest
from studio.audio.audio_builder import AudioBuilder
from studio.prompt.prompt_builder import PromptBuilder
from studio.engine.renderer import SceneRenderer
from studio.assembly.concatenator import SceneConcatenator
from studio.assembly.ducking_mixer import DuckingMixer

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

def find_config_path(project_arg: str = "") -> str:
    """Locate storyboard.yaml or storyboard.json in project path or current directory."""
    candidates = []
    if project_arg:
        if os.path.isfile(project_arg):
            return os.path.abspath(project_arg)
        candidates.append(os.path.join(project_arg, "storyboard.yaml"))
        candidates.append(os.path.join(project_arg, "storyboard.yml"))
        candidates.append(os.path.join(project_arg, "storyboard.json"))
        
    cwd = os.getcwd()
    candidates.append(os.path.join(cwd, "storyboard.yaml"))
    candidates.append(os.path.join(cwd, "storyboard.yml"))
    candidates.append(os.path.join(cwd, "storyboard.json"))
    
    for c in candidates:
        if os.path.exists(c):
            return os.path.abspath(c)
            
    raise FileNotFoundError(
        "Could not find storyboard.yaml or storyboard.json. "
        "Please specify --project <dir_or_file> or run in a project root."
    )

def cmd_init(args):
    """Initializes a new video project scaffolding."""
    target_dir = os.path.abspath(args.name)
    if os.path.exists(target_dir) and os.listdir(target_dir):
        print(f"Error: Target directory '{target_dir}' already exists and is not empty.")
        sys.exit(1)
        
    os.makedirs(os.path.join(target_dir, "assets", "masterframes"), exist_ok=True)
    os.makedirs(os.path.join(target_dir, "assets", "anchors"), exist_ok=True)
    os.makedirs(os.path.join(target_dir, "assets", "bgm"), exist_ok=True)
    os.makedirs(os.path.join(target_dir, "audio"), exist_ok=True)
    os.makedirs(os.path.join(target_dir, "output", "video"), exist_ok=True)
    os.makedirs(os.path.join(target_dir, "output", "qa_frames"), exist_ok=True)
    
    # Locate default template
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_yaml = os.path.join(repo_root, "templates", "default_project", "storyboard.yaml")
    
    dest_yaml = os.path.join(target_dir, "storyboard.yaml")
    if os.path.exists(template_yaml):
        shutil.copy2(template_yaml, dest_yaml)
    else:
        # Fallback inline minimal storyboard
        with open(dest_yaml, "w", encoding="utf-8") as f:
            f.write("""project:
  name: "my_video"
  title: "我的高品质短视频"
  resolution: [1080, 1920]
  fps: 30
  style_preset: "journal_scrapbook"
  audio:
    voice: "zh-CN-YunxiNeural"
    rate: "+20%"

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
""")
            
    # Add .gitkeep files to keep empty dirs in git if needed
    for sub in ["masterframes", "anchors", "bgm"]:
        with open(os.path.join(target_dir, "assets", sub, ".gitkeep"), "w") as f:
            pass
            
    print(f"\n🎉 Successfully initialized project at: {target_dir}")
    print(f"👉 Next steps:")
    print(f"  1. Edit '{os.path.join(target_dir, 'storyboard.yaml')}' to define your script & scenes.")
    print(f"  2. Run 'python -m studio audio build --project {target_dir}' to synthesize speech.")
    print(f"  3. Run 'python -m studio prompt generate --project {target_dir}' to get masterframe prompts.")

def cmd_audio(args):
    config_path = find_config_path(args.project)
    config = StoryboardConfig.load(config_path)
    builder = AudioBuilder(config)
    asyncio.run(builder.build_all())

def cmd_prompt(args):
    config_path = find_config_path(args.project)
    config = StoryboardConfig.load(config_path)
    builder = PromptBuilder(config)
    builder.export()

def cmd_render(args):
    config_path = find_config_path(args.project)
    config = StoryboardConfig.load(config_path)
    renderer = SceneRenderer(config)
    
    if args.all:
        print(f"Rendering all {len(config.scenes)} scenes in storyboard sequentially...")
        rendered = []
        for idx in range(1, len(config.scenes) + 1):
            mp4 = renderer.render_scene(idx)
            rendered.append(mp4)
        print(f"\n🎉 All {len(rendered)} scenes successfully rendered!")
    elif args.scene:
        renderer.render_scene(args.scene)
    else:
        print("Please specify --scene <id_or_number> or --all to render.")

def cmd_assemble(args):
    config_path = find_config_path(args.project)
    config = StoryboardConfig.load(config_path)
    project_dir = config.project_dir
    video_dir = os.path.join(project_dir, "output", "video")
    
    scene_mp4s = []
    for sc in config.scenes:
        sc_id = sc.get("id")
        mp4_path = os.path.join(video_dir, f"{sc_id}.mp4")
        if not os.path.exists(mp4_path):
            raise FileNotFoundError(f"Required scene成片 not found: {mp4_path}. Render it first!")
        scene_mp4s.append(mp4_path)
        
    concat_output = os.path.join(video_dir, f"{config.name}_raw_concat.mp4")
    final_output = os.path.join(video_dir, f"{config.name}_1080P_Final.mp4")
    
    print(f"Concatenating {len(scene_mp4s)} scenes...")
    SceneConcatenator.concat(scene_mp4s, concat_output)
    print(f"✓ Scenes concatenated to: {concat_output}")
    
    # Check BGM
    bgm_file = args.bgm or config.bgm_file
    if not bgm_file:
        # Search in assets/bgm
        bgm_candidates = os.listdir(os.path.join(project_dir, "assets", "bgm")) if os.path.exists(os.path.join(project_dir, "assets", "bgm")) else []
        for f in bgm_candidates:
            if f.lower().endswith((".mp3", ".wav", ".aac", ".m4a")):
                bgm_file = os.path.join(project_dir, "assets", "bgm", f)
                break
                
    if bgm_file and os.path.exists(bgm_file):
        print(f"Mixing BGM with dynamic sidechain ducking ({bgm_file})...")
        DuckingMixer.mix(
            concat_output,
            bgm_file,
            final_output,
            ducked_volume=config.bgm_volume_active,
            idle_volume=config.bgm_volume_idle
        )
        if os.path.exists(concat_output):
            os.remove(concat_output)
        print(f"\n🎉 Final masterpiece with BGM delivered to: {final_output}")
    else:
        print("Notice: No BGM file provided or found. Delivering raw assembled video.")
        if os.path.exists(final_output):
            os.remove(final_output)
        os.rename(concat_output, final_output)
        print(f"\n🎉 Final masterpiece delivered to: {final_output}")

def main():
    parser = argparse.ArgumentParser(
        prog="studio",
        description="human-ai-video-director: Industrial-grade short-video production pipeline."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # init
    p_init = subparsers.add_parser("init", help="Initialize a new project scaffold")
    p_init.add_argument("name", help="Name of project directory to create")
    
    # audio
    p_audio = subparsers.add_parser("audio", help="Build voice master and timestamp manifest")
    p_audio.add_argument("action", choices=["build"], help="Action to perform")
    p_audio.add_argument("--project", "-p", default="", help="Project directory or storyboard file")
    
    # prompt
    p_prompt = subparsers.add_parser("prompt", help="Generate 4-section In-Context Prompts for AI image tools")
    p_prompt.add_argument("action", choices=["generate"], help="Action to perform")
    p_prompt.add_argument("--project", "-p", default="", help="Project directory or storyboard file")
    
    # render
    p_render = subparsers.add_parser("render", help="Render scenes to MP4 with native stop-motion and subtitles")
    p_render.add_argument("--project", "-p", default="", help="Project directory or storyboard file")
    p_render.add_argument("--scene", "-s", default="", help="Scene ID or number to render (e.g. 1 or scene_01)")
    p_render.add_argument("--all", "-a", action="store_true", help="Render all scenes in storyboard")
    
    # assemble
    p_assemble = subparsers.add_parser("assemble", help="Losslessly concatenate scenes and mix BGM with ducking")
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
