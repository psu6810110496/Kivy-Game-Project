"""game/wave_manager.py — Wave/Boss spawning + progression scaling"""
import math
import random

from kivy.clock import Clock
from kivy.uix.label import Label

from game.enemy_widget import EnemyWidget


class WaveManager:
    def __init__(self, game):
        self.game = game
        self.current_wave: int = 0
        self.is_spawning: bool = False
        self._wave_label = None
        self._boss_overlay = None
        self._wave_stopped: bool = False  # debug: stop wave

    def try_start_next_wave(self):
        if self.is_spawning or self.game.is_dead or self._wave_stopped:
            return
        self.is_spawning = True 
        """game/wave_manager.py — Wave/Boss spawning + progression scaling"""
import math
import random

from kivy.clock import Clock
from kivy.uix.label import Label

from game.enemy_widget import EnemyWidget


class WaveManager:
    def __init__(self, game):
        self.game = game
        self.current_wave: int = 0
        self.is_spawning: bool = False
        self._wave_label = None
        self._boss_overlay = None
        self._wave_stopped: bool = False  # debug: stop wave

    def try_start_next_wave(self):
        if self.is_spawning or self.game.is_dead or self._wave_stopped:
            return
        self.is_spawning = True
        self.current_wave += 1
        self._show_wave_title()
        Clock.schedule_once(self._spawn_enemies, 1.5)

    def reset(self):
        self.current_wave = 0
        self.is_spawning = False
        self._wave_label = None
        self._boss_overlay = None

    # ── Spawn ──────────────────────────────────────────────
    def _spawn_enemies(self, _dt):
        game = self.game
        if game.is_dead or not game.game_started:
            self.is_spawning = False
            return

        w = self.current_wave

        # max_exp scaling: +20 ทุก 2 wave
        if game.player_stats and w % 2 == 0:
            game.player_stats.max_exp += 20
            game.hud.update_ui(game.player_stats)

        is_big_boss = (w % 10 == 0 and w > 0)
        is_boss = (w % 10 == 5)

        if is_big_boss:
            count = self._big_boss_count(w)
            for _ in range(count):
                self._spawn_big_boss(intro=False)
            for _ in range(8):
                self._spawn_single()
            self.is_spawning = False
            Clock.schedule_once(lambda _: self.start_boss_intro(count, is_big=True), 0.1)
        elif is_boss:
            count = self._boss_count(w)
            for _ in range(count):
                self._spawn_boss(intro=False)
            for _ in range(5):
                self._spawn_single()
            self.is_spawning = False
            Clock.schedule_once(lambda _: self.start_boss_intro(count, is_big=False), 0.1)
        else:
            for _ in range(5 + w * 2):
                self._spawn_single()
            self.is_spawning = False

    def _boss_count(self, wave: int) -> int:
        """wave 5=1, 15=2, 25=3 … สูงสุด 10"""
        return min(10, 1 + (wave - 5) // 10)

    def _big_boss_count(self, wave: int) -> int:
        """wave 10,20,30,40=1, wave 45=2 (ไม่มี), wave 50=1
        จริงๆ: wave 45 ไม่ใช่ big boss wave (45%10=5 เป็น boss)
        spec: wave 45 = 2 big boss → แต่ 45%10=5 เป็น boss wave
        ตีความว่า wave 40=1, wave 50=1,... wave ที่ >= 100 = 3"""
        if wave >= 100:
            return 3
        if wave >= 45:
            return 2
        return 1

    # ── Wave stat scaling ─────────────────────────────────
    @staticmethod
    def _wave_stat_bonus(wave: int) -> int:
        """คำนวณ cumulative bonus ตาม pattern +2,+2,+3,+4,+5,+7,+9,+11,+13,+15,+17,...
        หลัง index 10 จะเพิ่ม +2 ต่อ step ไปเรื่อยๆ (19, 21, 23, ...)"""
        if wave <= 0:
            return 0
        increments = [2, 2, 3, 4, 5, 7, 9, 11, 13, 15, 17]
        total = 0
        for i in range(wave):
            if i < len(increments):
                total += increments[i]
            else:
                total += increments[-1] + (i - (len(increments) - 1)) * 2
        return total

    def _apply_wave_scaling(self, enemy):
        """ใส่ HP / DMG bonus ตาม wave ให้ศัตรู"""
        bonus = self._wave_stat_bonus(self.current_wave)
        if bonus <= 0:
            return
        hp_mult = 1.0 + bonus * 0.05   # HP เพิ่มเป็น % ของ base
        enemy.hp     = int(enemy.hp * hp_mult)
        enemy.max_hp = enemy.hp
        enemy.damage = int(enemy.damage + bonus)

    def _spawn_single(self, force_type=None):
        game = self.game
        etype = force_type or random.choices(
            ["normal", "stalker", "ranger"], weights=[60, 25, 15])[0]
        angle = random.uniform(0, 2 * math.pi)
        r = random.uniform(850, 1100)
        sx = game.player_pos[0] + math.cos(angle) * r
        sy = game.player_pos[1] + math.sin(angle) * r
        enemy = EnemyWidget(spawn_pos=(sx, sy), enemy_type=etype)
        enemy.game = game
        self._apply_wave_scaling(enemy)
        game.enemies.append(enemy)
        game.world_layout.add_widget(enemy)
        game.hud.update_enemy_count(len(game.enemies))

    def _spawn_boss(self, intro: bool = True):
        game = self.game
        angle = random.uniform(0, 2 * math.pi)
        bx = game.player_pos[0] + math.cos(angle) * 900
        by = game.player_pos[1] + math.sin(angle) * 900
        boss = EnemyWidget(spawn_pos=(bx, by), enemy_type="boss")
        boss.game = game
        self._apply_wave_scaling(boss)
        game.boss = boss
        game.enemies.append(boss)
        game.world_layout.add_widget(boss)
        game.hud.update_enemy_count(len(game.enemies))
        if intro:
            self.start_boss_intro(1, is_big=False)

    def _spawn_big_boss(self, intro: bool = True):
        game = self.game
        angle = random.uniform(0, 2 * math.pi)
        bx = game.player_pos[0] + math.cos(angle) * 900
        by = game.player_pos[1] + math.sin(angle) * 900
        boss = EnemyWidget(spawn_pos=(bx, by), enemy_type="big_boss")
        boss.game = game
        self._apply_wave_scaling(boss)
        game.big_boss = boss
        game.enemies.append(boss)
        game.world_layout.add_widget(boss)
        game.hud.update_enemy_count(len(game.enemies))
        if intro:
            self.start_boss_intro(1, is_big=True)

    def start_boss_intro(self, boss_count: int, is_big: bool):
        game = self.game
        game.zoom_target = 3.0
        game.is_boss_intro = True
        tag = "BIG BOSS" if is_big else "BOSS"
        color = (0.8, 0.1, 0.8, 1) if is_big else (0.9, 0.2, 0.2, 1)
        multiplier = f"  ×{boss_count}" if boss_count > 1 else ""
        self._show_boss_overlay(f"{tag}{multiplier}", color)

    # ── UI helpers ─────────────────────────────────────────
    def _show_wave_title(self):
        game = self.game
        if self._wave_label and self._wave_label.parent:
            game.root_layout.remove_widget(self._wave_label)
        self._wave_label = Label(
            text=f"[b]WAVE {self.current_wave}[/b]",
            markup=True, font_size=80,
            color=(1, 1, 1, 1), outline_width=4, outline_color=(0, 0, 0, 1),
            pos_hint={"center_x": 0.5, "top": 0.92},
        )
        game.root_layout.add_widget(self._wave_label)
        game.hud.update_wave(self.current_wave)
        Clock.schedule_once(self._hide_wave_title, 1.5)

    def _hide_wave_title(self, _dt):
        if self._wave_label and self._wave_label.parent:
            self.game.root_layout.remove_widget(self._wave_label)
        self._wave_label = None

    def _show_boss_overlay(self, text, color):
        game = self.game
        if self._boss_overlay and self._boss_overlay.parent:
            game.root_layout.remove_widget(self._boss_overlay)
        self._boss_overlay = Label(
            text=f"[b]{text}[/b]",
            markup=True, font_size=100,
            color=color, outline_width=4, outline_color=(0, 0, 0, 1),
            pos_hint={"center_x": 0.5, "center_y": 0.7},
        )
        game.root_layout.add_widget(self._boss_overlay)
        Clock.schedule_once(self._end_boss_intro, 2.0)

    def _end_boss_intro(self, _dt):
        self.game.is_boss_intro = False
        self.game.zoom_target = 1.8
        if self._boss_overlay and self._boss_overlay.parent:
            self.game.root_layout.remove_widget(self._boss_overlay)
        self._boss_overlay = None
        self.current_wave += 1
        self._show_wave_title()
        Clock.schedule_once(self._spawn_enemies, 1.5)

    def reset(self):
        self.current_wave = 0
        self.is_spawning = False
        self._wave_label = None
        self._boss_overlay = None

    # ── Spawn ──────────────────────────────────────────────
    def _spawn_enemies(self, _dt):
        game = self.game
        if game.is_dead or not game.game_started:
            self.is_spawning = False
            return

        w = self.current_wave

        # max_exp scaling: +20 ทุก 2 wave
        if game.player_stats and w % 2 == 0:
            game.player_stats.max_exp += 20
            game.hud.update_ui(game.player_stats)

        is_big_boss = (w % 10 == 0 and w > 0)
        is_boss = (w % 10 == 5)

        if is_big_boss:
            count = self._big_boss_count(w)
            for _ in range(count):
                self._spawn_big_boss(intro=False)
            for _ in range(8):
                self._spawn_single()
            self.is_spawning = False
            Clock.schedule_once(lambda _: self.start_boss_intro(count, is_big=True), 0.1)
        elif is_boss:
            count = self._boss_count(w)
            for _ in range(count):
                self._spawn_boss(intro=False)
            for _ in range(5):
                self._spawn_single()
            self.is_spawning = False
            Clock.schedule_once(lambda _: self.start_boss_intro(count, is_big=False), 0.1)
        else:
            for _ in range(5 + w * 2):
                self._spawn_single()
            self.is_spawning = False

    def _boss_count(self, wave: int) -> int:
        """wave 5=1, 15=2, 25=3 … สูงสุด 10"""
        return min(10, 1 + (wave - 5) // 10)

    def _big_boss_count(self, wave: int) -> int:
        """wave 10,20,30,40=1, wave 45=2 (ไม่มี), wave 50=1
        จริงๆ: wave 45 ไม่ใช่ big boss wave (45%10=5 เป็น boss)
        spec: wave 45 = 2 big boss → แต่ 45%10=5 เป็น boss wave
        ตีความว่า wave 40=1, wave 50=1,... wave ที่ >= 100 = 3"""
        if wave >= 100:
            return 3
        if wave >= 45:
            return 2
        return 1

    def _spawn_single(self, force_type=None):
        game = self.game
        etype = force_type or random.choices(
            ["normal", "stalker", "ranger"], weights=[60, 25, 15])[0]
        angle = random.uniform(0, 2 * math.pi)
        r = random.uniform(850, 1100)
        sx = game.player_pos[0] + math.cos(angle) * r
        sy = game.player_pos[1] + math.sin(angle) * r
        enemy = EnemyWidget(spawn_pos=(sx, sy), enemy_type=etype)
        enemy.game = game
        # wave scaling ทุก 5 wave: +5 HP, +4 DMG
        mult = self.current_wave // 5
        if mult > 0:
            enemy.damage += mult * 4
            enemy.hp += mult * 5
            enemy.max_hp = enemy.hp
        game.enemies.append(enemy)
        game.world_layout.add_widget(enemy)
        game.hud.update_enemy_count(len(game.enemies))

    def _spawn_boss(self, intro: bool = True):
        game = self.game
        angle = random.uniform(0, 2 * math.pi)
        bx = game.player_pos[0] + math.cos(angle) * 900
        by = game.player_pos[1] + math.sin(angle) * 900
        boss = EnemyWidget(spawn_pos=(bx, by), enemy_type="boss")
        boss.game = game
        mult = self.current_wave // 5
        boss.hp += mult * 200; boss.max_hp = boss.hp
        game.boss = boss
        game.enemies.append(boss)
        game.world_layout.add_widget(boss)
        game.hud.update_enemy_count(len(game.enemies))
        if intro:
            self.start_boss_intro(1, is_big=False)

    def _spawn_big_boss(self, intro: bool = True):
        game = self.game
        angle = random.uniform(0, 2 * math.pi)
        bx = game.player_pos[0] + math.cos(angle) * 900
        by = game.player_pos[1] + math.sin(angle) * 900
        boss = EnemyWidget(spawn_pos=(bx, by), enemy_type="big_boss")
        boss.game = game
        mult = self.current_wave // 5
        boss.hp += mult * 400; boss.max_hp = boss.hp
        game.big_boss = boss
        game.enemies.append(boss)
        game.world_layout.add_widget(boss)
        game.hud.update_enemy_count(len(game.enemies))
        if intro:
            self.start_boss_intro(1, is_big=True)

    def start_boss_intro(self, boss_count: int, is_big: bool):
        game = self.game
        game.zoom_target = 3.0
        game.is_boss_intro = True
        tag = "BIG BOSS" if is_big else "BOSS"
        color = (0.8, 0.1, 0.8, 1) if is_big else (0.9, 0.2, 0.2, 1)
        multiplier = f"  ×{boss_count}" if boss_count > 1 else ""
        self._show_boss_overlay(f"{tag}{multiplier}", color)

    # ── UI helpers ─────────────────────────────────────────
    def _show_wave_title(self):
        game = self.game
        if self._wave_label and self._wave_label.parent:
            game.root_layout.remove_widget(self._wave_label)
        self._wave_label = Label(
            text=f"[b]WAVE {self.current_wave}[/b]",
            markup=True, font_size=80,
            color=(1, 1, 1, 1), outline_width=4, outline_color=(0, 0, 0, 1),
            pos_hint={"center_x": 0.5, "top": 0.92},
        )
        game.root_layout.add_widget(self._wave_label)
        game.hud.update_wave(self.current_wave)
        Clock.schedule_once(self._hide_wave_title, 1.5)

    def _hide_wave_title(self, _dt):
        if self._wave_label and self._wave_label.parent:
            self.game.root_layout.remove_widget(self._wave_label)
        self._wave_label = None

    def _show_boss_overlay(self, text, color):
        game = self.game
        if self._boss_overlay and self._boss_overlay.parent:
            game.root_layout.remove_widget(self._boss_overlay)
        self._boss_overlay = Label(
            text=f"[b]{text}[/b]",
            markup=True, font_size=100,
            color=color, outline_width=4, outline_color=(0, 0, 0, 1),
            pos_hint={"center_x": 0.5, "center_y": 0.7},
        )
        game.root_layout.add_widget(self._boss_overlay)
        Clock.schedule_once(self._end_boss_intro, 2.0)

    def _end_boss_intro(self, _dt):
        self.game.is_boss_intro = False
        self.game.zoom_target = 1.8
        if self._boss_overlay and self._boss_overlay.parent:
            self.game.root_layout.remove_widget(self._boss_overlay)
        self._boss_overlay = None
