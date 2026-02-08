from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock

from jnius import autoclass, PythonJavaClass, java_method

# =========================
# BLE KONSTANTEN
# =========================
DEVICE_NAME = "Arduino_GCS"
SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
CHAR_UUID = "abcdef01-1234-5678-1234-56789abcdef0"

BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
BluetoothGattCallback = autoclass('android.bluetooth.BluetoothGattCallback')
BluetoothProfile = autoclass('android.bluetooth.BluetoothProfile')
UUID = autoclass('java.util.UUID')

# =========================
# GATT CALLBACK
# =========================
class GattCallback(PythonJavaClass):
    __javainterfaces__ = ['android/bluetooth/BluetoothGattCallback']
    __javacontext__ = 'app'

    def __init__(self, app):
        super().__init__()
        self.app = app

    @java_method('(Landroid/bluetooth/BluetoothGatt;II)V')
    def onConnectionStateChange(self, gatt, status, newState):
        if newState == BluetoothProfile.STATE_CONNECTED:
            Clock.schedule_once(lambda dt: self.app.set_status("Verbunden"))
            gatt.discoverServices()
        elif newState == BluetoothProfile.STATE_DISCONNECTED:
            Clock.schedule_once(lambda dt: self.app.set_status("Getrennt"))

    @java_method('(Landroid/bluetooth/BluetoothGatt;I)V')
    def onServicesDiscovered(self, gatt, status):
        service = gatt.getService(UUID.fromString(SERVICE_UUID))
        char = service.getCharacteristic(UUID.fromString(CHAR_UUID))
        gatt.setCharacteristicNotification(char, True)

    @java_method('(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)V')
    def onCharacteristicChanged(self, gatt, characteristic):
        value = characteristic.getValue().tostring().decode("utf-8")
        Clock.schedule_once(lambda dt: self.app.update_direction(value))

# =========================
# KIVY APP
# =========================
class BLEApp(App):

    def build(self):
        self.layout = BoxLayout(orientation="vertical", padding=20, spacing=20)

        self.status_label = Label(text="Status: Nicht verbunden", font_size=22)
        self.dir_label = Label(text="Richtung: --", font_size=32)

        self.btn = Button(text="Neu verbinden", size_hint=(1, 0.2))
        self.btn.bind(on_press=self.start_scan)

        self.layout.add_widget(self.status_label)
        self.layout.add_widget(self.dir_label)
        self.layout.add_widget(self.btn)

        Clock.schedule_once(lambda dt: self.start_scan())
        return self.layout

    def set_status(self, text):
        self.status_label.text = f"Status: {text}"

    def update_direction(self, direction):
        self.dir_label.text = f"Richtung: {direction}"

    def start_scan(self, *args):
        self.set_status("Scanne...")
        adapter = BluetoothAdapter.getDefaultAdapter()
        scanner = adapter.getBluetoothLeScanner()
        scanner.startScan()
        Clock.schedule_once(lambda dt: self.find_device(adapter), 3)

    def find_device(self, adapter):
        for d in adapter.getBondedDevices().toArray():
            if d.getName() == DEVICE_NAME:
                self.connect(d)
                return
        self.set_status("Gerät nicht gefunden")

    def connect(self, device):
        self.set_status("Verbinde...")
        self.gatt = device.connectGatt(None, False, GattCallback(self))

# =========================
# START
# =========================
if __name__ == "__main__":
    BLEApp().run()
