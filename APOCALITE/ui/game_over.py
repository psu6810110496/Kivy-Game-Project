from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.app import App
from kivy.animation import Animation

class GameOverPopup(Popup):
    def __init__(self, win=False, **kwargs):
        super().__init__(**kwargs)
        self.title = ""
        self.separator_height = 0
        # ทำเป็น Overlay เต็มหน้าจอ
        self.size_hint = (1, 1)
        self.auto_dismiss = False
        # ซ่อนกรอบ Popup ปกติ ใช้สีดำโปร่งใสกินเต็มจอแทน
        self.background = ""
        # เริ่มจากพื้นหลังโปร่งใสทั้งจอ แล้วค่อย ๆ Fade เข้มขึ้น
        self.background_color = (0, 0, 0, 0)

        # เก็บ reference สำหรับอนิเมชัน / จอย
        self.menu_btn = None
        self.retry_btn = None
        self.die_label = None
        # สำหรับ Navigation ด้วยจอย
        self.selectable_buttons = []
        self.selected_index = 0
        self.show_highlight = False
        self.joy_cooldown = False
        self.win = win

        # Bind อีเวนต์ตอน Popup เปิด/ปิด
        self.bind(on_open=self._on_open, on_dismiss=self._remove_joy)

        layout = BoxLayout(orientation="vertical", padding=20, spacing=20)
        
        # ข้อความแจ้งเตือน
        text = "VICTORY!" if win else "YOU DIED"
        color = (0, 1, 0, 1) if win else (1, 0, 0, 1) # Green = Win, Red = Die

        die_label = Label(
            text=text,
            font_size=60 if win else 50,
            color=color,
            bold=True
        )
        die_label.opacity = 0  # ให้ค่อย ๆ โผล่ทีหลัง
        self.die_label = die_label
        
        # ปุ่ม Try Again -> เปลี่ยนเป็น Label แบบ "ลอย" (ใช้ฟอนต์เหมือน PausePopup)
        retry_lbl = Label(
            text="TRY AGAIN",
            font_size=30,
            bold=True,
            size_hint_y=None,
            height=50,
            color=(1, 1, 1, 1),
        )
        retry_lbl.opacity = 0
        # เก็บ callback สำหรับเรียกใช้ทั้งจาก touch และจอย
        retry_lbl.callback = self.try_again
        # bind touch event ให้ตรวจสอบการคลิกภายในพื้นที่
        retry_lbl.bind(on_touch_down=self._on_label_pressed)
        self.retry_btn = retry_lbl
        self.selectable_buttons.append(retry_lbl)

        # ปุ่มกลับหน้าเมนู -> ใช้ Label ด้วย
        menu_lbl = Label(
            text="BACK TO MENU",
            font_size=30,
            bold=True,
            size_hint_y=None,
            height=50,
            color=(1, 1, 1, 1),
        )
        menu_lbl.opacity = 0
        menu_lbl.callback = self.return_to_menu
        menu_lbl.bind(on_touch_down=self._on_label_pressed)
        self.menu_btn = menu_lbl
        self.selectable_buttons.append(menu_lbl)

        layout.add_widget(die_label)
        layout.add_widget(retry_lbl)
        layout.add_widget(menu_lbl)
        self.content = layout

    def return_to_menu(self, instance):
        self.dismiss()
        # ถ้าชนะ ให้ไปที่ credits_screen ถ้าแพ้ไป main_menu
        if getattr(self, "win", False):
            App.get_running_app().root.current = "credits_screen"
        else:
            App.get_running_app().root.current = "main_menu"

    def try_again(self, instance):
        """เริ่มเกมใหม่ทันทีด้วยตัวละครเดิม"""
        app = App.get_running_app()
        sm = app.root
        game_screen = sm.get_screen("game_screen")

        # รีเซ็ตสถานะ GameScreen คล้ายตอนเข้าใหม่
        if hasattr(app, "current_player") and app.current_player:
            app.current_player.reset()

        # เรียก on_enter ของ GameScreen เพื่อเซ็ตทุกอย่างใหม่
        game_screen.on_leave()
        game_screen.on_enter()

        self.dismiss()

    # ================================
    # --- อนิเมชัน & รองรับจอย ---
    # ================================
    def _on_open(self, *args):
        # Bind จอยตอน Popup เปิด
        Window.bind(
            on_joy_axis=self._on_joy_axis,
            on_joy_hat=self._on_joy_hat,
            on_joy_button_down=self._on_joy_button_down,
            on_key_down=self._on_keyboard_down,
        )

        # ค่าเริ่มต้นของตัวเลือก
        self.selected_index = 0
        self.show_highlight = False
        self._update_highlight()

        # 1) Fade พื้นหลังมืดขึ้น
        bg_anim = Animation(background_color=(0, 0, 0, 0.9), d=0.3)
        bg_anim.start(self)

        # 2) ให้ "YOU DIED" ค่อย ๆ โผล่ตามมา
        if self.die_label:
            title_anim = Animation(opacity=1.0, d=0.35)

            def start_title_anim(*_):
                title_anim.start(self.die_label)

            bg_anim.bind(on_complete=start_title_anim)

        # 3) ปุ่ม TRY AGAIN / BACK TO MENU ค่อย ๆ โผล่ตามหลัง Title
        if self.retry_btn and self.menu_btn:
            buttons_anim = Animation(opacity=1.0, d=0.3)

            def start_buttons_anim(*_):
                buttons_anim.start(self.retry_btn)
                buttons_anim.start(self.menu_btn)

            if self.die_label:
                title_anim.bind(on_complete=start_buttons_anim)
            else:
                bg_anim.bind(on_complete=start_buttons_anim)

    def _remove_joy(self, *args):
        Window.unbind(
            on_joy_axis=self._on_joy_axis,
            on_joy_hat=self._on_joy_hat,
            on_joy_button_down=self._on_joy_button_down,
            on_key_down=self._on_keyboard_down,
        )

    # --- [ระบบ Keyboard WASD + Space] ---
    def _on_keyboard_down(self, window, key, scancode, codepoint, modifiers):
        if key == 119 or key == 97: # W or A
            self._navigate("prev")
            return True
        elif key == 115 or key == 100: # S or D
            self._navigate("next")
            return True
        elif key == 32 or key == 13: # Spacebar or Enter
            self.show_highlight = True
            self._update_highlight()
            if self.selectable_buttons:
                btn = self.selectable_buttons[self.selected_index]
                if hasattr(btn, "callback") and btn.callback:
                    btn.callback(btn)
            return True
        return False

    def _on_joy_button_down(self, window, stickid, buttonid):
        # ปุ่ม A (0) = กดปุ่มที่เลือกอยู่, ปุ่ม B (1) = Back to Menu
        if buttonid == 0 and self.selectable_buttons:
            # เรียก callback ที่เก็บไว้
            btn = self.selectable_buttons[self.selected_index]
            if hasattr(btn, "callback") and btn.callback:
                btn.callback(btn)
        elif buttonid == 1 and self.menu_btn:
            self.return_to_menu(self.menu_btn)

    # -------------------------
    # Navigation ด้วยอนาล็อก / D-Pad
    # -------------------------
    def _reset_cooldown(self, dt):
        self.joy_cooldown = False

    def _navigate(self, direction: str):
        if self.joy_cooldown or not self.selectable_buttons:
            return
        self.joy_cooldown = True
        Clock.schedule_once(self._reset_cooldown, 0.2)

        if direction == "next":
            self.selected_index = (self.selected_index + 1) % len(self.selectable_buttons)
        elif direction == "prev":
            self.selected_index = (self.selected_index - 1) % len(self.selectable_buttons)

        self.show_highlight = True
        self._update_highlight()

    def _on_joy_axis(self, window, stickid, axisid, value):
        # ใช้อนาล็อกซ้ายแกนตั้ง เลื่อนขึ้น/ลง
        normalized = value / 32767.0
        if abs(normalized) > 0.5 and axisid in (1,):  # แกน Y
            self._navigate("next" if normalized > 0 else "prev")

    def _on_joy_hat(self, window, stickid, hatid, value):
        x, y = value
        if y == -1:   # ลง
            self._navigate("next")
        elif y == 1:  # ขึ้น
            self._navigate("prev")

    def _update_highlight(self):
        # ปรับสีปุ่มตามที่เลือกอยู่
        for i, btn in enumerate(self.selectable_buttons):
            if i == self.selected_index and self.show_highlight:
                # ปุ่มที่ถูกเลือกอยู่ ให้สว่างขึ้น
                if btn is self.retry_btn:
                    btn.color = (1, 0.4, 0.4, 1)
                else:
                    btn.color = (0.9, 0.9, 0.9, 1)
                # ขยายฟอนต์เมื่อถูกเลือก (เหมือน PausePopup)
                btn.font_size = 36
                btn.bold = True
            else:
                # สีปกติ
                if btn is self.retry_btn:
                    btn.color = (1, 1, 1, 1)
                else:
                    btn.color = (1, 1, 1, 1)
                btn.font_size = 30
                btn.bold = False

    def _on_label_pressed(self, instance, touch):
        """Handle touch on floating text labels."""
        if instance.collide_point(*touch.pos):
            if hasattr(instance, "callback") and instance.callback:
                instance.callback(instance)
            return True
        return False