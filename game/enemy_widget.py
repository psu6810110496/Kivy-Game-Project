from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
import math
from game.projectile_widget import EnemyProjectile

# --- [ Class สำหรับตัวศัตรู ] ---
class EnemyWidget(Widget):
    def __init__(self, spawn_pos=(0, 0), enemy_type="normal", **kwargs):
        super().__init__(**kwargs)
        self.pos = spawn_pos
        self.enemy_type = enemy_type
        
        # ระบบโจมตี (สำหรับ Ranger)
        self.attack_cooldown = 0
        self.shoot_delay = 2.0  # ยิงทุกๆ 2 วินาที
        
        # --- [ Enemy Stats ] ---
        stats = {
            "normal":  {"hp": 30,  "speed": 2.2, "damage": 10, "color": (1, 1, 1, 1), "size": (40, 40)},
            "stalker": {"hp": 15,  "speed": 3.8, "damage": 5,  "color": (0.8, 0.2, 1, 1), "size": (30, 30)},
            "ranger":  {"hp": 25,  "speed": 1.8, "damage": 15, "color": (0.2, 0.9, 0.3, 1), "size": (45, 45)},
            # Boss: ศัตรูตัวใหญ่ HP เยอะ เดินช้าแต่ตีแรง
            "boss":    {"hp": 400, "speed": 1.2, "damage": 30, "color": (0.9, 0.2, 0.2, 1), "size": (96, 96)},
        }
        
        current_stats = stats.get(enemy_type, stats["normal"])
        self.hp = current_stats["hp"]
        self.max_hp = self.hp
        self.speed = current_stats["speed"]
        self.damage = current_stats["damage"]
        self.enemy_size = current_stats["size"]

        with self.canvas:
            self.color_inst = Color(*current_stats["color"])
            self.rect = Rectangle(pos=self.pos, size=self.enemy_size)

        self.bind(pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.pos = value

    def update_movement(self, player_pos, all_enemies):
        """ ระบบ AI: แยกตามประเภทศัตรู """
        px, py = player_pos[0] + 32, player_pos[1] + 32
        ex, ey = self.pos[0] + self.enemy_size[0]/2, self.pos[1] + self.enemy_size[1]/2
        
        dx, dy = px - ex, py - ey
        dist = math.hypot(dx, dy)
        
        vx, vy = 0, 0

        # --- [ AI Logic ] ---
        if self.enemy_type == "ranger":
            # ระยะปลอดภัยของ Ranger (Kiting)
            if dist > 450: # ไกลไปให้เดินเข้าหา
                vx, vy = (dx / dist) * self.speed, (dy / dist) * self.speed
            elif dist < 250: # ใกล้ไปให้เดินหนี (ถอยหลังยิง)
                vx, vy = -(dx / dist) * self.speed, -(dy / dist) * self.speed
            
            # ระบบยิง
            self.attack_cooldown -= 1/60.0
            if dist < 600 and self.attack_cooldown <= 0:
                self.shoot(player_pos)
                self.attack_cooldown = self.shoot_delay
        else:
            # Normal & Stalker: วิ่งเข้าหาตรงๆ
            if dist > 0:
                vx, vy = (dx / dist) * self.speed, (dy / dist) * self.speed

        # --- [ Separation (ไม่ให้ทับกัน) ] ---
        sep_x, sep_y = 0, 0
        for other in all_enemies:
            if other is self: continue
            ox, oy = other.pos[0] + other.enemy_size[0]/2, other.pos[1] + other.enemy_size[1]/2
            d_other = math.hypot(ex - ox, ey - oy)
            if d_other < 45:
                sep_x += (ex - ox) * 0.15
                sep_y += (ey - oy) * 0.15

        self.pos = (self.pos[0] + vx + sep_x, 
                    self.pos[1] + vy + sep_y)

    def shoot(self, player_pos):
        if not self.parent: return
        
        ex, ey = self.pos[0] + self.enemy_size[0]/2, self.pos[1] + self.enemy_size[1]/2
        
        # หาจุดกึ่งกลางของผู้เล่นเพื่อใช้เป็นเป้าหมายกระสุน
        target_x = player_pos[0] + 32
        target_y = player_pos[1] + 32

        # ใช้ EnemyProjectile จากไฟล์ projectile_widget (เคลื่อนที่ด้วย dt)
        proj = EnemyProjectile(start_pos=(ex, ey), target_pos=(target_x, target_y), damage=self.damage)
        
        self.parent.add_widget(proj)
        
        # ส่งเข้า list ใน GameScreen เพื่อเช็ค Collision
        # เดินไต่ parent ขึ้นไปหาวัตถุที่มี attribute enemy_projectiles (คือ GameScreen)
        game_screen = self.parent
        while game_screen is not None and not hasattr(game_screen, "enemy_projectiles"):
            game_screen = game_screen.parent
        if game_screen is not None:
            game_screen.enemy_projectiles.append(proj)

    def take_damage(self, amount, knockback_dir=(0,0)):
        """ รับดาเมจและแสดงเอฟเฟกต์กระพริบแดง """
        self.hp -= amount
        
        # เอฟเฟกต์กระพริบแดง
        orig_color = self.color_inst.rgba
        self.color_inst.rgba = (1, 0, 0, 1)
        Clock.schedule_once(lambda dt: setattr(self.color_inst, 'rgba', orig_color), 0.1)
        
        # แรงสะท้อน (Knockback)
        kb = 25
        self.pos = (self.pos[0] + knockback_dir[0] * kb,
                    self.pos[1] + knockback_dir[1] * kb)