from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock

from android import mActivity
from jnius import autoclass, PythonJavaClass, java_method

# =========================
# BLE KONFIG
# =========================
DEVICE_NAME = "Arduino_GCS"
SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
CHAR_UUID = "abcdef01-1234-5678-1234-56789abcdef0"
CCCD_UUID = "00002902-0000-1000-8000-00805f9b34fb"

BluetoothAdapter = autoclass("android.bluetooth.BluetoothAdapter")
BluetoothProfile = autoclass("android.bluetooth.BluetoothProfile")
BluetoothGattDescriptor = autoclass("android.bluetooth.BluetoothGattDescriptor")
UUID = autoclass("java.util.UUID")

ScanCallback = autoclass("android.bluetooth.le.ScanCallback")

# =========================
# SCAN CALLBACK
# =========================
class BLEScanCallback(PythonJavaClass):
    __javainterfaces__ = ["android/bluetooth/le/ScanCallback"]
    __javacontext__ = "app"

    def __init__(self, app):
        super().__init__()
        self.app = app

    @java_method("(ILandroid/bluetooth/le/ScanResult;)V")
    def onScanResult(self, callbackType, result):
        device = result.getDevice()
        if device and device.getName() == DEVICE_NAME:
            self.app.stop_scan()
            self.app.connect(device)

# =========================
# GATT CALLBACK
# =========================
class GattCallback(PythonJavaClass):
    __javainterfaces__ = ["android/bluetooth/BluetoothGattCallback"]
    __javacontext__ = "app"

    def __init__(self, app):
        super().__init__()
        self.app = app

    @java_method("(Landroid/bluetooth/BluetoothGatt;II)V")
    def onConnectionStateChange(self, gatt, status, newState):
        if newState == BluetoothProfile.STATE_CONNECTED:
            Clock.schedule_once(lambda dt: self.app.set_status("Verbunden"))
            gatt.discoverServices()
        elif newState == BluetoothProfile.STATE_DISCONNECTED:
            Clock.schedule_once(lambda dt: self.app.set_status("Getrennt"))

    @java_method("(Landroid/bluetooth/BluetoothGatt;I)V")
    def onServicesDiscovered(self, gatt, status):
        service = gatt.getService(UUID.fromString(SERVICE_UUID))
        if not service:
            return

        char = service.getCharacteristic(UUID.fromString(CHAR_UUID))
        gatt.setCharacteristicNotification(char, True)

        cccd = char.getDescriptor(UUID.fromString(CCCD_UUID))
        cccd.setValue(BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE)
        gatt.writeDescriptor(cccd)

    @java_method("(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)V")
    def onCharacteristicChanged(self, gatt, characteristic):
        value = bytes(characteristic.getValue()).decode("utf-8", "ignore")
        Clock.schedule_once(lambda dt: self.app.update_direction(value))

# =========================
# KIVY APP
# =========================
class BLEApp(App):

    def build(self):
        self.layout = BoxLayout(orientation="vertical", padding=30, spacing=20)

        self.status_label = Label(text="Status: Idle", font_size=22)
        self.dir_label = Label(text="Richtung: --", font_size=36)

        self.btn = Button(text="Neu verbinden", size_hint=(1, 0.2))
        self.btn.bind(on_press=self.start_scan)

        self.layout.add_widget(self.status_label)
        self.layout.add_widget(self.dir_label)
        self.layout.add_widget(self.btn)

        Clock.schedule_once(lambda dt: self.start_scan(), 1)
        return self.layout

    def set_status(self, text):
        self.status_label.text = f"Status: {text}"

    def update_direction(self, value):
        self.dir_label.text = f"Richtung: {value}"

    # =========================
    # BLE FLOW
    # =========================
    def start_scan(self, *args):
        self.set_status("Scanne...")
        adapter = BluetoothAdapter.getDefaultAdapter()
        self.scanner = adapter.getBluetoothLeScanner()
        self.scan_cb = BLEScanCallback(self)
        self.scanner.startScan(self.scan_cb)

    def stop_scan(self):
        if self.scanner:
            self.scanner.stopScan(self.scan_cb)

    def connect(self, device):
        self.set_status("Verbinde...")
        self.gatt = device.connectGatt(
            mActivity,
            False,
            GattCallback(self)
        )

# =========================
# START
# =========================
if __name__ == "__main__":
    BLEApp().run()
