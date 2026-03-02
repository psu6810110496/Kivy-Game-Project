from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
import math

class EnemyWidget(Widget):
    def __init__(self, spawn_pos, **kwargs):
        super().__init__(**kwargs)
        self.size = (40, 40) # ขนาดศัตรู
        self.pos = spawn_pos # ตำแหน่งที่เกิด
        
        # ค่าสเตตัสเบื้องต้นของศัตรู
        self.speed = 1.5
        self.hp = 10
        self.damage = 5

        # วาดศัตรู (สี่เหลี่ยมสีแดง)
        with self.canvas:
            Color(1, 0, 0, 1) # สีแดง (R, G, B, A)
            self.rect = Rectangle(pos=self.pos, size=self.size)

    def update_movement(self, player_pos):
        # ตำแหน่งปัจจุบันของศัตรู
        ex, ey = self.pos
        # ตำแหน่งของผู้เล่น
        px, py = player_pos
        
        # คำนวณระยะห่างและทิศทาง (Vector Math)
        dx = px - ex
        dy = py - ey
        dist = math.hypot(dx, dy) # หาระยะจัดกระจัด
        
        # ถ้ายังไม่ถึงตัวผู้เล่น ให้เดินเข้าไปหา
        if dist > 0:
            ex += (dx / dist) * self.speed
            ey += (dy / dist) * self.speed
            
        # อัปเดตตำแหน่งใหม่
        self.pos = (ex, ey)
        self.rect.pos = self.pos