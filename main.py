from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.graphics import Rectangle, Color, PushMatrix, PopMatrix, Translate
from kivy.clock import Clock
from kivy.config import Config
import random
from kivy.graphics import Rotate, PushMatrix, PopMatrix
from kivy.graphics import Rectangle, Color, PushMatrix, PopMatrix, Translate, Scale, Rotate, Ellipse

Config.set('input', 'mouse', 'mouse,disable_multitouch')

Config.set('graphics', 'fullscreen', 'auto')
Config.set('graphics', 'resizable', '0')

Window.maximize()

class RainEffect(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.drops = []
        self.num_drops = 100 
        
        with self.canvas:
            Color(0.6, 0.6, 0.6, 0.4) 
            for _ in range(self.num_drops):
                PushMatrix()
                
                # 1. มุมเอียงเป็นลบ (-20) เพื่อให้เม็ดเอียงชี้ไปทางขวา
                rotation = Rotate(angle=20, origin=(0, 0)) 
                
                rect = Rectangle(
                    # สุ่ม X เผื่อไปทางซ้ายนอกจอ เพราะฝนจะวิ่งจากซ้ายไปขวา
                    pos=(random.uniform(-Window.width * 0.5, Window.width), 
                         random.uniform(0, Window.height)), 
                    size=(2, random.uniform(10, 25))
                )
                
                PopMatrix()

                drop = {
                    'rect': rect,
                    'rotation': rotation,
                    'speed': random.uniform(7, 15)
                }
                self.drops.append(drop)
        
        Clock.schedule_interval(self.update_rain, 1/60.0)

    def update_rain(self, dt):
        for drop in self.drops:
            x, y = drop['rect'].pos
            
            # 2. ปรับให้ตกเฉียงขวา: y ลดลง (ลงล่าง), x เพิ่มขึ้น (ไปขวา)
            y -= drop['speed']
            x += drop['speed'] * 0.4  # ปรับตัวคูณเพื่อเปลี่ยนความชัน
            
            drop['rotation'].origin = (x, y)

            # 3. ตรวจสอบขอบล่าง และขอบขวา
            if y < -30 or x > Window.width:
                y = Window.height + random.uniform(10, 100)
                # สุ่มเกิดใหม่จากทางซ้าย (รวมนอกจอฝั่งซ้าย) เพื่อให้เฉียงเข้าหาจอ
                x = random.uniform(-Window.width * 0.5, Window.width)
                
            drop['rect'].pos = (x, y)

# ==========================================
# 1. Data Model
# ==========================================
class PlayerStats:
    def __init__(self, name, hp, speed, damage):
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.speed = speed
        self.damage = damage
        self.level = 1
        self.exp = 0

# ==========================================
# 2. Widgets & Popups
# ==========================================
class PlayerWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.canvas.clear()
        
        # --- 1. เตรียมรายชื่อไฟล์ Animation ---
        self.anim_idle = ['assets/Monkey/IdleM/IdleM01.png', 'assets/Monkey/IdleM/IdleM02.png'] # ภาพตอนยืนนิ่ง
        self.anim_walk = ['assets/Monkey/WalkM/W01.png', 'assets/Monkey/WalkM/W02.png', 'assets/Monkey/WalkM/W03.png', 'assets/Monkey/WalkM/W04.png'] # ภาพตอนเดิน
        
        # --- 2. กำหนดความเร็วแยกกัน (วินาทีต่อเฟรม) ---
        self.idle_speed = 0.5   
        self.walk_speed = 0.15  
        
        # สถานะปัจจุบัน
        self.current_anim = self.anim_idle
        self.current_anim_speed = self.idle_speed 
        self.frame_index = 0
        self.anim_timer = 0
        self.is_facing_right = True 
        
        # --- [จุดสำคัญ] วาดตัวละคร (ตอนนี้มีแค่บล็อกเดียวแล้ว จะไม่มีร่างแยก) ---
        with self.canvas:
            self.color_inst = Color(1, 1, 1, 1) 
            self.rect = Rectangle(
                source=self.current_anim[0],  
                pos=(2500, 2500), 
                size=(64, 64)  
            )
            
        # --- วาดจุดเล็งเป้า (Aim Marker) วาดทับด้านบน ---
        with self.canvas.after:
            self.aim_color = Color(1, 0, 0, 0) # กำหนดค่า Alpha เป็น 0 เพื่อซ่อนไว้ก่อน
            self.aim_marker = Ellipse(size=(10, 10), pos=(0, 0)) 

        Clock.schedule_interval(self.animate, 1.0/60.0)

    def update_aim(self, is_aiming, aim_x, aim_y):
        if is_aiming and (aim_x != 0 or aim_y != 0):
            self.aim_color.a = 1.0  
            
            mag = (aim_x**2 + aim_y**2) ** 0.5
            if mag > 0:
                aim_x /= mag
                aim_y /= mag
                
            radius = 60  
            
            center_x = self.rect.pos[0] + (self.rect.size[0] / 2)
            center_y = self.rect.pos[1] + (self.rect.size[1] / 2)
            
            self.aim_marker.pos = (
                center_x + (aim_x * radius) - (self.aim_marker.size[0] / 2),
                center_y + (aim_y * radius) - (self.aim_marker.size[1] / 2)
            )
        else:
            self.aim_color.a = 0.0  

    def set_state(self, is_moving, facing_right=None, current_speed=5.0):
        if facing_right is not None:
            self.is_facing_right = facing_right
            
        base_speed_ref = 5.0 
        safe_speed = max(current_speed, 1.0) 
        dynamic_walk_speed = self.walk_speed * (base_speed_ref / safe_speed)
        
        new_anim = self.anim_walk if is_moving else self.anim_idle
        new_speed = dynamic_walk_speed if is_moving else self.idle_speed
        
        if self.current_anim != new_anim:
            self.current_anim = new_anim
            self.current_anim_speed = new_speed 
            self.frame_index = 0 
            self.anim_timer = 0 
        else:
            self.current_anim_speed = new_speed

    def animate(self, dt):
        self.anim_timer += dt
        
        if self.anim_timer >= self.current_anim_speed:
            self.anim_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.current_anim)
            self.rect.source = self.current_anim[self.frame_index]
            
        if self.is_facing_right:
            self.rect.tex_coords = (0, 1, 1, 1, 1, 0, 0, 0) 
        else:
            self.rect.tex_coords = (1, 1, 0, 1, 0, 0, 1, 0) 

    def update_pos(self, new_pos):
        self.rect.pos = new_pos

class LevelUpPopup(Popup):
    def __init__(self, game_screen, **kwargs):
        super().__init__(**kwargs)
        self.game_screen = game_screen
        self.title = "LEVEL UP! Choose your Upgrade:"
        self.title_size = 24
        self.size_hint = (0.6, 0.5)
        self.auto_dismiss = False
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        cards_layout = GridLayout(cols=3, spacing=15)
        
        upgrades = ["+ Damage", "+ Max HP", "+ Speed"]
        for upg in upgrades:
            btn = Button(text=upg, font_size=20)
            btn.bind(on_press=self.apply_upgrade)
            cards_layout.add_widget(btn)
            
        layout.add_widget(cards_layout)
        self.content = layout

    def apply_upgrade(self, instance):
        player = App.get_running_app().current_player
        if player:
            if "+ Damage" in instance.text: player.damage += 5
            elif "+ Max HP" in instance.text: player.hp += 20
            elif "+ Speed" in instance.text: player.speed += 2
        self.game_screen.resume_game()
        self.dismiss()

class PausePopup(Popup):
    def __init__(self, game_screen, **kwargs):
        super().__init__(**kwargs)
        self.game_screen = game_screen
        self.title = "GAME PAUSED"
        self.size_hint = (0.4, 0.4)
        self.auto_dismiss = False
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        btn_resume = Button(text="RESUME", size_hint=(1, 0.5))
        btn_menu = Button(text="RETURN TO MENU", size_hint=(1, 0.5))
        
        btn_resume.bind(on_press=self.resume)
        btn_menu.bind(on_press=self.go_to_menu)
        
        layout.add_widget(btn_resume)
        layout.add_widget(btn_menu)
        self.content = layout

    def resume(self, instance):
        self.game_screen.resume_game()
        self.dismiss()

    def go_to_menu(self, instance):
        self.dismiss()
        self.game_screen.manager.current = 'main_menu'

class CountdownOverlay(Label):
    def __init__(self, callback, **kwargs):
        super().__init__(**kwargs)
        self.callback = callback
        self.count = 3
        self.text = str(self.count)
        self.font_size = 200
        self.bold = True
        self.color = (1, 0.8, 0, 1) # สีเหลืองทอง
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        Clock.schedule_interval(self.update_countdown, 1)

    def update_countdown(self, dt):
        self.count -= 1
        if self.count > 0:
            self.text = str(self.count)
        elif self.count == 0:
            self.text = "SURVIVE!"
            self.color = (1, 0.2, 0.2, 1) # สีแดง
        else:
            Clock.unschedule(self.update_countdown)
            self.callback() # เรียกให้เริ่มเกม
            if self.parent:
                self.parent.remove_widget(self)

# ==========================================
# 3. UI Screens
# ==========================================
class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        main_layout = FloatLayout()

        with main_layout.canvas.before:
            Color(1, 1, 1, 1)
            self.bg_rect = Rectangle(
                source='assets/Menu/MenuTest.png', 
                pos=(0, 0),
                size=Window.size
            )
        
        self.rain = RainEffect()
        main_layout.add_widget(self.rain)

        menu_group = BoxLayout(
            orientation='vertical', spacing=45,
            size_hint=(None, None), size=(800, 600), 
            pos_hint={'x': 0.1, 'top': 0.9} 
        )

        title_label = Label(text="VAMPIRE SURVIVORS", font_size=70, bold=True, halign='left', valign='middle', size_hint=(1, None), height=150)
        title_label.bind(size=title_label.setter('text_size'))

        btn_start = Button(text="START SURVIVING", font_size=26, size_hint=(0.4, None), height=80, pos_hint={'center_x': 0.33}, background_color=(1,1,1,0.8))
        btn_quit = Button(text="QUIT GAME", font_size=26, size_hint=(0.4, None), height=80, pos_hint={'center_x': 0.33}, background_color=(1,1,1,0.8))

        btn_start.bind(on_press=lambda x: self.change_screen('char_select_screen'))
        btn_quit.bind(on_press=lambda x: App.get_running_app().stop())

        menu_group.add_widget(title_label)
        menu_group.add_widget(btn_start)
        menu_group.add_widget(btn_quit)
        
        main_layout.add_widget(menu_group)
        self.add_widget(main_layout)
        
        Window.bind(size=self._update_bg)

    def _update_bg(self, instance, value):
        self.bg_rect.size = value
        self.bg_rect.pos = (0, 0)

    def change_screen(self, screen_name):
        self.manager.current = screen_name

class CharacterSelectScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.char_data = {
            "Survivor": PlayerStats("Survivor", 100, 5, 10),
            "Scavenger": PlayerStats("Scavenger", 70, 10, 5),
            "Veteran": PlayerStats("Veteran", 200, 2, 15)
        }
        layout = BoxLayout(orientation='vertical', padding=50, spacing=20)
        layout.add_widget(Label(text="SELECT YOUR CHARACTER", font_size=30))
        
        chars = BoxLayout(spacing=20)
        for name, stats in self.char_data.items():
            btn = Button(text=f"{name}\nHP: {stats.hp}\nSPD: {stats.speed}")
            btn.bind(on_press=lambda inst, s=stats: self.select_char(s))
            chars.add_widget(btn)
        
        layout.add_widget(chars)
        self.add_widget(layout)

    def select_char(self, stats):
        App.get_running_app().current_player = stats
        self.manager.current = 'game_screen'

class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.keys_pressed = set()
        self.player_pos = [2500, 2500]
        self.player_stats = None 
        self.is_paused = False
        
        # --- ตัวแปรสำหรับระบบ Dash ---
        self.is_dashing = False
        self.dash_cooldown = False
        self.dash_speed_multiplier = 3.0 # ความเร็วจะเพิ่มเป็น 3 เท่าตอน Dash
        self.dash_duration = 0.2         # พุ่งตัวเป็นเวลา 0.2 วินาที
        self.dash_cooldown_time = 1.0    # รอ 1 วินาทีก่อน Dash ใหม่ได้
        
        # เก็บทิศทางล่าสุดที่เดิน เพื่อให้ Dash ไปทางนั้น
        self.last_dir_x = 0
        self.last_dir_y = 0
        
        # --- เพิ่มตัวแปรเก็บทิศทางการหันหน้า และสถานะเมาส์ ---
        self.facing_right = True 
        self.is_left_clicked = False  # เช็คว่ากดคลิกซ้ายค้างอยู่ไหม
        
        Window.bind(on_key_down=self._on_keydown)
        Window.bind(on_key_up=self._on_keyup)

        # ... โค้ดเดิมด้านบน ...
        self.facing_right = True 
        self.is_left_clicked = False  # เช็คว่ากดคลิกซ้ายค้างอยู่ไหม
        
        # --- ตัวแปรสำหรับจอยสติ๊ก ---
        self.joy_x = 0.0
        self.joy_y = 0.0
        self.joy_deadzone = 0.2
        
        # เพิ่มตัวแปรใหม่ตรงนี้
        self.joy_right_x = 0.0
        self.joy_right_y = 0.0
        self.joy_lt_pressed = False  # เช็คว่ากด LT ค้างอยู่ไหม
        
        Window.bind(on_key_down=self._on_keydown)
        Window.bind(on_key_up=self._on_keyup)
        # ผูก Event สำหรับจอยสติ๊ก
        Window.bind(on_joy_axis=self._on_joy_axis)
        Window.bind(on_joy_button_down=self._on_joy_button_down)
        # ...

        self.root_layout = FloatLayout()
        
        self.world_layout = FloatLayout(size_hint=(None, None), size=(5000, 5000)) 
        with self.world_layout.canvas.before:
            PushMatrix()
            # ปรับกลับเป็น 1, 1, 1 เพื่อให้มุมกล้องกลับไปเป็นขนาดดั้งเดิม
            # (หรือเปลี่ยนเป็น 0.7, 0.7, 1 ถ้าอยากได้มุมกว้างแบบที่ผมทำให้อันแรกครับ)
            self.zoom = Scale(2, 2, 2) 
            
            self.camera = Translate(0, 0)
            Color(0.2, 0.2, 0.2, 1)
            for i in range(0, 5001, 100):
                Rectangle(pos=(0, i), size=(5000, 1)) 
                Rectangle(pos=(i, 0), size=(1, 5000)) 
        with self.world_layout.canvas.after:
            PopMatrix()
            
        self.player_widget = PlayerWidget()
        self.world_layout.add_widget(self.player_widget)
        self.root_layout.add_widget(self.world_layout)

        self.hud = FloatLayout(size_hint=(1, 1))
        top_ui = BoxLayout(size_hint=(0.8, 0.05), pos_hint={'center_x': 0.5, 'top': 0.98}, spacing=10)
        self.lbl_level = Label(text="LV: 1", size_hint=(0.1, 1), bold=True)
        self.exp_bar = ProgressBar(max=100, value=0)
        top_ui.add_widget(self.lbl_level)
        top_ui.add_widget(self.exp_bar)
        self.hud.add_widget(top_ui)
        
        btn_pause = Button(text="||", size_hint=(None, None), size=(50, 50), pos_hint={'right': 0.98, 'top': 0.98})
        btn_pause.bind(on_press=self.pause_game)
        self.hud.add_widget(btn_pause)

        btn_test = Button(text="+EXP", size_hint=(None, None), size=(80, 40), pos_hint={'right': 0.98, 'y': 0.02})
        btn_test.bind(on_press=self.gain_exp)
        self.hud.add_widget(btn_test)

        self.root_layout.add_widget(self.hud)
        self.add_widget(self.root_layout)

    def on_enter(self):
        self.player_stats = App.get_running_app().current_player
        if self.player_stats:
            self.is_paused = True 
            self.update_ui()
            
            self.countdown = CountdownOverlay(callback=self.start_actual_game)
            self.root_layout.add_widget(self.countdown)
            
            Clock.schedule_interval(self.update_frame, 1.0/60.0)

    def start_actual_game(self):
        self.is_paused = False 

    def on_leave(self):
        Clock.unschedule(self.update_frame)
        self.is_paused = False
        self.player_pos = [2500, 2500]

    def update_ui(self):
        if self.player_stats:
            self.lbl_level.text = f"LV: {self.player_stats.level}"
            self.exp_bar.value = self.player_stats.exp

    def pause_game(self, instance):
        self.is_paused = True
        PausePopup(game_screen=self).open()

    def resume_game(self):
        self.is_paused = False
        self.keys_pressed.clear()

    def start_dash(self):
        if not self.dash_cooldown and not self.is_dashing:
            if self.last_dir_x != 0 or self.last_dir_y != 0:
                self.is_dashing = True
                self.dash_cooldown = True
                
                # เปลี่ยนสีตัวละครเป็นออร่าสีเหลือง (โดยไม่ต้อง clear canvas)
                self.player_widget.color_inst.rgba = (1, 1, 0, 1) 
                
                Clock.schedule_once(self.end_dash, self.dash_duration)
                Clock.schedule_once(self.reset_dash_cooldown, self.dash_cooldown_time)

    def end_dash(self, dt):
        self.is_dashing = False
        # เปลี่ยนสีตัวละครกลับเป็นสีปกติ
        self.player_widget.color_inst.rgba = (1, 1, 1, 1)

    def reset_dash_cooldown(self, dt):
        self.dash_cooldown = False

    def on_touch_down(self, touch):
        # เช็คว่าเป็นการคลิกซ้ายหรือไม่
        if 'button' in touch.profile and touch.button == 'left':
            self.is_left_clicked = True  # <--- บันทึกว่ากำลังกดเมาส์อยู่
            
            # เช็คว่าคลิกที่ครึ่งขวาหรือครึ่งซ้ายของหน้าจอ
            if touch.x > Window.width / 2:
                self.facing_right = True
            else:
                self.facing_right = False
                
        return super().on_touch_down(touch)
    
    def on_touch_move(self, touch):
        # เช็คว่าเป็นการกดเมาส์ซ้ายค้างไว้หรือไม่
        if 'button' in touch.profile and touch.button == 'left':
            # เช็คตำแหน่ง X ของเมาส์ขณะลาก ว่าอยู่ฝั่งซ้ายหรือขวาของจอ
            if touch.x > Window.width / 2:
                self.facing_right = True
            else:
                self.facing_right = False
                
        return super().on_touch_move(touch)
    
    def on_touch_up(self, touch):
        # เมื่อปล่อยเมาส์ซ้าย ให้รีเซ็ตสถานะ
        if 'button' in touch.profile and touch.button == 'left':
            self.is_left_clicked = False
            
        return super().on_touch_up(touch)
    
    def _on_joy_axis(self, window, stickid, axisid, value):
        # Kivy คืนค่า Analog ตั้งแต่ -32768 ถึง 32767 เราต้องแปลงให้เป็น -1.0 ถึง 1.0
        normalized = value / 32767.0
        
        # กรองค่าที่น้อยกว่า Deadzone ทิ้ง เพื่อป้องกันตัวละครเดินเองเวลาคันโยกเอียงนิดๆ
        if abs(normalized) < self.joy_deadzone:
            normalized = 0.0
            
        if axisid == 0: 
            # แกน X (ซ้าย-ขวา) ของ Analog ซ้าย
            self.joy_x = normalized
        elif axisid == 1: 
            # แกน Y (บน-ล่าง) ของ Analog ซ้าย (Kivy มักจะสลับแกน Y บนล่าง จึงต้องใส่ลบ)
            self.joy_y = -normalized 
            
    def _on_joy_button_down(self, window, stickid, buttonid):
        # Index ปุ่มของจอย Xbox ปกติ: A=0, B=1, X=2, Y=3, LB=4, RB=5, Back=6, Start=7
        if buttonid == 0: 
            # กดปุ่ม A เพื่อ Dash
            self.start_dash()
        elif buttonid == 7: 
            # กดปุ่ม Start เพื่อ Pause
            self.pause_game(None)

    def update_frame(self, dt):
        if not self.player_stats or self.is_paused:
            return

        current_speed = self.player_stats.speed
        if self.is_dashing:
            current_speed *= self.dash_speed_multiplier

        dir_x, dir_y = 0, 0
        
        if not self.is_dashing:
            # 1. เช็คคีย์บอร์ดก่อน
            if 'w' in self.keys_pressed: dir_y += 1
            if 's' in self.keys_pressed: dir_y -= 1
            if 'a' in self.keys_pressed: dir_x -= 1
            if 'd' in self.keys_pressed: dir_x += 1
            
            # 2. ถ้าไม่ได้กดคีย์บอร์ด ให้ดึงค่า Analog ของจอยมาใช้
            if dir_x == 0 and dir_y == 0:
                dir_x = self.joy_x
                dir_y = self.joy_y
            
            if dir_x != 0 or dir_y != 0:
                self.last_dir_x = dir_x
                self.last_dir_y = dir_y
        else:
            dir_x = self.last_dir_x
            dir_y = self.last_dir_y

        # --- ปรับแก้ความเร็วแนวทแยง (รองรับทั้งจอยและคีย์บอร์ด) ---
        # แทนที่การคูณ 0.7071 แบบเดิม ด้วยสูตรเวกเตอร์ เพื่อให้ความเร็วคงที่เสมอ
        magnitude = (dir_x**2 + dir_y**2) ** 0.5
        if magnitude > 1.0:
            dir_x /= magnitude
            dir_y /= magnitude
            
        self.player_pos[0] += dir_x * current_speed
        self.player_pos[1] += dir_y * current_speed
            
        self.player_widget.update_pos(self.player_pos)
        
        # --- โค้ดควบคุม Animation ---
        is_moving = (dir_x != 0 or dir_y != 0)
        
        if not self.is_left_clicked:
            # เช็คว่าเดินไปทางซ้ายหรือขวา (ใช้ 0.1 แทน 0 เพื่อป้องกันจอยสั่นนิดเดียวแล้วหันหน้า)
            if dir_x > 0.1:
                self.facing_right = True
            elif dir_x < -0.1:
                self.facing_right = False
                
        self.player_widget.set_state(is_moving, self.facing_right, current_speed)
        # -----------------------------------------------
        
        # --- โค้ดควบคุม Animation ---
        is_moving = (dir_x != 0 or dir_y != 0)
        
        if self.is_left_clicked:
            pass 
        elif self.joy_lt_pressed:
            if self.joy_right_x > 0.1:
                self.facing_right = True
            elif self.joy_right_x < -0.1:
                self.facing_right = False
        else:
            if dir_x > 0.1:
                self.facing_right = True
            elif dir_x < -0.1:
                self.facing_right = False
                
        self.player_widget.set_state(is_moving, self.facing_right, current_speed)
        
        # --- อัปเดตตำแหน่งจุดเล็งเป้าด้วยค่าจาก Analog ขวา ---
        self.player_widget.update_aim(
            self.joy_lt_pressed, 
            self.joy_right_x, 
            self.joy_right_y
        )
        
        # ⚠️ (ลบ self.zoom.origin ที่ซ้ำซ้อนออก ให้เหลือบรรทัดเดียว)
        self.zoom.origin = (Window.width / 2, Window.height / 2)
        self.camera.x = (Window.width / 2) - self.player_pos[0] - 25
        self.camera.y = (Window.height / 2) - self.player_pos[1] - 25

    def gain_exp(self, instance):
        if self.player_stats:
            self.player_stats.exp += 35
            if self.player_stats.exp >= 100:
                self.player_stats.level += 1
                self.player_stats.exp -= 100
                self.is_paused = True
                LevelUpPopup(game_screen=self).open()
            self.update_ui()

    def _on_keydown(self, window, key, scancode, codepoint, modifiers):
        if key == 292: # F11
            Window.fullscreen = not Window.fullscreen
            return True
            
        # ตรวจจับปุ่ม Spacebar (keycode: 32) เพื่อเริ่ม Dash
        if key == 32:
            self.start_dash()
            return True
        
        if codepoint: self.keys_pressed.add(codepoint.lower())
        if key == 27: 
            self.pause_game(None)
            return True 

    def _on_keyup(self, window, key, scancode):
        try:
            key_char = chr(key).lower()
            if key_char in self.keys_pressed:
                self.keys_pressed.remove(key_char)
        except: pass

    def _on_joy_axis(self, window, stickid, axisid, value):
        normalized = value / 32767.0
        
        # กรองค่าที่น้อยกว่า Deadzone ทิ้ง
        if abs(normalized) < self.joy_deadzone:
            normalized = 0.0
            
        if axisid == 0: 
            # แกน X ของ Analog ซ้าย
            self.joy_x = normalized
        elif axisid == 1: 
            # แกน Y ของ Analog ซ้าย
            self.joy_y = -normalized 
        elif axisid == 2:
            # แกน X ของ Analog ขวา (ใช้เล็งซ้าย-ขวา)
            self.joy_right_x = normalized
        elif axisid == 3:
            # แกน Y ของ Analog ขวา (เผื่อใช้เล็งบน-ล่างในอนาคต)
            self.joy_right_y = -normalized
        elif axisid == 4:
            # ปุ่ม LT (Left Trigger)
            # ปกติค่าปุ่ม Trigger จะเริ่มที่ -1.0 (ไม่ได้กด) จนถึง 1.0 (กดมิด)
            # ถ้าค่ามากกว่า 0.0 แสดงว่ากดลงไปเกินครึ่งนึงแล้ว
            self.joy_lt_pressed = (normalized > 0.0)
            
    def _on_joy_button_down(self, window, stickid, buttonid):
        # Index ปุ่มของจอย Xbox ปกติ: A=0, B=1, X=2, Y=3, LB=4, RB=5, Back=6, Start=7
        if buttonid == 0: 
            # กดปุ่ม A เพื่อ Dash
            self.start_dash()
        elif buttonid == 7: 
            # กดปุ่ม Start เพื่อ Pause
            self.pause_game(None)

class VampireApp(App):
    def build(self):
        self.current_player = None 
        sm = ScreenManager()
        sm.add_widget(MainMenuScreen(name='main_menu'))
        sm.add_widget(CharacterSelectScreen(name='char_select_screen'))
        sm.add_widget(GameScreen(name='game_screen'))
        return sm

if __name__ == '__main__':
    VampireApp().run()