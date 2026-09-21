#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Package the human-ai-video-director skill into a clean, self-contained zip distribution.
Excludes heavyweight test video assets, build caches, and private workspace logs.
"""

import os
import sys
import zipfile

# Ensure safe printing on Windows consoles
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

TARGET_ZIP = "human-ai-video-director.zip"
PREFIX = "human-ai-video-director"

ROOT_FILES = [
    "SKILL.md",
    "README.md",
    "LICENSE",
    "requirements.txt",
    "AI_VIDEO_PRODUCTION_SOP.md",
    "UNIVERSAL_AI_VIDEO_BATCH_SOP.md",
    "LESSONS_LEARNED_AND_RED_LINES.md",
    "PROJECT_KNOWLEDGE_GRAPH.md",
]

INCLUDE_DIRS = ["studio", "templates", "docs"]


def build_package(target_path: str = TARGET_ZIP, root_dir: str = "."):
    print(f"📦 Packaging skill into: {os.path.abspath(target_path)}")

    with zipfile.ZipFile(target_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        # 1. Package root markdown & configuration files
        for rf in ROOT_FILES:
            fp = os.path.join(root_dir, rf)
            if os.path.exists(fp):
                arc = f"{PREFIX}/{rf}".replace("\\", "/")
                z.write(fp, arc)
                print(f"  + {rf} -> {arc}")

        # 2. Package .gemini skill path for backward compatibility
        gemini_skill = os.path.join(root_dir, ".gemini", "skills", "human-ai-video-director", "SKILL.md")
        if os.path.exists(gemini_skill):
            arc = f"{PREFIX}/.gemini/skills/human-ai-video-director/SKILL.md"
            z.write(gemini_skill, arc)
            print(f"  + .gemini/skills/... -> {arc}")

        # 3. Package core modules (studio, templates, docs)
        for d in INCLUDE_DIRS:
            dp = os.path.join(root_dir, d)
            if not os.path.exists(dp):
                continue
            for root, dirs, files in os.walk(dp):
                # Filter out cache and transient directories
                dirs[:] = [sub for sub in dirs if sub not in ("__pycache__", ".pytest_cache")]
                for f in files:
                    if f.endswith((".pyc", ".pyo", ".DS_Store", "Thumbs.db")):
                        continue
                    fp = os.path.join(root, f)
                    rel = os.path.relpath(fp, root_dir).replace("\\", "/")
                    arc = f"{PREFIX}/{rel}"
                    z.write(fp, arc)

        # 4. Package clean example templates (excluding heavy video/audio binaries)
        examples_dir = os.path.join(root_dir, "examples")
        if os.path.exists(examples_dir):
            for root, dirs, files in os.walk(examples_dir):
                dirs[:] = [sub for sub in dirs if sub not in ("assets", "audio", "output")]
                for f in files:
                    if f.endswith((".yaml", ".yml", ".md", ".txt")):
                        fp = os.path.join(root, f)
                        rel = os.path.relpath(fp, root_dir).replace("\\", "/")
                        arc = f"{PREFIX}/{rel}"
                        z.write(fp, arc)

    # Verification
    size_bytes = os.path.getsize(target_path)
    size_mb = size_bytes / (1024 * 1024)

    with zipfile.ZipFile(target_path, "r") as z:
        corrupted = z.testzip()
        if corrupted is not None:
            raise RuntimeError(f"Corrupted file in zip: {corrupted}")
        count = len(z.namelist())

    print(f"✅ Packaging complete: {count} entries, {size_mb:.2f} MB ({size_bytes:,} bytes)")
    print(f"   Integrity check: 100% Passed.")


if __name__ == "__main__":
    build_package()
