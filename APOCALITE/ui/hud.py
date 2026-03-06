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
        self._build_debug_buttons()

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

    def _build_debug_buttons(self):
        """แบ่งปุ่ม debug เป็น 2 คอลัมน์เพื่อให้โชว์ครบ"""
        # (text, top, right, color, callback)
        debug_specs = [
            # คอลัมน์ขวาสุด (0.98) - ระบบหลัก
            ("SHOW\nHP/ATK",  0.88, 0.98, (0.1, 0.5, 0.8, 0.9), self._toggle_enemy_debug),
            ("PLAYER\nSTATS", 0.78, 0.98, (0.2, 0.7, 0.2, 0.9), self._show_player_stats),
            ("TEST\nLVL UP",  0.68, 0.98, (0.3, 0.1, 0.1, 0.85), self._test_level_up),
            ("ADD\nEXP +20",  0.58, 0.98, (0.1, 0.3, 0.3, 0.85), self._test_add_exp),
            ("CLEAR\nENEMY",  0.48, 0.98, (0.1, 0.2, 0.3, 0.85), self._clear_enemies),
            ("MAX\nALL",      0.38, 0.98, (1.0, 0.8, 0.0, 1.0),   self._test_max_all),

            # คอลัมน์ที่สอง (0.90) - Summon ต่างๆ
            ("STOP\nWAVE",    0.88, 0.90, (0.3, 0.2, 0.0, 0.85), self._toggle_stop_wave),
            ("NEXT\nWAVE",    0.78, 0.90, (0.1, 0.4, 0.1, 0.85), self._next_wave),
            ("SUMMON\nBOSS",  0.68, 0.90, (0.3, 0.1, 0.3, 0.85), self._test_summon_boss),
            ("SUMMON\nBIG",   0.58, 0.90, (0.5, 0.0, 0.5, 0.85), self._test_summon_big),
            ("SUMMON\nFINAL", 0.48, 0.90, (0.4, 0.0, 0.8, 0.85), self._test_summon_final),
        ]

        for text, top, right, color, callback in debug_specs:
            btn = Button(
                text=text, font_size=12, bold=True, halign="center",
                size_hint=(None, None), size=(85, 50),
                pos_hint={"right": right, "top": top},
                background_normal="", background_color=color,
                color=(1, 1, 1, 1),
            )
            btn.bind(on_press=callback)
            self.add_widget(btn)

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

    # ─── Debug callbacks ──────────────────────────────────
    def _test_level_up(self, _inst):
        self.game_screen.is_paused = True
        LevelUpPopup(self.game_screen).open()

    def _test_add_exp(self, _inst):
        player = kivy.app.App.get_running_app().current_player
        if player:
            self.game_screen.gain_exp(20)

    def _test_summon_boss(self, _inst):
        self.game_screen.wave_manager._spawn_boss()

    def _clear_enemies(self, _inst):
        gs = self.game_screen
        for e in gs.enemies[:]:
            if e.parent:
                e.parent.remove_widget(e)
        gs.enemies.clear()
        for p in gs.enemy_projectiles[:]:
            if p.parent:
                p.parent.remove_widget(p)
        gs.enemy_projectiles.clear()
        self.update_enemy_count(0)


    def _test_summon_big(self, _inst):
        self.game_screen.wave_manager._spawn_big_boss()

    def _next_wave(self, _inst):
        self._clear_enemies(None)
        gs = self.game_screen
        gs.wave_manager.is_spawning = False
        gs.wave_manager.try_start_next_wave()

    def _test_summon_final(self, _inst):
        self.game_screen.wave_manager._spawn_final_boss()

    def _test_max_all(self, _inst):
        gs = self.game_screen
        stats = gs.player_stats
        if not stats: return
        
        # Custom Max Stats based on Character
        if stats.name == "PTae":
            stats.hp = 1500
            stats.damage = 200
            stats.speed = 5.0
        elif stats.name == "Lostman":
            stats.hp = 1200
            stats.damage = 180
            stats.speed = 7.0
        elif stats.name == "Monkey":
            stats.hp = 1200
            stats.damage = 160
            stats.speed = 9.0
        
        stats.current_hp = stats.hp
        stats.level = 100
        
        # Get all possible skills for this character and max them
        from game.skills import get_upgrade_choices
        # We simulate multiple selections to unlock everything
        for _ in range(10): # Should be enough to unlock S1, S2, and S3
            choices = [c for c in get_upgrade_choices(stats) if c['type'] == 'skill']
            if not choices: break
            for c in choices:
                is_new = c.get("is_new", False)
                is_s3 = c.get("is_s3", False)
                skill = c['skill']
                if is_new:
                    if is_s3: stats.skill3 = skill
                    else: stats.skills.append(skill)
                # Max the level
                skill.level = skill.MAX_LEVEL
                if hasattr(skill, '_on_upgrade'): skill._on_upgrade()
        
        # Refresh UI
        self.update_ui(stats)

    def _toggle_stop_wave(self, inst):
        wm = self.game_screen.wave_manager
        wm._wave_stopped = not getattr(wm, '_wave_stopped', False)
        inst.text = "RESUME\nWAVE" if wm._wave_stopped else "STOP\nWAVE"

    def _toggle_enemy_debug(self, inst):
        from game.enemy_widget import EnemyWidget
        EnemyWidget.SHOW_DEBUG_STATS = not EnemyWidget.SHOW_DEBUG_STATS
        inst.text = "HIDE\nHP/ATK" if EnemyWidget.SHOW_DEBUG_STATS else "SHOW\nHP/ATK"

    def _show_player_stats(self, _inst):
        stats = self.game_screen.player_stats
        if not stats: return
        PlayerStatsPopup(stats).open()


# ═══════════════════════════════════════════════════════════
#  PlayerStatsPopup — Show current player stats in detail
# ═══════════════════════════════════════════════════════════
class PlayerStatsPopup(ModalView):
    def __init__(self, stats, **kwargs):
        super().__init__(size_hint=(None, None), size=(400, 500), background_color=(0,0,0,0.8), **kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        title = Label(text=f"PLAYER STATS: {stats.name}", font_size=28, bold=True, size_hint_y=None, height=50, color=(1, 0.8, 0, 1))
        layout.add_widget(title)
        
        # Grid for stats
        from kivy.uix.gridlayout import GridLayout
        grid = GridLayout(cols=2, spacing=10)
        
        stat_list = [
            ("LEVEL", f"{stats.level}"),
            ("HP", f"{int(stats.current_hp)} / {int(stats.hp)}"),
            ("DAMAGE", f"{int(stats.damage)}"),
            ("SPEED", f"{stats.speed:.2f}"),
            ("EXP", f"{int(stats.exp)} / {int(stats.max_exp)}"),
        ]
        
        for k, v in stat_list:
            grid.add_widget(Label(text=k, halign='left', text_size=(150, None), bold=True))
            grid.add_widget(Label(text=v, halign='right', text_size=(150, None), color=(0, 1, 0.8, 1)))
            
        layout.add_widget(grid)
        
        # Skills list
        layout.add_widget(Label(text="SKILLS", bold=True, color=(1,0.5,0,1), size_hint_y=None, height=30))
        skills_text = ""
        for s in stats.skills:
            if s: skills_text += f"• {s.name} (Lv.{s.level})\n"
        if stats.skill3:
            skills_text += f"• {stats.skill3.name} (Lv.{stats.skill3.level}) [S3]\n"
            
        layout.add_widget(Label(text=skills_text or "No skills unlocked", valign='top', text_size=(360, None)))
        
        close_btn = Button(text="CLOSE", size_hint_y=None, height=50, background_normal="", background_color=(0.3,0.3,0.3,1))
        close_btn.bind(on_release=self.dismiss)
        layout.add_widget(close_btn)
        
        self.add_widget(layout)


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