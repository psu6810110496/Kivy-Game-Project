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


# --- คลาสเอฟเฟกต์เถ้าถ่านไฟ (Ember Effect) ---
class EmberEffect(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.particles = []
        self.num_particles = 80

        with self.canvas:
            for _ in range(self.num_particles):
                # สุ่มสีส้ม-แดง-เหลือง ให้ดูเหมือนไฟ
                r = random.uniform(0.8, 1.0)
                g = random.uniform(0.2, 0.5)
                b = random.uniform(0.0, 0.1)
                a = random.uniform(0.3, 0.8)
                Color(r, g, b, a)

                size = random.uniform(3, 8)
                rect = Rectangle(
                    pos=(
                        random.uniform(-Window.width * 0.2, Window.width * 1.2),
                        random.uniform(0, Window.height),
                    ),
                    size=(size, size),
                )

                particle = {
                    "rect": rect,
                    "speed_y": random.uniform(2, 6),
                    "speed_x": random.uniform(-2, 4),
                }
                self.particles.append(particle)

        Clock.schedule_interval(self.update_embers, 1 / 60.0)

    def update_embers(self, dt):
        for p in self.particles:
            x, y = p["rect"].pos

            # เถ้าถ่านปลิวลงและส่ายไปมาเล็กน้อย
            y -= p["speed_y"]
            x += p["speed_x"]

            if y < -10 or x > Window.width + 10 or x < -10:
                y = Window.height + random.uniform(10, 50)
                x = random.uniform(-Window.width * 0.2, Window.width * 1.2)

            p["rect"].pos = (x, y)


class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        main_layout = FloatLayout()

        with main_layout.canvas.before:
            Color(0.05, 0.05, 0.08, 1)  # พื้นหลังสีเทาดำเข้มๆ (ถ้าไม่มีรูป)
            self.bg_rect = Rectangle(
                source="assets/Menu/MenuTest.png",  # รูปพื้นหลังของคุณ
                pos=(0, 0),
                size=Window.size,
            )

        main_layout.bind(size=self._update_bg, pos=self._update_bg)

        # เพิ่มเอฟเฟกต์เถ้าถ่าน
        self.ember = EmberEffect()
        main_layout.add_widget(self.ember)

        menu_group = BoxLayout(
            orientation="vertical",
            spacing=30,
            size_hint=(None, None),
            size=(800, 600),
            pos_hint={"x": 0.1, "center_y": 0.5},
        )

        # ชื่อเกมใหม่ APOCALITE
        title_label = Label(
            text="A P O C A L I T E",
            font_size=80,
            bold=True,
            color=(1, 0.3, 0.1, 1),  # สีส้มแดงเท่ๆ
            halign="left",
            valign="middle",
            size_hint=(1, None),
            height=150,
        )
        title_label.bind(size=title_label.setter("text_size"))

        btn_layout = BoxLayout(
            orientation="vertical", spacing=15, size_hint=(None, None), size=(350, 180)
        )

        # สไตล์ปุ่มแบบ Flat Design
        btn_start = Button(
            text="INITIATE SURVIVAL",
            font_size=24,
            bold=True,
            size_hint=(1, 1),
            background_normal="",  # ลบเงาปุ่มเดิมของ Kivy
            background_color=(0.8, 0.2, 0.1, 0.9),  # สีแดงส้ม
            color=(1, 1, 1, 1),
        )
        btn_quit = Button(
            text="ABORT",
            font_size=24,
            bold=True,
            size_hint=(1, 1),
            background_normal="",
            background_color=(0.2, 0.2, 0.2, 0.9),  # สีเทาเข้ม
            color=(0.8, 0.8, 0.8, 1),
        )

        btn_start.bind(on_press=lambda x: self.change_screen("char_select_screen"))
        btn_quit.bind(on_press=lambda x: App.get_running_app().stop())

        btn_layout.add_widget(btn_start)
        btn_layout.add_widget(btn_quit)

        menu_group.add_widget(title_label)
        menu_group.add_widget(btn_layout)

        main_layout.add_widget(menu_group)
        self.add_widget(main_layout)

    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def change_screen(self, screen_name):
        self.manager.current = screen_name
