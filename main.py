from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from jnius import autoclass, cast, PythonJavaClass, java_method

import struct
import math

# Android BLE Klassen
BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
BluetoothManager = autoclass('android.bluetooth.BluetoothManager')
PythonActivity = autoclass('org.kivy.android.PythonActivity')
UUID = autoclass('java.util.UUID')
BluetoothDevice = autoclass('android.bluetooth.BluetoothDevice')
BluetoothGattCallback = autoclass('android.bluetooth.BluetoothGattCallback')

# UUIDs Arduino BLE
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
        angle_rad = -math.radians(self.heading)
        x_end = cx + length * math.sin(angle_rad)
        y_end = cy + length * math.cos(angle_rad)
        self.arrow.points = [cx, cy, x_end, y_end]
        self.label.text = f"{int(self.heading)}°"

class MainApp(App):
    def build(self):
        self.widget = CompassWidget()
        # Starte BLE Scan nach Start
        Clock.schedule_once(lambda dt: self.start_ble(), 1)
        return self.widget

    def start_ble(self):
        # Adapter holen
        activity = PythonActivity.mActivity
        manager = cast('android.bluetooth.BluetoothManager', activity.getSystemService(activity.BLUETOOTH_SERVICE))
        self.adapter = manager.getAdapter()
        if not self.adapter.isEnabled():
            self.adapter.enable()
        print("BLE Adapter aktiv")

        # Scan starten
        self.adapter.startLeScan(self.scan_callback)

    # Callback für Scan
    def scan_callback(self, device, rssi, scanRecord):
        name = device.getName()
        if name and "Nano33Compass" in name:
            print("Arduino gefunden:", name)
            self.adapter.stopLeScan(self.scan_callback)
            self.connect_device(device)

    def connect_device(self, device):
        gatt = device.connectGatt(PythonActivity.mActivity, False, self.GattCallback(self.widget))
        print("Verbindung gestartet")

    class GattCallback(PythonJavaClass):
        __javainterfaces__ = ['android/bluetooth/BluetoothGattCallback']
        def __init__(self, widget):
            super().__init__()
            self.widget = widget

        @java_method('(Landroid/bluetooth/BluetoothGatt;I)V')
        def onServicesDiscovered(self, gatt, status):
            # Hier später Characteristic lesen
            pass

        # Du kannst hier onCharacteristicChanged implementieren, um Heading zu lesen
        # self.widget.heading = heading_from_arduino

if __name__ == "__main__":
    MainApp().run()
