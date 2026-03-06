"""ui/char_select.py — updated character stats for balance"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Rectangle, Color
from kivy.core.window import Window
from kivy.clock import Clock
from game.player import PlayerStats
from kivy.app import App


class CharacterSelectScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selectable_buttons = []
        self.selected_index = 0
        self.show_highlight = False
        self.joy_cooldown = False

        from game.skills import CHAR_SPEED_CAP
        self.char_data = {
            "PTae": PlayerStats(
                name="PTae", hp=180, speed=3.0, damage=15,
                idle_frames=["assets/PTae/PTIdle/PTTG1.png","assets/PTae/PTIdle/PTTG2.png"],
                walk_frames=["assets/PTae/PTPushUp/PTaeTester1.png","assets/PTae/PTPushUp/PTaeTester2.png",
                             "assets/PTae/PTPushUp/PTaeTester3.png","assets/PTae/PTPushUp/PTaeTester4.png"],
            ),
            "Lostman": PlayerStats(
                name="Lostman", hp=120, speed=4.5, damage=12,
                idle_frames=["assets/Lostman/idle/idleman1.png","assets/Lostman/idle/idleman2.png"],
                walk_frames=["assets/Lostman/walk/walk1.png","assets/Lostman/walk/walk2.png",
                             "assets/Lostman/walk/walk3.png","assets/Lostman/walk/walk4.png"],
            ),
            "Monkey": PlayerStats(
                name="Monkey", hp=80, speed=6.0, damage=10,
                idle_frames=["assets/Monkey/IdleM/IdleM01.png","assets/Monkey/IdleM/IdleM02.png"],
                walk_frames=["assets/Monkey/WalkM/W01.png","assets/Monkey/WalkM/W02.png",
                             "assets/Monkey/WalkM/W03.png","assets/Monkey/WalkM/W04.png"],
            ),
        }

        with self.canvas.before:
            Color(0.05, 0.08, 0.1, 1)
            self.bg = Rectangle(pos=self.pos, size=Window.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        layout = BoxLayout(orientation="vertical", padding=50, spacing=30)
        layout.add_widget(Label(
            text="SELECT CHARACTER", font_size=40, bold=True,
            color=(0.9, 0.95, 1, 1), outline_width=2, outline_color=(0, 0, 0, 1),
            size_hint=(1, 0.2),
        ))

        role_desc = {
            "PTae":    "TANK / AOE\n[AoE Burst]\n[Rockets]",
            "Lostman": "BALANCED / MELEE\n[Axe Torrent]\n[]",
            "Monkey":  "SPEED / GUNNER\n[Pistol + Shotgun]\n[RPG]",
        }

        chars = BoxLayout(spacing=20, size_hint=(1, 0.7))
        for name, stats in self.char_data.items():
            cap = CHAR_SPEED_CAP.get(name, 10.0)
            btn = Button(
                text=(f"[b]{name}[/b]\n\n"
                      f"HP: {stats.hp}\nATK: {stats.damage}\n"
                      f"SPD: {stats.speed} (cap {cap})\n\n"
                      f"{role_desc.get(name,'')}"),
                markup=True, font_size=17, halign="center",
                background_normal="", background_color=(0.1, 0.15, 0.2, 0.85),
                color=(0.85, 0.92, 1, 1),
            )
            btn.bind(on_press=lambda inst, s=stats: self.select_character(s))
            chars.add_widget(btn)
            self.selectable_buttons.append(btn)
        layout.add_widget(chars)

        back_btn = Button(
            text="BACK TO MENU", size_hint=(1, 0.15), font_size=20, bold=True,
            background_normal="", background_color=(0.4, 0.1, 0.1, 0.85),
            color=(1, 0.8, 0.8, 1),
        )
        back_btn.bind(on_press=lambda _: self.go_back(None))
        layout.add_widget(back_btn)
        self.selectable_buttons.append(back_btn)
        self.add_widget(layout)

    def _update_bg(self, i, v): self.bg.pos = i.pos; self.bg.size = i.size

    def select_character(self, stats):
        stats.reset()
        App.get_running_app().current_player = stats
        self.manager.current = "game_screen"

    def go_back(self, _): self.manager.current = "main_menu"

    def on_enter(self):
        Window.bind(on_joy_axis=self._on_joy_axis, on_joy_hat=self._on_joy_hat,
                    on_joy_button_down=self._on_joy_button_down, mouse_pos=self._on_mouse_pos,
                    on_key_down=self._on_keyboard_down)
        self.selected_index = 0; self.show_highlight = False; self.update_highlight()

    def on_leave(self):
        Window.unbind(on_joy_axis=self._on_joy_axis, on_joy_hat=self._on_joy_hat,
                      on_joy_button_down=self._on_joy_button_down, mouse_pos=self._on_mouse_pos,
                      on_key_down=self._on_keyboard_down)

    def _on_keyboard_down(self, window, key, scancode, codepoint, modifiers):
        if key == 119 or key == 97: # W or A
            self.navigate("prev")
            return True
        elif key == 115 or key == 100: # S or D
            self.navigate("next")
            return True
        elif key == 32 or key == 13: # Spacebar or Enter
            self.show_highlight = True
            self.update_highlight()
            if self.selectable_buttons:
                self.selectable_buttons[self.selected_index].dispatch('on_press')
            return True
        return False

    def _on_mouse_pos(self, window, pos):
        for i, btn in enumerate(self.selectable_buttons):
            if btn.collide_point(*pos):
                self.selected_index = i; self.show_highlight = True
                self.update_highlight(); return
        if self.show_highlight: self.show_highlight = False; self.update_highlight()

    def update_highlight(self):
        for i, btn in enumerate(self.selectable_buttons):
            is_back = (i == len(self.selectable_buttons) - 1)
            if i == self.selected_index and self.show_highlight:
                btn.background_color = (0.9, 0.2, 0.2, 1) if is_back else (0.3, 0.5, 0.7, 1)
            else:
                btn.background_color = (0.4, 0.1, 0.1, 0.85) if is_back else (0.1, 0.15, 0.2, 0.85)

    def navigate(self, direction):
        if self.joy_cooldown: return
        self.joy_cooldown = True; self.show_highlight = True
        Clock.schedule_once(lambda _: setattr(self, "joy_cooldown", False), 0.2)
        self.selected_index = (self.selected_index + (1 if direction == "next" else -1)) \
                              % len(self.selectable_buttons)
        self.update_highlight()

    def _on_joy_axis(self, w, stickid, axisid, value):
        if abs(value / 32767.0) > 0.5 and axisid in (0, 1):
            self.navigate("next" if value > 0 else "prev")

    def _on_joy_hat(self, w, stickid, hatid, value):
        x, y = value
        if x == 1 or y == -1: self.navigate("next")
        elif x == -1 or y == 1: self.navigate("prev")

    def _on_joy_button_down(self, w, stickid, buttonid):
        self.show_highlight = True; self.update_highlight()
        if buttonid == 0: self.selectable_buttons[self.selected_index].dispatch("on_press")
        elif buttonid == 1: self.go_back(None)
