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
from kivy.graphics.texture import Texture
import kivy.app
import math
import random
from io import BytesIO

from game.player_widget import PlayerWidget
from ui.hud import HUD, CountdownOverlay
from ui.level_up import LevelUpPopup
from ui.pause import PausePopup
from ui.game_over import GameOverPopup
from game.enemy_widget import EnemyWidget
from game.projectile_widget import EnemyProjectile
from game.skills import get_upgrade_choices, _hit_enemy


# ═════════════════════════════════════════════════════════════════════════
# Helper function to extract sprite sheet frames
# ═════════════════════════════════════════════════════════════════════════
def extract_sprite_sheet_frames(image_path, rows, cols):
    """
    Extract individual frames from a sprite sheet image

    Args:
        image_path: Path to the sprite sheet image
        rows: Number of rows in the grid
        cols: Number of columns in the grid

    Returns:
        List of Kivy Texture objects for each frame (row-major order)
    """
    try:
        from PIL import Image  # type: ignore

        # Load image using PIL
        img = Image.open(image_path)
        img_width, img_height = img.size

        # Calculate frame dimensions
        frame_width = img_width // cols
        frame_height = img_height // rows

        frames = []

        # Extract frames in row-major order (top-left to bottom-right)
        for row in range(rows):
            for col in range(cols):
                # Crop the frame
                left = col * frame_width
                top = row * frame_height
                right = left + frame_width
                bottom = top + frame_height

                frame_img = img.crop((left, top, right, bottom))

                # Convert PIL image to Kivy Texture
                # Save to bytes
                png_data = BytesIO()
                frame_img.save(png_data, format="PNG")
                png_data.seek(0)

                # Create Kivy texture from image data
                texture = CoreImage(BytesIO(png_data.getvalue()), ext="png").texture
                frames.append(texture)

        print(f"✓ Extracted {len(frames)} frames from {image_path} ({rows}x{cols})")
        return frames
    except ImportError as e:
        print(f"[Error] PIL not available: {e}")
        return None
    except Exception as e:
        print(f"[Error] Failed to extract sprite frames: {e}")
        return None


class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # ── Input ─────────────────────────────────────────
        self.keys_pressed = set()
        self.joy_x = self.joy_y = self.joy_right_x = self.joy_right_y = 0.0
        self.joy_lt_pressed = False
        self.joy_deadzone = 0.2
        self.mouse_world_pos = [0, 0]
        self.mouse_dir = [1, 0]

        # ── Player ────────────────────────────────────────
        self.player_pos = [2500, 2500]
        self.player_widget = None
        self.player_stats = None
        self.facing_right = True
        self.is_left_clicked = False
        self.is_invincible = False
        self.is_dead = False

        # ── Dash ──────────────────────────────────────────
        self.is_dashing = False
        self.dash_cooldown = False
        self.dash_duration = 0.2
        self.dash_cooldown_time = 1.0
        self.last_dir_x = 0
        self.last_dir_y = 0

        # ── Combat ────────────────────────────────────────
        self.enemies = []
        self.enemy_projectiles = []
        self.player_bullets = []
        self.attack_event = None

        # ── Wave / State ──────────────────────────────────
        self.current_wave = 0
        self.is_spawning_wave = False
        self.wave_label = None
        self.game_started = False
        self.is_paused = False
        self.active_pause_popup = None
        self.countdown = None

        # ── Boss ──────────────────────────────────────────
        self.boss = None
        self.big_boss = None
        self.is_boss_intro = False
        self.boss_overlay = None

        # ── Camera zoom (lerp) ────────────────────────────
        self.zoom_target = 2.0
        self.zoom_lerp_speed = 1.5

        # ── Camera follow smoothing ────────────────────────
        self.camera_pos = [0, 0]  # Current camera position
        self.camera_target = [0, 0]  # Target camera position
        self.camera_follow_speed = 5.0  # Damping factor (higher = faster follow)

        # ── Slash textures (will be loaded based on character) ────
        self.slash_textures = []

        # ── Layout ────────────────────────────────────────
        self.root_layout = FloatLayout(size_hint=(None, None))
        self.world_layout = FloatLayout(size_hint=(None, None), size=(5000, 5000))
        self.bind(size=self._update_layout_size)

        # ── Map ───────────────────────────────────────────
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
            Rectangle(pos=(5000, -3000), size=(3000, 11000))
            Rectangle(pos=(0, -3000), size=(5000, 3000))
            Rectangle(pos=(0, 5000), size=(5000, 3000))

        with self.world_layout.canvas.after:
            PopMatrix()

        self.root_layout.add_widget(self.world_layout)
        self.hud = HUD(game_screen=self)
        self.root_layout.add_widget(self.hud)
        self.add_widget(self.root_layout)

    # ── Layout ────────────────────────────────────────────
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

    # ── Camera (lerp zoom + smooth follow) ────────────────────────────────
    def update_camera(self, dt=0):
        rw, rh = self.root_layout.size
        self.zoom.origin = (rw / 2, rh / 2)

        # zoom lerp
        if dt > 0 and abs(self.zoom.x - self.zoom_target) > 0.01:
            self.zoom.x += (self.zoom_target - self.zoom.x) * self.zoom_lerp_speed * dt
            self.zoom.y += (self.zoom_target - self.zoom.y) * self.zoom_lerp_speed * dt
            self.zoom.z = self.zoom.x

        # Determine target camera position
        # boss intro → โฟกัสบอสหรือบิ๊กบอส
        if self.is_boss_intro:
            focus = None
            if self.boss and self.boss.parent:
                focus = self.boss
            elif hasattr(self, "big_boss") and self.big_boss and self.big_boss.parent:
                focus = self.big_boss
            if focus:
                bx = focus.pos[0] + (
                    focus.enemy_size[0] / 2 if hasattr(focus, "enemy_size") else 20
                )
                by = focus.pos[1] + (
                    focus.enemy_size[1] / 2 if hasattr(focus, "enemy_size") else 20
                )
                self.camera_target[0] = (rw / 2) - bx
                self.camera_target[1] = (rh / 2) - by
        else:
            self.camera_target[0] = (rw / 2) - self.player_pos[0] - 32
            self.camera_target[1] = (rh / 2) - self.player_pos[1] - 32

        # Smoothly follow target position with damping
        if dt > 0:
            # Linear interpolation towards target (damped follow)
            self.camera_pos[0] += (self.camera_target[0] - self.camera_pos[0]) * self.camera_follow_speed * dt
            self.camera_pos[1] += (self.camera_target[1] - self.camera_pos[1]) * self.camera_follow_speed * dt
        else:
            # First frame or dt=0, snap to target
            self.camera_pos = self.camera_target[:]

        # Apply smoothed camera position
        self.camera.x = self.camera_pos[0]
        self.camera.y = self.camera_pos[1]

    # ── Reset ─────────────────────────────────────────────
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
        self.is_spawning_wave = False
        self.current_wave = 0
        self.is_dead = False
        self.boss = None
        self.big_boss = None
        self.is_boss_intro = False
        self.zoom_target = 2.0
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

        # reset HUD enemy count
        if hasattr(self, "hud") and self.hud:
            self.hud.update_enemy_count(0)

        self.update_camera()

    # ── Lifecycle ─────────────────────────────────────────
    def on_enter(self):
        self._update_layout_size(None, Window.size)
        self.player_stats = kivy.app.App.get_running_app().current_player
        if not self.player_stats:
            return

        # Load character-specific attack effects
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
        self.world_layout.add_widget(self.player_widget)
        self.hud.update_ui(self.player_stats)

        self.is_paused = True
        self.countdown = CountdownOverlay(callback=self.start_actual_game)
        self.root_layout.add_widget(self.countdown)

        Window.unbind(
            on_key_down=self._on_window_key_down, on_key_up=self._on_window_key_up
        )
        Window.unbind(
            on_joy_axis=self._on_joy_axis, on_joy_button_down=self._on_joy_button_down
        )
        Window.unbind(mouse_pos=self._on_mouse_pos)
        Window.bind(
            on_key_down=self._on_window_key_down, on_key_up=self._on_window_key_up
        )
        Window.bind(
            on_joy_axis=self._on_joy_axis, on_joy_button_down=self._on_joy_button_down
        )
        Window.bind(mouse_pos=self._on_mouse_pos)

        Clock.unschedule(self.update_frame)
        Clock.schedule_interval(self.update_frame, 1.0 / 60.0)

    def on_leave(self):
        Clock.unschedule(self.update_frame)
        if self.attack_event:
            self.attack_event.cancel()
        Window.unbind(
            on_key_down=self._on_window_key_down, on_key_up=self._on_window_key_up
        )
        Window.unbind(
            on_joy_axis=self._on_joy_axis, on_joy_button_down=self._on_joy_button_down
        )
        Window.unbind(mouse_pos=self._on_mouse_pos)

    def _load_attack_effects(self):
        """Load character-specific attack effect textures"""
        self.slash_textures = []

        if self.player_stats.name == "PTae":
            # PTae uses aoeptae01-04 frames for all attacks
            ptae_frames = [
                "assets/PTae/skill1/aoeptae01.png",
                "assets/PTae/skill1/aoeptae02.png",
                "assets/PTae/skill1/aoeptae03.png",
                "assets/PTae/skill1/aoeptae04.png",
            ]

            try:
                for path in ptae_frames:
                    try:
                        texture = CoreImage(path).texture
                        self.slash_textures.append(texture)
                    except Exception as e:
                        print(f"[Warning] Could not load {path}: {e}")
                        continue

                if self.slash_textures:
                    print(
                        f"✓ Successfully loaded PTae attacks: {len(self.slash_textures)} frames (aoeptae01-04)"
                    )
                    return
                else:
                    print("[Fallback] No PTae frames loaded, using Lostman effects")
                    self._load_lostman_effects()
            except Exception as e:
                print(f"[Error] Failed to load PTae attack effects: {e}")
                # Fallback to Lostman effects
                self._load_lostman_effects()
        else:
            # Default to Lostman effects for other characters (Lostman, Monkey)
            self._load_lostman_effects()

    def _load_lostman_effects(self):
        """Load Lostman's attack effect textures (NPT100-103 animation frames)"""
        for path in [
            "assets/effect/NPT100.png",
            "assets/effect/NPT101.png",
            "assets/effect/NPT102.png",
            "assets/effect/NPT103.png",
        ]:
            try:
                texture = CoreImage(path).texture
                self.slash_textures.append(texture)
            except Exception:
                pass
                pass

    # ── Game Start ────────────────────────────────────────
    def start_actual_game(self):
        self.is_paused = False
        self.game_started = True
        self.start_next_wave()
        # skills.py จัดการ cooldown + attack + animation เองผ่าน skill.tick()

    # ── Wave ──────────────────────────────────────────────
    def start_next_wave(self, *args):
        if self.is_spawning_wave or self.is_dead:
            return
        self.is_spawning_wave = True
        self.current_wave += 1
        self.show_wave_title()
        Clock.schedule_once(self._spawn_wave_enemies, 1.5)

    def _spawn_wave_enemies(self, dt):
        if self.is_dead or not self.game_started:
            self.is_spawning_wave = False
            return
            
        # เช็คว่าเป็น Wave ของ Boss หรือ Big Boss หรือไม่
        is_boss_wave = (self.current_wave % 10 == 5)
        is_big_boss_wave = (self.current_wave % 10 == 0 and self.current_wave > 0)

        # ถ้าเป็น Wave บอส ให้เรียกบอสอย่างเดียว
        if is_boss_wave:
            self.start_boss_fight()
        elif is_big_boss_wave:
            self.start_big_boss_fight()
        else:
            # ถ้าเป็น Wave ปกติ ค่อยให้มอนสเตอร์ลูกน้องเกิด
            for _ in range(5 + self.current_wave * 2):
                self.spawn_single_enemy()

        self.is_spawning_wave = False

    def spawn_single_enemy(self, force_type=None):
        etype = (
            force_type
            or random.choices(["normal", "stalker", "ranger"], weights=[60, 25, 15])[0]
        )
        angle = random.uniform(0, 2 * math.pi)
        radius = random.uniform(850, 1100)
        spawn_x = self.player_pos[0] + math.cos(angle) * radius
        spawn_y = self.player_pos[1] + math.sin(angle) * radius
        enemy = EnemyWidget(spawn_pos=(spawn_x, spawn_y), enemy_type=etype)
        # give enemy reference back to game for special behaviors
        enemy.game = self
        self.enemies.append(enemy)
        self.world_layout.add_widget(enemy)
        # แจ้ง HUD ว่าจำนวนศัตรูเปลี่ยน
        if hasattr(self, "hud") and self.hud:
            self.hud.update_enemy_count(len(self.enemies))

    def show_wave_title(self):
        if self.wave_label and self.wave_label.parent:
            self.root_layout.remove_widget(self.wave_label)
        self.wave_label = Label(
            text=f"[b]WAVE {self.current_wave}[/b]",
            markup=True,
            font_size=64,
            color=(1, 1, 1, 1),
            outline_width=3,
            outline_color=(0, 0, 0, 1),
            pos_hint={"center_x": 0.5, "top": 0.95},
        )
        self.root_layout.add_widget(self.wave_label)
        if self.hud:
            self.hud.update_wave(self.current_wave)
        Clock.schedule_once(self._hide_wave_title, 1.5)

    def _hide_wave_title(self, dt):
        if self.wave_label and self.wave_label.parent:
            self.root_layout.remove_widget(self.wave_label)
        self.wave_label = None

    # ── Boss ──────────────────────────────────────────────
    # ── Boss ──────────────────────────────────────────────
    def start_boss_fight(self, *args):
        # เอา if self.boss is not None: return ออกไปเลยครับ ให้มันเสกใหม่ทับไปเลย
        
        angle = random.uniform(0, 2 * math.pi)
        bx = self.player_pos[0] + math.cos(angle) * 900
        by = self.player_pos[1] + math.sin(angle) * 900
        self.boss = EnemyWidget(spawn_pos=(bx, by), enemy_type="boss")
        self.boss.game = self
        self.enemies.append(self.boss)
        self.world_layout.add_widget(self.boss)
        if hasattr(self, "hud") and self.hud:
            self.hud.update_enemy_count(len(self.enemies))
        self.zoom_target = 3.0  # zoom in ตอน boss
        self.is_boss_intro = True
        self._show_boss_overlay()

    def start_big_boss_fight(self, *args):
        # เอา if self.big_boss is not None: return ออกเช่นกันครับ
        
        angle = random.uniform(0, 2 * math.pi)
        bx = self.player_pos[0] + math.cos(angle) * 900
        by = self.player_pos[1] + math.sin(angle) * 900
        boss = EnemyWidget(spawn_pos=(bx, by), enemy_type="big_boss")
        boss.game = self
        self.big_boss = boss
        self.enemies.append(boss)
        self.world_layout.add_widget(boss)
        if hasattr(self, "hud") and self.hud:
            self.hud.update_enemy_count(len(self.enemies))
        self.zoom_target = 3.0
        self.is_boss_intro = True
        self._show_big_boss_overlay()
        
    def _show_big_boss_overlay(self):
        if self.boss_overlay and self.boss_overlay.parent:
            self.root_layout.remove_widget(self.boss_overlay)
        self.boss_overlay = Label(
            text="[b]BIG BOSS ARRIVES[/b]",
            markup=True,
            font_size=120,
            color=(0.8, 0.1, 0.8, 1),
            outline_width=3,
            outline_color=(0, 0, 0, 1),
            pos_hint={"center_x": 0.5, "center_y": 0.7},
        )
        self.root_layout.add_widget(self.boss_overlay)
        Clock.schedule_once(self._end_boss_intro, 2.0)

    def _show_boss_overlay(self):
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
        Clock.schedule_once(self._end_boss_intro, 2.0)

    def _end_boss_intro(self, dt):
        self.is_boss_intro = False
        self.zoom_target = 2.0  # zoom กลับ
        if self.boss_overlay and self.boss_overlay.parent:
            self.root_layout.remove_widget(self.boss_overlay)
        self.boss_overlay = None

    # ── Main Loop ─────────────────────────────────────────
    def update_frame(self, dt):
        if (
            not self.player_stats
            or self.is_paused
            or not self.player_widget
            or self.is_dead
        ):
            return

        # Wave ใหม่ถ้าศัตรูหมด
        if self.game_started and not self.enemies and not self.is_spawning_wave:
            self.start_next_wave()

        # ✅ Tick สกิลทุกตัว
        if self.game_started and hasattr(self.player_stats, "skills"):
            for skill in self.player_stats.skills:
                skill.tick(dt, self)

        # อัปเดต player bullets
        for b in list(self.player_bullets):
            b.update(dt)
            hit = False
            for enemy in list(self.enemies):

                if math.hypot(b.pos[0] - (enemy.pos[0] + 20),
                              b.pos[1] - (enemy.pos[1] + 20)) < 40:
                    # Check if it's any boss before hitting
                    is_boss = (enemy is self.boss or enemy is getattr(self, 'big_boss', None))

                    _hit_enemy(self, enemy, b.damage)
                    # If it was the boss and is now gone from enemies list, clear reference
                    if is_boss and enemy not in self.enemies:
                        # clear whichever boss reference was hit
                        if enemy is self.boss:
                            self.boss = None
                        if hasattr(self, 'big_boss') and enemy is self.big_boss:
                            self.big_boss = None
                    self._remove_player_bullet(b)
                    hit = True
                    break
            if not hit and b in self.player_bullets:
                if (
                    math.hypot(
                        b.pos[0] - (self.player_pos[0] + 32),
                        b.pos[1] - (self.player_pos[1] + 32),
                    )
                    > 700
                ):
                    self._remove_player_bullet(b)

        # อัปเดตกระสุนศัตรู
        p_cx = self.player_pos[0] + 32
        p_cy = self.player_pos[1] + 32
        for proj in list(self.enemy_projectiles):
            proj.update(dt)
            dist = math.hypot(proj.pos[0] - p_cx, proj.pos[1] - p_cy)
            if dist < 35:
                self.take_damage(proj.damage)
                self._remove_enemy_projectile(proj)
            elif dist > 1200:
                self._remove_enemy_projectile(proj)

        # การเคลื่อนที่ผู้เล่น
        speed = self.player_stats.speed * (3.0 if self.is_dashing else 1.0)
        dir_x, dir_y = 0, 0

        if not self.is_dashing:
            if "w" in self.keys_pressed:
                dir_y += 1
            if "s" in self.keys_pressed:
                dir_y -= 1
            if "a" in self.keys_pressed:
                dir_x -= 1
            if "d" in self.keys_pressed:
                dir_x += 1
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

        self.player_widget.set_state(
            (dir_x != 0 or dir_y != 0), self.facing_right, speed
        )
        aim_x = self.joy_right_x if abs(self.joy_right_x) > 0.1 else self.mouse_dir[0]
        aim_y = self.joy_right_y if abs(self.joy_right_y) > 0.1 else self.mouse_dir[1]
        self.player_widget.update_aim(True, aim_x, aim_y)

        # อัปเดตศัตรู
        for enemy in list(self.enemies):
            enemy.update_movement(self.player_pos, self.enemies)

            if hasattr(enemy, "enemy_type") and enemy.enemy_type == "ranger":
                if not hasattr(enemy, "shoot_cooldown"):
                    enemy.shoot_cooldown = 0.0
                enemy.shoot_cooldown += dt
                if enemy.shoot_cooldown >= 2.5:
                    p = EnemyProjectile(
                        start_pos=(enemy.pos[0] + 20, enemy.pos[1] + 20),
                        target_pos=(p_cx, p_cy),
                        damage=enemy.damage,
                    )
                    self.enemy_projectiles.append(p)
                    self.world_layout.add_widget(p)
                    enemy.shoot_cooldown = 0

            ex = enemy.pos[0] + (
                enemy.enemy_size[0] / 2 if hasattr(enemy, "enemy_size") else 20
            )
            ey = enemy.pos[1] + (
                enemy.enemy_size[1] / 2 if hasattr(enemy, "enemy_size") else 20
            )
            dist = math.hypot(ex - p_cx, ey - p_cy)
            if dist < 45 and not self.is_invincible:
                self.take_damage(enemy.damage)

        self.update_camera(dt)

    # ── Combat Helpers ────────────────────────────────────
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
            # เพิ่มดีเลย์เล็กน้อยก่อนแสดงหน้า Game Over
            # เพื่อให้ผู้เล่นเห็นการตาย/อนิเมชันก่อน
            Clock.schedule_once(lambda dt: self.show_game_over(), 1.0)
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
        Window.unbind(
            on_key_down=self._on_window_key_down, on_key_up=self._on_window_key_up
        )
        Window.unbind(
            on_joy_axis=self._on_joy_axis, on_joy_button_down=self._on_joy_button_down
        )
        Window.unbind(mouse_pos=self._on_mouse_pos)
        GameOverPopup().open()

    # ── EXP / Level Up ────────────────────────────────────
    def gain_exp(self, amount):
        if not self.player_stats:
            return
        self.player_stats.exp += amount
        if self.player_stats.exp >= self.player_stats.max_exp:
            self.player_stats.exp -= self.player_stats.max_exp
            self.player_stats.level += 1
            self.is_paused = True
            choices = get_upgrade_choices(self.player_stats)
            print(
                f"[DEBUG] level up choices returned: {[c['skill'].name for c in choices]} if any"
            )
            if choices:
                LevelUpPopup(self, choices).open()
            else:
                LevelUpPopup(self).open()
        self.hud.update_ui(self.player_stats)

    # ── Dash ──────────────────────────────────────────────
    def start_dash(self):
        if (
            not self.dash_cooldown
            and not self.is_dashing
            and (self.last_dir_x or self.last_dir_y)
        ):
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

    # ── Pause ─────────────────────────────────────────────
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

    # ── Input ─────────────────────────────────────────────
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
        if axisid == 0:
            self.joy_x = val
        elif axisid == 1:
            self.joy_y = -val
        elif axisid == 2:
            self.joy_right_x = val
        elif axisid == 3:
            self.joy_right_y = -val
        elif axisid == 5 and val > 0.5:
            self.start_dash()

    def _on_joy_button_down(self, window, stickid, buttonid):
        if buttonid == 7:
            self.toggle_pause()
