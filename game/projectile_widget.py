from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse
import math

class EnemyProjectile(Widget):
    def __init__(self, start_pos, target_pos, damage=10, speed=5, **kwargs):
        super().__init__(**kwargs)
        self.pos = start_pos
        self.damage = damage
        self.speed = speed
        
        # คำนวณทิศทาง
        dx = target_pos[0] - start_pos[0]
        dy = target_pos[1] - start_pos[1]
        mag = math.hypot(dx, dy)
        self.dir_x = (dx / mag) if mag > 0 else 1
        self.dir_y = (dy / mag) if mag > 0 else 0

        with self.canvas:
            Color(1, 0.5, 0, 1) # สีส้ม
            self.rect = Ellipse(pos=self.pos, size=(10, 10))

    def update(self):
        self.pos = (self.pos[0] + self.dir_x * self.speed, 
                    self.pos[1] + self.dir_y * self.speed)
        self.rect.pos = self.pos