from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.button import Button
from kivy.clock import Clock

class HUD(FloatLayout):
    def __init__(self, game_screen, **kwargs):
        super().__init__(**kwargs)
        self.game_screen = game_screen
        top_ui = BoxLayout(size_hint=(0.8, 0.05), pos_hint={'center_x': 0.5, 'top': 0.98}, spacing=10)
        self.lbl_level = Label(text="LV: 1", size_hint=(0.1, 1), bold=True)
        self.exp_bar = ProgressBar(max=100, value=0)
        top_ui.add_widget(self.lbl_level)
        top_ui.add_widget(self.exp_bar)
        self.add_widget(top_ui)
        
        btn_pause = Button(text="||", size_hint=(None, None), size=(50, 50), pos_hint={'right': 0.98, 'top': 0.98})
        btn_pause.bind(on_press=self.game_screen.pause_game)
        self.add_widget(btn_pause)

    def update_ui(self, stats):
        self.lbl_level.text = f"LV: {stats.level}"
        self.exp_bar.value = stats.exp

class CountdownOverlay(Label):
    def __init__(self, callback, **kwargs):
        super().__init__(**kwargs)
        self.callback = callback
        self.count = 3
        self.text = "3"
        self.font_size = 200
        self.color = (1, 0.8, 0, 1)
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        Clock.schedule_interval(self.update_countdown, 1)

    def update_countdown(self, dt):
        self.count -= 1
        if self.count > 0: self.text = str(self.count)
        elif self.count == 0: self.text = "SURVIVE!"; self.color = (1, 0.2, 0.2, 1)
        else:
            self.callback()
            self.parent.remove_widget(self)
            return False