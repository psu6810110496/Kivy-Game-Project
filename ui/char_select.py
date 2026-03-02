from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from game.player import PlayerStats
import kivy.app


class CharacterSelectScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.char_data = {
            "Survivor": PlayerStats("Survivor", 100, 5, 10),
            "Scavenger": PlayerStats("Scavenger", 70, 10, 5),
            "Veteran": PlayerStats("Veteran", 200, 2, 15),
        }

        # พื้นหลังสีเข้ม
        with self.canvas.before:
            Color(0.05, 0.05, 0.08, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_bg, size=self.update_bg)

        layout = BoxLayout(orientation="vertical", padding=50, spacing=30)

        title = Label(
            text="SELECT YOUR OPERATIVE",
            font_size=40,
            bold=True,
            color=(1, 0.8, 0.2, 1),
            size_hint=(1, 0.2),
        )
        layout.add_widget(title)

        chars_layout = BoxLayout(spacing=20, size_hint=(1, 0.6))
        for name, stats in self.char_data.items():
            # ทำปุ่มให้เหมือนการ์ด
            btn = Button(
                text=f"{name.upper()}\n\nHP: {stats.hp}\nATK: {stats.damage}\nSPD: {stats.speed}",
                font_size=20,
                bold=True,
                halign="center",
                background_normal="",
                background_color=(0.15, 0.15, 0.15, 1),  # สีเทาเข้ม
                color=(0.9, 0.9, 0.9, 1),
            )
            btn.bind(on_press=lambda inst, s=stats: self.select_char(s))
            chars_layout.add_widget(btn)

        layout.add_widget(chars_layout)

        # ปุ่มกลับเมนู
        btn_back = Button(
            text="BACK",
            size_hint=(0.2, 0.1),
            pos_hint={"center_x": 0.5},
            background_normal="",
            background_color=(0.3, 0.1, 0.1, 1),
        )
        btn_back.bind(on_press=lambda x: setattr(self.manager, "current", "main_menu"))
        layout.add_widget(btn_back)

        self.add_widget(layout)

    def update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

    def select_char(self, stats):
        kivy.app.App.get_running_app().current_player = stats
        self.manager.current = "game_screen"
