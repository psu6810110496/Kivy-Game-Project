from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window

from kivy.graphics import (
    Rectangle,
    Color,
    PushMatrix,
    PopMatrix,
    Translate,
    Scale,
    InstructionGroup,
    Ellipse,
)
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
import kivy.app
import math
import random

from game.player_widget import PlayerWidget
from ui.hud import HUD, CountdownOverlay
from ui.level_up import LevelUpPopup
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from ui.pause import PausePopup
from game.enemy_widget import EnemyWidget

class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.keys_pressed = set()
        self.player_pos = [2500, 2500]
        self.is_paused = False
        self.facing_right = True
        self.is_left_clicked = False

        # --- [ระบบ Dash] ---
        self.is_dashing = False
        self.dash_cooldown = False
        self.dash_duration = 0.2
        self.dash_cooldown_time = 1.0
        self.last_dir_x = 0
        self.last_dir_y = 0

        # --- [ระบบ Input & Mouse] ---
        self.joy_x = self.joy_y = self.joy_right_x = self.joy_right_y = 0.0
        self.joy_lt_pressed = False
        self.joy_deadzone = 0.2
        self.mouse_world_pos = [0, 0]
        self.mouse_dir = [1, 0]

        self.active_pause_popup = None
        self.enemies = []
        self.current_wave = 0
        self.game_started = False
        self.is_invincible = False
        self.countdown = None
        self.attack_event = None

        self.root_layout = FloatLayout()
        self.world_layout = FloatLayout(size_hint=(None, None), size=(5000, 5000))

        # --- [Map Setup] ---
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
            
            # ขอบเขตแผนที่ (Void)
            Color(0, 0, 0, 0.85)
            Rectangle(pos=(-3000, -3000), size=(3000, 11000))
            Rectangle(pos=(5000, -3000), size=(3000, 11000))
            Rectangle(pos=(0, -3000), size=(5000, 3000))
            Rectangle(pos=(0, 5000), size=(5000, 3000))

        with self.world_layout.canvas.after:
            PopMatrix()

        self.player_widget = None
        self.player_stats = None

        self.root_layout.add_widget(self.world_layout)
        self.hud = HUD(game_screen=self)
        self.root_layout.add_widget(self.hud)

        # Debug Button
        self.btn_clear = Button(
            text="Clear Enemy",
            size_hint=(None, None),
            size=(150, 50),
            pos_hint={"right": 0.98, "top": 0.98},
            background_color=(1, 0, 0, 1),
        )
        self.btn_clear.bind(on_press=self.debug_clear_enemies)
        self.root_layout.add_widget(self.btn_clear)

        self.add_widget(self.root_layout)

    def _reset_state(self):
        self.player_pos = [2500, 2500]
        self.is_paused = False
        self.facing_right = True
        self.is_left_clicked = False
        self.is_dashing = False
        self.dash_cooldown = False
        self.last_dir_x = 0
        self.last_dir_y = 0
        self.joy_x = self.joy_y = self.joy_right_x = self.joy_right_y = 0.0
        self.joy_lt_pressed = False
        self.is_invincible = False
        self.game_started = False
        self.current_wave = 0
        if self.attack_event:
            self.attack_event.cancel()
            self.attack_event = None
        self.keys_pressed.clear()

    def on_enter(self):
        self.player_stats = kivy.app.App.get_running_app().current_player
        if self.player_stats:
            self.player_stats.reset()
            self._reset_state()

            if self.player_widget and self.player_widget.parent:
                self.world_layout.remove_widget(self.player_widget)

            self.player_widget = PlayerWidget(
                idle_frames=self.player_stats.idle_frames,
                walk_frames=self.player_stats.walk_frames,
                start_pos=tuple(self.player_pos),
            )
            self.world_layout.add_widget(self.player_widget)
            self.hud.update_ui(self.player_stats)

            self.is_paused = True
            self.countdown = CountdownOverlay(callback=self.start_actual_game)
            self.root_layout.add_widget(self.countdown)

            # Bind Controls
            Window.bind(on_key_down=self._on_keydown, on_key_up=self._on_keyup)
            Window.bind(on_joy_axis=self._on_joy_axis, on_joy_button_down=self._on_joy_button_down)
            Window.bind(mouse_pos=self._on_mouse_pos)

            Clock.unschedule(self.update_frame)
            Clock.schedule_interval(self.update_frame, 1.0 / 60.0)

    def _on_mouse_pos(self, window, pos):
        if self.is_paused or not self.player_widget:
            return
        
        # 1. ปรับการคำนวณ World Pos ให้แม่นยำตามค่า Zoom และ Camera
        # พิกัดเมาส์ (pos) อยู่ใน Screen Space ต้องแปลงเป็น World Space
        zoom_val = self.zoom.x
        world_x = (pos[0] - Window.width / 2) / zoom_val + self.player_pos[0] + 32
        world_y = (pos[1] - Window.height / 2) / zoom_val + self.player_pos[1] + 32
        self.mouse_world_pos = [world_x, world_y]

        # 2. คำนวณ Vector ทิศทาง
        dx = world_x - (self.player_pos[0] + 32)
        dy = world_y - (self.player_pos[1] + 32)
        mag = math.hypot(dx, dy)
        if mag > 0:
            self.mouse_dir = [dx / mag, dy / mag]

    def start_actual_game(self):
        self.is_paused = False
        self.game_started = True
        self.start_next_wave()
        if self.attack_event:
            self.attack_event.cancel()
        self.attack_event = Clock.schedule_interval(self.perform_attack, 1.0)

    def perform_attack(self, dt):
        if self.is_paused or not self.game_started or not self.player_stats:
            return

        # จุดศูนย์กลางผู้เล่น (Anchor point สำหรับการตี)
        px, py = self.player_pos[0] + 32, self.player_pos[1] + 32
        
        # เลือกทิศทางเล็ง (จอยขวา > เมาส์)
        aim_x, aim_y = self.joy_right_x, self.joy_right_y
        if aim_x == 0 and aim_y == 0:
            aim_x, aim_y = self.mouse_dir[0], self.mouse_dir[1]

        attack_range = 140
        hit_angle_spread = 60
        
        # มุมในทางคณิตศาสตร์ (องศา)
        angle_rad = math.atan2(aim_y, aim_x)
        angle_deg = math.degrees(angle_rad)

        # วาด Effect การโจมตี
        self.show_slash_effect(px, py, attack_range, angle_deg, hit_angle_spread)

        # ตรวจสอบศัตรู
        enemies_to_remove = []
        for enemy in self.enemies:
            ex, ey = enemy.pos[0] + 20, enemy.pos[1] + 20
            dx, dy = ex - px, ey - py
            dist = math.hypot(dx, dy)

            if dist < attack_range + 30:
                enemy_angle = math.degrees(math.atan2(dy, dx))
                angle_diff = (enemy_angle - angle_deg) % 360
                if angle_diff > 180: angle_diff -= 360

                if abs(angle_diff) <= hit_angle_spread:
                    enemy.hp -= self.player_stats.damage
                    # ผลักศัตรูออกตามทิศที่เล็ง
                    enemy.pos = (enemy.pos[0] + aim_x * 40, enemy.pos[1] + aim_y * 40)
                    if enemy.hp <= 0: enemies_to_remove.append(enemy)

        for enemy in enemies_to_remove:
            if enemy in self.enemies:
                self.enemies.remove(enemy)
                self.world_layout.remove_widget(enemy)
                self.gain_exp(10)

    def show_slash_effect(self, px, py, radius, angle_deg, spread):
        # แก้ไขจุดที่ทิศทางไม่ตรง: Kivy Ellipse นับองศาเริ่มจาก 0 ที่แกน Y (บน) 
        # และหมุนตามเข็มนาฬิกา เราต้องแปลงจาก Math Angle เป็น Kivy Angle
        # สูตรแปลง: kivy_angle = 90 - math_angle
        kivy_center_angle = 90 - angle_deg
        
        start_angle = kivy_center_angle - spread
        end_angle = kivy_center_angle + spread

        ig = InstructionGroup()
        ig.add(Color(1, 1, 0, 0.5)) # สีเหลืองโปร่งแสง
        
        # วาดพัด
        slash = Ellipse(
            pos=(px - radius, py - radius),
            size=(radius * 2, radius * 2),
            angle_start=start_angle,
            angle_end=end_angle,
        )
        ig.add(slash)
        
        self.world_layout.canvas.add(ig)
        
        # ฟังก์ชันลบ InstructionGroup อย่างปลอดภัยเพื่อแก้บั๊กจุดแดงค้าง
        def safe_remove(dt):
            if ig in self.world_layout.canvas.children:
                self.world_layout.canvas.remove(ig)
        
        Clock.schedule_once(safe_remove, 0.12)

    def update_frame(self, dt):
        if not self.player_stats or self.is_paused or not self.player_widget:
            return

        # --- [Movement] ---
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
                self.last_dir_x, self.last_dir_y = dir_x, dir_y
        else:
            dir_x, dir_y = self.last_dir_x, self.last_dir_y

        mag = math.hypot(dir_x, dir_y)
        if mag > 1.0:
            dir_x /= mag; dir_y /= mag

        self.player_pos[0] = max(20, min(self.player_pos[0] + dir_x * speed, 4980))
        self.player_pos[1] = max(20, min(self.player_pos[1] + dir_y * speed, 4980))
        self.player_widget.update_pos(self.player_pos)

        # --- [Facing & Aiming] ---
        # ตัวละครหันตามทิศเมาส์เสมอ ถ้าไม่ได้ใช้จอยเล็ง
        if abs(self.joy_right_x) > 0.1:
            self.facing_right = self.joy_right_x > 0
        else:
            self.facing_right = self.mouse_dir[0] > 0

        self.player_widget.set_state((dir_x != 0 or dir_y != 0), self.facing_right, speed)
        
        aim_x = self.joy_right_x if abs(self.joy_right_x) > 0.1 else self.mouse_dir[0]
        aim_y = self.joy_right_y if abs(self.joy_right_y) > 0.1 else self.mouse_dir[1]
        self.player_widget.update_aim(True, aim_x, aim_y)

        # Enemies & Camera
        for enemy in self.enemies:
            enemy.update_movement(self.player_pos, self.enemies)
        
        self.zoom.origin = (Window.width / 2, Window.height / 2)
        self.camera.x = (Window.width / 2) - self.player_pos[0] - 32
        self.camera.y = (Window.height / 2) - self.player_pos[1] - 32

    # ... (ส่วน setup_next_wave, gain_exp, toggle_pause, damage เหมือนเดิมของคุณ) ...

    def gain_exp(self, amount):
        if not self.player_stats: return
        self.player_stats.exp += amount
        if self.player_stats.exp >= self.player_stats.max_exp:
            self.player_stats.exp -= self.player_stats.max_exp
            self.player_stats.level += 1
            self.is_paused = True
            LevelUpPopup(self).open()
        self.hud.update_ui(self.player_stats)

    def start_next_wave(self):
        self.current_wave += 1
        for _ in range(5 + self.current_wave * 2):
            self.spawn_single_enemy()

    def spawn_single_enemy(self):
        angle = random.uniform(0, 2 * math.pi)
        radius = random.uniform(800, 1000)
        spawn_x = self.player_pos[0] + (math.cos(angle) * radius)
        spawn_y = self.player_pos[1] + (math.sin(angle) * radius)
        new_enemy = EnemyWidget(spawn_pos=(spawn_x, spawn_y))
        self.enemies.append(new_enemy)
        self.world_layout.add_widget(new_enemy)

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

    def on_leave(self):
        Clock.unschedule(self.update_frame)
        if self.attack_event: self.attack_event.cancel()
        Window.unbind(on_key_down=self._on_keydown, on_key_up=self._on_keyup)
        Window.unbind(on_joy_axis=self._on_joy_axis, on_joy_button_down=self._on_joy_button_down)
        Window.unbind(mouse_pos=self._on_mouse_pos)

    # --- [Inputs] ---
    def _on_keydown(self, window, key, scancode, codepoint, modifiers):
        if key == 27: self.toggle_pause()
        if key == 32: self.start_dash()
        if codepoint: self.keys_pressed.add(codepoint.lower())
        return True

    def _on_keyup(self, window, key, scancode):
        try:
            char = chr(key).lower()
            if char in self.keys_pressed: self.keys_pressed.remove(char)
        except: pass

    def toggle_pause(self):
        if self.is_paused: self.resume_game()
        else: self.pause_game()

    def start_dash(self):
        if not self.dash_cooldown and not self.is_dashing and (self.last_dir_x or self.last_dir_y):
            self.is_dashing = True
            self.dash_cooldown = True
            self.player_widget.color_inst.rgba = (1, 1, 0, 1)
            Clock.schedule_once(lambda dt: setattr(self, 'is_dashing', False), self.dash_duration)
            Clock.schedule_once(lambda dt: setattr(self, 'dash_cooldown', False), self.dash_cooldown_time)

    def _on_joy_axis(self, window, stickid, axisid, value):
        val = value / 32767.0
        if abs(val) < self.joy_deadzone: val = 0.0
        if axisid == 0: self.joy_x = val
        elif axisid == 1: self.joy_y = -val
        elif axisid == 2: self.joy_right_x = val
        elif axisid == 3: self.joy_right_y = -val
        elif axisid == 5 and val > 0.5: self.start_dash()

    def _on_joy_button_down(self, window, stickid, buttonid):
        if buttonid == 7: self.toggle_pause()

    def debug_clear_enemies(self, instance):
        for e in self.enemies: self.world_layout.remove_widget(e)
        self.enemies.clear()

    def take_damage(self, amount):
        if self.is_invincible or not self.player_stats: return
        self.player_stats.current_hp -= amount
        if self.player_stats.current_hp <= 0:
            self.show_game_over()
        else:
            self.is_invincible = True
            self.player_widget.color_inst.rgba = (1, 0, 0, 1)
            Clock.schedule_once(lambda dt: setattr(self, 'is_invincible', False), 1.0)