from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.clock import Clock
import kivy.app


class LevelUpPopup(Popup):
    def __init__(self, game_screen, **kwargs):
        super().__init__(**kwargs)
        self.game_screen = game_screen
        self.title = "LEVEL UP! Choose your Upgrade:"
        self.title_font_size = 22

        self.background = ""
        self.background_color = (0.05, 0.08, 0.1, 0.95)
        self.separator_color = (0.3, 0.5, 0.6, 1)

        self.size_hint = (0.6, 0.5)
        self.auto_dismiss = False  # บังคับให้ผู้เล่นต้องเลือก 1 อย่าง

        # --- [ระบบ Navigation (จอย + เมาส์)] ---
        self.selectable_buttons = []
        self.selected_index = 0
        self.show_highlight = False
        self.joy_cooldown = False
        self.bind(on_open=self.setup_joy, on_dismiss=self.remove_joy)

        layout = BoxLayout(orientation="vertical", padding=20, spacing=20)
        cards_layout = GridLayout(cols=3, spacing=15)

        # กำหนดของอัปเกรด
        upgrades = [
            {"text": "+ Damage\n(ตีแรงขึ้น)", "stat": "damage"},
            {"text": "+ Max HP\n(เลือดเยอะขึ้น)", "stat": "hp"},
            {"text": "+ Speed\n(วิ่งเร็วขึ้น)", "stat": "speed"},
        ]

        for idx, upg in enumerate(upgrades):
            btn = Button(
                text=upg["text"],
                font_size=20,
                bold=True,
                halign="center",
                background_normal="",
                background_color=(0.1, 0.15, 0.2, 0.8),
                color=(0.9, 0.95, 1, 1),
            )
            # ผูกปุ่มเข้ากับฟังก์ชันอัปเกรด
            btn.bind(on_press=lambda inst, s=upg["stat"]: self.select_upgrade(s))
            self.selectable_buttons.append(btn)
            cards_layout.add_widget(btn)

        layout.add_widget(cards_layout)
        self.content = layout

    def select_upgrade(self, stat_type):
        player = self.game_screen.player_stats

        # 🌟 อัปเกรดตามที่ผู้เล่นกดเลือก
        if stat_type == "damage":
            player.damage += 5
        elif stat_type == "hp":
            player.hp += 20
            player.current_hp += 20  # เพิ่มเลือดปัจจุบันให้ด้วย
        elif stat_type == "speed":
            player.speed += 0.5

        # อัปเดต UI และสั่งให้เกมเริ่มเดินต่อ
        self.game_screen.hud.update_ui(player)
        self.game_screen.resume_game()
        self.dismiss()  # ปิดหน้าต่าง Popup

    # ==========================================
    # --- [ระบบ Navigation ด้วยจอย/เมาส์] ---
    # ==========================================
    def setup_joy(self, *args):
        Window.bind(
            on_joy_axis=self._on_joy_axis,
            on_joy_hat=self._on_joy_hat,
            on_joy_button_down=self._on_joy_button_down,
            mouse_pos=self._on_mouse_pos,
        )
        self.selected_index = 0
        self.show_highlight = False
        self.update_highlight()

    def remove_joy(self, *args):
        Window.unbind(
            on_joy_axis=self._on_joy_axis,
            on_joy_hat=self._on_joy_hat,
            on_joy_button_down=self._on_joy_button_down,
            mouse_pos=self._on_mouse_pos,
        )

    def _on_mouse_pos(self, window, pos):
        for i, btn in enumerate(self.selectable_buttons):
            if btn.collide_point(*pos):
                self.selected_index = i
                self.show_highlight = True
                self.update_highlight()
                return

        if self.show_highlight:
            self.show_highlight = False
            self.update_highlight()

    def _reset_cooldown(self, dt):
        self.joy_cooldown = False

    def navigate(self, direction):
        if self.joy_cooldown:
            return
        self.joy_cooldown = True
        self.show_highlight = True
        Clock.schedule_once(self._reset_cooldown, 0.2)

        if direction == "next":
            self.selected_index = (self.selected_index + 1) % len(self.selectable_buttons)
        elif direction == "prev":
            self.selected_index = (self.selected_index - 1) % len(self.selectable_buttons)

        self.update_highlight()

    def update_highlight(self):
        for i, btn in enumerate(self.selectable_buttons):
            if i == self.selected_index and self.show_highlight:
                btn.background_color = (0.25, 0.4, 0.6, 1.0)
                btn.font_size = 22
            else:
                btn.background_color = (0.1, 0.15, 0.2, 0.8)
                btn.font_size = 20

    def _on_joy_axis(self, window, stickid, axisid, value):
        normalized = value / 32767.0
        if abs(normalized) > 0.5:
            # ใช้อนาล็อกซ้าย/ขวา หรือบน/ล่าง เลื่อนการ์ด
            if axisid in (0, 1):
                self.navigate("next" if normalized > 0 else "prev")

    def _on_joy_hat(self, window, stickid, hatid, value):
        x, y = value
        if x == 1 or y == -1:
            self.navigate("next")
        elif x == -1 or y == 1:
            self.navigate("prev")

    def _on_joy_button_down(self, window, stickid, buttonid):
        self.show_highlight = True
        self.update_highlight()

        if buttonid == 0:  # ปุ่ม A ยืนยัน
            self.selectable_buttons[self.selected_index].dispatch("on_press")
        elif buttonid == 1:  # ปุ่ม B = ยกเลิกเลือก (ไม่อัปเกรด) แล้วกลับเกมต่อ
            # ถ้าอยากบังคับให้ต้องเลือก สามารถคอมเมนต์ block นี้ทิ้งก็ได้
            self.game_screen.resume_game()
            self.dismiss()
