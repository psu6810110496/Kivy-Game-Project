from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, NoTransition
from kivy.core.window import Window
from ui.main_menu import MainMenuScreen
from ui.char_select import CharacterSelectScreen
from game.engine import GameScreen
from ui.credits import CreditsScreen
from ui.settings import SettingsScreen
from kivy.config import Config

# ตั้งค่าการปรับขนาดหน้าจอ
Config.set("graphics", "resizable", "1")
Config.set("graphics", "multisamples", "1")
Config.set("graphics", "width", "1280")
Config.set("graphics", "height", "720")
Config.set("input", "mouse", "mouse,disable_multitouch")

class Apocalite(App):
    def build(self):
        Window.bind(on_key_down=self._on_keyboard_down)
        
        self.current_player = None
        sm = ScreenManager(transition=NoTransition())
        sm.add_widget(MainMenuScreen(name="main_menu"))
        sm.add_widget(CharacterSelectScreen(name="char_select_screen"))
        sm.add_widget(GameScreen(name="game_screen"))
        sm.add_widget(CreditsScreen(name="credits_screen"))
        sm.add_widget(SettingsScreen(name="settings_screen"))
        return sm

    def _on_keyboard_down(self, window, key, scancode, codepoint, modifiers):
        if key == 292: # F11
            if Window.fullscreen:
                Window.fullscreen = False
            else:
                Window.fullscreen = 'auto'
            return True
        return False
if __name__ == "__main__":
    Apocalite().run()