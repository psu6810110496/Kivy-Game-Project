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
        LabelBase.register(
            name="PixelFont",
            fn_regular="assets/fornt/Stacked pixel.ttf",
        )
        _registered = True
    except Exception:
        pass

_register()

# ชื่อฟ้อนต์ที่ใช้ทั่วโปรเจกต์
PIXEL_FONT = "PixelFont"
