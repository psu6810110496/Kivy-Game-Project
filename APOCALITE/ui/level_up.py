"""ui/level_up.py — 4 choices: skill + stat upgrades  (premium UI)"""
from kivy.uix.modalview import ModalView
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.graphics import (
    Color, RoundedRectangle, Rectangle, Line,
    InstructionGroup,
)
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.animation import Animation
from game.skills import get_upgrade_choices, CHAR_SPEED_CAP

# ─── Icon mapping: skill class name → first asset frame ────────────
SKILL_ICONS = {
    # PTae
    "DinoCircle":  "assets/PTae/skill1/aoeptae01.png",
    "DinoSummon":  "assets/PTae/skill2/F0.png",
    "DinoPunch":   "assets/PTae/PTPushUp/PTaeTester1.png",
    "PtaePunch":   "assets/PTae/PTPushUp/PTaeTester1.png",
    # Lostman
    "AxeThrow":    "assets/Lostman/skill2/axe_t1.png",
    "WhirlSlash":  "assets/Lostman/skill1/axe_hit1.png",
    "BombTrap":    "assets/Lostman/skill3/c4_trap1.png",
    "LostmanAxe":  "assets/Lostman/skill1/axe_hit1.png",
    # Monkey
    "PistolSkill":   "assets/Monkey/shoot/bullets1.png",
    "ShotgunSkill":  "assets/Monkey/shoot/bullets1.png",
    "RPGSkill":      "assets/Monkey/Weapon/RPG.png",
    "MonkeyCombo":   "assets/Monkey/M/m1.png",
}

# ─── Stat icon images ────────────────────────────────────────────────
STAT_ICON_PATHS = {
    "hp":     "assets/icons/Skillicon7_16.png",
    "damage": "assets/icons/atk.png",
    "speed":  "assets/icons/speed.png",
}

# ─── Color palettes ─────────────────────────────────────────────────
CARD_COLORS = {
    "new_skill": {
        "bg":     (0.28, 0.10, 0.42, 1),     # deep purple
        "bg2":    (0.20, 0.06, 0.32, 1),
        "accent": (0.80, 0.45, 1.00, 1),
        "glow":   (0.75, 0.35, 1.00, 0.65),
        "label":  (0.92, 0.65, 1.00, 1),
    },
    "upgrade_skill": {
        "bg":     (0.08, 0.16, 0.30, 1),     # deep blue
        "bg2":    (0.05, 0.10, 0.22, 1),
        "accent": (0.40, 0.75, 1.00, 1),
        "glow":   (0.30, 0.65, 1.00, 0.50),
        "label":  (0.55, 0.88, 1.00, 1),
    },
    "stat": {
        "bg":     (0.06, 0.22, 0.14, 1),     # deep green
        "bg2":    (0.03, 0.15, 0.09, 1),
        "accent": (0.40, 1.00, 0.55, 1),
        "glow":   (0.30, 0.90, 0.45, 0.50),
        "label":  (0.55, 1.00, 0.65, 1),
    },
}


def _get_skill_icon(choice):
    """Return asset path for the first frame of a skill, or None."""
    ctype = choice.get("type", "skill")
    if ctype == "stat":
        return None  # stats use emoji instead
    skill = choice.get("skill")
    if skill is None:
        return None
    cls_name = type(skill).__name__
    return SKILL_ICONS.get(cls_name)


def _card_palette(choice):
    ctype = choice.get("type", "skill")
    if ctype == "stat":
        return CARD_COLORS["stat"]
    is_new = choice.get("is_new", False)
    return CARD_COLORS["new_skill"] if is_new else CARD_COLORS["upgrade_skill"]


class LevelUpPopup(ModalView):
    def __init__(self, game_screen, choices=None, **kw):
        super().__init__(
            size_hint=(0.78, 0.62),
            background_color=(0, 0, 0, 0),
            background="",
            auto_dismiss=False,
            **kw,
        )
        self.game_screen = game_screen
        self.choices = (
            choices
            if choices is not None
            else get_upgrade_choices(game_screen.player_stats)
        )

        root = FloatLayout()

        # ── dark outer frame ───────────────────────────────────
        with root.canvas.before:
            Color(0.02, 0.03, 0.08, 0.97)
            self._bg = RoundedRectangle(
                radius=[20], pos=root.pos, size=root.size
            )
            # subtle border
            Color(1, 0.85, 0.20, 0.35)
            self._border = RoundedRectangle(
                radius=[20],
                pos=(root.x - 2, root.y - 2),
                size=(root.width + 4, root.height + 4),
            )

        def _sync_bg(inst, val):
            self._bg.pos = root.pos
            self._bg.size = root.size
            self._border.pos = (root.x - 2, root.y - 2)
            self._border.size = (root.width + 4, root.height + 4)

        root.bind(pos=_sync_bg, size=_sync_bg)

        # ── title ──────────────────────────────────────────────
        title = Label(
            text="[b]LEVEL UP![/b]",
            markup=True,
            font_size=42,
            color=(1, 0.85, 0.20, 1),
            size_hint=(1, None),
            height=62,
            pos_hint={"center_x": 0.5, "top": 0.98},
            outline_width=3,
            outline_color=(0, 0, 0, 1),
            halign="center",
        )
        root.add_widget(title)



        # ── card container ─────────────────────────────────────
        card_box = BoxLayout(
            orientation="horizontal",
            size_hint=(0.94, 0.72),
            pos_hint={"center_x": 0.5, "y": 0.04},
            spacing=14,
            padding=[6, 0, 6, 0],
        )

        self.cards = []
        self.selected_idx = 0

        for choice in self.choices:
            card_widget = self._make_card(choice)
            card_box.add_widget(card_widget)
            self.cards.append((card_widget, choice))

        root.add_widget(card_box)
        self.add_widget(root)

        self._update_highlight()

        # ── animate title glow ─────────────────────────────────
        self._title_ref = title
        self._pulse_title()

        Window.bind(
            on_joy_axis=self._on_joy_axis,
            on_joy_button_down=self._on_joy_button,
            mouse_pos=self._on_mouse_pos,
            on_key_down=self._on_keyboard_down,
        )

    # ─────────────────────────────────────────────────────────
    #  CARD BUILDER
    # ─────────────────────────────────────────────────────────
    def _make_card(self, choice):
        pal = _card_palette(choice)
        ctype = choice.get("type", "skill")
        is_new = choice.get("is_new", False)

        card = FloatLayout(size_hint=(1, 1))

        # — background layers —
        with card.canvas.before:
            # glow behind card (selection will toggle alpha)
            card._glow_color = Color(*pal["glow"][:3], 0)
            card._glow_rect = RoundedRectangle(
                radius=[16],
                pos=(card.x - 5, card.y - 5),
                size=(card.width + 10, card.height + 10),
            )
            # main bg
            card._bg_col = Color(*pal["bg"])
            card._bg_rect = RoundedRectangle(
                radius=[14], pos=card.pos, size=card.size
            )
            # inner highlight stripe (top)
            card._hl_col = Color(*pal["bg2"])
            card._hl_rect = RoundedRectangle(
                radius=[14, 14, 0, 0],
                pos=(card.x, card.y + card.height * 0.55),
                size=(card.width, card.height * 0.45),
            )
            # border (selection-aware)
            card._border_color = Color(1, 1, 1, 0)
            card._border_rect = RoundedRectangle(
                radius=[14],
                pos=(card.x - 2, card.y - 2),
                size=(card.width + 4, card.height + 4),
            )

        def _update_rects(inst, value):
            card._bg_rect.pos = card.pos
            card._bg_rect.size = card.size
            card._hl_rect.pos = (card.x, card.y + card.height * 0.55)
            card._hl_rect.size = (card.width, card.height * 0.45)
            card._border_rect.pos = (card.x - 2, card.y - 2)
            card._border_rect.size = (card.width + 4, card.height + 4)
            card._glow_rect.pos = (card.x - 5, card.y - 5)
            card._glow_rect.size = (card.width + 10, card.height + 10)

        card.bind(pos=_update_rects, size=_update_rects)



        # — icon image —
        icon_path = _get_skill_icon(choice)
        if ctype == "stat":
            stat_key = choice.get("stat", "hp")
            icon_path = STAT_ICON_PATHS.get(stat_key)
        if icon_path:
            import os
            if os.path.isfile(icon_path):
                try:
                    icon_img = Image(
                        source=icon_path,
                        size_hint=(None, None),
                        size=(56, 56),
                        pos_hint={"center_x": 0.5, "top": 0.88},
                        allow_stretch=True,
                    )
                    card.add_widget(icon_img)
                except Exception:
                    pass

        # — title label —
        lbl = Label(
            text=f"[b]{choice['label']}[/b]",
            markup=True,
            font_size=17,
            color=pal["label"],
            halign="center",
            valign="middle",
            size_hint=(0.92, 0.22),
            pos_hint={"center_x": 0.5, "top": 0.42},
            outline_width=1,
            outline_color=(0, 0, 0, 1),
        )
        lbl.bind(size=lambda i, v: setattr(i, "text_size", v))
        card.add_widget(lbl)

        # — touch handling (click to select) —
        def on_card_down(touch):
            if card.collide_point(*touch.pos):
                self._select(choice)
                return True
            return False

        card.on_touch_down = on_card_down
        return card

    # ─────────────────────────────────────────────────────────
    #  HIGHLIGHT
    # ─────────────────────────────────────────────────────────
    def _update_highlight(self):
        if not self.cards:
            return
        for i, (card, choice) in enumerate(self.cards):
            pal = _card_palette(choice)
            if i == self.selected_idx:
                card._border_color.rgba = (1, 0.95, 0.65, 0.40)
                card._glow_color.a = pal["glow"][3] * 0.5
            else:
                card._border_color.rgba = (1, 1, 1, 0)
                card._glow_color.a = 0

    # ─────────────────────────────────────────────────────────
    #  TITLE PULSE
    # ─────────────────────────────────────────────────────────
    def _pulse_title(self):
        if not hasattr(self, '_title_ref'):
            return
        anim = (
            Animation(color=(1, 0.95, 0.40, 1), duration=0.7, t="in_out_sine")
            + Animation(color=(1, 0.80, 0.15, 1), duration=0.7, t="in_out_sine")
        )
        anim.repeat = True
        anim.start(self._title_ref)
        self._title_anim = anim

    # ─────────────────────────────────────────────────────────
    #  MOUSE HOVER
    # ─────────────────────────────────────────────────────────
    def _on_mouse_pos(self, win, pos):
        for i, (card, choice) in enumerate(self.cards):
            if card.collide_point(*card.to_widget(*pos)):
                if self.selected_idx != i:
                    self.selected_idx = i
                    self._update_highlight()
                break

    # ─────────────────────────────────────────────────────────
    #  SELECTION
    # ─────────────────────────────────────────────────────────
    def _select(self, choice):
        gs = self.game_screen
        stats = gs.player_stats
        ctype = choice.get("type", "skill")

        if ctype == "skill":
            skill = choice["skill"]
            is_new = choice.get("is_new", False)
            is_s3 = choice.get("is_s3", False)

            if is_new:
                if is_s3:
                    stats.skill3 = skill
                else:
                    skill._timer = 0.0
                    stats.skills.append(skill)
            else:
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
                stats.speed = min(stats.speed + 0.25, cap)

        gs.hud.update_ui(stats)
        gs.is_paused = False
        self.dismiss()

    # ─────────────────────────────────────────────────────────
    #  KEYBOARD / GAMEPAD
    # ─────────────────────────────────────────────────────────
    def _on_keyboard_down(self, window, key, scancode, codepoint, modifiers):
        if key in (119, 97):  # W or A
            self.selected_idx = (self.selected_idx - 1) % len(self.cards)
            self._update_highlight()
            return True
        elif key in (115, 100):  # S or D
            self.selected_idx = (self.selected_idx + 1) % len(self.cards)
            self._update_highlight()
            return True
        elif key in (32, 13):  # Spacebar or Enter
            if 0 <= self.selected_idx < len(self.cards):
                card, choice = self.cards[self.selected_idx]
                self._select(choice)
            return True
        return False

    def _on_joy_axis(self, win, stick, axisid, value):
        v = value / 32767.0
        if abs(v) > 0.5:
            if getattr(self, "_axis_cooldown", False):
                return
            if axisid in (0, 1):
                if v > 0:
                    self.selected_idx = (self.selected_idx + 1) % len(self.cards)
                else:
                    self.selected_idx = (self.selected_idx - 1) % len(self.cards)
                self._update_highlight()
                self._axis_cooldown = True
                Clock.schedule_once(
                    lambda dt: setattr(self, "_axis_cooldown", False), 0.2
                )

    def _on_joy_hat(self, win, stickid, hatid, value):
        x, y = value
        if x == 1 or y == -1:
            self.selected_idx = (self.selected_idx + 1) % len(self.cards)
            self._update_highlight()
        elif x == -1 or y == 1:
            self.selected_idx = (self.selected_idx - 1) % len(self.cards)
            self._update_highlight()

    def _on_joy_button(self, win, stick, buttonid):
        if buttonid == 0:
            if 0 <= self.selected_idx < len(self.cards):
                card, choice = self.cards[self.selected_idx]
                self._select(choice)

    # ─────────────────────────────────────────────────────────
    #  DISMISS
    # ─────────────────────────────────────────────────────────
    def dismiss(self, *args, **kwargs):
        Window.unbind(
            on_joy_axis=self._on_joy_axis,
            on_joy_button_down=self._on_joy_button,
            mouse_pos=self._on_mouse_pos,
            on_key_down=self._on_keyboard_down,
        )
        if hasattr(self, "_title_anim"):
            self._title_anim.cancel(self._title_ref)
        super().dismiss(*args, **kwargs)
