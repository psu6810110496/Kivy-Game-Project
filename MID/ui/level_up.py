from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle


class LevelUpPopup(Popup):
    def __init__(self, game_screen, choices=None, **kwargs):
        super().__init__(**kwargs)
        self.game_screen = game_screen
        self.title = f"LEVEL UP!  Lv {game_screen.player_stats.level}  — เลือก Upgrade:"
        self.title_font_size = 22
        self.background = ""
        self.background_color = (0.05, 0.08, 0.1, 0.95)
        self.separator_color = (0.3, 0.5, 0.6, 1)
        self.size_hint = (0.75, 0.55)
        self.auto_dismiss = False

        # choices=None → ใช้โหมด stat เดิม
        # choices=[...] → ใช้โหมดสกิลจาก engine ใหม่
        self._choices = choices

        layout = BoxLayout(orientation="vertical", padding=24, spacing=18)

        if self._choices:
            layout.add_widget(self._build_skill_cards())
        else:
            layout.add_widget(self._build_stat_cards())

        self.content = layout

    # ── โหมดสกิล ───────────────────────────────────────────────────────────
    def _build_skill_cards(self):
        grid = GridLayout(
            cols=min(len(self._choices), 3),
            spacing=20,
            padding=[5, 10, 5, 10],
        )
        for choice in self._choices:
            box = BoxLayout(orientation="vertical", spacing=8, padding=12)

            # พื้นหลังการ์ด
            with box.canvas.before:
                Color(0.08, 0.12, 0.18, 0.95)
                bg = RoundedRectangle(radius=[10, 10, 10, 10])

            def _update_bg(instance, value):
                bg.pos = instance.pos
                bg.size = instance.size

            box.bind(pos=_update_bg, size=_update_bg)

            title_lbl = Label(
                text=choice["label"],
                font_size=18,
                bold=True,
                color=(0.95, 0.98, 1, 1),
                size_hint_y=0.35,
                halign="center",
                valign="middle",
            )
            title_lbl.bind(size=lambda inst, _: setattr(inst, "text_size", inst.size))
            box.add_widget(title_lbl)

            desc_lbl = Label(
                text=choice["description"],
                font_size=13,
                color=(0.78, 0.88, 0.96, 1),
                size_hint_y=0.35,
                halign="center",
                valign="top",
            )
            desc_lbl.bind(size=lambda inst, _: setattr(inst, "text_size", inst.size))
            box.add_widget(desc_lbl)

            btn = Button(
                text="เลือกการ์ดนี้",
                font_size=16,
                bold=True,
                size_hint_y=0.3,
                background_normal="",
                background_color=(0.2, 0.55, 0.8, 1),
                color=(1, 1, 1, 1),
            )
            # ✅ ใช้ default arg c=choice กัน closure bug
            btn.bind(on_press=lambda inst, c=choice: self._pick_skill(c))
            box.add_widget(btn)
            grid.add_widget(box)

        return grid

    def _pick_skill(self, choice):
        stats = self.game_screen.player_stats
        skill = choice["skill"]

        if choice["is_new"]:
            skill._timer = 0.0      # ให้ยิงทันทีที่ได้รับสกิล
            stats.skills.append(skill)
        else:
            skill.upgrade()

        self._close()

    # ── โหมด stat เดิม (fallback ถ้าไม่ส่ง choices) ──────────────────────
    def _build_stat_cards(self):
        grid = GridLayout(cols=3, spacing=15)
        upgrades = [
            {"text": "+ Damage\n(ตีแรงขึ้น)",    "stat": "damage"},
            {"text": "+ Max HP\n(เลือดเยอะขึ้น)", "stat": "hp"},
            {"text": "+ Speed\n(วิ่งเร็วขึ้น)",   "stat": "speed"},
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
            btn.bind(on_press=lambda inst, s=upg["stat"]: self._pick_stat(s))
            grid.add_widget(btn)
        return grid

    def _pick_stat(self, stat_type):
        player = self.game_screen.player_stats
        if stat_type == "damage":
            player.damage += 5
        elif stat_type == "hp":
            player.hp += 20
            player.current_hp += 20
        elif stat_type == "speed":
            player.speed += 0.5
        self._close()

    # ── ปิด popup และ resume เกม ────────────────────────────────────────────
    def _close(self):
        self.game_screen.hud.update_ui(self.game_screen.player_stats)
        self.dismiss()
        self.game_screen.resume_game()

