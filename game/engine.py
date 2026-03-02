from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.graphics import Rectangle, Color, PushMatrix, PopMatrix, Translate, Scale
from kivy.clock import Clock
import kivy.app
from game.player_widget import PlayerWidget 
from ui.hud import HUD, CountdownOverlay
from ui.level_up import LevelUpPopup, PausePopup

class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.keys_pressed = set()
        self.player_pos = [2500, 2500]
        self.is_paused = False
        self.facing_right = True
        self.is_left_clicked = False
        
        # ตั้งค่าระบบ Dash
        self.is_dashing = False
        self.dash_cooldown = False
        self.last_dir_x = 0
        self.last_dir_y = 0
        self.dash_duration = 0.2
        self.dash_cooldown_time = 1.0

        # ตั้งค่าจอยสติ๊ก
        self.joy_x = self.joy_y = self.joy_right_x = self.joy_right_y = 0.0
        self.joy_lt_pressed = False
        self.joy_deadzone = 0.2

        self.root_layout = FloatLayout()
        self.world_layout = FloatLayout(size_hint=(None, None), size=(5000, 5000))
        
        with self.world_layout.canvas.before:
            PushMatrix()
            self.zoom = Scale(2, 2, 2)
            self.camera = Translate(0, 0)
            Color(0.2, 0.2, 0.2, 1)
            for i in range(0, 5001, 100):
                Rectangle(pos=(0, i), size=(5000, 1))
                Rectangle(pos=(i, 0), size=(1, 5000))
        
        with self.world_layout.canvas.after:
            PopMatrix()
        
        # สร้างตัวแปร player_widget ทิ้งไว้ก่อน
        self.player_widget = None
        
        self.root_layout.add_widget(self.world_layout)
        
        self.hud = HUD(game_screen=self)
        self.root_layout.add_widget(self.hud)
        self.add_widget(self.root_layout)

    def on_enter(self):
        # 1. ดึงข้อมูลตัวละครที่เลือกมาจากหน้าจอที่แล้ว
        self.player_stats = kivy.app.App.get_running_app().current_player
        
        if self.player_stats:
            # 2. ถ้ายืนยันว่าเลือกตัวละครแล้ว ให้ "ลบตัวเก่าทิ้ง" (ถ้ามี)
            if self.player_widget:
                self.world_layout.remove_widget(self.player_widget)

            # 3. แล้ว "สร้างตัวใหม่" ขึ้นมาทับเสมอ! (แก้ปัญหาเลือกตัวไหนก็ได้ตัวเดิม)
            self.player_widget = PlayerWidget(
                idle_frames=self.player_stats.idle_frames,
                walk_frames=self.player_stats.walk_frames,
                start_pos=tuple(self.player_pos)
            )
            self.world_layout.add_widget(self.player_widget)

            # เซ็ตอัประบบเริ่มเกม
            self.is_paused = True
            self.hud.update_ui(self.player_stats)
            self.countdown = CountdownOverlay(callback=self.start_actual_game)
            self.root_layout.add_widget(self.countdown)
            
            # เคลียร์ปุ่มเก่าและเริ่มจับการกดปุ่ม
            self.keys_pressed.clear()
            Window.bind(on_key_down=self._on_keydown, on_key_up=self._on_keyup)
            Window.bind(on_joy_axis=self._on_joy_axis, on_joy_button_down=self._on_joy_button_down)
            
            # เริ่ม Game Loop
            Clock.unschedule(self.update_frame) 
            Clock.schedule_interval(self.update_frame, 1.0/60.0)

    def on_leave(self):
        # ฟังก์ชันนี้จะทำงานตอนกด Pause ออกไปเมนูหลัก ป้องกันเกมแครช
        Clock.unschedule(self.update_frame)
        Window.unbind(on_key_down=self._on_keydown, on_key_up=self._on_keyup)
        Window.unbind(on_joy_axis=self._on_joy_axis, on_joy_button_down=self._on_joy_button_down)

    def start_actual_game(self): 
        self.is_paused = False
    
    def pause_game(self, instance):
        self.is_paused = True
        PausePopup(game_screen=self).open()

    def resume_game(self):
        self.is_paused = False
        self.keys_pressed.clear()

    def update_frame(self, dt):
        if not self.player_stats or self.is_paused or not self.player_widget: return
        
        speed = self.player_stats.speed * (3.0 if self.is_dashing else 1.0)
        dir_x, dir_y = 0, 0
        
        if not self.is_dashing:
            if 'w' in self.keys_pressed: dir_y += 1
            if 's' in self.keys_pressed: dir_y -= 1
            if 'a' in self.keys_pressed: dir_x -= 1
            if 'd' in self.keys_pressed: dir_x += 1
            
            if dir_x == 0 and dir_y == 0:
                dir_x, dir_y = self.joy_x, self.joy_y
            
            if dir_x != 0 or dir_y != 0:
                self.last_dir_x = dir_x
                self.last_dir_y = dir_y
        else:
            dir_x = self.last_dir_x
            dir_y = self.last_dir_y

        mag = (dir_x**2 + dir_y**2) ** 0.5
        if mag > 1.0:
            dir_x /= mag; dir_y /= mag

        self.player_pos[0] += dir_x * speed
        self.player_pos[1] += dir_y * speed
        self.player_widget.update_pos(self.player_pos)

        # จัดการหันหน้าตัวละคร
        if not self.is_left_clicked and not self.joy_lt_pressed:
            if dir_x > 0.1: self.facing_right = True
            elif dir_x < -0.1: self.facing_right = False
        elif self.joy_lt_pressed:
            if self.joy_right_x > 0.1: self.facing_right = True
            elif self.joy_right_x < -0.1: self.facing_right = False
        
        self.player_widget.set_state((dir_x != 0 or dir_y != 0), self.facing_right, speed)
        self.player_widget.update_aim(self.joy_lt_pressed, self.joy_right_x, self.joy_right_y)
        
        self.zoom.origin = (Window.width/2, Window.height/2)
        self.camera.x = (Window.width/2) - self.player_pos[0] - 32 
        self.camera.y = (Window.height/2) - self.player_pos[1] - 32

    def start_dash(self):
        if not self.dash_cooldown and not self.is_dashing and self.player_widget:
            if self.last_dir_x != 0 or self.last_dir_y != 0:
                self.is_dashing = True
                self.dash_cooldown = True
                self.player_widget.color_inst.rgba = (1, 1, 0, 1) 
                Clock.schedule_once(self.end_dash, self.dash_duration)
                Clock.schedule_once(self.reset_dash_cooldown, self.dash_cooldown_time)

    def end_dash(self, dt):
        self.is_dashing = False
        if self.player_widget:
            self.player_widget.color_inst.rgba = (1, 1, 1, 1)

    def reset_dash_cooldown(self, dt):
        self.dash_cooldown = False

    def _on_keydown(self, window, key, scancode, codepoint, modifiers):
        if key == 292: # F11
            Window.fullscreen = not Window.fullscreen
            return True
        if key == 32: # Spacebar
            self.start_dash()
            return True
        if codepoint: self.keys_pressed.add(codepoint.lower())
        if key == 27: # Esc
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
        if abs(normalized) < self.joy_deadzone:
            normalized = 0.0
            
        if axisid == 0: self.joy_x = normalized
        elif axisid == 1: self.joy_y = -normalized 
        elif axisid == 2: self.joy_right_x = normalized
        elif axisid == 3: self.joy_right_y = -normalized
        elif axisid == 4: self.joy_lt_pressed = (normalized > 0.0)
            
    def _on_joy_button_down(self, window, stickid, buttonid):
        if buttonid == 0: self.start_dash() # A button
        elif buttonid == 7: self.pause_game(None) # Start button