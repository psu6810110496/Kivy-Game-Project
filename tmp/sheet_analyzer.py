from PIL import Image
import os

def analyze_sheet(path, frame_w, frame_h):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return
    img = Image.open(path)
    w, h = img.size
    print(f"Analyzing {path}: {w}x{h}")
    # Check simple multiples
    for size in [32, 40, 48, 50, 64, 70, 80, 96, 100, 128]:
        if w % size == 0:
            print(f" - Width {w} is multiple of {size} ({w//size} frames)")
        if h % size == 0:
            print(f" - Height {h} is multiple of {size} ({h//size} rows)")

analyze_sheet('../assets/enemy/enemy1.png', 70, 70)
analyze_sheet('../assets/enemy/Canine_Black_Run.png', 64, 64)
analyze_sheet('../assets/enemy/enemy3.png', 170, 128)
