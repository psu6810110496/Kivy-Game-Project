# Apocalite - โครงการเกม Kivy

เกมแนว 2D Survival สุดมันส์ โฟกัสการต่อสู้แบบ **fast-paced, action-packed** สร้างด้วยเฟรมเวิร์ก **Kivy** กระโดดสู้กับ Wave ของศัตรู ยำบอส เก็บเลเวล แล้วปลดล็อกสกิลเทพเพื่ออยู่รอดให้ได้นานที่สุด

## Features

### กลไกการเล่นหลัก (Core Gameplay)
- **การเกิดศัตรูแบบเป็น Wave**: ต้องสู้กับคลื่นศัตรูที่มีความยากเพิ่มขึ้นเรื่อยๆ
- **เลือกตัวละครได้**: มีตัวละครให้เลือกหลายแบบ (Lostman, Monkey, PTae, Ranger)
- **ระบบสกิลไดนามิก**: เมื่อเลเวลอัพจะสุ่มให้เลือกสกิลใหม่ๆ เพื่ออัปเกรด
- **ต่อสู้กับบอส**: บอสธรรมดาจะโผล่ทุก 5 Wave (5, 15, 25...) ส่วน Big Boss ระดับตำนานจะโผล่ทุก 10 Wave (10, 20, 30...)
- **กล้องลื่นไหล**: กล้องจะตามผู้เล่นพร้อม damping ให้ความรู้สึกเหมือนซีเนมาติก

### ประเภทของศัตรู
- **Normal**: ศัตรูระยะประชิดธรรมดา ความสมดุล
- **Stalker**: เร็วแต่ HP ต่ำ
- **Ranger**: ยิงไกล พยายามรักษาระยะ
- **Boss**: ศัตรูตัวใหญ่ HP เยอะ โผล่ใน Wave 5,15,25...
- **Big Boss**: บอสระดับตำนานมีสกิลพิเศษ เช่น
  - **Ground Slam**: อัดพื้นเป็นวงรัศมี มีสัญญาณเตือนก่อน
  - **Swipe**: ตวัดตัวพุ่งไปข้างหน้าเร็วๆ
  - **Missile Barrage**: ปล่อยจรวดหนักช้า (โผล่ใน Wave 10,20,30...)

### หน้า UI & งานตกแต่ง
- **HUD Display**: แสดง HP, เลเวล, ตัวนับ Wave, แถบ EXP แบบเรียลไทม์
- **ช่องสกิล**: ปุ่มสกิล 3 ช่องขนาดใหญ่ (มุมซ้ายล่าง)
- **หน้าจอ Game Over**: โอเวอร์เลย์สไตล์มีปุ่ม "TRY AGAIN" และ "BACK TO MENU"
- **เมนู Pause**: ปิดเกมชั่วคราวแบบเต็มจอพร้อมระบบนำทาง
- **หน้าจอเปลี่ยน Scene**: เอฟเฟกต์ Fade ลื่นไหล
- **รองรับ Gamepad**: ควบคุมด้วยจอยได้ทั้ง D-Pad, แอนะล็อกสติ๊ก และปุ่มต่างๆ

### เอฟเฟกต์ภาพ
- **สัญญาณเตือน Slam**: วงสีเหลือง → วงสีแดงตอนบอสใหญ่กระทืบ
- **เอฟเฟกต์อนุภาค (particle)**: ตะลุมบอน, กระสุนมีอนิเมชัน
- **Feedback ด้วยสี**: ศัตรูเด้ง, สีเปลี่ยนเมื่อโดน
- **สไปรต์อนิเมชัน**: เดิน, ยืนนิ่ง, โจมตี สำหรับตัวละครทุกตัว

## Installation

### ความต้องการ
- Python 3.7 ขึ้นไป
- Kivy 2.0 ขึ้นไป
- Pillow (ไม่จำเป็น แต่ใช้ในกรณี extract sprite sheet)

### การติดตั้ง

```bash
# Clone the repository
git clone https://github.com/psu6810110496/Kivy-Game-Project.git
cd Kivy-Game-Project

# Install dependencies
pip install -r requirements.txt

# Run the game
python main.py
```

## โครงสร้างโปรเจกต์

```
Kivy-Game-Project/
├── main.py                 # Application entry point
├── game/
│   ├── engine.py          # Main game loop and screen manager
│   ├── player.py          # Player character definition
│   ├── player_widget.py   # Player rendering and animation
│   ├── enemy_widget.py    # Enemy rendering and AI
│   ├── projectile_widget.py # Bullet and projectile system
│   ├── skills.py          # Skill system and mechanics
│   └── __init__.py
├── ui/
│   ├── main_menu.py       # Main menu screen
│   ├── char_select.py     # Character selection screen
│   ├── game_over.py       # Game over overlay popup
│   ├── pause.py           # Pause menu popup
│   ├── level_up.py        # Level up selection screen
│   ├── hud.py             # In-game HUD display
│   └── __init__.py
├── assets/                # Game assets
│   ├── enemy/             # Enemy sprites
│   ├── effect/            # Visual effects
│   ├── maps/              # Game map backgrounds
│   ├── Lostman/           # Lostman character sprites
│   ├── Monkey/            # Monkey character sprites
│   ├── PTae/              # PTae character sprites
│   └── Ranger/            # Ranger character sprites
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## วิธีเล่น
1. **เริ่มเกม (Start Game)**: เลือกตัวละครจากหน้าจอเลือกตัวละคร
2. **เอาชีวิตรอดจากคลื่น (Survive Waves)**: สู้ผ่านคลื่นของศัตรูที่มีความยากเพิ่มขึ้นเรื่อยๆ
3. **เลเวลอัพ (Level Up)**: กำจัดศัตรูเพื่อรับ EXP และเพิ่มเลเวล
4. **เลือกสกิล (Choose Skills)**: เมื่อเลเวลอัพ จะมีหน้าต่างให้เลือกระหว่าง 3 สกิลที่สุ่มมาให้
5. **จัดการบอส (Defeat Bosses)**:
  - บอสปกติจะโผล่เมื่อ Wave ลงท้ายด้วยเลข 5 (e.g., 5, 15, 25)
  - Big Boss จะโผล่เมื่อ Wave ลงท้ายด้วยเลข 0 (e.g., 10, 20, 30) และมาพร้อมการโจมตีพิเศษ
6. **เมื่อเกมจบ (Game Over)**: เมื่อ HP เหลือ 0 ให้เลือกว่าจะลองอีกครั้ง (Try Again) หรือกลับไปที่เมนูหลัก (Back to Menu)

### การควบคุม

#### คีย์บอร์ด
- **WASD**: เคลื่อนที่
- **เมาส์**: เล็ง
- **auto**: โจมตี
- **Space**: พุ่งหลบ (Dash)
- **ESC**: หยุดเกม (Pause)
- **F11**: สลับเต็มจอ

#### จอยเกม (Gamepad)
- **D-Pad / แอนะล็อกซ้าย**: เคลื่อนที่
- **แอนะล็อกขวา**: เล็ง
- **ปุ่ม RT**: พุ่งหลบ
- **ปุ่ม Start**: หยุดเกม
- **เลื่อนเมนู**: D-Pad ขึ้น/ลง

## Game Mechanics

### ระบบ Wave
- จำนวนศัตรูเพิ่ม theo สูตร `5 + wave * 2`
- บอสจะโผล่ตามช่วง Wave ที่กำหนด
- ผู้เล่นมีเวลา 1 วินาทีก่อนหน้าจอ Game Over ปรากฏหลังตาย

### ระบบต่อสู้
- ศัตรูเด้งเมื่อโดน
- ผู้เล่นมีเฟรมกันกระสุน (invincibility) หลังถูกตี
- ศัตรูแต่ละประเภทมีพฤติกรรมต่างกัน

### การเก็บเลเวล
- ได้ EXP 10 ต่อศัตรูที่ฆ่า
- เต็ม 100 EXP จะเลเวลอัพ
- เลเวลอัพจะเปิดหน้าเลือกสกิล

### การโจมตีของบอส (Big Boss)
- **Slam** (ทุก 4-6 วินาที): รัศมี 250px, ทำ 60 ดาเมจ, มีวงเตือนก่อนและวงแผ่จริง
- **Swipe** (ทุก 3-5 วินาที): ปล่อยลูกศรเร็ว 700 เร็ว, ดาเมจ 48
- **Missile** (ทุก 4-6 วินาที): ปล่อยระเบิดช้า 300 เร็ว, ดาเมจ 32

- [ ] Sound effects and background music
- [ ] Additional skill types and combinations
- [ ] Leaderboard/high score system
- [ ] Mobile touch controls
- [ ] Difficulty settings
- [ ] Additional character types
- [ ] Boss variations and unique mechanics
## แผนพัฒนาในอนาคต
- [ ] ใส่เสียงและเพลงพื้นหลัง
- [ ] เพิ่มประเภทสกิลและการผสมกัน
- [ ] ระบบบอร์ดคะแนน/Leaderboard
- [ ] รองรับการควบคุมแบบสัมผัสบนมือถือ
- [ ] ตั้งค่าระดับความยาก
- [ ] เพิ่มตัวละครใหม่
- [ ] บอสหลากหลายรูปแบบและกลไกพิเศษ

- [ ] Sound effects and background music
- [ ] Additional skill types and combinations
- [ ] Leaderboard/high score system
- [ ] Mobile touch controls
- [ ] Difficulty settings
- [ ] Additional character types
- [ ] Boss variations and unique mechanics

- **Framework**: Kivy 2.0+
- **Development**: Game Development Team
## เครดิต
- **เฟรมเวิร์ก**: Kivy 2.0+
- **พัฒนาโดย**: ทีมพัฒนาเกม

- **Framework**: Kivy 2.0+
- **Development**: Game Development Team

## ไลเซนส์

โปรเจกต์นี้เป็นซอฟต์แวร์โอเพ่นซอร์ส ภายใต้สัญญาอนุญาต **MIT License**