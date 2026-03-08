"""
game/sound_manager.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SoundManager — จัดการระบบเสียงทั้งหมดในเกม
  - เล่น BGM (Looped) และ SFX
  - ควบคุมระดับเสียง (Volume) แยกตามประเภท (Music vs SFX)
  - จัดการการเปลี่ยนเพลง (Transitions) เช่น In-Game -> Boss Fight
"""
from kivy.core.audio import SoundLoader
from game.game_settings import settings
import os

class SoundManager:
    _instance = None

    # --- Assets Mapping ---
    BGM_PATHS = {
        "main_menu": "assets/sound/mainmenu/nothing-like-home-luminbird-main-version-36601-02-03.mp3",
        "ingame":    "assets/sound/ingame/dodgin-bullets-bosnow-main-version-45830-02-32.mp3",
        "bossfight": "assets/sound/bossfight/speed-demon-abbynoise-main-version-18766-02-24.mp3",
        "rain":      "assets/sound/mainmenu/rain.wav",
    }

    SFX_PATHS = {
        "attack": "assets/sound/attack/ninja-star-throw-joshua-chivers-1-00-00.mp3",
        "enemy_hit": "assets/sound/attack/bullet-impacting-body-gamemaster-audio-2-2-00-00.mp3",
        "button": "assets/sound/button/computer-mouse-click-joshua-chivers-1-00-00.mp3",
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

        self.current_bgm = None
        self.current_bgm_name = None
        
        self.current_ambient = None
        self.current_ambient_name = None
        self.ambient_volume_factor = 1.0
        
        # Cache loaded sounds to avoid reloading
        self._sfx_cache = {}
        self._bgm_cache = {}

    def play_bgm(self, name, loop=True):
        """เล่นเพลงประกอบพื้นหลัง (BGM) แบบวนลูป"""
        if self.current_bgm_name == name:
            return

        # Stop previous BGM
        if self.current_bgm:
            self.current_bgm.stop()

        path = self.BGM_PATHS.get(name)
        if not path or not os.path.exists(path):
            print(f"[SoundManager] BGM not found: {name} at {path}")
            return

        # Load from cache or file
        if name not in self._bgm_cache:
            sound = SoundLoader.load(path)
            if sound:
                self._bgm_cache[name] = sound
            else:
                print(f"[SoundManager] Failed to load BGM: {name}")
                return
        
        self.current_bgm = self._bgm_cache[name]
        self.current_bgm_name = name
        self.current_bgm.loop = loop
        self.current_bgm.volume = settings.music_volume
        self.current_bgm.play()
        print(f"[SoundManager] Playing BGM: {name} (Volume: {settings.music_volume})")

    def stop_bgm(self):
        """หยุดเพลงประกอบทั้งหมด"""
        if self.current_bgm:
            self.current_bgm.stop()
            self.current_bgm = None
            self.current_bgm_name = None

    def play_ambient(self, name, loop=True, volume_factor=0.3):
        """เล่นเสียง Ambient (เช่น เสียงฝน) แยกจากช่อง BGM หลัก"""
        if self.current_ambient_name == name:
            return

        if self.current_ambient:
            self.current_ambient.stop()

        path = self.BGM_PATHS.get(name)
        if not path or not os.path.exists(path):
            return

        if name not in self._bgm_cache:
            sound = SoundLoader.load(path)
            if sound: self._bgm_cache[name] = sound
            else: return
        
        self.current_ambient = self._bgm_cache[name]
        self.current_ambient_name = name
        self.ambient_volume_factor = volume_factor
        self.current_ambient.loop = loop
        self.current_ambient.volume = settings.music_volume * volume_factor
        self.current_ambient.play()

    def stop_ambient(self):
        if self.current_ambient:
            self.current_ambient.stop()
            self.current_ambient = None
            self.current_ambient_name = None

    def update_music_volume(self):
        """อัปเดตความดังของเพลงที่กำลังเล่นอยู่ทันที"""
        if self.current_bgm:
            self.current_bgm.volume = settings.music_volume
        if self.current_ambient:
            self.current_ambient.volume = settings.music_volume * self.ambient_volume_factor

    def play_sfx(self, name, volume=None):
        """เล่นเสียงเอฟเฟกต์ (SFX) หนึ่งครั้ง"""
        path = self.SFX_PATHS.get(name)
        if not path or not os.path.exists(path):
            return

        # Load from cache or file
        if name not in self._sfx_cache:
            sound = SoundLoader.load(path)
            if sound:
                self._sfx_cache[name] = sound
            else:
                print(f"[SoundManager] Failed to load SFX: {name}")
                return

        sfx = self._sfx_cache[name]
        sfx.volume = volume if volume is not None else settings.sfx_volume
        sfx.play()

# --- Global Instance ---
sound_manager = SoundManager()
