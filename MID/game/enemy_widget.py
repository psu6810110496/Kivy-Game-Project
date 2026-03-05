"""
game/enemy_widget.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ประกอบด้วย:
  EnemyStats      — dataclass ข้อมูล stat ของศัตรูแต่ละประเภท
  EnemyWidget     — Widget หลักของศัตรูทุกประเภท (normal/stalker/ranger/boss/big_boss)
                    มี AI, Movement, Separation, Attack logic
"""
import math
import random

from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Ellipse, Rectangle
from kivy.uix.widget import Widget

from game.entity import BaseEntity
from game.projectile_widget import EnemyProjectile


# ═══════════════════════════════════════════════════════════
#  Enemy stat definitions (data-driven, ขยายง่าย)
# ═══════════════════════════════════════════════════════════
_ENEMY_STATS: dict = {
    "normal": {
        "hp": 30, "speed": 2.2, "damage": 10,
        "color": (1, 1, 1, 1), "size": (40, 40),
    },
    "stalker": {
        "hp": 15, "speed": 3.8, "damage": 5,
        "color": (0.8, 0.2, 1, 1), "size": (30, 30),
    },
    "ranger": {
        "hp": 25, "speed": 1.8, "damage": 15,
        "color": (0.2, 0.9, 0.3, 1), "size": (45, 45),
    },
    "boss": {
        "hp": 400, "speed": 1.2, "damage": 30,
        "color": (0.9, 0.2, 0.2, 1), "size": (96, 96),
    },
    "big_boss": {
        "hp": 1200, "speed": 1.0, "damage": 40,
        "color": (0.5, 0.1, 0.7, 1), "size": (128, 128),
    },
}

# ─── Lazy-load textures เพียงครั้งเดียวต่อ class ─────────────
def _load_enemy_textures() -> dict:
    import os
    boss_path = "assets/enemy/boss.png" if os.path.exists("assets/enemy/boss.png") else "assets/enemy/enemy4.png"
    return {
        "normal":   CoreImage("assets/enemy/enemy1.png").texture,
        "stalker":  CoreImage("assets/enemy/enemy2.png").texture,
        "ranger":   CoreImage("assets/enemy/enemy3.png").texture,
        "boss":     CoreImage(boss_path).texture,
        "big_boss": CoreImage(boss_path).texture,
    }


# ═══════════════════════════════════════════════════════════
#  EnemyWidget
# ═══════════════════════════════════════════════════════════
class EnemyWidget(BaseEntity):
    """
    Widget ศัตรูทุกประเภท — รับ enemy_type string เพื่อโหลด stat และ texture
    AI แยกตาม type: normal/stalker วิ่งตรง, ranger kite+ยิง, big_boss มี special attacks
    """

    _TEXTURES: dict | None = None  # class-level texture cache

    @classmethod
    def _get_textures(cls) -> dict:
        if cls._TEXTURES is None:
            cls._TEXTURES = _load_enemy_textures()
        return cls._TEXTURES

    def __init__(self, spawn_pos=(0, 0), enemy_type: str = "normal", **kwargs):
        stat = _ENEMY_STATS.get(enemy_type, _ENEMY_STATS["normal"])
        super().__init__(
            hp=stat["hp"],
            damage=stat["damage"],
            speed=stat["speed"],
            **kwargs,
        )
        self.pos = spawn_pos
        self.enemy_type = enemy_type
        self.enemy_size: tuple = stat["size"]

        # ── Ranger attack cooldown ─────────────────────
        self.attack_cooldown: float = 0.0
        self.shoot_delay: float = 3.0

        # ── Big Boss special attack cooldowns ──────────
        self.slam_cooldown: float = random.uniform(3.0, 6.0)
        self.swipe_cooldown: float = random.uniform(2.0, 4.0)
        self.missile_cooldown: float = random.uniform(3.0, 5.0)

        # ── Melee hit cooldown (ไม่ให้ damage ทุก frame) ──
        self._melee_cooldown: float = 0.0

        # ── Drawing ────────────────────────────────────
        textures = self._get_textures()
        self.texture = textures.get(enemy_type, textures["normal"])

        with self.canvas:
            self.color_inst = Color(*stat["color"])
            self.rect = Rectangle(pos=self.pos, size=self.enemy_size, texture=self.texture)

        self.bind(pos=self._on_pos_changed)

    # ── Internal ──────────────────────────────────────────
    def _on_pos_changed(self, _inst, value):
        self.rect.pos = value

    # ── Public API ────────────────────────────────────────
    def take_damage(self, amount: float, knockback_dir=(0, 0)):
        """รับ damage + flash สีม่วง + knockback"""
        self.hp -= amount

        # Flash (closure-safe)
        orig = tuple(self.color_inst.rgba)
        self.color_inst.rgba = (1, 0, 1, 1)
        Clock.schedule_once(lambda dt, c=orig: setattr(self.color_inst, "rgba", c), 0.1)

        # Knockback
        if knockback_dir[0] != 0 or knockback_dir[1] != 0:
            kb = 25
            self.pos = (self.pos[0] + knockback_dir[0] * kb,
                        self.pos[1] + knockback_dir[1] * kb)

    # ── Movement / AI ─────────────────────────────────────
    def update_movement(self, player_pos, all_enemies: list, dt: float = 1 / 60.0):
        """อัปเดต AI movement ทุก frame"""
        px = player_pos[0] + 32
        py = player_pos[1] + 32
        ex = self.pos[0] + self.enemy_size[0] / 2
        ey = self.pos[1] + self.enemy_size[1] / 2

        dx, dy = px - ex, py - ey
        dist = math.hypot(dx, dy)
        vx, vy = 0.0, 0.0

        if self.enemy_type == "ranger":
            vx, vy = self._ai_ranger(dx, dy, dist, player_pos, dt)
        elif self.enemy_type == "big_boss":
            vx, vy = self._ai_big_boss(dx, dy, dist, player_pos, dt)
        else:
            # normal / stalker / boss — วิ่งตรง
            if dist > 0:
                vx, vy = (dx / dist) * self.speed, (dy / dist) * self.speed

        # ── Separation — ไม่ให้ทับกัน ─────────────────
        sep_x, sep_y = 0.0, 0.0
        for other in all_enemies:
            if other is self:
                continue
            ox = other.pos[0] + other.enemy_size[0] / 2
            oy = other.pos[1] + other.enemy_size[1] / 2
            d = math.hypot(ex - ox, ey - oy)
            if d < 45:
                sep_x += (ex - ox) * 0.15
                sep_y += (ey - oy) * 0.15

        self.pos = (self.pos[0] + vx + sep_x, self.pos[1] + vy + sep_y)

    # ── AI helpers ────────────────────────────────────────
    def _ai_ranger(self, dx, dy, dist, player_pos, dt) -> tuple:
        """Ranger: kite ระยะ 250–450 และยิงกระสุนเมื่ออยู่ในระยะ"""
        vx, vy = 0.0, 0.0
        if dist > 0:
            if dist > 450:
                vx, vy = (dx / dist) * self.speed, (dy / dist) * self.speed
            elif dist < 250:
                vx, vy = -(dx / dist) * self.speed, -(dy / dist) * self.speed

        self.attack_cooldown -= dt
        if dist < 600 and self.attack_cooldown <= 0:
            self.shoot(player_pos)
            self.attack_cooldown = self.shoot_delay
        return vx, vy

    def _ai_big_boss(self, dx, dy, dist, player_pos, dt) -> tuple:
        """Big Boss: วิ่งเข้าหาตลอด + ใช้สกิลพิเศษ"""
        vx, vy = 0.0, 0.0
        if dist > 0:
            vx, vy = (dx / dist) * self.speed, (dy / dist) * self.speed

        self.slam_cooldown -= dt
        self.swipe_cooldown -= dt
        self.missile_cooldown -= dt

        if self.slam_cooldown <= 0 and dist < 300:
            self.do_slam()
            self.slam_cooldown = random.uniform(4.0, 6.0)

        if self.swipe_cooldown <= 0:
            self.do_swipe(player_pos)
            self.swipe_cooldown = random.uniform(3.0, 5.0)

        if self.missile_cooldown <= 0:
            self.do_missile(player_pos)
            self.missile_cooldown = random.uniform(4.0, 6.0)

        return vx, vy

    # ── Ranger Shoot ──────────────────────────────────────
    def shoot(self, player_pos):
        if not self.parent:
            return
        ex = self.pos[0] + self.enemy_size[0] / 2
        ey = self.pos[1] + self.enemy_size[1] / 2
        proj = EnemyProjectile(
            start_pos=(ex, ey),
            target_pos=(player_pos[0] + 32, player_pos[1] + 32),
            damage=self.damage,
        )
        self.parent.add_widget(proj)
        self._register_projectile(proj)

    # ── Big Boss Attacks ──────────────────────────────────
    def do_slam(self):
        """Ground Slam: เตือนด้วยวงเหลือง แล้วระเบิดสีแดง"""
        if not hasattr(self, "game"):
            return
        cx = self.pos[0] + self.enemy_size[0] / 2
        cy = self.pos[1] + self.enemy_size[1] / 2
        radius = 250
        self._show_area_warning(cx, cy, radius, color=(1, 1, 0, 0.5), duration=0.4)
        Clock.schedule_once(lambda dt: self._execute_slam(cx, cy, radius), 0.4)

    def _execute_slam(self, cx, cy, radius):
        if not hasattr(self, "game"):
            return
        pp = self.game.player_pos
        if math.hypot(cx - (pp[0] + 32), cy - (pp[1] + 32)) < radius:
            self.game.take_damage(self.damage * 1.5)
        self._show_area_warning(cx, cy, radius, color=(1, 0, 0, 0.6), duration=0.25)
        # กระสุน radial 12 ทิศ
        for i in range(12):
            angle = 2 * math.pi * i / 12
            tx = cx + math.cos(angle) * 500
            ty = cy + math.sin(angle) * 500
            proj = EnemyProjectile(start_pos=(cx, cy), target_pos=(tx, ty), damage=self.damage)
            proj.speed = 250
            if self.parent:
                self.parent.add_widget(proj)
                self._register_projectile(proj)

    def do_swipe(self, player_pos):
        if not hasattr(self, "game") or not self.parent:
            return
        ex = self.pos[0] + self.enemy_size[0] / 2
        ey = self.pos[1] + self.enemy_size[1] / 2
        proj = EnemyProjectile(
            start_pos=(ex, ey),
            target_pos=(player_pos[0] + 32, player_pos[1] + 32),
            damage=self.damage * 1.2,
        )
        proj.speed = 700
        self.parent.add_widget(proj)
        self._register_projectile(proj)

    def do_missile(self, player_pos):
        if not hasattr(self, "game") or not self.parent:
            return
        ex = self.pos[0] + self.enemy_size[0] / 2
        ey = self.pos[1] + self.enemy_size[1] / 2
        proj = EnemyProjectile(
            start_pos=(ex, ey),
            target_pos=(player_pos[0] + 32, player_pos[1] + 32),
            damage=self.damage * 0.8,
        )
        proj.speed = 300
        self.parent.add_widget(proj)
        self._register_projectile(proj)

    # ── VFX helpers ───────────────────────────────────────
    def _show_area_warning(self, cx, cy, radius, color, duration):
        """แสดงวงกลมเตือน/ระเบิดชั่วคราว"""
        if not self.parent:
            return
        w = Widget(size_hint=(None, None), size=(radius * 2, radius * 2))
        w.pos = (cx - radius, cy - radius)
        with w.canvas:
            Color(*color)
            Ellipse(pos=w.pos, size=w.size)
        self.parent.add_widget(w)
        Clock.schedule_once(lambda dt: self._remove_widget_safe(w), duration)

    def _remove_widget_safe(self, widget):
        if widget.parent:
            widget.parent.remove_widget(widget)

    def _register_projectile(self, proj):
        """ไต่ parent tree หา GameScreen แล้วเพิ่ม proj เข้า enemy_projectiles"""
        node = self.parent
        while node and not hasattr(node, "enemy_projectiles"):
            node = node.parent
        if node:
            node.enemy_projectiles.append(proj)
