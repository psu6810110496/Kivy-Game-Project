# ในไฟล์ game/player.py
class PlayerStats:
    def __init__(self, name, hp, speed, damage, idle_frames, walk_frames):
        self.name = name
        self.hp = hp
        self.speed = speed
        self.damage = damage
        self.idle_frames = idle_frames
        self.walk_frames = walk_frames
        self.reset() # เรียกใช้ตอนสร้างครั้งแรก

    def reset(self):
        """ ฟังก์ชันล้างค่าตัวละคร """
        self.current_hp = self.hp
        self.level = 1
        self.exp = 0
        self.max_exp = 100