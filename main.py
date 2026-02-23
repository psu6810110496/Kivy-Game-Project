from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.core.window import Window

Window.size = (1280, 720)

# ==========================================
# หน้า 1: Main Menu (หน้าเมนูหลัก)
# ==========================================
class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=50, spacing=20)
        
        title = Label(text="VAMPIRE SURVIVORS\n(Kivy Edition)", font_size=40, halign="center")
        btn_start = Button(text="START SURVIVING", font_size=24, size_hint=(1, 0.3))
        btn_quit = Button(text="QUIT GAME", font_size=24, size_hint=(1, 0.3))
        
        btn_start.bind(on_press=self.start_game)
        btn_quit.bind(on_press=self.quit_game)
        
        layout.add_widget(title)
        layout.add_widget(btn_start)
        layout.add_widget(btn_quit)
        self.add_widget(layout)
        
    def start_game(self, instance):
        # เปลี่ยนให้วาร์ปไปหน้า "เลือกตัวละคร" แทนที่จะเข้าเกมทันที
        self.manager.current = 'char_select_screen'
        
    def quit_game(self, instance):
        App.get_running_app().stop()

# ==========================================
# หน้า 1.5: Character Selection (หน้าเลือกตัวละคร) [เพิ่มใหม่!]
# ==========================================
class CharacterSelectScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=40, spacing=20)
        
        # ป้ายหัวข้อ
        lbl_title = Label(text="SELECT YOUR HERO", font_size=36, size_hint=(1, 0.2))
        
        # กล่องแนวนอนสำหรับเรียงปุ่มตัวละคร 3 ตัว
        char_layout = BoxLayout(orientation='horizontal', spacing=20, size_hint=(1, 0.8))
        
        # รายชื่อตัวละคร (เพื่อนสาย UI ไปเปลี่ยนชื่อและแต่งรูปเพิ่มได้)
        characters = [
            "The Survivor\n(Balanced)", 
            "The Scavenger\n(High Speed)", 
            "The Veteran\n(High HP)"
        ]
        
        # สร้างปุ่ม 3 ปุ่มด้วยลูป
        for char_name in characters:
            btn_char = Button(text=char_name, font_size=20)
            btn_char.bind(on_press=self.choose_character)
            char_layout.add_widget(btn_char)
            
        layout.add_widget(lbl_title)
        layout.add_widget(char_layout)
        self.add_widget(layout)
        
    def choose_character(self, instance):
        # โชว์ใน Console ว่าเลือกตัวไหนไป (เดี๋ยวค่อยส่งค่านี้ไปให้หน้า Game)
        print(f"You selected: {instance.text}")
        
        # พอเลือกเสร็จ ก็เข้าหน้าเล่นเกม
        self.manager.current = 'game_screen'

# ==========================================
# หน้า 2: Game Screen (หน้าเล่นเกมหลัก)
# ==========================================
class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        hud_layout = BoxLayout(orientation='vertical')
        
        top_bar = BoxLayout(size_hint=(1, 0.1))
        self.exp_bar = ProgressBar(max=100, value=0)
        self.lbl_level = Label(text="LV: 1", size_hint=(0.2, 1))
        top_bar.add_widget(self.lbl_level)
        top_bar.add_widget(self.exp_bar)
        
        mid_space = Label(text="[ Game Area ]\n(เดี๋ยววาดตัวละครตรงนี้)", halign="center")
        
        btn_test_lvlup = Button(text="[TEST] Add EXP", size_hint=(1, 0.1))
        btn_test_lvlup.bind(on_press=self.test_add_exp)
        
        hud_layout.add_widget(top_bar)
        hud_layout.add_widget(mid_space)
        hud_layout.add_widget(btn_test_lvlup)
        
        self.add_widget(hud_layout)

    def test_add_exp(self, instance):
        self.exp_bar.value += 35
        if self.exp_bar.value >= 100:
            self.exp_bar.value = 0 
            self.manager.current = 'level_up_screen'

# ==========================================
# หน้า 3: Level Up Screen (หน้าอัปเกรด)
# ==========================================
class LevelUpScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=20)
        
        lbl_title = Label(text="LEVEL UP!\nChoose an Upgrade", font_size=30, size_hint=(1, 0.2))
        
        cards_layout = GridLayout(cols=3, spacing=10, size_hint=(1, 0.6))
        
        for i in range(1, 4):
            btn_skill = Button(text=f"Skill Option {i}\n(Click to select)")
            btn_skill.bind(on_press=self.select_skill)
            cards_layout.add_widget(btn_skill)
            
        layout.add_widget(lbl_title)
        layout.add_widget(cards_layout)
        self.add_widget(layout)
        
    def select_skill(self, instance):
        print(f"Player selected: {instance.text}")
        self.manager.current = 'game_screen'

# ==========================================
# ตัวจัดการแอปพลิเคชัน
# ==========================================
class VampireApp(App):
    def build(self):
        sm = ScreenManager()
        # ต้องแอดหน้า CharacterSelectScreen ลงไปในระบบด้วย
        sm.add_widget(MainMenuScreen(name='main_menu'))
        sm.add_widget(CharacterSelectScreen(name='char_select_screen'))
        sm.add_widget(GameScreen(name='game_screen'))
        sm.add_widget(LevelUpScreen(name='level_up_screen'))
        return sm

if __name__ == '__main__':
    VampireApp().run()