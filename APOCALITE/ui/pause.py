from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.clock import Clock
import kivy.app
from ui.font import PIXEL_FONT


class PausePopup(Popup):
    def __init__(self, game_screen, **kwargs):
        super().__init__(**kwargs)
        self.game_screen = game_screen

        # ฟ้อนต์ถูก register ไว้แล้วใน ui.font
        
        # --- [ซ่อนหัว Popup เดิมทิ้ง] ---
        self.title = ""
        self.separator_height = 0

        # --- [ทำให้เป็นหน้าต่าง Overlay เต็มจอแบบเนียนๆ] ---
        self.background = ""
        self.background_color = (0, 0, 0, 0.25) # พื้นหลังสีดำโปร่งแสง 80%
        self.size_hint = (1, 1) # ขยายเต็มหน้าจอ
        self.auto_dismiss = False

        # --- [ระบบ Navigation (จอย + เมาส์)] ---
        self.selectable_buttons = []
        self.selected_index = 0
        self.show_highlight = False
        self.joy_cooldown = False
        self.bind(on_open=self.setup_joy, on_dismiss=self.remove_joy)

        # กล่องหลักสำหรับจัดวาง
        layout = BoxLayout(orientation="vertical", padding=50, spacing=20)
        
        # หัว "PAUSED" ตรงกลางหน้าจอ (สีเหลือง)
        lbl_pause = Label(
            text="PAUSED",
            font_size=70,
            font_name=PIXEL_FONT,
            color=(1, 0.9, 0.2, 1),
            size_hint=(1, 0.5),
        )
        layout.add_widget(lbl_pause)

        # กล่องสำหรับปุ่ม
        btn_layout = BoxLayout(orientation="vertical", spacing=15, size_hint=(1, 0.6))

        # --- [สร้างปุ่มแบบโปร่งใส (Floating Buttons)] ---
        btn_resume = Button(
            text="RESUME",
            font_size=30, font_name=PIXEL_FONT,
            background_normal="", background_color=(0, 0, 0, 0),
            color=(0.5, 0.5, 0.5, 1),
        )
        btn_settings = Button(
            text="SETTINGS",
            font_size=30, font_name=PIXEL_FONT,
            background_normal="", background_color=(0, 0, 0, 0),
            color=(0.5, 0.75, 1, 1),
        )
        btn_menu = Button(
            text="RETURN TO MENU",
            font_size=30, font_name=PIXEL_FONT,
            background_normal="", background_color=(0, 0, 0, 0),
            color=(0.7, 0.2, 0.2, 1),
        )

        btn_resume.bind(on_press=lambda x: self.resume())
        btn_settings.bind(on_press=lambda x: self.open_settings())
        btn_menu.bind(on_press=lambda x: self.go_to_menu())

        btn_layout.add_widget(btn_resume)
        btn_layout.add_widget(btn_settings)
        btn_layout.add_widget(btn_menu)
        
        layout.add_widget(btn_layout)
        
        # เก็บปุ่มลง List
        self.selectable_buttons.append(btn_resume)
        self.selectable_buttons.append(btn_settings)
        self.selectable_buttons.append(btn_menu)

        self.content = layout

    # ==========================================
    # --- [ระบบ Navigation สำหรับหน้า Pause] ---
    # ==========================================
    def setup_joy(self, *args):
        Window.bind(
            on_joy_axis=self._on_joy_axis, 
            on_joy_hat=self._on_joy_hat, 
            on_joy_button_down=self._on_joy_button_down,
            mouse_pos=self._on_mouse_pos,
            on_key_down=self._on_keyboard_down
        )
        self.selected_index = 0
        self.show_highlight = False
        self.update_highlight()

    def remove_joy(self, *args):
        Window.unbind(
            on_joy_axis=self._on_joy_axis, 
            on_joy_hat=self._on_joy_hat, 
            on_joy_button_down=self._on_joy_button_down,
            mouse_pos=self._on_mouse_pos,
            on_key_down=self._on_keyboard_down
        )

    # --- [ระบบ Keyboard WASD + Space] ---
    def _on_keyboard_down(self, window, key, scancode, codepoint, modifiers):
        if key in (119, 97, 273, 276): # W, A, Up, Left
            self.navigate("prev")
            return True
        elif key in (115, 100, 274, 275): # S, D, Down, Right
            self.navigate("next")
            return True
        elif key == 32 or key == 13: # Spacebar or Enter
            self.show_highlight = True
            self.update_highlight()
            if self.selectable_buttons:
                self.selectable_buttons[self.selected_index].dispatch('on_press')
            return True
        return False

    # --- [ระบบตรวจจับเมาส์ Hover] ---
    def _on_mouse_pos(self, window, pos):
        for i, btn in enumerate(self.selectable_buttons):
            if btn.collide_point(*pos):
                self.selected_index = i
                self.show_highlight = True
                self.update_highlight()
                return 
        
        if self.show_highlight:
            self.show_highlight = False
            self.update_highlight()

    def update_highlight(self):
        for i, btn in enumerate(self.selectable_buttons):
            if i == self.selected_index and self.show_highlight:
                btn.font_size = 36
                if btn.text == "RETURN TO MENU":
                    btn.color = (1, 0.2, 0.2, 1)
                elif btn.text == "SETTINGS":
                    btn.color = (0.5, 0.9, 1, 1)
                else:
                    btn.color = (1, 1, 1, 1)
            else:
                btn.font_size = 30
                if btn.text == "RETURN TO MENU":
                    btn.color = (0.7, 0.2, 0.2, 1)
                elif btn.text == "SETTINGS":
                    btn.color = (0.5, 0.75, 1, 1)
                else:
                    btn.color = (0.5, 0.5, 0.5, 1)

    def _reset_cooldown(self, dt):
        self.joy_cooldown = False

    def navigate(self, direction):
        if self.joy_cooldown: return
        self.joy_cooldown = True
        self.show_highlight = True
        Clock.schedule_once(self._reset_cooldown, 0.2)
        if direction == "next":
            self.selected_index = (self.selected_index + 1) % len(self.selectable_buttons)
        elif direction == "prev":
            self.selected_index = (self.selected_index - 1) % len(self.selectable_buttons)
        self.update_highlight()

    def _on_joy_axis(self, window, stickid, axisid, value):
        normalized = value / 32767.0
        if abs(normalized) > 0.5:
            if axisid == 0 or axisid == 1: 
                self.navigate("next" if normalized > 0 else "prev")

    def _on_joy_hat(self, window, stickid, hatid, value):
        x, y = value
        if x == 1 or y == -1: self.navigate("next")
        elif x == -1 or y == 1: self.navigate("prev")

    def _on_joy_button_down(self, window, stickid, buttonid):
        self.show_highlight = True
        self.update_highlight()
        if buttonid == 0: # ปุ่ม A ยืนยัน
            self.selectable_buttons[self.selected_index].dispatch('on_press')
        elif buttonid == 1: # ปุ่ม B กดเพื่อ Resume เกมต่อ
            self.resume()

    # ==========================================

    def open_settings(self):
        self.game_screen.manager.current = "settings_screen"
        self.game_screen.manager.get_screen("settings_screen").set_previous_screen("game_screen")
        self.dismiss()

    def on_leave(self):
        self.dismiss()

    def resume(self):
        self.game_screen.resume_game()
        self.dismiss()

    def go_to_menu(self):
        self.dismiss()
        self.game_screen.resume_game()
        self.game_screen.manager.current = 'main_menu'