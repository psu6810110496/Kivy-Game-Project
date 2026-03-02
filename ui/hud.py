from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.properties import NumericProperty
import kivy.app
from ui.level_up import LevelUpPopup


# --- [คลาส HealthBar] ---
class HealthBar(Widget):
    current_hp = NumericProperty(100)
    max_hp = NumericProperty(100)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            pos=self.update_canvas,
            size=self.update_canvas,
            current_hp=self.update_canvas,
            max_hp=self.update_canvas,
        )

    def update_canvas(self, *args):
        self.canvas.clear()
        with self.canvas:
            Color(0.2, 0.2, 0.2, 1)
            Rectangle(pos=self.pos, size=self.size)

            Color(0.8, 0.1, 0.1, 1)
            hp_ratio = max(0, min(self.current_hp / max(self.max_hp, 1), 1))
            Rectangle(pos=self.pos, size=(self.width * hp_ratio, self.height))


# -----------------------------


class HUD(FloatLayout):
    def __init__(self, game_screen, **kwargs):
        super().__init__(**kwargs)
        self.game_screen = game_screen

        # --- [🌟 ส่วนที่แก้ไข: จัดกลุ่ม UI มุมซ้ายบนให้ตรงกันเป๊ะ] ---
        # สร้างกล่องรวม (กว้าง 360 = ตัวหนังสือ 60 + หลอด 300)
        top_left_ui = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            size=(360, 60),
            pos_hint={"x": 0.02, "top": 0.98},
            spacing=5,
        )

        # แถวบน: หลอดเลือด (ใช้ FloatLayout เพื่อซ้อนข้อความและจัดชิดขวา)
        hp_container = FloatLayout(size_hint=(1, 1))

        # ดันหลอดเลือดไปชิดขวาของกล่อง เพื่อเว้นที่ว่างด้านซ้ายให้ตรงกับคำว่า "LV : 1"
        self.health_bar = HealthBar(
            size_hint=(None, None),
            size=(300, 25),
            pos_hint={"right": 1, "center_y": 0.5},
        )
        self.hp_label = Label(
            text="100 / 100",
            size_hint=(None, None),
            size=(300, 25),
            pos_hint={"right": 1, "center_y": 0.5},
            bold=True,
        )
        hp_container.add_widget(self.health_bar)
        hp_container.add_widget(self.hp_label)

        # แถวล่าง: เลเวล + หลอด EXP
        exp_container = BoxLayout(orientation="horizontal", size_hint=(1, 1), spacing=5)
        self.lbl_level = Label(
            text="LV : 1",
            size_hint=(None, 1),
            width=55,  # ความกว้างตัวหนังสือ 55 + spacing 5 = 60 พอดี
            font_size=18,
            bold=True,
            color=(0.9, 0.95, 1, 1),
            outline_width=2,
            outline_color=(0, 0, 0, 1),
        )
        # ตั้งความกว้างหลอด EXP ให้เป็น 300 เท่ากับหลอดเลือด
        self.exp_bar = ProgressBar(max=100, value=0, size_hint=(None, 1), width=300)

        exp_container.add_widget(self.lbl_level)
        exp_container.add_widget(self.exp_bar)

        # นำทั้งสองแถวใส่เข้ากล่องรวม แล้วแปะลงบนหน้าจอ
        top_left_ui.add_widget(hp_container)
        top_left_ui.add_widget(exp_container)
        self.add_widget(top_left_ui)

        # ให้อัปเดตเลือดแบบเรียลไทม์ 60 เฟรมต่อวินาที
        Clock.schedule_interval(self.update_hp_realtime, 1.0 / 60.0)
        # --------------------------------------------------------

        # ปุ่มเมนูด้านขวาบน
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

        self.health_bar.max_hp = stats.hp
        self.health_bar.current_hp = stats.current_hp
        self.hp_label.text = f"{int(stats.current_hp)} / {int(stats.hp)}"

    def update_hp_realtime(self, dt):
        if hasattr(self.game_screen, "player_stats") and self.game_screen.player_stats:
            player_stats = self.game_screen.player_stats
            self.health_bar.max_hp = player_stats.hp
            self.health_bar.current_hp = player_stats.current_hp
            self.hp_label.text = (
                f"{int(player_stats.current_hp)} / {int(player_stats.hp)}"
            )


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
