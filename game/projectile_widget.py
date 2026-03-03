from kivy.uix.widget import Widget
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
        # 5. คำนวณตำแหน่งใหม่ตามเวลา (dt) ทำให้กระสุนเคลื่อนที่
        new_x = self.pos[0] + self.direction[0] * self.speed * dt
        new_y = self.pos[1] + self.direction[1] * self.speed * dt
        
        # การกำหนดค่าเป็น Tuple ใหม่ จะไปกระตุ้น self.bind(pos=...) ให้ทำงาน
        self.pos = (new_x, new_y)