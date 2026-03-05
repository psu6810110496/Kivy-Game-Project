"""
game/skills.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ระบบสกิลใหม่ทั้งหมด 
- Auto Skill 1 & 2
- Active Skill 3 (LMB) พร้อมระบบ Stack
"""

import math
import random
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line
from kivy.uix.widget import Widget

# ══════════════════════════════════════════════════════
#  BASE SKILLS
# ══════════════════════════════════════════════════════
class BaseSkill:
    name = "???"
    description = "???"
    max_level = 5
    is_active = False

    def __init__(self):
        self.level = 1
        self._timer = 0.0
        self.cooldown = 1.0

    def tick(self, dt, game):
        self._timer -= dt
        if self._timer <= 0:
            self._timer = self.cooldown
            self.activate(game)

    def activate(self, game):
        pass

    def upgrade(self):
        if self.level < self.max_level:
            self.level += 1
            return True
        return False

class ActiveSkill(BaseSkill):
    """
    Skill 3: กดคลิกซ้าย (LMB) ใช้ Stack
    """
    is_active = True

    def __init__(self, max_stacks=3, recharge_time=5.0):
        super().__init__()
        self.max_stacks = max_stacks
        self.current_stacks = max_stacks
        self.recharge_time = recharge_time
        self._recharge_timer = 0.0

    def tick(self, dt, game):
        # ระบบ Recharge Stack อัตโนมัติ
        if self.current_stacks < self.max_stacks:
            self._recharge_timer += dt
            if self._recharge_timer >= self.recharge_time:
                self.current_stacks += 1
                self._recharge_timer = 0.0

    @property
    def stack_fraction(self):
        """สำหรับนำไปทำ UI Progress Bar"""
        if self.current_stacks >= self.max_stacks:
            return 1.0
        return self._recharge_timer / self.recharge_time

    def fire(self, game):
        """เรียกใช้เมื่อผู้เล่นกดคลิกซ้าย"""
        if self.current_stacks > 0:
            self.current_stacks -= 1
            self.execute(game)
            return True
        return False

    def execute(self, game):
        pass


# ══════════════════════════════════════════════════════
#  PTAE SKILLS
# ══════════════════════════════════════════════════════
class DinoCircle(BaseSkill):
    name = "Dino Circle"
    description = "ไดโนเสาร์วิ่งวนรอบตัว ชนศัตรูเรื่อยๆ"
    
    def __init__(self):
        super().__init__()
        self.orbit_angle = 0.0
        self.hit_cooldowns = {}
    
    def tick(self, dt, game):
        # หมุนรอบตัว
        self.orbit_angle = (self.orbit_angle + 180 * dt) % 360
        px = game.player_pos[0] + 32
        py = game.player_pos[1] + 32
        radius = 80 + (self.level * 10)
        
        # ตำแหน่งของไดโนเสาร์ (สมมติ 1 ตัว ถ้าเลเวลสูงอาจเพิ่มจำนวนมุมได้)
        dx = px + math.cos(math.radians(self.orbit_angle)) * radius
        dy = py + math.sin(math.radians(self.orbit_angle)) * radius
        
        # อัปเดต Cooldown ของศัตรูแต่ละตัว
        for enemy in list(self.hit_cooldowns.keys()):
            self.hit_cooldowns[enemy] -= dt
            if self.hit_cooldowns[enemy] <= 0:
                del self.hit_cooldowns[enemy]

        # เช็คชน
        for enemy in list(game.enemies):
            ex = enemy.pos[0] + 20
            ey = enemy.pos[1] + 20
            if math.hypot(ex - dx, ey - dy) < 40: # รัศมีชนของไดโน
                if enemy not in self.hit_cooldowns:
                    enemy.take_damage(10 + (self.level * 5))
                    self.hit_cooldowns[enemy] = 0.5 # Hit cooldown 0.5s ต่อตัว

class DinoSummon(BaseSkill):
    name = "Dino Summon"
    description = "อัญเชิญไดโนเสาร์พุ่งชนเป้าหมาย"
    
    def __init__(self):
        super().__init__()
        self.cooldown = 2.0
        
    def activate(self, game):
        if not game.enemies: return
        px = game.player_pos[0] + 32
        py = game.player_pos[1] + 32
        
        from game.projectile_widget import EnemyProjectile # ยืมใช้คลาสกระสุนไปก่อน
        count = self.level
        targets = random.sample(game.enemies, min(count, len(game.enemies)))
        
        for enemy in targets:
            ex = enemy.pos[0] + 20
            ey = enemy.pos[1] + 20
            proj = EnemyProjectile(start_pos=(px, py), target_pos=(ex, ey), damage=15*self.level)
            proj.speed = 500
            game.world_layout.add_widget(proj)
            if hasattr(game, "player_projectiles"):
                game.player_projectiles.append(proj)

class DinoPunch(ActiveSkill):
    name = "Dino Punch"
    description = "Cone AoE สร้าง Knockback มหาศาล"
    
    def __init__(self):
        super().__init__(max_stacks=3, recharge_time=8.0)
        
    def execute(self, game):
        px = game.player_pos[0] + 32
        py = game.player_pos[1] + 32
        mouse_dir = getattr(game, "mouse_dir", (1, 0))
        aim_angle = math.degrees(math.atan2(mouse_dir[1], mouse_dir[0]))
        
        cone_angle = 60 # กว้าง 60 องศา
        radius = 200 + (self.level * 20)
        
        for enemy in list(game.enemies):
            ex = enemy.pos[0] + 20
            ey = enemy.pos[1] + 20
            dx, dy = ex - px, ey - py
            dist = math.hypot(dx, dy)
            
            if dist <= radius:
                angle_to_enemy = math.degrees(math.atan2(dy, dx))
                diff = (angle_to_enemy - aim_angle) % 360
                if diff > 180: diff -= 360
                
                if abs(diff) <= cone_angle / 2:
                    enemy.take_damage(30 * self.level)
                    # Knockback 150
                    knock_x = (dx / dist) * 150
                    knock_y = (dy / dist) * 150
                    enemy.pos = (enemy.pos[0] + knock_x, enemy.pos[1] + knock_y)


# ══════════════════════════════════════════════════════
#  LOSTMAN SKILLS
# ══════════════════════════════════════════════════════
class AxeThrow(BaseSkill):
    name = "Axe Throw"
    description = "ปาขวานติดตามศัตรู"
    
    def __init__(self):
        super().__init__()
        self.cooldown = 1.5
        
    def activate(self, game):
        if not game.enemies: return
        px = game.player_pos[0] + 32
        py = game.player_pos[1] + 32
        from game.projectile_widget import EnemyProjectile
        
        for _ in range(self.level):
            enemy = random.choice(game.enemies)
            ex = enemy.pos[0] + 20
            ey = enemy.pos[1] + 20
            proj = EnemyProjectile(start_pos=(px, py), target_pos=(ex, ey), damage=20)
            game.world_layout.add_widget(proj)
            if hasattr(game, "player_projectiles"):
                game.player_projectiles.append(proj)

class BombTrap(BaseSkill):
    name = "Bomb Trap"
    description = "วางระเบิดเวลา"
    
    def __init__(self):
        super().__init__()
        self.cooldown = 4.0
        self.active_bombs = []
        
    def tick(self, dt, game):
        super().tick(dt, game)
        # อัปเดตระเบิดที่วางไปแล้ว
        for bomb in self.active_bombs[:]:
            bomb["timer"] -= dt
            if bomb["timer"] <= 0:
                self.explode(bomb["pos"], game)
                self.active_bombs.remove(bomb)
                
    def activate(self, game):
        px = game.player_pos[0] + 32
        py = game.player_pos[1] + 32
        self.active_bombs.append({"pos": (px, py), "timer": 3.0}) # 3 วิ ระเบิด
        
    def explode(self, pos, game):
        radius = 120 + (self.level * 20)
        for enemy in list(game.enemies):
            ex = enemy.pos[0] + 20
            ey = enemy.pos[1] + 20
            if math.hypot(ex - pos[0], ey - pos[1]) <= radius:
                enemy.take_damage(50 * self.level)

class WhirlSlash(ActiveSkill):
    name = "Whirl Slash"
    description = "ฟันกวาด 360 องศา"
    
    def __init__(self):
        super().__init__(max_stacks=3, recharge_time=7.0)
        
    def execute(self, game):
        px = game.player_pos[0] + 32
        py = game.player_pos[1] + 32
        radius = 160 + (self.level * 15)
        
        for enemy in list(game.enemies):
            ex = enemy.pos[0] + 20
            ey = enemy.pos[1] + 20
            if math.hypot(ex - px, ey - py) <= radius:
                enemy.take_damage(40 * self.level)
                # Knockback นิดหน่อย
                dx, dy = ex - px, ey - py
                dist = math.hypot(dx, dy)
                if dist > 0:
                    enemy.pos = (enemy.pos[0] + (dx/dist)*50, enemy.pos[1] + (dy/dist)*50)


# ══════════════════════════════════════════════════════
#  MONKEY SKILLS
# ══════════════════════════════════════════════════════
class PistolSkill(BaseSkill):
    name = "Pistol Auto-lock"
    description = "ยิงปืนพกล็อกเป้าอัตโนมัติ"
    
    def __init__(self):
        super().__init__()
        self.cooldown = 0.5
        
    def activate(self, game):
        if not game.enemies: return
        px = game.player_pos[0] + 32
        py = game.player_pos[1] + 32
        # หาตัวใกล้สุด
        closest = min(game.enemies, key=lambda e: math.hypot(e.pos[0]-px, e.pos[1]-py))
        from game.projectile_widget import EnemyProjectile
        proj = EnemyProjectile(start_pos=(px, py), target_pos=(closest.pos[0]+20, closest.pos[1]+20), damage=15*self.level)
        proj.speed = 800
        game.world_layout.add_widget(proj)
        if hasattr(game, "player_projectiles"):
            game.player_projectiles.append(proj)

class ShotgunSkill(BaseSkill):
    name = "Shotgun Burst"
    description = "ยิงลูกซองกระจาย 5 นัด"
    
    def __init__(self):
        super().__init__()
        self.cooldown = 2.5
        
    def activate(self, game):
        px = game.player_pos[0] + 32
        py = game.player_pos[1] + 32
        mouse_dir = getattr(game, "mouse_dir", (1, 0))
        base_angle = math.degrees(math.atan2(mouse_dir[1], mouse_dir[0]))
        
        from game.projectile_widget import EnemyProjectile
        for offset in [-30, -15, 0, 15, 30]:
            angle = math.radians(base_angle + offset)
            tx = px + math.cos(angle) * 100
            ty = py + math.sin(angle) * 100
            proj = EnemyProjectile(start_pos=(px, py), target_pos=(tx, ty), damage=10*self.level)
            proj.speed = 600
            game.world_layout.add_widget(proj)
            if hasattr(game, "player_projectiles"):
                game.player_projectiles.append(proj)

class RPGSkill(ActiveSkill):
    name = "RPG Blast"
    description = "ยิงจรวดระเบิดเป็นวงกว้าง"
    
    def __init__(self):
        super().__init__(max_stacks=3, recharge_time=5.0)
        
    def execute(self, game):
        px = game.player_pos[0] + 32
        py = game.player_pos[1] + 32
        mouse_dir = getattr(game, "mouse_dir", (1, 0))
        
        # เป้าหมายไปทางเมาส์
        tx = px + mouse_dir[0] * 300
        ty = py + mouse_dir[1] * 300
        
        from game.projectile_widget import EnemyProjectile
        proj = EnemyProjectile(start_pos=(px, py), target_pos=(tx, ty), damage=60*self.level)
        # เพิ่มคุณสมบัติระเบิดตอนชน (ต้องไปดักตอนเช็คชนใน combat_manager หรือใช้ดาเมจวงกว้างเลย)
        proj.is_rpg = True 
        proj.explode_radius = 150 + (self.level * 20)
        
        game.world_layout.add_widget(proj)
        if hasattr(game, "player_projectiles"):
            game.player_projectiles.append(proj)


# ══════════════════════════════════════════════════════
#  DICTIONARY สำหรับผูกตัวละคร
# ══════════════════════════════════════════════════════
CHAR_DEFAULT_SKILLS = {
    "PTae":    [DinoCircle, DinoSummon, DinoPunch],
    "Lostman": [AxeThrow, BombTrap, WhirlSlash],
    "Monkey":  [PistolSkill, ShotgunSkill, RPGSkill],
}