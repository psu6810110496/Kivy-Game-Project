"""game/combat_manager.py — collision + combat per frame"""
import math
from game.projectile_widget import RPGRocket
from game.skills import _hit_enemy


class CombatManager:
    PICKUP_RADIUS = 50.0
    EXP_PICKUP_RADIUS = 55.0
    MELEE_RADIUS = 45.0
    MELEE_COOLDOWN = 0.8
    PLAYER_HIT_RADIUS = 20.0
    PROJ_MAX_DIST = 900.0   # ลดระยะ cleanup กระสุนที่หลงไปไกล
    EXP_ORB_MAX = 150       # จำนวน EXP orb สูงสุด เพื่อป้องกันเกมกระตุก

    def __init__(self, game):
        self.game = game
        self._dt = 1/60.0

    def update(self, dt: float):
        self._dt = dt
        g = self.game
        p_cx = g.player_pos[0] + 32
        p_cy = g.player_pos[1] + 32
        self._player_bullets(p_cx, p_cy)
        self._enemy_projectiles(dt, p_cx, p_cy)
        self._pickups(p_cx, p_cy)
        self._exp_orbs(p_cx, p_cy)
        self._enemy_melee(dt, p_cx, p_cy)


    # ── Player bullets ─────────────────────────────────────
    def _player_bullets(self, p_cx, p_cy):
        g = self.game
        for b in list(g.player_bullets):
            alive = b.update(self._dt)
            if not alive:
                self._rm_bullet(b); continue
                
            # -- Check Obstacle Collision --
            hit_obs = False
            b_cx, b_cy = b.pos[0], b.pos[1]
            
            # 🌟 [Optimization] Only check obstacles if bullet is within general range
            for obs in getattr(g, "obstacles", []):
                # Simple distance check before full collision
                if type(b).__name__ != "DinoBeam":
                    ox, oy = obs.pos[0] + 48, obs.pos[1] + 24
                    if abs(b_cx - ox) < 100 and abs(b_cy - oy) < 100:
                        if obs.collides_with(b_cx - 5, b_cy - 5, 10, 10):
                            if isinstance(b, RPGRocket):
                                b.explode(g)
                            self._rm_bullet(b)
                            hit_obs = True
                            break
            if hit_obs: continue

            for enemy in list(g.enemies):
                ec_x = enemy.pos[0] + enemy.enemy_size[0]/2
                ec_y = enemy.pos[1] + enemy.enemy_size[1]/2
                if math.hypot(b.pos[0]-ec_x, b.pos[1]-ec_y) < 40:
                    # RPGRocket → explode
                    if isinstance(b, RPGRocket):
                        b.explode(g)
                    else:
                        is_boss = (enemy is g.boss or enemy is getattr(g,'big_boss',None))
                        _hit_enemy(g, enemy, b.damage)
                        
                        # 🌟 Lifesteal for HomingDino (PTae Skill 2) - Nerfed to 15%
                        if type(b).__name__ == "HomingDino":
                            from game.sound_manager import sound_manager
                            sound_manager.play_sfx("dino_hit")
                            heal_amount = b.damage * 0.15
                            g.player_stats.current_hp = min(g.player_stats.hp, g.player_stats.current_hp + heal_amount)
                            if hasattr(g, 'hud') and g.hud:
                                g.hud.update_ui(g.player_stats)
                                
                        if is_boss and enemy not in g.enemies:
                            if enemy is g.boss: g.boss = None
                            if hasattr(g,'big_boss') and enemy is g.big_boss: g.big_boss = None
                    self._rm_bullet(b); break

    def _rm_bullet(self, b):
        g = self.game
        if b in g.player_bullets: g.player_bullets.remove(b)
        if b.parent: g.world_layout.remove_widget(b)

    # ── Enemy projectiles ───────────────────────────────────
    def _enemy_projectiles(self, dt, p_cx, p_cy):
        g = self.game
        for proj in list(g.enemy_projectiles):
            alive = proj.update(dt)
            if alive is False:
                self._rm_proj(proj)
                continue
            
            # Check Obstacle Collision
            hit_obs = False
            prj_x, prj_y = proj.pos[0], proj.pos[1]
            for obs in getattr(g, "obstacles", []):
                if obs.collides_with(prj_x - 5, prj_y - 5, 10, 10):
                    self._rm_proj(proj)
                    hit_obs = True
                    break
            if hit_obs: continue

            dist = math.hypot(proj.pos[0]-p_cx, proj.pos[1]-p_cy)
            if dist < self.PLAYER_HIT_RADIUS:
                g.take_damage(proj.damage)
                self._rm_proj(proj)
            elif dist > self.PROJ_MAX_DIST:
                self._rm_proj(proj)

    def _rm_proj(self, proj):
        g = self.game
        if proj in g.enemy_projectiles: g.enemy_projectiles.remove(proj)
        if proj.parent: g.world_layout.remove_widget(proj)

    # ── Health pickups ──────────────────────────────────────
    def _pickups(self, p_cx, p_cy):
        g = self.game
        for item in list(g.dropped_items):
            ix = item.pos[0] + item.size[0]/2
            iy = item.pos[1] + item.size[1]/2
            if math.hypot(ix-p_cx, iy-p_cy) < self.PICKUP_RADIUS:
                if type(item).__name__ == "MagnetPickup":
                    g.magnet_timer = getattr(item, 'duration', 8.0)
                elif type(item).__name__ == "GlobalMagnetPickup":
                    g.global_magnet_timer = getattr(item, 'duration', 8.0)
                else:
                    h_pct = getattr(item, 'heal_percent', 0)
                    if h_pct > 0:
                        heal = g.player_stats.hp * h_pct
                    else:
                        heal = getattr(item, 'heal_amount', 25)
                    g.player_stats.current_hp = min(g.player_stats.hp,
                                                     g.player_stats.current_hp + heal)
                    g.hud.update_ui(g.player_stats)
                g.dropped_items.remove(item)
                if item.parent: g.world_layout.remove_widget(item)

    # ── EXP orbs ────────────────────────────────────────────
    def _exp_orbs(self, p_cx, p_cy):
        g = self.game
        from kivy.clock import Clock
        t = Clock.get_time()
        
        # 🌟 [Optimization] อัปเดตสีรุ้งจากศูนย์กลาง (ทำทีเดียวให้ทุกลูก)
        for orb in g.exp_orbs:
            if hasattr(orb, 'update_visual'):
                orb.update_visual(t)
        
        # 🌟 Cap EXP orbs: ถ้าเกิน limit ให้ลบ orb เก่าสุดที่ตั้งไว้นาน
        if len(g.exp_orbs) > self.EXP_ORB_MAX:
            overflow = len(g.exp_orbs) - self.EXP_ORB_MAX
            for orb in g.exp_orbs[:overflow]:
                if orb.parent: g.world_layout.remove_widget(orb)
            g.exp_orbs = g.exp_orbs[overflow:]
        
        global_mag_pull = getattr(g, 'global_magnet_timer', 0.0) > 0
        mag_pull = getattr(g, 'magnet_timer', 0.0) > 0
        pull_radius = 450.0  # ระยะดูดตอนมี Magnet buff
        pull_spd = 900.0 * self._dt
        
        if global_mag_pull:
            mag_pull = True
            pull_radius = 99999.0
            pull_spd = 1600.0 * self._dt
            
        for orb in list(g.exp_orbs):
            ox = orb.pos[0] + orb.size[0]/2
            oy = orb.pos[1] + orb.size[1]/2
            dist = math.hypot(ox-p_cx, oy-p_cy)
            
            # ดูดถ้ามีบัฟ
            if mag_pull and dist < pull_radius:
                dx = (p_cx - ox) / max(0.1, dist)
                dy = (p_cy - oy) / max(0.1, dist)
                orb.pos = (orb.pos[0] + dx * pull_spd, orb.pos[1] + dy * pull_spd)
                # รีเซ็ตตำแหน่งที่ดูดเข้ามาล่าสุดเพื่อเทียบ pickup 
                ox = orb.pos[0] + orb.size[0]/2
                oy = orb.pos[1] + orb.size[1]/2
                dist = math.hypot(ox-p_cx, oy-p_cy)

            if dist < self.EXP_PICKUP_RADIUS:
                g.gain_exp(orb.exp_amount)
                g.exp_orbs.remove(orb)
                if orb.parent: g.world_layout.remove_widget(orb)

    # ── Enemy melee ─────────────────────────────────────────
    def _enemy_melee(self, dt, p_cx, p_cy):
        g = self.game
        for enemy in list(g.enemies):
            en_size_x = enemy.enemy_size[0] if hasattr(enemy, 'enemy_size') else 40
            en_size_y = enemy.enemy_size[1] if hasattr(enemy, 'enemy_size') else 40
            
            ec_x = enemy.pos[0] + en_size_x / 2
            ec_y = enemy.pos[1] + en_size_y / 2
            
            # Hitbox จะปรับให้พอดีตัว (รัศมีคนเล่น ~18 + รัศมีศัตรูที่ถูกคูณ 0.75 ลดขอบเขตหลอกตา)
            hit_radius = 18 + (en_size_x / 2) * 0.75
            
            if math.hypot(ec_x-p_cx, ec_y-p_cy) < hit_radius:
                if not hasattr(enemy,'_melee_cd'): enemy._melee_cd = 0.0
                enemy._melee_cd -= dt
                if enemy._melee_cd <= 0:
                    g.take_damage(enemy.damage)
                    enemy._melee_cd = self.MELEE_COOLDOWN
                    # 🌟 เล่นแอนิเมชันโจมตีเมื่อกัด/ตีโดนผู้เล่น
                    if hasattr(enemy, "play_attack"):
                        enemy.play_attack(0.4)


