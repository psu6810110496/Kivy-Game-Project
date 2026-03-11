"""
ui/font.py
──────────────────────────────────────────────────────────
ที่เดียวสำหรับจัดการ Font ทั้งโปรเจกต์

ให้ทุกไฟล์ import จากที่นี่:
    from ui.font import PIXEL_FONT
"""
from kivy.core.text import LabelBase

_registered = False

def _register():
    global _registered
    if _registered:
        return
    try:
        import os
        # Robust font path searching
        possible_paths = [
            "assets/fornt/Stacked pixel.ttf",
            "../assets/fornt/Stacked pixel.ttf",
            "APOCALITE/assets/fornt/Stacked pixel.ttf",
            "d:/Kivy-Game-Project/assets/fornt/Stacked pixel.ttf"
        ]
        font_path = None
        for p in possible_paths:
            if os.path.exists(p):
                font_path = p
                break
        
        LabelBase.register(
            name="PixelFont",
            fn_regular=font_path or "assets/fornt/Stacked pixel.ttf",
        )
        _registered = True
    except Exception:
        pass

_register()

# ชื่อฟ้อนต์ที่ใช้ทั่วโปรเจกต์
PIXEL_FONT = "PixelFont"
