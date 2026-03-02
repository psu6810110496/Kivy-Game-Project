class PlayerStats:
    def __init__(self, name, hp, speed, damage, idle_frames=None, walk_frames=None):
        self.name = name
        self.hp = hp            # เลือดสูงสุด
        self.speed = speed
        self.damage = damage
        self.idle_frames = idle_frames
        self.walk_frames = walk_frames
        
        # --- ค่าสถานะพื้นฐานที่ HUD น่าจะต้องการ ---
        self.level = 1          # เริ่มต้นที่เลเวล 1
        self.current_hp = hp    # เลือดปัจจุบัน (เริ่มเกมมาเลือดต้องเต็ม)
        self.exp = 0            # ค่าประสบการณ์เริ่มต้น
        self.max_exp = 100      # EXP ที่ต้องใช้เพื่ออัปเลเวล