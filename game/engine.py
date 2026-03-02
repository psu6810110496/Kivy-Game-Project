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
        self.dash_duration = 0.2
        self.dash_cooldown_time = 1.0
        self.last_dir_x = 0
        self.last_dir_y = 0

        self.joy_x = self.joy_y = self.joy_right_x = self.joy_right_y = 0.0
        self.joy_lt_pressed = False
        self.joy_deadzone = 0.2

        self.active_pause_popup = None
        self.enemies = []

        # --- [เพิ่มตัวแปรระบบ Wave] ---
        self.current_wave = 0
        self.game_started = False
        # ---------------------------

        # --- [เพิ่มสถานะอมตะ (I-frames) เมื่อโดนโจมตี] ---
        self.is_invincible = False
        # ---------------------------------------------

        self.countdown = None

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
            Rectangle(pos=(-3000, -3000), size=(3000, 11000))  # หมอกซ้าย
            Rectangle(pos=(5000, -3000), size=(3000, 11000))  # หมอกขวา
            Rectangle(pos=(0, -3000), size=(5000, 3000))  # หมอกล่าง
            Rectangle(pos=(0, 5000), size=(5000, 3000))  # หมอกบน

        with self.world_layout.canvas.after:
            PopMatrix()

        # สร้างตัวแปร player_widget ทิ้งไว้ก่อน
        self.player_widget = None
        self.player_stats = None

        self.root_layout.add_widget(self.world_layout)

        self.hud = HUD(game_screen=self)
        self.root_layout.add_widget(self.hud)

        # --- [เพิ่มปุ่ม Clear Enemy ไว้ที่มุมขวาบนของจอ (ใช้ทดสอบ)] ---
        self.btn_clear = Button(
            text="Clear Enemy",
            size_hint=(None, None),
            size=(150, 50),
            pos_hint={"right": 0.98, "top": 0.98},
            background_color=(1, 0, 0, 1),
        )
        self.btn_clear.bind(on_press=self.debug_clear_enemies)
        self.root_layout.add_widget(self.btn_clear)
        # ------------------------------------------------------

        self.add_widget(self.root_layout)

    def _reset_state(self):
        """Reset ทุก state กลับค่าเริ่มต้น เรียกทุกครั้งก่อนเริ่มเกมใหม่"""
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

        self.keys_pressed.clear()

        # Reset กล้องกลับตำแหน่งเริ่มต้น
        self.camera.x = 0
        self.camera.y = 0

    def on_enter(self):
        # 1. ดึงข้อมูลตัวละครที่เลือกมาจากหน้าจอที่แล้ว
        self.player_stats = kivy.app.App.get_running_app().current_player

        if self.player_stats:
            # 2. Reset ทุก state กลับค่าเริ่มต้น
            self._reset_state()

            # 3. ปิด Pause Popup เก่า ถ้ายังค้างอยู่
            if self.active_pause_popup:
                self.active_pause_popup.dismiss()
                self.active_pause_popup = None

            # 4. ลบ Countdown เก่าออก ถ้ายังค้างอยู่
            if self.countdown and self.countdown.parent:
                self.root_layout.remove_widget(self.countdown)
            self.countdown = None

            # 5. ลบ PlayerWidget เก่าออก แล้วสร้างใหม่
            if self.player_widget and self.player_widget.parent:
                self.world_layout.remove_widget(self.player_widget)

            self.player_widget = PlayerWidget(
                idle_frames=self.player_stats.idle_frames,
                walk_frames=self.player_stats.walk_frames,
                start_pos=tuple(self.player_pos),
            )
            self.world_layout.add_widget(self.player_widget)

            # 6. อัปเดต HUD
            self.hud.update_ui(self.player_stats)

            # 7. เริ่ม Countdown แล้วค่อยเริ่มเกมจริง
            self.is_paused = True
            self.countdown = CountdownOverlay(callback=self.start_actual_game)
            self.root_layout.add_widget(self.countdown)

            # 8. Unbind ก่อนเสมอ เพื่อป้องกัน Ghost Input แล้วค่อย Bind ใหม่
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

            # 9. เริ่ม Game Loop ใหม่
            Clock.unschedule(self.update_frame)
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
        print(f"Starting Wave {self.current_wave}!")  # แสดงในคอนโซล

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

    def on_leave(self):
        # หยุด Game Loop และ Unbind input ทั้งหมดตอนออกจากหน้านี้
        Clock.unschedule(self.update_frame)
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

    # --- [🌟 ฟังก์ชันรับดาเมจและอมตะชั่วคราว] ---
    def take_damage(self, amount):
        if self.is_invincible or not self.player_stats:
            return

        self.player_stats.current_hp -= amount

        # เช็คเลือดหมด = Game Over (เบื้องต้นตั้งค่าให้หยุดเกม)
        if self.player_stats.current_hp <= 0:
            self.player_stats.current_hp = 0
            print("GAME OVER!")
            self.is_paused = True
        else:
            # ติดสถานะอมตะ 1 วินาที และทำตัวกะพริบสีแดง
            self.is_invincible = True
            if self.player_widget:
                self.player_widget.color_inst.rgba = (1, 0, 0, 1)  # เปลี่ยนเป็นสีแดง
            Clock.schedule_once(self.reset_invincible, 1.0)

    def reset_invincible(self, dt):
        self.is_invincible = False
        # รีเซ็ตสีกลับเป็นปกติ (ถ้าไม่ได้กำลังแดชอยู่)
        if self.player_widget and not self.is_dashing:
            self.player_widget.color_inst.rgba = (1, 1, 1, 1)

    # ------------------------------------------

    def update_frame(self, dt):
        if not self.player_stats or self.is_paused or not self.player_widget:
            return

        # --- [ระบบตรวจสอบ Wave ถัดไป] ---
        if self.game_started and len(self.enemies) == 0:
            self.start_next_wave()
        # ------------------------------

        # --- [🌟 ระบบโดนโจมตี (Collision Check)] ---
        if not self.is_invincible and self.game_started:
            for enemy in self.enemies:
                # คำนวณระยะห่าง หากศัตรูเดินมาชนตัวผู้เล่น (ระยะ < 30)
                dist = math.hypot(
                    self.player_pos[0] - enemy.pos[0], self.player_pos[1] - enemy.pos[1]
                )
                if dist < 30:
                    self.take_damage(enemy.damage)
                    break  # โดนตีแล้วหยุดเช็ค เพื่อเข้าสู่สถานะอมตะทันที
        # -----------------------------------------

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

        # ส่งลิสต์ศัตรูเข้าไปเพื่อคำนวณการชน/ผลักกันเอง
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
                self.player_widget.color_inst.rgba = (1, 1, 0, 1)  # สีเหลืองตอนแดช
                Clock.schedule_once(self.end_dash, self.dash_duration)
                Clock.schedule_once(self.reset_dash_cooldown, self.dash_cooldown_time)

    def end_dash(self, dt):
        self.is_dashing = False
        # เช็คด้วยว่าไม่ได้ติดสถานะอมตะอยู่ (ตัวจะได้ไม่กลับเป็นสีขาวก่อนกำหนด)
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
