from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.graphics import Color, Ellipse
import math


class EnemyProjectile(Widget):
    def __init__(self, start_pos, target_pos, damage=10, **kwargs):
        super().__init__(**kwargs)
        # 1. กำหนดค่าเริ่มต้น
        self.size = (12, 12)
        self.pos = start_pos 
        self.damage = damage
        self.speed = 400.0 # ความเร็วกระสุน (พิกเซลต่อวินาที)
        
        # 2. คำนวณทิศทางครั้งเดียวตอนยิงออกมา
        dx = target_pos[0] - start_pos[0]
        dy = target_pos[1] - start_pos[1]
        mag = math.hypot(dx, dy)
        self.direction = (dx/mag, dy/mag) if mag > 0 else (1, 0)

        with self.canvas:
            Color(1, 0.6, 0, 1) # สีส้มทอง
            # 3. สร้างรูปทรงกระสุน
            self.bullet = Ellipse(pos=self.pos, size=self.size)
        
        # 4. Bind ฟังก์ชันอัปเดตกราฟิก เมื่อตำแหน่ง Widget เปลี่ยน
        self.bind(pos=self._update_bullet_graphics)

    def _update_bullet_graphics(self, *args):
        # อัปเดตตำแหน่งของรูปวาดให้ตามพิกัดของ Widget
        self.bullet.pos = self.pos

    def update(self, dt):
        # 5. คำนวณตำแหน่งใหม่ตามเวลา (dt) ทำให้กระสุนเคลื่อนที่ลื่นไหล
        new_x = self.pos[0] + self.direction[0] * self.speed * dt
        new_y = self.pos[1] + self.direction[1] * self.speed * dt
        
        # การกำหนดค่าเป็น Tuple ใหม่ จะไปกระตุ้น self.bind(pos=...) ให้ทำงาน
        self.pos = (new_x, new_y)


class PlayerBullet(Widget):
    """
    กระสุนฝั่งผู้เล่น
    - ขยับเองตามเวลา dt จาก GameScreen.update_frame()
    - รองรับทั้ง anim_frames (ภาพสกิล) หรือ fallback เป็นวงกลม
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

        dx = target_pos[0] - start_pos[0]
        dy = target_pos[1] - start_pos[1]
        mag = math.hypot(dx, dy)
        self.dir = (dx / mag, dy / mag) if mag > 0 else (1, 0)

        self._anim_frames = anim_frames or []

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
                Color(0.3, 1, 1, 1) # สีฟ้ากระสุนผู้เล่น
                self._ellipse = Ellipse(pos=(start_pos[0] - 6, start_pos[1] - 6), size=(12, 12))

        # ผูก event เพื่อให้กราฟิกขยับตามเวลาแก้พิกัด (pos)
        self.bind(pos=self._update_graphics)

    def _update_graphics(self, *args):
        if hasattr(self, "_sprite"):
            self._sprite.pos = (self.pos[0] - self._sprite.width / 2, self.pos[1] - self._sprite.height / 2)
        elif hasattr(self, "_ellipse"):
            self._ellipse.pos = (self.pos[0] - 6, self.pos[1] - 6)

    def update(self, dt):
        # เดินหน้าไปตามทิศทาง โดยใช้ dt เพื่อให้ภาพลื่นไหลไม่ขึ้นกับเฟรมเรต
        move_x = self.dir[0] * self.speed * dt
        move_y = self.dir[1] * self.speed * dt
        
        self.pos = (self.pos[0] + move_x, self.pos[1] + move_y)
        self._traveled += math.hypot(move_x, move_y)
        
        # คืนค่า True ถ้ายังอยู่ในระยะ (ให้มันบินต่อ) ถ้าบินเกินระยะ จะเป็น False (ให้ลบทิ้ง)
        return self._traveled < self._range