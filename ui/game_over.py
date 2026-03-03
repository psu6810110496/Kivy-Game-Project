from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.app import App
from kivy.animation import Animation

class GameOverPopup(Popup):
    def __init__(self, **kwargs):
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

        # Bind อีเวนต์ตอน Popup เปิด/ปิด
        self.bind(on_open=self._on_open, on_dismiss=self._remove_joy)

        layout = BoxLayout(orientation="vertical", padding=20, spacing=20)
        
        # ข้อความแจ้งเตือน
        die_label = Label(
            text="YOU DIED",
            font_size=50,
            color=(1, 0, 0, 1), # สีแดง
            bold=True
        )
        die_label.opacity = 0  # ให้ค่อย ๆ โผล่ทีหลัง
        self.die_label = die_label
        
        # ปุ่ม Try Again
        retry_btn = Button(
            text="TRY AGAIN",
            size_hint_y=None,
            height=50,
            background_color=(0.3, 0.3, 0.3, 1),
        )
        retry_btn.opacity = 0
        retry_btn.bind(on_press=self.try_again)
        self.retry_btn = retry_btn
        self.selectable_buttons.append(retry_btn)

        # ปุ่มกลับหน้าเมนู
        menu_btn = Button(
            text="BACK TO MENU",
            size_hint_y=None,
            height=50,
            background_color=(0.15, 0.15, 0.15, 1),
        )
        menu_btn.opacity = 0
        menu_btn.bind(on_press=self.return_to_menu)
        self.menu_btn = menu_btn
        self.selectable_buttons.append(menu_btn)

        layout.add_widget(die_label)
        layout.add_widget(retry_btn)
        layout.add_widget(menu_btn)
        self.content = layout

    def return_to_menu(self, instance):
        self.dismiss()
        # เปลี่ยนหน้าไปที่ main_menu
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
        )

    def _on_joy_button_down(self, window, stickid, buttonid):
        # ปุ่ม A (0) = กดปุ่มที่เลือกอยู่, ปุ่ม B (1) = Back to Menu
        if buttonid == 0 and self.selectable_buttons:
            self.selectable_buttons[self.selected_index].dispatch("on_press")
        elif buttonid == 1 and self.menu_btn:
            self.menu_btn.dispatch("on_press")

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
                    btn.background_color = (0.9, 0.4, 0.4, 1)
                else:
                    btn.background_color = (0.7, 0.7, 0.7, 1)
                btn.bold = True
            else:
                # สีปกติ
                if btn is self.retry_btn:
                    btn.background_color = (0.3, 0.3, 0.3, 1)
                else:
                    btn.background_color = (0.15, 0.15, 0.15, 1)
                btn.bold = False