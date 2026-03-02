from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Rectangle, Color
from kivy.core.window import Window
from kivy.clock import Clock
import random

# --- คลาสเอฟเฟกต์ฝนตก ---
class RainEffect(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.drops = []
        self.num_drops = 100 
        
        with self.canvas:
            Color(0.6, 0.6, 0.6, 0.4) 
            for _ in range(self.num_drops):
                # สร้างเม็ดฝนแนวตั้ง
                rect = Rectangle(
                    # สุ่ม X เผื่อไปทางซ้าย เพราะฝนวิ่งเฉียงไปทางขวา
                    pos=(random.uniform(-Window.width * 0.5, Window.width), 
                         random.uniform(0, Window.height)), 
                    size=(2, random.uniform(10, 25))
                )
                
                drop = {
                    'rect': rect,
                    'speed': random.uniform(7, 15)
                }
                self.drops.append(drop)
        
        Clock.schedule_interval(self.update_rain, 1/60.0)

    def update_rain(self, dt):
        for drop in self.drops:
            x, y = drop['rect'].pos
            
            # ปรับให้ตกเฉียงขวา: y ลดลง (ลง), x เพิ่มขึ้น (ไปขวา)
            y -= drop['speed']
            x += drop['speed'] * 0.4  # ปรับตัวคูณเพื่อเปลี่ยนความชัน
            
            # ตรวจสอบขอบล่าง และขอบขวา
            if y < -30 or x > Window.width:
                y = Window.height + random.uniform(10, 100)
                # สุ่มเกิดใหม่จากทางซ้าย เพื่อให้เฉียงเข้าหาจอ
                x = random.uniform(-Window.width * 0.5, Window.width)
                
            drop['rect'].pos = (x, y)

# --- คลาสหน้าจอเมนูหลัก ---
class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        main_layout = FloatLayout()

        # 1. จัดการรูปพื้นหลังให้เต็มจอเสมอ
        with main_layout.canvas.before:
            Color(1, 1, 1, 1)
            self.bg_rect = Rectangle(
                source='assets/Menu/MenuTest.png', 
                pos=(0, 0),
                size=self.size
            )
        
        # ผูกขนาดของ Rectangle เข้ากับ main_layout โดยตรง
        main_layout.bind(size=self._update_bg, pos=self._update_bg)
        
        # 2. เพิ่มเอฟเฟกต์ฝน
        self.rain = RainEffect()
        main_layout.add_widget(self.rain)

        # 3. จัดวางเมนู
        menu_group = BoxLayout(
            orientation='vertical', spacing=45,
            size_hint=(None, None), size=(800, 600), 
            pos_hint={'x': 0.1, 'top': 0.9} 
        )

        title_label = Label(
            text="VAMPIRE SURVIVORS", font_size=70, bold=True, 
            halign='left', valign='middle', size_hint=(1, None), height=150
        )
        title_label.bind(size=title_label.setter('text_size'))

        # 4. จัดวางปุ่มให้อยู่ทางซ้ายภายในเมนู
        btn_layout = BoxLayout(orientation='vertical', spacing=20, size_hint=(None, None), size=(400, 200))
        
        btn_start = Button(
            text="START SURVIVING", font_size=26, 
            size_hint=(None, None), size=(350, 80),
            background_color=(1,1,1,0.8)
        )
        btn_quit = Button(
            text="QUIT GAME", font_size=26, 
            size_hint=(None, None), size=(350, 80),
            background_color=(1,1,1,0.8)
        )

        btn_start.bind(on_press=lambda x: self.change_screen('char_select_screen'))
        btn_quit.bind(on_press=lambda x: App.get_running_app().stop())

        btn_layout.add_widget(btn_start)
        btn_layout.add_widget(btn_quit)
        
        menu_group.add_widget(title_label)
        menu_group.add_widget(btn_layout) 
        
        main_layout.add_widget(menu_group)
        self.add_widget(main_layout)
        

    # 5. ฟังก์ชันอัปเดตขนาดพื้นหลัง
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def change_screen(self, screen_name):
        self.manager.current = screen_name