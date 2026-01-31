from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.graphics import Line, Color, PushMatrix, PopMatrix, Rotate
from kivy.uix.label import Label
from jnius import autoclass, cast, PythonJavaClass, java_method

# ------------------- Android BLE Klassen -------------------
BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
PythonActivity = autoclass('org.kivy.android.PythonActivity')
BluetoothGattCharacteristic = autoclass('android.bluetooth.BluetoothGattCharacteristic')
BluetoothGattDescriptor = autoclass('android.bluetooth.BluetoothGattDescriptor')
BluetoothGatt = autoclass('android.bluetooth.BluetoothGatt')
UUID = autoclass('java.util.UUID')

SERVICE_UUID = "0000180C-0000-1000-8000-00805f9b34fb"
CHAR_UUID = "00002A57-0000-1000-8000-00805f9b34fb"

# ------------------- Widget für Pfeil + Gradzahl -------------------
class CompassWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.heading = 0
        with self.canvas:
            Color(1, 0, 0)
            PushMatrix()
            self.rot = Rotate(angle=0, origin=self.center)
            self.line = Line(points=[self.center_x, self.center_y,
                                     self.center_x, self.center_y + 150], width=4)
            PopMatrix()

        self.label = Label(text="0°", font_size=30, pos=(20, self.height - 50))
        self.add_widget(self.label)

    def update_arrow(self, dt):
        self.rot.angle = self.heading
        self.label.text = f"{int(self.heading)}°"

# ------------------- BLE Callback -------------------
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
        descriptor.setValue(BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE)
        gatt.writeDescriptor(descriptor)

    @java_method('(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)V')
    def onCharacteristicChanged(self, gatt, characteristic):
        value = characteristic.getFloatValue(0)
        self.app.compass.heading = value

# ------------------- App -------------------
class CompassApp(App):
    def build(self):
        self.compass = CompassWidget()
        Clock.schedule_interval(self.compass.update_arrow, 0.1)
        Clock.schedule_once(self.connect_paired_device, 1)
        return self.compass

    def connect_paired_device(self, dt):
        activity = PythonActivity.mActivity
        manager = cast('android.bluetooth.BluetoothManager', activity.getSystemService(activity.BLUETOOTH_SERVICE))
        adapter = manager.getAdapter()

        if not adapter.isEnabled():
            adapter.enable()

        paired_devices = adapter.getBondedDevices().toArray()
        target_device = None

        # <- HIER den Namen deines Arduino eintragen:
        target_name = "NanoCompass"  # <-- falls dein Gerät anders heißt, ändern!

        for d in paired_devices:
            if target_name in d.getName():
                target_device = d
                break

        if target_device:
            callback = MyGattCallback(self)
            self.gatt = target_device.connectGatt(activity, False, callback)
            print("Verbunden mit Arduino!")
        else:
            print(f"Kein gepaartes Gerät mit Name {target_name} gefunden!")

# ------------------- Start -------------------
if __name__ == '__main__':
    CompassApp().run()
