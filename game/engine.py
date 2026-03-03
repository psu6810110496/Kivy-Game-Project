from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.uix.label import Label
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

# Import ส่วนประกอบอื่นๆ
from game.player_widget import PlayerWidget
from ui.hud import HUD, CountdownOverlay
from ui.level_up import LevelUpPopup
from ui.pause import PausePopup
from game.enemy_widget import EnemyWidget
from ui.game_over import GameOverPopup
from game.projectile_widget import EnemyProjectile


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
        self.boss = None
        self.is_boss_intro = False
        self.boss_overlay = None
        self.game_started = False
        self.is_invincible = False
        self.countdown = None
        self.attack_event = None
        self.is_dead = False # ป้องกัน Game Over ซ้อน
        self.enemy_projectiles = []

        # --- [ระบบ Layout & Aspect Ratio] ---
        self.root_layout = FloatLayout(size_hint=(None, None))
        self.world_layout = FloatLayout(size_hint=(None, None), size=(5000, 5000))
        self.bind(size=self._update_layout_size)

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

        self.add_widget(self.root_layout)

    def _update_layout_size(self, instance, value):
        target_ratio = 16 / 9
        win_w, win_h = value
        if win_h == 0: return
        
        win_ratio = win_w / win_h

        if win_ratio > target_ratio:
            new_w = win_h * target_ratio
            new_h = win_h
        else:
            new_w = win_w
            new_h = win_w / target_ratio

        self.root_layout.size = (new_w, new_h)
        self.root_layout.pos = ((win_w - new_w) / 2, (win_h - new_h) / 2)

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
        self.is_invincible = False
        self.game_started = False
        self.current_wave = 0
        self.is_dead = False
        
        if self.attack_event:
            self.attack_event.cancel()
            self.attack_event = None
            
        self.keys_pressed.clear()

        if hasattr(self, 'enemies'):
            for enemy in self.enemies:
                if enemy.parent:
                    self.world_layout.remove_widget(enemy)
            self.enemies = []

        self.update_camera(0)

        for p in self.enemy_projectiles:
            if p.parent: self.world_layout.remove_widget(p)
        self.enemy_projectiles = []

    def on_enter(self):
        self._update_layout_size(None, Window.size)
        
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

            Window.bind(on_key_down=self._on_window_key_down, on_key_up=self._on_window_key_up)
            Window.bind(on_joy_axis=self._on_joy_axis, on_joy_button_down=self._on_joy_button_down)
            Window.bind(mouse_pos=self._on_mouse_pos)

            Clock.unschedule(self.update_frame)
            Clock.schedule_interval(self.update_frame, 1.0 / 60.0)

    def on_leave(self):
        Clock.unschedule(self.update_frame)
        if self.attack_event: self.attack_event.cancel()
        Window.unbind(on_key_down=self._on_window_key_down, on_key_up=self._on_window_key_up)
        Window.unbind(on_joy_axis=self._on_joy_axis, on_joy_button_down=self._on_joy_button_down)
        Window.unbind(mouse_pos=self._on_mouse_pos)

    # --- [ส่วนที่อัปเดตใหม่: Smooth Camera & Shake] ---
    def update_camera(self, dt):
        rw, rh = self.root_layout.size
        self.zoom.origin = (rw / 2, rh / 2)
        
        # ถ้าอยู่ในช่วง Intro บอส ให้โฟกัสที่บอสแทนผู้เล่น
        if self.is_boss_intro and self.boss and self.boss.parent:
            bx = self.boss.pos[0] + self.boss.enemy_size[0] / 2
            by = self.boss.pos[1] + self.boss.enemy_size[1] / 2
            target_x = (rw / 2) - bx
            target_y = (rh / 2) - by
        else:
            # เป้าหมายที่กล้องควรอยู่ (กึ่งกลางตัวละคร)
            target_x = (rw / 2) - self.player_pos[0] - 32
            target_y = (rh / 2) - self.player_pos[1] - 32

        # ใส่แรงเขย่าถ้ามีการ Dash
        if self.is_dashing:
            shake_intensity = 8.0
            target_x += (random.random() - 0.5) * shake_intensity
            target_y += (random.random() - 0.5) * shake_intensity

        # ใช้ Lerp เพื่อให้กล้องไหลลื่น (ปรับ 6.0 ให้สูงขึ้นถ้าอยากให้กล้องตามไวขึ้น)
        lerp_speed = 6.0
        self.camera.x += (target_x - self.camera.x) * lerp_speed * dt
        self.camera.y += (target_y - self.camera.y) * lerp_speed * dt

    def update_frame(self, dt):
        if not self.player_stats or self.is_paused or not self.player_widget or self.is_dead:
            return

        # 1. คำนวณความเร็วและการเคลื่อนที่ของผู้เล่น
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

        # 2. การหันหน้าและการเล็ง (Aiming)
        if abs(self.joy_right_x) > 0.1:
            self.facing_right = self.joy_right_x > 0
        else:
            self.facing_right = self.mouse_dir[0] > 0

        self.player_widget.set_state((dir_x != 0 or dir_y != 0), self.facing_right, speed)
        
        aim_x = self.joy_right_x if abs(self.joy_right_x) > 0.1 else self.mouse_dir[0]
        aim_y = self.joy_right_y if abs(self.joy_right_y) > 0.1 else self.mouse_dir[1]
        self.player_widget.update_aim(True, aim_x, aim_y)

        # 3. อัปเดตศัตรู และเช็คการชนตัวศัตรู (Melee Damage)
        for enemy in self.enemies:
            enemy.update_movement(self.player_pos, self.enemies)
            dist = math.hypot(
                (enemy.pos[0] + enemy.enemy_size[0]/2) - (self.player_pos[0] + 32),
                (enemy.pos[1] + enemy.enemy_size[1]/2) - (self.player_pos[1] + 32)
            )
            if dist < 45 and not self.is_invincible:
                self.take_damage(enemy.damage)

        # 4. [ส่วนที่เพิ่มใหม่] อัปเดตกระสุน และเช็ค Collision ของกระสุน (Ranger Projectiles)
        p_center_x = self.player_pos[0] + 32
        p_center_y = self.player_pos[1] + 32

        for proj in list(self.enemy_projectiles):
            proj.update(dt)

            # คำนวณจุดกึ่งกลางของกระสุน
            proj_center_x = proj.pos[0] + proj.size[0] / 2.0
            proj_center_y = proj.pos[1] + proj.size[1] / 2.0

            # คำนวณระยะห่างระหว่างกระสุนกับจุดกึ่งกลางผู้เล่น
            dist_to_player = math.hypot(proj_center_x - p_center_x, proj_center_y - p_center_y)
            
            # ถ้าชนผู้เล่น (ลดฮิตบ็อกซ์ลงให้หลบได้ง่ายขึ้น)
            if dist_to_player < 25: 
                if not self.is_invincible:
                    self.take_damage(proj.damage)
                
                # ลบกระสุนออกเมื่อชน
                if proj in self.enemy_projectiles:
                    self.enemy_projectiles.remove(proj)
                    self.world_layout.remove_widget(proj)
            
            # ถ้ากระสุนลอยไปไกลเกิน (เช่น 1200 px) ให้ลบทิ้งเพื่อประหยัด RAM
            elif math.hypot(proj_center_x - p_center_x, proj_center_y - p_center_y) > 1200:
                if proj in self.enemy_projectiles:
                    self.enemy_projectiles.remove(proj)
                    self.world_layout.remove_widget(proj)
            
        # 5. อัปเดตกล้อง
        self.update_camera(dt)

        # 6. ถ้าเคลียร์ศัตรูหมดแล้วให้เริ่ม wave ถัดไป
        if self.game_started and not self.is_paused and not self.is_dead and len(self.enemies) == 0:
            self.start_next_wave()

    def take_damage(self, amount):
        if self.is_dead or self.is_invincible or not self.player_stats: 
            return
            
        self.player_stats.current_hp -= amount
        self.hud.update_ui(self.player_stats)
        
        if self.player_stats.current_hp <= 0:
            self.is_dead = True
            self.show_game_over()
        else:
            self.is_invincible = True
            self.player_widget.color_inst.rgba = (1, 0, 0, 1)
            Clock.schedule_once(self.reset_invincibility, 1.0)

    def reset_invincibility(self, dt):
        self.is_invincible = False
        if not self.is_dashing and self.player_widget:
            self.player_widget.color_inst.rgba = (1, 1, 1, 1)

    def show_game_over(self):
        Clock.unschedule(self.update_frame)
        if self.attack_event:
            self.attack_event.cancel()
            self.attack_event = None
        
        Window.unbind(on_key_down=self._on_window_key_down, on_key_up=self._on_window_key_up)
        Window.unbind(on_joy_axis=self._on_joy_axis, on_joy_button_down=self._on_joy_button_down)
        Window.unbind(mouse_pos=self._on_mouse_pos)
        
        GameOverPopup().open()

    def start_dash(self):
        if not self.dash_cooldown and not self.is_dashing and (self.last_dir_x or self.last_dir_y):
            self.is_dashing = True
            self.dash_cooldown = True
            self.player_widget.color_inst.rgba = (1, 1, 0, 1)
            
            def end_dash(dt):
                self.is_dashing = False
                if not self.is_invincible and self.player_widget:
                    self.player_widget.color_inst.rgba = (1, 1, 1, 1)
            
            Clock.schedule_once(end_dash, self.dash_duration)
            Clock.schedule_once(lambda dt: setattr(self, 'dash_cooldown', False), self.dash_cooldown_time)

    def _on_window_key_down(self, window, key, scancode, codepoint, modifiers):
        if key == 27: # Esc
            self.toggle_pause()
            return True
        if key == 32: # Space
            self.start_dash()
            return True
        if codepoint: 
            self.keys_pressed.add(codepoint.lower())
        return False

    def _on_window_key_up(self, window, key, scancode):
        try:
            char = chr(key).lower()
            if char in self.keys_pressed: self.keys_pressed.remove(char)
        except: self.keys_pressed.clear()

    def _on_mouse_pos(self, window, pos):
        if self.is_paused or not self.player_widget: return
        rel_x = pos[0] - self.root_layout.x
        rel_y = pos[1] - self.root_layout.y
        zoom_val = self.zoom.x
        rw, rh = self.root_layout.size
        world_x = (rel_x - rw / 2) / zoom_val + self.player_pos[0] + 32
        world_y = (rel_y - rh / 2) / zoom_val + self.player_pos[1] + 32
        dx, dy = world_x - (self.player_pos[0] + 32), world_y - (self.player_pos[1] + 32)
        mag = math.hypot(dx, dy)
        if mag > 0: self.mouse_dir = [dx / mag, dy / mag]

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

    def toggle_pause(self):
        if self.is_paused: self.resume_game()
        else: self.pause_game()

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

    def start_actual_game(self):
        self.is_paused = False
        self.game_started = True
        self.start_next_wave()
        if self.attack_event: self.attack_event.cancel()
        self.attack_event = Clock.schedule_interval(self.perform_attack, 1.0)

    def start_next_wave(self):
        self.current_wave += 1
        # จำนวนศัตรูต่อ wave จะเพิ่มขึ้นเรื่อย ๆ
        total_count = 5 + self.current_wave * 2

        # ให้เกิดครบทุกประเภทอย่างน้อย 1 ตัว
        enemy_types = ["normal", "stalker", "ranger"]
        for etype in enemy_types:
            self.spawn_single_enemy(force_type=etype)

        # ที่เหลือสุ่มประเภท
        remaining = max(0, total_count - len(enemy_types))
        for _ in range(remaining):
            self.spawn_single_enemy()

        # ตัวอย่าง: เรียกบอสอัตโนมัติเมื่อถึง Wave 5
        if self.current_wave == 5:
            self.start_boss_fight()

    def spawn_single_enemy(self, force_type=None):
        # ถ้าไม่ได้บังคับประเภท ให้สุ่มตามน้ำหนักปกติ
        etype = force_type or random.choices(
            ["normal", "stalker", "ranger"], weights=[60, 25, 15]
        )[0]
        angle = random.uniform(0, 2 * math.pi)
        radius = random.uniform(850, 1100)
        spawn_x = self.player_pos[0] + (math.cos(angle) * radius)
        spawn_y = self.player_pos[1] + (math.sin(angle) * radius)
        new_enemy = EnemyWidget(spawn_pos=(spawn_x, spawn_y), enemy_type=etype)

        # สเกลความเก่งของมอนสเตอร์ตาม wave
        if self.current_wave > 1:
            diff_mul = 1.0 + (self.current_wave - 1) * 0.2  # HP / DMG เพิ่ม 20% ต่อ wave
            speed_mul = 1.0 + (self.current_wave - 1) * 0.05  # ความเร็วเพิ่ม 5% ต่อ wave

            new_enemy.hp = int(new_enemy.hp * diff_mul)
            new_enemy.max_hp = new_enemy.hp
            new_enemy.damage = int(new_enemy.damage * diff_mul)
            new_enemy.speed *= speed_mul

        self.enemies.append(new_enemy)
        self.world_layout.add_widget(new_enemy)
        
    # --- ระบบ Boss Fight ---
    def start_boss_fight(self, *args):
        if self.boss is not None:
            return

        # สุ่มตำแหน่งบอสให้อยู่ห่างจากผู้เล่นประมาณ 900 พิกเซล
        angle = random.uniform(0, 2 * math.pi)
        radius = 900
        bx = self.player_pos[0] + math.cos(angle) * radius
        by = self.player_pos[1] + math.sin(angle) * radius

        self.boss = EnemyWidget(spawn_pos=(bx, by), enemy_type="boss")
        self.enemies.append(self.boss)
        self.world_layout.add_widget(self.boss)

        # เริ่มช่วง Intro: ล็อกกล้องไปที่บอส + แสดงข้อความ
        self.is_boss_intro = True
        self.show_boss_overlay()

    def show_boss_overlay(self):
        if self.boss_overlay and self.boss_overlay.parent:
            self.root_layout.remove_widget(self.boss_overlay)

        self.boss_overlay = Label(
            text="[b]BOSS ARISE[/b]",
            markup=True,
            font_size=120,
            color=(0.9, 0.2, 0.2, 1),
            outline_width=3,
            outline_color=(0, 0, 0, 1),
            pos_hint={"center_x": 0.5, "center_y": 0.7},
        )
        self.root_layout.add_widget(self.boss_overlay)

        # แสดงข้อความประมาณ 2 วินาที แล้วกลับกล้องไปที่ผู้เล่น
        Clock.schedule_once(self.end_boss_intro, 2.0)

    def end_boss_intro(self, dt):
        self.is_boss_intro = False
        if self.boss_overlay and self.boss_overlay.parent:
            self.root_layout.remove_widget(self.boss_overlay)
        self.boss_overlay = None
        
    def perform_attack(self, dt):
        if self.is_paused or not self.game_started or not self.player_stats or self.is_dead: return
        px, py = self.player_pos[0] + 32, self.player_pos[1] + 32
        aim_x, aim_y = (self.joy_right_x, self.joy_right_y) if (self.joy_right_x or self.joy_right_y) else (self.mouse_dir[0], self.mouse_dir[1])
        
        attack_range, spread = 140, 60
        angle_deg = math.degrees(math.atan2(aim_y, aim_x))
        self.show_slash_effect(px, py, attack_range, angle_deg, spread)

        for enemy in list(self.enemies):
            ex, ey = enemy.pos[0] + 20, enemy.pos[1] + 20
            dx, dy = ex - px, ey - py
            dist = math.hypot(dx, dy)
            if dist < attack_range + 30:
                enemy_angle = math.degrees(math.atan2(dy, dx))
                diff = (enemy_angle - angle_deg) % 360
                if diff > 180: diff -= 360
                if abs(diff) <= spread:
                    # ให้ศัตรูรับดาเมจ + กระเด็น พร้อมเอฟเฟกต์สีใน take_damage()
                    enemy.take_damage(self.player_stats.damage, knockback_dir=(aim_x, aim_y))
                    if enemy.hp <= 0:
                        self.enemies.remove(enemy)
                        self.world_layout.remove_widget(enemy)
                        # ถ้าศัตรูที่ตายคือบอส ให้ล้าง reference
                        if enemy is self.boss:
                            self.boss = None
                        self.gain_exp(10)

    def gain_exp(self, amount):
        self.player_stats.exp += amount
        if self.player_stats.exp >= self.player_stats.max_exp:
            self.player_stats.exp -= self.player_stats.max_exp
            self.player_stats.level += 1
            self.is_paused = True
            LevelUpPopup(self).open()
        self.hud.update_ui(self.player_stats)

    def show_slash_effect(self, px, py, radius, angle_deg, spread):
        kivy_angle = 90 - angle_deg
        ig = InstructionGroup()
        ig.add(Color(1, 1, 0, 0.4))
        ig.add(Ellipse(pos=(px-radius, py-radius), size=(radius*2, radius*2), 
                       angle_start=kivy_angle-spread, angle_end=kivy_angle+spread))
        self.world_layout.canvas.add(ig)
        Clock.schedule_once(lambda dt: self.world_layout.canvas.remove(ig), 0.1)