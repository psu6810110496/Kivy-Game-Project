from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
import kivy.app


class LevelUpPopup(Popup):
    def __init__(self, game_screen, **kwargs):
        super().__init__(**kwargs)
        self.game_screen = game_screen
        self.title = "LEVEL UP! Choose your Upgrade:"
        self.size_hint = (0.6, 0.5)
        self.auto_dismiss = False

        layout = BoxLayout(orientation="vertical", padding=20, spacing=20)
        cards_layout = GridLayout(cols=3, spacing=15)

        upgrades = ["+ Damage", "+ Max HP", "+ Speed"]

        for upg in upgrades:
            btn = Button(text=upg, font_size=20)
            btn.bind(on_press=self.apply_upgrade)
            cards_layout.add_widget(btn)

        layout.add_widget(cards_layout)
        self.content = layout

    def apply_upgrade(self, instance):
        player = kivy.app.App.get_running_app().current_player
        if player:
            if "+ Damage" in instance.text:
                player.damage += 5
            elif "+ Max HP" in instance.text:
                player.hp += 20
            elif "+ Speed" in instance.text:
                player.speed += 2

        self.game_screen.resume_game()
        self.dismiss()


class PausePopup(Popup):
    def __init__(self, game_screen, **kwargs):
        super().__init__(**kwargs)
        self.game_screen = game_screen
        self.title = "GAME PAUSED"
        self.size_hint = (0.4, 0.4)
        self.auto_dismiss = False

        layout = BoxLayout(orientation="vertical", padding=20, spacing=15)
        btn_resume = Button(text="RESUME", size_hint=(1, 0.5))
        btn_menu = Button(text="RETURN TO MENU", size_hint=(1, 0.5))

        btn_resume.bind(on_press=lambda x: self.resume())
        btn_menu.bind(on_press=lambda x: self.go_to_menu())

        layout.add_widget(btn_resume)
        layout.add_widget(btn_menu)
        self.content = layout

    def resume(self):
        self.game_screen.resume_game()
        self.dismiss()

    def go_to_menu(self):
        self.dismiss()
        self.game_screen.manager.current = "main_menu"
