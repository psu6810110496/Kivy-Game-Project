from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup  # เพิ่ม Import Popup
from kivy.core.window import Window
from kivy.graphics import Rectangle, Color, PushMatrix, PopMatrix, Translate
from kivy.clock import Clock

Window.size = (1280, 720)

# ==========================================
# 1. Data Model
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
# 2. Player Sprite Widget
# ==========================================
class PlayerWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(0, 0.5, 1, 1) 
            self.rect = Rectangle(pos=(2500, 2500), size=(50, 50))

    def update_pos(self, new_pos):
        self.rect.pos = new_pos

# ==========================================
# 3. Popup เลเวลอัพ
# ==========================================
class LevelUpPopup(Popup):
    def __init__(self, game_screen, **kwargs):
        super().__init__(**kwargs)
        self.game_screen = game_screen  # เก็บอ้างอิงถึงหน้าจอเกมเพื่อสั่งทำงานต่อ
        self.title = "LEVEL UP! Choose your Upgrade:"
        self.title_size = 24
        self.size_hint = (0.6, 0.5)
        self.auto_dismiss = False # บังคับให้ผู้เล่นต้องกดเลือก ห้ามกดคลิกทิ้งนอกกรอบ
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        cards_layout = GridLayout(cols=3, spacing=15)
        
        upgrades = ["+ Damage", "+ Max HP", "+ Speed"]
        for upg in upgrades:
            btn = Button(text=upg, font_size=20)
            btn.bind(on_press=self.apply_upgrade)
            cards_layout.add_widget(btn)
            
        layout.add_widget(cards_layout)
        self.content = layout

    def apply_upgrade(self, instance):
        player = App.get_running_app().current_player
        if player:
            if "+ Damage" in instance.text: player.damage += 5
            elif "+ Max HP" in instance.text: player.hp += 20
            elif "+ Speed" in instance.text: player.speed += 2
        
        # คืนสถานะเกมและปิด Popup
        self.game_screen.resume_game()
        self.dismiss()

# ==========================================
# 4. UI Screens
# ==========================================
class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        main_layout = FloatLayout()
        menu_group = BoxLayout(
            orientation='vertical', spacing=45,
            size_hint=(None, None), size=(800, 600), 
            pos_hint={'x': 0.1, 'top': 0.9} 
        )

        title_label = Label(text="VAMPIRE SURVIVORS", font_size=70, bold=True, halign='left', valign='middle', size_hint=(1, None), height=150)
        title_label.bind(size=title_label.setter('text_size'))

        btn_start = Button(text="START SURVIVING", font_size=26, size_hint=(0.4, None), height=80, pos_hint={'center_x': 0.33})
        btn_quit = Button(text="QUIT GAME", font_size=26, size_hint=(0.4, None), height=80, pos_hint={'center_x': 0.33})

        btn_start.bind(on_press=lambda x: self.change_screen('char_select_screen'))
        btn_quit.bind(on_press=lambda x: App.get_running_app().stop())

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
            btn.bind(on_press=lambda instance, s=stats: self.select_hero(s))
            char_layout.add_widget(btn)
        layout.add_widget(char_layout)
        self.add_widget(layout)
        
    def select_hero(self, stats_obj):
        App.get_running_app().current_player = stats_obj
        self.manager.current = 'game_screen'

class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.keys_pressed = set()
        self.player_pos = [2500, 2500]
        self.player_stats = None 
        self.is_paused = False  # เพิ่มสถานะการหยุดเกม
        
        Window.bind(on_key_down=self._on_keydown)
        Window.bind(on_key_up=self._on_keyup)

        self.root_layout = FloatLayout()
        
        # --- กล้องและโลก ---
        self.world_layout = FloatLayout(size_hint=(None, None), size=(5000, 5000)) 
        
        with self.world_layout.canvas.before:
            PushMatrix()
            self.camera = Translate(0, 0)
            Color(0.2, 0.2, 0.2, 1)
            for i in range(0, 5001, 100):
                Rectangle(pos=(0, i), size=(5000, 1)) 
                Rectangle(pos=(i, 0), size=(1, 5000)) 

        with self.world_layout.canvas.after:
            PopMatrix()
            
        self.root_layout.add_widget(self.world_layout)
        self.player_widget = PlayerWidget()
        self.world_layout.add_widget(self.player_widget)

        # --- HUD ---
        self.hud_container = FloatLayout(size_hint=(1, 1))
        top_bar = BoxLayout(size_hint=(1, 0.1), pos_hint={'top': 1}, padding=10)
        self.lbl_level = Label(text="LV: 1", size_hint=(0.2, 1), bold=True)
        self.exp_bar = ProgressBar(max=100, value=0)
        top_bar.add_widget(self.lbl_level)
        top_bar.add_widget(self.exp_bar)
        
        self.hud_container.add_widget(top_bar)
        
        btn_test = Button(text="[TEST] EXP", size_hint=(None, None), size=(100, 40), pos_hint={'right': 1, 'y': 0})
        btn_test.bind(on_press=self.gain_exp)
        self.hud_container.add_widget(btn_test)

        self.root_layout.add_widget(self.hud_container)
        self.add_widget(self.root_layout)

    def on_enter(self):
        self.player_stats = App.get_running_app().current_player
        if self.player_stats:
            self.update_ui()
            Clock.schedule_interval(self.update_frame, 1.0/60.0)

    def on_leave(self):
        Clock.unschedule(self.update_frame)

    def update_ui(self):
        if self.player_stats:
            self.lbl_level.text = f"LV: {self.player_stats.level}"
            self.exp_bar.value = self.player_stats.exp

    def resume_game(self):
        self.is_paused = False
        self.keys_pressed.clear() # เคลียร์ปุ่มค้างเพื่อป้องกันตัวละครวิ่งเอง

    def update_frame(self, dt):
        # ถ้าไม่มีข้อมูลผู้เล่น หรือ "เกมหยุดอยู่" ห้ามคำนวณการเดิน
        if not self.player_stats or self.is_paused:
            return

        step = self.player_stats.speed
        if 'w' in self.keys_pressed: self.player_pos[1] += step
        if 's' in self.keys_pressed: self.player_pos[1] -= step
        if 'a' in self.keys_pressed: self.player_pos[0] -= step
        if 'd' in self.keys_pressed: self.player_pos[0] += step

        self.player_widget.update_pos(self.player_pos)
        self.camera.x = (Window.width / 2) - self.player_pos[0] - 25
        self.camera.y = (Window.height / 2) - self.player_pos[1] - 25

    def gain_exp(self, instance):
        if self.player_stats:
            self.player_stats.exp += 35
            if self.player_stats.exp >= 100:
                self.player_stats.level += 1
                self.player_stats.exp -= 100 # หักออก 100 เผื่อมีเศษ EXP ล้น
                
                # สั่งหยุดเวลาในเกม และเรียก Popup เลเวลอัพ!
                self.is_paused = True
                LevelUpPopup(game_screen=self).open()
                
            self.update_ui()

    def _on_keydown(self, window, key, scancode, codepoint, modifiers):
        if codepoint: self.keys_pressed.add(codepoint.lower())

    def _on_keyup(self, window, key, scancode):
        try:
            key_char = chr(key).lower()
            if key_char in self.keys_pressed:
                self.keys_pressed.remove(key_char)
        except: 
            pass

# ==========================================
# 5. Application Controller
# ==========================================
class VampireApp(App):
    def build(self):
        self.current_player = None 
        sm = ScreenManager()
        sm.add_widget(MainMenuScreen(name='main_menu'))
        sm.add_widget(CharacterSelectScreen(name='char_select_screen'))
        sm.add_widget(GameScreen(name='game_screen'))
        # ลบ LevelUpScreen ออกไป เพราะเราใช้ Popup แทนแล้ว
        return sm

if __name__ == '__main__':
    VampireApp().run()