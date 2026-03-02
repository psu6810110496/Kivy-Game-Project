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

        self.background = ""
        self.background_color = (0.05, 0.08, 0.1, 0.95)
        self.separator_color = (0.3, 0.5, 0.6, 1)

        self.size_hint = (0.6, 0.5)
        self.auto_dismiss = False  # บังคับให้ผู้เล่นต้องเลือก 1 อย่าง

        layout = BoxLayout(orientation="vertical", padding=20, spacing=20)
        cards_layout = GridLayout(cols=3, spacing=15)

        # กำหนดของอัปเกรด
        upgrades = [
            {"text": "+ Damage\n(ตีแรงขึ้น)", "stat": "damage"},
            {"text": "+ Max HP\n(เลือดเยอะขึ้น)", "stat": "hp"},
            {"text": "+ Speed\n(วิ่งเร็วขึ้น)", "stat": "speed"},
        ]

        for upg in upgrades:
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
