from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.graphics import (
    Rectangle, Color, PushMatrix, PopMatrix,
    Translate, Scale, InstructionGroup, Ellipse,
)
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
import kivy.app
import math
import random

from game.player_widget import PlayerWidget
from ui.hud import HUD, CountdownOverlay
from ui.level_up import LevelUpPopup
from ui.pause import PausePopup
from ui.game_over import GameOverPopup
from game.enemy_widget import EnemyWidget
from game.projectile_widget import EnemyProjectile
from game.skills import get_upgrade_choices, _hit_enemy


class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Input
        self.keys_pressed = set()
        self.joy_x = self.joy_y = self.joy_right_x = self.joy_right_y = 0.0
        self.joy_lt_pressed = False
        self.joy_deadzone = 0.2
        self.mouse_world_pos = [0, 0]
        self.mouse_dir = [1, 0]

        # Player
        self.player_pos = [2500, 2500]
        self.player_widget = None
        self.player_stats = None
        self.facing_right = True
        self.is_left_clicked = False
        self.is_invincible = False
        self.is_dead = False

        # Dash
        self.is_dashing = False
        self.dash_cooldown = False
        self.dash_duration = 0.2
        self.dash_cooldown_time = 1.0
        self.last_dir_x = 0
        self.last_dir_y = 0

        # Combat
        self.enemies = []
        self.enemy_projectiles = []
        self.player_bullets = []
        self.attack_event = None

        # Wave / State
        self.current_wave = 0
        self.game_started = False
        self.is_paused = False
        self.active_pause_popup = None
        self.countdown = None

        # Layout
        self.root_layout = FloatLayout(size_hint=(None, None))
        self.world_layout = FloatLayout(size_hint=(None, None), size=(5000, 5000))
        self.bind(size=self._update_layout_size)

        # Map
        try:
            map_texture = CoreImage("assets/maps/map.jpg").texture
            map_texture.wrap = "repeat"
            map_scale = 3.0
            u_scale = 5000 / (map_texture.width * map_scale)
            v_scale = 5000 / (map_texture.height * map_scale)
            map_texture.uvsize = (u_scale, -v_scale)
        except Exception:
            map_texture = None

        with self.world_layout.canvas.before:
            PushMatrix()
            self.zoom = Scale(2, 2, 2)
            self.camera = Translate(0, 0)
            if map_texture:
                Color(1, 1, 1, 1)
                Rectangle(pos=(0, 0), size=(5000, 5000), texture=map_texture)
            else:
                Color(0.15, 0.15, 0.15, 1)
                Rectangle(pos=(0, 0), size=(5000, 5000))
            Color(0, 0, 0, 0.85)
            Rectangle(pos=(-3000, -3000), size=(3000, 11000))
            Rectangle(pos=(5000, -3000),  size=(3000, 11000))
            Rectangle(pos=(0, -3000),     size=(5000, 3000))
            Rectangle(pos=(0, 5000),      size=(5000, 3000))

        with self.world_layout.canvas.after:
            PopMatrix()

        self.root_layout.add_widget(self.world_layout)
        self.hud = HUD(game_screen=self)
        self.root_layout.add_widget(self.hud)
        self.add_widget(self.root_layout)

    # Layout
    def _update_layout_size(self, instance, value):
        target_ratio = 16 / 9
        win_w, win_h = value
        if win_h == 0:
            return
        if win_w / win_h > target_ratio:
            new_w, new_h = win_h * target_ratio, win_h
        else:
            new_w, new_h = win_w, win_w / target_ratio
        self.root_layout.size = (new_w, new_h)
        self.root_layout.pos = ((win_w - new_w) / 2, (win_h - new_h) / 2)

    # Camera
    def update_camera(self, dt=0):
        rw, rh = self.root_layout.size
        self.zoom.origin = (rw / 2, rh / 2)
        self.camera.x = (rw / 2) - self.player_pos[0] - 32
        self.camera.y = (rh / 2) - self.player_pos[1] - 32

    # Reset
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
        self.keys_pressed.clear()
        self.mouse_dir = [1, 0]

        if self.attack_event:
            self.attack_event.cancel()
            self.attack_event = None

        for enemy in self.enemies:
            if enemy.parent:
                self.world_layout.remove_widget(enemy)
        self.enemies = []

        for p in self.enemy_projectiles:
            if p.parent:
                self.world_layout.remove_widget(p)
        self.enemy_projectiles = []

        for b in self.player_bullets:
            if b.parent:
                self.world_layout.remove_widget(b)
        self.player_bullets = []

        self.update_camera()

    # Lifecycle
    def on_enter(self):
        self._update_layout_size(None, Window.size)
        self.player_stats = kivy.app.App.get_running_app().current_player
        if not self.player_stats:
            return

        self.player_stats.reset()
        self._reset_state()

        if self.active_pause_popup:
            self.active_pause_popup.dismiss()
            self.active_pause_popup = None
        if self.countdown and self.countdown.parent:
            self.root_layout.remove_widget(self.countdown)
        self.countdown = None

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

        Window.unbind(on_key_down=self._on_window_key_down, on_key_up=self._on_window_key_up)
        Window.unbind(on_joy_axis=self._on_joy_axis, on_joy_button_down=self._on_joy_button_down)
        Window.unbind(mouse_pos=self._on_mouse_pos)
        Window.bind(on_key_down=self._on_window_key_down, on_key_up=self._on_window_key_up)
        Window.bind(on_joy_axis=self._on_joy_axis, on_joy_button_down=self._on_joy_button_down)
        Window.bind(mouse_pos=self._on_mouse_pos)

        Clock.unschedule(self.update_frame)
        Clock.schedule_interval(self.update_frame, 1.0 / 60.0)

    def on_leave(self):
        Clock.unschedule(self.update_frame)
        if self.attack_event:
            self.attack_event.cancel()
        Window.unbind(on_key_down=self._on_window_key_down, on_key_up=self._on_window_key_up)
        Window.unbind(on_joy_axis=self._on_joy_axis, on_joy_button_down=self._on_joy_button_down)
        Window.unbind(mouse_pos=self._on_mouse_pos)

    # Game Start
    def start_actual_game(self):
        self.is_paused = False
        self.game_started = True
        self.start_next_wave()
        # skills.py จัดการ cooldown + attack + animation เองผ่าน skill.tick()

    # Wave
    def start_next_wave(self):
        self.current_wave += 1
        for _ in range(5 + self.current_wave * 2):
            self.spawn_single_enemy()

    def spawn_single_enemy(self):
        etype = random.choices(["normal", "stalker", "ranger"], weights=[60, 25, 15])[0]
        angle = random.uniform(0, 2 * math.pi)
        radius = random.uniform(850, 1100)
        spawn_x = self.player_pos[0] + math.cos(angle) * radius
        spawn_y = self.player_pos[1] + math.sin(angle) * radius
        enemy = EnemyWidget(spawn_pos=(spawn_x, spawn_y), enemy_type=etype)
        self.enemies.append(enemy)
        self.world_layout.add_widget(enemy)

    # Main Loop
    def update_frame(self, dt):
        if not self.player_stats or self.is_paused or not self.player_widget or self.is_dead:
            return

        # Wave ใหม่ถ้าศัตรูหมด
        if self.game_started and not self.enemies:
            self.start_next_wave()

        # Tick สกิลทุกตัว — skills.py จัดการ cooldown/activate/animation เอง
        if self.game_started and hasattr(self.player_stats, 'skills'):
            for skill in self.player_stats.skills:
                skill.tick(dt, self)

        # อัปเดต player bullets
        for b in list(self.player_bullets):
            b.update()
            hit = False
            for enemy in list(self.enemies):
                if math.hypot(b.pos[0] - (enemy.pos[0] + 20),
                              b.pos[1] - (enemy.pos[1] + 20)) < 40:
                    _hit_enemy(self, enemy, b.damage)
                    self._remove_player_bullet(b)
                    hit = True
                    break
            if not hit and b in self.player_bullets:
                if math.hypot(b.pos[0] - (self.player_pos[0] + 32),
                              b.pos[1] - (self.player_pos[1] + 32)) > 700:
                    self._remove_player_bullet(b)

        # อัปเดตกระสุนศัตรู
        for proj in list(self.enemy_projectiles):
            proj.update()
            d = math.hypot(proj.pos[0] - (self.player_pos[0] + 32),
                           proj.pos[1] - (self.player_pos[1] + 32))
            if d < 35:
                self.take_damage(proj.damage)
                self._remove_enemy_projectile(proj)
            elif math.hypot(proj.pos[0] - self.player_pos[0],
                            proj.pos[1] - self.player_pos[1]) > 1200:
                self._remove_enemy_projectile(proj)

        # การเคลื่อนที่ผู้เล่น
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
            dir_x /= mag
            dir_y /= mag

        self.player_pos[0] = max(20, min(self.player_pos[0] + dir_x * speed, 4980))
        self.player_pos[1] = max(20, min(self.player_pos[1] + dir_y * speed, 4980))
        self.player_widget.update_pos(self.player_pos)

        # หันหน้า
        if abs(self.joy_right_x) > 0.1:
            self.facing_right = self.joy_right_x > 0
        else:
            self.facing_right = self.mouse_dir[0] >= 0

        self.player_widget.set_state((dir_x != 0 or dir_y != 0), self.facing_right, speed)
        aim_x = self.joy_right_x if abs(self.joy_right_x) > 0.1 else self.mouse_dir[0]
        aim_y = self.joy_right_y if abs(self.joy_right_y) > 0.1 else self.mouse_dir[1]
        self.player_widget.update_aim(True, aim_x, aim_y)

        # อัปเดตศัตรู
        for enemy in list(self.enemies):
            enemy.update_movement(self.player_pos, self.enemies)

            if hasattr(enemy, "enemy_type") and enemy.enemy_type == "ranger":
                enemy.shoot_cooldown += dt
                if enemy.shoot_cooldown >= 2.5:
                    p = EnemyProjectile(
                        start_pos=(enemy.pos[0] + 20, enemy.pos[1] + 20),
                        target_pos=(self.player_pos[0] + 32, self.player_pos[1] + 32),
                        damage=enemy.damage,
                    )
                    self.enemy_projectiles.append(p)
                    self.world_layout.add_widget(p)
                    enemy.shoot_cooldown = 0

            dist = math.hypot(
                (enemy.pos[0] + 20) - (self.player_pos[0] + 32),
                (enemy.pos[1] + 20) - (self.player_pos[1] + 32),
            )
            if dist < 45 and not self.is_invincible:
                self.take_damage(enemy.damage)

        self.update_camera(dt)

    # Combat Helpers
    def _remove_player_bullet(self, b):
        if b in self.player_bullets:
            self.player_bullets.remove(b)
        if b.parent:
            self.world_layout.remove_widget(b)

    def _remove_enemy_projectile(self, proj):
        if proj in self.enemy_projectiles:
            self.enemy_projectiles.remove(proj)
        if proj.parent:
            self.world_layout.remove_widget(proj)

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

    # EXP / Level Up
    def gain_exp(self, amount):
        if not self.player_stats:
            return
        self.player_stats.exp += amount
        if self.player_stats.exp >= self.player_stats.max_exp:
            self.player_stats.exp -= self.player_stats.max_exp
            self.player_stats.level += 1
            self.is_paused = True
            choices = get_upgrade_choices(self.player_stats)
            if choices:
                LevelUpPopup(self, choices).open()
            else:
                LevelUpPopup(self).open()
        self.hud.update_ui(self.player_stats)

    # Dash
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
            Clock.schedule_once(
                lambda dt: setattr(self, "dash_cooldown", False),
                self.dash_cooldown_time,
            )

    # Pause
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

    # Input
    def _on_window_key_down(self, window, key, scancode, codepoint, modifiers):
        if key == 27:
            self.toggle_pause()
            return True
        if key == 32:
            self.start_dash()
            return True
        if codepoint:
            self.keys_pressed.add(codepoint.lower())
        return False

    def _on_window_key_up(self, window, key, scancode):
        try:
            self.keys_pressed.discard(chr(key).lower())
        except Exception:
            self.keys_pressed.clear()

    def _on_mouse_pos(self, window, pos):
        if self.is_paused or not self.player_widget:
            return
        rel_x = pos[0] - self.root_layout.x
        rel_y = pos[1] - self.root_layout.y
        zoom_val = self.zoom.x
        rw, rh = self.root_layout.size
        world_x = (rel_x - rw / 2) / zoom_val + self.player_pos[0] + 32
        world_y = (rel_y - rh / 2) / zoom_val + self.player_pos[1] + 32
        dx = world_x - (self.player_pos[0] + 32)
        dy = world_y - (self.player_pos[1] + 32)
        mag = math.hypot(dx, dy)
        if mag > 0:
            self.mouse_dir = [dx / mag, dy / mag]

    def _on_joy_axis(self, window, stickid, axisid, value):
        val = value / 32767.0
        if abs(val) < self.joy_deadzone:
            val = 0.0
        if axisid == 0:   self.joy_x = val
        elif axisid == 1: self.joy_y = -val
        elif axisid == 2: self.joy_right_x = val
        elif axisid == 3: self.joy_right_y = -val
        elif axisid == 5 and val > 0.5: self.start_dash()

    def _on_joy_button_down(self, window, stickid, buttonid):
        if buttonid == 7:
            self.toggle_pause()