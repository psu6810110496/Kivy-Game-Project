from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, PushMatrix, PopMatrix, Translate, Rotate
from kivy.core.image import Image as CoreImage
import math


class EnemyProjectile(Widget):
    # โหลด texture สำหรับเอฟเฟกต์ยิงของ Ranger (ใช้ร่วมกันทุก instance)
    RANGERSHOOT_TEXTURES = None

    @classmethod
    def _load_textures(cls):
        """โหลด rangershoot textures เพียงครั้งเดียว"""
        if cls.RANGERSHOOT_TEXTURES is None:
            cls.RANGERSHOOT_TEXTURES = [
                CoreImage(f"assets/effect/rangershoot/1_{i}.png").texture
                for i in range(30)
            ]

    def __init__(self, start_pos, target_pos, damage=10, **kwargs):
        super().__init__(**kwargs)
        # โหลด textures ถ้ายังไม่ได้โหลด
        self._load_textures()

        # 1. กำหนดค่าเริ่มต้น
        self.pos = start_pos
        self.size = (80, 80)  # ขนาดเอฟเฟกต์
        self.damage = damage
        self.speed = 400.0  # ความเร็วกระสุน (พิกเซลต่อวินาที)

        # 2. คำนวณทิศทางครั้งเดียวตอนยิงออกมา
        dx = target_pos[0] - start_pos[0]
        dy = target_pos[1] - start_pos[1]
        mag = math.hypot(dx, dy)
        self.direction = (dx / mag, dy / mag) if mag > 0 else (1, 0)

        # 3. ระบบ Animation
        self.current_frame = 0
        self.animation_time = 0
        self.frame_duration = 0.02  # เปลี่ยนเฟรมทุก 0.02 วิ

        # เตรียมมุมหมุนให้กระสุนหันไปทางผู้เล่น
        self.angle = math.degrees(math.atan2(self.direction[1], self.direction[0]))

        with self.canvas:
            PushMatrix()
            # แปลงตำแหน่งไปยัง self.pos เพื่อให้ Rotate ใช้ origin = (0,0)
            self.translate = Translate(self.pos[0], self.pos[1])
            self.rotate = Rotate(angle=self.angle, origin=(0, 0))
            Color(1, 1, 1, 1)
            # 4. สร้าง Rectangle สำหรับแสดงเอฟเฟกต์กระสุน (จุดศูนย์กลางอยู่ที่ 0,0)
            self.bullet_rect = Rectangle(
                pos=(-self.size[0] / 2, -self.size[1] / 2),
                size=self.size,
                texture=self.RANGERSHOOT_TEXTURES[0],
            )
            PopMatrix()

        # bind เพื่อให้ transform ตามตำแหน่ง
        self.bind(pos=self._update_bullet_graphics)


    def update(self, dt):
        # 1. อัปเดต Animation -- เล่นจนถึงเฟรมสุดท้ายแล้วค้างไว้
        self.animation_time += dt
        if self.animation_time >= self.frame_duration:
            self.animation_time = 0
            if self.current_frame < len(self.RANGERSHOOT_TEXTURES) - 1:
                self.current_frame += 1
                self.bullet_rect.texture = self.RANGERSHOOT_TEXTURES[self.current_frame]
        # 2. คำนวณตำแหน่งใหม่ตามเวลา (dt) ทำให้กระสุนเคลื่อนที่
        new_x = self.pos[0] + self.direction[0] * self.speed * dt
        new_y = self.pos[1] + self.direction[1] * self.speed * dt

        # การกำหนดค่าเป็น Tuple ใหม่ จะไปกระตุ้น self.bind(pos=...) ให้ทำงาน
        self.pos = (new_x, new_y)

    def _update_bullet_graphics(self, instance, value):
        # ปรับ Translate ให้ตรงกับ pos ของ Widget
        self.translate.x = self.pos[0]
        self.translate.y = self.pos[1]
