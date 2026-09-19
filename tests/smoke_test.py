"""
Smoke Test & Dynamic Verification Suite for human-ai-video-director (studio).
Validates:
1. requirements.txt dependency consistency
2. Clean imports across all studio submodules (no circular dependencies)
3. ConfigParser loading templates/default_project/storyboard.yaml
4. PromptBuilder generation for 4-act / multi-act scenes
5. CLI help commands execution for root and all subcommands
"""

import sys
import os

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

import time
import importlib
import pkgutil
import subprocess
import warnings
from typing import List, Dict, Tuple


# Add workspace root to sys.path
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

def format_duration(seconds: float) -> str:
    if seconds < 0.001:
        return f"{seconds * 1_000_000:.1f} µs"
    elif seconds < 1.0:
        return f"{seconds * 1000:.2f} ms"
    return f"{seconds:.3f} s"

def check_requirements_consistency() -> Tuple[bool, List[str]]:
    """Verify installed packages against requirements.txt."""
    req_file = os.path.join(WORKSPACE_ROOT, "requirements.txt")
    if not os.path.exists(req_file):
        return False, [f"requirements.txt not found at {req_file}"]

    import importlib.metadata
    from packaging.requirements import Requirement

    messages = []
    all_passed = True

    with open(req_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            try:
                req = Requirement(line)
                installed_ver = importlib.metadata.version(req.name)
                # Check specifier
                if req.specifier and not req.specifier.contains(installed_ver):
                    messages.append(f"❌ {req.name}: installed {installed_ver} does NOT satisfy {req.specifier}")
                    all_passed = False
                else:
                    messages.append(f"✓ {req.name}: installed {installed_ver} satisfies {req.specifier or '(any)'}")
            except importlib.metadata.PackageNotFoundError:
                messages.append(f"❌ {line}: Package not installed!")
                all_passed = False
            except Exception as e:
                messages.append(f"❌ {line}: Failed to check requirement - {e}")
                all_passed = False

    return all_passed, messages

def check_clean_imports_and_circular_deps() -> Tuple[bool, List[str], List[str]]:
    """Verify all studio modules can be imported cleanly without circular dependencies or warnings."""
    studio_dir = os.path.join(WORKSPACE_ROOT, "studio")
    modules_to_test = []

    # Traverse all subpackages and modules in studio
    for root, dirs, files in os.walk(studio_dir):
        if "__pycache__" in root:
            continue
        rel_path = os.path.relpath(root, WORKSPACE_ROOT)
        pkg_parts = rel_path.replace("\\", "/").split("/")
        pkg_name = ".".join(pkg_parts)

        for file in files:
            if file.endswith(".py"):
                if file == "__init__.py":
                    modules_to_test.append(pkg_name)
                else:
                    mod_name = f"{pkg_name}.{file[:-3]}"
                    modules_to_test.append(mod_name)

    modules_to_test = sorted(list(set(modules_to_test)))
    
    import_logs = []
    recorded_warnings = []
    all_passed = True

    # Test importing each module with warning capture
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        for mod in modules_to_test:
            t0 = time.perf_counter()
            try:
                # Force fresh reload / import test in current runtime
                if mod in sys.modules:
                    imported_mod = importlib.reload(sys.modules[mod])
                else:
                    imported_mod = importlib.import_module(mod)
                elapsed = time.perf_counter() - t0
                import_logs.append(f"✓ {mod} ({format_duration(elapsed)})")
            except Exception as e:
                elapsed = time.perf_counter() - t0
                import_logs.append(f"❌ {mod} ({format_duration(elapsed)}): {type(e).__name__}: {e}")
                all_passed = False

        for w in captured:
            recorded_warnings.append(f"[{w.category.__name__}] {w.message} ({w.filename}:{w.lineno})")

    return all_passed, import_logs, recorded_warnings

def check_config_parser() -> Tuple[bool, List[str]]:
    """Test ConfigParser / StoryboardConfig loading templates/default_project/storyboard.yaml."""
    from studio.core.config import ConfigParser, StoryboardConfig

    logs = []
    template_yaml = os.path.join(WORKSPACE_ROOT, "templates", "default_project", "storyboard.yaml")
    
    if not os.path.exists(template_yaml):
        return False, [f"Template storyboard.yaml not found at {template_yaml}"]

    try:
        t0 = time.perf_counter()
        config = ConfigParser.load(template_yaml)
        elapsed = time.perf_counter() - t0

        logs.append(f"✓ ConfigParser loaded template in {format_duration(elapsed)}")
        logs.append(f"  - Project: '{config.name}', Title: '{config.title}'")
        logs.append(f"  - Resolution: {config.resolution}, FPS: {config.fps}, Style: '{config.style_preset}'")
        logs.append(f"  - Audio Voice: '{config.voice}', Rate: '{config.rate}', BGM Ducking: {config.bgm_volume_active} ~ {config.bgm_volume_idle}")
        logs.append(f"  - Total Scenes: {len(config.scenes)}")

        # Verify scenes integrity
        assert len(config.scenes) >= 4, f"Expected at least 4 scenes in template, found {len(config.scenes)}"
        for i, sc in enumerate(config.scenes, 1):
            assert "id" in sc, f"Scene #{i} missing 'id'"
            assert "headline" in sc, f"Scene #{i} missing 'headline'"
            assert "dialogue_segments" in sc and len(sc["dialogue_segments"]) > 0, f"Scene #{i} has no dialogue segments"

        # Verify get_scene by ID and index
        sc1_by_id = config.get_scene("scene_01")
        sc1_by_idx = config.get_scene(1)
        assert sc1_by_id is not None and sc1_by_id == sc1_by_idx, "get_scene lookup by ID and index mismatch"
        logs.append(f"✓ Scene lookup integrity verified (id='scene_01' & index=1 matched)")

        return True, logs
    except Exception as e:
        logs.append(f"❌ ConfigParser error: {type(e).__name__}: {e}")
        return False, logs

def check_prompt_builder() -> Tuple[bool, List[str]]:
    """Test PromptBuilder generating 4 acts / multi-act prompts from storyboard.yaml."""
    from studio.core.config import ConfigParser, StoryboardConfig
    from studio.prompt.prompt_builder import PromptBuilder

    logs = []
    template_yaml = os.path.join(WORKSPACE_ROOT, "templates", "default_project", "storyboard.yaml")

    try:
        config = ConfigParser.load(template_yaml)
        builder = PromptBuilder(config)

        t0 = time.perf_counter()
        md_content = builder.generate_markdown()
        elapsed = time.perf_counter() - t0

        logs.append(f"✓ PromptBuilder generated full markdown ({len(md_content)} chars) in {format_duration(elapsed)}")

        # Check key sections
        assert "大模型同底画卷标准提示词矩阵" in md_content, "Missing prompt matrix title"
        assert "生图核心铁律" in md_content, "Missing in-context non-negotiables"
        assert "Background & Layout Lock" in md_content, "Missing background layout lock"
        assert "Character & Pose" in md_content, "Missing character & pose spec"

        # Explicitly verify 4 acts prompt generation
        # Slicing 4 acts from storyboard config to test dedicated 4-act prompt generation
        four_act_data = dict(config.raw)
        four_act_data["scenes"] = config.scenes[:4]
        four_act_config = StoryboardConfig(four_act_data, config.config_path)

        t1 = time.perf_counter()
        four_act_builder = PromptBuilder(four_act_config)
        four_act_md = four_act_builder.generate_markdown()
        elapsed_4act = time.perf_counter() - t1

        # Verify each of the 4 acts exists in four_act_md
        for act_idx in range(1, 5):
            scene_header = f"Scene {act_idx:02d}"
            assert scene_header in four_act_md, f"Act {act_idx} header '{scene_header}' not found in 4-act output"
            # Verify Act headline
            expected_headline = four_act_config.scenes[act_idx - 1]["headline"]
            assert expected_headline in four_act_md, f"Act {act_idx} headline '{expected_headline}' not found"

        # Ensure Act 5 is NOT in 4-act generation
        assert "Scene 05" not in four_act_md, "Act 05 should not appear in 4-act generation"

        logs.append(f"✓ Verified 4-act dedicated prompt generation in {format_duration(elapsed_4act)}:")
        for act_idx in range(1, 5):
            sc = four_act_config.scenes[act_idx - 1]
            segs_count = len(sc.get("dialogue_segments", []))
            logs.append(f"  - Act {act_idx:02d} ({sc.get('stage_tag')}): '{sc.get('headline')}' -> {segs_count} poses")

        return True, logs
    except Exception as e:
        logs.append(f"❌ PromptBuilder error: {type(e).__name__}: {e}")
        return False, logs

def check_cli_subcommands() -> Tuple[bool, List[str]]:
    """Test python -m studio.cli --help and all subcommands (--help)."""
    subcommands = ["", "init", "audio", "prompt", "render", "assemble"]
    logs = []
    all_passed = True

    for sub in subcommands:
        cmd_str = f"python -m studio.cli {sub} --help".strip()
        cmd_args = [sys.executable, "-m", "studio.cli"]
        if sub:
            cmd_args.append(sub)
        cmd_args.append("--help")

        t0 = time.perf_counter()
        res = subprocess.run(
            cmd_args,
            cwd=WORKSPACE_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        elapsed = time.perf_counter() - t0

        if res.returncode == 0 and "usage: studio" in res.stdout:
            logs.append(f"✓ '{cmd_str}' exited 0 ({format_duration(elapsed)})")
        else:
            logs.append(f"❌ '{cmd_str}' failed! (code {res.returncode}):\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}")
            all_passed = False

    return all_passed, logs

# Pytest test cases (returns None, uses assert)
def test_pytest_requirements():
    passed, logs = check_requirements_consistency()
    assert passed, "\n".join(logs)

def test_pytest_clean_imports():
    passed, logs, warnings_list = check_clean_imports_and_circular_deps()
    assert passed, "\n".join(logs)

def test_pytest_config_parser():
    passed, logs = check_config_parser()
    assert passed, "\n".join(logs)

def test_pytest_prompt_builder():
    passed, logs = check_prompt_builder()
    assert passed, "\n".join(logs)

def test_pytest_cli_subcommands():
    passed, logs = check_cli_subcommands()
    assert passed, "\n".join(logs)


def run_smoke_test():
    total_start = time.perf_counter()
    print("=" * 70)
    print("🚀 Running Human-AI Video Studio Smoke Test & Dynamic Verification")
    print("=" * 70)

    # 1. Dependency Check
    print("\n[Phase 1] Checking requirements.txt dependencies...")
    req_passed, req_logs = check_requirements_consistency()
    for l in req_logs:
        print(f"  {l}")

    # 2. Module Clean Import & Circular Dependencies Check
    print("\n[Phase 2] Verifying module imports & checking circular dependencies...")
    import_passed, import_logs, warnings_list = check_clean_imports_and_circular_deps()
    for l in import_logs:
        print(f"  {l}")
    
    if warnings_list:
        print("\n  ⚠️ Captured Warnings during import:")
        for w in warnings_list:
            print(f"    - {w}")
    else:
        print("  ✓ Zero import warnings detected.")

    # 3. ConfigParser Load Test
    print("\n[Phase 3] Testing ConfigParser with templates/default_project/storyboard.yaml...")
    cfg_passed, cfg_logs = check_config_parser()
    for l in cfg_logs:
        print(f"  {l}")

    # 4. PromptBuilder 4-Act Generation Test
    print("\n[Phase 4] Testing PromptBuilder 4-act prompt matrix generation...")
    prompt_passed, prompt_logs = check_prompt_builder()
    for l in prompt_logs:
        print(f"  {l}")

    # 5. CLI & Subcommands Help Output Test
    print("\n[Phase 5] Testing CLI root and subcommands help invocation...")
    cli_passed, cli_logs = check_cli_subcommands()
    for l in cli_logs:
        print(f"  {l}")

    total_duration = time.perf_counter() - total_start
    all_ok = all([req_passed, import_passed, cfg_passed, prompt_passed, cli_passed])

    print("\n" + "=" * 70)
    if all_ok:
        print(f"🎉 ALL SMOKE TESTS PASSED! Total Elapsed Time: {format_duration(total_duration)}")
    else:
        print(f"💥 SMOKE TESTS FAILED! Total Elapsed Time: {format_duration(total_duration)}")
    print("=" * 70)

    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(run_smoke_test())
