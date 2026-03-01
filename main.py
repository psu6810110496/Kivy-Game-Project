Chap
chappawit
ไม่ระบุ

LowP
LowP — 23/2/2569 13:12
Chap — 23/2/2569 13:12
LowP
LowP — 23/2/2569 13:12
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

GG kivy.txt
6 KB
Chap — 24/2/2569 0:43
class DisplayClock:
    def display_time(self, time):
        print(f" {time.hour:02}:{time.min:02} ")


class Clock:

clock.txt
1 KB
Chap — 24/2/2569 19:52
76561199177525377
stream id
LowP
LowP — 24/2/2569 19:54
Chap — 24/2/2569 20:17
1217259649
LowP
LowP — 25/2/2569 14:04
https://github.com/denisseai/Project-1-Alien-Invasion-Game
GitHub
GitHub - denisseai/Project-1-Alien-Invasion-Game: 2D shooting game ...
2D shooting game in Pygame, which consists of levels of increasing difficulty- Following Python Crash Course, by Eric Matthes - denisseai/Project-1-Alien-Invasion-Game
2D shooting game in Pygame, which consists of levels of increasing difficulty- Following Python Crash Course, by Eric Matthes - denisseai/Project-1-Alien-Invasion-Game
Chap — 25/2/2569 14:11
https://github.com/artemshchirov/pyzelda-rpg.git
GitHub
GitHub - artemshchirov/pyzelda-rpg: ⚔ Tiled Zelda style game writ...
⚔ Tiled Zelda style game written in Python and Pygame. - artemshchirov/pyzelda-rpg
⚔ Tiled Zelda style game written in Python and Pygame. - artemshchirov/pyzelda-rpg
Chap — 22:21
ประเภทไฟล์ที่แนบ: unknown
พรี่เต2.aseprite
4.49 KB
LowP
LowP — 23:14
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

message.txt
7 KB
LowP
LowP — 23:50
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

message.txt
9 KB
﻿
LowP
LowP
absolutly01not
 
 
 
 
Want to know how it's like to hug
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.core.window import Window
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.floatlayout import FloatLayout

Window.size = (1280, 720)

# ==========================================
# 1. Data Model (ตัวอย่างคลาสข้อมูลตัวละคร)
# ==========================================
class PlayerStats:
    def __init__(self, name, hp, speed, damage):
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.speed = speed
        self.damage = damage
        self.level = 1
        self.exp = 0

# ==========================================
# 2. UI Screens (View Layers)
# ==========================================

class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        main_layout = FloatLayout()

        # ปรับความกว้าง (width) ของ menu_group เพิ่มขึ้นเป็น 600 
        # เพื่อให้พอดีกับชื่อเกมที่ยาวขึ้นในบรรทัดเดียว
        menu_group = BoxLayout(
            orientation='vertical',
            spacing=30,
            size_hint=(None, None),
            size=(600, 450), 
            pos_hint={'x': 0.1, 'top': 0.85}
        )

        # 1. Title (Single Line)
        title_label = Label(
            text="VAMPIRE SURVIVORS", # เอา \n ออกแล้ว
            font_size=60,            # ปรับขนาดใหญ่ขึ้นได้เพราะพื้นที่แนวนอนเหลือเยอะ
            bold=True,
            halign='left',
            valign='middle',
            color=(1, 0.2, 0.2, 1),
            size_hint=(1, None),
            height=100
        )
        title_label.bind(size=title_label.setter('text_size'))

        # 2. ปุ่ม Start (ปรับความกว้างให้สั้นกว่า Title เพื่อความสวยงาม)
        btn_start = Button(
            text="START SURVIVING",
            font_size=24,
            size_hint=(0.6, None),   # 0.6 คือกว้าง 60% ของ menu_group
            height=70,
            background_normal='',
            background_color=(0.1, 0.6, 0.2, 1)
        )
        
        # 3. ปุ่ม Quit
        btn_quit = Button(
            text="QUIT GAME",
            font_size=24,
            size_hint=(0.6, None),
            height=70,
            background_normal='',
            background_color=(0.6, 0.1, 0.1, 1)
        )

        btn_start.bind(on_press=lambda x: self.change_screen('char_select_screen'))
        btn_quit.bind(on_press=lambda x: App.get_running_app().stop())

        # เพิ่มลง Layout
        menu_group.add_widget(title_label)
        menu_group.add_widget(btn_start)
        menu_group.add_widget(btn_quit)

        main_layout.add_widget(menu_group)
        self.add_widget(main_layout)

    def change_screen(self, screen_name):
        self.manager.current = screen_name

class CharacterSelectScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # ข้อมูลตัวละคร (จำลอง Database ย่อมๆ)
        self.char_data = {
            "Survivor": PlayerStats("The Survivor", 100, 5, 10),
            "Scavenger": PlayerStats("The Scavenger", 70, 10, 5),
            "Veteran": PlayerStats("The Veteran", 200, 2, 15)
        }
        self.setup_ui()

    def setup_ui(self):
        layout = BoxLayout(orientation='vertical', padding=40, spacing=20)
        layout.add_widget(Label(text="SELECT YOUR HERO", font_size=36, size_hint=(1, 0.2)))
        
        char_layout = BoxLayout(orientation='horizontal', spacing=20, size_hint=(1, 0.8))
        
        for name, stats in self.char_data.items():
            btn = Button(text=f"{stats.name}\nHP: {stats.hp}\nSpeed: {stats.speed}")
            # ส่ง object stats เข้าไปใน function เมื่อกดปุ่ม
            btn.bind(on_press=lambda instance, s=stats: self.select_hero(s))
            char_layout.add_widget(btn)
            
        layout.add_widget(char_layout)
        self.add_widget(layout)
        
    def select_hero(self, stats_obj):
        # บันทึกตัวละครที่เลือกลงใน App (Global Storage ของแอปนี้)
        App.get_running_app().current_player = stats_obj
        self.manager.current = 'game_screen'

class GameScreen(Screen):
    def on_enter(self):
        # ดึงข้อมูลตัวละครที่เลือกมาจาก App
        self.player = App.get_running_app().current_player
        self.update_ui()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')
        
        # HUD Section
        self.top_bar = BoxLayout(size_hint=(1, 0.1))
        self.lbl_level = Label(text="LV: 1", size_hint=(0.2, 1))
        self.exp_bar = ProgressBar(max=100, value=0)
        self.top_bar.add_widget(self.lbl_level)
        self.top_bar.add_widget(self.exp_bar)
        
        # Game Display Section
        self.display_label = Label(text="Loading...", halign="center")
        
        btn_test_exp = Button(text="[TEST] Kill Enemy (+35 EXP)", size_hint=(1, 0.1))
        btn_test_exp.bind(on_press=self.gain_exp)
        
        self.layout.add_widget(self.top_bar)
        self.layout.add_widget(self.display_label)
        self.layout.add_widget(btn_test_exp)
        self.add_widget(self.layout)

    def update_ui(self):
        self.display_label.text = f"Hero: {self.player.name}\nHP: {self.player.hp}\nDamage: {self.player.damage}"
        self.lbl_level.text = f"LV: {self.player.level}"

    def gain_exp(self, instance):
        self.player.exp += 35
        self.exp_bar.value = self.player.exp
        
        if self.player.exp >= 100:
            self.player.level += 1
            self.player.exp = 0
            self.exp_bar.value = 0
            self.manager.current = 'level_up_screen'

class LevelUpScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=20)
        layout.add_widget(Label(text="LEVEL UP!", font_size=30, size_hint=(1, 0.2)))
        
        self.cards_layout = GridLayout(cols=3, spacing=10, size_hint=(1, 0.6))
        
        # รายการอัปเกรด
        upgrades = ["+ Damage", "+ Max HP", "+ Speed"]
        for upg in upgrades:
            btn = Button(text=upg)
            btn.bind(on_press=self.apply_upgrade)
            self.cards_layout.add_widget(btn)
            
        layout.add_widget(self.cards_layout)
        self.add_widget(layout)
        
    def apply_upgrade(self, instance):
        player = App.get_running_app().current_player
        if "+ Damage" in instance.text: player.damage += 5
        elif "+ Max HP" in instance.text: player.hp += 20
        elif "+ Speed" in instance.text: player.speed += 2
        
        self.manager.current = 'game_screen'

# ==========================================
# 3. Application Controller
# ==========================================
class VampireApp(App):
    def build(self):
        # สร้างตัวแปรไว้เก็บ Player ข้ามหน้าจอ
        self.current_player = None 
        
        sm = ScreenManager()
        sm.add_widget(MainMenuScreen(name='main_menu'))
        sm.add_widget(CharacterSelectScreen(name='char_select_screen'))
        sm.add_widget(GameScreen(name='game_screen'))
        sm.add_widget(LevelUpScreen(name='level_up_screen'))
        return sm

if __name__ == '__main__':
    VampireApp().run()
