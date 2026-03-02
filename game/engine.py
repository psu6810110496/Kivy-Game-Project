from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.graphics import Rectangle, Color, PushMatrix, PopMatrix, Translate, Scale
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
import kivy.app
from game.player_widget import PlayerWidget
from ui.hud import HUD, CountdownOverlay
from ui.level_up import LevelUpPopup
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from ui.pause import PausePopup

import math
import random
from game.enemy_widget import EnemyWidget

class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.keys_pressed = set()
        self.player_pos = [2500, 2500]
        self.is_paused = False
        self.facing_right = True
        self.is_left_clicked = False
        
        self.is_dashing = False
        self.dash_cooldown = False
        self.dash_duration = 0.5
        self.last_dir_x = 0
        self.last_dir_y = 0
        self.dash_duration = 0.2
        self.dash_cooldown_time = 1.0

        self.joy_x = self.joy_y = self.joy_right_x = self.joy_right_y = 0.0
        self.joy_lt_pressed = False
        self.joy_deadzone = 0.2

        self.active_pause_popup = None
        self.enemies = []

        # --- [เพิ่มตัวแปรระบบ Wave] ---
        self.current_wave = 0
        self.game_started = False
        # ---------------------------

        self.root_layout = FloatLayout()
        self.world_layout = FloatLayout(size_hint=(None, None), size=(5000, 5000))

        map_texture = CoreImage("assets/maps/map.jpg").texture
        map_texture.wrap = "repeat"

        map_scale = 3.0
        u_scale = 5000 / (map_texture.width * map_scale)
        v_scale = 5000 / (map_texture.height * map_scale)

        map_texture.uvsize = (u_scale, -v_scale)

        with self.world_layout.canvas.before:
            PushMatrix()
            self.zoom = Scale(2, 2, 2)
            self.camera = Translate(0, 0)

            Color(1, 1, 1, 1)
            Rectangle(pos=(0, 0), size=(5000, 5000), texture=map_texture)

            Color(0, 0, 0, 0.85)
            Rectangle(pos=(-3000, -3000), size=(3000, 11000))  
            Rectangle(pos=(5000, -3000), size=(3000, 11000))  
            Rectangle(pos=(0, -3000), size=(5000, 3000))  
            Rectangle(pos=(0, 5000), size=(5000, 3000))  

        with self.world_layout.canvas.after:
            PopMatrix()

        self.player_widget = PlayerWidget()
        self.world_layout.add_widget(self.player_widget)
        self.root_layout.add_widget(self.world_layout)

        self.hud = HUD(game_screen=self)
        self.root_layout.add_widget(self.hud)
        
        # --- [เพิ่มปุ่ม Clear Enemy ไว้ที่มุมขวาบนของจอ (ใช้ทดสอบ)] ---
        self.btn_clear = Button(
            text="Clear Enemy", size_hint=(None, None), size=(150, 50),
            pos_hint={'right': 0.98, 'top': 0.98}, background_color=(1, 0, 0, 1)
        )
        self.btn_clear.bind(on_press=self.debug_clear_enemies)
        self.root_layout.add_widget(self.btn_clear)
        # ------------------------------------------------------

        self.add_widget(self.root_layout)

        Window.bind(on_key_down=self._on_keydown, on_key_up=self._on_keyup)
        Window.bind(
            on_joy_axis=self._on_joy_axis, on_joy_button_down=self._on_joy_button_down
        )

    def on_enter(self):
        self.player_stats = kivy.app.App.get_running_app().current_player
        if self.player_stats:
            self.is_paused = True
            self.hud.update_ui(self.player_stats)
            self.countdown = CountdownOverlay(callback=self.start_actual_game)
            self.root_layout.add_widget(self.countdown)
            Clock.schedule_interval(self.update_frame, 1.0 / 60.0)

    def start_actual_game(self):
        self.is_paused = False
        self.game_started = True
        # --- [เริ่ม Wave แรก] ---
        self.start_next_wave()
        # -----------------------

    # --- [ระบบเริ่ม Wave ใหม่] ---
    def start_next_wave(self):
        self.current_wave += 1
        print(f"Starting Wave {self.current_wave}!") # แสดงในคอนโซล
        
        # เสกศัตรู 10 ตัว
        for _ in range(10):
            self.spawn_single_enemy()

    # --- [ฟังก์ชันเสกศัตรู 1 ตัว] ---
    def spawn_single_enemy(self):
        angle = random.uniform(0, 2 * math.pi)
        # สุ่มระยะห่างให้ต่างกันนิดหน่อย ศัตรูจะได้ไม่เกิดซ้อนเป็นก้อนเดียวกันหมด
        radius = random.uniform(800, 1000) 
        
        spawn_x = self.player_pos[0] + (math.cos(angle) * radius)
        spawn_y = self.player_pos[1] + (math.sin(angle) * radius)
        
        new_enemy = EnemyWidget(spawn_pos=(spawn_x, spawn_y))
        self.enemies.append(new_enemy)
        self.world_layout.add_widget(new_enemy)

    # --- [ฟังก์ชันสำหรับปุ่มลบศัตรูทั้งหมด] ---
    def debug_clear_enemies(self, instance):
        if not self.game_started or self.is_paused:
            return
        
        for enemy in self.enemies:
            self.world_layout.remove_widget(enemy)
        self.enemies.clear()
        print("All enemies cleared!")

    def toggle_pause(self):
        if self.is_paused:
            self.resume_game()
        else:
            self.pause_game()

    def pause_game(self, instance=None):
        if not self.is_paused and not self.active_pause_popup:
            self.is_paused = True
            self.active_pause_popup = PausePopup(game_screen=self)
            self.active_pause_popup.open()

    def resume_game(self):
        self.is_paused = False
        self.keys_pressed.clear()
        if self.active_pause_popup:
            self.active_pause_popup.dismiss()
            self.active_pause_popup = None

    def update_frame(self, dt):
        if not self.player_stats or self.is_paused:
            return

        # --- [ระบบตรวจสอบ Wave ถัดไป] ---
        # ถ้าเกมเริ่มแล้ว และศัตรูในฉากตายหมด (เป็น 0) ให้เริ่ม Wave ใหม่ทันที
        if self.game_started and len(self.enemies) == 0:
            self.start_next_wave()
        # ------------------------------

        speed = self.player_stats.speed * (3.0 if self.is_dashing else 1.0)
        dir_x, dir_y = 0, 0

        if not self.is_dashing:
            if "w" in self.keys_pressed: dir_y += 1
            if "s" in self.keys_pressed: dir_y -= 1
            if "a" in self.keys_pressed: dir_x -= 1
            if "d" in self.keys_pressed: dir_x += 1

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
            dir_x /= mag
            dir_y /= mag

        new_x = self.player_pos[0] + (dir_x * speed)
        new_y = self.player_pos[1] + (dir_y * speed)

        hitbox_radius = 20
        self.player_pos[0] = max(hitbox_radius, min(new_x, 5000 - hitbox_radius))
        self.player_pos[1] = max(hitbox_radius, min(new_y, 5000 - hitbox_radius))
        
        self.player_widget.update_pos(self.player_pos)

        # ส่งลิสต์ศัตรูเข้าไปเพื่อคำนวณการชน/ผลักกันเอง
        for enemy in self.enemies:
            enemy.update_movement(self.player_pos, self.enemies)

        if not self.is_left_clicked and not self.joy_lt_pressed:
            if dir_x > 0.1: self.facing_right = True
            elif dir_x < -0.1: self.facing_right = False
        elif self.joy_lt_pressed:
            if self.joy_right_x > 0.1: self.facing_right = True
            elif self.joy_right_x < -0.1: self.facing_right = False

        self.player_widget.set_state(
            (dir_x != 0 or dir_y != 0), self.facing_right, speed
        )
        self.player_widget.update_aim(
            self.joy_lt_pressed, self.joy_right_x, self.joy_right_y
        )

        self.zoom.origin = (Window.width / 2, Window.height / 2)
        self.camera.x = (Window.width / 2) - self.player_pos[0] - 25
        self.camera.y = (Window.height / 2) - self.player_pos[1] - 25

    def start_dash(self):
        if not self.dash_cooldown and not self.is_dashing:
            if self.last_dir_x != 0 or self.last_dir_y != 0:
                self.is_dashing = True
                self.dash_cooldown = True
                self.player_widget.color_inst.rgba = (1, 1, 0, 1)
                Clock.schedule_once(self.end_dash, self.dash_duration)
                Clock.schedule_once(self.reset_dash_cooldown, self.dash_cooldown_time)

    def end_dash(self, dt):
        self.is_dashing = False
        self.player_widget.color_inst.rgba = (1, 1, 1, 1)

    def reset_dash_cooldown(self, dt):
        self.dash_cooldown = False

    def _on_keydown(self, window, key, scancode, codepoint, modifiers):
        if key == 292:  
            Window.fullscreen = not Window.fullscreen
            return True
        if key == 32:  
            self.start_dash()
            return True
        if codepoint:
            self.keys_pressed.add(codepoint.lower())
        if key == 27:  
            self.toggle_pause()
            return True

    def _on_keyup(self, window, key, scancode):
        try:
            key_char = chr(key).lower()
            if key_char in self.keys_pressed:
                self.keys_pressed.remove(key_char)
        except:
            pass

    def _on_joy_axis(self, window, stickid, axisid, value):
        normalized = value / 32767.0
        if abs(normalized) < self.joy_deadzone:
            normalized = 0.0
            
        if axisid == 0: self.joy_x = normalized
        elif axisid == 1: self.joy_y = -normalized 
        elif axisid == 2: self.joy_right_x = normalized
        elif axisid == 3: self.joy_right_y = -normalized
        elif axisid == 4: self.joy_lt_pressed = (normalized > 0.0)
        elif axisid == 5:
            if normalized > 0.5:
                self.start_dash()
            
    def _on_joy_button_down(self, window, stickid, buttonid):
        if buttonid == 7: 
            self.toggle_pause()