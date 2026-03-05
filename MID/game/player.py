"""
game/player.py
"""
class PlayerStats:
    def __init__(
        self, name: str, hp: float, speed: float, damage: float, 
        idle_frames: list, walk_frames: list, skill_loadout: list | None = None, size=(64, 64),
        melee_cooldown: float = 0.5  # 🌟 เพิ่มบรรทัดนี้
    ):
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.speed = speed
        self.damage = damage
        self.size = size  # 🌟 เก็บค่าขนาดตัวละครไว้ใช้ในเกม
        self.melee_cooldown = melee_cooldown
        self.idle_frames = idle_frames
        self.walk_frames = walk_frames
        self.reset()

    def reset(self):
        """รีเซ็ตทุก stat กลับสู่ค่าเริ่มต้น"""
        self.current_hp = self.hp
        self.level = 1
        self.exp = 0
        self.max_exp = 100
        # บังคับให้ไม่มีสกิลใดๆ
        self.skills = []

    @property
    def is_alive(self) -> bool:
        return self.current_hp > 0