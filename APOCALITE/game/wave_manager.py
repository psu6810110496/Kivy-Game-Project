"""game/wave_manager.py — Wave/Boss spawning + progression scaling"""
import math
import random
from game.sound_manager import sound_manager

from kivy.clock import Clock
from kivy.uix.label import Label

from game.enemy_widget import EnemyWidget
from ui.font import PIXEL_FONT


class WaveManager:
    def __init__(self, game):
        self.game = game
        self.current_wave: int = 0
        self.is_spawning: bool = False
        self._wave_label = None
        self._boss_overlay = None
        self._wave_stopped: bool = False  # debug: stop wave

    def reset(self):
        self.current_wave = 0
        self.is_spawning = False
        self._wave_label = None
        self._boss_overlay = None
        # 🌟 Cancel any pending victory timers
        if hasattr(self, '_win_music_ev'): Clock.unschedule(self._win_music_ev)
        if hasattr(self, '_win_screen_ev'): Clock.unschedule(self._win_screen_ev)

    def try_start_next_wave(self):
        # Guard: Don't trigger if spawning, dead, stopped, or already won
        if self.is_spawning or self.game.is_dead or self._wave_stopped or self.current_wave > 21:
            return
            
        self.current_wave += 1
        
        # Check Win Condition: All 21 waves cleared
        if self.current_wave > 21:
            # ทิ้งความเงียบ 3 วินาทีก่อนเริ่มเพลง End Credit
            def _start_music(dt):
                from game.sound_manager import sound_manager
                sound_manager.stop_bgm()  # สรุปเพลงที่เปิดอยู่แล้วถ้ามี
                sound_manager.play_bgm("endcredit", loop=False, seek_pos=49.0)
            
            self._win_music_ev = Clock.schedule_once(_start_music, 3.0)

            def _delayed_victory(dt):
                if not self.game.is_dead:
                    self.game.show_game_over(win=True)
            
            self._win_screen_ev = Clock.schedule_once(_delayed_victory, 22.0)
            return

        self.is_spawning = True
        self._show_wave_title()
        Clock.schedule_once(self._spawn_enemies, 1.5)

    # ── Spawn Helpers ─────────────────────────────────────

    def _get_valid_spawn_pos(self, enemy_type, r_min=850, r_max=1100):
        """
        สุ่มตำแหน่งที่อยู่ภายในแมพ และไม่ทับกับสิ่งกีดขวาง (รถ)
        """
        game = self.game
        # ขนาดศัตรูอ้างอิงจาก EnemyWidget.__init__
        sizes = {
            "normal": (40, 40), "stalker": (30, 30), "ranger": (45, 45),
            "charger": (55, 55), "shielder": (65, 65), "bomber": (50, 50),
            "sniper": (45, 45), "boss": (96, 96), "big_boss": (128, 128)
        }
        ew, eh = sizes.get(enemy_type, (40, 40))
        
        # แมพขนาด 5000x5000 (0,0 ถึง 5000,5000)
        # เผื่อ padding 50 พิกเซล
        map_min_x, map_min_y = 50, 50
        map_max_x, map_max_y = 4950 - ew, 4950 - eh

        for _ in range(20): # ลองสุ่ม 20 ครั้ง
            angle = random.uniform(0, 2 * math.pi)
            r = random.uniform(r_min, r_max)
            sx = game.player_pos[0] + math.cos(angle) * r
            sy = game.player_pos[1] + math.sin(angle) * r
            
            # 1. เช็คขอบเขตแมพ
            if not (map_min_x <= sx <= map_max_x and map_min_y <= sy <= map_max_y):
                continue
                
            # 2. เช็คการชนกับสิ่งกีดขวาง
            collides = False
            for obs in game.obstacles:
                if obs.collides_with(sx, sy, ew, eh):
                    collides = True
                    break
            if collides:
                continue
                
            return sx, sy
            
        # หากสุ่มไม่ได้จริงๆ (ผู้เล่นอาจอยู่มุมแมพจนที่ว่างรอบๆ น้อย)
        # ให้ใช้ตำแหน่งที่สุ่มได้ล่าสุดแล้วบีบให้อยู่ในแมพ (Clamp) เพื่อกันไม่ให้ออกนอกแมพ
        # แม้ว่าอาจจะยังทับรถบ้างแต่ก็ดีกว่าออกนอกแมพ
        angle = random.uniform(0, 2 * math.pi)
        r = random.uniform(r_min, r_max)
        sx = max(map_min_x, min(map_max_x, game.player_pos[0] + math.cos(angle) * r))
        sy = max(map_min_y, min(map_max_y, game.player_pos[1] + math.sin(angle) * r))
        return sx, sy

    # ── Spawn Logic ────────────────────────────────────────

    def _spawn_enemies(self, _dt):
        game = self.game
        if game.is_dead or not game.game_started:
            self.is_spawning = False
            return

        w = self.current_wave

        if w == 21:
            # Final Boss Wave
            sound_manager.crossfade_to_bgm("bossfight")
            self._spawn_final_boss()
            self.is_spawning = False
            return

        is_big_boss = (w % 10 == 0 and w > 0)
        is_boss = (w % 10 == 5)

        if is_big_boss:
            bb_count = self._big_boss_count(w)
            b_count = self._boss_count_in_big_boss_wave(w)
            for _ in range(bb_count):
                self._spawn_big_boss(intro=False)
            for _ in range(b_count):
                self._spawn_boss(intro=False)
            for _ in range(8):
                self._spawn_single()
            self.is_spawning = False
            sound_manager.crossfade_to_bgm("bossfight")
            Clock.schedule_once(lambda _: self.start_boss_intro(bb_count, is_big=True), 0.1)
        elif is_boss:
            count = self._boss_count(w)
            for _ in range(count):
                self._spawn_boss(intro=False)
            for _ in range(5):
                self._spawn_single()
            self.is_spawning = False
            sound_manager.crossfade_to_bgm("bossfight")
            Clock.schedule_once(lambda _: self.start_boss_intro(count, is_big=False), 0.1)
        else:
            # 🌟 เมื่อกลับมาเป็น Wave ปกติ ให้เปลี่ยนเพลงกลับเป็น In-Game แบบ Smooth
            if sound_manager.current_bgm_name == "bossfight":
                sound_manager.crossfade_to_bgm("ingame")
                
            # 🌟 [Optimization] Cap total enemies at 100 to prevent extreme lag
            if len(game.enemies) < 100: 
                for _ in range(5 + w):
                    self._spawn_single()
                    if len(game.enemies) >= 100: break
            self.is_spawning = False

    def _boss_count(self, wave: int) -> int:
        """wave 5=1, 15=2, 25=3 … สูงสุด 10"""
        return min(10, 1 + (wave - 5) // 10)

    def _big_boss_count(self, wave: int) -> int:
        w_index = wave // 10
        if w_index <= 0: return 1
        return math.ceil((w_index + 0.1) / 2)

    def _boss_count_in_big_boss_wave(self, wave: int) -> int:
        if wave < 30 or (wave // 10) % 2 == 0:
            return 0
        w_index = wave // 10
        return 4 + (w_index - 3) // 2

    def _spawn_single(self, force_type=None):
        game = self.game
        w = self.current_wave
        
        weights = [60, 25, 15] # normal, stalker, ranger
        choices = ["normal", "stalker", "ranger"]
        
        if w >= 2:
            choices.extend(["charger", "bomber"])
            weights.extend([12, 14])
        if w >= 4:
            choices.extend(["shielder", "sniper"])
            weights.extend([18, 12])
            
        etype = force_type or random.choices(choices, weights=weights)[0]
        
        # ใช้ helper ในการหาตำแหน่งที่ถูกต้อง
        sx, sy = self._get_valid_spawn_pos(etype)
        
        enemy = EnemyWidget(spawn_pos=(sx, sy), enemy_type=etype)
        enemy.game = game
        
        # Stat scaling
        self._apply_wave_scaling(enemy)
            
        game.enemies.append(enemy)
        game.world_layout.add_widget(enemy)
        game.hud.update_enemy_count(len(game.enemies))

    def _spawn_boss(self, intro: bool = True):
        game = self.game
        etype = "boss"
        bx, by = self._get_valid_spawn_pos(etype, r_min=850, r_max=950)
        
        boss = EnemyWidget(spawn_pos=(bx, by), enemy_type=etype)
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
        etype = "big_boss"
        bx, by = self._get_valid_spawn_pos(etype, r_min=850, r_max=950)
        
        boss = EnemyWidget(spawn_pos=(bx, by), enemy_type=etype)
        boss.game = game
        
        self._apply_wave_scaling(boss)
        
        game.big_boss = boss
        game.enemies.append(boss)
        game.world_layout.add_widget(boss)
        game.hud.update_enemy_count(len(game.enemies))
        if intro:
            self.start_boss_intro(1, is_big=True)

    def _spawn_final_boss(self):
        game = self.game
        etype = "final_boss"
        bx, by = self._get_valid_spawn_pos(etype, r_min=850, r_max=950)
        
        boss = EnemyWidget(spawn_pos=(bx, by), enemy_type=etype)
        boss.game = game
        # Final Boss fixed stats, no extra wave scaling needed beyond definition
        game.boss = boss
        game.enemies.append(boss)
        game.world_layout.add_widget(boss)
        game.hud.update_enemy_count(len(game.enemies))
        # Special Intro
        Clock.schedule_once(lambda _: self.start_boss_intro(1, is_big=False, is_final=True), 0.1)
        # 🌟 Start spawning XP periodically for Wave 21
        Clock.schedule_interval(self._spawn_wave_21_xp, 3.0)
        # 🌟 Start spawning Heal periodically for Wave 21
        Clock.schedule_interval(self._spawn_wave_21_heal, 8.0)

    def _spawn_wave_21_xp(self, dt):
        """สุ่มเสก XP ให้ผู้เล่นเก็บใน Wave 21 (Final Boss)"""
        if self.current_wave != 21 or self.game.is_dead or not self.game.game_started:
            return False # Stop interval
            
        # เสก XP 8-12 เม็ด กระจายรอบตัวผู้เล่น (รัศมี 300-900)
        for _ in range(random.randint(8, 12)):
            pos = self._get_valid_spawn_pos("normal", r_min=300, r_max=900)
            self.game.spawn_exp_orb(pos)
        return True

    def _spawn_wave_21_heal(self, dt):
        """สุ่มเสกเลือดให้ผู้เล่นเก็บใน Wave 21 (Final Boss)"""
        if self.current_wave != 21 or self.game.is_dead or not self.game.game_started:
            return False # Stop interval
            
        # เสกเลือด 1-2 กล่องรอบตัวผู้เล่น
        for _ in range(random.randint(1, 2)):
            pos = self._get_valid_spawn_pos("normal", r_min=200, r_max=600)
            from game.projectile_widget import HealthPickup
            l_tex = getattr(self.game.player_stats, 'heal_large_tex', None)
            # ปรับเป็น 15% (Heal 2)
            heal = HealthPickup(pos=(pos[0], pos[1]), heal_percent=0.15, size=(32, 32), texture_path=l_tex)
            self.game.dropped_items.append(heal)
            self.game.world_layout.add_widget(heal)
        return True

    def _apply_wave_scaling(self, enemy):
        """ใส่ HP / DMG bonus ตาม wave ให้ศัตรู"""
        w = self.current_wave
        
        if enemy.enemy_type == "boss":
            if w > 5:
                # ตั้งแต่ครั้งที่ 2 เป็นต้นไป (Wave 15+) ให้บวกโบนัสและคูณ 2
                mult = w // 5
                enemy.hp += mult * 100
                enemy.hp *= 2
        elif enemy.enemy_type == "big_boss":
            if w > 10:
                # ตั้งแต่ครั้งที่ 2 เป็นต้นไป (Wave 20+) ให้บวกโบนัสและคูณ 2
                mult10 = w // 10
                enemy.hp += mult10 * 400
                enemy.hp *= 2
        elif enemy.enemy_type in ("final_boss", "final_boss_clone"):
            # Final Boss มีค่าคงที่แล้ว ไม่ต้องบวกเพิ่ม
            pass
        else:
            # มอนปกติ: เลือด +5 ทุก wave, ดาเมจ +10 ทุก 5 wave
            enemy.hp += w * 5
            mult = w // 5
            enemy.damage += mult * 10
        
        enemy.max_hp = enemy.hp

    def start_boss_intro(self, boss_count: int, is_big: bool, is_final: bool = False):
        game = self.game
        game.zoom_target = 2.8
        game.is_boss_intro = True
        
        if is_final:
            tag = "FINAL BOSS"
            color = (0.5, 0.0, 1.0, 1) # Purple
        else:
            tag = "BIG BOSS" if is_big else "BOSS"
            color = (0.8, 0.1, 0.8, 1) if is_big else (0.9, 0.2, 0.2, 1)
            
        multiplier = f"  x{boss_count}" if boss_count > 1 else ""
        self._show_boss_overlay(f"{tag}{multiplier}", color)

    # ── UI helpers ─────────────────────────────────────────

    def _show_wave_title(self):
        game = self.game
        if self._wave_label and self._wave_label.parent:
            game.root_layout.remove_widget(self._wave_label)
        self._wave_label = Label(
            text=f"[b]WAVE {self.current_wave}[/b]",
            markup=True, font_size=80,
            font_name=PIXEL_FONT,
            color=(1, 1, 1, 1),
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
            font_name=PIXEL_FONT,
            color=color,
            pos_hint={"center_x": 0.5, "center_y": 0.7},
        )
        game.root_layout.add_widget(self._boss_overlay)
        Clock.schedule_once(self._end_boss_intro, 2.0)

    def _end_boss_intro(self, _dt):
        self.game.is_boss_intro = False
        self.game.zoom_target = 1.9
        if self._boss_overlay and self._boss_overlay.parent:
            self.game.root_layout.remove_widget(self._boss_overlay)
        self._boss_overlay = None
