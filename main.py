from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar

# ==========================================
# หน้า 1: Main Menu (หน้าเมนูหลัก)
# ==========================================
class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=50, spacing=20)
        
        # Widgets: Label 1, Button 2 (รวม 3 Widgets / 2 Callbacks)
        title = Label(text="VAMPIRE SURVIVORS\n(Kivy Edition)", font_size=40, halign="center")
        btn_start = Button(text="START SURVIVING", font_size=24, size_hint=(1, 0.3))
        btn_quit = Button(text="QUIT GAME", font_size=24, size_hint=(1, 0.3))
        
        # ผูก Callbacks
        btn_start.bind(on_press=self.start_game)
        btn_quit.bind(on_press=self.quit_game)
        
        layout.add_widget(title)
        layout.add_widget(btn_start)
        layout.add_widget(btn_quit)
        self.add_widget(layout)
        
    def start_game(self, instance):
        # สั่งเปลี่ยนหน้าไปที่หน้าเล่นเกม
        self.manager.current = 'game_screen'
        
    def quit_game(self, instance):
        App.get_running_app().stop()

# ==========================================
# หน้า 2: Game Screen (หน้าเล่นเกมหลัก)
# ==========================================
class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # ใช้ FloatLayout เพื่อให้วาง UI ซ้อนทับบนตัวเกมได้
        # ตรงนี้เดี๋ยวเราจะเอาไว้ใช้วาดตัวละครกับมอนสเตอร์ (Canvas) ทีหลัง
        
        # --- สร้าง HUD (UI ตอนเล่น) ---
        hud_layout = BoxLayout(orientation='vertical')
        
        # หลอด EXP ด้านบน (Widgets: ProgressBar 1, Label 1)
        top_bar = BoxLayout(size_hint=(1, 0.1))
        self.exp_bar = ProgressBar(max=100, value=0)
        self.lbl_level = Label(text="LV: 1", size_hint=(0.2, 1))
        top_bar.add_widget(self.lbl_level)
        top_bar.add_widget(self.exp_bar)
        
        # พื้นที่ตรงกลางปล่อยว่างไว้รันเกมเพลย์
        mid_space = Label(text="[ Game Area ]\n(เดี๋ยววาดตัวละครตรงนี้)", halign="center")
        
        # ปุ่ม Test Level Up (ปุ่มจำลอง เดี๋ยวกดแล้วจะเด้งไปหน้าอัปสกิล)
        btn_test_lvlup = Button(text="[TEST] Add EXP", size_hint=(1, 0.1))
        btn_test_lvlup.bind(on_press=self.test_add_exp)
        
        hud_layout.add_widget(top_bar)
        hud_layout.add_widget(mid_space)
        hud_layout.add_widget(btn_test_lvlup)
        
        self.add_widget(hud_layout)

    def test_add_exp(self, instance):
        # จำลองการเก็บ EXP พอเต็ม 100 ให้เด้งไปหน้า Level Up
        self.exp_bar.value += 35
        if self.exp_bar.value >= 100:
            self.exp_bar.value = 0 # รีเซ็ตหลอด
            self.manager.current = 'level_up_screen'

# ==========================================
# หน้า 3: Level Up Screen (บ่อทองคำปั๊ม Widgets!)
# ==========================================
class LevelUpScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=20)
        
        lbl_title = Label(text="LEVEL UP!\nChoose an Upgrade", font_size=30, size_hint=(1, 0.2))
        
        # สร้าง GridLayout เพื่อวางการ์ดสกิล 3 ใบ
        cards_layout = GridLayout(cols=3, spacing=10, size_hint=(1, 0.6))
        
        # จำลองปุ่มสกิล 3 ปุ่ม (Widgets: Button 3 / Callbacks 3)
        # (เดี๋ยวเพื่อนคนที่ทำ UI ค่อยมาแต่งให้มันสวย มีรูปภาพ มีคำอธิบาย)
        for i in range(1, 4):
            btn_skill = Button(text=f"Skill Option {i}\n(Click to select)")
            btn_skill.bind(on_press=self.select_skill)
            cards_layout.add_widget(btn_skill)
            
        layout.add_widget(lbl_title)
        layout.add_widget(cards_layout)
        self.add_widget(layout)
        
    def select_skill(self, instance):
        print(f"Player selected: {instance.text}")
        # เลือกเสร็จ กลับไปหน้าเกมต่อ
        self.manager.current = 'game_screen'

# ==========================================
# ตัวจัดการแอปพลิเคชัน
# ==========================================
class VampireApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainMenuScreen(name='main_menu'))
        sm.add_widget(GameScreen(name='game_screen'))
        sm.add_widget(LevelUpScreen(name='level_up_screen'))
        return sm

if __name__ == '__main__':
    VampireApp().run()