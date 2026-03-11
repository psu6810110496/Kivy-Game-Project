from kivy.uix.widget import Widget
from kivy.graphics import Rectangle, Color, Line, Triangle, PushMatrix, PopMatrix, Translate, Rotate, Scale
from kivy.clock import Clock
import math
from game.utils import resolve_path, get_frames
from kivy.core.image import Image as CoreImage

class PlayerWidget(Widget):
    def __init__(self, idle_frames, walk_frames, start_pos=(2500, 2500), character_name=None, **kwargs):
        super().__init__(**kwargs)
        
        # --- 🌟 Spritesheet Logic (Pygame style) 🌟 ---
        # ถ้า idle_frames/walk_frames ส่งมาเป็น string path (จบด้วย .png) และไม่ใช่ list 
        # เราจะพยายามแบ่งเฟรมจาก sheet นั้น
        
        self.anim_idle = []
        self.anim_walk = []
        
        if isinstance(idle_frames, str) and idle_frames.endswith(".png"):
            # แบ่งเฟรมจาก sheet (64x64 ตามที่ user แนะนำ)
            self.anim_idle = get_frames(idle_frames, 64, 64, 4, row=0) # ประเมินว่ามี 4 เฟรมแถวแรก
        elif isinstance(idle_frames, list):
            self.anim_idle = idle_frames
            
        if isinstance(walk_frames, str) and walk_frames.endswith(".png"):
            self.anim_walk = get_frames(walk_frames, 64, 64, 6, row=0) # ประเมินว่ามี 6 เฟรม
        elif isinstance(walk_frames, list):
            self.anim_walk = walk_frames

        # Fallback ถ้าโหลดไม่ได้
        if not self.anim_idle: self.anim_idle = idle_frames if isinstance(idle_frames, list) else [idle_frames]
        if not self.anim_walk: self.anim_walk = walk_frames if isinstance(walk_frames, list) else [walk_frames]

        # Convert สตริง Path เป็น Texture เสมอ เพื่อให้ใช้ .texture ได้ใน animate
        def load_tex_list(lst):
            res = []
            for item in lst:
                if isinstance(item, str):
                    path = resolve_path(item)
                    if path:
                        try: res.append(CoreImage(path).texture)
                        except: pass
                else:
                    res.append(item)
            return res

        self.anim_idle = load_tex_list(self.anim_idle)
        self.anim_walk = load_tex_list(self.anim_walk)
        self.idle_speed = 0.5 
        self.walk_speed = 0.15 
        self.current_anim = self.anim_idle
        self.current_anim_speed = self.idle_speed 
        self.frame_index = 0
        self.anim_timer = 0
        self.is_facing_right = True 
        
        with self.canvas:
            self.color_inst = Color(1, 1, 1, 1) 
            first_frame = self.current_anim[0] if self.current_anim else None
            # ตอนนี้ทุกอย่างเป็น Texture แล้ว
            self.rect = Rectangle(texture=first_frame, pos=start_pos, size=self.size)
            if first_frame:
                self.rect.tex_coords = first_frame.tex_coords
            
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
        """จัดการ Animation และ Flip ทิศทาง (optimized เพื่อกันบัคกะพริบ)"""
        # 1. เช็คสถานะการกลับด้าน
        flipped = False
        old_facing = getattr(self, "_last_facing", None)
        if old_facing != self.is_facing_right:
            flipped = True
            self._last_facing = self.is_facing_right

        # 2. จัดการเปลี่ยนเฟรม
        frame_changed = False
        if self.current_anim:
            self.anim_timer += dt
            if self.anim_timer >= self.current_anim_speed:
                self.anim_timer = 0
                self.frame_index = (self.frame_index + 1) % len(self.current_anim)
                tex = self.current_anim[self.frame_index]
                self.rect.texture = tex
                frame_changed = True
        
        # 3. อัปเดตพิกัด UV เฉพาะที่จำเป็น
        tex = self.rect.texture
        if (frame_changed or flipped or not hasattr(self, "_initialized_uv")) and tex:
            tc = tex.tex_coords
            if self.is_facing_right:
                self.rect.tex_coords = tc
            else:
                self.rect.tex_coords = (tc[2], tc[3], tc[0], tc[1], tc[6], tc[7], tc[4], tc[5])
            self._initialized_uv = True

    def on_size(self, *args):
        if hasattr(self, "rect"):
            self.rect.size = self.size

    def update_pos(self, new_pos):
        self.rect.pos = new_pos