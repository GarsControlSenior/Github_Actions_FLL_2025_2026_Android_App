from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.graphics import Line, Color, PushMatrix, PopMatrix, Rotate
from kivy.uix.label import Label
from jnius import autoclass, cast, PythonJavaClass, java_method
from math import radians

# Android BLE Klassen
BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
BluetoothManager = autoclass('android.bluetooth.BluetoothManager')
PythonActivity = autoclass('org.kivy.android.PythonActivity')
BluetoothGattCharacteristic = autoclass('android.bluetooth.BluetoothGattCharacteristic')
BluetoothGatt = autoclass('android.bluetooth.BluetoothGatt')
UUID = autoclass('java.util.UUID')

SERVICE_UUID = "0000180C-0000-1000-8000-00805f9b34fb"
CHAR_UUID = "00002A57-0000-1000-8000-00805f9b34fb"

class CompassWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.heading = 0  # aktueller Winkel
        with self.canvas:
            Color(1, 0, 0)
            PushMatrix()
            self.rot = Rotate(angle=0, origin=self.center)
            self.line = Line(points=[self.center_x, self.center_y,
                                     self.center_x, self.center_y + 150], width=4)
            PopMatrix()

        # Label für Gradzahl
        self.label = Label(text="0°", font_size=30, pos=(20, self.height - 50))
        self.add_widget(self.label)

    def update_arrow(self, dt):
        # Pfeil rotieren
        self.rot.angle = self.heading
        # Gradzahl anzeigen
        self.label.text = f"{int(self.heading)}°"

class MyGattCallback(PythonJavaClass):
    __javainterfaces__ = ['android/bluetooth/BluetoothGattCallback']
    __javacontext__ = 'app'

    def __init__(self, app):
        super().__init__()
        self.app = app

    @java_method('(Landroid/bluetooth/BluetoothGatt;I)V')
    def onConnectionStateChange(self, gatt, status, newState):
        if newState == 2:  # Connected
            gatt.discoverServices()

    @java_method('(Landroid/bluetooth/BluetoothGatt;I)V')
    def onServicesDiscovered(self, gatt, status):
        service = gatt.getService(UUID.fromString(SERVICE_UUID))
        char = service.getCharacteristic(UUID.fromString(CHAR_UUID))
        gatt.setCharacteristicNotification(char, True)
        descriptor = char.getDescriptor(UUID.fromString("00002902-0000-1000-8000-00805f9b34fb"))
        descriptor.setValue(BluetoothGattCharacteristic.ENABLE_NOTIFICATION_VALUE)
        gatt.writeDescriptor(descriptor)

    @java_method('(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)V')
    def onCharacteristicChanged(self, gatt, characteristic):
        value = characteristic.getFloatValue(0)
        self.app.compass.heading = value

class CompassApp(App):
    def build(self):
        self.compass = CompassWidget()
        Clock.schedule_interval(self.compass.update_arrow, 0.1)
        Clock.schedule_once(self.setup_ble, 1)
        return self.compass

    def setup_ble(self, dt):
        activity = PythonActivity.mActivity
        service = activity.getSystemService(activity.BLUETOOTH_SERVICE)
        manager = cast('android.bluetooth.BluetoothManager', service)
        adapter = manager.getAdapter()

        if not adapter.isEnabled():
            adapter.enable()

        paired_devices = adapter.getBondedDevices().toArray()
        target_device = None
        for d in paired_devices:
            if "NanoCompass" in d.getName():
                target_device = d
                break

        if target_device:
            callback = MyGattCallback(self)
            self.gatt = target_device.connectGatt(activity, False, callback)
        else:
            print("Arduino BLE Gerät nicht gefunden!")

if __name__ == '__main__':
    CompassApp().run()
