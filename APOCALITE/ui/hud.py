"""
ui/hud.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ประกอบด้วย:
  HealthBar        — แถบ HP แบบ custom draw
  SkillSlotBox     — แสดงสกิลสล็อต 3 ช่อง
  HUD              — FloatLayout หลัก (HP bar, EXP bar, Wave, Enemy count)
  CountdownOverlay — นับถอยหลัง 3-2-1 ก่อนเริ่มเกม
"""
import os

import kivy.app
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.properties import NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.widget import Widget
from kivy.uix.modalview import ModalView

from ui.level_up import LevelUpPopup


# ═══════════════════════════════════════════════════════════
#  HealthBar — Custom HP bar widget
# ═══════════════════════════════════════════════════════════
class HealthBar(Widget):
    """แถบ HP สีแดง บน background สีเทาเข้ม"""

    current_hp = NumericProperty(100)
    max_hp = NumericProperty(100)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._redraw, size=self._redraw,
                  current_hp=self._redraw, max_hp=self._redraw)

    def _redraw(self, *_args):
        self.canvas.clear()
        with self.canvas:
            Color(0.2, 0.2, 0.2, 1)
            Rectangle(pos=self.pos, size=self.size)
            Color(0.8, 0.1, 0.1, 1)
            ratio = max(0, min(self.current_hp / max(self.max_hp, 1), 1))
            Rectangle(pos=self.pos, size=(self.width * ratio, self.height))


# ═══════════════════════════════════════════════════════════
#  SkillSlotBox — 3 skill slots แสดง cooldown
# ═══════════════════════════════════════════════════════════
class SkillSlotBox(BoxLayout):
    """3 ปุ่มสกิลมุมซ้ายล่าง แสดง name + cooldown หรือ Stack (เรียงตำแหน่ง S3, S1, S2)"""

    SLOT_COUNT = 3
    SLOT_SIZE = 128

    def __init__(self, **kwargs):
        normal_size = self.SLOT_SIZE
        large_size = self.SLOT_SIZE * 1.25
        total_width = (normal_size * 2) + large_size + (10 * 2)
        
        super().__init__(
            orientation="horizontal",
            size_hint=(None, None),
            size=(total_width, large_size),
            pos_hint={"x": 0.02, "y": 0.02},
            spacing=10,
            **kwargs,
        )
        self.slots: list[tuple[Button, Label]] = []
        
        # 🌟 กำหนดลำดับ Index ของสกิลที่จะให้แสดงผล (2 = S3, 0 = S1, 1 = S2)
        self.skill_indices = [2, 0, 1]
        
        for skill_idx in self.skill_indices:
            # ถ้าเป็น S3 (index 2) ให้ใช้ตัวคูณ 1.25
            multiplier = 1.25 if skill_idx == 2 else 1.0
            current_size = self.SLOT_SIZE * multiplier

            # Container เพื่อให้วาง Label ทับ Button ได้ (ใช้ FloatLayout)
            slot_container = FloatLayout(size_hint=(None, None), size=(current_size, current_size))
            
            btn = Button(
                text=f"S{skill_idx + 1}",
                font_size=16 * (1.2 if skill_idx == 2 else 1.0),
                bold=True,
                size_hint=(1, 1),
                pos_hint={"x": 0, "y": 0},
                background_normal="",
                background_color=(0.2, 0.2, 0.2, 0.6),
                color=(1, 1, 1, 1),
                text_size=(current_size - 10, None),
                halign="center",
                valign="middle"
            )
            
            # Label แสดงเลเวล (มุมขวาบน)
            lvl_lbl = Label(
                text="",
                font_size=14 * (1.1 if skill_idx == 2 else 1.0),
                bold=True,
                size_hint=(None, None),
                size=(50, 25),
                pos_hint={"right": 1, "top": 1},
                color=(1, 1, 0, 1), # สีเหลืองสดใส
                outline_width=2,
                outline_color=(0, 0, 0, 1)
            )
            
            slot_container.add_widget(btn)
            slot_container.add_widget(lvl_lbl)
            self.add_widget(slot_container)
            
            self.slots.append((btn, lvl_lbl))

    def update(self, skills: list):
        """รีเฟรชข้อความ / สี / เลเวล ทุก frame โดยดึงข้อมูลตามลำดับที่จัดไว้"""
        for (btn, lvl_lbl), skill_idx in zip(self.slots, self.skill_indices):
            skill = skills[skill_idx] if skill_idx < len(skills) else None

            if skill is None:
                btn.text = f"S{skill_idx + 1}\n[empty]"
                btn.background_color = (0.15, 0.15, 0.15, 0.5)
                lvl_lbl.text = "" # ซ่อนเวลถ้าไม่มีสกิล
                continue

            # อัปเดตเลเวล
            lvl_lbl.text = f"LV.{skill.level}"

            # อัปเดตข้อมูลการใช้งาน (CD / Stacks)
            stacks_val = getattr(skill, 'stacks', getattr(skill, 'current_stacks', None))
            max_stacks_val = getattr(skill, 'MAX_STACKS', getattr(skill, 'max_stacks', None))
            if stacks_val is not None:
                full = "●" * stacks_val
                empty = "○" * max(0, (max_stacks_val or 3) - stacks_val)
                btn.text = f"{skill.name}\n[LMB] {full}{empty}"
                btn.background_color = (0.4, 0.1, 0.7, 1) if stacks_val > 0 else (0.2, 0.2, 0.2, 0.6)
            else:
                cd = max(0.0, getattr(skill, '_timer', 0.0))
                btn.text = f"{skill.name}\nCD: {cd:.1f}s"
                btn.background_color = (0.2, 0.6, 0.2, 1) if cd <= 0 else (0.2, 0.2, 0.2, 0.6)


# ═══════════════════════════════════════════════════════════
#  Minimap — Minimap ขวาบน แสดงตำแหน่งผู้เล่น (เขียว) และศัตรู (แดง)
#  World Size: 5000x5000
# ═══════════════════════════════════════════════════════════
class Minimap(Widget):
    def __init__(self, game, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.size_hint = (None, None)
        self.size = (180, 180)
        self.pos_hint = {"right": 0.98, "top": 0.90}
        
    def update(self, dt):
        self.canvas.clear()
        if not self.game: return
        
        with self.canvas:
            # BG Layer (Glassmorphism look)
            Color(0, 0, 0, 0.5)
            from kivy.graphics import RoundedRectangle
            RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
            
            # Border
            Color(0.2, 0.7, 1.0, 0.3)
            from kivy.graphics import Line
            Line(rounded_rectangle=(self.x, self.y, self.width, self.height, 10), width=1.2)

            # Map scaling (World is 5000x5000 based on engine.py)
            world_w, world_h = 5000, 5000
            scale_x = self.width / world_w
            scale_y = self.height / world_h

            # Draw Enemies (Red dots)
            from kivy.graphics import Ellipse
            Color(1, 0.2, 0.2, 0.8)
            for enemy in getattr(self.game, 'enemies', []):
                ex, ey = enemy.pos
                nx = self.x + (ex * scale_x)
                ny = self.y + (ey * scale_y)
                nx = max(self.x + 2, min(self.right - 2, nx))
                ny = max(self.y + 2, min(self.top - 2, ny))
                Ellipse(pos=(nx-1.5, ny-1.5), size=(3, 3))

            # Draw EXP Orbs (Yellow dots)
            Color(1, 1, 0.3, 0.7)
            for orb in getattr(self.game, 'exp_orbs', []):
                ox, oy = orb.pos
                nx = self.x + (ox * scale_x)
                ny = self.y + (oy * scale_y)
                if self.x < nx < self.right and self.y < ny < self.top:
                    Ellipse(pos=(nx-1, ny-1), size=(2, 2))

            # Draw Dropped Items / Health (Cyan/Pink dots)
            for item in getattr(self.game, 'dropped_items', []):
                ix, iy = item.pos
                nx = self.x + (ix * scale_x)
                ny = self.y + (iy * scale_y)
                if self.x < nx < self.right and self.y < ny < self.top:
                    # 🌟 แยกสี: ถ้าเป็นเลือด (มี heal_amount) ให้เป็นสีเขียว ถ้าอย่างอื่นเป็น Cyan
                    if hasattr(item, 'heal_amount'):
                        Color(0, 1, 0.4, 1) # Green for Health
                    else:
                        Color(0.2, 0.9, 1, 0.9) # Cyan for magnets/others
                    Ellipse(pos=(nx-2, ny-2), size=(4, 4))

            # Draw Player (Blue dot)
            Color(0, 0.6, 1, 1)
            px, py = getattr(self.game, 'player_pos', (2500, 2500))
            nx = self.x + (px * scale_x)
            ny = self.y + (py * scale_y)
            # Clip player pos
            nx = max(self.x + 4, min(self.right - 4, nx))
            ny = max(self.y + 4, min(self.top - 4, ny))
            Ellipse(pos=(nx-2.5, ny-2.5), size=(5, 5))


# ═══════════════════════════════════════════════════════════
#  HUD — In-game heads-up display
# ═══════════════════════════════════════════════════════════
class HUD(FloatLayout):
    """
    HUD หลักของเกม แสดง:
      - HP bar + HP text (มุมซ้ายบน)
      - EXP bar + Level label
      - Wave label (กลางบน)
      - Enemy count (ใต้ wave)
      - Skill slots (ซ้ายล่าง)
      - ปุ่ม Pause (ขวาบน)
      - ปุ่ม debug (TEST LVL UP, ADD EXP, SUMMON BOSS, CLEAR)
    """

    def __init__(self, game_screen, **kwargs):
        super().__init__(**kwargs)
        self.game_screen = game_screen

        self._build_top_left()
        self._build_wave_label()
        self._build_time_label()
        self._build_enemy_count()
        self._build_skill_slots()
        self._build_pause_button()
        self._build_minimap()

        # 🌟 เปลี่ยนให้เรียกฟังก์ชันอัปเดตทั้ง UI (เลือด + สกิล) ทุกๆ 1/60 วินาที
        Clock.schedule_interval(self._realtime_ui_update, 1.0 / 60.0)

        try:
            self.update_enemy_count(len(self.game_screen.enemies))
        except Exception:
            pass

    # ─── Builder helpers ──────────────────────────────────
    def _build_top_left(self):
        container = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            size=(360, 85),
            pos_hint={"x": 0.02, "top": 0.98},
            spacing=5,
        )

        # HP row
        hp_row = FloatLayout(size_hint=(1, 1))
        self.health_bar = HealthBar(
            size_hint=(None, None), size=(300, 25),
            pos_hint={"right": 1, "center_y": 0.5},
        )
        self.hp_label = Label(
            text="100 / 100",
            size_hint=(None, None), size=(300, 25),
            pos_hint={"right": 1, "center_y": 0.5},
            bold=True,
        )
        hp_row.add_widget(self.health_bar)
        hp_row.add_widget(self.hp_label)

        # EXP row
        exp_row = BoxLayout(orientation="horizontal", size_hint=(1, 1), spacing=5)
        self.lbl_level = Label(
            text="LV : 1", size_hint=(None, 1), width=55,
            font_size=18, bold=True,
            color=(0.9, 0.95, 1, 1),
            outline_width=2, outline_color=(0, 0, 0, 1),
        )
        self.exp_bar = ProgressBar(max=100, value=0, size_hint=(None, 1), width=300)
        exp_row.add_widget(self.lbl_level)
        exp_row.add_widget(self.exp_bar)

        container.add_widget(hp_row)
        container.add_widget(exp_row)
        self.add_widget(container)

    def _build_wave_label(self):
        self.lbl_wave = Label(
            text="WAVE 0",
            size_hint=(None, None), size=(240, 30),
            pos_hint={"center_x": 0.5, "top": 0.98},
            font_size=18, bold=True,
            color=(0.9, 0.95, 1, 1),
            outline_width=2, outline_color=(0, 0, 0, 1),
            halign="center", valign="middle",
        )
        self.lbl_wave.bind(size=lambda inst, v: setattr(inst, "text_size", v))
        self.add_widget(self.lbl_wave)

    def _build_time_label(self):
        self.lbl_time = Label(
            text="00:00",
            size_hint=(None, None), size=(240, 30),
            pos_hint={"center_x": 0.5, "top": 0.94},
            font_size=22, bold=True,
            color=(1, 1, 1, 1),
            outline_width=2, outline_color=(0, 0, 0, 1),
            halign="center", valign="middle",
        )
        self.lbl_time.bind(size=lambda inst, v: setattr(inst, "text_size", v))
        self.add_widget(self.lbl_time)

    def _build_enemy_count(self):
        self.enemy_count_box = BoxLayout(
            orientation="horizontal",
            size_hint=(None, None), size=(160, 30),
            pos_hint={"center_x": 0.5, "top": 0.90},
            spacing=4,
        )
        with self.enemy_count_box.canvas.before:
            Color(0, 0, 0, 0.5)
            self._enemy_bg = Rectangle(
                pos=self.enemy_count_box.pos,
                size=self.enemy_count_box.size,
            )
        self.enemy_count_box.bind(
            pos=lambda i, v: setattr(self._enemy_bg, "pos", v),
            size=lambda i, v: setattr(self._enemy_bg, "size", v),
        )
        self.add_widget(self.enemy_count_box)

    def _build_skill_slots(self):
        self.skill_slot_box = SkillSlotBox()
        self.add_widget(self.skill_slot_box)

    def _build_pause_button(self):
        btn = Button(
            text="||", font_size=24, bold=True,
            size_hint=(None, None), size=(50, 50),
            pos_hint={"right": 0.98, "top": 0.98},
            background_normal="",
            background_color=(0.1, 0.15, 0.2, 0.85),
            color=(0.9, 0.95, 1, 1),
        )
        btn.bind(on_press=self.game_screen.pause_game)
        self.add_widget(btn)

    def _build_minimap(self):
        self.minimap = Minimap(game=self.game_screen)
        self.add_widget(self.minimap)



    # ─── Update API ───────────────────────────────────────
    def update_ui(self, stats):
        self.lbl_level.text = f"LV : {stats.level}"
        self.exp_bar.max = stats.max_exp
        self.exp_bar.value = stats.exp
        self.health_bar.max_hp = stats.hp
        self.health_bar.current_hp = stats.current_hp
        self.hp_label.text = f"{int(stats.current_hp)} / {int(stats.hp)}"

        if hasattr(stats, "skills"):
            skills = list(stats.skills)
            s3 = getattr(stats, 'skill3', None)
            if s3 is not None:
                while len(skills) < 2:
                    skills.append(None)
                skills_with_s3 = [skills[0] if len(skills) > 0 else None,
                                   skills[1] if len(skills) > 1 else None,
                                   s3]
                self.skill_slot_box.update(skills_with_s3)
            else:
                self.skill_slot_box.update(skills)

    def update_wave(self, wave_num: int):
        self.lbl_wave.text = f"WAVE {wave_num}"

    def update_enemy_count(self, count: int):
        self.enemy_count_box.clear_widgets()
        try:
            from kivy.uix.image import Image as KivyImage
            icon_path = "assets/enemy/enemy1.png"
            if os.path.exists(icon_path):
                icon = KivyImage(source=icon_path, size_hint=(None, None), size=(24, 24))
            else:
                raise FileNotFoundError
        except Exception:
            icon = Label(text="★", size_hint=(None, None), size=(24, 24), color=(1, 0, 0, 1))

        txt = Label(
            text=f"{int(count)} left",
            size_hint=(None, None), size=(100, 24),
            font_size=18, bold=True, color=(1, 0.9, 0.2, 1),
        )
        self.enemy_count_box.add_widget(icon)
        self.enemy_count_box.add_widget(txt)

    # 🌟 ฟังก์ชันนี้จะคอยทำงานตลอดเวลา (60 ครั้ง/วินาที)
    def _realtime_ui_update(self, _dt):
        gs = self.game_screen
        if hasattr(gs, "player_stats") and gs.player_stats:
            s = gs.player_stats

            # อัปเดตเลือด
            self.health_bar.max_hp = s.hp
            self.health_bar.current_hp = s.current_hp
            self.hp_label.text = f"{int(s.current_hp)} / {int(s.hp)}"

            # อัปเดตสกิล — รวม skill3 เข้าไปด้วย
            if hasattr(s, "skills"):
                skills = list(s.skills)
                s3 = getattr(s, 'skill3', None)
                if s3 is not None:
                    # ยัด skill3 เข้า index 2 ของ list เพื่อให้ SkillSlotBox แสดงถูกช่อง
                    while len(skills) < 2:
                        skills.append(None)
                    skills_with_s3 = [skills[0] if len(skills) > 0 else None,
                                      skills[1] if len(skills) > 1 else None,
                                      s3]
                    self.skill_slot_box.update(skills_with_s3)
                else:
                    self.skill_slot_box.update(skills)

            # อัปเดตเวลา
            if hasattr(gs, "play_time"):
                mins, secs = divmod(int(gs.play_time), 60)
                self.lbl_time.text = f"{mins:02d}:{secs:02d}"

            # อัปเดต Minimap
            if hasattr(self, "minimap"):
                self.minimap.update(_dt)




# ═══════════════════════════════════════════════════════════
#  CountdownOverlay — 3-2-1 GET READY
# ═══════════════════════════════════════════════════════════
class CountdownOverlay(Label):
    """แสดงนับถอยหลัง 3-2-1 แล้วเรียก callback เพื่อเริ่มเกม"""

    def __init__(self, callback, **kwargs):
        super().__init__(**kwargs)
        self.callback = callback
        self._count = 3
        self.text = "GET READY\n3"
        self.font_size = 200
        self.bold = True
        self.color = (0.9, 0.95, 1, 1)
        self.outline_width = 4
        self.outline_color = (0, 0, 0, 1)
        self.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        self.halign = self.valign = "center"
        self.bind(size=lambda inst, v: setattr(inst, "text_size", v))
        Clock.schedule_interval(self._tick, 1.0)

    def _tick(self, _dt):
        self._count -= 1
        if self._count > 0:
            self.text = f"GET READY\n{self._count}"
        else:
            self.callback()
            if self.parent:
                self.parent.remove_widget(self)
            return False