from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.app import App
from game.score_manager import ScoreManager

class LeaderboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        main_layout = BoxLayout(orientation="vertical", padding=40, spacing=20)
        
        title = Label(text="LEADERBOARD", font_size=50, bold=True, color=(1, 0.8, 0.2, 1), size_hint_y=None, height=80)
        main_layout.add_widget(title)
        
        # Header
        header_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height=40)
        header_layout.add_widget(Label(text="Rank", bold=True, size_hint_x=0.1))
        header_layout.add_widget(Label(text="Name", bold=True, size_hint_x=0.25))
        header_layout.add_widget(Label(text="Char", bold=True, size_hint_x=0.15))
        header_layout.add_widget(Label(text="Time", bold=True, size_hint_x=0.15))
        header_layout.add_widget(Label(text="Lv / Kills", bold=True, size_hint_x=0.15))
        header_layout.add_widget(Label(text="Score", bold=True, size_hint_x=0.2))
        main_layout.add_widget(header_layout)
        
        # Scrollable list
        self.scroll_view = ScrollView(size_hint=(1, 1))
        self.list_layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=10)
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        self.scroll_view.add_widget(self.list_layout)
        
        main_layout.add_widget(self.scroll_view)
        
        # Back Button
        back_btn = Button(text="BACK TO MENU", font_size=30, size_hint=(None, None), size=(300, 60), pos_hint={'center_x': 0.5})
        back_btn.bind(on_press=self.go_back)
        main_layout.add_widget(back_btn)
        
        self.add_widget(main_layout)

    def on_enter(self):
        """Update the list every time we enter the screen"""
        self.list_layout.clear_widgets()
        scores = ScoreManager.load_scores()
        
        if not scores:
            lbl = Label(text="No records yet.", font_size=30, color=(0.7, 0.7, 0.7, 1), size_hint_y=None, height=50)
            self.list_layout.add_widget(lbl)
            return

        for idx, entry in enumerate(scores):
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=40)
            
            # Rank color
            if idx == 0:
                color = (1, 0.84, 0, 1) # Gold
            elif idx == 1:
                color = (0.75, 0.75, 0.75, 1) # Silver
            elif idx == 2:
                color = (0.8, 0.5, 0.2, 1) # Bronze
            else:
                color = (1, 1, 1, 1)
                
            row.add_widget(Label(text=f"#{idx+1}", color=color, size_hint_x=0.1))
            row.add_widget(Label(text=str(entry.get("name", "???")), color=color, size_hint_x=0.25))
            row.add_widget(Label(text=str(entry.get("character", "?")), color=color, size_hint_x=0.15))
            row.add_widget(Label(text=str(entry.get("time_survived", "00:00")), color=color, size_hint_x=0.15))
            row.add_widget(Label(text=f"{entry.get('level', 1)} / {entry.get('kills', 0)}", color=color, size_hint_x=0.15))
            row.add_widget(Label(text=str(entry.get("score", 0)), color=color, bold=True, size_hint_x=0.2))
            
            self.list_layout.add_widget(row)

    def go_back(self, instance):
        App.get_running_app().root.current = "main_menu"
