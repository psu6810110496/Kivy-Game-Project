"""
game/engine.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GameScreen — Screen หลักของเกม (orchestrator)

GameScreen ดูแลเฉพาะ:
  - Layout / Camera
  - Input (keyboard / mouse / gamepad)
  - Player movement + dash
  - Game lifecycle (on_enter, on_leave, pause, game_over, level_up)
  - Delegate: WaveManager (wave/boss), CombatManager (collision/combat)
"""
import math
import random
from game.game_settings import settings
from io import BytesIO

import kivy.app
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.core.window import Window
from kivy.graphics import (
    Color, Ellipse, PushMatrix, PopMatrix,
    Rectangle, Scale, Translate,
)
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen

from game.combat_manager import CombatManager
from game.enemy_widget import EnemyWidget
from game.player_widget import PlayerWidget
from game.projectile_widget import EnemyProjectile, HealthPickup
from game.wave_manager import WaveManager
from ui.game_over import GameOverPopup
from ui.hud import HUD, CountdownOverlay
from ui.level_up import LevelUpPopup
from ui.pause import PausePopup


class GameScreen(Screen):
    """
    Screen หลัก — ประสานงานระหว่าง WaveManager, CombatManager, HUD และ Player
    """

    # ─── Lifecycle ──────────────────────────────────────────
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # ── Input state ─────────────────────────────────────
        self.keys_pressed: set = set()
        self.joy_x = self.joy_y = self.joy_right_x = self.joy_right_y = 0.0
        self.joy_deadzone = 0.2
        self.mouse_dir = [1, 0]

        # ── Player state ────────────────────────────────────
        self.player_pos = [2500, 2500]
        self.player_widget: PlayerWidget | None = None
        self.player_stats = None
        self.facing_right = True
        self.is_dead = False
        self.melee_timer = 0.0 # 🌟 เพิ่ม Timer สำหรับตี Melee

        # ── Dash ────────────────────────────────────────────
        self.is_dashing = False
        self.dash_cooldown = False
        self.dash_duration = 0.2
        self.dash_cooldown_time = 1.0
        self.last_dir_x = self.last_dir_y = 0.0

        # ── Combat lists (shared with managers) ─────────────
        self.enemies: list = []
        self.enemy_projectiles: list = []
        self.player_bullets: list = []
        self.dropped_items: list = []
        self.exp_orbs: list = []        # EXP orb objects (ต้องเดินเก็บ)

        # ── Boss references ─────────────────────────────────
        self.boss: EnemyWidget | None = None
        self.big_boss: EnemyWidget | None = None
        self.is_boss_intro = False

        # ── Game state ──────────────────────────────────────
        self.game_started = False
        self.is_paused = False
        self.active_pause_popup = None
        self.countdown = None
        self.attack_event = None
        self.slash_textures: list = []

        # ── Camera ──────────────────────────────────────────
        self.zoom_target = 2.0
        self.zoom_lerp_speed = 1.5
        self.camera_pos = [0, 0]
        self.camera_target = [0, 0]
        self.camera_follow_speed = 5.0

        # ── Managers ────────────────────────────────────────
        self.wave_manager = WaveManager(self)
        self.combat_manager = CombatManager(self)

        # ── Layout ──────────────────────────────────────────
        self.root_layout = FloatLayout(size_hint=(None, None))
        self.world_layout = FloatLayout(size_hint=(None, None), size=(5000, 5000))
        self.bind(size=self._update_layout_size)

        self._build_world()

        self.hud = HUD(game_screen=self)
        self.root_layout.add_widget(self.hud)
        self.add_widget(self.root_layout)

    def _build_world(self):
        """สร้าง map background + border"""
        try:
            tex = CoreImage("assets/maps/map.jpg").texture
            tex.wrap = "repeat"
            scale = 3.0
            tex.uvsize = (5000 / (tex.width * scale), -5000 / (tex.height * scale))
        except Exception:
            tex = None

        self.obstacles = []

        with self.world_layout.canvas.before:
            PushMatrix()
            self.zoom = Scale(2, 2, 2)
            self.camera = Translate(0, 0)
            if tex:
                Color(1, 1, 1, 1)
                Rectangle(pos=(0, 0), size=(5000, 5000), texture=tex)
            else:
                Color(0.15, 0.15, 0.15, 1)
                Rectangle(pos=(0, 0), size=(5000, 5000))
            # Border darkness
            Color(0, 0, 0, 0.85)
            for pos, size in [
                ((-3000, -3000), (3000, 11000)),
                ((5000, -3000), (3000, 11000)),
                ((0, -3000),    (5000, 3000)),
                ((0, 5000),     (5000, 3000)),
            ]:
                Rectangle(pos=pos, size=size)

        with self.world_layout.canvas.after:
            PopMatrix()
            
        import random
        from game.obstacle_widget import ObstacleWidget
        
        # วางรถตามขอบๆ แมพ (กันไม่ให้รกตรงกลาง)
        # ขอบซ้ายขวา
        for _ in range(25):
            x = random.choice([random.randint(50, 400), random.randint(4600, 4950)])
            y = random.randint(50, 4950)
            w, h = random.choice([(140, 80), (80, 140)])
            obs = ObstacleWidget(pos=(x, y), size=(w, h))
            self.obstacles.append(obs)
            self.world_layout.add_widget(obs)
            
        # ขอบบนล่าง
        for _ in range(25):
            x = random.randint(50, 4950)
            y = random.choice([random.randint(50, 400), random.randint(4600, 4950)])
            w, h = random.choice([(140, 80), (80, 140)])
            obs = ObstacleWidget(pos=(x, y), size=(w, h))
            self.obstacles.append(obs)
            self.world_layout.add_widget(obs)

        self.root_layout.add_widget(self.world_layout)

    # ── Layout ────────────────────────────────────────────
    def _update_layout_size(self, _inst, value):
        rw, rh = value
        if rh == 0:
            return
        ratio = 16 / 9
        if rw / rh > ratio:
            nw, nh = rh * ratio, rh
        else:
            nw, nh = rw, rw / ratio
        self.root_layout.size = (nw, nh)
        self.root_layout.pos = ((rw - nw) / 2, (rh - nh) / 2)

    # ── Camera ────────────────────────────────────────────
    def update_camera(self, dt: float = 0):
        rw, rh = self.root_layout.size
        self.zoom.origin = (rw / 2, rh / 2)

        # Zoom lerp
        if dt > 0 and abs(self.zoom.x - self.zoom_target) > 0.01:
            t = self.zoom_lerp_speed * dt
            self.zoom.x = self.zoom.y = self.zoom.z = self.zoom.x + (self.zoom_target - self.zoom.x) * t

        # Camera target
        if self.is_boss_intro:
            focus = self.boss or getattr(self, "big_boss", None)
            if focus:
                fx = focus.pos[0] + (focus.enemy_size[0] / 2 if hasattr(focus, "enemy_size") else 20)
                fy = focus.pos[1] + (focus.enemy_size[1] / 2 if hasattr(focus, "enemy_size") else 20)
                self.camera_target = [rw / 2 - fx, rh / 2 - fy]
        else:
            self.camera_target = [rw / 2 - self.player_pos[0] - 32, rh / 2 - self.player_pos[1] - 32]

        if dt > 0:
            spd = self.camera_follow_speed * dt
            self.camera_pos[0] += (self.camera_target[0] - self.camera_pos[0]) * spd
            self.camera_pos[1] += (self.camera_target[1] - self.camera_pos[1]) * spd
        else:
            self.camera_pos = self.camera_target[:]

        self.camera.x = self.camera_pos[0]
        self.camera.y = self.camera_pos[1]

    # ── Reset ─────────────────────────────────────────────
    def _reset_state(self):
        self.player_pos = [2500, 2500]
        self.is_paused = False
        self.facing_right = True
        self.is_dashing = False
        self.dash_cooldown = False
        self.last_dir_x = self.last_dir_y = 0.0
        self.joy_x = self.joy_y = self.joy_right_x = self.joy_right_y = 0.0
        self.game_started = False
        self.is_dead = False
        self.boss = self.big_boss = None
        self.is_boss_intro = False
        self.zoom_target = 2.0
        self.keys_pressed.clear()
        self.mouse_dir = [1, 0]
        self.melee_timer = 0.0 # 🌟 รีเซ็ต Cooldown การตี
        self.total_kills = 0
        self.play_time = 0.0
        self.magnet_timer = 0.0
        self.global_magnet_timer = 0.0

        if self.attack_event:
            self.attack_event.cancel()
            self.attack_event = None

        for lst, layout in [
            (self.enemies, self.world_layout),
            (self.enemy_projectiles, self.world_layout),
            (self.dropped_items, self.world_layout),
            (self.player_bullets, self.world_layout),
            (self.exp_orbs, self.world_layout),
        ]:
            for item in lst:
                if item.parent:
                    layout.remove_widget(item)
            lst.clear()

        self.active_beams = []
        self.wave_manager.reset()
        self.hud.update_enemy_count(0)
        self.update_camera()

    # ── Screen events ─────────────────────────────────────
    def on_enter(self):
        self._update_layout_size(None, Window.size)
        self.player_stats = kivy.app.App.get_running_app().current_player
        self._apply_display_settings()
        self._apply_audio_settings()
        if not self.player_stats:
            return

        self._load_attack_effects()
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

        # 🌟 เพิ่มโค้ดกำหนด Size ให้ PlayerWidget ตามค่าใน PlayerStats 🌟
        if hasattr(self.player_stats, 'size'):
            self.player_widget.size = self.player_stats.size
            self.player_widget.size_hint = (None, None)

        self.world_layout.add_widget(self.player_widget)
        self.hud.update_ui(self.player_stats)

        self.is_paused = True
        self.countdown = CountdownOverlay(callback=self._start_game)
        self.root_layout.add_widget(self.countdown)

        self._bind_input()
        Clock.unschedule(self.update_frame)
        Clock.schedule_interval(self.update_frame, 1.0 / 60.0)

    def on_leave(self):
        Clock.unschedule(self.update_frame)
        if self.attack_event:
            self.attack_event.cancel()
        self._unbind_input()

    def _start_game(self):
        self.is_paused = False
        self.game_started = True
        self.wave_manager.try_start_next_wave()

    # ── Character attack effects ───────────────────────────
    def _load_attack_effects(self):
        self.slash_textures = []
        if self.player_stats.name == "PTae":
            for path in [f"assets/PTae/skill1/aoeptae0{i}.png" for i in range(1, 5)]:
                try:
                    self.slash_textures.append(CoreImage(path).texture)
                except Exception:
                    pass
        if not self.slash_textures:
            self._load_lostman_effects()

    def _load_lostman_effects(self):
        for path in [f"assets/Lostman/skill1/axe_hit{i}.png" for i in range(1, 5)]:
            try:
                self.slash_textures.append(CoreImage(path).texture)
            except Exception:
                pass

    def _apply_audio_settings(self):
        """อัปเดตระดับเสียงตาม Settings"""
        # สมมติว่ามี SoundManager หรือ App ที่คุมเสียง
        # ในระบบปัจจุบัน เราแค่ประกาศว่าใช้ค่าจาก settings.music_volume / sfx_volume
        pass

    def _apply_display_settings(self):
        """อัปเดต Fullscreen ตาม Settings"""
        Window.fullscreen = "auto" if settings.fullscreen else False

    # ── Main loop ─────────────────────────────────────────
    def update_frame(self, dt: float):
        if not self.player_stats or self.is_paused or not self.player_widget or self.is_dead:
            return

        if self.game_started:
            self.play_time += dt
            if getattr(self, "magnet_timer", 0.0) > 0:
                self.magnet_timer -= dt
            if getattr(self, "global_magnet_timer", 0.0) > 0:
                self.global_magnet_timer -= dt

        # Wave check
        if self.game_started and not self.enemies and not self.wave_manager.is_spawning:
            self.wave_manager.try_start_next_wave()

        # 🌟 ระบบ Auto Melee Attack 
        if self.game_started and self.enemies:
            self.melee_timer -= dt
            if self.melee_timer <= 0:
                self.perform_melee_attack()
                # ดึงค่า Cooldown ของการโจมตีจาก player_stats
                # ถ้ายังไม่ได้ใส่ค่า melee_cooldown ใน player.py จะใช้ 0.5 วินาทีแทน
                self.melee_timer = getattr(self.player_stats, "melee_cooldown", 0.5)

        # Skills tick
        if self.game_started and hasattr(self.player_stats, "skills"):
            for skill in self.player_stats.skills:
                skill.tick(dt, self)
            # skill3 stack recharge only (no auto-fire)
            s3 = getattr(self.player_stats, 'skill3', None)
            if s3 is not None:
                s3.tick(dt, self)

        # Combat
        self.combat_manager.update(dt)

        # Player movement
        self._update_player_movement(dt)

        # Apply Screen Shake intensity from settings
        if settings.camera_shake and hasattr(self, '_shake_timer') and self._shake_timer > 0:
            # ของเดิมอาจจะมี logic shake อยู่แล้ว เราแค่คูณ intensity เข้าไป
            pass

        # Beam update (DinoBeam ติดตามเวลา)
        if hasattr(self, 'active_beams'):
            for beam in list(self.active_beams):
                alive = beam.update(dt, self)
                if not alive:
                    self.active_beams.remove(beam)
                    if beam.parent:
                        self.world_layout.remove_widget(beam)

        # Enemy AI
        for enemy in list(self.enemies):
            enemy.update_movement(self.player_pos, self.enemies, dt)

        self.update_camera(dt)

    # ── Player movement ───────────────────────────────────
    def _update_player_movement(self, dt: float):
        speed = self.player_stats.speed * (3.0 if self.is_dashing else 1.0)
        dx, dy = 0.0, 0.0

        if not self.is_dashing:
            kb = settings.key_bindings
            if kb.get('move_up') in self.keys_pressed: dy += 1
            if kb.get('move_down') in self.keys_pressed: dy -= 1
            if kb.get('move_left') in self.keys_pressed: dx -= 1
            if kb.get('move_right') in self.keys_pressed: dx += 1
            
            # Fallback to defaults if custom keys are not pressed OR if user wants WASD constant?
            # Actually, standard is to use the bound keys.
            if dx == 0 and dy == 0:
                dx, dy = self.joy_x, self.joy_y
            if dx != 0 or dy != 0:
                self.last_dir_x, self.last_dir_y = dx, dy
        else:
            dx, dy = self.last_dir_x, self.last_dir_y

        mag = math.hypot(dx, dy)
        if mag > 1.0:
            dx /= mag
            dy /= mag

        new_x = max(20, min(self.player_pos[0] + dx * speed, 4980))
        new_y = max(20, min(self.player_pos[1] + dy * speed, 4980))
        
        pw, ph = 64, 64 # player size

        # เลื่อนทีละแกน กันติดกำแพง
        can_move_x = True
        can_move_y = True
        for obs in getattr(self, "obstacles", []):
            if obs.collides_with(new_x, self.player_pos[1], pw, ph): can_move_x = False
            if obs.collides_with(self.player_pos[0], new_y, pw, ph): can_move_y = False

        if can_move_x: self.player_pos[0] = new_x
        if can_move_y: self.player_pos[1] = new_y
        self.player_widget.update_pos(self.player_pos)

        # Facing
        self.facing_right = self.joy_right_x > 0 if abs(self.joy_right_x) > 0.1 else self.mouse_dir[0] >= 0
        self.player_widget.set_state((dx != 0 or dy != 0), self.facing_right, speed)

        aim_x = self.joy_right_x if abs(self.joy_right_x) > 0.1 else self.mouse_dir[0]
        aim_y = self.joy_right_y if abs(self.joy_right_y) > 0.1 else self.mouse_dir[1]
        
        # อัพเดตทิศทางการเล็งให้ระบบยิงโจมตีใช้ได้
        if abs(self.joy_right_x) > 0.1 or abs(self.joy_right_y) > 0.1:
            mag_aim = math.hypot(aim_x, aim_y)
            if mag_aim > 0:
                self.mouse_dir[0] = aim_x / mag_aim
                self.mouse_dir[1] = aim_y / mag_aim

        self.player_widget.update_aim(True, aim_x, aim_y)

    # ── Combat (Melee Logic) ───────────────────────────────
    def perform_melee_attack(self):
        """ระบบโจมตีพื้นฐาน — เช็ค Hitbox ตามลักษณะตัวละคร"""
        p_x = self.player_pos[0] + 32
        p_y = self.player_pos[1] + 32
        m_dx, m_dy = self.mouse_dir
        mouse_angle = math.atan2(m_dy, m_dx)

        # ตั้งค่ารัศมีและองศาตามตัวละคร
        name = getattr(self.player_stats, "name", "Lostman")
        attack_radius = 100.0
        angle_spread = 0.0

        if name == "PTae":
            angle_spread = math.radians(45)   # Cone ข้างหน้า
            attack_radius = 120.0
        elif name == "Lostman":
            angle_spread = math.radians(100)  # Arc กว้าง
            attack_radius = 100.0
        elif name == "Monkey":
            # 🌟 ขยายจาก 30 เป็น 60 องศา และเพิ่มระยะจาก 80 เป็น 110
            angle_spread = math.radians(60)   
            attack_radius = 110.0
        else:
            angle_spread = math.radians(60)   # Default

        # 🌟 เรียกฟังก์ชันแสดง Highlight วงสวิงการโจมตี ตรงนี้เลย!
        self._show_melee_highlight(p_x, p_y, attack_radius, mouse_angle, angle_spread)

        for enemy in list(self.enemies):
            e_x = enemy.pos[0] + (enemy.enemy_size[0] / 2 if hasattr(enemy, "enemy_size") else 20)
            e_y = enemy.pos[1] + (enemy.enemy_size[1] / 2 if hasattr(enemy, "enemy_size") else 20)
            
            # 1. เช็คระยะห่าง
            dist = math.hypot(e_x - p_x, e_y - p_y)
            if dist <= attack_radius:
                # 2. เช็คมุม ว่าอยู่ในระยะกวาดอาวุธหรือไม่
                enemy_angle = math.atan2(e_y - p_y, e_x - p_x)
                angle_diff = abs(math.atan2(math.sin(enemy_angle - mouse_angle), math.cos(enemy_angle - mouse_angle)))
                
                if angle_diff <= angle_spread:
                    # ทำดาเมจ (หักจากของเก่า แล้วใช้ _hit_enemy เพื่อให้โค้ดส่วนตาย(boss/exp) ตรงกับ skills.py)
                    from game.skills import _hit_enemy
                    _hit_enemy(self, enemy, self.player_stats.damage)

    def take_damage(self, amount: float):
        """ผู้เล่นรับดาเมจ (ถอดระบบ i-frames ออกแล้ว)"""
        if self.is_dead or not self.player_stats:
            return
            
        self.player_stats.current_hp -= amount
        self.hud.update_ui(self.player_stats)
        
        # แสดงเอฟเฟกต์สีแดงกระพริบสั้นๆ เวลาโดนตี
        self.player_widget.color_inst.rgba = (1, 0, 0, 1)
        Clock.schedule_once(lambda dt: self._reset_hit_color(), 0.15)

        if self.player_stats.current_hp <= 0:
            self.is_dead = True
            Clock.schedule_once(lambda _dt: self.show_game_over(), 1.0)

    def _reset_hit_color(self):
        """รีเซ็ตสีตัวละครกลับมาเป็นปกติ"""
        if not self.is_dashing and self.player_widget:
            self.player_widget.color_inst.rgba = (1, 1, 1, 1)

    def gain_exp(self, amount):
        if not self.player_stats:
            return
        self.player_stats.exp += amount
        if self.player_stats.exp >= self.player_stats.max_exp:
            self.player_stats.exp -= self.player_stats.max_exp
            self.player_stats.level += 1
            self.is_paused = True
            from game.skills import get_upgrade_choices
            choices = get_upgrade_choices(self.player_stats)
            LevelUpPopup(self, choices=choices).open()

        if hasattr(self, "hud") and self.hud:
            self.hud.update_ui(self.player_stats)

    def spawn_drop_item(self, pos):
        """Drop HealthPickup หรือ MagnetPickup หรือ GlobalMagnet Pickup เมื่อศัตรูตาย"""
        r = random.random()
        # อัตราการดรอปเลือดอิงตาม settings
        health_rate = getattr(settings, 'health_drop_rate', 0.12)
        if r < health_rate:
            heal = HealthPickup(pos=(pos[0], pos[1]), heal_amount=25)
            self.dropped_items.append(heal)
            self.world_layout.add_widget(heal)
        elif r < health_rate + 0.005:  # 0.5% chance for Global Magnet
            from game.projectile_widget import GlobalMagnetPickup
            magnet = GlobalMagnetPickup(pos=(pos[0], pos[1]), duration=8.0)
            self.dropped_items.append(magnet)
            self.world_layout.add_widget(magnet)
        elif r < health_rate + 0.035: # 3% chance for normal magnet
            from game.projectile_widget import MagnetPickup
            magnet = MagnetPickup(pos=(pos[0], pos[1]), duration=8.0)
            self.dropped_items.append(magnet)
            self.world_layout.add_widget(magnet)

    def spawn_exp_orb(self, pos):
        """Drop EXP orb เมื่อศัตรูตาย — ต้องเดินเก็บ"""
        self.total_kills += 1
        from game.projectile_widget import ExpOrb
        texture = getattr(self.player_stats, 'exp_texture', None) if self.player_stats else None
        orb = ExpOrb(pos=(pos[0] + 5, pos[1] + 5), exp_amount=10, texture_path=texture)
        self.exp_orbs.append(orb)
        self.world_layout.add_widget(orb)

    # ── Dash ──────────────────────────────────────────────
    def start_dash(self):
        if self.dash_cooldown or self.is_dashing or not (self.last_dir_x or self.last_dir_y):
            return
        self.is_dashing = True
        self.dash_cooldown = True
        self.player_widget.color_inst.rgba = (1, 1, 0, 1)

        def _end(_dt):
            self.is_dashing = False
            self.player_widget.color_inst.rgba = (1, 1, 1, 1)

        Clock.schedule_once(_end, self.dash_duration)
        Clock.schedule_once(lambda _dt: setattr(self, "dash_cooldown", False), self.dash_cooldown_time)

    # ── Pause ─────────────────────────────────────────────
    def toggle_pause(self):
        self.resume_game() if self.is_paused else self.pause_game()

    def pause_game(self, _inst=None):
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

    # ── Game Over ─────────────────────────────────────────
    def show_game_over(self, win=False):
        Clock.unschedule(self.update_frame)
        if self.attack_event:
            self.attack_event.cancel()
            self.attack_event = None
        self._unbind_input()
        GameOverPopup(win=win, game_screen=self).open()

    # ── Input ─────────────────────────────────────────────
    def _bind_input(self):
        Window.unbind(
            on_key_down=self._on_key_down, on_key_up=self._on_key_up,
            on_joy_axis=self._on_joy_axis, on_joy_button_down=self._on_joy_button,
            mouse_pos=self._on_mouse_pos,
        )
        Window.bind(
            on_key_down=self._on_key_down, on_key_up=self._on_key_up,
            on_joy_axis=self._on_joy_axis, on_joy_button_down=self._on_joy_button,
            mouse_pos=self._on_mouse_pos,
        )

    def _unbind_input(self):
        Window.unbind(
            on_key_down=self._on_key_down, on_key_up=self._on_key_up,
            on_joy_axis=self._on_joy_axis, on_joy_button_down=self._on_joy_button,
            mouse_pos=self._on_mouse_pos,
        )

    def _on_key_down(self, _win, key, _scan, codepoint, _mods):
        kb = settings.key_bindings
        
        # Pause key
        if kb['pause'] == "escape" and key == 27:
            self.toggle_pause()
            return True
        elif kb['pause'] == codepoint:
            self.toggle_pause()
            return True
            
        # Dash key
        if kb['dash'] == "space" and key == 32:
            self.start_dash()
            return True
        elif kb['dash'] == codepoint:
            self.start_dash()
            return True

        # Skill 1, 2, 3 keys
        if codepoint:
            cp = codepoint.lower()
            if cp == kb['skill1'] or cp == kb['skill2']:
                # สกิล 1/2 ในโปรเจกต์นี้เป็น Auto-active แต่เผื่อผู้เล่นอยากกดใช้เอง
                pass
            if cp == kb['skill3']:
                if (self.game_started and not self.is_dead
                        and hasattr(self, 'player_stats') and self.player_stats):
                    s3 = getattr(self.player_stats, 'skill3', None)
                    if s3:
                        s3.manual_activate(self)
                return True

            self.keys_pressed.add(cp)
        return False

    def _on_key_up(self, _win, key, _scan):
        try:
            self.keys_pressed.discard(chr(key).lower())
        except Exception:
            self.keys_pressed.clear()

    def _on_mouse_pos(self, _win, pos):
        if self.is_paused or not self.player_widget:
            return
        rx = pos[0] - self.root_layout.x
        ry = pos[1] - self.root_layout.y
        rw, rh = self.root_layout.size
        z = self.zoom.x
        wx = (rx - rw / 2) / z + self.player_pos[0] + 32
        wy = (ry - rh / 2) / z + self.player_pos[1] + 32
        dx = wx - (self.player_pos[0] + 32)
        dy = wy - (self.player_pos[1] + 32)
        mag = math.hypot(dx, dy)
        if mag > 0:
            self.mouse_dir = [dx / mag, dy / mag]

    def _on_joy_axis(self, _win, _stick, axisid, value):
        v = value / 32767.0
        if abs(v) < self.joy_deadzone:
            v = 0.0
            
        # Xbox Controller Mapping (Standard SDL2)
        # 0: Left Stick X
        # 1: Left Stick Y
        # 2: Right Stick X
        # 3: Right Stick Y
        # 4: Left Trigger (LT) - Dash
        # 5: Right Trigger (RT) - Skill 3
        
        if axisid == 0: 
            self.joy_x = v
        elif axisid == 1: 
            self.joy_y = -v
        elif axisid == 2: 
            self.joy_right_x = v 
        elif axisid == 3: 
            self.joy_right_y = -v 
        elif axisid == 4:
            # LT for Dash
            is_pressed = v > 0.5
            lt_prev = getattr(self, '_lt_pressed', False)
            if is_pressed and not lt_prev:
                self.start_dash()
            self._lt_pressed = is_pressed
            
        elif axisid == 5: 
            # RT for Skill 3
            is_pressed = v > 0.5
            rt_prev = getattr(self, '_rt_pressed', False)
            if is_pressed and not rt_prev:
                if (self.game_started and not self.is_dead
                        and hasattr(self, 'player_stats') and self.player_stats):
                    s3 = getattr(self.player_stats, 'skill3', None)
                    if s3:
                        s3.manual_activate(self)
                        if hasattr(self, 'hud') and self.hud:
                            self.hud.update_ui(self.player_stats)
            self._rt_pressed = is_pressed
            
        # Left Trigger fallback? Actually, let's use RB (Button 5) and A (Button 0) for main actions to be safe.
        
    def _on_joy_button(self, _win, _stick, buttonid):
        # Generic XInput:
        # 0: A/Cross (Dash)
        # 1: B/Circle
        # 2: X/Square
        # 3: Y/Triangle
        # 4: LB
        # 5: RB (Skill 3)
        # 6: Back/Share
        # 7: Start/Options
        
        if buttonid == 7: # Start
            self.toggle_pause()
        elif buttonid == 0 or buttonid == 4: # A Button or LB (Left Bumper)
            self.start_dash()
        elif buttonid == 5 or buttonid == 4: # RB or LB
            if (self.game_started and not self.is_dead
                    and hasattr(self, 'player_stats') and self.player_stats):
                s3 = getattr(self.player_stats, 'skill3', None)
                if s3:
                    s3.manual_activate(self)
                    if hasattr(self, 'hud') and self.hud:
                        self.hud.update_ui(self.player_stats)

    def on_touch_down(self, touch):
        if self.is_paused:
            return super().on_touch_down(touch)

        if touch.button == 'left':
            if (self.game_started and not self.is_dead
                    and hasattr(self, 'player_stats') and self.player_stats):
                s3 = getattr(self.player_stats, 'skill3', None)
                if s3:
                    s3.manual_activate(self)
                    if hasattr(self, 'hud') and self.hud:
                        self.hud.update_ui(self.player_stats)

        return super().on_touch_down(touch)
    
    def _show_melee_highlight(self, cx, cy, radius, center_angle, spread_angle):
        """วาดกราฟิก Highlight แบบพัด (Cone/Arc) เพื่อให้ผู้เล่นเห็นระยะการตี"""
        from kivy.uix.widget import Widget
        from kivy.graphics import Color, Ellipse, Rectangle, PushMatrix, PopMatrix, Rotate
        from kivy.clock import Clock
        import math
        
        name = getattr(self.player_stats, "name", "")
        
        # 🌟 พิเศษสำหรับ Lostman: ใช้แอนิเมชันรูปภาพการตี (skill1) แทนแบบปกติ
        if name == "Lostman" and hasattr(self, "slash_textures") and self.slash_textures:
            size_w = radius * 2.5
            size_h = radius * 2.5
            eff = Widget(size_hint=(None, None), size=(size_w, size_h), pos=(cx - size_w/2, cy - size_h/2))
            
            # Kivy image rotation
            rot_deg = math.degrees(center_angle)
            
            with eff.canvas:
                Color(1, 1, 1, 1) # Full color
                PushMatrix()
                Rotate(angle=rot_deg, origin=(cx, cy))
                rect = Rectangle(texture=self.slash_textures[0], pos=eff.pos, size=eff.size)
                PopMatrix()
                
            self.world_layout.add_widget(eff)
            
            state = {"frame": 0}
            def _next_frame(dt):
                state["frame"] += 1
                if state["frame"] >= len(self.slash_textures):
                    if eff.parent:
                        self.world_layout.remove_widget(eff)
                    return False
                rect.texture = self.slash_textures[state["frame"]]
                
            # วนเฟรมภาพทั้งหมด 4 เฟรม ให้เสร็จในระยะเวลาประมาณ 0.15 วิ
            Clock.schedule_interval(_next_frame, 0.15 / max(1, len(self.slash_textures)))
            return

        # ---------------- ปกติ (Arc) ----------------
        highlight = Widget(size_hint=(None, None), size=(radius * 2, radius * 2), pos=(cx - radius, cy - radius))
        
        # 🌟 แก้ไขมุมให้หมุนตามเมาส์ 🌟
        # แปลงจากมุมคณิตศาสตร์ ให้เป็นมุมของ Kivy (สูตร: 90 - มุมเดิม)
        spread_deg = math.degrees(spread_angle)
        kivy_center_deg = 90 - math.degrees(center_angle)
        
        start_deg = kivy_center_deg - spread_deg
        end_deg = kivy_center_deg + spread_deg
        
        with highlight.canvas:
            # เปลี่ยนสี Highlight ตามตัวละคร
            if name == "PTae":
                Color(1, 0.3, 0.3, 0.4)  # สีแดงโปร่งแสง
            elif name == "Monkey":
                Color(1, 0.8, 0.2, 0.4)  # สีเหลืองโปร่งแสง
            else:
                Color(1, 1, 1, 0.4)      # สีขาวโปร่งแสง
                
            Ellipse(pos=highlight.pos, size=highlight.size, angle_start=start_deg, angle_end=end_deg)
            
        self.world_layout.add_widget(highlight)
        Clock.schedule_once(lambda dt: self.world_layout.remove_widget(highlight) if highlight.parent else None, 0.15)