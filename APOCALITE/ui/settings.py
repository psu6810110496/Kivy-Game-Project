"""
ui/settings.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SettingsScreen — หน้าต่างตั้งค่าแบบเต็มรูปแบบ (เรียกได้จากทั้ง Main Menu และ Pause)
มี 3 แท็บหลัก:
  🔊 Audio    — ปรับระดับเสียง
  🎮 Controls — เปลี่ยนปุ่มกด (Key Rebinding)
  ⚙️ Gameplay — ตั้งค่าการแสดงผลและระบบเกม
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
from kivy.animation import Animation

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

    def set_focus(self, active):
        self.val_lbl.color = (1, 1, 0, 1) if active else (0.3, 1, 0.9, 1)
        self.slider.value_track_color = (0.2, 0.9, 0.4, 1) if active else (0.2, 0.7, 1.0, 1)

    def trigger(self, buttonid):
        pass

    def adjust(self, amount):
        self.slider.value = max(0.0, min(1.0, self.slider.value + amount))


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
            self.set_focus(getattr(self, '_is_focused', False))
            on_change(active)

        self.btn.bind(on_press=_toggle)
        self.add_widget(self.btn)

    def set_focus(self, active):
        self._is_focused = active
        is_on = self.btn.state == "down"
        if active:
            self.btn.background_color = (0.3, 0.8, 0.4, 1) if is_on else (0.6, 0.3, 0.3, 1)
        else:
            self.btn.background_color = (0.2, 0.6, 0.3, 1) if is_on else (0.4, 0.15, 0.15, 1)

    def trigger(self, buttonid):
        if buttonid == 0:
            self.btn.dispatch('on_press')


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
        self.set_focus(getattr(self, '_is_focused', False))

    def set_focus(self, active):
        self._is_focused = active
        self.key_btn.background_color = (0.2, 0.4, 0.6, 1) if active else (0.15, 0.2, 0.3, 1)

    def trigger(self, buttonid):
        if buttonid == 0:
            self._start_listening(None)
        elif buttonid == 2: # X Button on Xbox
            self._reset_key(None)

# ─── Joy Bind Row ─────────────────────────────────────────────
class JoyBindRow(BoxLayout):
    """แถวสำหรับแสดงและเปลี่ยน Joy binding"""
    _listening_row = None

    def __init__(self, action_key, popup_ref, **kw):
        super().__init__(orientation="horizontal", size_hint_y=None, height=48,
                         spacing=10, **kw)
        self.action_key = action_key
        self.popup_ref = popup_ref

        display_name = settings.KEY_DISPLAY_NAMES.get(action_key, action_key)
        self.add_widget(_lbl(display_name, font_size=15, size_hint_x=0.55))

        current_key = settings.joy_bindings.get(action_key, "?")
        self.key_btn = Button(
            text=self._format_key(current_key),
            size_hint_x=0.35,
            background_normal="",
            background_color=(0.3, 0.15, 0.3, 1),
            color=(0.95, 0.9, 1, 1),
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
        JOY_ICONS = {
            "0": "A / Cross",
            "1": "B / Circle",
            "2": "X / Square",
            "3": "Y / Triangle",
            "4": "LB / L1",
            "5": "RB / R1",
            "6": "Back / Select",
            "7": "Start / Options",
        }
        return JOY_ICONS.get(str(key), f"Joy Btn {key}")

    def _start_listening(self, inst):
        if JoyBindRow._listening_row and JoyBindRow._listening_row is not self:
            JoyBindRow._listening_row._cancel_listening()
        JoyBindRow._listening_row = self
        self.key_btn.text = "[ กดจอย... ]"
        self.key_btn.background_color = (0.5, 0.1, 0.3, 1)
        self.key_btn.color = (1, 0.8, 0.8, 1)
        Window.bind(on_joy_button_down=self._on_joy_button_down)

    def _cancel_listening(self):
        JoyBindRow._listening_row = None
        current_key = settings.joy_bindings.get(self.action_key, "?")
        self.key_btn.text = self._format_key(current_key)
        self.key_btn.background_color = (0.3, 0.15, 0.3, 1)
        self.key_btn.color = (0.95, 0.9, 1, 1)
        Window.unbind(on_joy_button_down=self._on_joy_button_down)

    def _on_joy_button_down(self, window, stickid, buttonid):
        key_name = str(buttonid)
        settings.joy_bindings[self.action_key] = key_name
        settings.save()
        self.key_btn.text = self._format_key(key_name)
        self.key_btn.background_color = (0.4, 0.1, 0.4, 1)
        self.key_btn.color = (1, 0.5, 0.8, 1)
        Clock.schedule_once(lambda dt: self._finish_listening(), 0.5)
        Window.unbind(on_joy_button_down=self._on_joy_button_down)
        JoyBindRow._listening_row = None
        return True

    def _finish_listening(self):
        current_key = settings.joy_bindings.get(self.action_key, "?")
        self.key_btn.text = self._format_key(current_key)
        self.key_btn.background_color = (0.3, 0.15, 0.3, 1)
        self.key_btn.color = (0.95, 0.9, 1, 1)

    def _reset_key(self, inst):
        default = settings.DEFAULT_JOY_KEYS.get(self.action_key, "?")
        settings.joy_bindings[self.action_key] = default
        settings.save()
        self.key_btn.text = self._format_key(default)
        self.set_focus(getattr(self, '_is_focused', False))

    def set_focus(self, active):
        self._is_focused = active
        self.key_btn.background_color = (0.4, 0.25, 0.4, 1) if active else (0.3, 0.15, 0.3, 1)

    def trigger(self, buttonid):
        if buttonid == 0:
            if not JoyBindRow._listening_row:
                self._start_listening(None)
        elif buttonid == 2:
            self._reset_key(None)


# ─── SettingsScreen (Main Tabbed Interface) ───────────────────
class SettingsScreen(Screen):
    """
    หน้าจอตั้งค่าแบบสมบูรณ์: Audio, Controls, Gameplay
    ระบบ Tabbed Interface พร้อมดีไซน์ Neon-Glassmorphism
    """
    def __init__(self, **kw):
        super().__init__(**kw)
        self._previous_screen = "main_menu"
        self._current_tab = "audio"
        self.focusable_widgets = []
        self.selected_index = 0
        self.joy_cooldown = False
        self._build()

    def set_previous_screen(self, screen_name):
        self._previous_screen = screen_name

    def on_enter(self):
        # Entry Animation
        self.main_container.opacity = 0
        anim = Animation(opacity=1, duration=0.4, t='out_quad')
        anim.start(self.main_container)
        self.switch_tab(self._current_tab)
        
        Window.bind(on_joy_axis=self._on_joy_axis, on_joy_hat=self._on_joy_hat,
                    on_joy_button_down=self._on_joy_button_down, on_key_down=self._on_keyboard_down)

    def on_leave(self):
        Window.unbind(on_joy_axis=self._on_joy_axis, on_joy_hat=self._on_joy_hat,
                      on_joy_button_down=self._on_joy_button_down, on_key_down=self._on_keyboard_down)


    def _build(self):
        # ─── พื้นหลัง (Layered Deep Blue) ───
        root = FloatLayout()
        with root.canvas.before:
            # Deep Navy Base
            Color(0.01, 0.02, 0.04, 1)
            Rectangle(pos=root.pos, size=root.size)
            
            # Subtle glow spots
            Color(0.1, 0.3, 0.5, 0.15)
            self._glow_spot = Ellipse(size=(800, 800))
            
            # Center Panel (Glassmorphism)
            Color(0.08, 0.12, 0.2, 0.75)
            self._bg_rect = RoundedRectangle(radius=[30])
            
            # Glowing Border
            Color(0.2, 0.7, 1.0, 0.25)
            self._border_rect = RoundedRectangle(radius=[30], width=2)
            
        root.bind(pos=self._update_bg, size=self._update_bg)

        # ─── Main Content Container ───
        self.main_container = BoxLayout(orientation="vertical", padding=[60, 45], spacing=25)
        
        # 🟢 HEADER: Title & Tabs
        header = BoxLayout(size_hint_y=None, height=90, spacing=25)
        
        # Title
        title_box = BoxLayout(orientation="vertical", size_hint_x=0.35)
        title_box.add_widget(_lbl("[b]GAME SETTINGS[/b]", font_size=34, color=(0.4, 0.9, 1, 1)))
        title_box.add_widget(_lbl("TAILOR YOUR APOCALYPSE", font_size=13, color=(0.5, 0.6, 0.7, 1)))
        
        # Tab Buttons
        self.tab_container = BoxLayout(spacing=15, size_hint_x=0.55)
        self.tab_buttons = {}
        tabs = [("audio", "AUDIO"), ("gameplay", "GAMEPLAY")]
        for tab_id, tab_label in tabs:
            btn = Button(
                text=tab_label, size_hint_x=1,
                background_normal="", background_color=(0.1, 0.15, 0.25, 0.4),
                color=(0.7, 0.8, 0.9, 1), bold=True, font_size=16
            )
            btn._base_color = (0.7, 0.8, 0.9, 1)
            btn._is_tab = True
            btn._tab_id = tab_id
            btn.bind(on_press=lambda inst, tid=tab_id: self.switch_tab(tid))
            self.tab_container.add_widget(btn)
            self.tab_buttons[tab_id] = btn
        
        # X Close Button
        close_btn = Button(
            text="✕", size_hint=(None, None), size=(55, 55),
            background_normal="", background_color=(0.3, 0.1, 0.1, 0.6),
            color=(1, 0.5, 0.5, 1), font_size=26, bold=True,
        )
        close_btn._base_color = (1, 0.5, 0.5, 1)
        self.close_btn = close_btn
        # Custom close button background
        with close_btn.canvas.before:
            Color(0.3, 0.1, 0.1, 0.5)
            self._close_bg = RoundedRectangle(pos=close_btn.pos, size=close_btn.size, radius=[15])
        close_btn.bind(pos=self._update_close_btn, size=self._update_close_btn)
        close_btn.bind(on_press=lambda x: self._close())
        
        header.add_widget(title_box)
        header.add_widget(self.tab_container)
        header.add_widget(close_btn)

        # 🟢 BODY: Content View
        self.content_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, bar_width=5)
        self.content_box = BoxLayout(orientation="vertical", spacing=18, size_hint_y=None)
        self.content_box.bind(minimum_height=self.content_box.setter("height"))
        self.content_scroll.add_widget(self.content_box)

        # 🟢 FOOTER
        footer = _lbl("ALL SETTINGS ARE SAVED LOCALLY", 
                      font_size=12, color=(0.3, 0.4, 0.5, 1), halign="center",
                      size_hint_y=None, height=30)

        self.main_container.add_widget(header)
        self.main_container.add_widget(self.content_scroll)
        self.main_container.add_widget(footer)

        root.add_widget(self.main_container)
        self.add_widget(root)

        # Default Tab
        self.switch_tab("audio")

    def switch_tab(self, tab_id):
        self._current_tab = tab_id
        if hasattr(self, 'content_box'):
            self.content_box.clear_widgets()
        
        # Update Tab Styles
        for tid, btn in self.tab_buttons.items():
            if tid == tab_id:
                btn.background_color = (0.2, 0.6, 1.0, 0.8)
                btn.color = (1, 1, 1, 1)
            else:
                btn.background_color = (0.1, 0.15, 0.25, 0.4)
                btn.color = (0.7, 0.8, 0.9, 1)

        # Build Tab Content
        if tab_id == "audio":
            self._build_audio()
        elif tab_id == "controls":
            self._build_controls()
        elif tab_id == "gameplay":
            self._build_gameplay()

        # Update Navigation List
        self.focusable_widgets = []
        for tid in ["audio", "gameplay"]:
            self.focusable_widgets.append(self.tab_buttons[tid])
        for child in reversed(self.content_box.children):
            if hasattr(child, "set_focus") or isinstance(child, Button):
                 self.focusable_widgets.append(child)
        self.focusable_widgets.append(self.close_btn)
        self.selected_index = 0
        self.update_highlight()

    def update_highlight(self):
        for i, w in enumerate(self.focusable_widgets):
            active = (i == self.selected_index)
            if hasattr(w, "set_focus"):
                w.set_focus(active)
            elif isinstance(w, Button):
                if active:
                    w.color = (1, 0.8, 0.2, 1) # Highlight yellow
                else:
                    if getattr(w, '_is_tab', False) and w._tab_id == self._current_tab:
                        w.color = (1, 1, 1, 1)
                    else:
                        w.color = getattr(w, '_base_color', (1, 1, 1, 1))

        # Auto-scroll adjustment
        if self.focusable_widgets and self.selected_index >= 0:
            target = self.focusable_widgets[self.selected_index]
            if hasattr(target, 'parent') and target.parent:
                # Basic scroll approximation
                if target.y < self.content_scroll.scroll_y * self.content_box.height:
                    self.content_scroll.scroll_y = max(0.0, target.y / self.content_box.height)

    def navigate(self, direction):
        if self.joy_cooldown or not self.focusable_widgets: return
        self.joy_cooldown = True
        Clock.schedule_once(lambda dt: setattr(self, 'joy_cooldown', False), 0.15)
        
        if direction == "next":
            self.selected_index = (self.selected_index + 1) % len(self.focusable_widgets)
        elif direction == "prev":
            self.selected_index = (self.selected_index - 1) % len(self.focusable_widgets)
        self.update_highlight()

    def handle_action(self, action, value=0):
        if not self.focusable_widgets: return
        w = self.focusable_widgets[self.selected_index]
        if action == "press":
            if hasattr(w, "trigger"):
                w.trigger(0)
            elif isinstance(w, Button):
                w.dispatch('on_press')
        elif action == "alt_press":
            if hasattr(w, "trigger"):
                w.trigger(2)
        elif action == "adjust":
            if hasattr(w, "adjust"):
                w.adjust(value)

    def _on_joy_axis(self, win, stickid, axisid, value):
        normalized = value / 32767.0
        if abs(normalized) > 0.5:
            if axisid == 1: # Y axis
                if self.joy_cooldown: return
                self.navigate("next" if normalized > 0 else "prev")
            if axisid == 0: # X axis
                if self.joy_cooldown: return
                self.joy_cooldown = True
                Clock.schedule_once(lambda dt: setattr(self, 'joy_cooldown', False), 0.1)
                self.handle_action("adjust", 0.05 if normalized > 0 else -0.05)

    def _on_joy_hat(self, win, stickid, hatid, value):
        x, y = value
        if y == -1: self.navigate("next")
        elif y == 1: self.navigate("prev")
        elif x == 1: self.handle_action("adjust", 0.05)
        elif x == -1: self.handle_action("adjust", -0.05)

    def _on_joy_button_down(self, win, stickid, buttonid):
        if buttonid == 0:
            self.handle_action("press")
        elif buttonid == 1:
            self._close()
        elif buttonid == 2:
            self.handle_action("alt_press")

    def _on_keyboard_down(self, window, key, scancode, codepoint, modifiers):
        if key == 27: # ESC
            self._close()
            return True
        elif key == 119 or key == 273: # W or Up
            self.navigate("prev")
            return True
        elif key == 115 or key == 274: # S or Down
            self.navigate("next")
            return True
        elif key == 97 or key == 276: # A or Left
            self.handle_action("adjust", -0.05)
            return True
        elif key == 100 or key == 275: # D or Right
            self.handle_action("adjust", 0.05)
            return True
        elif key == 32 or key == 13: # Space or Enter
            self.handle_action("press")
            return True
        return False

    def _build_audio(self):
        self.content_box.add_widget(_lbl("[b]VOLUME SETTINGS[/b]", font_size=18, color=(0.4, 0.8, 1, 1), size_hint_y=None, height=40))
        self.content_box.add_widget(_divider())
        
        def music_cb(v): settings.music_volume = v; settings.save()
        def sfx_cb(v): settings.sfx_volume = v; settings.save()
        
        self.content_box.add_widget(VolumeRow("Music Volume", settings.music_volume, music_cb, "🎵"))
        self.content_box.add_widget(VolumeRow("Sound Effects", settings.sfx_volume, sfx_cb, "💥"))

    def _build_controls(self):
        # Keyboard Mappings
        self.content_box.add_widget(_lbl("[b]KEYBOARD MAPPING[/b]", font_size=18, color=(0.4, 0.8, 1, 1), size_hint_y=None, height=40))
        self.content_box.add_widget(_divider())
        keys = ["move_up", "move_down", "move_left", "move_right", "dash", "skill1", "skill2", "skill3", "pause"]
        for k in keys:
            if k in settings.key_bindings:
                self.content_box.add_widget(KeyBindRow(k, self))
                
        # Joy Mappings
        self.content_box.add_widget(BoxLayout(size_hint_y=None, height=20))
        self.content_box.add_widget(_lbl("[b]CONTROLLER (JOY) MAPPING[/b]", font_size=18, color=(0.8, 0.4, 1, 1), size_hint_y=None, height=40))
        self.content_box.add_widget(_divider())
        joy_keys = ["dash", "skill1", "skill2", "skill3", "pause"]
        for k in joy_keys:
            if k in settings.joy_bindings:
                self.content_box.add_widget(JoyBindRow(k, self))
                
        self.content_box.add_widget(BoxLayout(size_hint_y=None, height=10))
        reset_all = Button(
            text="RESET ALL CONTROLS TO DEFAULT", size_hint_y=None, height=50,
            background_normal="", background_color=(0.4, 0.3, 0.1, 0.6),
            color=(1, 0.8, 0.6, 1), bold=True
        )
        reset_all._base_color = (1, 0.8, 0.6, 1)
        reset_all.bind(on_press=lambda x: self._reset_all_keys())
        self.content_box.add_widget(reset_all)

    def _reset_all_keys(self):
        settings.reset_keys()
        self.switch_tab("controls")

    def _build_gameplay(self):
        # DISPLAY SECTION
        self.content_box.add_widget(_lbl("[b]VIDEO & EFFECTS[/b]", font_size=18, color=(0.4, 0.8, 1, 1), size_hint_y=None, height=40))
        self.content_box.add_widget(_divider())
        
        def fs_cb(active):
            settings.fullscreen = active
            Window.fullscreen = 'auto' if active else False
            settings.save()
        self.content_box.add_widget(ToggleRow("Fullscreen Mode", settings.fullscreen, fs_cb))
        
        def cam_cb(active): settings.camera_shake = active; settings.save()
        self.content_box.add_widget(ToggleRow("Camera Shake Effects", settings.camera_shake, cam_cb))

        # VISUAL FEEDBACK SECTION
        self.content_box.add_widget(BoxLayout(size_hint_y=None, height=20))
        self.content_box.add_widget(_lbl("[b]VISUAL FEEDBACK[/b]", font_size=18, color=(0.4, 0.8, 1, 1), size_hint_y=None, height=40))
        self.content_box.add_widget(_divider())

        def dmg_cb(active): settings.show_damage_numbers = active; settings.save()
        self.content_box.add_widget(ToggleRow("Show Damage Numbers", settings.show_damage_numbers, dmg_cb))

        def hp_cb(active): settings.show_enemy_hp = active; settings.save()
        self.content_box.add_widget(ToggleRow("Show Enemy Health Bars", settings.show_enemy_hp, hp_cb))


    def _update_bg(self, inst, val):
        pad = 45
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
        if not self.manager:
            return

        target = self._previous_screen
        self.manager.current = target
        
        # ถ้ามาจากหน้าเกม ให้กลับไปเปิด Pause Popup ให้ด้วย
        if target == "game_screen":
            from ui.pause import PausePopup
            game_screen = self.manager.get_screen("game_screen")
            # เปิด Popup อีกครั้งเพื่อให้เกมยังคงสถานะ Pause อยู่
            Clock.schedule_once(lambda dt: PausePopup(game_screen).open(), 0.1)

