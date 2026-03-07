import os
from kivy.core.image import Image as CoreImage

def resolve_path(p):
    """Helper ในการหา Path ของ Asset ให้เจอไม่ว่าจะรันจากโฟลเดอร์ไหน"""
    trials = [
        p,                                      # CWD
        os.path.join("..", p),                  # Parent (if in APOCALITE)
        os.path.join("APOCALITE", p),           # Child (if in root)
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", p)) # relative to project root
    ]
    for t in trials:
        if os.path.exists(t): return t.replace('\\', '/')
    return None

def get_frames(path, frame_w, frame_h, frames_count, row=0):
    """แบ่งเฟรมจาก SpriteSheet (Pygame สไตล์: row 0 คือแถวบนสุด)"""
    full_path = resolve_path(path)
    if not full_path:
        print(f"[Utils] ❌ Asset NOT FOUND: {path}")
        return []
    
    try:
        img = CoreImage(full_path).texture
        # คำนวณ Y ใหม่ให้ Row 0 อยู่บนสุด (Pygame style)
        # Kivy origin อยู่ล่างซ้าย ดังนั้น Row 0 (บนสุด) คือ y = total_h - frame_h
        total_h = img.height
        y = total_h - (row + 1) * frame_h
        
        res = []
        for i in range(frames_count):
            res.append(img.get_region(i * frame_w, y, frame_w, frame_h))
        return res
    except Exception as e:
        print(f"[Utils] ❌ Error slicing {path}: {e}")
        return []
