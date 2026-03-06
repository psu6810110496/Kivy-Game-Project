"""
game/game_settings.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Singleton สำหรับเก็บ settings ทั้งหมดในเกม
  - Volume (BGM, SFX)
  - Key Bindings
  - Display Settings (Fullscreen, Camera Shake)
  - Gameplay Settings
"""
import json
import os


class GameSettings:
    """Singleton เก็บ settings ทั้งหมด"""

    _instance = None
    SETTINGS_FILE = "apocalite_settings.json"

    # --- Default Key Bindings ---
    DEFAULT_KEYS = {
        "move_up":    "w",
        "move_down":  "s",
        "move_left":  "a",
        "move_right": "d",
        "dash":       "space",
        "skill1":     "q",
        "skill2":     "e",
        "skill3":     "lmb",   # Left Mouse Button
        "pause":      "escape",
    }

    KEY_DISPLAY_NAMES = {
        "move_up":    "เดินขึ้น (Move Up)",
        "move_down":  "เดินลง (Move Down)",
        "move_left":  "เดินซ้าย (Move Left)",
        "move_right": "เดินขวา (Move Right)",
        "dash":       "แดช (Dash)",
        "skill1":     "สกิล 1 (Skill 1)",
        "skill2":     "สกิล 2 (Skill 2)",
        "skill3":     "สกิล 3 (Skill 3 - S3)",
        "pause":      "พัก (Pause)",
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # --- Volume (0.0 – 1.0) ---
        self.music_volume: float = 0.5
        self.sfx_volume: float = 0.8

        # --- Display ---
        self.fullscreen: bool = False
        self.camera_shake: bool = True
        self.show_damage_numbers: bool = True
        self.show_enemy_hp: bool = False
        self.health_drop_rate: float = 0.12

        # --- Gameplay ---
        self.screen_shake_intensity: float = 1.0

        # --- Key Bindings ---
        self.key_bindings: dict = dict(self.DEFAULT_KEYS)

        self.load()

    # ─── Save / Load ─────────────────────────────
    def save(self):
        data = {
            "music_volume": self.music_volume,
            "sfx_volume": self.sfx_volume,
            "fullscreen": self.fullscreen,
            "camera_shake": self.camera_shake,
            "show_damage_numbers": self.show_damage_numbers,
            "show_enemy_hp": self.show_enemy_hp,
            "health_drop_rate": self.health_drop_rate,
            "screen_shake_intensity": self.screen_shake_intensity,
            "key_bindings": self.key_bindings,
        }
        try:
            with open(self.SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Settings] Save failed: {e}")

    def load(self):
        if not os.path.exists(self.SETTINGS_FILE):
            return
        try:
            with open(self.SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.music_volume = float(data.get("music_volume", self.music_volume))
            self.sfx_volume = float(data.get("sfx_volume", self.sfx_volume))
            self.fullscreen = bool(data.get("fullscreen", self.fullscreen))
            self.camera_shake = bool(data.get("camera_shake", self.camera_shake))
            self.show_damage_numbers = bool(data.get("show_damage_numbers", self.show_damage_numbers))
            self.show_enemy_hp = bool(data.get("show_enemy_hp", self.show_enemy_hp))
            self.health_drop_rate = float(data.get("health_drop_rate", self.health_drop_rate))
            self.screen_shake_intensity = float(data.get("screen_shake_intensity", self.screen_shake_intensity))
            loaded_keys = data.get("key_bindings", {})
            for k, v in loaded_keys.items():
                if k in self.key_bindings:
                    self.key_bindings[k] = v
        except Exception as e:
            print(f"[Settings] Load failed: {e}")

    def reset_keys(self):
        """Reset key bindings to default"""
        self.key_bindings = dict(self.DEFAULT_KEYS)
        self.save()


# --- Global Instance ---
settings = GameSettings()
