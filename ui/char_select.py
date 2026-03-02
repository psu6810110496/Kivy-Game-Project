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

        # 1. ใช้ข้อมูลตัวละครใหม่ของเรา (PTae, Lostman, Monke)
        self.char_data = {
            "PTae": PlayerStats(
                name="PTae",
                hp=150,
                speed=3.5,
                damage=14,
                idle_frames=[
                    "assets/PTae/PTIdle/PTTG1.png",
                    "assets/PTae/PTIdle/PTTG2.png",
                ],
                walk_frames=[
                    "assets/PTae/PTPushUp/PTaeTester1.png",
                    "assets/PTae/PTPushUp/PTaeTester2.png",
                    "assets/PTae/PTPushUp/PTaeTester3.png",
                    "assets/PTae/PTPushUp/PTaeTester4.png",
                ],
            ),
            "Lostman": PlayerStats(
                name="Lostman",
                hp=100,
                speed=5.0,
                damage=17,
                idle_frames=[
                    "assets/Lostman/idle/idleman1.png",
                    "assets/Lostman/idle/idleman2.png",
                ],
                walk_frames=[
                    "assets/Lostman/walk/walk1.png",
                    "assets/Lostman/walk/walk2.png",
                    "assets/Lostman/walk/walk3.png",
                    "assets/Lostman/walk/walk4.png",
                ],
            ),
            "Monke": PlayerStats(
                name="Monke",
                hp=90,
                speed=7.0,
                damage=12,
                idle_frames=[
                    "assets/Monkey/IdleM/IdleM01.png",
                    "assets/Monkey/IdleM/IdleM02.png",
                ],
                walk_frames=[
                    "assets/Monkey/WalkM/W01.png",
                    "assets/Monkey/WalkM/W02.png",
                    "assets/Monkey/WalkM/W03.png",
                    "assets/Monkey/WalkM/W04.png",
                ],
            ),
        }

        # 2. นำ UI สวยๆ (พื้นหลังสีเทาเข้มอมฟ้า) มาใช้
        with self.canvas.before:
            Color(0.05, 0.08, 0.1, 1)
            self.bg = Rectangle(pos=self.pos, size=Window.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        layout = BoxLayout(orientation="vertical", padding=50, spacing=30)

        # 3. หัวข้อมีขอบดำสวยๆ
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
            # 4. ปรับปุ่มให้เป็นธีมกระจกโปร่งแสงและแสดง Status โชว์ ATK ด้วย
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
        # บันทึกตัวละครที่เลือกลงใน App และเปลี่ยนหน้า
        kivy.app.App.get_running_app().current_player = stats
        self.manager.current = "game_screen"
