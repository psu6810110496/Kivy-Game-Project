"""ui/level_up.py — 4 choices: skill + stat upgrades"""
from kivy.uix.modalview import ModalView
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle
from game.skills import get_upgrade_choices, CHAR_SPEED_CAP


class LevelUpPopup(ModalView):
    def __init__(self, game_screen, choices=None, **kw):
        super().__init__(
            size_hint=(0.72, 0.55),
            background_color=(0, 0, 0, 0),
            background="",
            auto_dismiss=False,
            **kw,
        )
        self.game_screen = game_screen
        self.choices = choices if choices is not None else get_upgrade_choices(game_screen.player_stats)

        root = FloatLayout()
        with root.canvas.before:
            Color(0.03, 0.05, 0.1, 0.97)
            self._bg = RoundedRectangle(radius=[16], pos=root.pos, size=root.size)
        root.bind(pos=lambda i, v: setattr(self._bg, "pos", v),
                  size=lambda i, v: setattr(self._bg, "size", v))

        title = Label(
            text="[b]LEVEL UP![/b]", markup=True,
            font_size=38, color=(1, 0.85, 0.2, 1),
            size_hint=(1, None), height=58,
            pos_hint={"center_x": 0.5, "top": 1.0},
            outline_width=3, outline_color=(0, 0, 0, 1),
            halign="center",
        )
        root.add_widget(title)

        card_box = BoxLayout(
            orientation="horizontal",
            size_hint=(0.95, 0.72),
            pos_hint={"center_x": 0.5, "y": 0.04},
            spacing=10,
        )
        for choice in self.choices:
            card_box.add_widget(self._make_card(choice))
        root.add_widget(card_box)
        self.add_widget(root)

    def _make_card(self, choice):
        is_new = choice.get("is_new", False)
        ctype = choice.get("type", "skill")

        card = FloatLayout(size_hint=(1, 1))
        with card.canvas.before:
            if ctype == "stat":
                Color(0.08, 0.22, 0.12, 1)
            elif is_new:
                Color(0.18, 0.1, 0.26, 1)
            else:
                Color(0.1, 0.14, 0.22, 1)
            self._card_bg = RoundedRectangle(radius=[12], pos=card.pos, size=card.size)
        card.bind(pos=lambda i, v: setattr(self._card_bg, "pos", v),
                  size=lambda i, v: setattr(self._card_bg, "size", v))

        label_color = (0.5, 1.0, 0.6, 1) if ctype == "stat" else \
                      (0.85, 0.5, 1.0, 1) if is_new else (0.5, 0.85, 1.0, 1)

        lbl = Label(
            text=f"[b]{choice['label']}[/b]",
            markup=True, font_size=15, color=label_color,
            halign="center", valign="middle",
            size_hint=(0.9, 0.3),
            pos_hint={"center_x": 0.5, "top": 0.97},
        )
        lbl.bind(size=lambda i, v: setattr(i, "text_size", v))
        card.add_widget(lbl)

        desc = Label(
            text=choice.get("description", ""),
            font_size=12, color=(0.85, 0.85, 0.85, 1),
            halign="center", valign="top",
            size_hint=(0.9, 0.38),
            pos_hint={"center_x": 0.5, "top": 0.64},
        )
        desc.bind(size=lambda i, v: setattr(i, "text_size", v))
        card.add_widget(desc)

        btn = Button(
            text="SELECT", font_size=14, bold=True,
            size_hint=(0.78, None), height=40,
            pos_hint={"center_x": 0.5, "y": 0.05},
            background_normal="", background_color=(0.2, 0.6, 1.0, 1),
            color=(1, 1, 1, 1),
        )
        btn.bind(on_press=lambda _: self._select(choice))
        card.add_widget(btn)
        return card

    def _select(self, choice):
        gs = self.game_screen
        stats = gs.player_stats
        ctype = choice.get("type", "skill")

        if ctype == "skill":
            skill = choice["skill"]
            is_new = choice.get("is_new", False)
            is_s3  = choice.get("is_s3", False)

            if is_new:
                if is_s3:
                    # unlock skill3 — เก็บแยกออกจาก skills list
                    stats.skill3 = skill
                else:
                    skill._timer = 0.0  # ยิงทันทีที่ได้รับ
                    stats.skills.append(skill)
            else:
                # upgrade (เพิ่ม level)
                skill.upgrade()

        elif ctype == "stat":
            stat = choice["stat"]
            if stat == "hp":
                stats.hp += 20
                stats.current_hp = min(stats.current_hp + 20, stats.hp)
            elif stat == "damage":
                stats.damage += 3
            elif stat == "speed":
                cap = CHAR_SPEED_CAP.get(stats.name, 10.0)
                stats.speed = min(stats.speed + 0.5, cap)

        gs.hud.update_ui(stats)
        gs.is_paused = False
        self.dismiss()
