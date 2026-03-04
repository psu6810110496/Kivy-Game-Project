from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.graphics import (
    Color,
    Ellipse,
    Rectangle,
    PushMatrix,
    PopMatrix,
    Translate,
    Rotate,
)
from kivy.core.image import Image as CoreImage
import math
import random
from kivy.uix.label import Label


class EnemyProjectile(Widget):
    """กระสุนศัตรู Ranger — มี sprite animation + หมุนตามทิศทาง"""

    RANGERSHOOT_TEXTURES = None

    @classmethod
    def _load_textures(cls):
        if cls.RANGERSHOOT_TEXTURES is None:
            try:
                cls.RANGERSHOOT_TEXTURES = [
                    CoreImage(f"assets/effect/rangershoot/1_{i}.png").texture
                    for i in range(30)
                ]
            except Exception:
                cls.RANGERSHOOT_TEXTURES = []

    def __init__(self, start_pos, target_pos, damage=10, **kwargs):
        super().__init__(**kwargs)
        self._load_textures()

        self.pos = start_pos
        self.size = (80, 80)
        self.damage = damage
        self.speed = 400.0

        dx = target_pos[0] - start_pos[0]
        dy = target_pos[1] - start_pos[1]
        mag = math.hypot(dx, dy)
        self.direction = (dx / mag, dy / mag) if mag > 0 else (1, 0)

        self.current_frame = 0
        self.animation_time = 0.0
        self.frame_duration = 0.02

        self.angle = math.degrees(math.atan2(self.direction[1], self.direction[0]))

        with self.canvas:
            PushMatrix()
            self.translate = Translate(self.pos[0], self.pos[1])
            self.rotate = Rotate(angle=self.angle, origin=(0, 0))
            Color(1, 1, 1, 1)
            first_tex = (
                self.RANGERSHOOT_TEXTURES[0] if self.RANGERSHOOT_TEXTURES else None
            )
            self.bullet_rect = Rectangle(
                pos=(-self.size[0] / 2, -self.size[1] / 2),
                size=self.size,
                texture=first_tex,
            )
            PopMatrix()

        self.bind(pos=self._update_bullet_graphics)

    def _update_bullet_graphics(self, instance, value):
        self.translate.x = self.pos[0]
        self.translate.y = self.pos[1]

    def update(self, dt):
        # อัปเดต animation
        if self.RANGERSHOOT_TEXTURES:
            self.animation_time += dt
            if self.animation_time >= self.frame_duration:
                self.animation_time = 0
                if self.current_frame < len(self.RANGERSHOOT_TEXTURES) - 1:
                    self.current_frame += 1
                    self.bullet_rect.texture = self.RANGERSHOOT_TEXTURES[
                        self.current_frame
                    ]

        # เคลื่อนที่
        self.pos = (
            self.pos[0] + self.direction[0] * self.speed * dt,
            self.pos[1] + self.direction[1] * self.speed * dt,
        )


class PlayerBullet(Widget):
    """
    กระสุนผู้เล่น
    - รองรับ anim_frames (sprite สกิล) หรือ fallback วงกลมสีฟ้า
    - ขยับตาม dt ทุก frame
    """

    def __init__(
        self,
        start_pos,
        target_pos,
        speed,
        proj_range,
        damage,
        anim_frames=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.pos = start_pos
        self.damage = damage
        self.speed = speed
        self._range = proj_range
        self._traveled = 0.0
        self._anim_frames = anim_frames or []
        self._anim_index = 0
        self._anim_timer = 0.0
        self._frame_duration = 0.06  # วินาทีต่อเฟรม

        dx = target_pos[0] - start_pos[0]
        dy = target_pos[1] - start_pos[1]
        mag = math.hypot(dx, dy)
        self.dir = (dx / mag, dy / mag) if mag > 0 else (1, 0)

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

        self.bind(pos=self._update_graphics)

    def _update_graphics(self, *args):
        if hasattr(self, "_sprite"):
            self._sprite.pos = (
                self.pos[0] - self._sprite.width / 2,
                self.pos[1] - self._sprite.height / 2,
            )
        elif hasattr(self, "_ellipse"):
            self._ellipse.pos = (self.pos[0] - 6, self.pos[1] - 6)

    def update(self, dt):
        # อัปเดต sprite animation
        if self._anim_frames and len(self._anim_frames) > 1:
            self._anim_timer += dt
            if self._anim_timer >= self._frame_duration:
                self._anim_timer = 0
                self._anim_index = (self._anim_index + 1) % len(self._anim_frames)
                if hasattr(self, "_sprite"):
                    self._sprite.source = self._anim_frames[self._anim_index]

        # เคลื่อนที่
        move_x = self.dir[0] * self.speed * dt
        move_y = self.dir[1] * self.speed * dt
        self.pos = (self.pos[0] + move_x, self.pos[1] + move_y)
        self._traveled += math.hypot(move_x, move_y)

        # คืน True ถ้ายังในระยะ
        return self._traveled < self._range


# ═════════════════════════════════════════════════════════════════
#  Rocket projectile for PTae skill
# ═════════════════════════════════════════════════════════════════
class RocketBullet(Widget):
    """จรวดสี่เหลี่ยมบินตรงมาหาผู้เล่น"""

    def __init__(
        self,
        start_pos,
        target_pos,
        speed,
        proj_range,
        damage,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.pos = start_pos
        self.damage = damage
        self.speed = speed
        self._range = proj_range
        self._traveled = 0.0

        dx = target_pos[0] - start_pos[0]
        dy = target_pos[1] - start_pos[1]
        mag = math.hypot(dx, dy)
        self.dir = (dx / mag, dy / mag) if mag > 0 else (1, 0)

        self.size = (12, 32)
        with self.canvas:
            Color(1, 0.2, 0.2, 1)
            self.rect = Rectangle(
                pos=(start_pos[0] - self.size[0] / 2, start_pos[1] - self.size[1] / 2),
                size=self.size,
            )
        self.bind(pos=self._update_graphics)

    def _update_graphics(self, *args):
        self.rect.pos = (self.pos[0] - self.size[0] / 2, self.pos[1] - self.size[1] / 2)

    def update(self, dt):
        move_x = self.dir[0] * self.speed * dt
        move_y = self.dir[1] * self.speed * dt
        self.pos = (self.pos[0] + move_x, self.pos[1] + move_y)
        self._traveled += math.hypot(move_x, move_y)
        return self._traveled < self._range


class HealthPickup(Widget):
    """Simple health pickup that can be collected by the player.
    
    Appearance: green rectangle with "+" label.
    """

    def __init__(self, pos=(0, 0), heal_amount=25, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (28, 28))
        super().__init__(**kwargs)
        self.pos = pos
        self.heal_amount = heal_amount
        self.size = (28, 28)
        
        # Draw green rectangle + label
        with self.canvas:
            Color(0.1, 0.8, 0.3, 1)
            self._rect = Rectangle(pos=self.pos, size=self.size)
        self._lbl = Label(text="+", size_hint=(None, None), size=self.size, pos=self.pos, color=(1, 1, 1, 1), bold=True, font_size=16)
        self.add_widget(self._lbl)
        self.bind(pos=self._update_graphics)

    def _update_graphics(self, instance, value):
        if hasattr(self, "_rect"):
            self._rect.pos = value
        if hasattr(self, "_lbl"):
            self._lbl.pos = value