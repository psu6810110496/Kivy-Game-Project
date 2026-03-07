"""
ui/settings.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SettingsScreen — หน้าต่างตั้งค่าสไตล์ Pixel / Apocalypse
เข้ากับ Theme ของ Main Menu (PixelFont, สีฝน, พื้นหลังเดียวกัน)
มี 2 แท็บหลัก:
  🔊 AUDIO    — ปรับระดับเสียง
  ⚙️ GAMEPLAY — ตั้งค่าการแสดงผลและระบบเกม
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.core.text import LabelBase
import random
from game.sound_manager import sound_manager
from game.game_settings import settings


# ─── Register Pixel Font ─────────────────────────────────────
try:
    LabelBase.register(
        name="PixelFont",
        fn_regular="assets/fornt/Stacked pixel.ttf",
    )
    _PIXEL_FONT = "PixelFont"
except Exception:
    _PIXEL_FONT = "Roboto"


# ─── Rain Effect (ใช้ซ้ำจาก main_menu) ───────────────────────
class RainEffect(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.drops = []
        self.num_drops = 100

        with self.canvas:
            Color(0.7, 0.8, 0.9, 0.25)
            for _ in range(self.num_drops):
                rect = Rectangle(
                    pos=(
                        random.uniform(-Window.width * 0.5, Window.width),
                        random.uniform(0, Window.height),
                    ),
                    size=(1.5, random.uniform(12, 28)),
                )
                drop = {"rect": rect, "speed": random.uniform(10, 18)}
                self.drops.append(drop)

        Clock.schedule_interval(self.update_rain, 1 / 60.0)

    def update_rain(self, dt):
        for drop in self.drops:
            x, y = drop["rect"].pos
            y -= drop["speed"]
            x += drop["speed"] * 0.15
            if y < -50 or x > Window.width:
                y = Window.height + random.uniform(10, 80)
                x = random.uniform(-Window.width * 0.2, Window.width)
            drop["rect"].pos = (x, y)


# ─── Helper: Pixel-styled label ──────────────────────────────
def _lbl(text, font_size=16, color=(0.85, 0.9, 1, 1), bold=False,
         halign="left", font_name=None, **kw):
    fn = font_name or "Roboto"
    l = Label(text=text, font_size=font_size, color=color, bold=bold,
               markup=True, halign=halign, font_name=fn, **kw)
    l.bind(size=lambda inst, v: setattr(inst, "text_size", (v[0], None)))
    return l


def _pixel_lbl(text, font_size=20, color=(0.85, 0.9, 1, 1), halign="left", **kw):
    l = Label(text=text, font_size=font_size, color=color,
               markup=True, halign=halign, font_name=_PIXEL_FONT, **kw)
    l.bind(size=lambda inst, v: setattr(inst, "text_size", (v[0], None)))
    return l


# ─── Pixel Section Header ─────────────────────────────────────
def _section_header(text, color=(0.6, 0.85, 1, 1)):
    box = BoxLayout(size_hint_y=None, height=50, padding=[0, 5])
    lbl = _pixel_lbl(f"[ {text} ]", font_size=22, color=color)
    box.add_widget(lbl)
    return box


# ─── Pixel Divider ───────────────────────────────────────────
def _divider():
    w = Widget(size_hint_y=None, height=2)
    with w.canvas:
        Color(0.3, 0.4, 0.55, 0.6)
        w._line = Line(points=[], width=1)
    def _upd(inst, val):
        inst._line.points = [inst.x, inst.center_y, inst.right, inst.center_y]
    w.bind(pos=_upd, size=_upd)
    return w


# ─── VolumeRow: Pixel Style ──────────────────────────────────
class VolumeRow(BoxLayout):
    def __init__(self, label_text, initial_value, on_change, icon="♪", **kw):
        super().__init__(orientation="horizontal", size_hint_y=None, height=64,
                         spacing=16, padding=[10, 4], **kw)

        # Draw subtle row bg
        with self.canvas.before:
            Color(0.1, 0.15, 0.22, 0.0)
            self._row_bg = RoundedRectangle(radius=[6])
        self.bind(pos=self._upd_bg, size=self._upd_bg)

        # Icon + Name
        self.name_lbl = _pixel_lbl(f"{icon}  {label_text}", font_size=18,
                                    color=(1, 1, 1, 1), size_hint_x=0.42)
        self.add_widget(self.name_lbl)

        # Slider
        self.slider = Slider(
            min=0.0, max=1.0, value=initial_value,
            step=0.01, size_hint_x=0.43,
            value_track=True,
            value_track_color=(0.4, 0.75, 1, 1),
            cursor_size=(20, 20),
        )

        # Value label — PixelFont เหมือนกัน
        self.val_lbl = _pixel_lbl(f"{int(initial_value * 100)}%", font_size=18,
                                   color=(0.5, 1, 0.85, 1), size_hint_x=0.15,
                                   halign="right")

        def _update(inst, val):
            self.val_lbl.text = f"{int(val * 100)}%"
            on_change(val)

        self.slider.bind(value=_update)
        self.add_widget(self.slider)
        self.add_widget(self.val_lbl)

    def _upd_bg(self, inst, val):
        self._row_bg.pos = inst.pos
        self._row_bg.size = inst.size

    def set_focus(self, active):
        if active:
            self.name_lbl.color = (1, 1, 0.4, 1)
            self.val_lbl.color = (0.4, 1, 0.7, 1)
            self.slider.value_track_color = (0.3, 1, 0.6, 1)
        else:
            self.name_lbl.color = (1, 1, 1, 1)
            self.val_lbl.color = (0.5, 1, 0.85, 1)
            self.slider.value_track_color = (0.4, 0.75, 1, 1)

    def trigger(self, buttonid):
        pass

    def adjust(self, amount):
        self.slider.value = max(0.0, min(1.0, self.slider.value + amount))


# ─── ToggleRow: Pixel Style ──────────────────────────────────
class ToggleRow(BoxLayout):
    def __init__(self, label_text, initial_state, on_change, **kw):
        super().__init__(orientation="horizontal", size_hint_y=None, height=52,
                         spacing=16, padding=[10, 4], **kw)

        self._is_focused = False

        self.name_lbl = _lbl(label_text, font_size=17,
                              color=(0.8, 0.88, 1, 0.9), size_hint_x=0.7)
        self.add_widget(self.name_lbl)

        # Custom pixel toggle button
        self._state = initial_state
        self.toggle_lbl = _pixel_lbl(
            "[  ON  ]" if initial_state else "[  OFF  ]",
            font_size=17,
            color=(0.3, 1, 0.6, 1) if initial_state else (0.6, 0.3, 0.3, 1),
            size_hint_x=0.3,
            halign="right",
        )

        def _do_toggle(inst, touch):
            if inst.collide_point(*touch.pos):
                self._state = not self._state
                self.toggle_lbl.text = "[  ON  ]" if self._state else "[  OFF  ]"
                self._update_toggle_color()
                on_change(self._state)
                return True
            return False

        self.toggle_lbl.bind(on_touch_down=_do_toggle)
        self._on_change = on_change
        self.add_widget(self.toggle_lbl)

    def _update_toggle_color(self):
        if self._state:
            self.toggle_lbl.color = (0.3, 1, 0.6, 1) if not self._is_focused else (0.5, 1, 0.5, 1)
        else:
            self.toggle_lbl.color = (0.6, 0.3, 0.3, 1) if not self._is_focused else (1, 0.5, 0.5, 1)

    def set_focus(self, active):
        self._is_focused = active
        if active:
            self.name_lbl.color = (1, 1, 0.5, 1)
        else:
            self.name_lbl.color = (0.8, 0.88, 1, 0.9)
        self._update_toggle_color()

    def trigger(self, buttonid):
        if buttonid == 0:
            self._state = not self._state
            self.toggle_lbl.text = "[  ON  ]" if self._state else "[  OFF  ]"
            self._update_toggle_color()
            self._on_change(self._state)


# ─── KeyBindRow ───────────────────────────────────────────────
class KeyBindRow(BoxLayout):
    _listening_row = None

    def __init__(self, action_key, popup_ref, **kw):
        super().__init__(orientation="horizontal", size_hint_y=None, height=50,
                         spacing=10, padding=[10, 2], **kw)
        self.action_key = action_key
        self.popup_ref = popup_ref

        display_name = settings.KEY_DISPLAY_NAMES.get(action_key, action_key)
        self.add_widget(_lbl(display_name, font_size=16,
                              color=(0.75, 0.85, 1, 0.9), size_hint_x=0.55))

        current_key = settings.key_bindings.get(action_key, "?")
        self.key_btn = Button(
            text=self._format_key(current_key),
            size_hint_x=0.35,
            background_normal="",
            background_color=(0.1, 0.18, 0.3, 1),
            color=(0.85, 0.95, 1, 1),
            font_size=14, bold=True,
        )
        self.key_btn.bind(on_press=self._start_listening)
        self.add_widget(self.key_btn)

        reset_btn = Button(
            text="↺", size_hint_x=0.1,
            font_size=16,
            background_normal="",
            background_color=(0.2, 0.15, 0.05, 1),
            color=(1, 0.75, 0.2, 1),
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
        if KeyBindRow._listening_row and KeyBindRow._listening_row is not self:
            KeyBindRow._listening_row._cancel_listening()
        KeyBindRow._listening_row = self
        self.key_btn.text = "[ กด... ]"
        self.key_btn.background_color = (0.4, 0.25, 0.05, 1)
        self.key_btn.color = (1, 1, 0.4, 1)
        Window.bind(on_key_down=self._on_key_press)

    def _cancel_listening(self):
        KeyBindRow._listening_row = None
        current_key = settings.key_bindings.get(self.action_key, "?")
        self.key_btn.text = self._format_key(current_key)
        self.key_btn.background_color = (0.1, 0.18, 0.3, 1)
        self.key_btn.color = (0.85, 0.95, 1, 1)
        Window.unbind(on_key_down=self._on_key_press)

    def _on_key_press(self, window, key, scancode, codepoint, modifiers):
        if key == 27:
            self._cancel_listening()
            return True
        SPECIAL = {32: "space", 13: "enter", 9: "tab", 8: "backspace"}
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
        self.key_btn.background_color = (0.05, 0.3, 0.15, 1)
        self.key_btn.color = (0.4, 1, 0.5, 1)
        Clock.schedule_once(lambda dt: self._finish_listening(), 0.5)
        Window.unbind(on_key_down=self._on_key_press)
        KeyBindRow._listening_row = None
        return True

    def _finish_listening(self):
        current_key = settings.key_bindings.get(self.action_key, "?")
        self.key_btn.text = self._format_key(current_key)
        self.key_btn.background_color = (0.1, 0.18, 0.3, 1)
        self.key_btn.color = (0.85, 0.95, 1, 1)

    def _reset_key(self, inst):
        default = settings.DEFAULT_KEYS.get(self.action_key, "?")
        settings.key_bindings[self.action_key] = default
        settings.save()
        self.key_btn.text = self._format_key(default)
        self.set_focus(getattr(self, '_is_focused', False))

    def set_focus(self, active):
        self._is_focused = active
        self.key_btn.background_color = (0.15, 0.35, 0.55, 1) if active else (0.1, 0.18, 0.3, 1)

    def trigger(self, buttonid):
        if buttonid == 0:
            self._start_listening(None)
        elif buttonid == 2:
            self._reset_key(None)


# ─── JoyBindRow ───────────────────────────────────────────────
class JoyBindRow(BoxLayout):
    _listening_row = None

    def __init__(self, action_key, popup_ref, **kw):
        super().__init__(orientation="horizontal", size_hint_y=None, height=50,
                         spacing=10, padding=[10, 2], **kw)
        self.action_key = action_key
        self.popup_ref = popup_ref

        display_name = settings.KEY_DISPLAY_NAMES.get(action_key, action_key)
        self.add_widget(_lbl(display_name, font_size=16,
                              color=(0.75, 0.85, 1, 0.9), size_hint_x=0.55))

        current_key = settings.joy_bindings.get(action_key, "?")
        self.key_btn = Button(
            text=self._format_key(current_key),
            size_hint_x=0.35,
            background_normal="",
            background_color=(0.2, 0.1, 0.28, 1),
            color=(0.9, 0.85, 1, 1),
            font_size=14, bold=True,
        )
        self.key_btn.bind(on_press=self._start_listening)
        self.add_widget(self.key_btn)

        reset_btn = Button(
            text="↺", size_hint_x=0.1,
            font_size=16,
            background_normal="",
            background_color=(0.2, 0.15, 0.05, 1),
            color=(1, 0.75, 0.2, 1),
        )
        reset_btn.bind(on_press=self._reset_key)
        self.add_widget(reset_btn)

    def _format_key(self, key):
        JOY_ICONS = {
            "0": "A / Cross", "1": "B / Circle", "2": "X / Square",
            "3": "Y / Triangle", "4": "LB / L1", "5": "RB / R1",
            "6": "Back / Select", "7": "Start / Options",
        }
        return JOY_ICONS.get(str(key), f"Joy Btn {key}")

    def _start_listening(self, inst):
        if JoyBindRow._listening_row and JoyBindRow._listening_row is not self:
            JoyBindRow._listening_row._cancel_listening()
        JoyBindRow._listening_row = self
        self.key_btn.text = "[ กดจอย... ]"
        self.key_btn.background_color = (0.4, 0.05, 0.25, 1)
        self.key_btn.color = (1, 0.7, 0.8, 1)
        Window.bind(on_joy_button_down=self._on_joy_button_down)

    def _cancel_listening(self):
        JoyBindRow._listening_row = None
        current_key = settings.joy_bindings.get(self.action_key, "?")
        self.key_btn.text = self._format_key(current_key)
        self.key_btn.background_color = (0.2, 0.1, 0.28, 1)
        self.key_btn.color = (0.9, 0.85, 1, 1)
        Window.unbind(on_joy_button_down=self._on_joy_button_down)

    def _on_joy_button_down(self, window, stickid, buttonid):
        key_name = str(buttonid)
        settings.joy_bindings[self.action_key] = key_name
        settings.save()
        self.key_btn.text = self._format_key(key_name)
        self.key_btn.background_color = (0.3, 0.05, 0.35, 1)
        self.key_btn.color = (1, 0.4, 0.9, 1)
        Clock.schedule_once(lambda dt: self._finish_listening(), 0.5)
        Window.unbind(on_joy_button_down=self._on_joy_button_down)
        JoyBindRow._listening_row = None
        return True

    def _finish_listening(self):
        current_key = settings.joy_bindings.get(self.action_key, "?")
        self.key_btn.text = self._format_key(current_key)
        self.key_btn.background_color = (0.2, 0.1, 0.28, 1)
        self.key_btn.color = (0.9, 0.85, 1, 1)

    def _reset_key(self, inst):
        default = settings.DEFAULT_JOY_KEYS.get(self.action_key, "?")
        settings.joy_bindings[self.action_key] = default
        settings.save()
        self.key_btn.text = self._format_key(default)
        self.set_focus(getattr(self, '_is_focused', False))

    def set_focus(self, active):
        self._is_focused = active
        self.key_btn.background_color = (0.3, 0.2, 0.45, 1) if active else (0.2, 0.1, 0.28, 1)

    def trigger(self, buttonid):
        if buttonid == 0:
            if not JoyBindRow._listening_row:
                self._start_listening(None)
        elif buttonid == 2:
            self._reset_key(None)


# ─── Pixel Tab Button ────────────────────────────────────────
class PixelTabLabel(Label):
    """
    Tab ที่เป็น Label แบบ Pixel ไม่มีปุ่มกด
    Highlight ด้วยการเปลี่ยนสีและขีดล่าง
    """
    def __init__(self, text, tab_id, on_select, **kw):
        super().__init__(
            text=text,
            font_name=_PIXEL_FONT,
            font_size=22,
            color=(0.65, 0.65, 0.65, 1),
            markup=True,
            halign="center",
            size_hint_x=1,
            **kw
        )
        self.tab_id = tab_id
        self._on_select = on_select
        self._active = False
        self._base_color = (0.65, 0.65, 0.65, 1)   # ขาวหรี่ — inactive
        self.bind(size=self.setter("text_size"))
        self.bind(on_touch_down=self._on_touch)

    def _on_touch(self, inst, touch):
        if self.collide_point(*touch.pos):
            self._on_select(self.tab_id)
            return True
        return False

    def set_active(self, active):
        self._active = active
        if active:
            self.color = (1, 1, 1, 1)       # ขาวสว่างเต็ม — active
            self.font_size = 25
        else:
            self.color = self._base_color    # ขาวหรี่ — inactive
            self.font_size = 22

    def set_focus(self, active):
        if self._active:
            self.color = (1, 1, 0.4, 1) if active else (1, 1, 1, 1)
        else:
            self.color = (1, 1, 0.5, 1) if active else self._base_color


# ─── SettingsScreen ──────────────────────────────────────────
class SettingsScreen(Screen):
    """
    หน้าจอตั้งค่า Pixel Apocalypse Style
    พื้นหลัง MenuTest.png + Rain Effect + PixelFont
    """

    def __init__(self, **kw):
        super().__init__(**kw)
        self._previous_screen = "main_menu"
        self._current_tab = "audio"
        self.focusable_widgets = []
        self.selected_index = 0
        self.joy_cooldown = False
        self.show_highlight = False  # เหมือน main_menu / pause
        self._build()

    def set_previous_screen(self, screen_name):
        self._previous_screen = screen_name

    def on_enter(self):
        self.root_float.opacity = 0
        Animation(opacity=1, duration=0.35, t="out_quad").start(self.root_float)
        self.switch_tab(self._current_tab)
        self.selected_index = 0
        self.show_highlight = False
        self.update_highlight()
        Window.bind(
            on_joy_axis=self._on_joy_axis,
            on_joy_hat=self._on_joy_hat,
            on_joy_button_down=self._on_joy_button_down,
            on_key_down=self._on_keyboard_down,
            mouse_pos=self._on_mouse_pos,
        )

    def on_leave(self):
        Window.unbind(
            on_joy_axis=self._on_joy_axis,
            on_joy_hat=self._on_joy_hat,
            on_joy_button_down=self._on_joy_button_down,
            on_key_down=self._on_keyboard_down,
            mouse_pos=self._on_mouse_pos,
        )

    # ─── BUILD ───────────────────────────────────────────────
    def _build(self):
        # ══ Background: MenuTest.png ══
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._bg_rect = Rectangle(
                source="assets/Menu/MenuTest.png",
                pos=self.pos,
                size=Window.size,
            )
        self.bind(pos=self._update_bg, size=self._update_bg)

        self.root_float = FloatLayout()

        # ══ Rain Effect ══
        self.rain = RainEffect()
        self.root_float.add_widget(self.rain)

        # ══ Semi-transparent Dark Panel ══
        panel_widget = Widget()
        with panel_widget.canvas:
            Color(0.03, 0.05, 0.1, 0.82)
            self._panel_rect = RoundedRectangle(radius=[16])

            # Panel border
            Color(0.3, 0.5, 0.7, 0.45)
            self._panel_border = RoundedRectangle(radius=[16])

        panel_widget.bind(pos=self._upd_panel, size=self._upd_panel)

        # ══ Main Layout (absolute positioned) ══
        self.main_box = BoxLayout(
            orientation="vertical",
            padding=[50, 40],
            spacing=0,
            size_hint=(0.72, 0.88),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )

        # ── HEADER ────────────────────────────────────────────
        header = BoxLayout(size_hint_y=None, height=80, spacing=20,
                           padding=[0, 0, 0, 10])

        # Back / Close label (เหมือน style main menu)
        self.close_lbl = _pixel_lbl(
            "< BACK", font_size=22,
            color=(0.6, 0.7, 0.85, 1),
            size_hint_x=None, width=160,
        )
        self.close_lbl._base_color = (0.6, 0.7, 0.85, 1)
        self.close_lbl._is_close = True

        def _close_touch(inst, touch):
            if inst.collide_point(*touch.pos):
                self._close()
                return True
            return False
        self.close_lbl.bind(on_touch_down=_close_touch)

        # Title
        title_lbl = _pixel_lbl(
            "SETTINGS",
            font_size=52,
            color=(1, 1, 1, 1),
            halign="left",
            size_hint_x=1,
        )

        header.add_widget(title_lbl)
        header.add_widget(self.close_lbl)

        # ── TAB ROW ───────────────────────────────────────────
        tab_row = BoxLayout(size_hint_y=None, height=52, spacing=30,
                            padding=[0, 8, 0, 8])

        self.tab_labels = {}
        tabs = [("audio", "AUDIO"), ("gameplay", "GAMEPLAY")]
        for tab_id, tab_text in tabs:
            tl = PixelTabLabel(tab_text, tab_id, self.switch_tab)
            self.tab_labels[tab_id] = tl
            tab_row.add_widget(tl)

        # Tab underline divider
        tab_div = _divider()

        # ── CONTENT SCROLL ────────────────────────────────────
        self.content_scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=4,
            bar_color=(0.4, 0.65, 1, 0.7),
            bar_inactive_color=(0.2, 0.35, 0.55, 0.4),
        )
        self.content_box = BoxLayout(
            orientation="vertical",
            spacing=8,
            size_hint_y=None,
            padding=[0, 10, 0, 20],
        )
        self.content_box.bind(minimum_height=self.content_box.setter("height"))
        self.content_scroll.add_widget(self.content_box)

        # ── FOOTER ────────────────────────────────────────────
        footer_box = BoxLayout(size_hint_y=None, height=32)
        footer_lbl = _pixel_lbl(
            "ALL CHANGES SAVED AUTOMATICALLY",
            font_size=13, color=(0.3, 0.4, 0.55, 0.8),
            halign="center",
        )
        footer_box.add_widget(footer_lbl)

        # Assemble
        self.main_box.add_widget(header)
        self.main_box.add_widget(tab_row)
        self.main_box.add_widget(tab_div)
        self.main_box.add_widget(BoxLayout(size_hint_y=None, height=10))
        self.main_box.add_widget(self.content_scroll)
        self.main_box.add_widget(footer_box)

        # Panel is behind content
        self.root_float.add_widget(panel_widget)
        self.root_float.add_widget(self.main_box)

        self.add_widget(self.root_float)

        # bind panel to main_box position
        self.main_box.bind(pos=self._upd_panel_to_box, size=self._upd_panel_to_box)
        self._panel_widget = panel_widget

        self.switch_tab("audio")

    # ─── BG & Panel Updates ──────────────────────────────────
    def _update_bg(self, inst, val):
        self._bg_rect.pos = inst.pos
        self._bg_rect.size = inst.size

    def _upd_panel(self, inst, val):
        pass  # handled via _upd_panel_to_box

    def _upd_panel_to_box(self, inst, val):
        pad = 12
        self._panel_rect.pos = (inst.x - pad, inst.y - pad)
        self._panel_rect.size = (inst.width + pad * 2, inst.height + pad * 2)
        self._panel_border.pos = (inst.x - pad - 1, inst.y - pad - 1)
        self._panel_border.size = (inst.width + pad * 2 + 2, inst.height + pad * 2 + 2)

    # ─── TAB SWITCHING ───────────────────────────────────────
    def switch_tab(self, tab_id):
        self._current_tab = tab_id
        self.content_box.clear_widgets()

        # Update tab styles
        for tid, tl in self.tab_labels.items():
            tl.set_active(tid == tab_id)

        # Build content
        if tab_id == "audio":
            self._build_audio()
        elif tab_id == "gameplay":
            self._build_gameplay()

        # Rebuild focusable list
        self.focusable_widgets = []
        for tid in ["audio", "gameplay"]:
            self.focusable_widgets.append(self.tab_labels[tid])
        for child in reversed(self.content_box.children):
            if hasattr(child, "set_focus"):
                self.focusable_widgets.append(child)
        self.focusable_widgets.append(self.close_lbl)
        self.selected_index = 0
        self.show_highlight = False
        self.update_highlight()

    # ─── HIGHLIGHT ───────────────────────────────────────────
    def update_highlight(self):
        for i, w in enumerate(self.focusable_widgets):
            active = (i == self.selected_index and self.show_highlight)
            if hasattr(w, "set_focus"):
                w.set_focus(active)
            elif isinstance(w, Button):
                w.color = (1, 0.85, 0.2, 1) if active else getattr(w, '_base_color', (1, 1, 1, 1))

    # ─── MOUSE HOVER ─────────────────────────────────────────
    def _on_mouse_pos(self, window, pos):
        for i, w in enumerate(self.focusable_widgets):
            if hasattr(w, "collide_point") and w.collide_point(*pos):
                self.selected_index = i
                self.show_highlight = True
                self.update_highlight()
                return
        if self.show_highlight:
            self.show_highlight = False
            self.update_highlight()

    # ─── NAVIGATE ────────────────────────────────────────────
    def navigate(self, direction):
        if self.joy_cooldown or not self.focusable_widgets:
            return
        self.joy_cooldown = True
        self.show_highlight = True  # ขยับ keyboard/จอย → เปิด highlight
        Clock.schedule_once(lambda dt: setattr(self, "joy_cooldown", False), 0.15)
        if direction == "next":
            self.selected_index = (self.selected_index + 1) % len(self.focusable_widgets)
        elif direction == "prev":
            self.selected_index = (self.selected_index - 1) % len(self.focusable_widgets)
        self.update_highlight()

    def handle_action(self, action, value=0):
        if not self.focusable_widgets:
            return
        self.show_highlight = True
        self.update_highlight()
        w = self.focusable_widgets[self.selected_index]
        if action == "press":
            sound_manager.play_sfx("button")
            if hasattr(w, "trigger"):
                w.trigger(0)
            elif isinstance(w, Button):
                w.dispatch("on_press")
            elif hasattr(w, "_on_select"):
                w._on_select(w.tab_id)
            elif hasattr(w, "_is_close"):
                self._close()
        elif action == "alt_press":
            if hasattr(w, "trigger"):
                w.trigger(2)
        elif action == "adjust":
            if hasattr(w, "adjust"):
                w.adjust(value)

    # ─── INPUT: JOY ──────────────────────────────────────────
    def _on_joy_axis(self, win, stickid, axisid, value):
        normalized = value / 32767.0
        if abs(normalized) > 0.5:
            if axisid == 1:
                if self.joy_cooldown:
                    return
                self.navigate("next" if normalized > 0 else "prev")
            if axisid == 0:
                if self.joy_cooldown:
                    return
                self.joy_cooldown = True
                Clock.schedule_once(lambda dt: setattr(self, "joy_cooldown", False), 0.1)
                self.handle_action("adjust", 0.05 if normalized > 0 else -0.05)

    def _on_joy_hat(self, win, stickid, hatid, value):
        x, y = value
        if y == -1:
            self.navigate("next")
        elif y == 1:
            self.navigate("prev")
        elif x == 1:
            self.handle_action("adjust", 0.05)
        elif x == -1:
            self.handle_action("adjust", -0.05)

    def _on_joy_button_down(self, win, stickid, buttonid):
        self.show_highlight = True  # กดจอย → เปิด highlight
        self.update_highlight()
        if buttonid == 0:
            self.handle_action("press")
        elif buttonid == 1:
            self._close()
        elif buttonid == 2:
            self.handle_action("alt_press")

    # ─── INPUT: KEYBOARD ─────────────────────────────────────
    def _on_keyboard_down(self, window, key, scancode, codepoint, modifiers):
        if key == 27:       # ESC
            self._close(); return True
        elif key in (119, 273):   # W / Up
            self.show_highlight = True
            self.navigate("prev"); return True
        elif key in (115, 274):   # S / Down
            self.show_highlight = True
            self.navigate("next"); return True
        elif key in (97, 276):    # A / Left
            self.show_highlight = True
            self.handle_action("adjust", -0.05); return True
        elif key in (100, 275):   # D / Right
            self.show_highlight = True
            self.handle_action("adjust", 0.05); return True
        elif key in (32, 13):     # Space / Enter
            self.show_highlight = True
            self.handle_action("press"); return True
        return False

    # ─── BUILD CONTENT ───────────────────────────────────────
    def _build_audio(self):
        self.content_box.add_widget(_section_header("VOLUME SETTINGS"))
        self.content_box.add_widget(_divider())
        self.content_box.add_widget(BoxLayout(size_hint_y=None, height=6))

        def music_cb(v):
            settings.music_volume = v
            sound_manager.update_music_volume()
            settings.save()

        def sfx_cb(v):
            settings.sfx_volume = v
            # SFX will scale automatically on next play
            settings.save()

        self.content_box.add_widget(
            VolumeRow("Music Volume", settings.music_volume, music_cb, icon="♪"))
        self.content_box.add_widget(BoxLayout(size_hint_y=None, height=4))
        self.content_box.add_widget(
            VolumeRow("Sound Effects", settings.sfx_volume, sfx_cb, icon="♦"))

    def _build_gameplay(self):
        # ── VIDEO & EFFECTS ──
        self.content_box.add_widget(_section_header("VIDEO  &  EFFECTS"))
        self.content_box.add_widget(_divider())
        self.content_box.add_widget(BoxLayout(size_hint_y=None, height=6))

        def fs_cb(active):
            settings.fullscreen = active
            Window.fullscreen = "auto" if active else False
            settings.save()

        def cam_cb(active):
            settings.camera_shake = active
            settings.save()

        self.content_box.add_widget(
            ToggleRow("Fullscreen Mode", settings.fullscreen, fs_cb))
        self.content_box.add_widget(
            ToggleRow("Camera Shake Effects", settings.camera_shake, cam_cb))

        # ── VISUAL FEEDBACK ──
        self.content_box.add_widget(BoxLayout(size_hint_y=None, height=18))
        self.content_box.add_widget(_section_header("VISUAL FEEDBACK"))
        self.content_box.add_widget(_divider())
        self.content_box.add_widget(BoxLayout(size_hint_y=None, height=6))

        def dmg_cb(active):
            settings.show_damage_numbers = active
            settings.save()

        def hp_cb(active):
            settings.show_enemy_hp = active
            settings.save()

        self.content_box.add_widget(
            ToggleRow("Show Damage Numbers", settings.show_damage_numbers, dmg_cb))
        self.content_box.add_widget(
            ToggleRow("Show Enemy Health Bars", settings.show_enemy_hp, hp_cb))

    # ─── CLOSE ───────────────────────────────────────────────
    def _close(self):
        settings.save()
        if not self.manager:
            return
        target = self._previous_screen
        self.manager.current = target
        if target == "game_screen":
            from ui.pause import PausePopup
            game_screen = self.manager.get_screen("game_screen")
            Clock.schedule_once(lambda dt: PausePopup(game_screen).open(), 0.1)
