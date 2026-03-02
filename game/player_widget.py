from kivy.uix.widget import Widget
from kivy.graphics import Rectangle, Color, Ellipse
from kivy.clock import Clock

class PlayerWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # ตรวจสอบ Path ไฟล์ภาพให้ถูกต้อง
        self.anim_idle = ['assets/PTae/PTIdle/PTTG1.png', 'assets/PTae/PTIdle/PTTG2.png']
        self.anim_walk = ['assets/PTae/PTPushUp/PTaeTester1.png', 'assets/PTae/PTPushUp/PTaeTester2.png', 'assets/PTae/PTPushUp/PTaeTester3.png', 'assets/PTae/PTPushUp/PTaeTester4.png']
        self.idle_speed = 0.5 
        self.walk_speed = 0.15 
        self.current_anim = self.anim_idle
        self.current_anim_speed = self.idle_speed 
        self.frame_index = 0
        self.anim_timer = 0
        self.is_facing_right = True 
        
        with self.canvas:
            self.color_inst = Color(1, 1, 1, 1) 
            self.rect = Rectangle(source=self.current_anim[0], pos=(2500, 2500), size=(64, 64))
            
        with self.canvas.after:
            self.aim_color = Color(1, 0, 0, 0)
            self.aim_marker = Ellipse(size=(10, 10), pos=(0, 0)) 

        Clock.schedule_interval(self.animate, 1.0/60.0)

    def update_aim(self, is_aiming, aim_x, aim_y):
        if is_aiming and (aim_x != 0 or aim_y != 0):
            self.aim_color.a = 1.0 
            mag = (aim_x**2 + aim_y**2) ** 0.5
            if mag > 0:
                aim_x /= mag
                aim_y /= mag
            radius = 60 
            center_x = self.rect.pos[0] + (self.rect.size[0] / 2)
            center_y = self.rect.pos[1] + (self.rect.size[1] / 2)
            self.aim_marker.pos = (center_x + (aim_x * radius) - 5, center_y + (aim_y * radius) - 5)
        else:
            self.aim_color.a = 0.0 

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
        self.rect.tex_coords = (0,1,1,1,1,0,0,0) if self.is_facing_right else (1,1,0,1,0,0,1,0)

    def update_pos(self, new_pos):
        self.rect.pos = new_pos