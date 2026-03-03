from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.graphics import Color, Ellipse
import math


class EnemyProjectile(Widget):
    def __init__(self, start_pos, target_pos, damage=10, **kwargs):
        super().__init__(**kwargs)
        self.pos = start_pos
        self.damage = damage
        self.speed = 6.0

        dx = target_pos[0] - start_pos[0]
        dy = target_pos[1] - start_pos[1]
        mag = math.hypot(dx, dy)
        self.dir = (dx / mag, dy / mag) if mag > 0 else (1, 0)

        with self.canvas:
            Color(1, 0.6, 0, 1)
            self.bullet = Ellipse(pos=self.pos, size=(12, 12))

    def update(self):
        self.pos = (
            self.pos[0] + self.dir[0] * self.speed,
            self.pos[1] + self.dir[1] * self.speed,
        )
        self.bullet.pos = self.pos


class PlayerBullet(Widget):
    """
    กระสุนฝั่งผู้เล่น ใช้โดยสกิล AxeTSkill ผ่านฟังก์ชัน _spawn_bullet
    - ขยับเองทุกเฟรมจาก GameScreen.update_frame()
    - รองรับทั้ง anim_frames (สกิล Lostman) หรือ fallback เป็นวงกลม
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
        # แปลง speed จากหน่วยต่อวินาที → หน่วยต่อเฟรม (เกม 60 FPS)
        self._speed_per_frame = speed / 60.0
        self._range = proj_range
        self._traveled = 0.0

        dx = target_pos[0] - start_pos[0]
        dy = target_pos[1] - start_pos[1]
        mag = math.hypot(dx, dy)
        self.dir = (dx / mag, dy / mag) if mag > 0 else (1, 0)

        self._anim_frames = anim_frames or []
        self._frame_index = 0

        if self._anim_frames:
            # ใช้ sprite ภาพสกิล
            self._sprite = Image(
                source=self._anim_frames[0],
                size=(48, 48),
                pos=(start_pos[0] - 24, start_pos[1] - 24),
                allow_stretch=True,
                keep_ratio=False,
            )
            self.add_widget(self._sprite)
        else:
            # Fallback เป็นวงกลมถ้าไม่มีภาพ
            with self.canvas:
                Color(0.3, 1, 1, 1)
                self._ellipse = Ellipse(pos=(start_pos[0] - 6, start_pos[1] - 6), size=(12, 12))

    def update(self):
        # เดินหน้าไปตามทิศทาง
        dx = self.dir[0] * self._speed_per_frame
        dy = self.dir[1] * self._speed_per_frame
        self.pos = (self.pos[0] + dx, self.pos[1] + dy)
        self._traveled += math.hypot(dx, dy)

        if hasattr(self, "_sprite"):
            self._sprite.pos = (self.pos[0] - self._sprite.width / 2, self.pos[1] - self._sprite.height / 2)
        elif hasattr(self, "_ellipse"):
            self._ellipse.pos = (self.pos[0] - 6, self.pos[1] - 6)
