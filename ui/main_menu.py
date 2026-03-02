from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Rectangle, Color
from kivy.core.window import Window
from kivy.clock import Clock
import random


# --- คลาสเอฟเฟกต์ฝนตก ---
class RainEffect(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.drops = []
        self.num_drops = 150  # เพิ่มจำนวนเม็ดฝนให้ดูสมจริงขึ้น

        with self.canvas:
            # ใช้สีขาว/ฟ้าเทา โปร่งแสงนิดๆ ให้ดูเป็นเม็ดฝน
            Color(0.7, 0.8, 0.9, 0.4)
            for _ in range(self.num_drops):
                rect = Rectangle(
                    pos=(
                        random.uniform(-Window.width * 0.5, Window.width),
                        random.uniform(0, Window.height),
                    ),
                    size=(1.5, random.uniform(15, 35)),  # ปรับเม็ดฝนให้เรียวยาวขึ้น
                )

                drop = {"rect": rect, "speed": random.uniform(12, 22)}  # ความเร็วในการตก
                self.drops.append(drop)

        Clock.schedule_interval(self.update_rain, 1 / 60.0)

    def update_rain(self, dt):
        for drop in self.drops:
            x, y = drop["rect"].pos

            y -= drop["speed"]
            x += drop["speed"] * 0.15  # ปรับความเฉียงของฝนให้ดูพอดี

            if y < -50 or x > Window.width:
                y = Window.height + random.uniform(10, 100)
                x = random.uniform(-Window.width * 0.2, Window.width)

            drop["rect"].pos = (x, y)


# --- คลาสหน้าจอเมนูหลัก ---
class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 1. จัดการรูปพื้นหลังให้อยู่บนสุดของ Screen และปรับตาม Window
        with self.canvas.before:
            Color(1, 1, 1, 1)  # ตั้งเป็นสีขาวล้วนเพื่อไม่ให้สีรูปเพี้ยน
            self.bg_rect = Rectangle(
                source="assets/Menu/MenuTest.png", pos=self.pos, size=Window.size
            )

        # ผูกการอัปเดตขนาดให้เท่ากับ Window เสมอ ไม่ว่าจะย่อหรือขยายจอ
        self.bind(pos=self._update_bg, size=self._update_bg)

        main_layout = FloatLayout()

        # 2. เพิ่มเอฟเฟกต์ฝน
        self.rain = RainEffect()
        main_layout.add_widget(self.rain)

        # 3. จัดวางกรอบเมนู (ขยับมาอยู่ตรงกลางแนวตั้ง)
        menu_group = BoxLayout(
            orientation="vertical",
            spacing=30,
            size_hint=(None, None),
            size=(600, 450),
            pos_hint={"x": 0.1, "center_y": 0.5},
        )

        # ปรับสี Title ให้เข้ากับธีมบรรยากาศฝนตก (สีฟ้าอ่อนอมเทา)
        title_label = Label(
            text="APOCALITE",
            font_size=80,
            bold=True,
            color=(0.8, 0.9, 1, 0.9),
            outline_width=4,
            outline_color=(0, 0, 0, 1),  # <--- เพิ่มขอบดำตรงนี้
            # font_name='assets/fonts/pixel_font.ttf', # <--- ถ้ามีไฟล์ฟอนต์ Pixel ให้เอา # ออกแล้วแก้ Path
            halign="left",
            valign="middle",
            size_hint=(1, None),
            height=120,
        )
        title_label.bind(size=title_label.setter("text_size"))

        # 4. ปุ่มเข้ากับธีมฝน (Rain Theme: กระจกโปร่งแสงสีเข้ม)
        btn_layout = BoxLayout(
            orientation="vertical", spacing=20, size_hint=(None, None), size=(350, 180)
        )

        btn_start = Button(
            text="START SURVIVING",
            font_size=22,
            bold=True,
            size_hint=(None, None),
            size=(350, 70),
            background_normal="",  # ต้องมีบรรทัดนี้ ไม่งั้นปุ่มจะเป็นก้อนสีขาว
            background_color=(0.1, 0.15, 0.2, 0.85),  # สีเทาเข้มอมฟ้า โปร่งแสง
            color=(0.9, 0.95, 1, 1),
        )
        btn_quit = Button(
            text="QUIT GAME",
            font_size=22,
            bold=True,
            size_hint=(None, None),
            size=(350, 70),
            background_normal="",
            background_color=(0.05, 0.08, 0.1, 0.85),  # สีดำเทา โปร่งแสง
            color=(0.7, 0.75, 0.8, 1),
        )

        btn_start.bind(on_press=lambda x: self.change_screen("char_select_screen"))
        btn_quit.bind(on_press=lambda x: App.get_running_app().stop())

        btn_layout.add_widget(btn_start)
        btn_layout.add_widget(btn_quit)

        menu_group.add_widget(title_label)
        menu_group.add_widget(btn_layout)

        main_layout.add_widget(menu_group)
        self.add_widget(main_layout)

    # 5. ฟังก์ชันอัปเดตขนาดพื้นหลังให้ติดหนึบกับหน้าจอ
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def change_screen(self, screen_name):
        self.manager.current = screen_name
