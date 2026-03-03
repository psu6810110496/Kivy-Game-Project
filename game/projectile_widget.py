from kivy.uix.widget import Widget
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
        self.dir = (dx/mag, dy/mag) if mag > 0 else (1, 0)

        with self.canvas:
            Color(1, 0.6, 0, 1) # สีส้มทอง
            self.bullet = Ellipse(pos=self.pos, size=(12, 12))

    def update(self):
        self.pos = (self.pos[0] + self.dir[0] * self.speed, 
                    self.pos[1] + self.dir[1] * self.speed)
        self.bullet.pos = self.pos