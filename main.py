from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line
from kivy.clock import Clock
import asyncio
from bleak import BleakClient, BleakScanner

SERVICE_UUID = "12345678-1234-1234-1234-1234567890ab"
CHAR_UUID = "abcdefab-1234-1234-1234-abcdefabcdef"

class CompassWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0, 0, 0.6, 1)  # Dunkelblauer Hintergrund
            self.bg = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self.update_bg, pos=self.update_bg)

        # Pfeil initial
        with self.canvas:
            Color(1, 1, 1)
            self.arrow = Line(points=[0, 0, 0, 0], width=4)

        self.heading = 0
        Clock.schedule_interval(self.update_arrow, 0.1)

    def update_bg(self, *args):
        self.bg.size = self.size
        self.bg.pos = self.pos

    def update_arrow(self, dt):
        # Pfeil von Mitte nach Norden
        cx, cy = self.center
        length = min(self.width, self.height) * 0.4

        import math
        angle_rad = -math.radians(self.heading)  # Minus = CW
        x_end = cx + length * math.sin(angle_rad)
        y_end = cy + length * math.cos(angle_rad)

        self.arrow.points = [cx, cy, x_end, y_end]

class CompassApp(App):
    def build(self):
        self.widget = CompassWidget()
        Clock.schedule_once(lambda dt: asyncio.ensure_future(self.ble_connect()), 0)
        return self.widget

    async def ble_connect(self):
        # 1️⃣ Scan nach Nano33Compass
        devices = await BleakScanner.discover()
        target = None
        for d in devices:
            if "Nano33Compass" in d.name:
                target = d
                break
        if not target:
            print("Arduino nicht gefunden")
            return

        # 2️⃣ Verbinden
        async with BleakClient(target.address) as client:
            print("Verbunden!")
            while True:
                try:
                    data = await client.read_gatt_char(CHAR_UUID)
                    import struct
                    heading = struct.unpack('f', data)[0]
                    self.widget.heading = heading
                except Exception as e:
                    print("Fehler:", e)
                await asyncio.sleep(0.2)

if __name__ == "__main__":
    CompassApp().run()
