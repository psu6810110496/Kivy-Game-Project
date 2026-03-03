from kivy.uix.widget import Widget
from kivy.graphics import Rectangle, Color, Line  # นำเข้า Line แทน Triangle
from kivy.clock import Clock
import math

class PlayerWidget(Widget):
    def __init__(self, idle_frames, walk_frames, start_pos=(2500, 2500), **kwargs):
        super().__init__(**kwargs)
        
        # Animation Setup (เหมือนเดิม)
        self.anim_idle = idle_frames
        self.anim_walk = walk_frames
        self.idle_speed = 0.5 
        self.walk_speed = 0.15 
        self.current_anim = self.anim_idle
        self.current_anim_speed = self.idle_speed 
        self.frame_index = 0
        self.anim_timer = 0
        self.is_facing_right = True 
        
        with self.canvas:
            self.color_inst = Color(1, 1, 1, 1) 
            self.rect = Rectangle(source=self.current_anim[0], pos=start_pos, size=(64, 64))
            
        with self.canvas.after:
            # เปลี่ยนสีเป็นสีขาว (1, 1, 1) และค่า Alpha เริ่มต้นเป็น 0
            self.aim_color = Color(1, 1, 1, 0) 
            
            # ใช้ Line วาดหัวลูกศรแบบ >
            # points จะรับ [x_base_top, y_base_top, x_tip, y_tip, x_base_bottom, y_base_bottom]
            self.aim_line = Line(points=[0, 0, 0, 0, 0, 0], width=1.5, joint='miter')

        Clock.schedule_interval(self.animate, 1.0/60.0)

    def update_aim(self, is_aiming, aim_x, aim_y):
        """ อัปเดตตำแหน่งและทิศทางของลูกศรเล็งแบบ > """
        if is_aiming and (aim_x != 0 or aim_y != 0):
            self.aim_color.a = 1.0 # แสดงลูกศรสีขาว
            
            cx = self.rect.pos[0] + (self.rect.size[0] / 2)
            cy = self.rect.pos[1] + (self.rect.size[1] / 2)
            
            # ปรับทิศทางเป็น Unit Vector
            mag = (aim_x**2 + aim_y**2) ** 0.5
            ux, uy = aim_x / mag, aim_y / mag
            
            # ตั้งค่ารูปร่างลูกศร
            dist = 50        # ระยะห่างจากตัวละคร
            arrow_size = 10  # ความยาวก้านของหัวศร
            spread = 1     # ความกว้างของปากลูกศร (ยิ่งเยอะยิ่งอ้ากว้าง)
            
            # Vector ตั้งฉาก
            px, py = -uy, ux
            
            # 1. จุดยอด (Tip) ของลูกศร >
            tip_x = cx + (ux * dist)
            tip_y = cy + (uy * dist)
            
            # 2. จุดปลายก้านบน
            p2_x = cx + (ux * (dist - arrow_size)) + (px * arrow_size * spread)
            p2_y = cy + (uy * (dist - arrow_size)) + (py * arrow_size * spread)
            
            # 3. จุดปลายก้านล่าง
            p3_x = cx + (ux * (dist - arrow_size)) - (px * arrow_size * spread)
            p3_y = cy + (uy * (dist - arrow_size)) - (py * arrow_size * spread)
            
            # อัปเดตเส้น Line ให้ลากจาก (ปลายก้านบน -> จุดยอด -> ปลายก้านล่าง)
            self.aim_line.points = [p2_x, p2_y, tip_x, tip_y, p3_x, p3_y]
        else:
            self.aim_color.a = 0.0 # ซ่อนเมื่อไม่ได้เล็ง

    # --- ฟังก์ชันอื่นๆ (set_state, animate, update_pos) คงเดิมเหมือนโค้ดก่อนหน้า ---
    def set_state(self, is_moving, facing_right, current_speed):
        self.is_facing_right = facing_right
        base_speed_ref = 5.0 
        dynamic_walk_speed = self.walk_speed * (base_speed_ref / max(current_speed, 1.0))
        new_anim = self.anim_walk if is_moving else self.anim_idle
        self.current_anim_speed = dynamic_walk_speed if is_moving else self.idle_speed
        if self.current_anim != new_anim:
            self.current_anim = new_anim
            self.frame_index = 0

    def animate(self, dt):
        self.anim_timer += dt
        if self.anim_timer >= self.current_anim_speed:
            self.anim_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.current_anim)
            self.rect.source = self.current_anim[self.frame_index]
        
        if self.is_facing_right:
            self.rect.tex_coords = (0, 1, 1, 1, 1, 0, 0, 0)
        else:
            self.rect.tex_coords = (1, 1, 0, 1, 0, 0, 1, 0)

    def update_pos(self, new_pos):
        self.rect.pos = new_pos