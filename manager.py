"""
Santa's Countdown for LEDMatrix

An animated countdown to Christmas for kids: Santa's sleigh and reindeer,
a waving snowman, bouncing presents, dancing gingerbread men, chasing
lights, Santa kicking his legs in a chimney, elves throwing presents and
elves building one in their workshop. A different scene each time
the plugin comes round.

- Normal rotation: display() is called repeatedly and animates at
  animation_fps.
- Vegas scroll: the card is one live element. The ticker carries it across
  the panel (so the sleigh flies the length of the wall) and redraws it in
  place about once a second -- legs gallop, Rudolph's nose blinks, snow
  falls, lights chase. The ticker caps that rate (1 Hz on a display with the
  stock rgbmatrix binding).

All art is drawn in code (santa_scenes.py). No network, no files.
"""

import random
import time
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from src.plugin_system.base_plugin import BasePlugin

from santa_scenes import ELF_SCENES, SCENES, render

try:  # core 3.8.0+
    from src.plugin_system.vegas_elements import VegasElement
except ImportError:  # older cores: get_vegas_content() still works
    VegasElement = None

SCENE_NAMES = list(SCENES)
#: In normal rotation, a display() call this long after the previous one is a
#: new turn even without force_clear.
ROUND_GAP_S = 30.0
#: In Vegas, a fetch at least this long after the current scene was first
#: handed out starts the next scene. The ticker fetches once per round (and
#: again after each update(), every update_interval); a round is never shorter
#: than the card takes to cross the panel, about 10 s for a 256px card at the
#: usual speed, so even a wall showing nothing else changes scene every round.
SCENE_MIN_S = 6.0


def _season_start(raw: Any) -> tuple:
    try:
        month, day = (int(p) for p in str(raw).split("-"))
        date(2000, month, day)
        return month, day
    except (TypeError, ValueError):
        return 11, 1


class SantaCountdownPlugin(BasePlugin):

    def __init__(self, plugin_id: str, config: Dict[str, Any],
                 display_manager, cache_manager, plugin_manager):
        super().__init__(plugin_id, config, display_manager, cache_manager, plugin_manager)
        self._apply_config(config)
        self._turn = -1
        self._scene = self.scenes[0]
        self._scene_since = float("-inf")
        self._last_display = float("-inf")
        self._started = time.monotonic()
        self.days = self._days_until_christmas()

    # ── settings ──────────────────────────────────────────────────────────
    def _apply_config(self, config: Dict[str, Any]) -> None:
        chosen = [s for s in (config.get("scenes") or SCENE_NAMES) if s in SCENES]
        self.scenes: List[str] = chosen or SCENE_NAMES
        self.order = config.get("order", "in_turn")
        self.season = _season_start(config.get("season_start", "11-01"))
        try:
            self.fps = max(1.0, min(30.0, float(config.get("animation_fps", 6))))
        except (TypeError, ValueError):
            self.fps = 6.0
        try:
            self.vegas_hz = max(0.2, min(30.0, float(config.get("vegas_animation_hz", 1))))
        except (TypeError, ValueError):
            self.vegas_hz = 1.0

    def on_config_change(self, new_config: Dict[str, Any]) -> None:
        super().on_config_change(new_config)
        self._apply_config(new_config)
        if self._scene not in self.scenes:
            self._scene = self.scenes[0]

    # ── the date ──────────────────────────────────────────────────────────
    def _today(self) -> date:
        tz_name = None
        for owner in (self.plugin_manager, self.cache_manager):
            cm = getattr(owner, "config_manager", None)
            if cm is not None:
                try:
                    tz_name = cm.get_timezone()
                    break
                except Exception:  # pylint: disable=broad-except
                    pass
        if tz_name:
            try:
                from zoneinfo import ZoneInfo
                return datetime.now(ZoneInfo(tz_name)).date()
            except Exception:  # pylint: disable=broad-except
                pass
        return date.today()

    def _days_until_christmas(self) -> int:
        today = self._today()
        xmas = date(today.year, 12, 25)
        if today > xmas:
            xmas = date(today.year + 1, 12, 25)
        return (xmas - today).days

    def in_season(self) -> bool:
        """From season_start through Christmas Day."""
        today = self._today()
        start = date(today.year, *self.season)
        return start <= today <= date(today.year, 12, 25)

    def update(self) -> None:
        self.days = self._days_until_christmas()

    # ── which scene ───────────────────────────────────────────────────────
    def _next_scene(self) -> str:
        self._turn += 1
        if self.order == "random" and len(self.scenes) > 1:
            choices = [s for s in self.scenes if s != self._scene]
            if self._scene in ELF_SCENES:
                # never one elf card straight after the other
                choices = [s for s in choices if s not in ELF_SCENES] or choices
            self._scene = random.choice(choices)
        else:
            self._scene = self.scenes[self._turn % len(self.scenes)]
        return self._scene

    def _phase(self, at: float, rate: float) -> int:
        return int((at - self._started) * rate)

    # ── normal rotation ───────────────────────────────────────────────────
    def display(self, force_clear: bool = False) -> None:
        now = time.monotonic()
        if force_clear or now - self._last_display > ROUND_GAP_S:
            self._next_scene()
        self._last_display = now
        dm = self.display_manager
        if not self.in_season():
            dm.clear()
            dm.update_display()
            return
        frame = render(self._scene, self._days_until_christmas(),
                       self._phase(now, self.fps), dm.width, dm.height)
        dm.image.paste(frame, (0, 0))
        dm.update_display()

    def get_display_duration(self) -> float:
        try:
            return float(self.config.get("display_duration", 15))
        except (TypeError, ValueError):
            return 15.0

    # ── Vegas ─────────────────────────────────────────────────────────────
    def _vegas_turn(self, now: float) -> None:
        if now - self._scene_since >= SCENE_MIN_S:
            self._next_scene()
            self._scene_since = now
            self.logger.debug("Vegas turn %d: %s", self._turn, self._scene)

    def _vegas_frame(self, scene: str, at: float, width: int, height: int):
        return render(scene, self.days, self._phase(at, self.vegas_hz), width, height)

    def get_vegas_elements(self) -> Optional[List[Any]]:
        if VegasElement is None:
            return None
        if not self.in_season():
            return []
        now = time.monotonic()
        self._vegas_turn(now)
        dm = self.display_manager
        key = "santa:%s:%d" % (self._scene, self._turn)
        return [VegasElement(key=key,
                             image=self._vegas_frame(self._scene, now, dm.width, dm.height),
                             version=(key, self.days, self._phase(now, self.vegas_hz)),
                             live=True, refresh_hz=self.vegas_hz)]

    def redraw_vegas_element(self, key: str, width: int, height: int, at: float):
        # Lock-free: reads only self.days (replaced whole by update()) and the
        # scene name in the key.
        parts = key.split(":")
        if len(parts) != 3 or parts[1] not in SCENES:
            return None
        return self._vegas_frame(parts[1], at, width, height)

    def get_vegas_content(self):
        """For cores without live elements: one still frame."""
        if not self.in_season():
            return None
        now = time.monotonic()
        self._vegas_turn(now)
        dm = self.display_manager
        return [self._vegas_frame(self._scene, now, dm.width, dm.height)]

    # ── housekeeping ──────────────────────────────────────────────────────
    def validate_config(self) -> bool:
        if not super().validate_config():
            return False
        bad = [s for s in (self.config.get("scenes") or []) if s not in SCENES]
        if bad:
            self.logger.warning("Unknown scenes ignored: %s", ", ".join(bad))
        return True

    def get_info(self) -> Dict[str, Any]:
        info = super().get_info()
        info.update({"days_until_christmas": self.days, "scene": self._scene,
                     "scenes": self.scenes, "in_season": self.in_season()})
        return info
