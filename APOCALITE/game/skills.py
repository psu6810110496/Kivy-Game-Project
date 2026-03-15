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
from game.game_settings import settings
from game.utils import resolve_path, get_frames

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
        if not getattr(game, "enemies", []):
            return
            
        self._timer -= dt
        if self._timer <= 0:
            self.activate(game)
            self._timer = self.cooldown

    def activate(self, game): pass
    def manual_activate(self, game) -> bool: return False
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

    _TEXTURES = None
    _ORBIT_TEXTURES = None

    @classmethod
    def _load(cls):
        if cls._TEXTURES is None:
            import os
            cls._TEXTURES = []
            cls._ORBIT_TEXTURES = []
            # base: c:\Users\Nicky\Kivy-Game-Project
            base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            # Load Dinosaurs (Skill 1)
            for i in range(1, 5):
                path = resolve_path(f"assets/PTae/skill1/aoeptae{i:02d}.png")
                if path:
                    try: cls._TEXTURES.append(CoreImage(path).texture)
                    except: pass
            
            # Load Orbit Aura (lo)
            # frame_00_delay-0.02s.png ถึง frame_13_delay-0.02s.png
            for i in range(14):
                path = resolve_path(f"assets/PTae/lo/frame_{i:02d}_delay-0.02s.png")
                if path:
                    try: cls._ORBIT_TEXTURES.append(CoreImage(path).texture)
                    except: pass
            print(f"[DinoCircle] Loaded {len(cls._TEXTURES)} dinos and {len(cls._ORBIT_TEXTURES)} orbit aura frames")

    def __init__(self):
        super().__init__()
        self.orbit_radius = 40
        self.dino_count = 1
        self.damage_mult = 1.5
        self.orbit_speed = 3.0       # rad/s
        self._orbit_angle = 0.0
        self._hit_cooldowns: dict = {}  # enemy_id → cooldown
        self._frame = 0
        self._at = 0.0
        self._orbit_frame = 0
        self._orbit_at = 0.0

    @property
    def cooldown(self):
        # ไม่ใช้ cooldown เหมือนสกิลอื่น — tick ทุก frame เพื่ออัปเดต orbit
        return 0.016  # ~60fps

    def _on_upgrade(self):
        # เพิ่มจำนวนไดโนให้ตันที่ 15 ตัวที่เลเวล 25
        self.dino_count = 1 + (self.level // 2) + (self.level // 12)
        self.damage_mult += 0.3
        self.orbit_radius += 2.8

    def tick(self, dt: float, game):
        """อัปเดต orbit angle และตรวจ collision"""
        if not getattr(game, "enemies", []):
            return
            
        self._load()
        
        # [Aesthetic] Play looping skill sound
        from game.sound_manager import sound_manager
        sound_manager.play_loop_sfx("dino_circle_loop", volume=settings.sfx_volume * 0.4)
        
        self._orbit_angle += self.orbit_speed * dt
        if self._orbit_angle > 2 * math.pi:
            self._orbit_angle -= 2 * math.pi
            
        # [Animation] อัปเดตเฟรมไดโน
        if self._TEXTURES:
            self._at += dt
            if self._at >= 0.08:
                self._at = 0.0
                self._frame = (self._frame + 1) % len(self._TEXTURES)
                
        # [Animation] อัปเดตเฟรม Orbit Aura
        if self._ORBIT_TEXTURES:
            self._orbit_at += dt
            if self._orbit_at >= 0.05:
                self._orbit_at = 0.0
                self._orbit_frame = (self._orbit_frame + 1) % len(self._ORBIT_TEXTURES)

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

            # 🛡️ Proximity Protection: ตีมอนที่อยู่ชิดตัวผู้เล่นมากเกินไป (ระยะประชิด 60px)
            dist_to_player = math.hypot(ec_x - px, ec_y - py)
            if dist_to_player < 60:
                _hit_enemy(game, enemy, dmg)
                self._hit_cooldowns[eid] = 0.5
                continue

            for (ox, oy) in positions:
                if math.hypot(ox - ec_x, oy - ec_y) < 45:
                    _hit_enemy(game, enemy, dmg)
                    self._hit_cooldowns[eid] = 0.5  # hit cooldown 0.5s per enemy
                    break

        # วาด dino indicators และวงกลมป้องกันชั้นใน
        # วาด dino indicators และวงกลมป้องกันชั้นใน
        _draw_orbit_indicators(game, positions, self._orbit_angle, inner_radius=60, 
                               textures=self._TEXTURES, frame=self._frame,
                               orbit_textures=self._ORBIT_TEXTURES, orbit_frame=self._orbit_frame)

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
        
        # [Aesthetic] Play summon sound
        from game.sound_manager import sound_manager
        sound_manager.play_sfx("dino_summon")

        from game.projectile_widget import HomingDino
        px = game.player_pos[0] + 32
        py = game.player_pos[1] + 32
        dmg = game.player_stats.damage * self.damage_mult
        count = min(7, self.level)  # ลดจำนวนสูงสุดลงครึ่งหนึ่ง (เดิม 15)
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
        # [Aesthetic] Play activation sound (low volume as it's loud/meme)
        from game.sound_manager import sound_manager
        sound_manager.play_sfx("dino_beam", volume=settings.sfx_volume * 0.6)

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
            # ตีได้ถ้าอยู่ในกรวย หรือถ้าอยู่ชิดตัวมาก (dist <= 45)
            if dist <= 45 or diff <= half:
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
        
        # [Aesthetic] Play throw sound
        from game.sound_manager import sound_manager
        sound_manager.play_sfx("lostman_throw")
        
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


class BombTrap(StackSkill):
    """Lostman Skill 3 — วางระเบิด manual LMB, stack×3"""
    name = "Bomb Trap"
    description = "วางระเบิด AoE พลังทำลายสูง (manual LMB)"

    def __init__(self):
        super().__init__()
        self.splash_damage_mult = 6.0
        self.splash_radius = 180
        self.fuse_time = 2.0
        self.bomb_count = 1

    @property
    def recharge_time(self):
        return max(3.0, 7.0 - (self.level - 1) * 0.5)

    def _on_upgrade(self):
        self.splash_damage_mult += 1.5
        self.splash_radius += 20
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
            # วางกระจายรอบตัว
            angle = (i * 2 * math.pi / max(1, self.bomb_count))
            offset_dist = 40 if self.bomb_count > 1 else 0
            bx = px + math.cos(angle) * offset_dist
            by = py + math.sin(angle) * offset_dist
            
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


class WhirlSlash(BaseSkill):
    """Lostman Skill 2 — ฟันขวานวงใหญ่รอบตัว (auto)"""
    name = "Whirl Slash"
    description = "ฟันขวานวงใหญ่รอบตัว knockback (auto)"

    def __init__(self):
        super().__init__()
        self.radius = 90
        self.damage_mult = 3.5
        self.knockback = 120
        self.anim_frames = [
            "assets/Lostman/skill1/axe_hit1.png",
            "assets/Lostman/skill1/axe_hit2.png",
            "assets/Lostman/skill1/axe_hit3.png",
            "assets/Lostman/skill1/axe_hit4.png",
        ]

    @property
    def cooldown(self):
        return max(2.5, 5.0 - (self.level - 1) * 0.4)

    def _on_upgrade(self):
        self.radius = min(120, self.radius + 10)
        self.damage_mult += 0.5
        self.knockback += 20

    def activate(self, game):
        px = game.player_pos[0] + 32
        py = game.player_pos[1] + 32
        dmg = game.player_stats.damage * self.damage_mult

        # [Aesthetic] Play axe sound
        from game.sound_manager import sound_manager
        sound_manager.play_sfx("lostman_axe")

        _show_slash_vfx(game, px, py, self.radius, 0, 360, self.anim_frames)

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

        # [Aesthetic] Play axe sound
        from game.sound_manager import sound_manager
        sound_manager.play_sfx("lostman_axe")

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
            # ตีได้ถ้าอยู่ในขอบเขต หรือถ้าอยู่ชิดตัวมาก (dist <= 45)
            if dist <= 45 or diff <= half:
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
        self.anim_frames = [
            "assets/Monkey/shoot/bullets1.png",
            "assets/Monkey/shoot/bullets2.png",
        ]

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
                          self.bullet_speed, self.bullet_range, dmg, self.anim_frames)


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
        self.anim_frames = [
            "assets/Monkey/shoot/bullets1.png",
            "assets/Monkey/shoot/bullets2.png",
        ]

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
                          self.bullet_speed, self.bullet_range, dmg, self.anim_frames)


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
    "Lostman": [AxeThrow, WhirlSlash],
    "Monkey":  [PistolSkill, ShotgunSkill],
}

# Skill 3 per character (manual/stack)
CHAR_SKILL3: Dict[str, Type[StackSkill]] = {
    "PTae":    DinoPunch,
    "Lostman": BombTrap,
    "Monkey":  RPGSkill,
}

CHARACTER_SKILL_POOL: Dict[str, List[Type[BaseSkill]]] = {
    "PTae":    [DinoCircle, DinoSummon],
    "Lostman": [AxeThrow, WhirlSlash],
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
        spd_inc = 1.0 if player_stats.name == "PTae" else 0.5
        stat_choices.append({
            "type": "stat", "stat": "speed",
            "val": spd_inc,
            "label": f"+{spd_inc} SPD",
            "description": f"เพิ่มความเร็ว {spd_inc} (cap {spd_cap})",
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
    if not enemy or enemy.is_dead:
        return
        
    # [Aesthetic] Play hit sound (quieter than melee)
    from game.sound_manager import sound_manager
    sfx_name = "lostman_hit" if game.player_stats.name == "Lostman" else "enemy_hit"
    sound_manager.play_sfx(sfx_name, volume=settings.sfx_volume * 0.4)

    if hasattr(enemy, "take_damage"):
        enemy.take_damage(dmg)
    else:
        enemy.hp -= dmg

    # 🌟 แสดงตัวเลขดาเมจบนหัว
    if settings.show_damage_numbers:
        _show_damage_number(game, enemy.pos[0] + 15, enemy.pos[1] + 35, dmg)

    if enemy.hp > 0:
        return

    if enemy in game.enemies:
        game.enemies.remove(enemy)
        enemy.is_dead = True
        
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


def _show_damage_number(game, x, y, damage):
    """สร้าง Label ดาเมจลอยขึ้นบนหัว"""
    from kivy.uix.label import Label
    from kivy.animation import Animation
    
    lbl = Label(
        text=str(int(damage)),
        font_size=20,
        bold=True,
        color=(1, 0.2, 0.2, 1),
        pos=(x, y),
        size_hint=(None, None),
        size=(40, 40)
    )
    game.world_layout.add_widget(lbl)
    
    # Animation ลอยขึ้นและหายไป
    anim = Animation(y=y + 80, opacity=0, duration=0.8, transition='out_quad')
    anim.bind(on_complete=lambda *args: game.world_layout.remove_widget(lbl) if lbl.parent else None)
    anim.start(lbl)


def _explode_bomb(game, bomb):
    """เรียกตอนระเบิด bomb — AoE damage + remove widget"""
    if not bomb.parent:
        return
    px = bomb.pos[0] + 16
    py = bomb.pos[1] + 16
    
    # [Aesthetic] Play explosion sound
    from game.sound_manager import sound_manager
    sound_manager.play_sfx("lostman_bomb_explosion")
    
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


EXPLOSION_ANIM_FRAMES = []

def _load_explosion_frames():
    global EXPLOSION_ANIM_FRAMES
    if not EXPLOSION_ANIM_FRAMES:
        for i in range(1, 13):
            path = resolve_path(f"assets/enemy/boss/{i}.png")
            if path:
                EXPLOSION_ANIM_FRAMES.append(path)
    return EXPLOSION_ANIM_FRAMES

def _show_aoe_vfx(game, px, py, radius, anim_frames=None):
    if not anim_frames:
        anim_frames = _load_explosion_frames()
        
    if anim_frames:
        # Increase duration slightly for 12 frames
        _play_vfx_sprite(game, px, py, radius * 2.2, radius * 2.2, anim_frames, 0.45)
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
        _play_vfx_sprite(game, px, py, radius * 2, radius * 2, anim_frames, 0.20)
        return
    ig = InstructionGroup()
    ig.add(Color(1, 1, 0, 0.6))
    ig.add(Ellipse(pos=(px - radius, py - radius), size=(radius * 2, radius * 2)))
    game.world_layout.canvas.add(ig)
    Clock.schedule_once(lambda dt: game.world_layout.canvas.remove(ig), 0.08)


def _draw_orbit_indicators(game, positions, angle, inner_radius=0, textures=None, frame=0, 
                           orbit_textures=None, orbit_frame=0):
    """วาดจุดเล็กๆ แสดงตำแหน่งไดโน orbit และวงกลมป้องกันด้านใน"""
    ig = InstructionGroup()
    
    # วงกลมป้องกันชั้นใน (Orbit Aura)
    if inner_radius > 0:
        if orbit_textures:
            # ใช้สีขาวเข้มขึ้นตาม texture (ปรับ alpha ให้เห็นชัด)
            ig.add(Color(1, 1, 1, 1)) # [Fix] Revert to original bright colors
            tex = orbit_textures[orbit_frame % len(orbit_textures)]
            # [Fix] Reduce Aura size multiplier from 3.5 to 3.0
            aura_size = inner_radius * 3.0
            ig.add(Rectangle(texture=tex, 
                             pos=(game.player_pos[0]+32 - aura_size/2, game.player_pos[1]+32 - aura_size/2), 
                             size=(aura_size, aura_size)))
        else:
            ig.add(Color(0.2, 0.9, 0.3, 0.4))
            ig.add(Ellipse(pos=(game.player_pos[0]+32 - inner_radius, game.player_pos[1]+32 - inner_radius), 
                           size=(inner_radius * 2, inner_radius * 2)))

    # จุดไดโนรอบนอก
    if textures:
        # [Fix] Revert to original bright colors
        ig.add(Color(1, 1, 1, 1))
        tex = textures[frame % len(textures)]
        for (ox, oy) in positions:
            # [Fix] Reduced size from 110 to 64
            sz = 64
            ig.add(Rectangle(texture=tex, pos=(ox - sz/2, oy - sz/2), size=(sz, sz)))
    else:
        ig.add(Color(0.2, 0.6, 0.2, 0.9))
        for (ox, oy) in positions:
            ig.add(Ellipse(pos=(ox - 20, oy - 20), size=(40, 40)))
        
    game.world_layout.canvas.add(ig)
    Clock.schedule_once(lambda dt: game.world_layout.canvas.remove(ig), 0.032)


def _play_vfx_sprite(game, cx, cy, w, h, frames, duration=0.25):
    textures = []
    for item in frames:
        # Check if item is already a texture (e.g. from engine.py self.slash_textures)
        if hasattr(item, 'width') and hasattr(item, 'height'):
            textures.append(item)
            continue
        try:
            if isinstance(item, str):
                textures.append(CoreImage(item).texture)
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
    for item in frames:
        if hasattr(item, 'width') and hasattr(item, 'height'):
            textures.append(item)
            continue
        try:
            if isinstance(item, str):
                textures.append(CoreImage(item).texture)
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