"""ui/level_up.py — 4 choices: skill + stat upgrades"""
from kivy.uix.modalview import ModalView
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle
from kivy.core.window import Window
from kivy.clock import Clock
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
        
        self.cards = []
        self.selected_idx = 0
        
        for choice in self.choices:
            card_widget = self._make_card(choice)
            card_box.add_widget(card_widget)
            self.cards.append((card_widget, choice))
            
        root.add_widget(card_box)
        self.add_widget(root)

        self._update_highlight()
            
        Window.bind(on_joy_axis=self._on_joy_axis, on_joy_button_down=self._on_joy_button, mouse_pos=self._on_mouse_pos)

    def _make_card(self, choice):
        is_new = choice.get("is_new", False)
        ctype = choice.get("type", "skill")

        card = FloatLayout(size_hint=(1, 1))
        
        with card.canvas.before:
            if ctype == "stat":
                card._bg_col = Color(0.08, 0.22, 0.12, 1)
            elif is_new:
                card._bg_col = Color(0.18, 0.1, 0.26, 1)
            else:
                card._bg_col = Color(0.1, 0.14, 0.22, 1)
            card._bg_rect = RoundedRectangle(radius=[12], pos=card.pos, size=card.size)
            
            # Selection Border
            card._border_color = Color(1, 1, 1, 0)
            card._border_rect = RoundedRectangle(radius=[12], pos=(card.x-3, card.y-3), size=(card.width+6, card.height+6))

        def _update_rects(inst, value):
            card._bg_rect.pos = card.pos
            card._bg_rect.size = card.size
            card._border_rect.pos = (card.x-3, card.y-3)
            card._border_rect.size = (card.width+6, card.height+6)

        card.bind(pos=_update_rects, size=_update_rects)

        label_color = (0.5, 1.0, 0.6, 1) if ctype == "stat" else \
                      (0.85, 0.5, 1.0, 1) if is_new else (0.5, 0.85, 1.0, 1)

        lbl = Label(
            text=f"[b]{choice['label']}[/b]",
            markup=True, font_size=17, color=label_color,
            halign="center", valign="middle",
            size_hint=(0.9, 0.3),
            pos_hint={"center_x": 0.5, "top": 0.92},
        )
        lbl.bind(size=lambda i, v: setattr(i, "text_size", v))
        card.add_widget(lbl)

        desc = Label(
            text=choice.get("description", ""),
            font_size=13, color=(0.85, 0.85, 0.85, 1),
            halign="center", valign="top",
            size_hint=(0.9, 0.45),
            pos_hint={"center_x": 0.5, "top": 0.6},
        )
        desc.bind(size=lambda i, v: setattr(i, "text_size", v))
        card.add_widget(desc)

        # Handle touch manually for the card
        def on_card_down(touch):
            if card.collide_point(*touch.pos):
                self._select(choice)
                return True
            return False
        
        card.on_touch_down = on_card_down
        return card

    def _on_mouse_pos(self, win, pos):
        # ตรวจสอบว่าเมาส์ชี้ที่การ์ดไหนเพื่อไฮไลต์ตาม
        for i, (card, choice) in enumerate(self.cards):
            if card.collide_point(*card.to_widget(*pos)):
                if self.selected_idx != i:
                    self.selected_idx = i
                    self._update_highlight()
                break

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
                stats.speed = min(stats.speed + 0.5, cap)

        gs.hud.update_ui(stats)
        gs.is_paused = False
        self.dismiss()

    def _update_highlight(self):
        if not self.cards: return
        for i, (card, choice) in enumerate(self.cards):
            if i == self.selected_idx:
                card._border_color.rgba = (1, 0.85, 0.2, 0.8)
            else:
                card._border_color.rgba = (1, 1, 1, 0)
                
    def _on_joy_axis(self, win, stick, axisid, value):
        v = value / 32767.0
        if abs(v) > 0.5:
            if getattr(self, '_axis_cooldown', False): return
            if axisid == 0:
                if v > 0:
                    self.selected_idx = (self.selected_idx + 1) % len(self.cards)
                else:
                    self.selected_idx = (self.selected_idx - 1) % len(self.cards)
                self._update_highlight()
                self._axis_cooldown = True
                Clock.schedule_once(lambda dt: setattr(self, '_axis_cooldown', False), 0.2)
                
    def _on_joy_button(self, win, stick, buttonid):
        if buttonid == 0:
            if 0 <= self.selected_idx < len(self.cards):
                card, choice = self.cards[self.selected_idx]
                self._select(choice)
                
    def dismiss(self, *args, **kwargs):
        Window.unbind(on_joy_axis=self._on_joy_axis, on_joy_button_down=self._on_joy_button, mouse_pos=self._on_mouse_pos)
        super().dismiss(*args, **kwargs)
