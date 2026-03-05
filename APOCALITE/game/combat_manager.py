"""game/combat_manager.py — collision + combat per frame"""
import math
from game.projectile_widget import RPGRocket
from game.skills import _hit_enemy


class CombatManager:
    PICKUP_RADIUS = 50.0
    EXP_PICKUP_RADIUS = 55.0
    MELEE_RADIUS = 45.0
    MELEE_COOLDOWN = 0.8
    PROJ_MAX_DIST = 1200.0
    PLAYER_HIT_RADIUS = 35.0

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
                        
                        # 🌟 Lifesteal for HomingDino (PTae Skill 2)
                        if type(b).__name__ == "HomingDino":
                            heal_amount = b.damage * 0.5
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
            proj.update(dt)
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
                heal = getattr(item,'heal_amount',25)
                g.player_stats.current_hp = min(g.player_stats.hp,
                                                 g.player_stats.current_hp + heal)
                g.hud.update_ui(g.player_stats)
                g.dropped_items.remove(item)
                if item.parent: g.world_layout.remove_widget(item)

    # ── EXP orbs ────────────────────────────────────────────
    def _exp_orbs(self, p_cx, p_cy):
        g = self.game
        for orb in list(g.exp_orbs):
            ox = orb.pos[0] + orb.size[0]/2
            oy = orb.pos[1] + orb.size[1]/2
            if math.hypot(ox-p_cx, oy-p_cy) < self.EXP_PICKUP_RADIUS:
                g.gain_exp(orb.exp_amount)
                g.exp_orbs.remove(orb)
                if orb.parent: g.world_layout.remove_widget(orb)

    # ── Enemy melee ─────────────────────────────────────────
    def _enemy_melee(self, dt, p_cx, p_cy):
        g = self.game
        for enemy in list(g.enemies):
            ec_x = enemy.pos[0] + (enemy.enemy_size[0]/2 if hasattr(enemy,'enemy_size') else 20)
            ec_y = enemy.pos[1] + (enemy.enemy_size[1]/2 if hasattr(enemy,'enemy_size') else 20)
            if math.hypot(ec_x-p_cx, ec_y-p_cy) < self.MELEE_RADIUS:
                if not hasattr(enemy,'_melee_cd'): enemy._melee_cd = 0.0
                enemy._melee_cd -= dt
                if enemy._melee_cd <= 0:
                    g.take_damage(enemy.damage)
                    enemy._melee_cd = self.MELEE_COOLDOWN


