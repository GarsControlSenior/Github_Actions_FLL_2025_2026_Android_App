from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
import math

class CompassScreen(Widget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Hintergrund
        with self.canvas.before:
            Color(0, 0, 0.6, 1)  # Dunkelblau
            self.bg = Rectangle(size=self.size, pos=self.pos)

        self.bind(size=self.update_bg, pos=self.update_bg)

        # Anzeige
        self.label = Label(
            text="NORD: 0°",
            font_size="40sp",
            color=(1, 1, 1, 1),
            center=self.center
        )
        self.add_widget(self.label)

        self.angle = 0
        Clock.schedule_interval(self.update_direction, 0.5)

    def update_bg(self, *args):
        self.bg.size = self.size
        self.bg.pos = self.pos
        self.label.center = self.center

    def update_direction(self, dt):
        # 🔁 SIMULATION (ersetzt später Arduino-Wert)
        self.angle = (self.angle + 10) % 360

        direction = self.get_direction(self.angle)
        self.label.text = f"NORD: {self.angle}°\n{direction}"

    def get_direction(self, angle):
        dirs = ["N", "NO", "O", "SO", "S", "SW", "W", "NW"]
        return dirs[int((angle + 22.5) / 45) % 8]


class MainApp(App):
    def build(self):
        return CompassScreen()


if __name__ == "__main__":
    MainApp().run()
