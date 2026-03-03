"""
game/skills.py
ระบบสกิลทั้งหมด — ออโต้ทุกตัว ทำงานผ่าน GameScreen

สกิลที่มี:
  AxeTSkill    — กระสุนยิงตรงหาศัตรูใกล้สุด (Magic Bullet)
  SlashSkill   — ฟันรอบตัว (arc)
  AoESkill     — ระเบิดรอบตัว

แต่ละสกิลมี .tick(dt, game) เรียกทุก frame จาก engine
และมี .upgrade() เรียกตอน level up
"""

import math


# ══════════════════════════════════════════════════════
#  BASE
# ══════════════════════════════════════════════════════
class BaseSkill:
    name = "???"
    description = "???"
    max_level = 5

    def __init__(self):
        self.level = 1
        self._timer = 0.0

    def tick(self, dt, game):
        self._timer -= dt
        if self._timer <= 0:
            self._timer = self.cooldown
            self.activate(game)

    def activate(self, game):
        raise NotImplementedError

    def upgrade(self):
        """เพิ่ม level และคืนค่า True ถ้าอัปได้"""
        if self.level < self.max_level:
            self.level += 1
            self._on_upgrade()
            return True
        return False

    def _on_upgrade(self):
        pass

    @property
    def cooldown(self):
        raise NotImplementedError

    def summary(self):
        return f"{self.name} Lv{self.level} — {self.description}"


# ══════════════════════════════════════════════════════
#  1. BULLET — กระสุนยิงตรง
# ══════════════════════════════════════════════════════
class AxeTSkill(BaseSkill):
    name = "Axe Torrent"
    description = "ยิงขวานติดตามศัตรูใกล้ที่สุดแบบอัตโนมัติ"

    def __init__(self):
        super().__init__()
        self.damage_mult = 1.0
        self.bullet_count = 1
        self.bullet_speed = 400
        self.bullet_range = 600
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
        # Lv1=1.5s → Lv5=0.7s
        return max(0.7, 1.5 - (self.level - 1) * 0.2)

    def _on_upgrade(self):
        if self.level % 2 == 0:
            self.bullet_count += 1   # Lv2, Lv4 → +1 กระสุน
        self.damage_mult += 0.25     # ทุก level +25% damage

    def activate(self, game):
        if not game.enemies:
            return
        px = game.player_pos[0] + 32
        py = game.player_pos[1] + 32
        dmg = game.player_stats.damage * self.damage_mult

        sorted_enemies = sorted(
            game.enemies,
            key=lambda e: math.hypot(px - (e.pos[0] + 20), py - (e.pos[1] + 20))
        )
        targets = sorted_enemies[:self.bullet_count]

        for enemy in targets:
            tx, ty = enemy.pos[0] + 20, enemy.pos[1] + 20
            _spawn_bullet(
                game, px, py, tx, ty,
                self.bullet_speed, self.bullet_range,
                dmg, self.anim_frames          # ✅ ส่ง anim_frames
            )


# ══════════════════════════════════════════════════════
#  2. SLASH — ฟันรอบตัว
# ══════════════════════════════════════════════════════
class SlashSkill(BaseSkill):
    name = "Whirl Slash"
    description = "ฟันรอบตัว สร้างความเสียหายศัตรูที่อยู่ประชิด"

    def __init__(self):
        super().__init__()
        self.radius = 120
        self.damage_mult = 5
        self.arc = 360
        self.knockback = 50
        self.anim_frames = [
            "assets/Lostman/skill1/axe_hit1.png",
            "assets/Lostman/skill1/axe_hit2.png",
            "assets/Lostman/skill1/axe_hit3.png",
            "assets/Lostman/skill1/axe_hit4.png",
        ]

    @property
    def cooldown(self):
        # Lv1=2.0s → Lv5=1.0s
        return max(1.0, 2.0 - (self.level - 1) * 0.25)

    def _on_upgrade(self):
        self.radius += 15
        self.damage_mult += 0.2
        if self.level == 3:
            self.knockback += 30

    def activate(self, game):
        px = game.player_pos[0] + 32
        py = game.player_pos[1] + 32
        dmg = game.player_stats.damage * self.damage_mult
        aim_angle = math.degrees(math.atan2(game.mouse_dir[1], game.mouse_dir[0]))

        _show_slash_vfx(game, px, py, self.radius, aim_angle, self.arc / 2,
                        self.anim_frames)     # ✅ ส่ง anim_frames

        for enemy in list(game.enemies):
            ex, ey = enemy.pos[0] + 20, enemy.pos[1] + 20
            dist = math.hypot(ex - px, ey - py)
            if dist > self.radius:
                continue
            enemy_angle = math.degrees(math.atan2(ey - py, ex - px))
            diff = (enemy_angle - aim_angle) % 360
            if diff > 180:
                diff -= 360
            if self.arc < 360 and abs(diff) > self.arc / 2:
                continue
            _hit_enemy(game, enemy, dmg)
            if dist > 0:
                kx = (ex - px) / dist * self.knockback
                ky = (ey - py) / dist * self.knockback
                enemy.pos = (enemy.pos[0] + kx, enemy.pos[1] + ky)


# ══════════════════════════════════════════════════════
#  3. AOE — ระเบิดรอบตัว
# ══════════════════════════════════════════════════════
class AoESkill(BaseSkill):
    name = "Nova Burst"
    description = "ชาร์จพลังระเบิดรอบตัว กวาดศัตรูทั้งหมดในรัศมี"

    def __init__(self):
        super().__init__()
        self.radius = 180
        self.damage_mult = 1.2
        self.knockback = 80
        self.anim_frames = [
            "assets/Lostman/skill3/c4_trap1.png",
            "assets/Lostman/skill3/c4_trap2.png",
            "assets/Lostman/skill3/c4_trap3.png",
            "assets/Lostman/skill3/c4_trap4.png",
        ]

    @property
    def cooldown(self):
        # Lv1=4.0s → Lv5=2.0s
        return max(2.0, 4.0 - (self.level - 1) * 0.5)

    def _on_upgrade(self):
        self.radius += 20
        self.damage_mult += 0.3
        self.knockback += 20

    def activate(self, game):
        px = game.player_pos[0] + 32
        py = game.player_pos[1] + 32
        dmg = game.player_stats.damage * self.damage_mult

        _show_aoe_vfx(game, px, py, self.radius,
                      self.anim_frames)        # ✅ ส่ง anim_frames

        for enemy in list(game.enemies):      # ✅ ลบ for-targets ที่ค้างอยู่ใน AoE
            ex, ey = enemy.pos[0] + 20, enemy.pos[1] + 20
            dist = math.hypot(ex - px, ey - py)
            if dist <= self.radius:
                _hit_enemy(game, enemy, dmg)
                if dist > 0:
                    kx = (ex - px) / dist * self.knockback
                    ky = (ey - py) / dist * self.knockback
                    enemy.pos = (enemy.pos[0] + kx, enemy.pos[1] + ky)


# ══════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ══════════════════════════════════════════════════════
def _hit_enemy(game, enemy, dmg):
    """ทำ damage ศัตรู และลบออกถ้า HP หมด"""
    enemy.hp -= dmg
    if enemy.hp <= 0:
        if enemy in game.enemies:
            game.enemies.remove(enemy)
        if enemy.parent:
            game.world_layout.remove_widget(enemy)
        game.gain_exp(10)


def _spawn_bullet(game, sx, sy, tx, ty, speed, rng, dmg, anim_frames=None):
    """สร้างกระสุนพร้อม animation และเพิ่มเข้า world"""
    try:
        from game.projectile_widget import PlayerBullet
        b = PlayerBullet(
            start_pos=(sx, sy),
            target_pos=(tx, ty),
            speed=speed,
            proj_range=rng,
            damage=dmg,
            anim_frames=anim_frames or [],    # ✅ ส่ง frames เสมอ
        )
        game.player_bullets.append(b)
        game.world_layout.add_widget(b)
    except ImportError:
        pass


def _show_slash_vfx(game, px, py, radius, angle_deg, spread, anim_frames=None):
    """
    เล่น sprite animation รอบตัว ถ้ามี anim_frames
    แล้ว fallback วาด arc สีเหลืองถ้าไม่มีรูป
    """
    from kivy.clock import Clock

    # ── Sprite animation: วงกลมรอบตัว ─────────────────
    if anim_frames:
        _play_slash_circle_vfx(game, px, py, radius, anim_frames, duration=0.25)
        return

    # ── Fallback: arc สีเหลือง ────────────────────────
    from kivy.graphics import Color, Ellipse, InstructionGroup
    kivy_angle = 90 - angle_deg
    ig = InstructionGroup()
    ig.add(Color(1, 1, 0, 0.45))
    ig.add(Ellipse(
        pos=(px - radius, py - radius),
        size=(radius * 2, radius * 2),
        angle_start=kivy_angle - spread,
        angle_end=kivy_angle + spread,
    ))
    game.world_layout.canvas.add(ig)
    Clock.schedule_once(lambda dt: game.world_layout.canvas.remove(ig), 0.12)


def _show_aoe_vfx(game, px, py, radius, anim_frames=None):
    """
    เล่น sprite animation ถ้ามี anim_frames
    แล้ว fallback วาดวงกลมสีแดงถ้าไม่มีรูป
    """
    from kivy.clock import Clock

    # ── Sprite animation (ระเบิดกลางวง) ───────────────
    if anim_frames:
        # ให้ขนาดวิชวลใหญ่กว่ารัศมีเล็กน้อย แต่ไม่ล้นจอเกินไป
        size = radius * 2.2
        _play_vfx_sprite(game, px, py, size, size, anim_frames,
                         duration=0.2)
        return

    # ── Fallback: วงกลมสีแดง ──────────────────────────
    from kivy.graphics import Color, Ellipse, InstructionGroup
    ig = InstructionGroup()
    ig.add(Color(1, 0.2, 0.2, 0.4))
    ig.add(Ellipse(pos=(px - radius, py - radius),
                   size=(radius * 2, radius * 2)))
    game.world_layout.canvas.add(ig)
    Clock.schedule_once(lambda dt: game.world_layout.canvas.remove(ig), 0.15)


def _play_vfx_sprite(game, cx, cy, w, h, frames, duration=0.25):
    """
    เล่น sprite sheet แบบ frame-by-frame ด้วย Rectangle บน world_layout.canvas
    cx, cy = จุดกึ่งกลาง (center)
    w, h   = ขนาดที่วาด
    frames = list ของ path รูป
    duration = เวลารวมทั้งหมด (วินาที)
    """
    from kivy.clock import Clock
    from kivy.core.image import Image as CoreImage
    from kivy.graphics import InstructionGroup, Rectangle, Color

    if not frames:
        return

    # โหลด texture ล่วงหน้าเพื่อให้เปลี่ยนเฟรมได้เร็ว
    textures = []
    for path in frames:
        try:
            textures.append(CoreImage(path).texture)
        except Exception:
            # ถ้าโหลดรูปไม่ได้ ให้ข้าม (จะเหลือเฉพาะรูปที่โหลดได้)
            continue

    if not textures:
        return

    frame_time = duration / len(textures)

    ig = InstructionGroup()
    ig.add(Color(1, 1, 1, 1))
    rect = Rectangle(
        texture=textures[0],
        pos=(cx - w / 2, cy - h / 2),
        size=(w, h),
    )
    ig.add(rect)
    game.world_layout.canvas.add(ig)

    frame_index = [1]

    def _next_frame(dt):
        if frame_index[0] >= len(textures):
            # เล่นจบ → ลบออกจาก canvas
            game.world_layout.canvas.remove(ig)
            return
        rect.texture = textures[frame_index[0]]
        frame_index[0] += 1
        Clock.schedule_once(_next_frame, frame_time)

    Clock.schedule_once(_next_frame, frame_time)


def _play_slash_circle_vfx(game, cx, cy, radius, frames, duration=0.25, blades=6):
    """
    เอฟเฟกต์ Slash ฟีลตีรอบตัวเป็นวงกลม:
    - สร้าง "ใบมีด" หลายอันล้อมรอบผู้เล่น
    - หมุนรอบตัวภายในช่วง duration
    """
    from kivy.clock import Clock
    from kivy.core.image import Image as CoreImage
    from kivy.graphics import InstructionGroup, Rectangle, Color
    import math as _m

    if not frames:
        return

    # โหลด texture
    textures = []
    for path in frames:
        try:
            textures.append(CoreImage(path).texture)
        except Exception:
            continue
    if not textures:
        return

    # ขนาดใบมีดให้สมดุลกับระยะ ไม่ใหญ่จนบังตัวละคร
    blade_size = max(48, min(96, radius * 0.9))

    ig = InstructionGroup()
    ig.add(Color(1, 1, 1, 1))

    rects = []
    base_angles = []
    for i in range(blades):
        ang = 2 * _m.pi * i / blades
        base_angles.append(ang)
        x = cx + _m.cos(ang) * radius - blade_size / 2
        y = cy + _m.sin(ang) * radius - blade_size / 2
        r = Rectangle(
            texture=textures[0],
            pos=(x, y),
            size=(blade_size, blade_size),
        )
        rects.append(r)
        ig.add(r)

    game.world_layout.canvas.add(ig)

    steps = max(6, int(duration * 20))  # อัปเดตประมาณ 20 ครั้งต่อวินาที
    step_time = duration / steps
    state = {"step": 0, "frame": 0}

    def _step(dt):
        if state["step"] >= steps:
            game.world_layout.canvas.remove(ig)
            return

        angle_offset = 2 * _m.pi * (state["step"] / steps)
        tex = textures[state["frame"]]

        for base_ang, rect in zip(base_angles, rects):
            a = base_ang + angle_offset
            x = cx + _m.cos(a) * radius - blade_size / 2
            y = cy + _m.sin(a) * radius - blade_size / 2
            rect.pos = (x, y)
            rect.texture = tex

        state["step"] += 1
        # เปลี่ยนเฟรมภาพเป็นจังหวะ ๆ
        if state["step"] % max(1, steps // len(textures)) == 0:
            state["frame"] = (state["frame"] + 1) % len(textures)

        Clock.schedule_once(_step, step_time)

    Clock.schedule_once(_step, step_time)


from typing import Dict, List, Type


# ══════════════════════════════════════════════════════
#  SKILL REGISTRY / LOADOUT — ใช้ใน LevelUpPopup + PlayerStats
# ══════════════════════════════════════════════════════
ALL_SKILLS: List[Type[BaseSkill]] = [AxeTSkill, SlashSkill, AoESkill]

# สกิลเริ่มต้นต่อคาแรกเตอร์ (ตอนเริ่มเกม)
CHAR_DEFAULT_SKILLS: Dict[str, List[Type[BaseSkill]]] = {
    # Lostman เริ่มด้วยสกิลตีใกล้เท่านั้น
    "Lostman": [SlashSkill],
    # PTae / Monkey ยังไม่ใส่สกิล เริ่มต้นด้วย stat-only upgrade
}

# สกิลที่ "อนุญาต" ให้สุ่ม / ปลดล็อกต่อคาแรกเตอร์
CHARACTER_SKILL_POOL: Dict[str, List[Type[BaseSkill]]] = {
    # Lostman สามารถปลดได้ครบ 3 สกิล
    "Lostman": [SlashSkill, AxeTSkill, AoESkill],
    # ตัวอื่นสามารถเพิ่ม mapping ภายหลังได้ง่าย ๆ
}


def get_upgrade_choices(player_stats, count=3):
    """
    คืน list ของ dict สำหรับแสดงใน LevelUpPopup
    แต่ละ choice มี: skill_instance, label, description
    """
    import random

    # เลือก pool สกิลที่อนุญาตตามชื่อคาแรกเตอร์
    allowed_pool = CHARACTER_SKILL_POOL.get(player_stats.name, [])
    if not allowed_pool:
        # คาแรกเตอร์นี้ยังไม่ออกแบบระบบสกิล → กลับไปใช้โหมดอัป stat
        return []

    upgradeable = [s for s in player_stats.skills if s.level < s.max_level]
    owned_types = {type(s) for s in player_stats.skills}
    new_skills = [cls() for cls in allowed_pool if cls not in owned_types]

    pool = upgradeable + new_skills
    random.shuffle(pool)
    selected = pool[:count]

    choices = []
    for skill in selected:
        is_new = skill not in player_stats.skills
        label = (f"[NEW] {skill.name}" if is_new
                 else f"[Lv{skill.level}→{skill.level+1}] {skill.name}")
        choices.append({
            "skill": skill,
            "label": label,
            "description": skill.description,
            "is_new": is_new,
        })

    return choices