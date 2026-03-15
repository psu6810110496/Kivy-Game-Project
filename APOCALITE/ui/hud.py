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
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.properties import NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.widget import Widget
from kivy.uix.modalview import ModalView
from kivy.uix.image import Image as KivyImage

from ui.level_up import LevelUpPopup
from ui.font import PIXEL_FONT


# ═══════════════════════════════════════════════════════════
#  HealthBar — Custom HP bar widget
# ═══════════════════════════════════════════════════════════
class HealthBar(Widget):
    """แถบ HP สไตล์ Modern พร้อมเส้นขอบและ Rounded Corner"""

    current_hp = NumericProperty(100)
    max_hp = NumericProperty(100)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._redraw, size=self._redraw,
                  current_hp=self._redraw, max_hp=self._redraw)

    def _redraw(self, *_args):
        self.canvas.clear()
        with self.canvas:
            # Border
            Color(1, 1, 1, 0.2)
            RoundedRectangle(pos=(self.x - 2, self.y - 2), 
                             size=(self.width + 4, self.height + 4), radius=[5])
            
            # Background
            Color(0.1, 0.1, 0.1, 0.7)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[5])
            
            ratio = max(0, min(self.current_hp / max(self.max_hp, 1), 1))
            if ratio > 0:
                # Main Bar
                Color(0.85, 0.15, 0.15, 1)
                RoundedRectangle(pos=self.pos, size=(self.width * ratio, self.height), radius=[5])
                # Highlight Line
                Color(1, 1, 1, 0.15)
                Rectangle(pos=(self.x, self.y + self.height * 0.6), 
                          size=(self.width * ratio, self.height * 0.2))

class ExpBar(Widget):
    """แถบ EXP สีฟ้า/ม่วง สไตล์เดียวกับ HealthBar"""
    value = NumericProperty(0)
    max = NumericProperty(100)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._redraw, size=self._redraw,
                  value=self._redraw, max=self._redraw)

    def _redraw(self, *_args):
        self.canvas.clear()
        with self.canvas:
            Color(0.1, 0.1, 0.1, 0.7)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[4])
            
            ratio = max(0, min(self.value / max(self.max, 1), 1))
            if ratio > 0:
                Color(0.2, 0.6, 1, 1) # Blue
                RoundedRectangle(pos=self.pos, size=(self.width * ratio, self.height), radius=[4])
                Color(1, 1, 1, 0.1)
                Rectangle(pos=(self.x, self.y + self.height * 0.6), 
                          size=(self.width * ratio, self.height * 0.2))


# ═══════════════════════════════════════════════════════════
#  SkillSlotBox — 3 skill slots แสดง cooldown
# ═══════════════════════════════════════════════════════════
class SkillSlotBox(BoxLayout):
    """3 ปุ่มสกิลมุมซ้ายล่าง แสดง name + cooldown overlay หรือ Stack (เรียงตำแหน่ง S3, S1, S2)"""

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
        # เก็บ tuple: (btn, lvl_lbl, overlay_widget, cd_rect, cd_color)
        self.slots: list = []
        
        # ลำดับ Index: (2 = S3, 0 = S1, 1 = S2)
        self.skill_indices = [2, 0, 1]
        
        for skill_idx in self.skill_indices:
            multiplier = 1.25 if skill_idx == 2 else 1.0
            current_size = self.SLOT_SIZE * multiplier

            # Container
            slot_container = FloatLayout(size_hint=(None, None), size=(current_size, current_size))
            
            # 🌟 Background Icon (สำหรับสกิลที่ต้องการ 2 layer เช่น Dino Circle)
            bg_icon_img = KivyImage(
                size_hint=(0.9, 0.9),
                pos_hint={"center_x": 0.5, "center_y": 0.5},
                allow_stretch=True,
                keep_ratio=True,
                opacity=0
            )
            # 🌟 Icon Image Widget (สำหรับภาพ Pixel Art ให้คมชัด)
            icon_img = KivyImage(
                size_hint=(0.9, 0.9),
                pos_hint={"center_x": 0.5, "center_y": 0.5},
                allow_stretch=True,
                keep_ratio=True,
                opacity=0 # ซ่อนไว้ก่อน
            )

            btn = Button(
                text=f"S{skill_idx + 1}",
                font_size=16 * (1.2 if skill_idx == 2 else 1.0),
                bold=True,
                size_hint=(1, 1),
                pos_hint={"x": 0, "y": 0},
                background_normal="",
                background_color=(0.2, 0.2, 0.2, 0.6),
                color=(1, 1, 1, 1),
                text_size=(current_size - 10, current_size - 10),
                halign="center",
                valign="bottom",
                padding=(2, 2),
            )

            # Level Label (มุมขวาบน)
            lvl_lbl = Label(
                text="",
                font_size=14 * (1.1 if skill_idx == 2 else 1.0),
                bold=True,
                size_hint=(None, None),
                size=(50, 25),
                pos_hint={"right": 1, "top": 1},
                color=(1, 1, 0, 1),
            )

            # 🌟 Cooldown Overlay Widget (วาดทับปุ่มตามสัดส่วน CD ที่เหลือ)
            overlay = Widget(
                size_hint=(1, 1),
                pos_hint={"x": 0, "y": 0},
            )
            # เราจะ draw ผ่าน canvas ของ overlay โดยตรงใน update()
            overlay.canvas.clear()
            
            slot_container.add_widget(bg_icon_img) 
            slot_container.add_widget(icon_img) 
            slot_container.add_widget(btn)
            slot_container.add_widget(overlay)
            slot_container.add_widget(lvl_lbl)
            self.add_widget(slot_container)
            
            self.slots.append((btn, lvl_lbl, overlay, icon_img, current_size, bg_icon_img))

    def update(self, skills: list, char_name: str = ""):
        """รีเฟรชข้อความ / สี / CD overlay ทุก frame"""
        char_name_lower = char_name.lower()
        for slot_data, skill_idx in zip(self.slots, self.skill_indices):
            btn, lvl_lbl, overlay, icon_img, slot_sz, bg_icon = slot_data
            skill = skills[skill_idx] if skill_idx < len(skills) else None

            if skill is None:
                btn.text = f"S{skill_idx + 1}\n[empty]"
                btn.background_color = (0.15, 0.15, 0.15, 0.5)
                icon_img.opacity = 0
                bg_icon.opacity = 0
                lvl_lbl.text = ""
                overlay.canvas.clear()
                continue

            # --- identify skill by name for accuracy ---
            skill_name = skill.name
            skill_name_lower = skill_name.lower()
            
            icon_path = ""
            bg_icon_path = ""
            current_bg_rgba = (0.2, 0.2, 0.2, 0.6)

            if char_name_lower == "monkey":
                icon_path = f"assets/Monkey/slotM/Sm{skill_idx + 1}.png"
                current_bg_rgba = (0.1, 0.1, 0.1, 0.8)
            elif char_name_lower == "ptae":
                if "circle" in skill_name_lower:
                    icon_path = "assets/PTae/skill1/aoeptae04.png"
                    bg_icon_path = "assets/PTae/lo/frame_09_delay-0.02s.png"
                    current_bg_rgba = (0.4, 0.1, 0.7, 0.5) # [Aesthetic] Lower alpha (0.5) for prominence
                elif "summon" in skill_name_lower:
                    icon_path = "assets/PTae/skill2/frame_00_delay-0.05s.png"
                    current_bg_rgba = (0.1, 0.5, 0.1, 0.5) # [Aesthetic] Lower alpha
                elif "beam" in skill_name_lower or "punch" in skill_name_lower:
                    icon_path = "assets/PTae/skill3/frame_01_delay-0.05s.png"
                    current_bg_rgba = (0, 0, 0, 0.6) # [Aesthetic] Lower alpha
            elif char_name_lower == "lostman":
                lost_icons = [
                    "assets/Lostman/skill1/axe_hit1.png",
                    "assets/Lostman/skill2/axe_t1.png",
                    "assets/Lostman/skill3/c4_trap1.png"
                ]
                icon_path = lost_icons[skill_idx] if skill_idx < len(lost_icons) else ""
                current_bg_rgba = (0.15, 0.15, 0.15, 0.7)

            # Update BG Color using button's background
            btn.background_color = current_bg_rgba

            # Update Main Icon
            if icon_path and os.path.exists(icon_path):
                if icon_img.source != icon_path:
                    icon_img.source = icon_path
                    try: icon_img.texture.mag_filter = 'nearest'
                    except: pass
                icon_img.opacity = 1.0 # [Aesthetic] Full opacity for texture
                display_name = "" if char_name_lower == "monkey" else skill_name
            else:
                icon_img.opacity = 0
                display_name = skill_name

            # Update BG Icon
            if bg_icon_path and os.path.exists(bg_icon_path):
                if bg_icon.source != bg_icon_path:
                    bg_icon.source = bg_icon_path
                    try: bg_icon.texture.mag_filter = 'nearest'
                    except: pass
                bg_icon.opacity = 0.8 # [Aesthetic] Increase slightly
            else:
                bg_icon.opacity = 0

            # อัปเดตเลเวล
            lvl_lbl.text = f"LV.{skill.level}"

            # --- Stack Skill (S3) ---
            stacks_val = getattr(skill, 'stacks', None)
            max_stacks_val = getattr(skill, 'MAX_STACKS', 3)

            if stacks_val is not None:
                # [Fix] Use simple characters instead of special circles for better font compatibility
                full = "A" * stacks_val
                empty = "-" * max(0, max_stacks_val - stacks_val)
                btn.text = f"{display_name}\n{full}{empty}"
                
                # 🌟 Stack CD overlay: ถ้า stack ไม่เต็มให้แสดง recharge progress
                overlay.canvas.clear()
                if stacks_val < max_stacks_val:
                    recharge_time = getattr(skill, 'recharge_time', 8.0)
                    recharge_timer = getattr(skill, '_recharge_timer', 0.0)
                    frac = max(0.0, min(1.0, recharge_timer / max(0.01, recharge_time)))
                    # วาด overlay สีม่วงทึบส่วน top ตามสัดส่วน fraction ที่เหลือ
                    cover_h = slot_sz * frac
                    if cover_h > 0:
                        with overlay.canvas:
                            Color(0, 0, 0, 0.65)
                            Rectangle(
                                pos=(overlay.x, overlay.y + slot_sz - cover_h),
                                size=(slot_sz, cover_h)
                            )
            else:
                # --- Auto Skill (S1/S2): CD timer ---
                cd_remaining = max(0.0, getattr(skill, '_timer', 0.0))
                cd_total = skill.cooldown
                frac = max(0.0, min(1.0, cd_remaining / max(0.01, cd_total)))

                if cd_remaining <= 0:
                    btn.text = f"{display_name}\n✔"
                else:
                    btn.text = f"{display_name}\n{cd_remaining:.1f}s"

                # 🌟 วาด CD Overlay: overlay ทึบส่วน top ลดลงเรื่อยๆ
                overlay.canvas.clear()
                if frac > 0:
                    cover_h = slot_sz * frac
                    with overlay.canvas:
                        Color(0, 0, 0, 0.70)  # สีดำกึ่งทึบ
                        Rectangle(
                            pos=(overlay.x, overlay.y + slot_sz - cover_h),
                            size=(slot_sz, cover_h)
                        )


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
        self._frame_skip = 0  # 🌟 นับ frame เพื่อ skip
        
    def update(self, dt):
        # 🌟 วาดใหม่แค่ทุก 4 frame (ลด GPU load ~75%)
        self._frame_skip = (self._frame_skip + 1) % 4
        if self._frame_skip != 0:
            return
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
            for enemy in getattr(self.game, 'enemies', []):
                etype = getattr(enemy, 'enemy_type', 'normal')
                is_boss = "boss" in etype
                
                if is_boss:
                    Color(1, 0, 0, 1) # Bright Red for Boss
                    dot_size = 8
                else:
                    Color(1, 0.2, 0.2, 0.8) # Normal Red
                    dot_size = 3
                
                ex, ey = enemy.pos
                nx = self.x + (ex * scale_x)
                ny = self.y + (ey * scale_y)
                nx = max(self.x + 2, min(self.right - 2, nx))
                ny = max(self.y + 2, min(self.top - 2, ny))
                Ellipse(pos=(nx - dot_size/2, ny - dot_size/2), size=(dot_size, dot_size))

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
            ny = max(self.y + 4, min(self.right - 4, ny))
            Ellipse(pos=(nx-2.5, ny-2.5), size=(5, 5))


# ═══════════════════════════════════════════════════════════
#  HUD — Overlay หลักทับบน GameScreen
# ═══════════════════════════════════════════════════════════
class HUD(FloatLayout):
    """
    ประสานงาน UI ทุกอย่างหน้าเกม:
      - HP bar + HP text (มุมซ้ายบน)
      - EXP bar + Level label
      - Wave label (กลางบน)
      - Enemy count (ใต้ wave)
      - Skill slots (ซ้ายล่าง)
      - ปุ่ม Pause (ขวาบน)
      - Minimap (ขวาบน)
    """

    def __init__(self, game_screen, **kwargs):
        super().__init__(**kwargs)
        self.game_screen = game_screen

        # ฟ้อนต์ถูก register ไว้แล้วใน ui.font

        self._build_top_left()
        self._build_wave_label()
        self._build_time_label()
        self._build_enemy_count()
        self._build_skill_slots()
        self._build_pause_button()
        self._build_minimap()

        Clock.schedule_interval(self._realtime_ui_update, 1.0 / 60.0)

        try:
            self.update_enemy_count(len(self.game_screen.enemies))
        except: pass

    # ─── Builder helpers ──────────────────────────────────
    def _build_top_left(self):
        # 🌟 Container with Glassmorphism
        container = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            size=(450, 120),
            pos_hint={"x": 0.02, "top": 0.98},
            spacing=10,
            padding=[8, 8]
        )

        # HP Row
        hp_row = BoxLayout(orientation="vertical", spacing=2)
        self.hp_label = Label(
            text="100 / 100", size_hint=(1, None), height=32,
            font_name=PIXEL_FONT, font_size=28, color=(1, 0.3, 0.3, 1),
            halign="left", valign="middle"
        )
        self.hp_label.bind(size=lambda i,v: setattr(i, "text_size", v))
        self.health_bar = HealthBar(size_hint=(None, None), size=(400, 15))
        hp_row.add_widget(self.hp_label)
        hp_row.add_widget(self.health_bar)

        # EXP Row
        exp_row = BoxLayout(orientation="vertical", spacing=2)
        self.lbl_level = Label(
            text="LV : 1", size_hint=(1, None), height=28,
            font_name=PIXEL_FONT, font_size=24, color=(0.4, 0.8, 1, 1),
            halign="left", valign="middle"
        )
        self.lbl_level.bind(size=lambda i,v: setattr(i, "text_size", v))
        self.exp_bar = ExpBar(size_hint=(None, None), size=(400, 8))
        exp_row.add_widget(self.lbl_level)
        exp_row.add_widget(self.exp_bar)

        container.add_widget(hp_row)
        container.add_widget(exp_row)
        self.add_widget(container)

    def _build_wave_label(self):
        self.lbl_wave = Label(
            text="WAVE 0",
            size_hint=(None, None), size=(200, 48),
            pos_hint={"center_x": 0.5, "top": 0.99},
            font_size=26, bold=True, font_name=PIXEL_FONT,
            color=(1, 0.9, 0.4, 1), halign="center", valign="middle",
        )
        with self.lbl_wave.canvas.before:
            Color(0, 0, 0, 0.5)
            self._wave_bg = RoundedRectangle(pos=self.lbl_wave.pos, size=self.lbl_wave.size, radius=[0, 0, 15, 15])
        self.lbl_wave.bind(pos=lambda i,v: setattr(self._wave_bg, "pos", v),
                           size=lambda i,v: (setattr(self._wave_bg, "size", v), setattr(i, "text_size", v)))
        self.add_widget(self.lbl_wave)

    def _build_time_label(self):
        self.lbl_time = Label(
            text="00:00",
            size_hint=(None, None), size=(110, 32),
            pos_hint={"center_x": 0.5, "top": 0.915},
            font_size=20, font_name=PIXEL_FONT, color=(1, 1, 1, 1),
            halign="center", valign="middle",
        )
        with self.lbl_time.canvas.before:
            Color(0, 0, 0, 0.4)
            self._time_bg = RoundedRectangle(pos=self.lbl_time.pos, size=self.lbl_time.size, radius=[8])
        self.lbl_time.bind(pos=lambda i,v: setattr(self._time_bg, "pos", v),
                           size=lambda i,v: (setattr(self._time_bg, "size", v), setattr(i, "text_size", v)))
        self.add_widget(self.lbl_time)

    def _build_enemy_count(self):
        self.enemy_count_box = BoxLayout(
            orientation="horizontal",
            size_hint=(None, None), size=(120, 30),
            pos_hint={"center_x": 0.5, "top": 0.865},
            padding=[8, 0]
        )
        with self.enemy_count_box.canvas.before:
            Color(0, 0, 0, 0.5)
            self._enemy_bg = RoundedRectangle(pos=self.enemy_count_box.pos, size=self.enemy_count_box.size, radius=[10])
        self.enemy_count_box.bind(pos=lambda i, v: setattr(self._enemy_bg, "pos", v),
                                  size=lambda i, v: setattr(self._enemy_bg, "size", v))
        self.add_widget(self.enemy_count_box)

    def _build_skill_slots(self):
        self.skill_slot_box = SkillSlotBox()
        self.add_widget(self.skill_slot_box)

    def _build_pause_button(self):
        from kivy.graphics import Line
        btn = Button(
            text="||", font_size=22, font_name=PIXEL_FONT,
            size_hint=(None, None), size=(55, 55),
            pos_hint={"right": 0.985, "top": 0.985},
            background_normal="", background_color=(0, 0, 0, 0),
            color=(1, 1, 1, 1),
        )
        with btn.canvas.before:
            Color(0, 0, 0, 0.4)
            self._p_bg = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[10])
            Color(1, 1, 1, 0.2)
            self._p_line = Line(rounded_rectangle=(btn.x, btn.y, btn.width, btn.height, 10), width=1.5)
        
        btn.bind(pos=lambda i,v: (setattr(self._p_bg, "pos", v), 
                                  setattr(self._p_line, "rounded_rectangle", (v[0], v[1], i.width, i.height, 10))),
                 size=lambda i,v: (setattr(self._p_bg, "size", v),
                                   setattr(self._p_line, "rounded_rectangle", (i.x, i.y, v[0], v[1], 10))))
        
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
            from game.skills import CHAR_DEFAULT_SKILLS
            defaults = CHAR_DEFAULT_SKILLS.get(stats.name, [])
            s1, s2 = None, None
            for skill in stats.skills:
                if len(defaults) > 0 and isinstance(skill, defaults[0]): s1 = skill
                elif len(defaults) > 1 and isinstance(skill, defaults[1]): s2 = skill
            
            s3 = getattr(stats, 'skill3', None)
            self.skill_slot_box.update([s1, s2, s3], stats.name)

    def update_wave(self, wave_num: int):
        self.lbl_wave.text = f"WAVE {wave_num}"

    def update_enemy_count(self, count: int):
        # 🌟 อัปเดตเฉพาะเมื่อตัวเลขเปลี่ยน (ไม่สร้าง Widget ใหม่ทุกครั้ง)
        if getattr(self, '_last_enemy_count', -1) == count:
            return
        self._last_enemy_count = count
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

            # อัปเดตเลือด (ทุก frame — สำคัญ)
            self.health_bar.max_hp = s.hp
            self.health_bar.current_hp = s.current_hp
            self.hp_label.text = f"{int(s.current_hp)} / {int(s.hp)}"

            # อัปเดตสกิล overlay (ทุก 2 frame — ลด canvas.clear() call)
            if not hasattr(self, '_skill_frame_tick'):
                self._skill_frame_tick = 0
            self._skill_frame_tick += 1
            if self._skill_frame_tick % 2 == 0 and hasattr(s, "skills"):
                from game.skills import CHAR_DEFAULT_SKILLS
                defaults = CHAR_DEFAULT_SKILLS.get(s.name, [])
                s1, s2 = None, None
                for skill in s.skills:
                    if len(defaults) > 0 and isinstance(skill, defaults[0]): s1 = skill
                    elif len(defaults) > 1 and isinstance(skill, defaults[1]): s2 = skill
                
                s3 = getattr(s, 'skill3', None)
                self.skill_slot_box.update([s1, s2, s3], s.name)

            # อัปเดตเวลา (ทุก 30 frame = ~0.5s)
            if self._skill_frame_tick % 30 == 0 and hasattr(gs, "play_time"):
                mins, secs = divmod(int(gs.play_time), 60)
                self.lbl_time.text = f"{mins:02d}:{secs:02d}"

            # อัปเดต Minimap (มี frame skip อยู่ข้างในแล้ว)
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
        self.font_name = PIXEL_FONT
        self.font_size = 200
        self.bold = True
        self.color = (0.9, 0.95, 1, 1)
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