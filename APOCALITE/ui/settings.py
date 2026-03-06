"""
ui/settings.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SettingsPopup — หน้าต่างตั้งค่า (เรียกได้จากทั้ง Main Menu และ Pause)
มี 4 แท็บ:
  🔊 Audio    — BGM volume, SFX volume
  🎮 Controls — Key rebinding
  🖥️ Display  — Fullscreen, Camera Shake
  ⚙️ Gameplay — ตั้งค่าความยากและการแสดงผล
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Rectangle, RoundedRectangle, Ellipse
from kivy.core.window import Window
from kivy.clock import Clock

from game.game_settings import settings


# ─── Helper: สร้าง styled label ──────────────────────────────
def _lbl(text, font_size=16, color=(0.9, 0.9, 0.9, 1), bold=False, halign="left", **kw):
    l = Label(text=text, font_size=font_size, color=color, bold=bold,
               markup=True, halign=halign, **kw)
    l.bind(size=lambda inst, v: setattr(inst, "text_size", (v[0], None)))
    return l


# ─── Helper: Section Divider ─────────────────────────────────
def _divider():
    w = Label(text="─" * 60, color=(0.3, 0.3, 0.35, 1), font_size=12,
               size_hint_y=None, height=20)
    return w


# ─── Volume Row ──────────────────────────────────────────────
class VolumeRow(BoxLayout):
    def __init__(self, label_text, initial_value, on_change, icon="🔊", **kw):
        super().__init__(orientation="horizontal", size_hint_y=None, height=60,
                         spacing=20, padding=[10, 5], **kw)
        
        # Label
        self.add_widget(_lbl(f"{icon} {label_text}", font_size=18, size_hint_x=0.4, color=(0.8, 0.9, 1, 1)))

        # Slider with native modern styling
        self.slider = Slider(
            min=0.0, max=1.0, value=initial_value,
            step=0.01, size_hint_x=0.45,
            value_track=True, 
            value_track_color=(0.2, 0.7, 1.0, 1),
            cursor_size=(24, 24)
        )
        
        # Value Label
        self.val_lbl = _lbl(f"{int(initial_value * 100)}%", font_size=16,
                             color=(0.3, 1, 0.9, 1), size_hint_x=0.15,
                             halign="right", bold=True)

        def _update(inst, val):
            self.val_lbl.text = f"{int(val * 100)}%"
            on_change(val)

        self.slider.bind(value=_update)
        self.add_widget(self.slider)
        self.add_widget(self.val_lbl)


# ─── Toggle Row ──────────────────────────────────────────────
class ToggleRow(BoxLayout):
    def __init__(self, label_text, initial_state, on_change, **kw):
        super().__init__(orientation="horizontal", size_hint_y=None, height=48,
                         spacing=12, **kw)
        self.add_widget(_lbl(label_text, font_size=16, size_hint_x=0.7))

        self.btn = ToggleButton(
            text="ON" if initial_state else "OFF",
            state="down" if initial_state else "normal",
            size_hint_x=0.3,
            background_normal="",
            background_color=(0.2, 0.6, 0.3, 1) if initial_state else (0.4, 0.15, 0.15, 1),
            bold=True, font_size=15,
        )

        def _toggle(inst):
            active = inst.state == "down"
            inst.text = "ON" if active else "OFF"
            inst.background_color = (0.2, 0.6, 0.3, 1) if active else (0.4, 0.15, 0.15, 1)
            on_change(active)

        self.btn.bind(on_press=_toggle)
        self.add_widget(self.btn)


# ─── Key Bind Row ─────────────────────────────────────────────
class KeyBindRow(BoxLayout):
    """แถวสำหรับแสดงและเปลี่ยน key binding"""
    _listening_row = None  # ติดตาม row ที่กำลัง listen

    def __init__(self, action_key, popup_ref, **kw):
        super().__init__(orientation="horizontal", size_hint_y=None, height=48,
                         spacing=10, **kw)
        self.action_key = action_key
        self.popup_ref = popup_ref

        display_name = settings.KEY_DISPLAY_NAMES.get(action_key, action_key)
        self.add_widget(_lbl(display_name, font_size=15, size_hint_x=0.55))

        current_key = settings.key_bindings.get(action_key, "?")
        self.key_btn = Button(
            text=self._format_key(current_key),
            size_hint_x=0.35,
            background_normal="",
            background_color=(0.15, 0.2, 0.3, 1),
            color=(0.9, 0.95, 1, 1),
            font_size=14, bold=True,
        )
        self.key_btn.bind(on_press=self._start_listening)
        self.add_widget(self.key_btn)

        # ปุ่ม Reset
        reset_btn = Button(
            text="↺", size_hint_x=0.1,
            font_size=18,
            background_normal="",
            background_color=(0.3, 0.2, 0.05, 1),
            color=(1, 0.8, 0.3, 1),
        )
        reset_btn.bind(on_press=self._reset_key)
        self.add_widget(reset_btn)

    def _format_key(self, key):
        KEY_ICONS = {
            "space": "SPACE", "lmb": "CLICK", "rmb": "RCLICK",
            "escape": "ESC", "tab": "TAB",
        }
        return KEY_ICONS.get(key, key.upper())

    def _start_listening(self, inst):
        # ยกเลิก row เก่าก่อน
        if KeyBindRow._listening_row and KeyBindRow._listening_row is not self:
            KeyBindRow._listening_row._cancel_listening()
        KeyBindRow._listening_row = self
        self.key_btn.text = "[ กดปุ่มใหม่... ]"
        self.key_btn.background_color = (0.5, 0.3, 0.05, 1)
        self.key_btn.color = (1, 1, 0.5, 1)
        Window.bind(on_key_down=self._on_key_press)

    def _cancel_listening(self):
        KeyBindRow._listening_row = None
        current_key = settings.key_bindings.get(self.action_key, "?")
        self.key_btn.text = self._format_key(current_key)
        self.key_btn.background_color = (0.15, 0.2, 0.3, 1)
        self.key_btn.color = (0.9, 0.95, 1, 1)
        Window.unbind(on_key_down=self._on_key_press)

    def _on_key_press(self, window, key, scancode, codepoint, modifiers):
        from kivy.core.window import Keyboard
        key_name = None

        if key == 27:
            self._cancel_listening()
            return True

        # แปลง key code → ชื่อปุ่ม
        SPECIAL = {
            32: "space", 13: "enter", 9: "tab",
            8: "backspace", 281: "pageup", 280: "pagedown",
        }
        if key in SPECIAL:
            key_name = SPECIAL[key]
        elif codepoint and codepoint.isalnum():
            key_name = codepoint.lower()
        elif codepoint:
            key_name = codepoint.lower()
        else:
            key_name = str(key)

        settings.key_bindings[self.action_key] = key_name
        settings.save()
        self.key_btn.text = self._format_key(key_name)
        self.key_btn.background_color = (0.1, 0.4, 0.2, 1)
        self.key_btn.color = (0.5, 1, 0.6, 1)
        Clock.schedule_once(lambda dt: self._finish_listening(), 0.5)
        Window.unbind(on_key_down=self._on_key_press)
        KeyBindRow._listening_row = None
        return True

    def _finish_listening(self):
        current_key = settings.key_bindings.get(self.action_key, "?")
        self.key_btn.text = self._format_key(current_key)
        self.key_btn.background_color = (0.15, 0.2, 0.3, 1)
        self.key_btn.color = (0.9, 0.95, 1, 1)

    def _reset_key(self, inst):
        default = settings.DEFAULT_KEYS.get(self.action_key, "?")
        settings.key_bindings[self.action_key] = default
        settings.save()
        self.key_btn.text = self._format_key(default)
        self.key_btn.background_color = (0.15, 0.2, 0.3, 1)
        self.key_btn.color = (0.9, 0.95, 1, 1)


# ─── SettingsPopup (Main) ─────────────────────────────────────
class SettingsScreen(Screen):
    """
    หน้าจอตั้งค่าแบบเรียบง่าย มีเฉพาะการปรับระดับเสียงตามคำขอ
    """
    def __init__(self, **kw):
        super().__init__(**kw)
        self._previous_screen = "main_menu"
        self._build()

    def set_previous_screen(self, screen_name):
        self._previous_screen = screen_name

    def _build(self):
        # ─── พื้นหลัง (Layered Deep Blue) ───
        root = FloatLayout()
        with root.canvas.before:
            # Gradient-ish deep background
            Color(0.02, 0.03, 0.08, 1)
            Rectangle(pos=root.pos, size=root.size)
            # Subtle glow spots
            Color(0.1, 0.3, 0.5, 0.15)
            self._glow_spot = Ellipse(size=(800, 800))
            
            # Center Panel (Glassmorphism)
            Color(0.1, 0.15, 0.25, 0.7)
            self._bg_rect = RoundedRectangle(radius=[24])
            
            # Glowing Border
            Color(0.2, 0.8, 1, 0.3)
            self._border_rect = RoundedRectangle(radius=[24], width=2)
            
        root.bind(pos=self._update_bg, size=self._update_bg)

        # ─── Main Content Container ───
        self.main_container = BoxLayout(orientation="vertical", padding=50, spacing=35, opacity=0)
        
        # Header with neon title
        header = BoxLayout(size_hint_y=None, height=70, spacing=15)
        title_box = BoxLayout(orientation="vertical")
        title_box.add_widget(_lbl("[b]AUDIO CONTROL[/b]", font_size=36,
                                  color=(0.3, 0.9, 1, 1), halign="left"))
        title_box.add_widget(_lbl("CONFIGURE GAME SOUND AND EFFECTS", font_size=12,
                                  color=(0.5, 0.6, 0.8, 1), halign="left"))
        
        close_btn = Button(
            text="✕", size_hint=(None, None), size=(55, 55),
            background_normal="", background_color=(0, 0, 0, 0),
            color=(0.8, 0.8, 0.9, 1), font_size=28, bold=True,
        )
        # Custom close button background
        with close_btn.canvas.before:
            Color(0.3, 0.1, 0.1, 0.5)
            self._close_bg = RoundedRectangle(pos=close_btn.pos, size=close_btn.size, radius=[12])
        close_btn.bind(pos=self._update_close_btn, size=self._update_close_btn)
        close_btn.bind(on_press=lambda x: self._close())
        
        header.add_widget(title_box)
        header.add_widget(close_btn)

        # Content Section
        content = BoxLayout(orientation="vertical", spacing=25, size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        def set_music(v):
            settings.music_volume = v
            settings.save()

        def set_sfx(v):
            settings.sfx_volume = v
            settings.save()

        # Audio Section Header
        content.add_widget(_lbl("[b]VOLUME LEVELS[/b]", font_size=16, color=(0.4, 0.5, 0.7, 1)))
        
        # Rows with icons
        content.add_widget(VolumeRow("Background Music", settings.music_volume, set_music, icon="🎵"))
        content.add_widget(VolumeRow("Sound Effects", settings.sfx_volume, set_sfx, icon="💥"))

        # Footer
        footer = _lbl("SETTINGS ARE APPLIED AND SAVED AUTOMATICALLY",
                      font_size=12, color=(0.4, 0.4, 0.5, 1), halign="center",
                      size_hint_y=None, height=50)

        self.main_container.add_widget(header)
        self.main_container.add_widget(content)
        self.main_container.add_widget(BoxLayout()) # Spacer
        self.main_container.add_widget(footer)

        root.add_widget(self.main_container)
        self.add_widget(root)
        
        # Entrance Animation
        from kivy.animation import Animation
        anim = Animation(opacity=1, duration=0.6, t='out_quad')
        Clock.schedule_once(lambda dt: anim.start(self.main_container), 0.1)

    def _update_bg(self, inst, val):
        pad = 40
        self._bg_rect.pos = (inst.x + pad, inst.y + pad)
        self._bg_rect.size = (inst.width - pad*2, inst.height - pad*2)
        self._border_rect.pos = self._bg_rect.pos
        self._border_rect.size = self._bg_rect.size
        self._glow_spot.pos = (inst.center_x - 400, inst.center_y - 400)

    def _update_close_btn(self, inst, val):
        if hasattr(self, '_close_bg'):
            self._close_bg.pos = inst.pos
            self._close_bg.size = inst.size


    def _close(self):
        settings.save()
        if self.manager:
            self.manager.current = self._previous_screen
