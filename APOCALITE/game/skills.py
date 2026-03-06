"""
game/skills.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PTae   (Tank/Dino)  : DinoCircle, DinoSummon, [S3] DinoPunch (cone AoE)
Lostman (Axe/Trap)  : AxeThrow, BombTrap,   [S3] WhirlSlash (big arc)
Monkey  (Gunner)    : PistolSkill, ShotgunSkill, [S3] RPGSkill

Skill 3 ทุกตัว: manual LMB, Stack max 3, recharge per-skill
Melee auto-attack: PtaePunch / LostmanAxe / MonkeyCombo (auto-tick)
"""

import math
import random
from typing import Dict, List, Type

from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Ellipse, InstructionGroup, Line, Rectangle


# ═══════════════════════════════════════════════════════════
#  BASE
# ═══════════════════════════════════════════════════════════
class BaseSkill:
    name: str = "???"
    description: str = ""
    MAX_LEVEL: int = 25

    def __init__(self):
        self.level: int = 1
        self.max_level: int = self.MAX_LEVEL
        self._timer: float = 0.0

    @property
    def cooldown(self) -> float:
        return 2.0

    def tick(self, dt: float, game):
        self._timer -= dt
        if self._timer <= 0:
            self.activate(game)
            self._timer = self.cooldown

    def activate(self, game): pass
    def upgrade(self):
        if self.level < self.max_level:
            self.level += 1
            self._on_upgrade()
    def _on_upgrade(self): pass
    def summary(self): return f"{self.name} Lv{self.level}"


class StackSkill(BaseSkill):
    """
    Skill 3 base — manual (LMB), stack system
    - max_stacks = 3
    - recharge_time: เวลาเติม 1 stack
    - กด manual_activate() จาก engine ตอน LMB
    """
    MAX_STACKS: int = 3

    def __init__(self):
        super().__init__()
        self.stacks: int = self.MAX_STACKS
        self._recharge_timer: float = 0.0

    @property
    def recharge_time(self) -> float:
        return 8.0  # override ใน subclass

    def tick(self, dt: float, game):
        """auto-tick เฉพาะ recharge — ไม่ activate อัตโนมัติ"""
        if self.stacks < self.MAX_STACKS:
            self._recharge_timer -= dt
            if self._recharge_timer <= 0:
                self.stacks += 1
                if self.stacks < self.MAX_STACKS:
                    self._recharge_timer = self.recharge_time

    def manual_activate(self, game) -> bool:
        """เรียกจาก engine ตอน LMB กด — return True ถ้าใช้ได้"""
        if self.stacks <= 0:
            return False
        self.stacks -= 1
        if self.stacks == self.MAX_STACKS - 1:
            self._recharge_timer = self.recharge_time
        elif self.stacks < self.MAX_STACKS and self._recharge_timer <= 0:
            self._recharge_timer = self.recharge_time
        self.activate(game)
        return True

    @property
    def stack_fraction(self) -> float:
        """fraction ของ recharge progress (0.0–1.0)"""
        if self.stacks >= self.MAX_STACKS:
            return 1.0
        if self.recharge_time <= 0:
            return 1.0
        return 1.0 - max(0, self._recharge_timer) / self.recharge_time


# ═══════════════════════════════════════════════════════════
#  ─── PTAE SKILLS ──────────────────────────────────────
# ═══════════════════════════════════════════════════════════

class DinoCircle(BaseSkill):
    """PTae Skill 1 — ไดโนเสาร์วิ่งวนรอบตัว ชนศัตรูทำดาเมจ (auto)"""
    name = "Dino Circle"
    description = "ไดโนเสาร์วิ่งวนรอบตัว ทำดาเมจทุกศัตรูที่โดน"

    def __init__(self):
        super().__init__()
        self.orbit_radius = 130
        self.dino_count = 1
        self.damage_mult = 1.5
        self.orbit_speed = 3.0       # rad/s
        self._orbit_angle = 0.0
        self._hit_cooldowns: dict = {}  # enemy_id → cooldown

    @property
    def cooldown(self):
        # ไม่ใช้ cooldown เหมือนสกิลอื่น — tick ทุก frame เพื่ออัปเดต orbit
        return 0.016  # ~60fps

    def _on_upgrade(self):
        if self.level % 2 == 0:
            self.dino_count += 1
        self.damage_mult += 0.3
        self.orbit_radius += 10

    def tick(self, dt: float, game):
        """อัปเดต orbit angle และตรวจ collision"""
        self._orbit_angle += self.orbit_speed * dt
        if self._orbit_angle > 2 * math.pi:
            self._orbit_angle -= 2 * math.pi

        px = game.player_pos[0] + 32
        py = game.player_pos[1] + 32
        dmg = game.player_stats.damage * self.damage_mult

        # อัปเดต cooldown hitboxes
        for eid in list(self._hit_cooldowns):
            self._hit_cooldowns[eid] -= dt
            if self._hit_cooldowns[eid] <= 0:
                del self._hit_cooldowns[eid]

        # ตำแหน่งไดโนแต่ละตัว
        positions = []
        for i in range(self.dino_count):
            ang = self._orbit_angle + (2 * math.pi * i / max(1, self.dino_count))
            dx = math.cos(ang) * self.orbit_radius
            dy = math.sin(ang) * self.orbit_radius
            positions.append((px + dx, py + dy))

        # ตรวจ collision กับ enemy
        for enemy in list(game.enemies):
            eid = id(enemy)
            if eid in self._hit_cooldowns:
                continue
            ec_x = enemy.pos[0] + 20
            ec_y = enemy.pos[1] + 20
            for (ox, oy) in positions:
                if math.hypot(ox - ec_x, oy - ec_y) < 45:
                    _hit_enemy(game, enemy, dmg)
                    self._hit_cooldowns[eid] = 0.5  # hit cooldown 0.5s per enemy
                    break

        # วาด dino indicators (วงกลมเล็ก)
        _draw_orbit_indicators(game, positions, self._orbit_angle)

    def activate(self, game):
        pass  # ใช้ tick แทน


class DinoSummon(BaseSkill):
    """PTae Skill 2 — Summon ไดโนเสาร์ homing ติดตามศัตรู (auto)
    จำนวน = level, แต่ละตัวติดตาม enemy แยกตัว"""
    name = "Dino Summon"
    description = "เรียกไดโนเสาร์ homing ติดตามศัตรู จำนวนเพิ่มตาม level"

    def __init__(self):
        super().__init__()
        self.damage_mult = 2.0
        self.dino_speed = 320
        self.dino_range = 900

    @property
    def cooldown(self):
        return max(2.0, 5.0 - (self.level - 1) * 0.6)

    def _on_upgrade(self):
        self.damage_mult += 0.4
        self.dino_speed = min(480, self.dino_speed + 15)

    def activate(self, game):
        if not game.enemies:
            return
        from game.projectile_widget import HomingDino
        px = game.player_pos[0] + 32
        py = game.player_pos[1] + 32
        dmg = game.player_stats.damage * self.damage_mult
        count = self.level  # จำนวนไดโน = level
        # แต่ละตัวเลือก enemy สุ่ม (อาจซ้ำถ้า enemy น้อย)
        targets = random.choices(game.enemies, k=min(count, len(game.enemies)))
        for target in targets:
            proj = HomingDino(
                start_pos=(px, py),
                target_ref=target,
                speed=self.dino_speed,
                proj_range=self.dino_range,
                damage=dmg,
                game=game, # 🌟 เพิ่ม game parameter เพื่อให้ retarget ได้
            )
            game.player_bullets.append(proj)
            game.world_layout.add_widget(proj)


class DinoPunch(StackSkill):
    """PTae Skill 3 — ยิงลำแสง AoE กว้างตามทิศเมาส์ ตี enemy ทุกตัวในเส้นทาง (manual LMB, Stack×3)"""
    name = "Dino Beam"
    description = "ยิงลำแสงไดโนกว้าง AoE ตรงไปข้างหน้า ทะลุและตีศัตรูทุกตัวในเส้นทาง (Stack ×3)"

    STACK_RECHARGE = 7.0

    def __init__(self):
        super().__init__()
        self.damage_mult = 5.0
        self.beam_length = 1200

    @property
    def recharge_time(self):
        return max(4.0, self.STACK_RECHARGE - (self.level - 1) * 0.5)

    @property
    def beam_width(self):
        if self.level <= 5:
            return int(50 + (self.level - 1) * 12.5)
        return int(100 + (self.level - 5) * 10)

    def _on_upgrade(self):
        self.damage_mult += 1.0
        self.beam_length  = min(2000, self.beam_length + 80)

    def activate(self, game):
        from game.projectile_widget import DinoBeam
        px = game.player_pos[0] + 32
        py = game.player_pos[1] + 32
        dmg = game.player_stats.damage * self.damage_mult
        dx, dy = game.mouse_dir[0], game.mouse_dir[1]
        mag = math.hypot(dx, dy)
        if mag == 0:
            dx, dy = 1.0, 0.0
        else:
            dx, dy = dx/mag, dy/mag
        beam = DinoBeam(
            start_pos=(px, py),
            direction=(dx, dy),
            damage=dmg,
            length=self.beam_length,
            width=self.beam_width,
        )
        game.world_layout.add_widget(beam)
        if not hasattr(game, 'active_beams'):
            game.active_beams = []
        game.active_beams.append(beam)


# ═══════════════════════════════════════════════════════════
#  ─── PTAE MELEE ──────────────────────────────────────────
# ═══════════════════════════════════════════════════════════
class PtaePunch(BaseSkill):
    """PTae melee — ต่อยไปข้างหน้า cone 60° (auto-tick)"""
    name = "Punch"
    description = "ต่อยไปข้างหน้า (auto)"

    def __init__(self):
        super().__init__()
        self.radius = 90
        self.cone_deg = 60
        self.damage_mult = 1.0

    @property
    def cooldown(self):
        return max(0.4, 0.8 - (self.level - 1) * 0.1)

    def _on_upgrade(self):
        self.damage_mult += 0.2
        self.radius += 10

    def activate(self, game):
        px = game.player_pos[0] + 32
        py = game.player_pos[1] + 32
        dmg = game.player_stats.damage * self.damage_mult
        aim = math.atan2(game.mouse_dir[1], game.mouse_dir[0])
        half = math.radians(self.cone_deg / 2)
        _show_cone_vfx(game, px, py, self.radius, math.degrees(aim),
                       self.cone_deg, game.slash_textures)
        for enemy in list(game.enemies):
            ex = enemy.pos[0] + 20
            ey = enemy.pos[1] + 20
            dist = math.hypot(ex - px, ey - py)
            if dist > self.radius:
                continue
            ang = math.atan2(ey - py, ex - px)
            diff = abs((ang - aim + math.pi) % (2 * math.pi) - math.pi)
            if diff <= half:
                _hit_enemy(game, enemy, dmg)


# ═══════════════════════════════════════════════════════════
#  ─── LOSTMAN SKILLS ──────────────────────────────────────
# ═══════════════════════════════════════════════════════════

class AxeThrow(BaseSkill):
    """Lostman Skill 1 — ปาขวาน homing, เพิ่มจำนวนตาม level (auto)"""
    name = "Axe Throw"
    description = "ปาขวาน homing หาศัตรูใกล้สุด จำนวนเพิ่มตาม level"

    def __init__(self):
        super().__init__()
        self.damage_mult = 0.7
        self.bullet_speed = 420
        self.bullet_range = 650
        self.anim_frames = [
            "assets/Lostman/skill2/axe_t1.png",
            "assets/Lostman/skill2/axe_t2.png",
            "assets/Lostman/skill2/axe_t3.png",
            "assets/Lostman/skill2/axe_t4.png",
            "assets/Lostman/skill2/axe_t5.png",
            "assets/Lostman/skill2/axe_t6.png",
            "assets/Lostman/skill2/axe_t7.png",
            "assets/Lostman/skill2/axe_t8.png",
        ]

    @property
    def cooldown(self):
        return max(0.6, 1.5 - (self.level - 1) * 0.22)

    def _on_upgrade(self):
        self.damage_mult += 0.3

    def activate(self, game):
        if not game.enemies:
            return
        px = game.player_pos[0] + 32
        py = game.player_pos[1] + 32
        dmg = game.player_stats.damage * self.damage_mult
        count = self.level  # ยิง level ลูก
        sorted_e = sorted(
            game.enemies,
            key=lambda e: math.hypot(px - (e.pos[0] + 20), py - (e.pos[1] + 20))
        )
        targets = sorted_e[:count]
        for enemy in targets:
            _spawn_bullet(game, px, py,
                          enemy.pos[0] + 20, enemy.pos[1] + 20,
                          self.bullet_speed, self.bullet_range, dmg,
                          self.anim_frames)


class BombTrap(BaseSkill):
    """Lostman Skill 2 — วางระเบิด countdown 3-2-1 ระเบิด (auto)"""
    name = "Bomb Trap"
    description = "วางระเบิดนับถอยหลัง 3-2-1 แล้วระเบิด AoE"

    def __init__(self):
        super().__init__()
        self.splash_damage_mult = 6.0
        self.splash_radius = 160
        self.fuse_time = 3.0
        self.bomb_count = 1

    @property
    def cooldown(self):
        return max(3.0, 6.0 - (self.level - 1) * 0.6)

    def _on_upgrade(self):
        self.splash_damage_mult += 1.0
        self.splash_radius += 15
        if self.level >= 3:
            self.bomb_count = 2
        if self.level >= 5:
            self.bomb_count = 3

    def activate(self, game):
        from game.projectile_widget import BombWidget
        px = game.player_pos[0] + 32
        py = game.player_pos[1] + 32
        dmg = game.player_stats.damage * self.splash_damage_mult

        for i in range(self.bomb_count):
            # กระจายถ้าหลายลูก
            offset_x = (i - self.bomb_count // 2) * 60
            bx = px + offset_x
            by = py - 20
            bomb = BombWidget(
                pos=(bx - 16, by - 16),
                fuse=self.fuse_time,
                damage=dmg,
                radius=self.splash_radius,
            )
            game.world_layout.add_widget(bomb)
            # schedule explosion
            Clock.schedule_once(
                lambda _dt, b=bomb, g=game: _explode_bomb(g, b),
                self.fuse_time
            )


class WhirlSlash(StackSkill):
    """Lostman Skill 3 — ฟันขวานวงใหญ่รอบตัว (manual LMB, stack)"""
    name = "Whirl Slash"
    description = "ฟันขวานวงใหญ่รอบตัว knockback แรง (Stack ×3)"

    STACK_RECHARGE = 7.0

    def __init__(self):
        super().__init__()
        self.radius = 160
        self.damage_mult = 6.0
        self.knockback = 120
        self.anim_frames = [
            "assets/Lostman/skill1/axe_hit1.png",
            "assets/Lostman/skill1/axe_hit2.png",
            "assets/Lostman/skill1/axe_hit3.png",
            "assets/Lostman/skill1/axe_hit4.png",
        ]

    @property
    def recharge_time(self):
        return max(4.0, self.STACK_RECHARGE - (self.level - 1) * 0.7)

    def _on_upgrade(self):
        self.radius += 20
        self.damage_mult += 1.0
        self.knockback += 20

    def activate(self, game):
        px = game.player_pos[0] + 32
        py = game.player_pos[1] + 32
        dmg = game.player_stats.damage * self.damage_mult

        _show_slash_vfx(game, px, py, self.radius, 0, 180, self.anim_frames)

        for enemy in list(game.enemies):
            ex = enemy.pos[0] + 20
            ey = enemy.pos[1] + 20
            dist = math.hypot(ex - px, ey - py)
            if dist <= self.radius:
                _hit_enemy(game, enemy, dmg)
                if dist > 0:
                    enemy.pos = (
                        enemy.pos[0] + (ex - px) / dist * self.knockback,
                        enemy.pos[1] + (ey - py) / dist * self.knockback,
                    )


# ═══════════════════════════════════════════════════════════
#  ─── LOSTMAN MELEE ───────────────────────────────────────
# ═══════════════════════════════════════════════════════════
class LostmanAxe(BaseSkill):
    """Lostman melee — ฟันขวานโค้ง 120° (auto-tick)"""
    name = "Axe Swing"
    description = "ฟันขวานโค้งกว้างข้างหน้า (auto)"

    def __init__(self):
        super().__init__()
        self.radius = 110
        self.cone_deg = 120
        self.damage_mult = 1.2

    @property
    def cooldown(self):
        return max(0.5, 0.9 - (self.level - 1) * 0.1)

    def _on_upgrade(self):
        self.damage_mult += 0.2
        self.radius += 12

    def activate(self, game):
        px = game.player_pos[0] + 32
        py = game.player_pos[1] + 32
        dmg = game.player_stats.damage * self.damage_mult
        aim = math.atan2(game.mouse_dir[1], game.mouse_dir[0])
        half = math.radians(self.cone_deg / 2)
        _show_slash_vfx(game, px, py, self.radius,
                        math.degrees(aim), self.cone_deg / 2,
                        game.slash_textures)
        for enemy in list(game.enemies):
            ex = enemy.pos[0] + 20
            ey = enemy.pos[1] + 20
            dist = math.hypot(ex - px, ey - py)
            if dist > self.radius:
                continue
            ang = math.atan2(ey - py, ex - px)
            diff = abs((ang - aim + math.pi) % (2 * math.pi) - math.pi)
            if diff <= half:
                _hit_enemy(game, enemy, dmg)


# ═══════════════════════════════════════════════════════════
#  ─── MONKEY SKILLS ───────────────────────────────────────
# ═══════════════════════════════════════════════════════════

class PistolSkill(BaseSkill):
    """Monkey Skill 1 — ปืนพก auto-lock ศัตรูใกล้สุด (auto)"""
    name = "Pistol"
    description = "ยิงกระสุน auto-lock ศัตรูใกล้สุด"

    def __init__(self):
        super().__init__()
        self.damage_mult = 0.8
        self.bullet_count = 1
        self.bullet_speed = 520
        self.bullet_range = 720

    @property
    def cooldown(self):
        return max(0.25, 0.8 - (self.level - 1) * 0.13)

    def _on_upgrade(self):
        self.damage_mult += 0.2
        if self.level >= 3:
            self.bullet_count = 2
        if self.level >= 5:
            self.bullet_count = 3

    def activate(self, game):
        if not game.enemies:
            return
        px = game.player_pos[0] + 32
        py = game.player_pos[1] + 32
        dmg = game.player_stats.damage * self.damage_mult
        sorted_e = sorted(
            game.enemies,
            key=lambda e: math.hypot(px - (e.pos[0] + 20), py - (e.pos[1] + 20))
        )
        for enemy in sorted_e[:self.bullet_count]:
            _spawn_bullet(game, px, py,
                          enemy.pos[0] + 20, enemy.pos[1] + 20,
                          self.bullet_speed, self.bullet_range, dmg, [])


class ShotgunSkill(BaseSkill):
    """Monkey Skill 2 — Shotgun ยิงกระจายตามเมาส์ (auto)"""
    name = "Shotgun"
    description = "ยิงกระสุนกระจาย 5 นัดตามทิศที่เล็ง"

    def __init__(self):
        super().__init__()
        self.damage_mult = 0.6
        self.pellet_count = 5
        self.spread_deg = 22
        self.bullet_speed = 460
        self.bullet_range = 420

    @property
    def cooldown(self):
        return max(0.7, 1.5 - (self.level - 1) * 0.2)

    def _on_upgrade(self):
        self.damage_mult += 0.15
        if self.level % 2 == 0:
            self.pellet_count += 1

    def activate(self, game):
        px = game.player_pos[0] + 32
        py = game.player_pos[1] + 32
        dmg = game.player_stats.damage * self.damage_mult
        base_angle = math.atan2(game.mouse_dir[1], game.mouse_dir[0])
        spread = math.radians(self.spread_deg)
        half = (self.pellet_count - 1) / 2
        for i in range(self.pellet_count):
            offset = (i - half) / max(1, self.pellet_count - 1) * spread * 2
            ang = base_angle + offset
            tx = px + math.cos(ang) * 600
            ty = py + math.sin(ang) * 600
            _spawn_bullet(game, px, py, tx, ty,
                          self.bullet_speed, self.bullet_range, dmg, [])


class RPGSkill(StackSkill):
    """Monkey Skill 3 — จรวด RPG ระเบิด AoE เมื่อโดนศัตรู (manual LMB, stack)"""
    name = "RPG"
    description = "ยิงจรวดตามเมาส์ ระเบิด AoE เมื่อโดนศัตรู (Stack ×3)"

    STACK_RECHARGE = 5.0  # Monkey เร็วกว่า

    def __init__(self):
        super().__init__()
        self.direct_damage = 30
        self.splash_damage = 70
        self.splash_radius = 160
        self.bullet_speed = 400
        self.bullet_range = 950

    @property
    def recharge_time(self):
        return max(3.0, self.STACK_RECHARGE - (self.level - 1) * 0.5)

    def _on_upgrade(self):
        self.direct_damage += 10
        self.splash_damage += 20
        self.splash_radius += 15

    def activate(self, game):
        from game.projectile_widget import RPGRocket
        px = game.player_pos[0] + 32
        py = game.player_pos[1] + 32
        tx = px + game.mouse_dir[0] * 700
        ty = py + game.mouse_dir[1] * 700
        rocket = RPGRocket(
            start_pos=(px, py), target_pos=(tx, ty),
            speed=self.bullet_speed, proj_range=self.bullet_range,
            damage=self.direct_damage,
            splash_damage=self.splash_damage,
            splash_radius=self.splash_radius,
        )
        game.player_bullets.append(rocket)
        game.world_layout.add_widget(rocket)


# ═══════════════════════════════════════════════════════════
#  ─── MONKEY MELEE ────────────────────────────────────────
# ═══════════════════════════════════════════════════════════
class MonkeyCombo(BaseSkill):
    """Monkey melee — ต่อยเร็วหลายครั้ง combo (auto-tick)"""
    name = "Combo"
    description = "ต่อยรัวเร็วหลายครั้งในระยะใกล้ (auto)"

    def __init__(self):
        super().__init__()
        self.radius = 70
        self.hits = 3
        self.damage_mult = 0.5

    @property
    def cooldown(self):
        return max(0.15, 0.35 - (self.level - 1) * 0.05)

    def _on_upgrade(self):
        self.damage_mult += 0.1
        if self.level % 2 == 0:
            self.hits += 1

    def activate(self, game):
        px = game.player_pos[0] + 32
        py = game.player_pos[1] + 32
        dmg = game.player_stats.damage * self.damage_mult
        for i in range(self.hits):
            Clock.schedule_once(
                lambda dt, d=dmg, ppx=px, ppy=py: self._do_hit(game, ppx, ppy, d),
                i * 0.07
            )

    def _do_hit(self, game, px, py, dmg):
        for enemy in list(game.enemies):
            ex = enemy.pos[0] + 20
            ey = enemy.pos[1] + 20
            if math.hypot(ex - px, ey - py) <= self.radius:
                _hit_enemy(game, enemy, dmg)
        _show_punch_vfx(game, px, py, self.radius, game.slash_textures)


# ═══════════════════════════════════════════════════════════
#  REGISTRY
# ═══════════════════════════════════════════════════════════
CHAR_MELEE: Dict[str, Type[BaseSkill]] = {
    "PTae":    PtaePunch,
    "Lostman": LostmanAxe,
    "Monkey":  MonkeyCombo,
}

CHAR_DEFAULT_SKILLS: Dict[str, List[Type[BaseSkill]]] = {
    "PTae":    [DinoCircle, DinoSummon],
    "Lostman": [AxeThrow, BombTrap],
    "Monkey":  [PistolSkill, ShotgunSkill],
}

# Skill 3 per character (manual/stack)
CHAR_SKILL3: Dict[str, Type[StackSkill]] = {
    "PTae":    DinoPunch,
    "Lostman": WhirlSlash,
    "Monkey":  RPGSkill,
}

CHARACTER_SKILL_POOL: Dict[str, List[Type[BaseSkill]]] = {
    "PTae":    [DinoCircle, DinoSummon],
    "Lostman": [AxeThrow, BombTrap],
    "Monkey":  [PistolSkill, ShotgunSkill],
}

CHAR_SPEED_CAP: Dict[str, float] = {
    "PTae": 5.0, "Lostman": 7.0, "Monkey": 9.0,
}


# ═══════════════════════════════════════════════════════════
#  LEVEL UP — 4 ตัวเลือก
# ═══════════════════════════════════════════════════════════
def get_upgrade_choices(player_stats, count: int = 4) -> list:
    pool_auto = CHARACTER_SKILL_POOL.get(player_stats.name, [])
    s3_cls = CHAR_SKILL3.get(player_stats.name)

    owned_auto_types = {type(s) for s in player_stats.skills}

    # Auto skills S1/S2
    new_auto = [cls() for cls in pool_auto if cls not in owned_auto_types]
    upgradeable_auto = [s for s in player_stats.skills if s.level < s.max_level]

    # Skill 3
    new_s3 = []
    upgradeable_s3 = []
    if s3_cls:
        if player_stats.skill3 is None:
            new_s3 = [s3_cls()]
        elif player_stats.skill3.level < player_stats.skill3.max_level:
            upgradeable_s3 = [player_stats.skill3]

    # รวม pool (new ก่อน, upgrade ทีหลัง)
    pool_new = new_auto + new_s3
    pool_upg = upgradeable_auto + upgradeable_s3
    random.shuffle(pool_new)
    random.shuffle(pool_upg)

    skill_candidates = pool_new[:2]
    if len(skill_candidates) < 2:
        skill_candidates += pool_upg[:2 - len(skill_candidates)]
    random.shuffle(skill_candidates)
    skill_choices = skill_candidates[:2]

    stat_choices = [
        {"type": "stat", "stat": "hp",
         "label": "+20 HP Max", "description": "เพิ่ม HP สูงสุด 20",
         "skill": None, "is_new": False},
        {"type": "stat", "stat": "damage",
         "label": "+3 ATK", "description": "เพิ่มดาเมจพื้นฐาน 3",
         "skill": None, "is_new": False},
    ]
    spd_cap = CHAR_SPEED_CAP.get(player_stats.name, 10.0)
    if player_stats.speed < spd_cap:
        stat_choices.append({
            "type": "stat", "stat": "speed",
            "label": "+0.25 SPD",
            "description": f"เพิ่มความเร็ว 0.25 (cap {spd_cap})",
            "skill": None, "is_new": False,
        })
    random.shuffle(stat_choices)
    stat_choices = stat_choices[:2]

    skill_dicts = []
    for skill in skill_choices:
        is_s3 = bool(s3_cls and isinstance(skill, s3_cls))
        is_new = (skill not in player_stats.skills) and (skill is not player_stats.skill3)
        label = f"[NEW] {skill.name}" if is_new else f"[Lv{skill.level}→{skill.level + 1}] {skill.name}"
        skill_dicts.append({
            "type": "skill", "skill": skill,
            "label": label, "description": skill.description,
            "is_new": is_new, "is_s3": is_s3,
        })

    combined = skill_dicts + stat_choices
    random.shuffle(combined)
    return combined[:count]


# ═══════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════
def _hit_enemy(game, enemy, dmg: float):
    if hasattr(enemy, "take_damage"):
        enemy.take_damage(dmg)
    else:
        enemy.hp -= dmg

    if enemy.hp > 0:
        return
    if enemy in game.enemies:
        game.enemies.remove(enemy)
        
    # เช็คว่าเป็นบอสหรือไม่ เพื่อดรอประเบิดตัวเอง
    is_any_boss = False
    if hasattr(game, "boss") and enemy is game.boss:
        game.boss = None
        is_any_boss = True
    if hasattr(game, "big_boss") and enemy is game.big_boss:
        game.big_boss = None
        is_any_boss = True
        
    if is_any_boss:
        from game.projectile_widget import BossBombWidget
        bx = enemy.pos[0] + (enemy.enemy_size[0]/2 if hasattr(enemy, 'enemy_size') else 20) - 32
        by = enemy.pos[1] + (enemy.enemy_size[1]/2 if hasattr(enemy, 'enemy_size') else 20) - 32
        bomb = BossBombWidget(
            pos=(bx, by),
            fuse=3.0,
            damage=300, # ดาเมจมหาศาล
            radius=250, # รัศมีกว้าง
            game=game
        )
        game.world_layout.add_widget(bomb)

        # 🌟 Summon Stalkers (3-6 ตัว) เมื่อบอสตาย
        import random
        from game.enemy_widget import EnemyWidget
        stalker_count = random.randint(3, 6)
        for _ in range(stalker_count):
            # สุ่มตำแหน่งกระจายรอบๆ จุดที่บอสตายเล็กน้อย
            sx = enemy.pos[0] + random.uniform(-60, 60)
            sy = enemy.pos[1] + random.uniform(-60, 60)
            st = EnemyWidget(spawn_pos=(sx, sy), enemy_type="stalker")
            st.game = game
            # ใส่ Wave scaling ให้ด้วยไม่งั้นเลเวลสูงๆ จะตัวบางเกินไป
            if hasattr(game.wave_manager, "_apply_wave_scaling"):
                game.wave_manager._apply_wave_scaling(st)
            game.enemies.append(st)
            game.world_layout.add_widget(st)

    if enemy.parent:
        game.world_layout.remove_widget(enemy)
    game.spawn_exp_orb(enemy.pos)
    
    # ให้เมธอด spawn_drop_item เป็นคนสุ่มความน่าจะเป็นเอง ไม่ต้องสุ่มซ้ำซ้อน
    game.spawn_drop_item(enemy.pos)
    
    if hasattr(game, "hud") and game.hud:
        game.hud.update_enemy_count(len(game.enemies))
    if hasattr(game, "gain_exp"):
        game.gain_exp(10)


def _explode_bomb(game, bomb):
    """เรียกตอนระเบิด bomb — AoE damage + remove widget"""
    if not bomb.parent:
        return
    px = bomb.pos[0] + 16
    py = bomb.pos[1] + 16
    _show_aoe_vfx(game, px, py, bomb.radius)
    for enemy in list(game.enemies):
        ex = enemy.pos[0] + 20
        ey = enemy.pos[1] + 20
        if math.hypot(ex - px, ey - py) <= bomb.radius:
            _hit_enemy(game, enemy, bomb.damage)
    game.world_layout.remove_widget(bomb)


def _spawn_bullet(game, sx, sy, tx, ty, speed, rng, dmg, anim_frames=None):
    from game.projectile_widget import PlayerBullet
    b = PlayerBullet(
        start_pos=(sx, sy), target_pos=(tx, ty),
        speed=speed, proj_range=rng, damage=dmg,
        anim_frames=anim_frames or [],
    )
    game.player_bullets.append(b)
    game.world_layout.add_widget(b)


def _show_slash_vfx(game, px, py, radius, angle_deg, spread, anim_frames=None):
    if anim_frames:
        _play_slash_circle_vfx(game, px, py, radius, anim_frames, duration=0.25)
        return
    ig = InstructionGroup()
    ig.add(Color(1, 1, 0, 0.45))
    ka = 90 - angle_deg
    ig.add(Ellipse(pos=(px - radius, py - radius), size=(radius * 2, radius * 2),
                   angle_start=ka - spread, angle_end=ka + spread))
    game.world_layout.canvas.add(ig)
    Clock.schedule_once(lambda dt: game.world_layout.canvas.remove(ig), 0.12)


def _show_aoe_vfx(game, px, py, radius, anim_frames=None):
    if anim_frames:
        _play_vfx_sprite(game, px, py, radius * 2.2, radius * 2.2, anim_frames, 0.2)
        return
    ig = InstructionGroup()
    ig.add(Color(1, 0.2, 0.2, 0.4))
    ig.add(Ellipse(pos=(px - radius, py - radius), size=(radius * 2, radius * 2)))
    game.world_layout.canvas.add(ig)
    Clock.schedule_once(lambda dt: game.world_layout.canvas.remove(ig), 0.18)


def _show_cone_vfx(game, px, py, radius, angle_deg, spread_deg, anim_frames=None):
    if anim_frames:
        _play_vfx_sprite(game, px, py, radius * 2, radius * 2, anim_frames, 0.15)
        return
    ig = InstructionGroup()
    ig.add(Color(1, 0.55, 0.05, 0.55))
    ka = 90 - angle_deg
    half = spread_deg / 2
    ig.add(Ellipse(pos=(px - radius, py - radius), size=(radius * 2, radius * 2),
                   angle_start=ka - half, angle_end=ka + half))
    game.world_layout.canvas.add(ig)
    Clock.schedule_once(lambda dt: game.world_layout.canvas.remove(ig), 0.12)


def _show_punch_vfx(game, px, py, radius, anim_frames=None):
    if anim_frames:
        _play_vfx_sprite(game, px, py, radius * 2, radius * 2, anim_frames, 0.08)
        return
    ig = InstructionGroup()
    ig.add(Color(1, 1, 0, 0.6))
    ig.add(Ellipse(pos=(px - radius, py - radius), size=(radius * 2, radius * 2)))
    game.world_layout.canvas.add(ig)
    Clock.schedule_once(lambda dt: game.world_layout.canvas.remove(ig), 0.08)


def _draw_orbit_indicators(game, positions, angle):
    """วาดจุดเล็กๆ แสดงตำแหน่งไดโน orbit"""
    ig = InstructionGroup()
    ig.add(Color(0.3, 1.0, 0.4, 0.8))
    for (ox, oy) in positions:
        ig.add(Ellipse(pos=(ox - 10, oy - 10), size=(20, 20)))
    game.world_layout.canvas.add(ig)
    Clock.schedule_once(lambda dt: game.world_layout.canvas.remove(ig), 0.032)


def _play_vfx_sprite(game, cx, cy, w, h, frames, duration=0.25):
    textures = []
    for path in frames:
        try:
            textures.append(CoreImage(path).texture)
        except Exception:
            continue
    if not textures:
        return
    ft = duration / len(textures)
    ig = InstructionGroup()
    ig.add(Color(1, 1, 1, 1))
    rect = Rectangle(texture=textures[0], pos=(cx - w / 2, cy - h / 2), size=(w, h))
    ig.add(rect)
    game.world_layout.canvas.add(ig)
    idx = [1]

    def _next(dt):
        if idx[0] >= len(textures):
            game.world_layout.canvas.remove(ig)
            return
        rect.texture = textures[idx[0]]
        idx[0] += 1
        Clock.schedule_once(_next, ft)

    Clock.schedule_once(_next, ft)


def _play_slash_circle_vfx(game, cx, cy, radius, frames, duration=0.25, blades=6):
    import math as _m
    textures = []
    for path in frames:
        try:
            textures.append(CoreImage(path).texture)
        except Exception:
            continue
    if not textures:
        return
    bs = max(48, min(96, radius * 0.9))
    ig = InstructionGroup()
    ig.add(Color(1, 1, 1, 1))
    rects, base_angles = [], []
    for i in range(blades):
        ang = 2 * _m.pi * i / blades
        base_angles.append(ang)
        r = Rectangle(
            texture=textures[0],
            pos=(cx + _m.cos(ang) * radius - bs / 2,
                 cy + _m.sin(ang) * radius - bs / 2),
            size=(bs, bs),
        )
        rects.append(r)
        ig.add(r)
    game.world_layout.canvas.add(ig)
    steps = max(6, int(duration * 20))
    st = duration / steps
    state = {"step": 0, "frame": 0}

    def _step(dt):
        if state["step"] >= steps:
            game.world_layout.canvas.remove(ig)
            return
        ao = 2 * _m.pi * (state["step"] / steps)
        tex = textures[state["frame"]]
        for ba, rect in zip(base_angles, rects):
            a = ba + ao
            rect.pos = (cx + _m.cos(a) * radius - bs / 2,
                        cy + _m.sin(a) * radius - bs / 2)
            rect.texture = tex
        state["step"] += 1
        if state["step"] % max(1, steps // len(textures)) == 0:
            state["frame"] = (state["frame"] + 1) % len(textures)
        Clock.schedule_once(_step, st)

    Clock.schedule_once(_step, st)