from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.properties import NumericProperty
import os
import kivy.app
from ui.level_up import LevelUpPopup


# --- [คลาส HealthBar] ---
class HealthBar(Widget):
    current_hp = NumericProperty(100)
    max_hp = NumericProperty(100)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            pos=self.update_canvas,
            size=self.update_canvas,
            current_hp=self.update_canvas,
            max_hp=self.update_canvas,
        )

    def update_canvas(self, *args):
        self.canvas.clear()
        with self.canvas:
            Color(0.2, 0.2, 0.2, 1)
            Rectangle(pos=self.pos, size=self.size)

            Color(0.8, 0.1, 0.1, 1)
            hp_ratio = max(0, min(self.current_hp / max(self.max_hp, 1), 1))
            Rectangle(pos=self.pos, size=(self.width * hp_ratio, self.height))


# -----------------------------


class HUD(FloatLayout):
    def __init__(self, game_screen, **kwargs):
        super().__init__(**kwargs)
        self.game_screen = game_screen

        # --- [🌟 ส่วนที่แก้ไข: จัดกลุ่ม UI มุมซ้ายบนให้ตรงกันเป๊ะ] ---
        # สร้างกล่องรวม (กว้าง 360 = ตัวหนังสือ 60 + หลอด 300)
        top_left_ui = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            size=(360, 85),
            pos_hint={"x": 0.02, "top": 0.98},
            spacing=5,
        )

        # แถวบน: หลอดเลือด (ใช้ FloatLayout เพื่อซ้อนข้อความและจัดชิดขวา)
        hp_container = FloatLayout(size_hint=(1, 1))

        # ดันหลอดเลือดไปชิดขวาของกล่อง เพื่อเว้นที่ว่างด้านซ้ายให้ตรงกับคำว่า "LV : 1"
        self.health_bar = HealthBar(
            size_hint=(None, None),
            size=(300, 25),
            pos_hint={"right": 1, "center_y": 0.5},
        )
        self.hp_label = Label(
            text="100 / 100",
            size_hint=(None, None),
            size=(300, 25),
            pos_hint={"right": 1, "center_y": 0.5},
            bold=True,
        )
        hp_container.add_widget(self.health_bar)
        hp_container.add_widget(self.hp_label)
        # แถวล่าง: เลเวล + หลอด EXP
        exp_container = BoxLayout(orientation="horizontal", size_hint=(1, 1), spacing=5)
        self.lbl_level = Label(
            text="LV : 1",
            size_hint=(None, 1),
            width=55,  # ความกว้างตัวหนังสือ 55 + spacing 5 = 60 พอดี
            font_size=18,
            bold=True,
            color=(0.9, 0.95, 1, 1),
            outline_width=2,
            outline_color=(0, 0, 0, 1),
        )
        # ตั้งความกว้างหลอด EXP ให้เป็น 300 เท่ากับหลอดเลือด
        self.exp_bar = ProgressBar(max=100, value=0, size_hint=(None, 1), width=300)

        exp_container.add_widget(self.lbl_level)
        exp_container.add_widget(self.exp_bar)

        # นำสองแถว (HP / EXP) ใส่เข้ากล่องรวม แล้วแปะลงบนหน้าจอมุมซ้ายบน
        top_left_ui.add_widget(hp_container)
        top_left_ui.add_widget(exp_container)
        self.add_widget(top_left_ui)

        # Label แสดง Wave ปัจจุบัน ตรงกลางด้านบนของหน้าจอ
        self.lbl_wave = Label(
            text="WAVE 0",
            size_hint=(None, None),
            size=(240, 30),
            pos_hint={"center_x": 0.5, "top": 0.98},
            font_size=18,
            bold=True,
            color=(0.9, 0.95, 1, 1),
            outline_width=2,
            outline_color=(0, 0, 0, 1),
            halign="center",
            valign="middle",
        )
        # ให้ข้อความจัดกึ่งกลางในกรอบของตัวเอง
        self.lbl_wave.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self.add_widget(self.lbl_wave)

        # --- [ใหม่] กล่องแสดงจำนวนศัตรูที่เหลือ ---
        # วางไว้เหนือตัวหนังสือ "WAVE" นิดหน่อย (ขึ้นไปอีก)
        self.enemy_icon_box = BoxLayout(
            orientation="horizontal",
            size_hint=(None, None),
            size=(160, 30),
            # ขยับลงให้ใต้ข้อความ Wave
            pos_hint={"center_x": 0.5, "top": 0.90},
            spacing=4,
        )
        # วาดพื้นหลังโปร่งไว้เป็นกรอบ
        with self.enemy_icon_box.canvas.before:
            Color(0, 0, 0, 0.5)
            self._enemy_box_bg = Rectangle(pos=self.enemy_icon_box.pos, size=self.enemy_icon_box.size)
        # อัพเดทแบ็กกราวน์เมื่อขยับหรือเปลี่ยนไซส์
        self.enemy_icon_box.bind(pos=self._update_enemy_box_bg, size=self._update_enemy_box_bg)
        self.add_widget(self.enemy_icon_box)

        # ให้อัปเดตเลือดแบบเรียลไทม์ 60 เฟรมต่อวินาที
        Clock.schedule_interval(self.update_hp_realtime, 1.0 / 60.0)
        # --------------------------------------------------------

        # แสดงค่าจำนวนศัตรูเริ่มต้น (มักจะเป็น 0)
        try:
            self.update_enemy_count(len(self.game_screen.enemies))
        except Exception:
            pass

    def _update_enemy_box_bg(self, instance, value):
        # synchronize the background rectangle with the box layout
        if hasattr(self, '_enemy_box_bg'):
            self._enemy_box_bg.pos = instance.pos
            self._enemy_box_bg.size = instance.size

        # ปุ่มเมนูด้านขวาบน
        btn_pause = Button(
            text="||",
            font_size=24,
            bold=True,
            size_hint=(None, None),
            size=(50, 50),
            pos_hint={"right": 0.98, "top": 0.98},
            background_normal="",
            background_color=(0.1, 0.15, 0.2, 0.85),
            color=(0.9, 0.95, 1, 1),
        )
        btn_pause.bind(on_press=self.game_screen.pause_game)
        self.add_widget(btn_pause)

        btn_test_lvl = Button(
            text="TEST\nLVL UP",
            font_size=14,
            bold=True,
            halign="center",
            size_hint=(None, None),
            size=(80, 50),
            pos_hint={"right": 0.98, "top": 0.88},
            background_normal="",
            background_color=(0.3, 0.1, 0.1, 0.85),
            color=(1, 1, 1, 1),
        )
        btn_test_lvl.bind(on_press=self.test_level_up)
        self.add_widget(btn_test_lvl)

        btn_add_exp = Button(
            text="ADD\nEXP +20",
            font_size=14,
            bold=True,
            halign="center",
            size_hint=(None, None),
            size=(80, 50),
            pos_hint={"right": 0.98, "top": 0.78},
            background_normal="",
            background_color=(0.1, 0.3, 0.3, 0.85),
            color=(1, 1, 1, 1),
        )
        btn_add_exp.bind(on_press=self.test_add_exp)
        self.add_widget(btn_add_exp)

        # ปุ่มทดสอบเรียกบอส
        btn_boss = Button(
            text="SUMMON\nBOSS",
            font_size=14,
            bold=True,
            halign="center",
            size_hint=(None, None),
            size=(80, 50),
            pos_hint={"right": 0.98, "top": 0.68},
            background_normal="",
            background_color=(0.3, 0.1, 0.3, 0.85),
            color=(1, 1, 1, 1),
        )
        btn_boss.bind(on_press=self.test_summon_boss)
        self.add_widget(btn_boss)

        # ปุ่มล้างศัตรู
        btn_clear = Button(
            text="CLEAR\nENEMY",
            font_size=14,
            bold=True,
            halign="center",
            size_hint=(None, None),
            size=(80, 50),
            pos_hint={"right": 0.98, "top": 0.58},
            background_normal="",
            background_color=(0.1, 0.2, 0.3, 0.85),
            color=(1, 1, 1, 1),
        )
        btn_clear.bind(on_press=self.clear_all_enemies)
        self.add_widget(btn_clear)

        # --- [⚡ ช่องแสดงสกิล 3 ช่อง ด้านซ้ายล่าง] ---
        # วางก่อนเพราะเริ่มต้นจะยังไม่มีการใช้งานจริง
        skill_box = BoxLayout(
            orientation="horizontal",
            size_hint=(None, None),
            size=(3 * 256 + 2 * 10, 256),  # 3 ปุ่ม 256x256 + spacing 10
            pos_hint={"x": 0.02, "y": 0.02},
            spacing=10,
        )
        self.skill_buttons = []
        for i in range(3):
            btn = Button(
                text=f"S{i+1}",
                font_size=24,
                bold=True,
                size_hint=(None, None),
                size=(128, 128),
                background_normal="",
                background_color=(0.2, 0.2, 0.2, 0.6),
                color=(1, 1, 1, 1),
            )
            # ต่อไปจะ bind กับสกิลจริงเมื่อมี
            skill_box.add_widget(btn)
            self.skill_buttons.append(btn)
        self.add_widget(skill_box)

    def test_level_up(self, instance):
        if hasattr(self.game_screen, "is_paused"):
            self.game_screen.is_paused = True
        popup = LevelUpPopup(self.game_screen)
        popup.open()

    def test_add_exp(self, instance):
        player = kivy.app.App.get_running_app().current_player
        if player:
            player.exp += 20
            if player.exp >= 100:
                player.exp -= 100
                player.level += 1
                if hasattr(self.game_screen, "is_paused"):
                    self.game_screen.is_paused = True
                popup = LevelUpPopup(self.game_screen)
                popup.open()
            self.update_ui(player)

    def test_summon_boss(self, instance):
        # เรียกใช้ฟังก์ชันเริ่ม Boss Fight จาก GameScreen
        if hasattr(self.game_screen, "start_boss_fight"):
            self.game_screen.start_boss_fight()

    def clear_all_enemies(self, instance):
        """ล้างศัตรูทั้งหมดออกจากเกม (เพื่อการทดสอบ)"""
        # ลบศัตรูทั้งหมดออกจาก world_layout
        for enemy in self.game_screen.enemies[:]:  # ใช้ slice เพื่อ iterate over copy
            if enemy.parent:
                enemy.parent.remove_widget(enemy)
        self.game_screen.enemies.clear()
        
        # ล้าง projectiles ของศัตรูด้วย
        for proj in self.game_screen.enemy_projectiles[:]:
            if proj.parent:
                proj.parent.remove_widget(proj)
        self.game_screen.enemy_projectiles.clear()
        # อัปเดต HUD ด้วย
        if hasattr(self.game_screen, "hud"):
            self.game_screen.hud.update_enemy_count(0)


    def update_ui(self, stats):
        self.lbl_level.text = f"LV : {stats.level}"
        self.exp_bar.value = stats.exp

        self.health_bar.max_hp = stats.hp
        self.health_bar.current_hp = stats.current_hp
        self.hp_label.text = f"{int(stats.current_hp)} / {int(stats.hp)}"

        # update skill buttons with names and cooldowns
        for idx, btn in enumerate(self.skill_buttons):
            if hasattr(stats, "skills") and idx < len(stats.skills):
                skill = stats.skills[idx]
                # timer counts down; show as integer or 1 decimal
                cd = max(0.0, skill._timer)
                btn.text = f"{skill.name}\nCD:{cd:.1f}s"
                # change color if ready
                if cd <= 0:
                    btn.background_color = (0.2, 0.6, 0.2, 1)
                else:
                    btn.background_color = (0.2, 0.2, 0.2, 0.6)
            else:
                # empty slots
                btn.text = f"S{idx+1}"
                btn.background_color = (0.2, 0.2, 0.2, 0.6)

    def update_wave(self, wave_num: int):
        self.lbl_wave.text = f"WAVE {wave_num}"

    def update_enemy_count(self, count: int):
        """ปรับปรุงข้อความจำนวนศัตรูที่เหลือบน HUD

        แสดงเป็นไอคอน (placeholder) และตัวเลขพร้อมคำว่า "left".
        """
        if count is None:
            count = 0
        self.enemy_icon_box.clear_widgets()
        # ใช้ภาพไอคอนจากโฟลเดอร์ assets/enemy
        try:
            from kivy.uix.image import Image
            icon_path = "assets/enemy/enemy1.png"
            if os.path.exists(icon_path):
                icon = Image(source=icon_path, size_hint=(None, None), size=(24, 24))
            else:
                raise FileNotFoundError
        except Exception:
            # fallback เป็นกล่องสีแทน
            from kivy.graphics import Color, Rectangle
            icon = Label(text=" ", size_hint=(None, None), size=(24, 24))
            with icon.canvas.before:
                Color(1, 0, 0, 1)
                Rectangle(pos=icon.pos, size=icon.size)
            # อัพเดทเมื่อ icon ย้าย/ขยาย
            icon.bind(pos=lambda i, v: setattr(icon.canvas.before.children[0], 'pos', v),
                      size=lambda i, v: setattr(icon.canvas.before.children[0], 'size', v))

        # ตัวเลขแสดงจำนวนนำฟอนต์ต่างออกไป
        txt = Label(text=f"{int(count)} left",
                    size_hint=(None, None), size=(100, 24),
                    font_size=18,
                    bold=True,
                    color=(1, 0.9, 0.2, 1))
        self.enemy_icon_box.add_widget(icon)
        self.enemy_icon_box.add_widget(txt)

    def update_hp_realtime(self, dt):
        if hasattr(self.game_screen, "player_stats") and self.game_screen.player_stats:
            player_stats = self.game_screen.player_stats
            self.health_bar.max_hp = player_stats.hp
            self.health_bar.current_hp = player_stats.current_hp
            self.hp_label.text = (
                f"{int(player_stats.current_hp)} / {int(player_stats.hp)}"
            )


class CountdownOverlay(Label):
    def __init__(self, callback, **kwargs):
        super().__init__(**kwargs)
        self.callback = callback
        self.count = 3
        self.text = "GET READY\n3"
        self.font_size = 200
        self.bold = True
        self.color = (0.9, 0.95, 1, 1)
        self.outline_width = 4
        self.outline_color = (0, 0, 0, 1)
        self.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        self.halign = "center"
        self.valign = "middle"
        # ให้ข้อความจัดกึ่งกลางในกรอบของ Label
        self.bind(size=self._update_text_size)
        Clock.schedule_interval(self.update_countdown, 1)

    def _update_text_size(self, *args):
        self.text_size = self.size

    def update_countdown(self, dt):
        self.count -= 1
        if self.count > 0:
            self.text = f"GET READY\n{self.count}"
        else:
            # นับจบแล้ว เริ่มเกม/เริ่ม Wave แรก
            self.callback()
            if self.parent:
                self.parent.remove_widget(self)
            return False
