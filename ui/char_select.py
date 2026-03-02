from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Rectangle, Color
from kivy.core.window import Window
from kivy.clock import Clock
from game.player import PlayerStats
import kivy.app

class CharacterSelectScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # --- [ระบบ Navigation] ---
        self.selectable_buttons = [] # เก็บปุ่มที่เลือกได้ทั้งหมด
        self.selected_index = 0      # ตำแหน่งปุ่มที่กำลังเลือกอยู่
        self.show_highlight = False  # <--- ประกาศตรงนี้! ป้องกัน Error ตอนเปิดหน้าจอ
        self.joy_cooldown = False    # ป้องกันอนาล็อกเลื่อนรัวเกินไป
        # ---------------------------

        # 1. ใช้ข้อมูลตัวละครใหม่ของเรา (PTae, Lostman, Monke)
        self.char_data = {
            "PTae": PlayerStats(
                name="PTae",
                hp=150,
                speed=3.5,
                damage=14,
                idle_frames=[
                    "assets/PTae/PTIdle/PTTG1.png",
                    "assets/PTae/PTIdle/PTTG2.png",
                ],
                walk_frames=[
                    "assets/PTae/PTPushUp/PTaeTester1.png",
                    "assets/PTae/PTPushUp/PTaeTester2.png",
                    "assets/PTae/PTPushUp/PTaeTester3.png",
                    "assets/PTae/PTPushUp/PTaeTester4.png",
                ],
            ),
            "Lostman": PlayerStats(
                name="Lostman",
                hp=100,
                speed=5.0,
                damage=17,
                idle_frames=[
                    "assets/Lostman/idle/idleman1.png",
                    "assets/Lostman/idle/idleman2.png",
                ],
                walk_frames=[
                    "assets/Lostman/walk/walk1.png",
                    "assets/Lostman/walk/walk2.png",
                    "assets/Lostman/walk/walk3.png",
                    "assets/Lostman/walk/walk4.png",
                ],
            ),
            "Monkey": PlayerStats(
                name="Monkey",
                hp=90,
                speed=7.0,
                damage=12,
                idle_frames=[
                    "assets/Monkey/IdleM/IdleM01.png",
                    "assets/Monkey/IdleM/IdleM02.png",
                ],
                walk_frames=[
                    "assets/Monkey/WalkM/W01.png",
                    "assets/Monkey/WalkM/W02.png",
                    "assets/Monkey/WalkM/W03.png",
                    "assets/Monkey/WalkM/W04.png",
                ],
            ),
        }

        # 2. นำ UI สวยๆ (พื้นหลังสีเทาเข้มอมฟ้า) มาใช้
        with self.canvas.before:
            Color(0.05, 0.08, 0.1, 1)
            self.bg = Rectangle(pos=self.pos, size=Window.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        layout = BoxLayout(orientation="vertical", padding=50, spacing=30)

        # 3. หัวข้อมีขอบดำสวยๆ
        layout.add_widget(
            Label(
                text="SELECT CHARACTER",
                font_size=40,
                bold=True,
                color=(0.9, 0.95, 1, 1),
                outline_width=2,
                outline_color=(0, 0, 0, 1),
                size_hint=(1, 0.2),
            )
        )

        chars = BoxLayout(spacing=20, size_hint=(1, 0.7)) 
        for name, stats in self.char_data.items():
            # 4. ปรับปุ่มให้เป็นธีมกระจกโปร่งแสงและแสดง Status โชว์ ATK ด้วย
            btn = Button(
                text=f"{name}\n\nHP: {stats.hp}\nATK: {stats.damage}\nSPD: {stats.speed}",
                font_size=20,
                bold=True,
                halign="center",
                background_normal="",
                background_color=(0.1, 0.15, 0.2, 0.85),
                color=(0.8, 0.9, 1, 1),
            )
            btn.bind(on_press=lambda inst, s=stats: self.select_char(s))
            chars.add_widget(btn)
            
            # --- [เก็บปุ่มตัวละครลงใน List สำหรับจอยและเมาส์] ---
            self.selectable_buttons.append(btn)

        layout.add_widget(chars)

        # --- [ส่วนปุ่ม Back to Menu ไว้ด้านล่าง] ---
        back_btn = Button(
            text="BACK TO MENU",
            size_hint=(1, 0.15), 
            font_size=20,
            bold=True,
            background_normal="",
            # เปลี่ยนสีพื้นฐานให้เป็นสีเทาปกติเหมือนปุ่มอื่น
            background_color=(0.1, 0.15, 0.2, 0.85), 
            color=(1, 0.8, 0.8, 1)
        )
        back_btn.bind(on_press=self.go_back)
        layout.add_widget(back_btn)
        
        # --- [เก็บปุ่ม Back ลงใน List ด้วย] ---
        self.selectable_buttons.append(back_btn)
        # ----------------------------------------

        self.add_widget(layout)

    def _update_bg(self, instance, value):
        self.bg.pos = instance.pos
        self.bg.size = instance.size

    def select_char(self, stats):
        kivy.app.App.get_running_app().current_player = stats
        self.manager.current = "game_screen"

    def go_back(self, instance):
        self.manager.current = "main_menu"

    # ==========================================
    # --- [ระบบ Navigation (จอยสติ๊ก + เมาส์)] ---
    # ==========================================
    def on_enter(self):
        Window.bind(
            on_joy_axis=self._on_joy_axis, 
            on_joy_hat=self._on_joy_hat, 
            on_joy_button_down=self._on_joy_button_down,
            mouse_pos=self._on_mouse_pos # <--- Bind เมาส์
        )
        self.selected_index = 0
        self.show_highlight = False  
        self.update_highlight()

    def on_leave(self):
        Window.unbind(
            on_joy_axis=self._on_joy_axis, 
            on_joy_hat=self._on_joy_hat, 
            on_joy_button_down=self._on_joy_button_down,
            mouse_pos=self._on_mouse_pos # <--- Unbind เมาส์
        )

    # --- [ระบบตรวจจับเมาส์ Hover] ---
    def _on_mouse_pos(self, window, pos):
        # เช็คว่าเมาส์ชนโดนปุ่มไหนบ้าง
        for i, btn in enumerate(self.selectable_buttons):
            if btn.collide_point(*pos):
                self.selected_index = i
                self.show_highlight = True
                self.update_highlight()
                return 
        
        # ถ้าเมาส์ไม่โดนปุ่มไหนเลย ให้ปิดแสง Highlight
        if self.show_highlight:
            self.show_highlight = False
            self.update_highlight()

    def update_highlight(self):
        for i, btn in enumerate(self.selectable_buttons):
            # เช็คว่าตรงกับ Index ที่เลือก "และ" โชว์ Highlight ทำงานอยู่
            if i == self.selected_index and self.show_highlight:
                
                # --- [ตอนชี้ปุ่ม (Highlight สว่างขึ้น)] ---
                if btn.text == "BACK TO MENU":
                    # แดงสว่างจ้า! (ปรับให้สว่างขึ้นเพื่อความชัดเจน)
                    btn.background_color = (0.9, 0.2, 0.2, 1) 
                else:
                    btn.background_color = (0.3, 0.5, 0.7, 1) # ฟ้าสว่าง
            else:
                
                # --- [ตอนไม่ได้ชี้ปุ่ม (สีปกติ)] ---
                if btn.text == "BACK TO MENU":
                    # ปุ่ม Back ให้เป็นสีแดงหม่น/แดงเข้ม
                    btn.background_color = (0.4, 0.1, 0.1, 0.85) 
                else:
                    # ปุ่มอื่นๆ เป็นสีเทาปกติ
                    btn.background_color = (0.1, 0.15, 0.2, 0.85)

    def _reset_cooldown(self, dt):
        self.joy_cooldown = False

    def navigate(self, direction):
        if self.joy_cooldown: return
        self.joy_cooldown = True
        self.show_highlight = True  # ขยับจอยปุ๊บ เปิดโหมด Highlight
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
        self.show_highlight = True  # กดจอยปุ๊บ เปิดโหมด Highlight
        self.update_highlight()
        
        if buttonid == 0:  # ปุ่ม A (ยืนยัน)
            self.selectable_buttons[self.selected_index].dispatch('on_press')
        elif buttonid == 1:  # ปุ่ม B (คีย์ลัดกดยกเลิก/กลับ)
            self.go_back(None)
    # ==========================================