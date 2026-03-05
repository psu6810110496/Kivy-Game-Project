"""
game/wave_manager.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WaveManager — จัดการ Wave / Boss / BigBoss ทั้งหมด
แยกออกจาก GameScreen เพื่อให้ engine.py สะอาดขึ้น

ความรับผิดชอบ:
  - นับและเริ่ม wave ใหม่
  - spawn ศัตรูปกติ / boss / big_boss
  - แสดง overlay ข้อความ wave / boss
  - scale stat ศัตรูตาม wave
  - อัปเดต max_exp ผู้เล่นต่อ wave
"""
import math
import random

from kivy.clock import Clock
from kivy.uix.label import Label

from game.enemy_widget import EnemyWidget


class WaveManager:
    """
    ผูกกับ GameScreen ผ่าน self.game
    เรียก game.world_layout, game.enemies, game.hud, game.player_stats ฯลฯ
    """

    BOSS_WAVE_INTERVAL = 5    # wave 5, 15, 25 … → boss
    BIG_BOSS_WAVE_INTERVAL = 10  # wave 10, 20, 30 … → big boss

    def __init__(self, game):
        self.game = game
        self.current_wave: int = 0
        self.is_spawning: bool = False
        self._wave_label = None
        self._boss_overlay = None

    # ─── Public ────────────────────────────────────────────
    def try_start_next_wave(self):
        """เรียกจาก update_frame เมื่อศัตรูหมด"""
        if self.is_spawning or self.game.is_dead:
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

    # ─── Spawn ─────────────────────────────────────────────
    def _spawn_enemies(self, _dt):
        game = self.game
        if game.is_dead or not game.game_started:
            self.is_spawning = False
            return

        # อัปเดต max_exp ต่อ wave
        if game.player_stats:
            game.player_stats.max_exp += 50
            game.hud.update_ui(game.player_stats)

        # อัปเดต skill max_level
        if game.player_stats and hasattr(game.player_stats, "skills"):
            for skill in game.player_stats.skills:
                skill.max_level = 5 + self.current_wave

        w = self.current_wave
        is_big_boss = (w % self.BIG_BOSS_WAVE_INTERVAL == 0 and w > 0)
        is_boss = (w % self.BIG_BOSS_WAVE_INTERVAL == self.BOSS_WAVE_INTERVAL and not is_big_boss)

        if is_big_boss:
            self._spawn_big_boss()
            for _ in range(8):
                self._spawn_single()
        elif is_boss:
            self._spawn_boss()
            for _ in range(5):
                self._spawn_single()
        else:
            for _ in range(5 + w * 2):
                self._spawn_single()

        self.is_spawning = False

    def _spawn_single(self, force_type: str | None = None):
        game = self.game
        etype = force_type or random.choices(
            ["normal", "stalker", "ranger"], weights=[60, 25, 15]
        )[0]
        angle = random.uniform(0, 2 * math.pi)
        r = random.uniform(850, 1100)
        sx = game.player_pos[0] + math.cos(angle) * r
        sy = game.player_pos[1] + math.sin(angle) * r

        enemy = EnemyWidget(spawn_pos=(sx, sy), enemy_type=etype)
        enemy.game = game

        # Wave scaling ทุก 5 wave
        mult = self.current_wave // 5
        if mult > 0:
            enemy.damage += mult * 3.5
            enemy.hp += mult * 2.5
            enemy.max_hp = enemy.hp

        game.enemies.append(enemy)
        game.world_layout.add_widget(enemy)
        game.hud.update_enemy_count(len(game.enemies))

    def _spawn_boss(self):
        game = self.game
        angle = random.uniform(0, 2 * math.pi)
        bx = game.player_pos[0] + math.cos(angle) * 900
        by = game.player_pos[1] + math.sin(angle) * 900
        boss = EnemyWidget(spawn_pos=(bx, by), enemy_type="boss")
        boss.game = game

        # Wave scaling
        mult = self.current_wave // 5
        boss.hp += mult * 200
        boss.max_hp = boss.hp

        game.boss = boss
        game.enemies.append(boss)
        game.world_layout.add_widget(boss)
        game.hud.update_enemy_count(len(game.enemies))
        game.zoom_target = 3.0
        game.is_boss_intro = True
        self._show_boss_overlay("BOSS ARISE", (0.9, 0.2, 0.2, 1))

    def _spawn_big_boss(self):
        game = self.game
        angle = random.uniform(0, 2 * math.pi)
        bx = game.player_pos[0] + math.cos(angle) * 900
        by = game.player_pos[1] + math.sin(angle) * 900
        boss = EnemyWidget(spawn_pos=(bx, by), enemy_type="big_boss")
        boss.game = game

        mult = self.current_wave // 5
        boss.hp += mult * 400
        boss.max_hp = boss.hp

        game.big_boss = boss
        game.enemies.append(boss)
        game.world_layout.add_widget(boss)
        game.hud.update_enemy_count(len(game.enemies))
        game.zoom_target = 3.0
        game.is_boss_intro = True
        self._show_boss_overlay("BIG BOSS ARRIVES", (0.8, 0.1, 0.8, 1))

    # ─── UI helpers ────────────────────────────────────────
    def _show_wave_title(self):
        game = self.game
        if self._wave_label and self._wave_label.parent:
            game.root_layout.remove_widget(self._wave_label)
        self._wave_label = Label(
            text=f"[b]WAVE {self.current_wave}[/b]",
            markup=True,
            font_size=64,
            color=(1, 1, 1, 1),
            outline_width=3,
            outline_color=(0, 0, 0, 1),
            pos_hint={"center_x": 0.5, "top": 0.95},
        )
        game.root_layout.add_widget(self._wave_label)
        game.hud.update_wave(self.current_wave)
        Clock.schedule_once(self._hide_wave_title, 1.5)

    def _hide_wave_title(self, _dt):
        if self._wave_label and self._wave_label.parent:
            self.game.root_layout.remove_widget(self._wave_label)
        self._wave_label = None

    def _show_boss_overlay(self, text: str, color: tuple):
        game = self.game
        if self._boss_overlay and self._boss_overlay.parent:
            game.root_layout.remove_widget(self._boss_overlay)
        self._boss_overlay = Label(
            text=f"[b]{text}[/b]",
            markup=True,
            font_size=120,
            color=color,
            outline_width=3,
            outline_color=(0, 0, 0, 1),
            pos_hint={"center_x": 0.5, "center_y": 0.7},
        )
        game.root_layout.add_widget(self._boss_overlay)
        Clock.schedule_once(self._end_boss_intro, 2.0)

    def _end_boss_intro(self, _dt):
        self.game.is_boss_intro = False
        self.game.zoom_target = 2.0
        if self._boss_overlay and self._boss_overlay.parent:
            self.game.root_layout.remove_widget(self._boss_overlay)
        self._boss_overlay = None
