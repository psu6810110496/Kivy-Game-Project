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
        self.title_font_size = 22

        # ปรับพื้นหลัง Popup ให้มืดลง
        self.background = ""
        self.background_color = (0.05, 0.08, 0.1, 0.95)
        self.separator_color = (0.3, 0.5, 0.6, 1)  # เส้นขีดใต้ Title

        self.size_hint = (0.6, 0.5)
        self.auto_dismiss = False

        layout = BoxLayout(orientation="vertical", padding=20, spacing=20)
        cards_layout = GridLayout(cols=3, spacing=15)

        # รายการอัปเกรด
        upgrades = ["+ Damage", "+ Max HP", "+ Speed"]

        for upg in upgrades:
            btn = Button(
                text=upg,
                font_size=20,
                bold=True,
                background_normal="",
                background_color=(0.1, 0.15, 0.2, 0.9),
                color=(0.8, 0.9, 1, 1),
            )
            btn.bind(on_press=self.apply_upgrade)
            cards_layout.add_widget(btn)

        layout.add_widget(cards_layout)
        self.content = layout

    def apply_upgrade(self, instance):
        # รับค่าผู้เล่นจาก App
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
        self.title_font_size = 24

        self.background = ""
        self.background_color = (0.05, 0.08, 0.1, 0.95)
        self.separator_color = (0.3, 0.5, 0.6, 1)

        self.size_hint = (0.4, 0.4)
        self.auto_dismiss = False

        layout = BoxLayout(orientation="vertical", padding=20, spacing=15)
        btn_resume = Button(
            text="RESUME",
            font_size=20,
            bold=True,
            size_hint=(1, 0.5),
            background_normal="",
            background_color=(0.1, 0.2, 0.15, 0.9),  # สีเขียวหม่น
        )
        btn_menu = Button(
            text="RETURN TO MENU",
            font_size=20,
            bold=True,
            size_hint=(1, 0.5),
            background_normal="",
            background_color=(0.2, 0.1, 0.1, 0.9),  # สีแดงหม่น
        )

        btn_resume.bind(on_press=lambda x: self.resume())
        btn_menu.bind(on_press=lambda x: self.go_to_menu())

        layout.add_widget(btn_resume)
        layout.add_widget(btn_menu)
        self.content = layout

    def resume(self):
        self.game_screen.resume_game()
        self.dismiss()

    def go_to_menu(self):
        self.game_screen.resume_game()
        self.dismiss()
