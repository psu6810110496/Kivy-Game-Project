from kivy.uix.widget import Widget
from kivy.graphics import Rectangle, Color
import math
import random

class EnemyWidget(Widget):
    def __init__(self, spawn_pos, enemy_type="normal", **kwargs):
        super().__init__(**kwargs)
        self.enemy_type = enemy_type
        self.pos = spawn_pos
        
        # ตั้งค่า Status ตามประเภท
        if enemy_type == "stalker":
            self.hp = 15
            self.speed = 4.5  # วิ่งไวมาก
            self.damage = 5
            self.color = (0.2, 0.8, 0.2, 1) # สีเขียวสด
            self.size = (30, 30)
        elif enemy_type == "ranger":
            self.hp = 30
            self.speed = 1.5  # เดินอืด
            self.damage = 15
            self.color = (0.2, 0.2, 1, 1) # สีน้ำเงิน
            self.size = (45, 45)
            self.shoot_cooldown = 0
        else: # normal
            self.hp = 50
            self.speed = 2.0
            self.damage = 10
            self.color = (0.8, 0.2, 0.2, 1)
            self.size = (40, 40)

        with self.canvas:
            self.color_inst = Color(*self.color)
            self.rect = Rectangle(pos=self.pos, size=self.size)

    def update_movement(self, player_pos, all_enemies):
        dx = player_pos[0] - self.pos[0]
        dy = player_pos[1] - self.pos[1]
        dist = math.hypot(dx, dy)

        # Ranger จะหยุดเดินถ้าเข้าระยะยิง (300 px)
        if self.enemy_type == "ranger" and dist < 300:
            return # หยุดเดินเพื่อเตรียมยิง

        if dist > 0:
            mx, my = (dx / dist) * self.speed, (dy / dist) * self.speed
            self.pos = (self.pos[0] + mx, self.pos[1] + my)
            self.rect.pos = self.pos