# Apocalite - โครงการเกม Kivy

เกมแนว 2D Survival สุดมันส์ โฟกัสการต่อสู้แบบ **fast-paced, action-packed** สร้างด้วยเฟรมเวิร์ก **Kivy** กระโดดสู้กับ Wave ของศัตรู ยำบอส เก็บเลเวล แล้วปลดล็อกสกิลเทพเพื่ออยู่รอดให้ได้นานที่สุด

## Features

### กลไกการเล่นหลัก (Core Gameplay)
- **การเกิดศัตรูแบบเป็น Wave**: ต้องสู้กับคลื่นศัตรูที่มีความยากเพิ่มขึ้นเรื่อยๆ
- **เลือกตัวละครได้**: มีตัวละครให้เลือกหลายแบบ (Lostman, Monkey, PTae)
- **ระบบสกิลไดนามิก**: เมื่อเลเวลอัพจะสุ่มให้เลือกสกิลหรือสถานะเพิ่มค่าพลัง
- **ต่อสู้กับบอส**: บอสธรรมดาจะโผล่ทุก 5 Wave (5, 15, 25...) ส่วน Big Boss ระดับตำนานจะโผล่ทุก 10 Wave (10, 20, 30...)
- **กล้องลื่นไหล**: กล้องจะตามผู้เล่นพร้อม damping ให้ความรู้สึกเหมือนซีเนมาติก พร้อมหน้าจอเลื่อนตามการเคลื่อนที่

### ประเภทของศัตรู
- **Normal**: ศัตรูระยะประชิดธรรมดา ความสมดุล
- **Stalker**: เร็วแต่ HP ต่ำ
- **Ranger**: ยิงไกล พยายามรักษาระยะ
- **Charger / Bomber**: ศัตรูพิเศษที่จะโผล่ใน Wave ที่สูงขึ้น (Wave 2+)
- **Shielder / Sniper**: ศัตรูสวมเกราะและพลซุ่มยิง (Wave 4+)
- **Boss**: ศัตรูตัวใหญ่ HP เยอะ โผล่ใน Wave 5, 15, 25...
- **Big Boss**: บอสระดับตำนานที่มี HP มหาศาลและมาพร้อมสมุน

### หน้า UI & งานตกแต่ง
- **HUD Display**: แสดง HP, เลเวล, ตัวนับ Wave, แถบ EXP และจำนวนศัตรูที่เหลือ
- **หน้าจอเลือกตัวละคร**: แสดงสถานะ (HP, ATK, SPD) ของแต่ละตัวละคร
- **หน้าจอ Level Up**: ให้เลือกการ์ดอัปเกรด 4 ใบ (สกิลใหม่ หรือ เพิ่มสถานะ)
- **เมนู Pause**: พักเกมแบบเต็มจอพร้อมเอฟเฟกต์ Glassmorphism
- **หน้าจอ Game Over**: โอเวอร์เลย์สไตล์ "YOU DIED" พร้อมทางเลือก TRY AGAIN
- **ระบบนำทาง (Navigation)**: รองรับการใช้ เมาส์, คีย์บอร์ด (WASD), และ Gamepad อย่างเต็มรูปแบบ

### การควบคุมและการเข้าถึง
- **Full Gamepad Support**: ควบคุมด้วยจอยได้ทั้งการเคลื่อนที่, การเล็ง และการนำทางในเมนู
- **Full Keyboard Support**: รองรับ **WASD** ทั้งในการเล่นและการเลือกเมนู
- **Mouse Support**: ใช้เล็งทิศทาง (ในเกม) และคลิกเลือก (ในเมนู)

## Installation

### ความต้องการ
- Python 3.7 ขึ้นไป
- Kivy 2.3 ขึ้นไป
- Pillow

### การติดตั้ง

```bash
# Clone the repository
git clone https://github.com/psu6810110496/Kivy-Game-Project.git
cd Kivy-Game-Project

# Install dependencies
pip install -r requirements.txt

# Run the game
python APOCALITE/main.py
```

## โครงสร้างโปรเจกต์

```
APOCALITE/
├── main.py                 # Application entry point
├── game/
│   ├── engine.py          # Main game loop and engine logic
│   ├── player.py          # Player stats and logic
│   ├── enemy_widget.py    # Enemy AI and behaviors
│   ├── projectile_widget.py # Projectiles, Explosions, and EXP orbs
│   ├── wave_manager.py    # Wave spawning and scaling logic
│   ├── skills.py          # Skill definitions and upgrades
│   └── obstacle_widget.py # Environmental obstacles
├── ui/
│   ├── main_menu.py       # Main menu with rain effect
│   ├── char_select.py     # Character selection
│   ├── hud.py             # In-game HUD
│   ├── pause.py           # Pause menu
│   ├── level_up.py        # Level up upgrade cards
│   └── game_over.py       # Game over overlay
└── assets/                # Images, Sprites, and Animations
```

## วิธีเล่น
1. **เริ่มเกม**: เลือกตัวละครที่ชอบ (เลือกได้จาก HP/ATK/SPD ที่ต่างกัน)
2. **เอาชีวิตรอด**: เคลื่อนที่หลบศัตรู ตัวละครจะโจมตีอัตโนมัติ (หรือใช้สกิลตามสถานการณ์)
3. **เก็บ EXP**: เก็บเม็ดพลังสีเขียวที่ดรอปจากศัตรูเพื่อเลเวลอัพ
4. **เลเวลอัพ**: เลือกอัปเกรดสกิล (เพื่อความรุนแรง) หรืออัปเกรด Stat (HP, DMG, SPD) เพื่อความอึด
5. **ปราบความยาก**: ศัตรูจะโหดขึ้นเรื่อยๆ ทุกๆ Wave และจะมีความยากเพิ่มขึ้น (Scaling) ทุก 5 Wave

### การควบคุม (Controls)

#### ต่อสู้ (In-Game)
- **WASD / ลูกศร**: เคลื่อนที่
- **เมาส์**: เล็งทิศทางการยิง
- **Spacebar**: พลุ่งหลบ (Dash)
- **ESC**: หยุดเกม (Pause)
- **F11**: สลับโหมดเต็มจอ

#### เมนู (Menu Navigation)
- **WASD**: เลื่อนตัวเลือก (ขึ้น/ลง/ซ้าย/ขวา)
- **Spacebar / Enter**: ยืนยันการเลือก
- **เมาส์**: คลิกเลือก

#### จอยเกม (Gamepad)
- **Analog ซ้าย / D-Pad**: เคลื่อนที่ / เลื่อนเมนู
- **Analog ขวา**: เล็งทิศทาง
- **ปุ่ม A (Cross)**: เลือกเมนู / ยืนยัน
- **ปุ่ม RT (Trigger)**: พุ่งหลบ
- **ปุ่ม Start / Menu**: หยุดเกม

## แผนที่พัฒนาในอนาคต
- [ ] ใส่ระบบเสียงและเพลงพื้นหลัง (BGM / SFX)
- [ ] เพิ่มระบบผสมสกิล (Skill Synergy)
- [ ] ระบบบันทึกคะแนนสูงสุด (High Score)
- [ ] เพิ่มฉาก (Maps) และอุปสรรคใหม่ๆ
- [ ] ปรับตัวละครใหม่ๆ และสกิลที่เป็นเอกลักษณ์มากขึ้น

## เครดิต
- **พัฒนาโดย**: ทีมพัฒนาเกม (psu6810110496)
- **เฟรมเวิร์ก**: Kivy 2.3
- **กราฟิก**: สไปรต์และแอนิเมชันที่ปรับแต่งมาเพื่อโปรเจกต์นี้โดยเฉพาะ

## ไลเซนส์
โปรเจกต์นี้อยู่ภายใต้สัญญาอนุญาต **MIT License**