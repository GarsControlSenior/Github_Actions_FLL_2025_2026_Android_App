from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.clock import Clock
from jnius import autoclass, cast
from math import radians

# Android BLE Klassen
BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
BluetoothManager = autoclass('android.bluetooth.BluetoothManager')
PythonActivity = autoclass('org.kivy.android.PythonActivity')
UUID = autoclass('java.util.UUID')

SERVICE_UUID = "0000180C-0000-1000-8000-00805f9b34fb"
CHAR_UUID = "00002A57-0000-1000-8000-00805f9b34fb"

class CompassWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.arrow = Image(source='arrow.png', center=self.center)
        self.add_widget(self.arrow)
        self.heading = 0

    def update_arrow(self, dt):
        self.arrow.angle = self.heading

class CompassApp(App):
    def build(self):
        self.compass = CompassWidget()
        Clock.schedule_interval(self.compass.update_arrow, 0.1)
        Clock.schedule_once(self.setup_ble, 1)
        return self.compass

    def setup_ble(self, dt):
        activity = PythonActivity.mActivity
        service = activity.getSystemService(activity.BLUETOOTH_SERVICE)
        adapter = cast('android.bluetooth.BluetoothManager', service).getAdapter()

        if not adapter.isEnabled():
            adapter.enable()

        # Scan starten (hier stark vereinfacht, für Test)
        print("BLE Scan sollte starten... (Android BLE API nötig)")

        # Hier müsstest du mit pyjnius die Services und Characteristics auslesen
        # und dann self.compass.heading = empfangener Winkel setzen

if __name__ == '__main__':
    CompassApp().run()
