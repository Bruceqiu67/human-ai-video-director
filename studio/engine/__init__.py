"""Visual rendering, subtitle generation, and stop-motion composition engine."""
from studio.engine.renderer import SceneRenderer
from studio.engine.subtitles import AdaptiveCapsuleSubtitle
from studio.engine.stopmotion import StopMotionSequencer
from studio.engine.transitions import PageFlipTransition
from studio.engine.camera import KenBurnsZoom

# Ergonomic aliases
SubtitleGenerator = AdaptiveCapsuleSubtitle
FrameSequencer = StopMotionSequencer
TransitionFX = PageFlipTransition
CameraMovement = KenBurnsZoom

__all__ = [
    "SceneRenderer",
    "AdaptiveCapsuleSubtitle",
    "StopMotionSequencer",
    "PageFlipTransition",
    "KenBurnsZoom",
    "SubtitleGenerator",
    "FrameSequencer",
    "TransitionFX",
    "CameraMovement",
]
