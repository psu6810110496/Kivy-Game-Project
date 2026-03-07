from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Rectangle, Color
from kivy.core.window import Window
from kivy.clock import Clock
import random
from game.sound_manager import sound_manager


# --- คลาสเอฟเฟกต์ฝนตก ---
class RainEffect(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.drops = []
        self.num_drops = 150  # เพิ่มจำนวนเม็ดฝนให้ดูสมจริงขึ้น

        with self.canvas:
            # ใช้สีขาว/ฟ้าเทา โปร่งแสงนิดๆ ให้ดูเป็นเม็ดฝน
            Color(0.7, 0.8, 0.9, 0.4)
            for _ in range(self.num_drops):
                rect = Rectangle(
                    pos=(
                        random.uniform(-Window.width * 0.5, Window.width),
                        random.uniform(0, Window.height),
                    ),
                    size=(1.5, random.uniform(15, 35)),  # ปรับเม็ดฝนให้เรียวยาวขึ้น
                )

                drop = {"rect": rect, "speed": random.uniform(12, 22)}  # ความเร็วในการตก
                self.drops.append(drop)

        Clock.schedule_interval(self.update_rain, 1 / 60.0)

    def update_rain(self, dt):
        for drop in self.drops:
            x, y = drop["rect"].pos

            y -= drop["speed"]
            x += drop["speed"] * 0.15  # ปรับความเฉียงของฝนให้ดูพอดี

            if y < -50 or x > Window.width:
                y = Window.height + random.uniform(10, 100)
                x = random.uniform(-Window.width * 0.2, Window.width)

            drop["rect"].pos = (x, y)


# --- คลาสหน้าจอเมนูหลัก ---
class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 🌟 ลงทะเบียน Pixel Font จาก assets
        from kivy.core.text import LabelBase
        try:
            LabelBase.register(
                name="PixelFont",
                fn_regular="assets/fornt/Stacked pixel.ttf",
            )
        except Exception:
            pass

        # --- [ระบบ Joy Navigation] ---
        self.selectable_buttons = [] 
        self.selected_index = 0      
        self.joy_cooldown = False    
        # ---------------------------

        # 1. จัดการรูปพื้นหลังให้อยู่บนสุดของ Screen และปรับตาม Window
        with self.canvas.before:
            Color(1, 1, 1, 1)  # ตั้งเป็นสีขาวล้วนเพื่อไม่ให้สีรูปเพี้ยน
            self.bg_rect = Rectangle(
                source="assets/Menu/MenuTest.png", pos=self.pos, size=Window.size
            )

        # ผูกการอัปเดตขนาดให้เท่ากับ Window เสมอ ไม่ว่าจะย่อหรือขยายจอ
        self.bind(pos=self._update_bg, size=self._update_bg)

        main_layout = FloatLayout()

        # 2. เพิ่มเอฟเฟกต์ฝน
        self.rain = RainEffect()
        main_layout.add_widget(self.rain)

        # 3. จัดวางกรอบเมนู (ขยับมาอยู่ตรงกลางแนวตั้ง)
        menu_group = BoxLayout(
            orientation="vertical",
            spacing=30,
            size_hint=(None, None),
            size=(700, 540),
            pos_hint={"x": 0.1, "center_y": 0.48},
        )

        # ปรับสี Title ให้เข้ากับธีมบรรยากาศฝนตก (สีฟ้าอ่อนอมเทา)
        title_label = Label(
            text="APOCALITE",
            font_size=140,
            font_name="PixelFont",
            color=(1, 1, 1, 1),
            halign="left",
            valign="middle",
            size_hint=(1, None),
            height=170,
        )
        title_label.bind(size=title_label.setter("text_size"))

        # 4. ปุ่มแบบ Text ลอยๆ ไม่มีพื้นหลัง
        btn_layout = BoxLayout(
            orientation="vertical", spacing=8, size_hint=(None, None), size=(500, 360)
        )

        def make_menu_label(text, callback, is_quit=False):
            color = (0.7, 0.75, 0.8, 0.85)
            lbl = Label(
                text=text,
                font_size=42,
                font_name="PixelFont",
                size_hint=(1, None),
                height=75,
                color=color,
                halign="left",
                valign="middle",
            )
            lbl.bind(size=lbl.setter("text_size"))
            lbl._callback = callback
            lbl._is_quit = is_quit
            lbl._base_color = color

            def on_touch(obj, touch):
                if obj.collide_point(*touch.pos):
                    sound_manager.play_sfx("button")
                    obj._callback()
                    return True
                return False
            lbl.bind(on_touch_down=on_touch)
            return lbl

        btn_start      = make_menu_label("PLAY", lambda: self.change_screen("char_select_screen"))
        btn_leaderboard= make_menu_label("LEADERBOARD",    lambda: self.change_screen("leaderboard_screen"))
        btn_settings   = make_menu_label("SETTINGS",       lambda: self.open_settings())
        btn_quit       = make_menu_label("QUIT GAME",      lambda: App.get_running_app().stop(), is_quit=True)

        btn_layout.add_widget(btn_start)
        btn_layout.add_widget(btn_leaderboard)
        btn_layout.add_widget(btn_settings)
        btn_layout.add_widget(btn_quit)

        # --- [เก็บปุ่มลงใน List สำหรับจอย] ---
        self.selectable_buttons.clear()
        self.selectable_buttons.append(btn_start)
        self.selectable_buttons.append(btn_leaderboard)
        self.selectable_buttons.append(btn_settings)
        self.selectable_buttons.append(btn_quit)

        menu_group.add_widget(title_label)
        menu_group.add_widget(btn_layout)

        main_layout.add_widget(menu_group)
        self.add_widget(main_layout)

    # 5. ฟังก์ชันอัปเดตขนาดพื้นหลังให้ติดหนึบกับหน้าจอ
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def open_settings(self):
        self.manager.current = "settings_screen"
        self.manager.get_screen("settings_screen").set_previous_screen("main_menu")

    def change_screen(self, screen_name):
        self.manager.current = screen_name

    def go_back(self, instance):
        """
        ฟังก์ชันกลับจากเมนูหลักเมื่อกดปุ่ม B บนจอย
        ในหน้าหลักเราจะถือว่าเป็นการออกจากเกม (เหมือนกด QUIT GAME)
        """
        App.get_running_app().stop()

    # ==========================================
    # --- [ระบบ Navigation (จอยสติ๊ก + เมาส์)] ---
    # ==========================================
    def on_enter(self):
        Window.bind(
            on_joy_axis=self._on_joy_axis, 
            on_joy_hat=self._on_joy_hat, 
            on_joy_button_down=self._on_joy_button_down,
            mouse_pos=self._on_mouse_pos, # <--- เพิ่ม Event จับการขยับเมาส์
            on_key_down=self._on_keyboard_down
        )
        sound_manager.play_bgm("main_menu")
        self.selected_index = 0
        self.show_highlight = False  # <--- ใช้ตัวนี้คุมแสง Highlight ทั้งคู่
        self.update_highlight()

    def on_leave(self):
        Window.unbind(
            on_joy_axis=self._on_joy_axis, 
            on_joy_hat=self._on_joy_hat, 
            on_joy_button_down=self._on_joy_button_down,
            mouse_pos=self._on_mouse_pos, # <--- อย่าลืม unbind เมาส์ตอนออกหน้าด้วย
            on_key_down=self._on_keyboard_down
        )

    # --- [ระบบ Keyboard WASD + Space] ---
    def _on_keyboard_down(self, window, key, scancode, codepoint, modifiers):
        if key == 119 or key == 97: # W or A
            self.navigate("prev")
            return True
        elif key in (115, 100, 274, 275): # S, D or Down, Right
            self.navigate("next")
            return True
        elif key == 32 or key == 13: # Spacebar or Enter
            self.show_highlight = True
            self.update_highlight()
            if self.selectable_buttons:
                # เรียก callback ของ Label โดยตรง
                if hasattr(lbl, '_callback'):
                    sound_manager.play_sfx("button")
                    lbl._callback()
            return True
        return False

    # --- [ระบบตรวจจับเมาส์ Hover] ---
    def _on_mouse_pos(self, window, pos):
        # วนลูปเช็คว่าเมาส์ไปชน (Hover) โดนปุ่มไหนบ้าง
        for i, btn in enumerate(self.selectable_buttons):
            if btn.collide_point(*pos):
                self.selected_index = i
                self.show_highlight = True # เปิดแสง
                self.update_highlight()
                return # เจอแล้วก็จบการทำงานได้เลย
        
        # ถ้าขยับเมาส์ออกนอกปุ่มทั้งหมด ให้ปิดแสง Highlight
        if self.show_highlight:
            self.show_highlight = False
            self.update_highlight()

    def update_highlight(self):
        for i, lbl in enumerate(self.selectable_buttons):
            is_selected = (i == self.selected_index and self.show_highlight)
            is_quit = getattr(lbl, '_is_quit', False)
            base = getattr(lbl, '_base_color', (0.92, 0.96, 1.0, 1.0))
            if is_selected:
                # ไฮไลท์: เปลี่ยนสีตัวอักษรและเพิ่ม > อว < ด้านหน้า
                lbl.color = (1.0, 1.0, 1.0, 1.0)
                lbl.font_size = 48
                lbl.text = f"> {lbl.text.lstrip('> ').rstrip()}"
            else:
                lbl.color = base
                lbl.font_size = 42
                # ลบ > ออกถ้ามี
                if lbl.text.startswith("> "):
                    lbl.text = lbl.text[2:]

    def _reset_cooldown(self, dt):
        self.joy_cooldown = False

    def navigate(self, direction):
        if self.joy_cooldown: return
        self.joy_cooldown = True
        self.show_highlight = True  # ขยับจอยปุ๊บ เปิดแสง
        sound_manager.play_sfx("button") # ขยับเปลี่ยนปุ่มก็มีเสียง
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
        self.show_highlight = True # กดปุ่มจอยปุ๊บ เปิดแสง
        self.update_highlight()
        
        if buttonid == 0:  
            sound_manager.play_sfx("button")
            lbl = self.selectable_buttons[self.selected_index]
            if hasattr(lbl, '_callback'):
                lbl._callback()
        elif buttonid == 1:  
            self.go_back(None)
    # ==========================================