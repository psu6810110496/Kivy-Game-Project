import os
import sys

# บังคับให้ Working Directory อยู่ที่โฟลเดอร์นอกสุด (Kivy-Game-Project) เสมอ
# เพื่อให้โหลด assets/ ได้ถูกต้องไม่ว่าจะรันจากโฟลเดอร์ไหน
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if os.path.basename(project_root) == "Kivy-Game-Project" or os.path.exists(os.path.join(project_root, 'assets')):
    os.chdir(project_root)
    # เพิ่ม APOCALITE ลงใน sys.path เผื่อ import ภายในหาไม่เจอ
    sys.path.insert(0, os.path.join(project_root, 'APOCALITE'))

from kivy.config import Config

# ตั้งค่าการปรับขนาดหน้าจอ
Config.set("graphics", "resizable", "1")
Config.set("graphics", "multisamples", "0") # ลดภาระ GPU
Config.set("graphics", "width", "1280")
Config.set("graphics", "height", "720")
Config.set("graphics", "maxfps", "60") # ล็อก FPS เพื่อความนิ่ง
Config.set("graphics", "vsync", "1")   # เปิด VSync ลดการฉีกขาดของภาพ
Config.set("input", "mouse", "mouse,disable_multitouch")

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, NoTransition
from kivy.core.window import Window
from ui.main_menu import MainMenuScreen
from ui.char_select import CharacterSelectScreen
from game.engine import GameScreen
from ui.credits import CreditsScreen
from ui.settings import SettingsScreen
from ui.leaderboard import LeaderboardScreen
from ui.how_to_play import HowToPlayScreen

class Apocalite(App):
    def build(self):
        Window.show_cursor = True
        Window.bind(on_key_down=self._on_keyboard_down)
        
        self.current_player = None
        sm = ScreenManager(transition=NoTransition())
        sm.add_widget(MainMenuScreen(name="main_menu"))
        sm.add_widget(CharacterSelectScreen(name="char_select_screen"))
        sm.add_widget(GameScreen(name="game_screen"))
        sm.add_widget(CreditsScreen(name="credits_screen"))
        sm.add_widget(SettingsScreen(name="settings_screen"))
        sm.add_widget(LeaderboardScreen(name="leaderboard_screen"))
        sm.add_widget(HowToPlayScreen(name="how_to_play_screen"))
        return sm

    def _on_keyboard_down(self, window, key, scancode, codepoint, modifiers):
        if key == 292: # F11
            if Window.fullscreen:
                Window.fullscreen = False
            else:
                Window.fullscreen = 'auto'
            # Force cursor visibility after toggle
            Window.show_cursor = True
            return True
        return False
if __name__ == "__main__":
    Apocalite().run()