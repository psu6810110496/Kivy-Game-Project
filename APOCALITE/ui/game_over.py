from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.app import App
from kivy.animation import Animation
from kivy.uix.textinput import TextInput
from game.score_manager import ScoreManager
from ui.font import PIXEL_FONT

class GameOverPopup(Popup):
    def __init__(self, win=False, game_screen=None, **kwargs):
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
        self.score_label = None
        # สำหรับ Navigation ด้วยจอย
        self.selectable_buttons = []
        self.selected_index = 0
        self.show_highlight = False
        self.joy_cooldown = False
        self.win = win
        
        # --- Score calculation ---
        self.score = 0
        self.character = "Unknown"
        self.time_survived = 0.0
        self.level = 1
        self.kills = 0
        
        if game_screen:
            self.time_survived = getattr(game_screen, "play_time", 0.0)
            self.kills = getattr(game_screen, "total_kills", 0)
            if game_screen.player_stats:
                self.level = getattr(game_screen.player_stats, "level", 1)
                self.character = getattr(game_screen.player_stats, "name", "Unknown")
            
            # Formula: (Time x 10) + (kills x 5) + (level x 50)
            self.score = int(self.time_survived * 10) + (self.kills * 5) + (self.level * 50)
            if win:
                self.score += 5000

        # Bind อีเวนต์ตอน Popup เปิด/ปิด
        self.bind(on_open=self._on_open, on_dismiss=self._remove_joy)

        layout = BoxLayout(orientation="vertical", padding=20, spacing=20)
        
        # ข้อความแจ้งเตือน
        text = "VICTORY!" if win else "YOU DIED"
        color = (1, 0.84, 0, 1) if win else (1, 0, 0, 1) # Gold = Win, Red = Die

        die_label = Label(
            text=text,
            font_size=80 if win else 50, # Larger for victory
            font_name=PIXEL_FONT,
            color=color,
            bold=True,
            size_hint_y=None,
            height=120 if win else 80
        )
        die_label.opacity = 0  # ให้ค่อย ๆ โผล่ทีหลัง
        self.die_label = die_label
        
        # --- Stats Label ---
        mins, secs = divmod(int(self.time_survived), 60)
        time_str = f"{mins:02d}:{secs:02d}"
        score_text = f"Time: {time_str} | Kills: {self.kills} | Lvl: {self.level}\nTOTAL SCORE: {self.score}"
        self.score_label = Label(
            text=score_text, 
            font_size=24, 
            font_name=PIXEL_FONT, 
            color=(1,1,1,1), 
            halign="center",
            size_hint_y=None,
            height=60
        )
        self.score_label.bind(size=lambda i,v: setattr(i, 'text_size', (v[0], None))) # Wrap text
        self.score_label.opacity = 0

        # --- Name Input ---
        self.name_input = TextInput(
            hint_text="Enter Name",
            font_size=24,
            font_name=PIXEL_FONT,
            size_hint=(None, None),
            size=(250, 45),
            pos_hint={'center_x': 0.5},
            multiline=False,
            halign="center"
        )
        self.name_input.opacity = 0

        # ปุ่ม Try Again -> เปลี่ยนเป็น Label แบบ "ลอย" (ใช้ฟอนต์เหมือน PausePopup)
        retry_lbl = Label(
            text="TRY AGAIN (Don't Save)",
            font_size=30,
            font_name=PIXEL_FONT,
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
            text="SAVE & BACK TO MENU",
            font_size=30,
            font_name=PIXEL_FONT,
            bold=True,
            size_hint_y=None,
            height=50,
            color=(1, 1, 1, 1),
        )
        menu_lbl.opacity = 0
        menu_lbl.callback = self.save_and_return_to_menu
        menu_lbl.bind(on_touch_down=self._on_label_pressed)
        self.menu_btn = menu_lbl
        self.selectable_buttons.append(menu_lbl)

        # ปุ่มกลับหน้าเมนูแบบไม่เซฟ
        no_save_menu_lbl = Label(
            text="BACK TO MENU (Don't Save)",
            font_size=30,
            font_name=PIXEL_FONT,
            bold=True,
            size_hint_y=None,
            height=50,
            color=(1, 1, 1, 1),
        )
        no_save_menu_lbl.opacity = 0
        no_save_menu_lbl.callback = self.back_to_menu_no_save
        no_save_menu_lbl.bind(on_touch_down=self._on_label_pressed)
        self.no_save_menu_btn = no_save_menu_lbl
        self.selectable_buttons.append(no_save_menu_lbl)

        layout.add_widget(die_label)
        layout.add_widget(self.score_label)
        layout.add_widget(self.name_input)
        layout.add_widget(retry_lbl)
        layout.add_widget(menu_lbl)
        layout.add_widget(no_save_menu_lbl)
        self.content = layout

    def save_and_return_to_menu(self, instance):
        name = self.name_input.text.strip()
        if not name:
            name = "Player"
            
        mins, secs = divmod(int(self.time_survived), 60)
        time_str = f"{mins:02d}:{secs:02d}"
            
        ScoreManager.save_score(name, self.score, self.character, time_str, self.level, self.kills)
        
        self.dismiss()
        # 🌟 ไปที่ main_menu เสมอ (ไม่วนกลับ credits_screen)
        App.get_running_app().root.current = "main_menu"

    def back_to_menu_no_save(self, instance):
        """กลับหน้าเมนูโดยไม่บันทึกคะแนน"""
        self.dismiss()
        App.get_running_app().root.current = "main_menu"

    def try_again(self, instance):
        """เริ่มเกมใหม่ทันทีด้วยตัวละครเดิม"""
        app = App.get_running_app()
        sm = app.root
        game_screen = sm.get_screen("game_screen")

        # รีเซ็ต Player
        if hasattr(app, "current_player") and app.current_player:
            app.current_player.reset()

        # รีเซ็ต GameScreen state
        game_screen.on_leave()
        game_screen.on_enter()

        self.dismiss()

        # 🌟 เปลี่ยน Screen ไป game_screen เพื่อให้หน้าดำหายไป
        def _switch(dt):
            sm.current = "game_screen"
        Clock.schedule_once(_switch, 0.1)

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
                buttons_anim.start(self.score_label)
                buttons_anim.start(self.name_input)
                buttons_anim.start(self.retry_btn)
                buttons_anim.start(self.menu_btn)
                buttons_anim.start(self.no_save_menu_btn)

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
        # 🌟 ถ้ากำลังพิมพ์ชื่ออยู่ ให้ Keyboard ทำงานปกติ (พิมพ์ตัวอักษร)
        # ไม่ให้ WASD/Space มาเลื่อนปุ่ม
        if self.name_input.focus:
            return False

        if key in (119, 97, 273, 276): # W, A, Up, Left
            self._navigate("prev")
            return True
        elif key in (115, 100, 274, 275): # S, D, Down, Right
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
            self.save_and_return_to_menu(self.menu_btn)

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