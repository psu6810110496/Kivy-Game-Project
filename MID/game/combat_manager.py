"""
game/combat_manager.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CombatManager — จัดการ collision / combat ทั้งหมดต่อ frame

ความรับผิดชอบ:
  - อัปเดตกระสุนผู้เล่น + เช็ค hit ศัตรู (รองรับ RPGRocket AoE)
  - อัปเดตกระสุนศัตรู + เช็ค hit ผู้เล่น
  - ตรวจจับ melee collision ศัตรู-ผู้เล่น (พร้อม cooldown)
  - เช็คการเก็บ HealthPickup
  - เช็คการเก็บ ExpOrb
  - ตรวจสอบ boss reference clear เมื่อตาย
"""
import math

class CombatManager:
    """
    ผูกกับ GameScreen ผ่าน self.game
    เรียกทุก frame ผ่าน update(dt)
    """

    PICKUP_RADIUS: float = 50.0
    EXP_PICKUP_RADIUS: float = 55.0
    MELEE_RADIUS: float = 45.0
    MELEE_COOLDOWN: float = 0.8
    PROJ_MAX_DIST: float = 1200.0
    PLAYER_HIT_RADIUS: float = 35.0

    def __init__(self, game):
        self.game = game

    def update(self, dt: float):
        game = self.game
        self._dt = dt
        p_cx = game.player_pos[0] + 32
        p_cy = game.player_pos[1] + 32

        self._update_player_bullets(p_cx, p_cy)
        self._update_enemy_projectiles(dt, p_cx, p_cy)
        self._update_pickups(p_cx, p_cy)
        self._update_exp_orbs(p_cx, p_cy)
        self._update_enemy_melee(dt, p_cx, p_cy)

    # ─── Player bullets ────────────────────────────────────
    def _update_player_bullets(self, p_cx, p_cy):
        game = self.game
        from game.projectile_widget import RPGRocket
        for b in list(game.player_bullets):
            still_alive = b.update(self._dt)
            if not still_alive:
                self._remove_bullet(b)
                continue

            for enemy in list(game.enemies):
                ec_x = enemy.pos[0] + enemy.enemy_size[0] / 2
                ec_y = enemy.pos[1] + enemy.enemy_size[1] / 2
                if math.hypot(b.pos[0] - ec_x, b.pos[1] - ec_y) < 40:
                    if isinstance(b, RPGRocket):
                        b.explode(game)
                    else:
                        is_boss = (enemy is game.boss or enemy is getattr(game, "big_boss", None))

                    # 🌟 เปลี่ยนจากการเรียก _hit_enemy(...) เป็นโค้ดชุดนี้แทน:
                    enemy.take_damage(b.damage)
                    
                    if enemy.hp <= 0:
                        if enemy in game.enemies:
                            game.enemies.remove(enemy)
                        if enemy.parent:
                            enemy.parent.remove_widget(enemy)
                            
                        # ได้รับ EXP
                        game.gain_exp(10) 
                        
                        # สุ่มดรอปยา
                        if hasattr(game, "spawn_drop_item"):
                            game.spawn_drop_item(enemy.pos)

    def _remove_bullet(self, b):
        game = self.game
        if b in game.player_bullets:
            game.player_bullets.remove(b)
        if b.parent:
            game.world_layout.remove_widget(b)

    # ─── Enemy projectiles ─────────────────────────────────
    def _update_enemy_projectiles(self, dt: float, p_cx: float, p_cy: float):
        game = self.game
        for proj in list(game.enemy_projectiles):
            proj.update(dt)
            dist = math.hypot(proj.pos[0] - p_cx, proj.pos[1] - p_cy)
            if dist < self.PLAYER_HIT_RADIUS:
                game.take_damage(proj.damage)
                self._remove_projectile(proj)
            elif dist > self.PROJ_MAX_DIST:
                self._remove_projectile(proj)

    def _remove_projectile(self, proj):
        game = self.game
        if proj in game.enemy_projectiles:
            game.enemy_projectiles.remove(proj)
        if proj.parent:
            game.world_layout.remove_widget(proj)

    # ─── Health pickups ────────────────────────────────────
    def _update_pickups(self, p_cx: float, p_cy: float):
        game = self.game
        for item in list(game.dropped_items):
            iw = item.size[0] if item.size else 28
            ih = item.size[1] if item.size else 28
            ix = item.pos[0] + iw / 2
            iy = item.pos[1] + ih / 2
            if math.hypot(ix - p_cx, iy - p_cy) < self.PICKUP_RADIUS:
                heal = getattr(item, "heal_amount", 25)
                game.player_stats.current_hp = min(
                    game.player_stats.hp,
                    game.player_stats.current_hp + heal,
                )
                game.hud.update_ui(game.player_stats)
                game.dropped_items.remove(item)
                if item.parent:
                    game.world_layout.remove_widget(item)

    # ─── EXP orbs ──────────────────────────────────────────
    def _update_exp_orbs(self, p_cx: float, p_cy: float):
        """เก็บ ExpOrb — รองรับ game.exp_orbs list (optional)"""
        game = self.game
        exp_orbs = getattr(game, "exp_orbs", None)
        if not exp_orbs:
            return
        for orb in list(exp_orbs):
            ox = orb.pos[0] + orb.size[0] / 2
            oy = orb.pos[1] + orb.size[1] / 2
            if math.hypot(ox - p_cx, oy - p_cy) < self.EXP_PICKUP_RADIUS:
                game.gain_exp(getattr(orb, "exp_amount", 10))
                exp_orbs.remove(orb)
                if orb.parent:
                    game.world_layout.remove_widget(orb)

    # ─── Enemy melee ───────────────────────────────────────
    def _update_enemy_melee(self, dt: float, p_cx: float, p_cy: float):
        game = self.game
        for enemy in list(game.enemies):
            ec_x = enemy.pos[0] + (enemy.enemy_size[0] / 2 if hasattr(enemy, "enemy_size") else 20)
            ec_y = enemy.pos[1] + (enemy.enemy_size[1] / 2 if hasattr(enemy, "enemy_size") else 20)
            
            # 🌟 ลบ and not game.is_invincible ออก เหลือแค่นี้:
            if math.hypot(ec_x - p_cx, ec_y - p_cy) < self.MELEE_RADIUS:
                
                # ระบบตีแบบมี Cooldown ของศัตรู
                if not hasattr(enemy, "attack_cooldown_timer"):
                    enemy.attack_cooldown_timer = 0
                    
                enemy.attack_cooldown_timer -= dt
                
                if enemy.attack_cooldown_timer <= 0:
                    game.take_damage(enemy.damage)
                    enemy.attack_cooldown_timer = self.MELEE_COOLDOWN