"""ui/char_select.py — updated character stats for balance"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Rectangle, Color
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from game.player import PlayerStats
from kivy.app import App
from kivy.animation import Animation
from ui.font import PIXEL_FONT


class CharCard(ButtonBehavior, BoxLayout):
    def __init__(self, name, stats, role_text, on_select, **kwargs):
        super().__init__(orientation="vertical", spacing=10, padding=[10, 15], **kwargs)
        self.name = name
        self.stats = stats
        self._on_select = on_select

        # Background styling
        self.bg_color = (0.1, 0.15, 0.25, 0.85)
        with self.canvas.before:
            self._color = Color(*self.bg_color)
            self._rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_rect, size=self._update_rect)

        # 1. Idle Animation Container
        anim_container = BoxLayout(size_hint_y=0.45, padding=[0, 30, 0, 5])
        self.anim_img = Image(
            source=stats.idle_frames[0],
            allow_stretch=True,
            keep_ratio=True,
            size_hint=(0.8, 0.8),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            color=(0.5, 0.5, 0.5, 0.8) # เริ่มต้นแบบซีดๆ
        )
        anim_container.add_widget(self.anim_img)
        self.add_widget(anim_container)

        # Animation state
        self.frame_idx = 0
        self.frames = stats.idle_frames
        # No initial animation start - only play when highlighted

        # 2. Character Name & Stats Label
        self.stats_lbl = Label(
            text=(f"[size=44][b]{name}[/b][/size]\n\n"
                  f"HP: {stats.hp}  "
                  f"ATK: {stats.damage}\n"
                  f"SPD: {stats.speed}\n\n"
                  f"{role_text}"),
            markup=True,
            font_size=24,
            font_name="PixelFont",
            halign="center",
            valign="middle",
            size_hint_y=0.55,
            color=(0.5, 0.55, 0.6, 0.7) # ตัวอักษรเริ่มต้นแบบซีดๆ
        )
        self.stats_lbl.bind(size=self.stats_lbl.setter("text_size"))
        self.add_widget(self.stats_lbl)

    def _animate(self, dt):
        if not self.frames: return
        self.frame_idx = (self.frame_idx + 1) % len(self.frames)
        self.anim_img.source = self.frames[self.frame_idx]

    def _update_rect(self, inst, val):
        self._rect.pos = inst.pos
        self._rect.size = inst.size

    def on_press(self):
        self._on_select(self.stats)

    def set_highlight(self, active):
        if active:
            # เปลี่ยนสีพื้นหลังและการ์ดทันที (No smooth animation)
            self._color.rgba = (0.3, 0.5, 0.8, 1)
            self.stats_lbl.color = (1, 1, 1, 1)
            
            # ขยายตัวละครทันที (Instant Scale)
            self.anim_img.size_hint = (1.1, 1.1)
            self.anim_img.color = (1, 1, 1, 1)
        else:
            self._color.rgba = self.bg_color
            self.stats_lbl.color = (0.5, 0.55, 0.6, 0.7)
            
            # กลับสู่ขนาดปกติทันที
            self.anim_img.size_hint = (0.8, 0.8)
            self.anim_img.color = (0.5, 0.5, 0.5, 0.6)
        
        # ปิด Sprite Animation (เปลี่ยนเป็นภาพนิ่งเฟรมแรกเสมอ)
        Clock.unschedule(self._animate)
        if self.frames:
            self.anim_img.source = self.frames[0]
            self.frame_idx = 0

class CharacterSelectScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selectable_buttons = []
        self.selected_index = 0
        self.show_highlight = False
        self.joy_cooldown = False

        # ฟ้อนต์ถูก register ไว้แล้วใน ui.font

        from game.skills import CHAR_SPEED_CAP
        self.char_data = {
            "PTae": PlayerStats(
                name="PTae", hp=180, speed=3.0, damage=15,
                idle_frames=["assets/PTae/PTIdle/PTTG1.png","assets/PTae/PTIdle/PTTG2.png"],
                walk_frames=["assets/PTae/PTPushUp/PTaeTester1.png","assets/PTae/PTPushUp/PTaeTester2.png",
                             "assets/PTae/PTPushUp/PTaeTester3.png","assets/PTae/PTPushUp/PTaeTester4.png"],
                heal_small_tex="assets/PTae/skill2/heal_s.png",
                heal_large_tex="assets/PTae/skill2/heal_l.png",
            ),
            "Lostman": PlayerStats(
                name="Lostman", hp=120, speed=4.5, damage=12,
                idle_frames=["assets/Lostman/idle/idleman1.png","assets/Lostman/idle/idleman2.png"],
                walk_frames=["assets/Lostman/walk/walk1.png","assets/Lostman/walk/walk2.png",
                             "assets/Lostman/walk/walk3.png","assets/Lostman/walk/walk4.png"],
                heal_small_tex="assets/Lostman/skill3/heal_s.png",
                heal_large_tex="assets/Lostman/skill3/heal_l.png",
            ),
            "Monkey": PlayerStats(
                name="Monkey", hp=80, speed=6.0, damage=10,
                idle_frames=["assets/Monkey/IdleM/IdleM01.png","assets/Monkey/IdleM/IdleM02.png"],
                walk_frames=["assets/Monkey/WalkM/W01.png","assets/Monkey/WalkM/W02.png",
                             "assets/Monkey/WalkM/W03.png","assets/Monkey/WalkM/W04.png"],
                heal_small_tex="assets/Monkey/Heal/Banana_s1.png",
                heal_large_tex="assets/Monkey/Heal/Banana_s2.png",
            ),
        }

        from kivy.uix.floatlayout import FloatLayout
        from ui.main_menu import RainEffect
        from kivy.uix.widget import Widget
        from kivy.graphics import RoundedRectangle

        # Background Image (อิงตาม MenuTest.png)
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg = Rectangle(source="assets/Menu/MenuTest.png", pos=self.pos, size=Window.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        root_layout = FloatLayout()
        
        # Rain Effect
        self.rain = RainEffect()
        root_layout.add_widget(self.rain)

        # Semi-transparent background panel
        panel = Widget()
        with panel.canvas:
            Color(0.03, 0.05, 0.1, 0.82)
            self._panel_rect = RoundedRectangle(radius=[16])
            Color(0.3, 0.5, 0.7, 0.45)
            self._panel_border = RoundedRectangle(radius=[16])
        root_layout.add_widget(panel)

        # Main Layout inside the panel
        layout = BoxLayout(
            orientation="vertical", padding=[40, 40], spacing=20,
            size_hint=(0.85, 0.85), pos_hint={"center_x": 0.5, "center_y": 0.5}
        )

        def _upd_panel(inst, val):
            pad = 20
            self._panel_rect.pos = (inst.x - pad, inst.y - pad)
            self._panel_rect.size = (inst.width + pad * 2, inst.height + pad * 2)
            self._panel_border.pos = (inst.x - pad - 1, inst.y - pad - 1)
            self._panel_border.size = (inst.width + pad * 2 + 2, inst.height + pad * 2 + 2)
        layout.bind(pos=_upd_panel, size=_upd_panel)

        layout.add_widget(Label(
            text="SELECT CHARACTER", font_size=60, font_name="PixelFont",
            color=(1, 0.85, 0.2, 1),
            size_hint=(1, 0.2),
        ))

        role_desc = {
            "PTae":    "TANK / AOE",
            "Lostman": "BALANCED / MELEE",
            "Monkey":  "SPEED / GUNNER",
        }

        chars = BoxLayout(spacing=25, size_hint=(1, 0.7))
        for name, stats in self.char_data.items():
            card = CharCard(
                name=name,
                stats=stats,
                role_text=role_desc.get(name, ""),
                on_select=self.select_character,
                size_hint_x=1
            )
            chars.add_widget(card)
            self.selectable_buttons.append(card)
        layout.add_widget(chars)

        back_btn = Button(
            text="< BACK TO MENU", size_hint=(1, 0.12), font_size=28, bold=True, font_name="PixelFont",
            background_normal="", background_color=(0.4, 0.1, 0.1, 0.85),
            color=(1, 0.8, 0.8, 1),
        )
        back_btn.bind(on_press=lambda _: self.go_back(None))
        layout.add_widget(back_btn)
        self.selectable_buttons.append(back_btn)
        
        root_layout.add_widget(layout)
        
        # 🌟 Black Fade Overlay (ซ่อนไว้เริ่มต้น)
        self.fade_overlay = Widget(size_hint=(1, 1), opacity=0)
        with self.fade_overlay.canvas:
            Color(0, 0, 0, 1)
            self.fade_rect = Rectangle(pos=self.pos, size=Window.size)
        self.bind(size=self._update_fade_rect, pos=self._update_fade_rect)
        
        root_layout.add_widget(self.fade_overlay)
        self.add_widget(root_layout)

    def _update_fade_rect(self, inst, val):
        self.fade_rect.size = Window.size
        self.fade_rect.pos = self.pos

    def _update_bg(self, i, v): self.bg.pos = i.pos; self.bg.size = i.size

    def select_character(self, stats):
        # 1. ปิด Input กันกดซ้ำ
        Window.unbind(on_joy_axis=self._on_joy_axis, on_joy_hat=self._on_joy_hat,
                      on_joy_button_down=self._on_joy_button_down, mouse_pos=self._on_mouse_pos,
                      on_key_down=self._on_keyboard_down)
        
        # 2. Fade to Black
        anim = Animation(opacity=1, duration=0.6, t='in_quad')
        
        def on_fade_done(*args):
            # 3. เตรียม Stats และเปลี่ยนจอตอนหน้าจอดำสนิท
            stats.reset()
            App.get_running_app().current_player = stats
            self.manager.current = "game_screen"
            
            # 4. Fade out กลับมาใส (และย้ายกลับมาที่หน้าจอเดิมในเบื้องหลัง)
            Clock.schedule_once(lambda dt: self._fade_out_overlay(), 0.1)

        anim.bind(on_complete=on_fade_done)
        anim.start(self.fade_overlay)

    def _fade_out_overlay(self):
        # ทำให้ overlay จางหายไป
        anim = Animation(opacity=0, duration=0.6, t='out_quad')
        anim.start(self.fade_overlay)

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
            active = (i == self.selected_index and self.show_highlight)
            
            if isinstance(btn, CharCard):
                btn.set_highlight(active)
            else:
                if active:
                    btn.background_color = (0.9, 0.2, 0.2, 1)
                    btn.color = (1, 1, 1, 1)
                else:
                    btn.background_color = (0.4, 0.1, 0.1, 0.85)
                    btn.color = (0.8, 0.8, 0.8, 1)

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
