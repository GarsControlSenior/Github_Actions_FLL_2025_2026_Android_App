from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line
from kivy.clock import Clock
import math

class CompassWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0, 0, 0.6, 1)  # Blau
            self.bg = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self.update_bg, pos=self.update_bg)

        with self.canvas:
            Color(1, 1, 1)
            self.arrow = Line(points=[0,0,0,0], width=4)

        self.heading = 0
        Clock.schedule_interval(self.update_arrow, 0.1)

    def update_bg(self, *args):
        self.bg.size = self.size
        self.bg.pos = self.pos

    def update_arrow(self, dt):
        cx, cy = self.center
        length = min(self.width, self.height)*0.4
        angle_rad = -math.radians(self.heading)
        x_end = cx + length*math.sin(angle_rad)
        y_end = cy + length*math.cos(angle_rad)
        self.arrow.points = [cx, cy, x_end, y_end]

        # Simulieren: Pfeil dreht sich langsam
        self.heading = (self.heading + 1) % 360

class CompassApp(App):
    def build(self):
        return CompassWidget()

if __name__ == "__main__":
    CompassApp().run()
