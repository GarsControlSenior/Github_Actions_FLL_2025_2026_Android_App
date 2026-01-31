from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

from plyer import permission

# Simulierter BLE-Heading (später echte Werte vom Arduino)
import random

class CompassWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0, 0, 0.6, 1)  # Blau
            self.bg = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self.update_bg, pos=self.update_bg)

        # Pfeil
        with self.canvas:
            Color(1, 1, 1)
            self.arrow = Line(points=[0,0,0,0], width=4)

        self.heading = 0
        Clock.schedule_interval(self.update_arrow, 0.1)

        # Gradzahl Label
        self.label = Label(text="0°", font_size="40sp", color=(1,1,1,1))
        self.add_widget(self.label)
        self.bind(size=self.update_label, pos=self.update_label)

    def update_bg(self, *args):
        self.bg.size = self.size
        self.bg.pos = self.pos

    def update_label(self, *args):
        self.label.center = (self.center_x, self.y + 50)

    def update_arrow(self, dt):
        cx, cy = self.center
        length = min(self.width, self.height)*0.4
        import math
        angle_rad = -math.radians(self.heading)
        x_end = cx + length * math.sin(angle_rad)
        y_end = cy + length * math.cos(angle_rad)
        self.arrow.points = [cx, cy, x_end, y_end]
        self.label.text = f"{int(self.heading)}°"

        # Simulierte Heading-Aktualisierung (später BLE)
        self.heading = (self.heading + random.uniform(-1,1)) % 360

class CompassApp(App):
    def build(self):
        self.root_layout = BoxLayout()
        # Roter Startscreen
        with self.root_layout.canvas:
            Color(1,0,0,1)
            self.splash = Rectangle(size=self.root_layout.size, pos=self.root_layout.pos)
        self.root_layout.bind(size=self.update_splash, pos=self.update_splash)

        # Nach kurzer Zeit: Berechtigungen prüfen
        Clock.schedule_once(lambda dt: self.check_permissions(), 1)
        return self.root_layout

    def update_splash(self, *args):
        self.splash.size = self.root_layout.size
        self.splash.pos = self.root_layout.pos

    def check_permissions(self):
        required = ["android.permission.ACCESS_FINE_LOCATION",
                    "android.permission.BLUETOOTH",
                    "android.permission.BLUETOOTH_ADMIN"]

        all_granted = True
        for p in required:
            if not permission.check_permission(p):
                permission.request_permission(p)
                all_granted = False

        if all_granted:
            self.start_compass()
        else:
            # Wenn nicht erlaubt, Button zum Retry
            btn = Button(text="Berechtigungen prüfen", size_hint=(0.6,0.2),
                         pos_hint={'center_x':0.5,'center_y':0.5})
            btn.bind(on_press=lambda x: self.check_permissions())
            self.root_layout.clear_widgets()
            self.root_layout.add_widget(btn)

    def start_compass(self):
        self.root_layout.clear_widgets()
        self.root_layout.add_widget(CompassWidget())

if __name__ == "__main__":
    CompassApp().run()
