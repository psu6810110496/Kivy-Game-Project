from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from game.player import PlayerStats
import kivy.app

class CharacterSelectScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.char_data = {
            "Survivor": PlayerStats("Survivor", 100, 5, 10),
            "Scavenger": PlayerStats("Scavenger", 70, 10, 5),
            "Veteran": PlayerStats("Veteran", 200, 2, 15)
        }
        layout = BoxLayout(orientation='vertical', padding=50)
        layout.add_widget(Label(text="SELECT CHARACTER", font_size=30))
        
        chars = BoxLayout(spacing=20)
        for name, stats in self.char_data.items():
            btn = Button(text=f"{name}\nHP: {stats.hp}")
            btn.bind(on_press=lambda inst, s=stats: self.select_char(s))
            chars.add_widget(btn)
            
        layout.add_widget(chars)
        self.add_widget(layout)

    def select_char(self, stats):
        kivy.app.App.get_running_app().current_player = stats
        self.manager.current = 'game_screen'