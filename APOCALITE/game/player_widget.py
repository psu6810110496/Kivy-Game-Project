from kivy.uix.widget import Widget
from kivy.graphics import Rectangle, Color, Line, Triangle, PushMatrix, PopMatrix, Translate, Rotate, Scale
from kivy.clock import Clock
import math

class PlayerWidget(Widget):
    def __init__(self, idle_frames, walk_frames, start_pos=(2500, 2500), **kwargs):
        super().__init__(**kwargs)
        
        # Animation Setup
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
            self.weapon_group = []
            
            PushMatrix()
            self.weapon_trans = Translate(0, 0)
            self.weapon_rot = Rotate(angle=0, origin=(0, 0))
            self.weapon_scale = Scale(1, 1, 1, origin=(0, 0))
            
            # --- 🌟 Aiming Arrow (ลูกศรเล็งแบบ >) ---
            self.c_aim = Color(1, 1, 1, 0) # สีขาว, ซ่อนไว้ก่อน
            # วาดรูปเชฟรอน (>) ที่อยู่ใกล้ตัวผู้เล่นมากขึ้น
            self.line_aim = Line(points=[45, -12, 60, 0, 45, 12], width=2.5)

            # --- RPG Tube (เฉพาะ Monkey) ---
            self.c_tube = Color(1, 1, 1, 0) # Alpha toggled by update_aim
            self.r_tube = Rectangle(source="assets/Monkey/Weapon/RPG.png", pos=(0, -45), size=(96, 96))

            # เก็บ Color instrucs เพื่อคุมการซ่อน/แสดง
            self.weapon_group = [self.c_tube, self.c_aim]
            PopMatrix()

        Clock.schedule_interval(self.animate, 1.0/60.0)

    def update_aim(self, is_aiming, aim_x, aim_y, has_rpg=False):
        """ อัปเดตตำแหน่งและให้ตัวละครดึง RPG ออกมาถือเล็ง (เฉพาะ Monkey ที่มีสกิลแล้ว) 
            ส่วนตัวละครอื่นจะขึ้นลูกศรสีเหลืองบอกทิศทาง
        """
        if is_aiming and (aim_x != 0 or aim_y != 0):
            # ตรวจสอบการแสดงผล
            if has_rpg:
                self.c_tube.a = 1.0  # Show RPG
                self.c_aim.a = 0.0   # Hide Arrow
            else:
                self.c_tube.a = 0.0  # Hide RPG
                self.c_aim.a = 0.8   # Show Arrow (ลูกศรเล็ง)

            cx = self.rect.pos[0] + (self.rect.size[0] / 2)
            cy = self.rect.pos[1] + (self.rect.size[1] / 2)
            
            mag = (aim_x**2 + aim_y**2) ** 0.5
            ux, uy = aim_x / mag, aim_y / mag
            
            # Update transformation
            self.weapon_trans.x = cx
            self.weapon_trans.y = cy
            self.weapon_rot.angle = math.degrees(math.atan2(uy, ux))
            
            # Flip weapon vertically if aiming left so grips face down
            if ux < 0:
                self.weapon_scale.y = -1
            else:
                self.weapon_scale.y = 1
        else:
            self.c_tube.a = 0.0
            self.c_aim.a = 0.0


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