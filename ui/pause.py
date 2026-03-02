from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.clock import Clock
import kivy.app


class PausePopup(Popup):
    def __init__(self, game_screen, **kwargs):
        super().__init__(**kwargs)
        self.game_screen = game_screen
        
        # --- [ซ่อนหัว Popup เดิมทิ้ง] ---
        self.title = ""
        self.separator_height = 0

        # --- [ทำให้เป็นหน้าต่าง Overlay เต็มจอแบบเนียนๆ] ---
        self.background = ""
        self.background_color = (0, 0, 0, 0.8) # พื้นหลังสีดำโปร่งแสง 80%
        self.size_hint = (1, 1) # ขยายเต็มหน้าจอ
        self.auto_dismiss = False

        # --- [ระบบ Navigation (จอย + เมาส์)] ---
        self.selectable_buttons = []
        self.selected_index = 0
        self.show_highlight = False # <--- ประกาศตัวแปรเปิด/ปิดแสง
        self.joy_cooldown = False
        self.bind(on_open=self.setup_joy, on_dismiss=self.remove_joy)
        # ---------------------------

        # กล่องหลักสำหรับจัดวาง
        layout = BoxLayout(orientation="vertical", padding=50, spacing=20)
        
        # หัว "PAUSED" ตรงกลางหน้าจอ (สีเหลือง)
        lbl_pause = Label(
            text="PAUSED",
            font_size=70,
            bold=True,
            color=(1, 0.9, 0.2, 1), # สีเหลือง
            size_hint=(1, 0.5), # กินพื้นที่ครึ่งบน
        )
        layout.add_widget(lbl_pause)

        # กล่องสำหรับปุ่ม
        btn_layout = BoxLayout(orientation="vertical", spacing=15, size_hint=(1, 0.5))

        # --- [สร้างปุ่มแบบโปร่งใส (Floating Buttons)] ---
        btn_resume = Button(
            text="RESUME",
            font_size=30,
            bold=True,
            background_normal="",
            background_color=(0, 0, 0, 0), # พื้นหลังโปร่งใส 100%
            color=(0.5, 0.5, 0.5, 1),      # สีตัวอักษรปกติ (สีเทา)
        )
        btn_menu = Button(
            text="RETURN TO MENU",
            font_size=30,
            bold=True,
            background_normal="",
            background_color=(0, 0, 0, 0), # พื้นหลังโปร่งใส 100%
            color=(0.7, 0.2, 0.2, 1),      # สีตัวอักษรปกติ (แดงเข้ม)
        )

        btn_resume.bind(on_press=lambda x: self.resume())
        btn_menu.bind(on_press=lambda x: self.go_to_menu())

        btn_layout.add_widget(btn_resume)
        btn_layout.add_widget(btn_menu)
        
        layout.add_widget(btn_layout)
        
        # เก็บปุ่มลง List
        self.selectable_buttons.append(btn_resume)
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
            mouse_pos=self._on_mouse_pos # <--- Bind เมาส์ตอนเปิด Popup
        )
        self.selected_index = 0
        self.show_highlight = False
        self.update_highlight()

    def remove_joy(self, *args):
        Window.unbind(
            on_joy_axis=self._on_joy_axis, 
            on_joy_hat=self._on_joy_hat, 
            on_joy_button_down=self._on_joy_button_down,
            mouse_pos=self._on_mouse_pos # <--- Unbind เมาส์ตอนปิด Popup
        )

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
            # เช็คว่าเลือกปุ่มนี้อยู่ และกำลังโชว์ Highlight (เมาส์ชี้/ใช้จอย)
            if i == self.selected_index and self.show_highlight:
                btn.font_size = 36 # ขยายฟอนต์
                if btn.text == "RETURN TO MENU":
                    btn.color = (1, 0.2, 0.2, 1) # แดงสว่างจ้า
                else:
                    btn.color = (1, 1, 1, 1) # ขาวสว่าง (Resume)
            else:
                # ตอนไม่ได้เลือก
                btn.font_size = 30 # ฟอนต์ขนาดปกติ
                if btn.text == "RETURN TO MENU":
                    btn.color = (0.7, 0.2, 0.2, 1) # แดงเข้มปกติ
                else:
                    btn.color = (0.5, 0.5, 0.5, 1) # เทามืด (Resume)

    def _reset_cooldown(self, dt):
        self.joy_cooldown = False

    def navigate(self, direction):
        if self.joy_cooldown: return
        self.joy_cooldown = True
        self.show_highlight = True # ขยับจอยแล้ว เปิดโหมด Highlight
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
        self.show_highlight = True # กดปุ่มแล้ว เปิดโหมด Highlight
        self.update_highlight()
        
        if buttonid == 0: # ปุ่ม A ยืนยัน
            self.selectable_buttons[self.selected_index].dispatch('on_press')
        elif buttonid == 1: # ปุ่ม B กดเพื่อ Resume เกมต่อ
            self.resume()
    # ==========================================

    def resume(self):
        self.game_screen.resume_game()
        self.dismiss()

    def go_to_menu(self):
        # ปิด Popup และเปลี่ยน Screen
        self.dismiss()
        self.game_screen.resume_game() # ตรวจสอบให้แน่ใจว่า resume เกมก่อนย้ายหน้า
        self.game_screen.manager.current = 'main_menu'