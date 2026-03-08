from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
import os
import math
import random
from game.projectile_widget import EnemyProjectile
from game.utils import resolve_path, get_frames

# --- [ Class สำหรับตัวศัตรู ] ---
from game.game_settings import settings

class EnemyWidget(Widget):
    SHOW_DEBUG_STATS = settings.show_enemy_hp
    ENEMY_TEXTURES = {} # จะโหลดแบบ Dynamic ใน __init__ เพื่อรองรับ Spritesheet

    def __init__(self, spawn_pos=(0, 0), enemy_type="normal", **kwargs):
        super().__init__(**kwargs)
        self.pos = spawn_pos
        self.enemy_type = enemy_type

        # ระบบโจมตี (สำหรับ Ranger)
        self.attack_cooldown = 0
        self.shoot_delay = 3.0  # ยิงทุกๆ 2 วินาที

        # คูลดาวน์สำหรับบิ๊กบอส หากเป็นชนิดนั้น
        self.slam_cooldown = random.uniform(3.0, 6.0)
        self.swipe_cooldown = random.uniform(2.0, 4.0)
        self.missile_cooldown = random.uniform(3.0, 5.0)

        # ตัวแปรสำหรับมินิบอส
        self.is_charging = False
        self.charge_cooldown = 7.0
        self.charge_timer = random.uniform(2.0, 5.0)
        self.charge_dir = (0, 0)
        self.charge_duration = 0.0

        self.has_shield = True
        # Sniper ยิงแบบแพทเทิร์น 3 นัด
        self.sniper_cooldown = random.uniform(1.0, 2.0)
        self.time_counter = random.uniform(0, 5.0) # 🌟 สำหรับ Zigzag หรือ AI อื่นๆ


        # --- [ Enemy Stats ] ---
        stats = {
            "normal": {
                "hp": 50,
                "speed": 2.2,
                "damage": 8,
                "color": (1, 1, 1, 1),
                "size": (64, 64),
            },
            "stalker": {
                "hp": 40,
                "speed": 3.8,
                "damage": 5,
                "color": (1, 1, 1, 1),
                "size": (80, 80), # Increase from 64
            },
            "ranger": {
                "hp": 40,
                "speed": 1.8,
                "damage": 12,
                "color": (1, 1, 1, 1),
                "size": (200, 150), # Increased again as requested
            },
            "charger": {
                "hp": 120,
                "speed": 1.5,
                "damage": 25,
                "color": (1.0, 0.5, 0.0, 1), # 🟠 ส้ม
                "size": (80, 80),
            },
            "shielder": {
                "hp": 300,
                "speed": 1.0,
                "damage": 15,
                "color": (0.2, 0.5, 1.0, 1), # 🔵 ฟ้า
                "size": (90, 90),
            },
            "bomber": {
                "hp": 80,
                "speed": 2.5,
                "damage": 20, # ระเบิดแรง
                "color": (1, 1, 1, 1), # 🟡 เหลือง
                "size": (64, 64),
            },
            "sniper": {
                "hp": 60,
                "speed": 0.5,
                "damage": 15,
                "color": (1, 1, 1, 1), # 🩵 ฟ้าอ่อน
                "size": (64, 64),
            },
            "boss": {
                "hp": 450,
                "speed": 1.2,
                "damage": 40,
                "color": (0.9, 0.2, 0.2, 1),
                "size": (96, 96),
            },
            # Big boss type with additional special attacks
            "big_boss": {
                "hp": 1500,
                "speed": 1.0,
                "damage": 55,
                "color": (0.5, 0.1, 0.7, 1),
                "size": (128, 128),
            },
            # Final Boss: Wave 45 Exclusive
            "final_boss": {
                "hp": 50000, 
                "speed": 0.4,
                "damage": 60,
                "color": (0.2, 0.0, 0.5, 1),
                "size": (180, 180),
            },
            "final_boss_clone": {
                "hp": 1000,
                "speed": 0.2,
                "damage": 30,
                "color": (0.3, 0.1, 0.6, 0.6), # Semi-transparent
                "size": (140, 140),
            },
        }

        # --- Final Boss Variables ---
        self.final_phase = 1
        self.final_attack_timer = 5.0
        self.final_attack_index = 0
        self.final_dash_count = 0
        self.final_is_acting = False
        self.lethal_cooldown = 0.0
        self.final_clones = [] # To keep track of spawned clones

        current_stats = stats.get(enemy_type, stats["normal"])
        self.hp = current_stats["hp"]
        self.max_hp = self.hp
        self.speed = current_stats["speed"]
        self.damage = current_stats["damage"]
        self.enemy_size = current_stats["size"]
        
        # 🌟 สุ่มขนาดตัวสำหรับ Normal ให้ดูหลากหลาย (ใหญ่ขึ้นบ้างเล็กน้อย)
        if enemy_type == "normal":
            scale = random.uniform(1.0, 1.3) # ใหญ่ขึ้นได้ถึง 30%
            self.enemy_size = (self.enemy_size[0] * scale, self.enemy_size[1] * scale)
        
        # [Fix] Sniper size should also be increased to match Ranger if they use same base
        if enemy_type == "sniper":
            self.enemy_size = (120, 120)

        # Animation Setup
        self.frame_index = 0
        self.anim_timer = 0
        self.anim_speed = 0.15 # Default
        self.anim_frames = []
        self.is_facing_right = True

        self._init_enemy_visuals(enemy_type)

        # 🌟 ลดขนาด Texture แสดงผล (Visual) ลงอีกให้ดูพอดีช่อง (Hitbox เท่าเดิม)
        # ปรับเหลือ 0.5 (50%) สำหรับมอนทั่วไป และ 0.6 สำหรับบอส
        visual_scale = 0.6 if enemy_type in ["boss", "big_boss", "final_boss"] else 0.5
        self.render_size = (self.enemy_size[0] * visual_scale, self.enemy_size[1] * visual_scale)

        with self.canvas:
            self.color_inst = Color(*current_stats["color"])
            
            # คำนวณตำแหน่งเริ่มต้นให้กึ่งกลาง hitbox
            off_x = (self.enemy_size[0] - self.render_size[0]) / 2
            off_y = (self.enemy_size[1] - self.render_size[1]) / 2
            
            self.rect = Rectangle(
                pos=(self.pos[0] + off_x, self.pos[1] + off_y), 
                size=self.render_size, 
                texture=self.texture
            )
            if self.texture:
                self.rect.tex_coords = self.texture.tex_coords
        
        Clock.schedule_interval(self.animate, 1.0/60.0)
        self.shake_offset = [0, 0]
        
        # Debug Label
        self._debug_label = Label(
            text="", font_size=12, bold=True,
            color=(1, 0.2, 0.2, 1), outline_width=1, outline_color=(0,0,0,1),
            size_hint=(None, None), size=(100, 20),
            opacity=1 if self.SHOW_DEBUG_STATS else 0
        )
        self.add_widget(self._debug_label)
        
        self.bind(pos=self._update_rect)

    def _init_enemy_visuals(self, etype):
        """โหลด Texture และเตรียม Animation ตามประเภท"""

        if etype == "ranger" or etype == "sniper":
            # [Fix] Ranger row ใน enemy3.png ถ้า 0 อยู่บนสุด
            # ลอง Row 1 หรือ 2 เผื่อเป็นท่าเดินที่ชัดเจนกว่า
            self.anim_frames = get_frames("assets/enemy/enemy3.png", 170, 128, 16, row=1)
            if not self.anim_frames: self.anim_frames = get_frames("assets/enemy/enemy3.png", 170, 128, 16, row=0)
            self.anim_speed = 0.08 # Faster animation for smoother look
        elif etype == "bomber":
            # 🌟 โหลดเฟรมระเบิดแยกไฟล์ Bomb1, 2, ...
            frames = []
            for i in range(1, 9):
                p = resolve_path(f"assets/enemy/bomber/Bomb{i}.png")
                if p:
                    try:
                        frames.append(CoreImage(p).texture)
                    except: pass
            
            if frames:
                self.anim_frames = frames
            else:
                # Fallback
                self.anim_frames = get_frames("assets/enemy/bomber/Bomb_Walk.png", 40, 40, 8)
            self.anim_speed = 0.12
        elif etype == "stalker":
            # 🌟 สุ่มสีน้องหมา (Stalker) และดึงภาพแยก Run1, 2, 3, ... ตามที่ User ต้องการ
            colors = ["Black", "Gray", "White"]
            chosen = random.choice(colors)
            
            frames = []
            for i in range(1, 7):
                p = f"assets/enemy/Canine_{chosen}_Run{i}.png"
                if os.path.exists(p):
                    try:
                        frames.append(CoreImage(p).texture)
                    except: pass
            
            if frames:
                self.anim_frames = frames
            else:
                # Fallback ถ้าหาไฟล์แยกไม่เจอ ให้ใช้ spritesheet เดิม
                self.anim_frames = get_frames(f"assets/enemy/Canine_{chosen}_Run.png", 24, 64, 8)
            
            self.anim_speed = 0.08
        elif etype == "boss" or etype == "big_boss":
            # Minotaur sheet: row 0=attack, row 1=walk, row 2=idle (ตามเดิมที่เดาไว้)
            # แต่ถ้าเป็น top-down indexing: row 0 คือบนสุด
            row_attack = 0
            row_walk = 1
            row_idle = 2
            sheet_path = "assets/enemy/boss/minotaur_288x160_SpriteSheet.png"
            self.boss_idle = get_frames(sheet_path, 288, 160, 16, row=row_idle)
            self.boss_walk = get_frames(sheet_path, 288, 160, 16, row=row_walk)
            self.boss_attack = get_frames(sheet_path, 288, 160, 16, row=row_attack)
            
            def set_boss_anim(state, loop=True):
                if state == "idle": frames = self.boss_idle
                elif state == "walk": frames = self.boss_walk
                elif state == "attack": frames = self.boss_attack
                else: return
                if self.anim_frames != frames:
                    self.anim_frames = frames
                    self.frame_index = 0
            
            self.set_boss_anim = set_boss_anim
            self.anim_frames = self.boss_walk
            self.anim_speed = 0.08
        elif etype == "final_boss" or etype == "final_boss_clone":
            self.anim_frames = get_frames("assets/enemy/boss/minotaur_288x160_SpriteSheet.png", 288, 160, 16, row=1)
            self.anim_speed = 0.06
        else:
            # Normal / Default (enemy1, 2 Alt) - STATIC TEXTURE
            chosen = random.choice(["enemy1.png", "enemy2.png"])
            path = resolve_path(f"assets/enemy/{chosen}")
            if path:
                try:
                    self.texture = CoreImage(path).texture
                    self.anim_frames = [self.texture]
                except:
                    self.anim_frames = []
            else:
                self.anim_frames = []
            self.anim_speed = 999.0 # Don't update

        if self.anim_frames:
            self.texture = self.anim_frames[0]
        else:
            # Fallback
            self.texture = None

    def animate(self, dt):
        """จัดการ Animation และ Flip ทิศทาง (optimized เพื่อกันบัคกะพริบ)"""
        if not self.anim_frames: return
        
        # 1. จัดการ Flip ทิศทาง (หันหน้าหา Player)
        flipped = False
        if hasattr(self, "game") and self.game and self.game.player_pos:
            px = self.game.player_pos[0] + 32
            ex = self.pos[0] + self.enemy_size[0]/2
            
            # สมมติว่าไฟล์ภาพต้นฉบับหันหน้าไปทาง "ซ้าย" (Standard assets)
            # ถ้า Player อยู่ทางขวา (px > ex) เราต้อง Flip ทิศทาง (หันขวา)
            new_facing_right = (px > ex)
            
            if self.is_facing_right != new_facing_right:
                self.is_facing_right = new_facing_right
                flipped = True

        # 2. จัดการเปลี่ยนเฟรม Animation
        frame_changed = False
        if len(self.anim_frames) > 1:
            self.anim_timer += dt
            if self.anim_timer >= self.anim_speed:
                self.anim_timer = 0
                self.frame_index = (self.frame_index + 1) % len(self.anim_frames)
                self.texture = self.anim_frames[self.frame_index]
                self.rect.texture = self.texture
                frame_changed = True

        # 3. อัปเดต UV (หันหน้า)
        if (frame_changed or flipped or not hasattr(self, "_initialized_uv")) and self.texture:
            tc = self.texture.tex_coords
            # ถ้าหันขวา (is_facing_right = True) ให้ใช้พิกัด Flip (เพราะรูปเดิมหันซ้าย)
            if not self.is_facing_right:
                self.rect.tex_coords = tc
            else:
                # Flip Horizontal
                self.rect.tex_coords = (tc[2], tc[3], tc[0], tc[1], tc[6], tc[7], tc[4], tc[5])
            self._initialized_uv = True

    def _update_rect(self, instance, value):
        # 🌟 วาด Texture ให้กึ่งกลาง hitbox ที่เล็กลง
        off_x = (self.enemy_size[0] - self.render_size[0]) / 2
        off_y = (self.enemy_size[1] - self.render_size[1]) / 2
        
        new_pos = (value[0] + off_x + self.shake_offset[0], 
                   value[1] + off_y + self.shake_offset[1])
        self.rect.pos = new_pos
        # Sync debug label (จัดให้อยู่เหนือ hitbox จริง)
        if self._debug_label:
            self._debug_label.pos = (value[0] + self.enemy_size[0]/2 - 50, value[1] + self.enemy_size[1] + 5)
            if self.SHOW_DEBUG_STATS:
                self._debug_label.text = f"HP:{int(self.hp)}  ATK:{int(self.damage)}"
                self._debug_label.opacity = 1
            else:
                self._debug_label.opacity = 0

    def update_movement(self, player_pos, all_enemies, dt: float = 1/60.0):
        """ระบบ AI: แยกตามประเภทศัตรู"""
        px, py = player_pos[0] + 32, player_pos[1] + 32
        ex, ey = (
            self.pos[0] + self.enemy_size[0] / 2,
            self.pos[1] + self.enemy_size[1] / 2,
        )

        dx, dy = px - ex, py - ey
        dist = math.hypot(dx, dy)

        vx, vy = 0, 0

        self.time_counter += dt

        # --- [ Smart Dodge Projectiles ] ---
        # หลบกระสุนผู้เล่น (Dodge Logic) - ปรับให้หลบได้บ้างไม่ได้บ้างตามความฉลาด
        dodge_vx, dodge_vy = 0, 0
        if hasattr(self, "game") and self.game and self.game.player_bullets:
            # กำหนดเกณฑ์การตัดสินใจหลบ (ยิ่งต่ำยิ่งฉลาด/หลบบ่อย)
            # 10 คือไม่หลบเลย, 0 คือหลบทุกนัด
            threshold = 6  # Default: 40% chance
            if self.enemy_type == "stalker": threshold = 5    # 50%
            elif self.enemy_type == "sniper": threshold = 4   # 60%
            elif self.enemy_type == "ranger": threshold = 8   # 20%
            elif self.enemy_type in ["normal", "bomber"]: threshold = 9 # 10%
            elif self.enemy_type == "big_boss": threshold = 7 # 30%
            elif self.enemy_type == "final_boss": threshold = 6 # 40%

            # 🌟 [Optimization] Limit dodge checks to first 10 bullets to save CPU
            bullet_count = 0
            for bullet in self.game.player_bullets:
                bullet_count += 1
                if bullet_count > 10: break
                
                bx, by = bullet.pos
                dist_b = math.hypot(ex - bx, ey - by)
                
                # ระยะที่เริ่มมองเห็นกระสุน (140-180 ตามความฉลาด)
                detect_range = 150 + (10 - threshold) * 5
                
                if dist_b < detect_range:
                    # ใช้ id ผสมกันเพื่อให้ผลลัพธ์ "คงทัด" ต่อกระสุนลูกเดิม (ไม่ส่ายไปมา) 
                    # แต่ "สุ่ม" ว่านัดนี้จะหลบพ้นไหม
                    if (id(self) + id(bullet)) % 10 >= threshold:
                        if hasattr(bullet, 'direction'):
                            bdx, bdy = bullet.direction
                            # เวกเตอร์ตั้งฉาก (Perpendicular)
                            side = 1 if (ex-bx)*(-bdy) + (ey-by)*(bdx) > 0 else -1
                            
                            # ความแรงในการหลบ (ใส่ความ "เหวอ" เล็กน้อย)
                            react_force = 1.2 + (id(self) % 5) * 0.1
                            dodge_vx += (-bdy) * side * self.speed * react_force
                            dodge_vy += (bdx) * side * self.speed * react_force
            
            # จำกัดความเร็วในการหลบไม่ให้พุ่งทะลุจอถ้ากระสุนเยอะ
            max_d = self.speed * 2.0
            mag_d = math.hypot(dodge_vx, dodge_vy)
            if mag_d > max_d:
                dodge_vx = (dodge_vx / mag_d) * max_d
                dodge_vy = (dodge_vy / mag_d) * max_d

        # --- [ AI Logic ] ---
        if self.enemy_type == "ranger":
            # ระยะปลอดภัยของ Ranger (Kiting + Side Strafe)
            if dist > 450:
                vx, vy = (dx / dist) * self.speed, (dy / dist) * self.speed
            elif dist < 250:
                vx, vy = -(dx / dist) * self.speed, -(dy / dist) * self.speed
            
            # เพิ่ม Orbiting movement (เดินวนรอบผู้เล่นเล็กน้อย)
            if dist > 0:
                vx += (-dy / dist) * self.speed * 0.4 * math.sin(self.time_counter * 3)
                vy += (dx / dist) * self.speed * 0.4 * math.sin(self.time_counter * 3)

            self.attack_cooldown -= dt
            if dist < 600 and self.attack_cooldown <= 0:
                self.shoot(player_pos)
                self.attack_cooldown = self.shoot_delay

        elif self.enemy_type == "stalker":
            # Stalker: วิ่งเข้าหาแบบ Fast Orbit (เดินวนพุ่งเข้าหา)
            if dist > 0:
                # 70% พุ่งเข้าหา, 50% วนข้าง
                vx = (dx / dist) * self.speed * 0.8
                vy = (dy / dist) * self.speed * 0.8
                orbit_dir = 1 if id(self) % 2 == 0 else -1
                vx += (-dy / dist) * self.speed * 0.7 * orbit_dir
                vy += (dx / dist) * self.speed * 0.7 * orbit_dir
            
        elif self.enemy_type == "sniper":
            self.sniper_cooldown -= dt
            if self.sniper_cooldown <= 0:
                self.shoot_sniper(player_pos)
                self.sniper_cooldown = 2.0
            # Sniper หลบกระสุนอย่างเดียว
            vx, vy = dodge_vx * 0.3, dodge_vy * 0.3

        elif self.enemy_type == "charger":
            self.charge_timer -= dt
            if self.is_charging:
                self.charge_duration -= dt
                vx, vy = self.charge_dir[0] * self.speed * 4, self.charge_dir[1] * self.speed * 4
                if self.charge_duration <= 0:
                    self.is_charging = False
                    self.color_inst.rgba = (1.0, 0.5, 0.0, 1)
            else:
                if dist > 0:
                    vx, vy = (dx / dist) * self.speed, (dy / dist) * self.speed
                if self.charge_timer <= 0 and dist < 700:
                    self.charge_timer = self.charge_cooldown
                    self.color_inst.rgba = (1.0, 1.0, 0.8, 1)
                    if dist > 0:
                        self.charge_dir = (dx / dist, dy / dist)
                    Clock.schedule_once(lambda dt: self._start_charge_dash(), 1.0)

        elif self.enemy_type == "shielder":
            if not self.has_shield:
                self.speed = 4.5 
                self.color_inst.rgba = (1, 0, 0, 1)
                if dist > 0:
                    # Zigzag แบบดุเดือดขึ้น
                    vx = (dx / dist) * self.speed
                    vy = (dy / dist) * self.speed
                    z_freq = 15.0
                    z_mag = 6.0
                    vx += (-dy / dist) * math.sin(self.time_counter * z_freq) * z_mag
                    vy += (dx / dist) * math.sin(self.time_counter * z_freq) * z_mag
            else:
                if dist > 0:
                    vx, vy = (dx / dist) * self.speed, (dy / dist) * self.speed

        elif self.enemy_type == "bomber":
            if dist > 0:
                vx, vy = (dx / dist) * self.speed, (dy / dist) * self.speed
                # Bomber แอบหลบข้างๆ เล็กน้อย
                vx += (-dy / dist) * self.speed * 0.3 * math.cos(self.time_counter * 5)
                vy += (dx / dist) * self.speed * 0.3 * math.cos(self.time_counter * 5)
            if dist < 45:
                self._explode_bomber()

        else:
            # Normal: วิ่งเข้าหาปกติ แต่มีการส่ายตัว (Wavering)
            if dist > 0:
                vx = (dx / dist) * self.speed
                vy = (dy / dist) * self.speed
                vx += (-dy / dist) * self.speed * 0.2 * math.sin(self.time_counter * 4)
                vy += (dx / dist) * self.speed * 0.2 * math.sin(self.time_counter * 4)

        # รวมแรงหลบกระสุนเข้าไปด้วย (Priority สูง)
        vx += dodge_vx
        vy += dodge_vy
        
        # --- [ Boss Animation State ] ---
        if self.enemy_type in ["boss", "big_boss"] and not getattr(self, "is_boss_attacking", False):
            if abs(vx) > 0.1 or abs(vy) > 0.1:
                self.set_boss_anim("walk")
            else:
                self.set_boss_anim("idle")

        # --- [ Big boss special behavior ] ---
        if self.enemy_type == "big_boss":
            if dist > 0:
                vx, vy = (dx / dist) * self.speed, (dy / dist) * self.speed

            dec = dt
            self.slam_cooldown -= dec
            self.swipe_cooldown -= dec
            self.missile_cooldown -= dec

            if self.slam_cooldown <= 0 and dist < 300:
                self.do_slam()
                self.slam_cooldown = random.uniform(4.0, 6.0)

            if self.swipe_cooldown <= 0:
                self.do_swipe(player_pos)
                self.swipe_cooldown = random.uniform(3.0, 5.0)

            if self.missile_cooldown <= 0:
                self.do_missile(player_pos)
                self.missile_cooldown = random.uniform(4.0, 6.0)

        # --- [ Final Boss Logic ] ---
        if self.enemy_type == "final_boss":
            self.final_attack_timer -= dt
            
            if self.final_phase == 1 and self.hp < self.max_hp * 0.5:
                self.final_phase = 2
                self.speed = 5.0
                self.color_inst.rgba = (0.8, 0.0, 0.2, 1)
                self.final_attack_timer = 3.0

            if not self.final_is_acting:
                if dist > 0:
                    vx, vy = (dx / dist) * self.speed, (dy / dist) * self.speed

            if self.final_attack_timer <= 0:
                if self.final_phase == 1:
                    if self.final_attack_index == 0:
                        self.do_final_spiral()
                        self.final_attack_timer = 6.0
                    elif self.final_attack_index == 1:
                        self.do_final_beam()
                        self.final_attack_timer = 6.0
                    else:
                        self.do_final_clones()
                        self.final_attack_timer = 8.0
                    
                    self.final_attack_index = (self.final_attack_index + 1) % 3
                else:
                    if self.lethal_cooldown <= 0:
                        self.do_final_lethal_homing()
                        self.lethal_cooldown = 30.0
                    
                    if self.final_attack_index == 0:
                        self.do_final_spiral()
                        self.final_attack_timer = 7.0 
                    elif self.final_attack_index == 1:
                        self.do_final_dash(player_pos)
                    elif self.final_attack_index == 2:
                        self.do_final_spikes()
                        self.final_attack_timer = 5.0
                    elif self.final_attack_index == 3:
                        self.do_final_beam()
                        self.final_attack_timer = 7.0 
                    else:
                        self.do_final_slam(player_pos)
                    
                    self.final_attack_index = (self.final_attack_index + 1) % 5
            
            self.lethal_cooldown -= dt

        # --- [ Separation (ไม่ให้ทับกัน) ] ---
        # 🌟 [Optimization] Skip separation if enemy is far away or too many enemies
        sep_x, sep_y = 0, 0
        if dist < 1000: # Only separate if somewhat near player
            check_count = 0
            for other in all_enemies:
                if other is self:
                    continue
                check_count += 1
                if check_count > 50: break # Only check first 50 neighbors to save CPU
                
                ox, oy = (
                    other.pos[0] + other.enemy_size[0] / 2,
                    other.pos[1] + other.enemy_size[1] / 2,
                )
                d_other = math.hypot(ex - ox, ey - oy)
                if d_other < 45:
                    sep_x += (ex - ox) * 0.15
                    sep_y += (ey - oy) * 0.15

        ew, eh = self.enemy_size
        new_x = max(0, min(self.pos[0] + vx + sep_x, 5000 - ew))
        new_y = max(0, min(self.pos[1] + vy + sep_y, 5000 - eh))
        
        can_move_x = True
        can_move_y = True
        
        # ถอยเข้าหากำแพงหรือไม่ตอนกั้นอยู่
        if hasattr(self, "game") and getattr(self.game, "obstacles", []):
            for obs in self.game.obstacles:
                if obs.collides_with(new_x, self.pos[1], ew, eh): can_move_x = False
                if obs.collides_with(self.pos[0], new_y, ew, eh): can_move_y = False
                
        if can_move_x: self.pos = (new_x, self.pos[1])
        if can_move_y: self.pos = (self.pos[0], new_y)

    # --- Big boss attacks helpers ---
    def do_slam(self):
        """Ground slam: warns with red circle, then deals damage after delay"""
        if not hasattr(self, "game"):
            return
        ex = self.pos[0] + self.enemy_size[0] / 2
        ey = self.pos[1] + self.enemy_size[1] / 2
        slam_radius = 250
        
        # Show warning highlight first (yellow/orange)
        self._show_slam_warning(ex, ey, slam_radius)
        
        # Animation
        if hasattr(self, "set_boss_anim"):
            self.is_boss_attacking = True
            self.set_boss_anim("attack")
            Clock.schedule_once(lambda dt: setattr(self, "is_boss_attacking", False), 1.0)

        # Delay the actual damage and projectiles by 0.4 seconds
        Clock.schedule_once(
            lambda dt: self._execute_slam_damage(ex, ey, slam_radius),
            0.4
        )

    def _show_slam_warning(self, cx, cy, radius):
        """Show yellow/orange warning circle before slam hits"""
        if not hasattr(self, "game") or not self.game or not self.parent:
            return
        
        effect_widget = Widget(size_hint=(None, None), size=(radius * 2, radius * 2))
        effect_widget.pos = (cx - radius, cy - radius)
        
        with effect_widget.canvas:
            Color(1, 1, 0, 0.5)  # Yellow warning with transparency
            Ellipse(pos=effect_widget.pos, size=effect_widget.size)
        
        self.game.world_layout.add_widget(effect_widget)
        Clock.schedule_once(lambda dt: self._remove_effect_widget(effect_widget), 0.4)

    def _execute_slam_damage(self, cx, cy, slam_radius):
        """Actually deal damage and show red impact circle"""
        if not hasattr(self, "game") or not self.game or not self.parent:
            return
        
        # Direct melee damage to player if they're in slam radius
        player_pos = self.game.player_pos
        px, py = player_pos[0] + 32, player_pos[1] + 32
        dist_to_player = math.hypot(cx - px, cy - py)
        
        if dist_to_player < slam_radius:
            # Direct damage to player from the slam
            self.game.take_damage(self.damage * 1.5)
        
        # Show red damage impact circle
        self._show_slam_impact(cx, cy, slam_radius)
        
        # Create radial projectiles for visual effect and additional coverage
        for i in range(12):
            angle = 2 * math.pi * i / 12
            tx = cx + math.cos(angle) * 500
            ty = cy + math.sin(angle) * 500
            proj = EnemyProjectile(start_pos=(cx, cy), target_pos=(tx, ty), damage=self.damage)
            proj.speed = 250
            self.game.world_layout.add_widget(proj)
            self.game.enemy_projectiles.append(proj)

    def _show_slam_impact(self, cx, cy, radius):
        """Show red impact circle after damage is dealt"""
        if not hasattr(self, "game") or not self.game or not self.parent:
            return
        
        effect_widget = Widget(size_hint=(None, None), size=(radius * 2, radius * 2))
        effect_widget.pos = (cx - radius, cy - radius)
        
        with effect_widget.canvas:
            Color(1, 0, 0, 0.6)  # Red impact with transparency
            Ellipse(pos=effect_widget.pos, size=effect_widget.size)
        
        self.game.world_layout.add_widget(effect_widget)
        Clock.schedule_once(lambda dt: self._remove_effect_widget(effect_widget), 0.25)

    def do_swipe(self, player_pos):
        if not hasattr(self, "game") or not self.game or not self.parent:
            return
        ex = self.pos[0] + self.enemy_size[0] / 2
        ey = self.pos[1] + self.enemy_size[1] / 2
        
        # 🌟 สร้างกระสุน Swipe พุ่งหาผู้เล่นอย่างรวดเร็ว
        proj = EnemyProjectile(start_pos=(ex, ey), target_pos=(player_pos[0] + 32, player_pos[1] + 32), damage=self.damage * 1.2)
        proj.speed = 700
        self.game.world_layout.add_widget(proj)
        self.game.enemy_projectiles.append(proj)
        
        if hasattr(self, "set_boss_anim"):
            self.is_boss_attacking = True
            self.set_boss_anim("attack")
            Clock.schedule_once(lambda dt: setattr(self, "is_boss_attacking", False), 0.6)

    def do_missile(self, player_pos):
        if not hasattr(self, "game") or not self.game or not self.parent:
            return
        ex = self.pos[0] + self.enemy_size[0] / 2
        ey = self.pos[1] + self.enemy_size[1] / 2
        proj = EnemyProjectile(start_pos=(ex, ey), target_pos=(player_pos[0] + 32, player_pos[1] + 32), damage=self.damage * 0.8)
        proj.speed = 300
        self.game.world_layout.add_widget(proj)
        self.game.enemy_projectiles.append(proj)
        
        if hasattr(self, "set_boss_anim"):
            self.is_boss_attacking = True
            self.set_boss_anim("attack")
            Clock.schedule_once(lambda dt: setattr(self, "is_boss_attacking", False), 0.6)

    def _remove_effect_widget(self, widget):
        """Remove effect widget from parent"""
        if widget.parent:
            widget.parent.remove_widget(widget)

    def shoot(self, player_pos):
        if not self.parent:
            return

        # ตำแหน่งจุดเริ่มกระสุน (กึ่งกลางตัว Ranger)
        ex = self.pos[0] + self.enemy_size[0] / 2
        ey = self.pos[1] + self.enemy_size[1] / 2

        # หาจุดกึ่งกลางของผู้เล่นเพื่อใช้เป็นเป้าหมายกระสุน
        target_x = player_pos[0] + 32
        target_y = player_pos[1] + 32

        # ใช้ EnemyProjectile จากไฟล์ projectile_widget (เคลื่อนที่ด้วย dt)
        proj = EnemyProjectile(
            start_pos=(ex, ey), target_pos=(target_x, target_y), damage=self.damage
        )

        if hasattr(self, "game") and self.game is not None:
            self.game.world_layout.add_widget(proj)
            self.game.enemy_projectiles.append(proj)

    def take_damage(self, amount, knockback_dir=(0, 0)):
        """รับดาเมจและแสดงเอฟเฟกต์กระพริบม่วงชั่วขณะ พร้อมเขย่าตัว"""
        self._apply_hit_shake()
        
        # 🔵 Shielder damage reduction
        if getattr(self, "enemy_type", "") == "shielder" and getattr(self, "has_shield", False):
            amount *= 0.40  # รับดาเมจแค่ 40%
            if self.hp - amount <= self.max_hp * 0.5: # เลือดเหลือ < 50% โล่แตกและคลั่ง
                self.has_shield = False

        self.hp -= amount
        
        # Check death for Final Boss Self-Destruct
        if self.hp <= 0 and self.enemy_type == "final_boss":
            from game.projectile_widget import FinalBossExplosion
            cx, cy = self.pos[0]+self.enemy_size[0]/2, self.pos[1]+self.enemy_size[1]/2
            exp = FinalBossExplosion(pos=(cx, cy), radius=1200, fuse=10.0, game=self.game)
            if self.game:
                self.game.world_layout.add_widget(exp)

        # เอฟเฟกต์กระพริบม่วง (capture orig_color ด้วย default arg เพื่อป้องกัน closure bug)
        orig_color = tuple(self.color_inst.rgba)
        if getattr(self, "enemy_type", "") == "shielder" and not getattr(self, "has_shield", False):
            orig_color = (1, 0, 0, 1) # Red enrage
        elif getattr(self, "enemy_type", "") == "charger" and getattr(self, "is_charging", False):
            orig_color = (1.0, 1.0, 0.8, 1) # White charging
            
        self.color_inst.rgba = (1, 0, 1, 1)  # ม่วง
        Clock.schedule_once(
            lambda dt, c=orig_color: setattr(self.color_inst, "rgba", c), 0.1
        )

        # แรงสะท้อน (Knockback) (ชาร์จเจอร์ตอนพุ่งจะไม่ถอย)
        if (knockback_dir[0] != 0 or knockback_dir[1] != 0) and not getattr(self, "is_charging", False):
            kb = 25
            self.pos = (
                self.pos[0] + knockback_dir[0] * kb,
                self.pos[1] + knockback_dir[1] * kb,
            )

    def _apply_hit_shake(self, count=0):
        """เขย่าตัวศัตรูเมื่อโดนดาเมจ"""
        if count >= 4 or self.hp <= 0:
            self.shake_offset = [0, 0]
            # Reset เป็นตำแหน่งกึ่งกลาง hitbox
            off_x = (self.enemy_size[0] - self.render_size[0]) / 2
            off_y = (self.enemy_size[1] - self.render_size[1]) / 2
            self.rect.pos = (self.pos[0] + off_x, self.pos[1] + off_y)
            return

        mag = self.enemy_size[0] * 0.12
        self.shake_offset = [random.uniform(-mag, mag), random.uniform(-mag, mag)]
        
        off_x = (self.enemy_size[0] - self.render_size[0]) / 2
        off_y = (self.enemy_size[1] - self.render_size[1]) / 2
        self.rect.pos = (self.pos[0] + off_x + self.shake_offset[0], self.pos[1] + off_y + self.shake_offset[1])

        Clock.schedule_once(lambda dt: self._apply_hit_shake(count + 1), 0.04)

    # --- Mini boss abilities helpers ---
    def _start_charge_dash(self):
        self.is_charging = True
        self.charge_duration = 1.0  # พุ่งน้าน 1 วินาที

    def _explode_bomber(self):
        if not hasattr(self, "game") or not self.parent:
            return
        # ทำดาเมจตัวเองให้ตาย (hp=0) ทันที
        self.hp = 0
        px = self.pos[0] + self.enemy_size[0] / 2
        py = self.pos[1] + self.enemy_size[1] / 2
        
        from game.skills import _show_aoe_vfx
        _show_aoe_vfx(self.game, px, py, 180)
        
        player_x = self.game.player_pos[0] + 32
        player_y = self.game.player_pos[1] + 32
        dist = math.hypot(player_x - px, player_y - py)
        if dist <= 180:
            self.game.take_damage(self.damage)
            
        # remove self
        if self in self.game.enemies:
            self.game.enemies.remove(self)
        if self.parent:
            self.parent.remove_widget(self)

    def shoot_sniper(self, player_pos):
        if not self.parent:
            return
        ex = self.pos[0] + self.enemy_size[0] / 2
        ey = self.pos[1] + self.enemy_size[1] / 2
        
        target_x = player_pos[0] + 32
        target_y = player_pos[1] + 32
        dx, dy = target_x - ex, target_y - ey
        dist = max(1, math.hypot(dx, dy))
        
        base_angle = math.atan2(dy, dx)
        spread_deg = math.radians(5) # Tightly (5 degrees offset)
        
        for offset in [-spread_deg, 0, spread_deg]:
            ang = base_angle + offset
            tx = ex + math.cos(ang) * 900
            ty = ey + math.sin(ang) * 900
            
            proj = EnemyProjectile(
                start_pos=(ex, ey), target_pos=(tx, ty), damage=self.damage
            )
            proj.speed = 550
            if hasattr(self, "game") and self.game is not None:
                self.game.world_layout.add_widget(proj)
                self.game.enemy_projectiles.append(proj)

    # --- Final Boss Specials Implementation ---

    def do_final_spiral(self):
        self.final_is_acting = True
        origins = [(self.pos[0] + self.enemy_size[0]/2, self.pos[1] + self.enemy_size[1]/2)]
        # Also clean up dead clones
        self.final_clones = [c for c in self.final_clones if c.parent and c.hp > 0]
        for clone in self.final_clones:
            origins.append((clone.pos[0] + clone.enemy_size[0]/2, clone.pos[1] + clone.enemy_size[1]/2))
            
        from game.projectile_widget import BossSpiralMissile
        
        def _spiral(dt, step=0):
            if step >= 40:
                self.final_is_acting = False
                return
            pulse_angle = step * 0.25
            for ox, oy in origins:
                for i in range(4):
                    angle = pulse_angle + (i * math.pi / 2)
                    m = BossSpiralMissile(start_pos=(ox, oy), angle=angle, speed=280, damage=35)
                    if self.game:
                        self.game.enemy_projectiles.append(m)
                        self.game.world_layout.add_widget(m)
            Clock.schedule_once(lambda d: _spiral(d, step+1), 0.1)
        
        _spiral(0)

    def do_final_beam(self):
        self.final_is_acting = True
        origins = [(self.pos[0] + self.enemy_size[0]/2, self.pos[1] + self.enemy_size[1]/2)]
        self.final_clones = [c for c in self.final_clones if c.parent and c.hp > 0]
        for clone in self.final_clones:
            origins.append((clone.pos[0] + clone.enemy_size[0]/2, clone.pos[1] + clone.enemy_size[1]/2))
            
        from game.projectile_widget import BossBeamHighlight
        
        start_angle = random.uniform(0, math.pi * 2)
        rot_speed = random.choice([-20, 20, -40, 40])
        highlights = []
        
        for ox, oy in origins:
            for i in range(8):
                a = start_angle + (i * math.pi / 4)
                h = BossBeamHighlight(pos=(ox, oy), angle=a, duration=2.5, rotation_speed=rot_speed)
                if self.game: self.game.world_layout.add_widget(h)
                highlights.append(h)

        def _rotate_highlights(dt, elapsed=0):
            if elapsed >= 2.0: return
            for h in highlights:
                if h.parent: h.update_rotation(dt)
            Clock.schedule_once(lambda d: _rotate_highlights(d, elapsed+dt), 0.016)
        
        _rotate_highlights(0.016)
            
        def _fire(dt):
            self.final_is_acting = False
            if not self.game: return
            px, py = self.game.player_pos[0]+32, self.game.player_pos[1]+32
            final_rot = rot_speed * 2.0
            from game.skills import _show_cone_vfx
            
            for ox, oy in origins:
                for i in range(8):
                    fa = start_angle + (i * math.pi / 4) + math.radians(final_rot)
                    p_angle = math.atan2(py-oy, px-ox)
                    diff = abs((p_angle - fa + math.pi) % (2*math.pi) - math.pi)
                    if diff < 0.08 and math.hypot(px-ox, py-oy) < 2000:
                        self.game.take_damage(50)
                    _show_cone_vfx(self.game, ox, oy, 2000, math.degrees(fa), 6, None)

        Clock.schedule_once(_fire, 2.0)

    def do_final_dash(self, player_pos):
        self.final_is_acting = True
        self.final_dash_count = 0
        
        def _prep_dash(dt):
            if self.final_dash_count >= 2: # Reduce to 2 for better pattern flow
                self.final_is_acting = False
                self.final_attack_timer = 3.0
                return
                
            # Highlight 3s
            self.color_inst.rgba = (1, 1, 1, 1) # Flash white warning
            px, py = self.game.player_pos[0]+32, self.game.player_pos[1]+32
            cx, cy = self.pos[0]+self.enemy_size[0]/2, self.pos[1]+self.enemy_size[1]/2
            dist = math.hypot(px-cx, py-cy)
            if dist > 0:
                self.charge_dir = ((px-cx)/dist, (py-cy)/dist)
            
            Clock.schedule_once(_execute_dash, 3.0)

        def _execute_dash(dt):
            # Rapid dash (teleport-like movement for speed 5 enemy)
            self.speed = 15.0
            self.is_charging = True
            def _stop_dash(d):
                self.is_charging = False
                self.speed = 5.0
                self.final_dash_count += 1
                _prep_dash(0)
            Clock.schedule_once(_stop_dash, 0.5)

        _prep_dash(0)

    def do_final_clones(self):
        """Phase 1: Spawn 2 clones that copy attacks"""
        if not self.game: return
        self.final_is_acting = True
        
        # Clean up old clones
        for c in self.final_clones:
            if c.parent: c.parent.remove_widget(c)
            if c in self.game.enemies: self.game.enemies.remove(c)
        self.final_clones = []
        
        for _ in range(2):
            # Spawn at random points around boss
            dist = random.uniform(300, 500)
            ang = random.uniform(0, 2*math.pi)
            sx = self.pos[0] + math.cos(ang)*dist
            sy = self.pos[1] + math.sin(ang)*dist
            clone = EnemyWidget(spawn_pos=(sx, sy), enemy_type="final_boss_clone")
            clone.game = self.game
            self.game.enemies.append(clone)
            self.game.world_layout.add_widget(clone)
            self.final_clones.append(clone)
            
        # Visual effect
        from game.skills import _show_aoe_vfx
        _show_aoe_vfx(self.game, self.pos[0]+90, self.pos[1]+90, 250)
        
        def _done(dt): self.final_is_acting = False
        Clock.schedule_once(_done, 2.0)

    def do_final_lethal_homing(self):
        """Phase 2: Fire a homing missile that deals 50% max HP damage"""
        if not self.game: return
        cx, cy = self.pos[0] + self.enemy_size[0]/2, self.pos[1] + self.enemy_size[1]/2
        from game.projectile_widget import LethalHomingMissile
        m = LethalHomingMissile(start_pos=(cx, cy), game=self.game)
        self.game.enemy_projectiles.append(m)
        self.game.world_layout.add_widget(m)

    def do_final_spikes(self):
        """Phase 2: Spawn random spikes around boss"""
        if not self.game: return
        self.final_is_acting = True
        
        cx, cy = self.pos[0] + self.enemy_size[0]/2, self.pos[1] + self.enemy_size[1]/2
        from game.projectile_widget import BossSpike
        
        def _spawn_spike_wave(dt, wave_num=0):
            if wave_num >= 3:
                self.final_is_acting = False
                return
            
            # Spawn 10 spikes in a circle
            count = 10 + wave_num * 5
            radius = 200 + wave_num * 180
            for i in range(count):
                angle = (i * 2 * math.pi / count) + random.uniform(-0.2, 0.2)
                sx = cx + math.cos(angle) * radius
                sy = cy + math.sin(angle) * radius
                s = BossSpike(pos=(sx, sy), game=self.game, warning_duration=1.2)
                self.game.world_layout.add_widget(s)
                
            Clock.schedule_once(lambda d: _spawn_spike_wave(d, wave_num+1), 0.8)
            
        _spawn_spike_wave(0)

    def do_final_slam(self, player_pos):
        self.final_is_acting = True
        target_pos = (self.game.player_pos[0]+32, self.game.player_pos[1]+32)
        from game.projectile_widget import BossJumpHighlight
        h = BossJumpHighlight(pos=target_pos, radius=400, duration=5.0)
        if self.game: self.game.world_layout.add_widget(h)
        
        # Invis/Jump effect
        self.opacity = 0.3
        
        def _execute_slam(dt):
            self.pos = (target_pos[0] - self.enemy_size[0]/2, target_pos[1] - self.enemy_size[1]/2)
            self.opacity = 1.0
            self.final_is_acting = False
            self.final_attack_timer = 3.0
            
            if self.game:
                px, py = self.game.player_pos[0]+32, self.game.player_pos[1]+32
                if math.hypot(px-target_pos[0], py-target_pos[1]) < 400:
                    self.game.take_damage(70)
                from game.skills import _show_aoe_vfx
                _show_aoe_vfx(self.game, target_pos[0], target_pos[1], 400)

        Clock.schedule_once(_execute_slam, 5.0)