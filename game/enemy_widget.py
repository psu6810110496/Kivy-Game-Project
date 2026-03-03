from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
import math


class EnemyWidget(Widget):
    def __init__(self, spawn_pos, **kwargs):
        super().__init__(**kwargs)
        self.size = (50, 50)  # ปรับขนาดซอมบี้ได้ตามต้องการ
        self.pos = spawn_pos

        self.speed = 1.5
        self.hp = 10
        self.damage = 5

        with self.canvas:
            # 🌟 เปลี่ยนสีเป็น (1, 1, 1, 1) สีขาว เพื่อให้รูปภาพแสดงสีตามต้นฉบับ 100%
            Color(1, 1, 1, 1)

            # 🌟 ดึงรูปภาพซอมบี้มาใช้ (อย่าลืมหาไฟล์รูปไปใส่ไว้ในโฟลเดอร์ assets นะครับ)
            self.rect = Rectangle(
                source="assets/enemy/zombie.png", pos=self.pos, size=self.size
            )

    def update_movement(self, player_pos, all_enemies):
        ex, ey = self.pos
        px, py = player_pos

        # --- 1. เดินหาผู้เล่น (Attraction) ---
        dx = px - ex
        dy = py - ey
        dist_to_player = math.hypot(dx, dy)

        move_x = move_y = 0
        if dist_to_player > 0:
            move_x = (dx / dist_to_player) * self.speed
            move_y = (dy / dist_to_player) * self.speed

        # --- 2. ผลักออกจากศัตรูตัวอื่นเพื่อไม่ให้ซ้อนกัน (Separation) ---
        push_x = push_y = 0
        hitbox_radius = 20  # รัศมีของตัวศัตรู (กว้าง 40 / 2)
        min_dist = hitbox_radius * 2  # ระยะห่างขั้นต่ำที่ห้ามซ้อนกัน (40 พิกเซล)

        for other in all_enemies:
            if other is self:  # ไม่ต้องเช็คระยะกับตัวเอง
                continue

            ox, oy = other.pos
            diff_x = ex - ox
            diff_y = ey - oy
            dist_to_enemy = math.hypot(diff_x, diff_y)

            # ถ้าศัตรูอยู่ใกล้กันเกินไป (ซ้อนทับกัน)
            if dist_to_enemy < min_dist and dist_to_enemy > 0:
                overlap = min_dist - dist_to_enemy
                # ค่อยๆ ผลักออก (คูณ 0.1 เพื่อให้การผลักดูนุ่มนวล ไม่กระตุกแรงเกินไป)
                push_x += (diff_x / dist_to_enemy) * overlap * 0.1
                push_y += (diff_y / dist_to_enemy) * overlap * 0.1

        # --- 3. อัปเดตตำแหน่ง (ความเร็วเดิน + แรงผลัก) ---
        ex += move_x + push_x
        ey += move_y + push_y

        self.pos = (ex, ey)
        self.rect.pos = self.pos
