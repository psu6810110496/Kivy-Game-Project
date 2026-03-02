from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Rectangle, Color
from kivy.core.window import Window
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

        # ใส่พื้นหลังสีเทาเข้มอมฟ้า
        with self.canvas.before:
            Color(0.05, 0.08, 0.1, 1)
            self.bg = Rectangle(pos=self.pos, size=Window.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        layout = BoxLayout(orientation="vertical", padding=50, spacing=30)

        # หัวข้อมีขอบดำ
        layout.add_widget(
            Label(
                text="SELECT CHARACTER",
                font_size=40,
                bold=True,
                color=(0.9, 0.95, 1, 1),
                outline_width=2,
                outline_color=(0, 0, 0, 1),
                size_hint=(1, 0.2),
            )
        )

        chars = BoxLayout(spacing=20, size_hint=(1, 0.8))
        for name, stats in self.char_data.items():
            # ปรับปุ่มให้เป็นธีมกระจกโปร่งแสงและแสดง Status ชัดเจน
            btn = Button(
                text=f"{name}\n\nHP: {stats.hp}\nATK: {stats.damage}\nSPD: {stats.speed}",
                font_size=20,
                bold=True,
                halign="center",
                background_normal="",
                background_color=(0.1, 0.15, 0.2, 0.85),
                color=(0.8, 0.9, 1, 1),
            )
            btn.bind(on_press=lambda inst, s=stats: self.select_char(s))
            chars.add_widget(btn)

        layout.add_widget(chars)
        self.add_widget(layout)

    def _update_bg(self, instance, value):
        self.bg.pos = instance.pos
        self.bg.size = instance.size

    def select_char(self, stats):
        kivy.app.App.get_running_app().current_player = stats
        self.manager.current = "game_screen"
