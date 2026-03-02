from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from ui.main_menu import MainMenuScreen
from ui.char_select import CharacterSelectScreen
from game.engine import GameScreen
from kivy.config import Config

Config.set("input", "mouse", "mouse,disable_multitouch")
Config.set("graphics", "fullscreen", "0")
Config.set("graphics", "resizable", "0")
Config.set("graphics", "width", "1280")
Config.set("graphics", "height", "720")

class VampireApp(App):
    def build(self):
        self.current_player = None
        sm = ScreenManager()
        sm.add_widget(MainMenuScreen(name="main_menu"))
        sm.add_widget(CharacterSelectScreen(name="char_select_screen"))
        sm.add_widget(GameScreen(name="game_screen"))
        return sm

if __name__ == "__main__":
    VampireApp().run()
