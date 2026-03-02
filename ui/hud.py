from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.button import Button
from kivy.clock import Clock
import kivy.app
from ui.level_up import LevelUpPopup


class HUD(FloatLayout):
    def __init__(self, game_screen, **kwargs):
        super().__init__(**kwargs)
        self.game_screen = game_screen

        top_ui = BoxLayout(
            size_hint=(0.8, 0.05), pos_hint={"center_x": 0.5, "top": 0.98}, spacing=15
        )

        self.lbl_level = Label(
            text="LV : 1",
            size_hint=(0.15, 1),
            font_size=20,
            bold=True,
            color=(0.9, 0.95, 1, 1),
            outline_width=2,
            outline_color=(0, 0, 0, 1),
        )
        self.exp_bar = ProgressBar(max=100, value=0, size_hint=(0.85, 1))

        top_ui.add_widget(self.lbl_level)
        top_ui.add_widget(self.exp_bar)
        self.add_widget(top_ui)

        btn_pause = Button(
            text="||",
            font_size=24,
            bold=True,
            size_hint=(None, None),
            size=(50, 50),
            pos_hint={"right": 0.98, "top": 0.98},
            background_normal="",
            background_color=(0.1, 0.15, 0.2, 0.85),
            color=(0.9, 0.95, 1, 1),
        )
        btn_pause.bind(on_press=self.game_screen.pause_game)
        self.add_widget(btn_pause)

        btn_test_lvl = Button(
            text="TEST\nLVL UP",
            font_size=14,
            bold=True,
            halign="center",
            size_hint=(None, None),
            size=(80, 50),
            pos_hint={"right": 0.98, "top": 0.88},
            background_normal="",
            background_color=(0.3, 0.1, 0.1, 0.85),
            color=(1, 1, 1, 1),
        )
        btn_test_lvl.bind(on_press=self.test_level_up)
        self.add_widget(btn_test_lvl)

        btn_add_exp = Button(
            text="ADD\nEXP +20",
            font_size=14,
            bold=True,
            halign="center",
            size_hint=(None, None),
            size=(80, 50),
            pos_hint={"right": 0.98, "top": 0.78},
            background_normal="",
            background_color=(0.1, 0.3, 0.3, 0.85),
            color=(1, 1, 1, 1),
        )
        btn_add_exp.bind(on_press=self.test_add_exp)
        self.add_widget(btn_add_exp)

    def test_level_up(self, instance):
        if hasattr(self.game_screen, "is_paused"):
            self.game_screen.is_paused = True
        popup = LevelUpPopup(self.game_screen)
        popup.open()

    def test_add_exp(self, instance):
        player = kivy.app.App.get_running_app().current_player
        if player:
            player.exp += 20
            if player.exp >= 100:
                player.exp -= 100
                player.level += 1
                if hasattr(self.game_screen, "is_paused"):
                    self.game_screen.is_paused = True
                popup = LevelUpPopup(self.game_screen)
                popup.open()
            self.update_ui(player)

    def update_ui(self, stats):
        self.lbl_level.text = f"LV : {stats.level}"
        self.exp_bar.value = stats.exp


class CountdownOverlay(Label):
    def __init__(self, callback, **kwargs):
        super().__init__(**kwargs)
        self.callback = callback
        self.count = 3
        self.text = "3"
        self.font_size = 200
        self.bold = True
        self.color = (0.9, 0.95, 1, 1)
        self.outline_width = 4
        self.outline_color = (0, 0, 0, 1)
        self.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        Clock.schedule_interval(self.update_countdown, 1)

    def update_countdown(self, dt):
        self.count -= 1
        if self.count > 0:
            self.text = str(self.count)
        elif self.count == 0:
            self.text = "S U R V I V E !"
            self.font_size = 120
            self.color = (0.8, 0.2, 0.2, 1)
        else:
            self.callback()
            self.parent.remove_widget(self)
            return False
