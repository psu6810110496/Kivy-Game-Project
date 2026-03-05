from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
import math
import random
from game.projectile_widget import EnemyProjectile


# --- [ Class สำหรับตัวศัตรู ] ---
class EnemyWidget(Widget):
    # โหลด texture ของศัตรูแต่ละประเภท (ใช้ร่วมกันทุก instance)
    # bosses may be updated by placing a file named boss.png in assets/enemy
    import os

    boss_path = "assets/enemy/boss.png"
    if not os.path.exists(boss_path):
        boss_path = "assets/enemy/enemy4.png"

    ENEMY_TEXTURES = {
        "normal": CoreImage("assets/enemy/enemy1.png").texture,
        "stalker": CoreImage("assets/enemy/enemy2.png").texture,
        "ranger": CoreImage("assets/enemy/enemy3.png").texture,
        "boss": CoreImage(boss_path).texture,
        "big_boss": CoreImage(boss_path).texture,
        "charger": CoreImage("assets/enemy/enemy2.png").texture,  # Fallback texture
        "shielder": CoreImage("assets/enemy/enemy1.png").texture,
        "bomber": CoreImage("assets/enemy/enemy2.png").texture,
        "sniper": CoreImage("assets/enemy/enemy3.png").texture,
    }

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


        # --- [ Enemy Stats ] ---
        stats = {
            "normal": {
                "hp": 50,
                "speed": 2.2,
                "damage": 8,
                "color": (1, 1, 1, 1),
                "size": (40, 40),
            },
            "stalker": {
                "hp": 40,
                "speed": 3.8,
                "damage": 5,
                "color": (0.8, 0.2, 1, 1),
                "size": (30, 30),
            },
            "ranger": {
                "hp": 40,
                "speed": 1.8,
                "damage": 12,
                "color": (0.2, 0.9, 0.3, 1),
                "size": (45, 45),
            },
            "charger": {
                "hp": 120,
                "speed": 1.5,
                "damage": 25,
                "color": (1.0, 0.5, 0.0, 1), # 🟠 ส้ม
                "size": (55, 55),
            },
            "shielder": {
                "hp": 300,
                "speed": 1.0,
                "damage": 15,
                "color": (0.2, 0.5, 1.0, 1), # 🔵 ฟ้า
                "size": (65, 65),
            },
            "bomber": {
                "hp": 80,
                "speed": 2.5,
                "damage": 60, # ระเบิดแรง
                "color": (1.0, 1.0, 0.2, 1), # 🟡 เหลือง
                "size": (50, 50),
            },
            "sniper": {
                "hp": 60,
                "speed": 0.5, # แทบไม่เดิน
                "damage": 15,
                "color": (0.4, 0.8, 0.9, 1), # 🩵 ฟ้าอ่อน
                "size": (45, 45),
            },
            # Boss: ศัตรูตัวใหญ่ HP เยอะ เดินช้าแต่ตีแรง
            "boss": {
                "hp": 600,
                "speed": 1.2,
                "damage": 40,
                "color": (0.9, 0.2, 0.2, 1),
                "size": (96, 96),
            },
            # Big boss type with additional special attacks
            "big_boss": {
                "hp": 2000,
                "speed": 1.0,
                "damage": 55,
                "color": (0.5, 0.1, 0.7, 1),
                "size": (128, 128),
            },
        }

        current_stats = stats.get(enemy_type, stats["normal"])
        self.hp = current_stats["hp"]
        self.max_hp = self.hp
        self.speed = current_stats["speed"]
        self.damage = current_stats["damage"]
        self.enemy_size = current_stats["size"]

        # เลือก texture ตามประเภทศัตรู (ถ้าไม่เจอใช้ normal แทน)
        self.texture = self.ENEMY_TEXTURES.get(
            enemy_type, self.ENEMY_TEXTURES["normal"]
        )

        with self.canvas:
            # ใช้สีขาวเพื่อไม่ให้กลบสีจาก texture และเอาไว้เปลี่ยนสีตอนโดนตี
            self.color_inst = Color(*current_stats["color"])
            self.rect = Rectangle(
                pos=self.pos, size=self.enemy_size, texture=self.texture
            )

        self.bind(pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.pos = value

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

        # --- [ AI Logic ] ---
        if self.enemy_type == "ranger":
            # ระยะปลอดภัยของ Ranger (Kiting)
            if dist > 450:  # ไกลไปให้เดินเข้าหา
                vx, vy = (dx / dist) * self.speed, (dy / dist) * self.speed
            elif dist < 250:  # ใกล้ไปให้เดินหนี (ถอยหลังยิง)
                vx, vy = -(dx / dist) * self.speed, -(dy / dist) * self.speed

            self.attack_cooldown -= 1 / 60.0
            if dist < 600 and self.attack_cooldown <= 0:
                self.shoot(player_pos)
                self.attack_cooldown = self.shoot_delay

        elif self.enemy_type == "sniper":
            self.sniper_cooldown -= 1 / 60.0
            if self.sniper_cooldown <= 0:
                self.shoot_sniper(player_pos)
                self.sniper_cooldown = 2.0
            # Sniper แทบไม่เดิน (speed = 0.5)

        elif self.enemy_type == "charger":
            self.charge_timer -= 1 / 60.0
            if self.is_charging:
                self.charge_duration -= 1 / 60.0
                vx, vy = self.charge_dir[0] * self.speed * 4, self.charge_dir[1] * self.speed * 4
                if self.charge_duration <= 0:
                    self.is_charging = False
                    self.color_inst.rgba = (1.0, 0.5, 0.0, 1) # กลับมาสีส้มปกติ
            else:
                if dist > 0:
                    vx, vy = (dx / dist) * self.speed, (dy / dist) * self.speed
                if self.charge_timer <= 0 and dist < 700:
                    self.charge_timer = self.charge_cooldown
                    # ไฮไลต์เหลือง/ขาวก่อนพุ่ง
                    self.color_inst.rgba = (1.0, 1.0, 0.8, 1)
                    # เก็บ vector ไปหาผู้เล่นไว้พุ่งตรงๆ
                    if dist > 0:
                        self.charge_dir = (dx / dist, dy / dist)
                    # ร่ายชาร์จ 1 วิ ก่อนพุ่ง
                    Clock.schedule_once(lambda dt: self._start_charge_dash(), 1.0)

        elif self.enemy_type == "shielder":
            if not self.has_shield:
                self.speed = 3.0 # Enrage (เดินเร็วขึ้น)
                self.color_inst.rgba = (1, 0, 0, 1) # กลายเป็นสีแดง
            if dist > 0:
                vx, vy = (dx / dist) * self.speed, (dy / dist) * self.speed

        elif self.enemy_type == "bomber":
            if dist > 0:
                vx, vy = (dx / dist) * self.speed, (dy / dist) * self.speed
            if dist < 45:
                # ระเบิดทันทีหากโดนตัวผู้เล่น
                self._explode_bomber()

        else:
            # Normal & Stalker: วิ่งเข้าหาตรงๆ
            if dist > 0:
                vx, vy = (dx / dist) * self.speed, (dy / dist) * self.speed

        # --- [ Big boss special behavior ] ---
        if self.enemy_type == "big_boss":
            # always move toward player
            if dist > 0:
                vx, vy = (dx / dist) * self.speed, (dy / dist) * self.speed

            # decrement cooldowns (approximate dt=1/60)
            dec = 1.0 / 60.0
            self.slam_cooldown -= dec
            self.swipe_cooldown -= dec
            self.missile_cooldown -= dec

            # slam when close
            if self.slam_cooldown <= 0 and dist < 300:
                self.do_slam()
                self.slam_cooldown = random.uniform(4.0, 6.0)

            # swipe attack periodically
            if self.swipe_cooldown <= 0:
                self.do_swipe(player_pos)
                self.swipe_cooldown = random.uniform(3.0, 5.0)

            # missile barrage periodically
            if self.missile_cooldown <= 0:
                self.do_missile(player_pos)
                self.missile_cooldown = random.uniform(4.0, 6.0)

        # --- [ Separation (ไม่ให้ทับกัน) ] ---
        sep_x, sep_y = 0, 0
        for other in all_enemies:
            if other is self:
                continue
            ox, oy = (
                other.pos[0] + other.enemy_size[0] / 2,
                other.pos[1] + other.enemy_size[1] / 2,
            )
            d_other = math.hypot(ex - ox, ey - oy)
            if d_other < 45:
                sep_x += (ex - ox) * 0.15
                sep_y += (ey - oy) * 0.15

        self.pos = (self.pos[0] + vx + sep_x, self.pos[1] + vy + sep_y)

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
        
        # Delay the actual damage and projectiles by 0.4 seconds
        Clock.schedule_once(
            lambda dt: self._execute_slam_damage(ex, ey, slam_radius),
            0.4
        )

    def _show_slam_warning(self, cx, cy, radius):
        """Show yellow/orange warning circle before slam hits"""
        if not hasattr(self, "game") or not self.parent:
            return
        
        effect_widget = Widget(size_hint=(None, None), size=(radius * 2, radius * 2))
        effect_widget.pos = (cx - radius, cy - radius)
        
        with effect_widget.canvas:
            Color(1, 1, 0, 0.5)  # Yellow warning with transparency
            Ellipse(pos=effect_widget.pos, size=effect_widget.size)
        
        self.parent.add_widget(effect_widget)
        Clock.schedule_once(lambda dt: self._remove_effect_widget(effect_widget), 0.4)

    def _execute_slam_damage(self, cx, cy, slam_radius):
        """Actually deal damage and show red impact circle"""
        if not hasattr(self, "game"):
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
            self.parent.add_widget(proj)
            game_screen = self.parent
            while game_screen and not hasattr(game_screen, "enemy_projectiles"):
                game_screen = game_screen.parent
            if game_screen:
                game_screen.enemy_projectiles.append(proj)

    def _show_slam_impact(self, cx, cy, radius):
        """Show red impact circle after damage is dealt"""
        if not hasattr(self, "game") or not self.parent:
            return
        
        effect_widget = Widget(size_hint=(None, None), size=(radius * 2, radius * 2))
        effect_widget.pos = (cx - radius, cy - radius)
        
        with effect_widget.canvas:
            Color(1, 0, 0, 0.6)  # Red impact with transparency
            Ellipse(pos=effect_widget.pos, size=effect_widget.size)
        
        self.parent.add_widget(effect_widget)
        Clock.schedule_once(lambda dt: self._remove_effect_widget(effect_widget), 0.25)

    def do_swipe(self, player_pos):
        if not hasattr(self, "game"):
            return
        ex = self.pos[0] + self.enemy_size[0] / 2
        ey = self.pos[1] + self.enemy_size[1] / 2
        proj = EnemyProjectile(start_pos=(ex, ey), target_pos=(player_pos[0] + 32, player_pos[1] + 32), damage=self.damage * 1.2)
        proj.speed = 700
        self.parent.add_widget(proj)
        game_screen = self.parent
        while game_screen and not hasattr(game_screen, "enemy_projectiles"):
            game_screen = game_screen.parent
        if game_screen:
            game_screen.enemy_projectiles.append(proj)

    def do_missile(self, player_pos):
        if not hasattr(self, "game"):
            return
        ex = self.pos[0] + self.enemy_size[0] / 2
        ey = self.pos[1] + self.enemy_size[1] / 2
        proj = EnemyProjectile(start_pos=(ex, ey), target_pos=(player_pos[0] + 32, player_pos[1] + 32), damage=self.damage * 0.8)
        proj.speed = 300
        self.parent.add_widget(proj)
        game_screen = self.parent
        while game_screen and not hasattr(game_screen, "enemy_projectiles"):
            game_screen = game_screen.parent
        if game_screen:
            game_screen.enemy_projectiles.append(proj)

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

        # เพิ่มกระสุนเข้า world_layout (parent ของศัตรู)
        self.parent.add_widget(proj)

        # ส่งเข้า list ใน GameScreen เพื่อเช็ค Collision
        # เดินไต่ parent ขึ้นไปหาวัตถุที่มี attribute enemy_projectiles (คือ GameScreen)
        game_screen = self.parent
        while game_screen is not None and not hasattr(game_screen, "enemy_projectiles"):
            game_screen = game_screen.parent
        if game_screen is not None:
            game_screen.enemy_projectiles.append(proj)

    def take_damage(self, amount, knockback_dir=(0, 0)):
        """รับดาเมจและแสดงเอฟเฟกต์กระพริบม่วงชั่วขณะ"""
        
        # 🔵 Shielder damage reduction
        if getattr(self, "enemy_type", "") == "shielder" and getattr(self, "has_shield", False):
            amount *= 0.40  # รับดาเมจแค่ 40%
            if self.hp - amount <= self.max_hp * 0.2: # เลือดเหลือ < 20% โล่แตก
                self.has_shield = False

        self.hp -= amount

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
        dist = math.hypot(dx, dy)
        
        if dist == 0:
            dx, dy = 1, 0
            
        base_angle = math.atan2(dy, dx)
        spread_deg = math.radians(5) # Tightly (5 degrees offset)
        
        for offset in [-spread_deg, 0, spread_deg]:
            ang = base_angle + offset
            tx = ex + math.cos(ang) * 900
            ty = ey + math.sin(ang) * 900
            
            proj = EnemyProjectile(
                start_pos=(ex, ey), target_pos=(tx, ty), damage=self.damage
            )
            proj.speed = 450
            self.parent.add_widget(proj)
            
            game_screen = self.parent
            while game_screen is not None and not hasattr(game_screen, "enemy_projectiles"):
                game_screen = game_screen.parent
            if game_screen is not None:
                game_screen.enemy_projectiles.append(proj)