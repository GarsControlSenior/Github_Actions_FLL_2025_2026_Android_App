from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line
from kivy.clock import Clock
from kivy.uix.label import Label

from jnius import autoclass, PythonJavaClass, java_method

# Android BLE Klassen
BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
BluetoothManager = autoclass('android.bluetooth.BluetoothManager')
PythonActivity = autoclass('org.kivy.android.PythonActivity')
UUID = autoclass('java.util.UUID')

# UUIDs Arduino
SERVICE_UUID = "12345678-1234-1234-1234-1234567890ab"
CHAR_UUID = "abcdefab-1234-1234-1234-abcdefabcdef"

class CompassWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0,0,0.6,1)
            self.bg = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self.update_bg, pos=self.update_bg)

        with self.canvas:
            Color(1,1,1)
            self.arrow = Line(points=[0,0,0,0], width=4)

        self.label = Label(text="0°", font_size="40sp", color=(1,1,1,1))
        self.add_widget(self.label)
        self.bind(size=self.update_label, pos=self.update_label)

        self.heading = 0
        Clock.schedule_interval(self.update_arrow, 0.1)

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

class MainApp(App):
    def build(self):
        self.widget = CompassWidget()
        # Nach App Start BLE Verbindung starten
        Clock.schedule_once(lambda dt: self.start_ble(), 1)
        return self.widget

    def start_ble(self):
        # BLE Verbindung hier implementieren
        # 1. Adapter holen
        activity = PythonActivity.mActivity
        context = activity.getSystemService(activity.BLUETOOTH_SERVICE)
        adapter = context.getAdapter()
        if not adapter.isEnabled():
            adapter.enable()
        print("BLE Adapter aktiv")

        # ⚠ Hier müsstest du mit Java BLE API den Arduino finden,
        # verbinden und Characteristic lesen.
        # Python-only auf Android: pyjnius -> BluetoothGatt
        # Für Live-Demo: wir simulieren weiter
        Clock.schedule_interval(lambda dt: self.simulate_ble(), 0.2)

    def simulate_ble(self):
        # ⚠ Später hier echte Heading-Werte vom Arduino setzen
        import random
        self.widget.heading = (self.widget.heading + random.uniform(-1,1)) % 360

if __name__ == "__main__":
    MainApp().run()
