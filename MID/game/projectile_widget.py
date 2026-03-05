"""
game/projectile_widget.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ประกอบด้วย:
  EnemyProjectile  — กระสุนของศัตรู (animated sprite + rotate)
  PlayerBullet     — กระสุนของผู้เล่น (sprite animation หรือ fallback ellipse)
  RocketBullet     — จรวดของสกิล PTae
  HealthPickup     — ไอเทมเก็บเลือด
"""
import math

from kivy.core.image import Image as CoreImage
from kivy.graphics import (
    Color, Ellipse, Rectangle,
    PushMatrix, PopMatrix, Translate, Rotate,
)
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.widget import Widget


# ═══════════════════════════════════════════════════════════
#  Base — กระสุนที่เคลื่อนที่เป็นเส้นตรง
# ═══════════════════════════════════════════════════════════
class _LinearProjectile(Widget):
    """Base class สำหรับกระสุนทุกชนิดที่บินตรง"""

    def __init__(self, start_pos, target_pos, speed: float, damage: float, **kwargs):
        super().__init__(**kwargs)
        self.pos = start_pos
        self.speed = speed
        self.damage = damage

        dx = target_pos[0] - start_pos[0]
        dy = target_pos[1] - start_pos[1]
        mag = math.hypot(dx, dy)
        self.direction = (dx / mag, dy / mag) if mag > 0 else (1, 0)

    def _move(self, dt: float):
        self.pos = (
            self.pos[0] + self.direction[0] * self.speed * dt,
            self.pos[1] + self.direction[1] * self.speed * dt,
        )


# ═══════════════════════════════════════════════════════════
#  EnemyProjectile
# ═══════════════════════════════════════════════════════════
class EnemyProjectile(_LinearProjectile):
    """
    กระสุนของศัตรู Ranger / Boss special attacks
    - โหลด sprite sheet animation จาก assets/effect/rangershoot/
    - หมุนตามทิศทาง
    """

    _TEXTURES: list | None = None  # class-level cache

    @classmethod
    def _load_textures(cls):
        if cls._TEXTURES is None:
            try:
                cls._TEXTURES = [
                    CoreImage(f"assets/effect/rangershoot/1_{i}.png").texture
                    for i in range(30)
                ]
            except Exception:
                cls._TEXTURES = []

    def __init__(self, start_pos, target_pos, damage: float = 10, **kwargs):
        super().__init__(start_pos, target_pos, speed=400.0, damage=damage, **kwargs)
        self._load_textures()

        self.size = (80, 80)
        self._frame: int = 0
        self._anim_timer: float = 0.0
        self._frame_duration: float = 0.02

        angle = math.degrees(math.atan2(self.direction[1], self.direction[0]))

        with self.canvas:
            PushMatrix()
            self.translate = Translate(self.pos[0], self.pos[1])
            self.rotate = Rotate(angle=angle, origin=(0, 0))
            Color(1, 1, 1, 1)
            self.bullet_rect = Rectangle(
                pos=(-self.size[0] / 2, -self.size[1] / 2),
                size=self.size,
                texture=self._TEXTURES[0] if self._TEXTURES else None,
            )
            PopMatrix()

        self.bind(pos=self._sync_translate)

    def _sync_translate(self, _inst, value):
        self.translate.x = value[0]
        self.translate.y = value[1]

    def update(self, dt: float):
        # Animation
        if self._TEXTURES:
            self._anim_timer += dt
            if self._anim_timer >= self._frame_duration:
                self._anim_timer = 0.0
                if self._frame < len(self._TEXTURES) - 1:
                    self._frame += 1
                    self.bullet_rect.texture = self._TEXTURES[self._frame]
        self._move(dt)


# ═══════════════════════════════════════════════════════════
#  PlayerBullet
# ═══════════════════════════════════════════════════════════
class PlayerBullet(_LinearProjectile):
    """
    กระสุนของผู้เล่น
    - ถ้ามี anim_frames → แสดง sprite animation
    - ถ้าไม่มี → fallback วงกลมสีฟ้า
    - update() คืน True ถ้ายังในระยะ, False ถ้าหมด range
    """

    def __init__(
        self,
        start_pos, target_pos,
        speed: float, proj_range: float, damage: float,
        anim_frames: list | None = None,
        **kwargs,
    ):
        super().__init__(start_pos, target_pos, speed=speed, damage=damage, **kwargs)
        self._range = proj_range
        self._traveled = 0.0
        self._anim_frames = anim_frames or []
        self._anim_index = 0
        self._anim_timer = 0.0
        self._frame_duration = 0.06

        if self._anim_frames:
            self._sprite = Image(
                source=self._anim_frames[0],
                size=(48, 48),
                pos=(start_pos[0] - 24, start_pos[1] - 24),
                allow_stretch=True,
                keep_ratio=False,
            )
            self.add_widget(self._sprite)
        else:
            with self.canvas:
                Color(0.3, 1, 1, 1)
                self._ellipse = Ellipse(
                    pos=(start_pos[0] - 6, start_pos[1] - 6),
                    size=(12, 12),
                )

        self.bind(pos=self._sync_graphics)

    def _sync_graphics(self, *_args):
        if hasattr(self, "_sprite"):
            self._sprite.pos = (
                self.pos[0] - self._sprite.width / 2,
                self.pos[1] - self._sprite.height / 2,
            )
        elif hasattr(self, "_ellipse"):
            self._ellipse.pos = (self.pos[0] - 6, self.pos[1] - 6)

    def update(self, dt: float) -> bool:
        """คืน True ถ้ายังในระยะ"""
        if self._anim_frames and len(self._anim_frames) > 1:
            self._anim_timer += dt
            if self._anim_timer >= self._frame_duration:
                self._anim_timer = 0.0
                self._anim_index = (self._anim_index + 1) % len(self._anim_frames)
                if hasattr(self, "_sprite"):
                    self._sprite.source = self._anim_frames[self._anim_index]

        move_x = self.direction[0] * self.speed * dt
        move_y = self.direction[1] * self.speed * dt
        self.pos = (self.pos[0] + move_x, self.pos[1] + move_y)
        self._traveled += math.hypot(move_x, move_y)
        return self._traveled < self._range


# ═══════════════════════════════════════════════════════════
#  RocketBullet  (สกิล PTae)
# ═══════════════════════════════════════════════════════════
class RocketBullet(_LinearProjectile):
    """
    จรวดสีแดงสี่เหลี่ยม — บินตรงเข้าหาผู้เล่น
    update() คืน True ถ้ายังในระยะ
    """

    def __init__(self, start_pos, target_pos, speed: float, proj_range: float, damage: float, **kwargs):
        super().__init__(start_pos, target_pos, speed=speed, damage=damage, **kwargs)
        self._range = proj_range
        self._traveled = 0.0
        self.size = (12, 32)

        with self.canvas:
            Color(1, 0.2, 0.2, 1)
            self.rect = Rectangle(
                pos=(start_pos[0] - self.size[0] / 2, start_pos[1] - self.size[1] / 2),
                size=self.size,
            )
        self.bind(pos=self._sync_rect)

    def _sync_rect(self, *_args):
        self.rect.pos = (self.pos[0] - self.size[0] / 2, self.pos[1] - self.size[1] / 2)

    def update(self, dt: float) -> bool:
        move_x = self.direction[0] * self.speed * dt
        move_y = self.direction[1] * self.speed * dt
        self.pos = (self.pos[0] + move_x, self.pos[1] + move_y)
        self._traveled += math.hypot(move_x, move_y)
        return self._traveled < self._range


# ═══════════════════════════════════════════════════════════
#  HealthPickup
# ═══════════════════════════════════════════════════════════
class HealthPickup(Widget):
    """ไอเทมเก็บเลือด — รูปแบบเปลี่ยนตามตัวละคร"""

    def __init__(self, pos=(0, 0), heal_amount=25, char_name="Lostman", **kwargs):
        super().__init__(**kwargs)
        self.pos = pos
        self.heal_amount = heal_amount
        self.size = (28, 28)

        # 🌟 เลือกไฟล์ภาพตามชื่อตัวละคร (ตั้งชื่อไฟล์ให้ตรงกับ assets ของคุณ)
        textures = {
            "PTae": "assets/effect/ptae_heal.png",
            "Lostman": "assets/effect/lostman_heal.png",
            "Monkey": "assets/effect/monkey_heal.png"
        }
        img_path = textures.get(char_name, "assets/effect/health_potion.png") # fallback

        try:
            if __import__("os").path.exists(img_path):
                self._img = Image(source=img_path, size=self.size, pos=self.pos)
                self.add_widget(self._img)
                self.bind(pos=self._update_img_pos)
                return
        except Exception:
            pass

    def _sync_graphics(self, _inst, value):
        if hasattr(self, "_rect"):
            self._rect.pos = value
        if hasattr(self, "_lbl"):
            self._lbl.pos = value


# ═══════════════════════════════════════════════════════════
#  RPGRocket  (ระเบิด AoE เมื่อชนศัตรู)
# ═══════════════════════════════════════════════════════════
class RPGRocket(_LinearProjectile):
    """จรวดส้ม — ระเบิด AoE กว้างเมื่อชนศัตรู"""

    def __init__(
        self, start_pos, target_pos,
        speed: float, proj_range: float, damage: float,
        splash_damage: float = 60, splash_radius: float = 150,
        **kwargs,
    ):
        super().__init__(start_pos, target_pos, speed=speed, damage=damage, **kwargs)
        self._range = proj_range
        self._traveled = 0.0
        self.splash_damage = splash_damage
        self.splash_radius = splash_radius
        self.exploded = False
        self.size = (16, 40)

        with self.canvas:
            Color(1, 0.4, 0.0, 1)
            self.rect = Rectangle(
                pos=(start_pos[0] - 8, start_pos[1] - 20),
                size=self.size,
            )
        self.bind(pos=lambda i, v: setattr(self.rect, "pos", (v[0] - 8, v[1] - 20)))

    def explode(self, game):
        """ระเบิด AoE — เรียกจาก CombatManager เมื่อชนศัตรู"""
        if self.exploded:
            return
        self.exploded = True
        px, py = self.pos[0], self.pos[1]
        from game.skills import _hit_enemy, _show_aoe_vfx
        _show_aoe_vfx(game, px, py, self.splash_radius)
        for enemy in list(game.enemies):
            ex = enemy.pos[0] + 20
            ey = enemy.pos[1] + 20
            if math.hypot(ex - px, ey - py) <= self.splash_radius:
                _hit_enemy(game, enemy, self.splash_damage)

    def update(self, dt: float) -> bool:
        if self.exploded:
            return False
        move_x = self.direction[0] * self.speed * dt
        move_y = self.direction[1] * self.speed * dt
        self.pos = (self.pos[0] + move_x, self.pos[1] + move_y)
        self._traveled += math.hypot(move_x, move_y)
        return self._traveled < self._range


# ═══════════════════════════════════════════════════════════
#  ExpOrb  (EXP drop จากศัตรู)
# ═══════════════════════════════════════════════════════════
class ExpOrb(Widget):
    """ลูกกลม EXP สีเหลือง — วิ่งไปเก็บเพื่อรับ EXP"""

    def __init__(self, pos=(0, 0), exp_amount: float = 10, texture_path=None, **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (20, 20))
        super().__init__(**kwargs)
        self.pos = pos
        self.exp_amount = exp_amount
        self.size = (20, 20)

        with self.canvas:
            if texture_path:
                try:
                    tex = CoreImage(texture_path).texture
                    Color(1, 1, 1, 1)
                    self._shape = Rectangle(pos=self.pos, size=self.size, texture=tex)
                    self.bind(pos=lambda i, v: setattr(self._shape, "pos", v))
                    return
                except Exception:
                    pass
            Color(1, 0.9, 0.1, 1)
            self._shape = Ellipse(pos=self.pos, size=self.size)
        self.bind(pos=lambda i, v: setattr(self._shape, "pos", v))