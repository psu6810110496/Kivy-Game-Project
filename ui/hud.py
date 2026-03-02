from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
import kivy.app

# นำเข้า LevelUpPopup สำหรับเรียกใช้เวลาเลเวลอัป
from ui.level_up import LevelUpPopup


class HUD(FloatLayout):
    def __init__(self, game_screen, **kwargs):
        super().__init__(**kwargs)
        self.game_screen = game_screen

        # --- แถบ UI ด้านบน (Level & EXP) ---
        top_ui = BoxLayout(
            size_hint=(0.8, 0.05), pos_hint={"center_x": 0.5, "top": 0.98}, spacing=15
        )

        self.lbl_level = Label(
            text="LV : 1",
            size_hint=(0.15, 1),
            bold=True,
            color=(1, 0.5, 0.1, 1),  # สีส้มไฟ
            font_size=20,
        )
        self.exp_bar = ProgressBar(max=100, value=0, size_hint=(0.85, 1))

        top_ui.add_widget(self.lbl_level)
        top_ui.add_widget(self.exp_bar)
        self.add_widget(top_ui)

        # --- ปุ่ม Pause สไตล์ Flat ---
        btn_pause = Button(
            text="||",
            font_size=24,
            bold=True,
            size_hint=(None, None),
            size=(50, 50),
            pos_hint={"right": 0.98, "top": 0.98},
            background_normal="",
            background_color=(0.2, 0.2, 0.2, 0.8),
            color=(1, 0.8, 0.2, 1),
        )
        btn_pause.bind(on_press=self.game_screen.pause_game)
        self.add_widget(btn_pause)

        # --- [ปุ่มสำหรับ TEST Level Up (เรียก Popup ทันที)] ---
        btn_test_lvl = Button(
            text="TEST\nLVL UP",
            font_size=14,
            bold=True,
            halign="center",
            size_hint=(None, None),
            size=(80, 50),
            pos_hint={"right": 0.98, "top": 0.88},  # วางไว้ใต้ปุ่ม Pause
            background_normal="",
            background_color=(0.6, 0.1, 0.6, 0.8),  # สีม่วง
            color=(1, 1, 1, 1),
        )
        btn_test_lvl.bind(on_press=self.test_level_up)
        self.add_widget(btn_test_lvl)

        # --- [ปุ่มสำหรับ ADD EXP (เพิ่ม EXP ทีละ 20)] ---
        btn_add_exp = Button(
            text="ADD\nEXP +20",
            font_size=14,
            bold=True,
            halign="center",
            size_hint=(None, None),
            size=(80, 50),
            pos_hint={"right": 0.98, "top": 0.78},  # วางไว้ใต้ปุ่ม TEST LVL UP
            background_normal="",
            background_color=(0.1, 0.5, 0.6, 0.8),  # สีฟ้าอมเขียว (Teal)
            color=(1, 1, 1, 1),
        )
        btn_add_exp.bind(on_press=self.test_add_exp)
        self.add_widget(btn_add_exp)

    def test_level_up(self, instance):
        # สั่งหยุดเกมเบื้องหลังโดยไม่เรียกหน้าต่าง Pause ปกติ
        # (ตรวจสอบว่าใน engine ของคุณใช้ตัวแปร is_paused หรือไม่ ถ้าใช่ให้ตั้งเป็น True)
        if hasattr(self.game_screen, "is_paused"):
            self.game_screen.is_paused = True

        # เปิดหน้าต่างอัปเกรด
        popup = LevelUpPopup(self.game_screen)
        popup.open()

    def test_add_exp(self, instance):
        # ดึงข้อมูลผู้เล่นปัจจุบัน
        player = kivy.app.App.get_running_app().current_player
        if player:
            player.exp += 20  # เพิ่ม EXP ทีละ 20

            # เช็คว่า EXP เต็มหลอด (100) หรือไม่
            if player.exp >= 100:
                player.exp -= 100
                player.level += 1

                # --- ส่วนที่แก้ไข ---
                # ลบ self.game_screen.pause_game(instance) ออกเพื่อกันเมนูซ้อน
                if hasattr(self.game_screen, "is_paused"):
                    self.game_screen.is_paused = True

                # เปิดแค่หน้าต่างระบบอัปเกรด
                popup = LevelUpPopup(self.game_screen)
                popup.open()

            # อัปเดต UI ทันที
            self.update_ui(player)

    def update_ui(self, stats):
        # ฟังก์ชันนี้ใช้สำหรับอัปเดตตัวเลขและหลอดบนหน้าจอ
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
        self.color = (1, 0.6, 0.1, 1)  # สีส้ม
        self.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        Clock.schedule_interval(self.update_countdown, 1)

    def update_countdown(self, dt):
        self.count -= 1
        if self.count > 0:
            self.text = str(self.count)
        elif self.count == 0:
            self.text = "S U R V I V E !"
            self.font_size = 120
            self.color = (1, 0.1, 0.1, 1)  # แดงเลือด
        else:
            self.callback()
            self.parent.remove_widget(self)
            return False
