"""game/projectile_widget.py"""
import math
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Ellipse, Rectangle, PushMatrix, PopMatrix, Translate, Rotate
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.widget import Widget

from game.utils import resolve_path, get_frames

class _Linear(Widget):
    def __init__(self, start_pos, target_pos, speed, damage, **kw):
        super().__init__(**kw)
        self.pos = start_pos; self.speed = speed; self.damage = damage
        self._lived = 0.0
        self._lifetime = 30.0
        dx = target_pos[0]-start_pos[0]; dy = target_pos[1]-start_pos[1]
        mag = math.hypot(dx, dy)
        self.direction = (dx/mag, dy/mag) if mag > 0 else (1, 0)

    def _move(self, dt):
        self.pos = (self.pos[0]+self.direction[0]*self.speed*dt,
                    self.pos[1]+self.direction[1]*self.speed*dt)


class EnemyProjectile(_Linear):
    _TEXTURES = None

    @classmethod
    def _load(cls):
        if cls._TEXTURES is None:
            cls._TEXTURES = []
            for i in range(4): # [Fix] Limit to 4 frames as requested
                path = resolve_path(f"assets/effect/rangershoot/1_{i}.png")
                if path:
                    try: cls._TEXTURES.append(CoreImage(path).texture)
                    except: pass

    def __init__(self, start_pos, target_pos, damage=10, **kw):
        super().__init__(start_pos, target_pos, speed=400.0, damage=damage, **kw)
        self._load(); self.size=(80,80); self._frame=0; self._at=0.0; self._fd=0.02
        angle = math.degrees(math.atan2(self.direction[1], self.direction[0]))
        with self.canvas:
            PushMatrix()
            self.tr = Translate(self.pos[0], self.pos[1])
            self.ro = Rotate(angle=angle, origin=(0,0))
            Color(0.6, 0.05, 0.5, 1) # [Fix] Dark Red-Purple (Red-Purple + Black tint)
            self.br = Rectangle(pos=(-40,-40), size=(80,80),
                                 texture=self._TEXTURES[0] if self._TEXTURES else None)
            PopMatrix()
        self.bind(pos=lambda i,v: [setattr(self.tr,'x',v[0]),setattr(self.tr,'y',v[1])])

    def update(self, dt):
        if self._TEXTURES:
            self._at += dt
            if self._at >= self._fd:
                self._at = 0.0
                if self._frame < len(self._TEXTURES)-1:
                    self._frame += 1; self.br.texture = self._TEXTURES[self._frame]
        self._move(dt)
        self._lived += dt
        return self._lived < self._lifetime


class PlayerBullet(_Linear):
    def __init__(self, start_pos, target_pos, speed, proj_range, damage, anim_frames=None, **kw):
        super().__init__(start_pos, target_pos, speed=speed, damage=damage, **kw)
        self._range=proj_range; self._traveled=0.0
        self._anim=anim_frames or []; self._ai=0; self._at=0.0; self._fd=0.06
        self._textures = []
        
        # คำนวณมุมตามทิศทาง (ใช้ Rotate ในทิศที่ยิง)
        self.angle = math.degrees(math.atan2(self.direction[1], self.direction[0]))
        
        if self._anim:
            for p in self._anim:
                path = resolve_path(p)
                if path:
                    try: self._textures.append(CoreImage(path).texture)
                    except: pass
        
        if self._textures:
            with self.canvas:
                PushMatrix()
                self.tr = Translate(self.pos[0], self.pos[1])
                self.ro = Rotate(angle=self.angle, origin=(0, 0))
                Color(1,1,1,1)
                self.rect = Rectangle(pos=(-20,-20), size=(40,40), texture=self._textures[0])
                PopMatrix()
        else:
            with self.canvas:
                Color(0.3,1,1,1)
                self._ell = Ellipse(pos=(start_pos[0]-6,start_pos[1]-6), size=(12,12))
        
        self.bind(pos=self._sync)

    def _sync(self, *_):
        if hasattr(self, 'tr'):
            self.tr.x = self.pos[0]
            self.tr.y = self.pos[1]
        elif hasattr(self,'_ell'):
            self._ell.pos = (self.pos[0]-6, self.pos[1]-6)

    def update(self, dt) -> bool:
        if self._textures and len(self._textures) > 1:
            self._at += dt
            if self._at >= self._fd:
                self._at = 0.0
                self._ai = (self._ai + 1) % len(self._textures)
                self.rect.texture = self._textures[self._ai]
                
        mx = self.direction[0] * self.speed * dt
        my = self.direction[1] * self.speed * dt
        self.pos = (self.pos[0] + mx, self.pos[1] + my)
        self._traveled += math.hypot(mx, my)
        return self._traveled < self._range


class RocketBullet(_Linear):
    """PTae Rocket Volley — สี่เหลี่ยมแดง"""
    def __init__(self, start_pos, target_pos, speed, proj_range, damage, **kw):
        super().__init__(start_pos, target_pos, speed=speed, damage=damage, **kw)
        self._range=proj_range; self._traveled=0.0; self.size=(12,32)
        with self.canvas:
            Color(1,0.2,0.2,1)
            self.rect=Rectangle(pos=(start_pos[0]-6,start_pos[1]-16), size=(12,32))
        self.bind(pos=lambda i,v: setattr(self.rect,'pos',(v[0]-6,v[1]-16)))

    def update(self, dt) -> bool:
        mx=self.direction[0]*self.speed*dt; my=self.direction[1]*self.speed*dt
        self.pos=(self.pos[0]+mx,self.pos[1]+my); self._traveled+=math.hypot(mx,my)
        return self._traveled < self._range


class RPGRocket(_Linear):
    """Monkey RPG — จรวดส้มระเบิด AoE เมื่อโดนศัตรู"""
    def __init__(self, start_pos, target_pos, speed, proj_range, damage,
                 splash_damage=60, splash_radius=150, **kw):
        super().__init__(start_pos, target_pos, speed=speed, damage=damage, **kw)
        self._range=proj_range; self._traveled=0.0
        self.splash_damage=splash_damage; self.splash_radius=splash_radius
        self.exploded=False; self.size=(16,40)
        with self.canvas:
            Color(1,0.4,0.0,1)
            self.rect=Rectangle(pos=(start_pos[0]-8,start_pos[1]-20), size=(16,40))
        self.bind(pos=lambda i,v: setattr(self.rect,'pos',(v[0]-8,v[1]-20)))

    def explode(self, game):
        self.exploded=True
        px,py=self.pos[0],self.pos[1]
        from game.skills import _hit_enemy, _show_aoe_vfx
        _show_aoe_vfx(game, px, py, self.splash_radius)
        for enemy in list(game.enemies):
            ex,ey=enemy.pos[0]+20,enemy.pos[1]+20
            if math.hypot(ex-px,ey-py)<=self.splash_radius:
                _hit_enemy(game, enemy, self.splash_damage)

    def update(self, dt) -> bool:
        if self.exploded: return False
        mx=self.direction[0]*self.speed*dt; my=self.direction[1]*self.speed*dt
        self.pos=(self.pos[0]+mx,self.pos[1]+my); self._traveled+=math.hypot(mx,my)
        return self._traveled < self._range


class HealthPickup(Widget):
    def __init__(self, pos=(0,0), heal_amount=25, size=(28,28), texture_path=None, heal_percent=0, **kw):
        kw.setdefault('size_hint',(None,None)); kw.setdefault('size', size)
        super().__init__(**kw)
        self.pos=pos; self.heal_amount=heal_amount; self.size=size; self.heal_percent=heal_percent
        
        # ปรับขนาดตัวหนังสือตามขนาดกล่อง
        f_size = 10 if size[0] <= 16 else 16
        
        self.tex = None
        if texture_path:
            full_path = resolve_path(texture_path)
            if full_path:
                try:
                    self.tex = CoreImage(full_path).texture
                except: pass

        with self.canvas:
            if self.tex:
                Color(1, 1, 1, 1)
                self._rect = Rectangle(pos=self.pos, size=self.size, texture=self.tex)
            else:
                # Fallback: วาดกล่องสีถ้าไม่มี Texture
                if heal_amount >= 30:
                    Color(0, 1, 0.6, 1) # Cyan-Green for Large
                else:
                    Color(0, 1, 0.4, 1) # Standard Green
                self._rect = Rectangle(pos=self.pos, size=self.size)
            
        # สร้าง Label เฉพาะกรณีที่ไม่มี Texture (กันรก) หรือจะโชว์ทับก็ได้
        if not self.tex:
            self._lbl = Label(text="+", size_hint=(None,None), size=self.size, pos=self.pos,
                            color=(1,1,1,1), bold=True, font_size=f_size)
            self.add_widget(self._lbl)
        else:
            self._lbl = None

        self.bind(pos=self._sync)

    def _sync(self, i, v):
        if hasattr(self, '_rect'): self._rect.pos = v
        if self._lbl: self._lbl.pos = v


class MagnetPickup(Widget):
    """แม่เหล็กดูด EXP เข้าหาตัว"""
    def __init__(self, pos=(0,0), duration=8.0, texture_path=None, **kw):
        kw.setdefault('size_hint',(None,None)); kw.setdefault('size',(28,28))
        super().__init__(**kw)
        self.pos=pos; self.duration=duration; self.size=(28,28)
        with self.canvas:
            Color(0.2, 0.4, 1.0, 1) # สีน้ำเงิน
            self._rect=Rectangle(pos=self.pos, size=self.size)
        self._lbl=Label(text="U",size_hint=(None,None),size=self.size,pos=self.pos,
                        color=(1,1,1,1),bold=True,font_size=16)
        self.add_widget(self._lbl)
        self.bind(pos=self._sync)

    def _sync(self,i,v):
        if hasattr(self,'_rect'): self._rect.pos=v
        if hasattr(self,'_lbl'): self._lbl.pos=v


class GlobalMagnetPickup(Widget):
    """แม่เหล็กดูด EXP เข้าหาตัว (ดูดทั้งแมพ)"""
    def __init__(self, pos=(0,0), duration=8.0, texture_path=None, **kw):
        kw.setdefault('size_hint',(None,None)); kw.setdefault('size',(32,32))
        super().__init__(**kw)
        self.pos=pos; self.duration=duration; self.size=(32,32)
        with self.canvas:
            Color(0.8, 0.2, 1.0, 1) # สีม่วง
            self._rect=Rectangle(pos=self.pos, size=self.size)
        self._lbl=Label(text="UU",size_hint=(None,None),size=self.size,pos=self.pos,
                        color=(1,1,1,1),bold=True,font_size=18)
        self.add_widget(self._lbl)
        self.bind(pos=self._sync)

    def _sync(self,i,v):
        if hasattr(self,'_rect'): self._rect.pos=v
        if hasattr(self,'_lbl'): self._lbl.pos=v



class ExpOrb(Widget):
    """EXP orb ที่ drop จากศัตรู — ขนาด 8x8 พร้อมแอนิเมชันสีรุ้ง (เหลือง-เขียว)"""
    def __init__(self, pos=(0,0), exp_amount=10, texture_path=None, **kw):
        kw.setdefault('size_hint',(None,None)); kw.setdefault('size',(8,8))
        super().__init__(**kw)
        self.pos=pos; self.exp_amount=exp_amount; self.size=(8,8)
        self._hue = 0.16 # เริ่มที่สีเหลือง
        
        with self.canvas:
            self.color_inst = Color(1, 1, 0, 1) # Fallback RGB
            # กำหนดเป็นสี่เหลี่ยมขนาด 2x2 (Pixel look)
            self._shape = Rectangle(pos=self.pos, size=self.size)
            
        self.bind(pos=lambda i,v: setattr(self._shape,'pos',v))
        # 🌟 [Optimization] เลิกใช้ Clock แยกรายก้อน (หมื่นก้อนหมื่น Clock)
        # จะใช้วิธีอัปเดตสีจากส่วนกลาง หรือใช้การผูกกับเวลาส่วนกลาง

    def update_visual(self, global_time):
        # 🌟 [Optimization] คำนวณสีจากเวลาส่วนกลางที่ส่งมา
        # ช่วง hue 0.15 -> 0.40: R จะค่อยๆ ลดลงจาก 1 -> 0
        hue = 0.15 + (global_time * 0.5) % 0.25
        r = max(0, min(1, 1.0 - (hue - 0.15) * 4.0)) 
        self.color_inst.rgb = (r, 1.0, 0.1)

    def on_expire(self):
        pass


class DinoProjectile(_Linear):
    """PTae Dino Summon — จรวดรูปไดโน (fallback สีเขียว)"""
    def __init__(self, start_pos, target_pos, speed, proj_range, damage, **kw):
        super().__init__(start_pos, target_pos, speed=speed, damage=damage, **kw)
        self._range = proj_range; self._traveled = 0.0; self.size = (28, 28)
        with self.canvas:
            Color(0.2, 0.9, 0.3, 1)
            self.rect = Rectangle(pos=(start_pos[0]-14, start_pos[1]-14), size=(28, 28))
        self.bind(pos=lambda i, v: setattr(self.rect, 'pos', (v[0]-14, v[1]-14)))

    def update(self, dt) -> bool:
        mx = self.direction[0]*self.speed*dt; my = self.direction[1]*self.speed*dt
        self.pos = (self.pos[0]+mx, self.pos[1]+my); self._traveled += math.hypot(mx, my)
        return self._traveled < self._range

class HomingDino(_Linear):
    """PTae Skill 2 — ไดโนเสาร์ติดตามศัตรู (homing)"""
    TURN_SPEED = 4.0   # rad/s
    _TEXTURES = None

    @classmethod
    def _load(cls):
        if cls._TEXTURES is None:
            cls._TEXTURES = []
            for i in range(18):
                path = resolve_path(f"assets/PTae/skill2/frame_{i:02d}_delay-0.05s.png")
                if path:
                    try: cls._TEXTURES.append(CoreImage(path).texture)
                    except Exception as e: print(f"[HomingDino] Error load {i}: {e}")
            print(f"[HomingDino] Loaded {len(cls._TEXTURES)} frames")

    def __init__(self, start_pos, target_ref, speed=320, proj_range=900, damage=20, game=None, **kw):
        # target_ref = enemy widget (ติดตาม live pos)
        tx = target_ref.pos[0] + 20
        ty = target_ref.pos[1] + 20
        super().__init__(start_pos, (tx, ty), speed=speed, damage=damage, **kw)
        self._load()
        self._frame = 0
        self._at = 0.0
        self._fd = 0.05

        self._target = target_ref
        self._game = game  # 🌟 เก็บ reference ของเกมเพื่อหาเป้าหมายใหม่
        self._range = proj_range
        self._traveled = 0.0
        sz = 64 # [Fix] Reduced size from 100
        self.size = (sz, sz)
        offset = sz / 2
        with self.canvas:
            Color(1, 1, 1, 1) # [Fix] Revert to original bright colors
            self.dino_rect = Rectangle(
                pos=(start_pos[0]-offset, start_pos[1]-offset), 
                size=(sz, sz),
                texture=self._TEXTURES[0] if self._TEXTURES else None)
        self.bind(pos=lambda i, v: setattr(self.dino_rect, 'pos', (v[0]-offset, v[1]-offset)))

    def update(self, dt) -> bool:
        # ถ้า target เดิมตาย ลองหาตัวใหม่
        if not (self._target and self._target.parent and getattr(self._target, 'hp', 0) > 0):
            if hasattr(self, '_game') and self._game and self._game.enemies:
                # หาตัวที่ใกล้ HomingDino ที่สุด
                nearest_e = min(self._game.enemies, key=lambda e: math.hypot((e.pos[0]+20) - self.pos[0], (e.pos[1]+20) - self.pos[1]))
                self._target = nearest_e
        
        # ถ้ายังมี target ให้หมุนทิศทางเข้าหา
        if self._target and self._target.parent and getattr(self._target, 'hp', 0) > 0:
            tx = self._target.pos[0] + 20 - self.pos[0]
            ty = self._target.pos[1] + 20 - self.pos[1]
            dist = math.hypot(tx, ty)
            if dist > 0:
                desired_angle = math.atan2(ty, tx)
                current_angle = math.atan2(self.direction[1], self.direction[0])
                diff = (desired_angle - current_angle + math.pi) % (2*math.pi) - math.pi
                turn = max(-self.TURN_SPEED*dt, min(self.TURN_SPEED*dt, diff))
                new_angle = current_angle + turn
                self.direction = (math.cos(new_angle), math.sin(new_angle))
                
        mx = self.direction[0]*self.speed*dt
        my = self.direction[1]*self.speed*dt
        self.pos = (self.pos[0]+mx, self.pos[1]+my)
        self._traveled += math.hypot(mx, my)

        # [Animation] อัปเดตเฟรม
        if self._TEXTURES:
            self._at += dt
            if self._at >= self._fd:
                self._at = 0.0
                self._frame = (self._frame + 1) % len(self._TEXTURES)
                self.dino_rect.texture = self._TEXTURES[self._frame]

        return self._traveled < self._range


class LethalHomingMissile(_Linear):
    """Final Boss lethal projectile - targets player and deals 50% max HP damage"""
    TURN_SPEED = 3.5

    def __init__(self, start_pos, game, speed=220, proj_range=2500, **kw):
        # Target is player
        px, py = game.player_pos[0]+32, game.player_pos[1]+32
        super().__init__(start_pos, (px, py), speed=speed, damage=0, **kw) # Damage handled in update/collision
        self.game = game
        self._range = proj_range
        self._traveled = 0.0
        self.size = (40, 40)
        with self.canvas:
            Color(1, 0, 0, 1) # Solid bright red
            self.rect = Rectangle(pos=(start_pos[0]-20, start_pos[1]-20), size=(40, 40))
            Color(1, 1, 1, 1)
            self.inner = Ellipse(pos=(start_pos[0]-10, start_pos[1]-10), size=(20, 20))
        self.bind(pos=self._update_graphics)

    def _update_graphics(self, i, v):
        self.rect.pos = (v[0]-20, v[1]-20)
        self.inner.pos = (v[0]-10, v[1]-10)

    def update(self, dt) -> bool:
        if not self.game or self.game.is_dead:
            return False
            
        self._lived += dt
        if self._lived >= self._lifetime:
            return False

        # Homm towards player
        tx, ty = self.game.player_pos[0]+32, self.game.player_pos[1]+32
        dx, dy = tx - self.pos[0], ty - self.pos[1]
        dist = math.hypot(dx, dy)
        
        # Check collision with player
        if dist < 50:
            # Deal 50% max HP
            max_hp = self.game.player_stats.hp if self.game.player_stats else 100
            self.game.take_damage(max_hp * 0.5)
            from game.skills import _show_aoe_vfx
            _show_aoe_vfx(self.game, self.pos[0], self.pos[1], 150)
            return False # Destroy self
            
        if dist > 0:
            desired_angle = math.atan2(dy, dx)
            current_angle = math.atan2(self.direction[1], self.direction[0])
            diff = (desired_angle - current_angle + math.pi) % (2*math.pi) - math.pi
            turn = max(-self.TURN_SPEED*dt, min(self.TURN_SPEED*dt, diff))
            new_angle = current_angle + turn
            self.direction = (math.cos(new_angle), math.sin(new_angle))
            
        mx = self.direction[0]*self.speed*dt
        my = self.direction[1]*self.speed*dt
        self.pos = (self.pos[0]+mx, self.pos[1]+my)
        self._traveled += math.hypot(mx, my)
        return self._traveled < self._range
class DinoBeam(Widget):
    """PTae Skill 3 — ลำแสงตรงไปตามทิศเมาส์ ทำดาเมจทุก enemy ที่ผ่าน"""
    DEFAULT_WIDTH = 160
    DURATION = 0.55
    SPEED = 900
    _TEXTURES = None

    @classmethod
    def _load(cls):
        if cls._TEXTURES is None:
            cls._TEXTURES = []
            for i in range(11):
                path = resolve_path(f"assets/PTae/skill3/frame_{i:02d}_delay-0.05s.png")
                if path:
                    try: cls._TEXTURES.append(CoreImage(path).texture)
                    except: pass
            path11 = resolve_path("assets/PTae/skill3/frame_11_delay-0.02s.png")
            if path11:
                try: cls._TEXTURES.append(CoreImage(path11).texture)
                except: pass
            print(f"[DinoBeam] Loaded {len(cls._TEXTURES)} frames")

    def __init__(self, start_pos, direction, damage, length=1200, width=None, **kw):
        kw.setdefault('size_hint', (None, None))
        kw.setdefault('size', (1, 1))
        super().__init__(**kw)
        self.pos = start_pos
        self.damage = damage
        self._dir = direction
        self._length = length
        self._width = width if width is not None else self.DEFAULT_WIDTH
        self._traveled = 0.0
        self._hit_enemies: set = set()
        self._alive = True

        self._load()
        self._frame = 0
        self._at = 0.0
        self._fd = 0.05

        angle_deg = math.degrees(math.atan2(direction[1], direction[0]))
        with self.canvas:
            PushMatrix()
            self._tr = Translate(start_pos[0], start_pos[1])
            Rotate(angle=angle_deg, origin=(0, 0))
            Color(1, 1, 1, 1)
            self._rect = Rectangle(
                pos=(0, -self._width // 2),
                size=(0, self._width),
                texture=self._TEXTURES[0] if self._TEXTURES else None)
            PopMatrix()
        self.bind(pos=lambda i, v: setattr(self._tr, 'x', v[0]) or
                                    setattr(self._tr, 'y', v[1]))
        Clock.schedule_once(self._expire, self.DURATION)

    def update(self, dt: float, game) -> bool:
        if not self._alive:
            return False
        step = self.SPEED * dt
        self._traveled = min(self._traveled + step, self._length)

        # ขยาย beam ตาม traveled
        self._rect.size = (self._traveled, self._width)
        
        # [Animation] เปลี่ยนเฟรมตามเวลา
        if self._TEXTURES:
            self._at += dt
            if self._at >= self._fd:
                self._at = 0.0
                self._frame = (self._frame + 1) % len(self._TEXTURES)
                self._rect.texture = self._TEXTURES[self._frame]

        # เช็ค hit ทุก enemy ในแนว beam
        sx, sy = self.pos
        perp = (-self._dir[1], self._dir[0])
        half_w = self._width / 2

        for enemy in list(game.enemies):
            eid = id(enemy)
            if eid in self._hit_enemies:
                continue
            ecx = enemy.pos[0] + 20
            ecy = enemy.pos[1] + 20
            along = (ecx - sx)*self._dir[0] + (ecy - sy)*self._dir[1]
            perp_d = abs((ecx - sx)*perp[0] + (ecy - sy)*perp[1])
            if 0 <= along <= self._traveled and perp_d <= half_w:
                from game.skills import _hit_enemy
                _hit_enemy(game, enemy, self.damage)
                self._hit_enemies.add(eid)

        return self._alive

    def _expire(self, _dt):
        self._alive = False
        if self.parent:
            self.parent.remove_widget(self)

# ── Final Boss Specials ───────────────────────────────────

class BossSpiralMissile(_Linear):
    """Missile that spirals outward"""
    def __init__(self, start_pos, angle, speed, damage, spiral_speed=1.5, **kw):
        # We'll use self.direction but rotate it over time
        dx, dy = math.cos(angle), math.sin(angle)
        super().__init__(start_pos, (start_pos[0]+dx, start_pos[1]+dy), speed=speed, damage=damage, **kw)
        self.angle = angle
        self.spiral_speed = spiral_speed
        self.size = (20, 20)
        with self.canvas:
            Color(1, 1, 0, 1) # Yellow
            self.ell = Ellipse(pos=(start_pos[0]-10, start_pos[1]-10), size=(20, 20))
        self.bind(pos=lambda i, v: setattr(self.ell, 'pos', (v[0]-10, v[1]-10)))

    def update(self, dt):
        # Move straight in the initial direction to form an outward spiral pattern
        self._move(dt)
        self._lived += dt
        return self._lived < self._lifetime

class BossBeamHighlight(Widget):
    """Visual warning for 8-way beam"""
    def __init__(self, pos, angle, length=2000, width=40, duration=2.0, rotation_speed=0, **kw):
        super().__init__(**kw)
        self.pos = pos
        self.angle = math.degrees(angle)
        self.rotation_speed = rotation_speed
        with self.canvas:
            PushMatrix()
            self.color = Color(1, 0, 0, 0.3)
            self.rot = Rotate(angle=self.angle, origin=self.pos)
            self.rect = Rectangle(pos=(self.pos[0], self.pos[1]-width/2), size=(length, width))
            PopMatrix()
        Clock.schedule_once(lambda dt: self.parent.remove_widget(self) if self.parent else None, duration)

    def update_rotation(self, dt):
        self.angle += self.rotation_speed * dt
        self.rot.angle = self.angle

class BossJumpHighlight(Widget):
    """Visual warning for jump slam"""
    def __init__(self, pos, radius=300, duration=5.0, **kw):
        super().__init__(**kw)
        self.pos = pos
        self.radius = radius
        with self.canvas:
            self.color = Color(1, 0, 0, 0.2)
            self.ell = Ellipse(pos=(pos[0]-radius, pos[1]-radius), size=(radius*2, radius*2))
            Color(1, 0, 0, 0.5)
            self.line = Ellipse(pos=(pos[0]-radius, pos[1]-radius), size=(radius*2, radius*2)) # Placeholder for visual
        Clock.schedule_once(lambda dt: self.parent.remove_widget(self) if self.parent else None, duration)

class FinalBossExplosion(Widget):
    """Massive death explosion widget"""
    def __init__(self, pos, radius=1000, fuse=10.0, game=None, **kw):
        super().__init__(**kw)
        self.pos = pos
        self.radius = radius
        self.fuse = fuse
        self.game = game
        self._elapsed = 0.0
        with self.canvas:
            self.color = Color(1, 0, 0, 0.1)
            self.ell = Ellipse(pos=(pos[0]-radius, pos[1]-radius), size=(radius*2, radius*2))
        
        self.lbl = Label(text="SELF-DESTRUCT: 10", font_size=50, bold=True, color=(1,0,0,1), pos=pos)
        self.add_widget(self.lbl)
        Clock.schedule_interval(self._tick, 1.0)
        Clock.schedule_once(self._explode, fuse)

    def _tick(self, dt):
        self._elapsed += 1
        rem = int(self.fuse - self._elapsed)
        self.lbl.text = f"SELF-DESTRUCT: {rem}"
        self.color.a = 0.1 + (self._elapsed / self.fuse) * 0.4
        return rem > 0

    def _explode(self, dt):
        if self.game:
            px, py = self.game.player_pos[0]+32, self.game.player_pos[1]+32
            if math.hypot(px-self.pos[0], py-self.pos[1]) < self.radius:
                self.game.take_damage(999999) # Instant death
            from game.skills import _show_aoe_vfx
            _show_aoe_vfx(self.game, self.pos[0], self.pos[1], self.radius)
        if self.parent: self.parent.remove_widget(self)


class BossSpike(Widget):
    """Spikes that pop up from the ground with a warning"""
    def __init__(self, pos, damage=45, radius=80, warning_duration=1.5, game=None, **kw):
        super().__init__(**kw)
        self.pos = pos
        self.damage = damage
        self.radius = radius
        self.game = game
        self.active = False
        
        with self.canvas:
            self.warning_color = Color(1, 0, 0, 0.4)
            self.warning_ell = Ellipse(pos=(pos[0]-radius, pos[1]-radius), size=(radius*2, radius*2))
            
            self.spike_color = Color(1, 1, 1, 0) # Initially invisible
            self.spike_rect = Rectangle(pos=(pos[0]-radius*0.7, pos[1]-radius*0.7), size=(radius*1.4, radius*1.4))
            
        Clock.schedule_once(self._activate, warning_duration)
        Clock.schedule_once(self._remove, warning_duration + 0.5)

    def _activate(self, dt):
        self.active = True
        self.warning_color.a = 0
        self.spike_color.a = 1.0 # Show spike
        # Check damage
        if self.game:
            px, py = self.game.player_pos[0]+32, self.game.player_pos[1]+32
            if math.hypot(px-self.pos[0], py-self.pos[1]) < self.radius:
                self.game.take_damage(self.damage)

    def _remove(self, dt):
        if self.parent:
            self.parent.remove_widget(self)

class BombWidget(Widget):
    """Lostman Bomb Trap — countdown widget แสดงตัวเลข 3-2-1 และ C4 sprite"""
    _TEXTURES = None

    @classmethod
    def _load(cls):
        if cls._TEXTURES is None:
            cls._TEXTURES = []
            for i in range(1, 5):
                path = resolve_path(f"assets/Lostman/skill3/c4_trap{i}.png")
                if path:
                    try: cls._TEXTURES.append(CoreImage(path).texture)
                    except: pass

    def __init__(self, pos=(0,0), fuse=3.0, damage=100, radius=160, **kw):
        kw.setdefault('size_hint', (None, None)); kw.setdefault('size', (48, 48))
        super().__init__(**kw)
        self._load()
        self.pos = pos; self.damage = damage; self.radius = radius; self.size = (48, 48)
        self._fuse = fuse; self._elapsed = 0.0
        self._frame = 0; self._at = 0.0; self._fd = 0.15
        
        with self.canvas:
            if self._TEXTURES:
                Color(1, 1, 1, 1)
                self._bg = Rectangle(pos=self.pos, size=self.size, texture=self._TEXTURES[0])
            else:
                Color(0.9, 0.5, 0.1, 1)
                self._bg = Ellipse(pos=self.pos, size=self.size)
                
        self._lbl = Label(
            text=str(int(fuse)), font_size=20, bold=True,
            color=(1, 1, 1, 1), size_hint=(None, None), size=self.size, pos=self.pos,
            halign='center', valign='middle'
        )
        self._lbl.bind(size=lambda i, v: setattr(i, 'text_size', v))
        self.add_widget(self._lbl)
        self.bind(pos=self._sync)
        
        # นับถอยหลังทุกๆ 1 วิ
        Clock.schedule_interval(self._tick, 1.0)
        # รัน anim ทุกเสี้ยววิ
        Clock.schedule_interval(self._anim_tick, 1/60.0)

    def _sync(self, i, v):
        if hasattr(self, '_bg'): self._bg.pos = v
        if hasattr(self, '_lbl'): self._lbl.pos = v

    def _tick(self, dt):
        self._elapsed += 1
        remaining = max(0, int(self._fuse - self._elapsed))
        if hasattr(self, '_lbl'): self._lbl.text = str(remaining)
        if remaining <= 0: return False

    def _anim_tick(self, dt):
        if self._TEXTURES:
            self._at += dt
            if self._at >= self._fd:
                self._at = 0.0
                self._frame = (self._frame + 1) % len(self._TEXTURES)
                self._bg.texture = self._TEXTURES[self._frame]

class BossBombWidget(Widget):
    """Boss Bomb — explosion that damages the player after 3 seconds"""
    def __init__(self, pos=(0,0), fuse=3.0, damage=100, radius=200, game=None, **kw):
        kw.setdefault('size_hint', (None, None)); kw.setdefault('size', (64, 64))
        super().__init__(**kw)
        self.pos = pos; self.damage = damage; self.radius = radius; self.size = (64, 64)
        self._fuse = fuse; self._elapsed = 0.0
        self._game = game
        
        with self.canvas:
            Color(1, 0.2, 0.2, 0.8) # สีแดงน่ากลัว
            self._bg = Ellipse(pos=self.pos, size=self.size)
        
        self._lbl = Label(
            text=str(int(fuse)), font_size=32, bold=True,
            color=(1, 1, 1, 1), size_hint=(None, None), size=(64, 64), pos=self.pos,
            halign='center', valign='middle'
        )
        self._lbl.bind(size=lambda i, v: setattr(i, 'text_size', v))
        self.add_widget(self._lbl)
        self.bind(pos=self._sync)
        
        Clock.schedule_interval(self._tick, 1.0)
        Clock.schedule_once(self._explode, fuse)

    def _sync(self, i, v):
        if hasattr(self, '_bg'): self._bg.pos = v
        if hasattr(self, '_lbl'): self._lbl.pos = v

    def _tick(self, dt):
        self._elapsed += 1
        remaining = max(0, int(self._fuse - self._elapsed))
        if hasattr(self, '_lbl'): self._lbl.text = str(remaining)
        if remaining <= 0: return False
        
    def _explode(self, dt):
        if not self._game: return
        px = self.pos[0] + 32
        py = self.pos[1] + 32
        
        # วาดวงกลมวงกว้างโชว์รัศมีระเบิด (ใช้ effect)
        from game.skills import _show_aoe_vfx
        _show_aoe_vfx(self._game, px, py, self.radius)
        
        # ดาเมจคนเล่นที่อยู่ในรัศมี
        player_x = self._game.player_pos[0] + 32
        player_y = self._game.player_pos[1] + 32
        dist = math.hypot(player_x - px, player_y - py)
        if dist <= self.radius:
            self._game.take_damage(self.damage)
            
        if self.parent:
            self.parent.remove_widget(self)