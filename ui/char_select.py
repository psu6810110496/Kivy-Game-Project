from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from game.player import PlayerStats
import kivy.app

class CharacterSelectScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.char_data = {
            "PTae": PlayerStats(
                name="PTae", 
                hp=100, 
                speed=5.0, 
                damage=10, 
                idle_frames=['assets/PTae/PTIdle/PTTG1.png', 'assets/PTae/PTIdle/PTTG2.png'],
                walk_frames=['assets/PTae/PTPushUp/PTaeTester1.png', 'assets/PTae/PTPushUp/PTaeTester2.png', 'assets/PTae/PTPushUp/PTaeTester3.png', 'assets/PTae/PTPushUp/PTaeTester4.png']
            ),
            "Lostman": PlayerStats(
                name="Lostman", 
                hp=80, 
                speed=7.0, 
                damage=15, 
                idle_frames=['assets/Lostman/idle/idleman1.png', 'assets/Lostman/idle/idleman2.png'],
                walk_frames=['assets/Lostman/walk/walk1.png', 'assets/Lostman/walk/walk2.png', 'assets/Lostman/walk/walk3.png', 'assets/Lostman/walk/walk4.png']
            ),
            # --- เพิ่ม Monke เข้ามาตรงนี้ครับ ---
            "Monke": PlayerStats(
                name="Monke",
                hp=90,        # เลือดกลางๆ
                speed=8.0,      # ลิงต้องวิ่งไว!
                damage=12,      # ดาเมจกำลังดี
                idle_frames=['assets/Monkey/IdleM/IdleM01.png', 'assets/Monkey/IdleM/IdleM02.png'],
                walk_frames=['assets/Monkey/WalkM/W01.png', 'assets/Monkey/WalkM/W02.png', 'assets/Monkey/WalkM/W03.png', 'assets/Monkey/WalkM/W04.png']
            )
        }
        
        layout = BoxLayout(orientation='vertical', padding=50)
        layout.add_widget(Label(text="SELECT CHARACTER", font_size=30))
        
        chars = BoxLayout(spacing=20)
        for name, stats in self.char_data.items():
            # แสดงชื่อ เลือด และความเร็ว บนปุ่มให้ผู้เล่นเห็น
            btn = Button(text=f"{name}\nHP: {stats.hp}\nSpeed: {stats.speed}")
            btn.bind(on_press=lambda inst, s=stats: self.select_char(s))
            chars.add_widget(btn)
            
        layout.add_widget(chars)
        self.add_widget(layout)

    def select_char(self, stats):
        # บันทึกตัวละครที่เลือกลงใน App และเปลี่ยนหน้า
        kivy.app.App.get_running_app().current_player = stats
        self.manager.current = 'game_screen'