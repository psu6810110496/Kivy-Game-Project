from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window

# 🌟 เพิ่ม InstructionGroup และ Ellipse เข้ามาสำหรับการวาด Hitbox โจมตี
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
from game.player_widget import PlayerWidget
from ui.hud import HUD, CountdownOverlay
from ui.level_up import LevelUpPopup
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
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
        self.dash_duration = 0.2
        self.dash_cooldown_time = 1.0
        self.last_dir_x = 0
        self.last_dir_y = 0

        self.joy_x = self.joy_y = self.joy_right_x = self.joy_right_y = 0.0
        self.joy_lt_pressed = False
        self.joy_deadzone = 0.2

        self.active_pause_popup = None
        self.enemies = []

        self.current_wave = 0
        self.game_started = False
        self.is_invincible = False
        self.countdown = None
        self.attack_event = None  # 🌟 เพิ่มตัวแปรเก็บ Event การโจมตี

        self.root_layout = FloatLayout()
        self.world_layout = FloatLayout(size_hint=(None, None), size=(5000, 5000))

        # จัดการภาพพื้นหลัง Map
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

        self.player_widget = None
        self.player_stats = None

        self.root_layout.add_widget(self.world_layout)

        self.hud = HUD(game_screen=self)
        self.root_layout.add_widget(self.hud)

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
        self.camera.x = 0
        self.camera.y = 0

    def on_enter(self):
        self.player_stats = kivy.app.App.get_running_app().current_player

        if self.player_stats:
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

            Window.unbind(on_key_down=self._on_keydown, on_key_up=self._on_keyup)
            Window.unbind(
                on_joy_axis=self._on_joy_axis,
                on_joy_button_down=self._on_joy_button_down,
            )
            Window.bind(on_key_down=self._on_keydown, on_key_up=self._on_keyup)
            Window.bind(
                on_joy_axis=self._on_joy_axis,
                on_joy_button_down=self._on_joy_button_down,
            )

            Clock.unschedule(self.update_frame)
            Clock.schedule_interval(self.update_frame, 1.0 / 60.0)

    def start_actual_game(self):
        self.is_paused = False
        self.game_started = True
        self.start_next_wave()

        # 🌟 เริ่มระบบออโต้โจมตี (ฟาดทุกๆ 1 วินาที ปรับความเร็วตรงเลข 1.0 ได้เลย)
        if self.attack_event:
            self.attack_event.cancel()
        self.attack_event = Clock.schedule_interval(self.perform_attack, 1.0)

    def perform_attack(self, dt):
        if self.is_paused or not self.game_started or not self.player_stats:
            return

        # 1. หาจุดศูนย์กลางผู้เล่น
        px = self.player_pos[0] + 32
        py = self.player_pos[1] + 32

        # 2. คำนวณทิศทางการตี
        aim_x, aim_y = self.joy_right_x, self.joy_right_y
        if aim_x == 0 and aim_y == 0:
            aim_x, aim_y = self.last_dir_x, self.last_dir_y
        if aim_x == 0 and aim_y == 0:
            aim_x = 1 if self.facing_right else -1
            aim_y = 0

        mag = math.hypot(aim_x, aim_y)
        if mag > 0:
            aim_x /= mag
            aim_y /= mag

        # 3. 🌟 ตั้งค่า Hitbox แบบ "เส้นโค้ง" (Arc / Cone)
        attack_range = 120  # รัศมีความกว้างของการฟาด (ยื่นออกไปไกลขึ้น)
        hit_angle_spread = 60  # รัศมีกวาดข้างละ 60 องศา (รวมพื้นที่โดนตี 120 องศา)

        # หามุมที่ผู้เล่นกำลังหันหน้าไป (เป็นองศา)
        aim_angle_deg = math.degrees(math.atan2(aim_y, aim_x))

        # 4. วาด Effect การโจมตีแบบเส้นโค้ง (คล้ายคลื่นดาบ)
        self.show_slash_effect(px, py, attack_range, aim_angle_deg, hit_angle_spread)

        # 5. เช็คศัตรูในระยะกวาด
        enemies_to_remove = []
        for enemy in self.enemies:
            ex = enemy.pos[0] + 20
            ey = enemy.pos[1] + 20

            dx = ex - px
            dy = ey - py
            dist = math.hypot(dx, dy)

            # ถ้าระยะอยู่ในวงกว้าง
            if dist < attack_range + 20:
                enemy_angle = math.degrees(math.atan2(dy, dx))
                angle_diff = (enemy_angle - aim_angle_deg) % 360

                # ปรับองศาให้เปรียบเทียบง่ายขึ้น
                if angle_diff > 180:
                    angle_diff -= 360

                # ถัาศัตรูอยู่ในมุมฟาด (อยู่ในพื้นที่หน้าพัด)
                if abs(angle_diff) <= hit_angle_spread:
                    enemy.hp -= self.player_stats.damage

                    # Knockback ตามทิศทางการฟาด
                    enemy.pos = (enemy.pos[0] + aim_x * 25, enemy.pos[1] + aim_y * 25)

                    if enemy.hp <= 0:
                        enemies_to_remove.append(enemy)

        # 6. ลบศัตรูและแจก EXP
        for enemy in enemies_to_remove:
            if enemy in self.enemies:
                self.enemies.remove(enemy)
                self.world_layout.remove_widget(enemy)
                self.gain_exp(10)

    def show_slash_effect(self, px, py, radius, aim_angle_deg, spread):
        ig = InstructionGroup()
        ig.add(Color(1, 0.8, 0, 0.4))
        # วาดพัดเส้นโค้ง โดยอิงจากมุมที่หันหน้า
        ig.add(
            Ellipse(
                pos=(px - radius, py - radius),
                size=(radius * 2, radius * 2),
                angle_start=aim_angle_deg - spread,
                angle_end=aim_angle_deg + spread,
            )
        )

        self.world_layout.canvas.add(ig)

        # ฟังก์ชันเคลียร์ Effect อย่างปลอดภัย (แก้บั๊กภาพค้างตอนเด้ง Level Up)
        def remove_effect(dt):
            if ig in self.world_layout.canvas.children:
                self.world_layout.canvas.remove(ig)

        Clock.schedule_once(remove_effect, 0.15)

    def gain_exp(self, amount):
        if not self.player_stats:
            return
        self.player_stats.exp += amount

        # ถ้า EXP เต็ม หลอด
        if self.player_stats.exp >= self.player_stats.max_exp:
            self.player_stats.exp -= self.player_stats.max_exp
            self.player_stats.level += 1
            self.hud.update_ui(self.player_stats)

            # โชว์หน้าต่าง Level UP !
            self.is_paused = True
            popup = LevelUpPopup(self)
            popup.open()
        else:
            self.hud.update_ui(self.player_stats)

    # -------------------------------------------------------------

    def start_next_wave(self):
        self.current_wave += 1
        print(f"Starting Wave {self.current_wave}!")
        for _ in range(10):
            self.spawn_single_enemy()

    def spawn_single_enemy(self):
        angle = random.uniform(0, 2 * math.pi)
        radius = random.uniform(800, 1000)

        spawn_x = self.player_pos[0] + (math.cos(angle) * radius)
        spawn_y = self.player_pos[1] + (math.sin(angle) * radius)

        new_enemy = EnemyWidget(spawn_pos=(spawn_x, spawn_y))
        self.enemies.append(new_enemy)
        self.world_layout.add_widget(new_enemy)

    def debug_clear_enemies(self, instance):
        if not self.game_started or self.is_paused:
            return
        for enemy in self.enemies:
            self.world_layout.remove_widget(enemy)
        self.enemies.clear()
        print("All enemies cleared!")

    def on_leave(self):
        Clock.unschedule(self.update_frame)
        if self.attack_event:
            self.attack_event.cancel()
        Window.unbind(on_key_down=self._on_keydown, on_key_up=self._on_keyup)
        Window.unbind(
            on_joy_axis=self._on_joy_axis, on_joy_button_down=self._on_joy_button_down
        )

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

    def take_damage(self, amount):
        if self.is_invincible or not self.player_stats:
            return

        self.player_stats.current_hp -= amount

        if self.player_stats.current_hp <= 0:
            self.player_stats.current_hp = 0
            self.is_paused = True
            self.show_game_over()
        else:
            self.is_invincible = True
            if self.player_widget:
                self.player_widget.color_inst.rgba = (1, 0, 0, 1)
            Clock.schedule_once(self.reset_invincible, 1.0)

    def reset_invincible(self, dt):
        self.is_invincible = False
        if self.player_widget and not self.is_dashing:
            self.player_widget.color_inst.rgba = (1, 1, 1, 1)

    def show_game_over(self):
        layout = BoxLayout(orientation="vertical", padding=20, spacing=20)

        lbl_dead = Label(text="YOU DIED!", font_size=40, color=(1, 0, 0, 1), bold=True)
        btn_menu = Button(
            text="RETURN TO MENU",
            font_size=20,
            bold=True,
            size_hint=(1, 0.4),
            background_color=(0.2, 0.1, 0.1, 1),
        )
        btn_menu.bind(on_press=self.return_to_menu)

        layout.add_widget(lbl_dead)
        layout.add_widget(btn_menu)

        self.game_over_popup = Popup(
            title="",
            separator_height=0,
            content=layout,
            size_hint=(0.4, 0.3),
            auto_dismiss=False,
            background_color=(0, 0, 0, 0.9),
        )
        self.game_over_popup.open()

    def return_to_menu(self, instance):
        self.game_over_popup.dismiss()
        self.debug_clear_enemies(None)
        if self.attack_event:
            self.attack_event.cancel()
        self.manager.current = "main_menu"

    def update_frame(self, dt):
        if not self.player_stats or self.is_paused or not self.player_widget:
            return

        if self.game_started and len(self.enemies) == 0:
            self.start_next_wave()

        if not self.is_invincible and self.game_started:
            for enemy in self.enemies:
                dist = math.hypot(
                    self.player_pos[0] - enemy.pos[0], self.player_pos[1] - enemy.pos[1]
                )
                if dist < 30:
                    self.take_damage(enemy.damage)
                    break

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

        for enemy in self.enemies:
            enemy.update_movement(self.player_pos, self.enemies)

        if not self.is_left_clicked and not self.joy_lt_pressed:
            if dir_x > 0.1:
                self.facing_right = True
            elif dir_x < -0.1:
                self.facing_right = False
        elif self.joy_lt_pressed:
            if self.joy_right_x > 0.1:
                self.facing_right = True
            elif self.joy_right_x < -0.1:
                self.facing_right = False

        self.player_widget.set_state(
            (dir_x != 0 or dir_y != 0), self.facing_right, speed
        )
        self.player_widget.update_aim(
            self.joy_lt_pressed, self.joy_right_x, self.joy_right_y
        )

        self.zoom.origin = (Window.width / 2, Window.height / 2)
        self.camera.x = (Window.width / 2) - self.player_pos[0] - 32
        self.camera.y = (Window.height / 2) - self.player_pos[1] - 32

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
        if self.player_widget and not self.is_invincible:
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

        if axisid == 0:
            self.joy_x = normalized
        elif axisid == 1:
            self.joy_y = -normalized
        elif axisid == 2:
            self.joy_right_x = normalized
        elif axisid == 3:
            self.joy_right_y = -normalized
        elif axisid == 4:
            self.joy_lt_pressed = normalized > 0.0
        elif axisid == 5:
            if normalized > 0.5:
                self.start_dash()

    def _on_joy_button_down(self, window, stickid, buttonid):
        if buttonid == 7:
            self.toggle_pause()
