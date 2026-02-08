from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.utils import platform

from jnius import autoclass, PythonJavaClass, java_method, cast

# =========================
# BLE KONFIG
# =========================
DEVICE_NAME = "Arduino_GCS"
SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
CHAR_UUID = "abcdef01-1234-5678-1234-56789abcdef0"
CCCD_UUID = "00002902-0000-1000-8000-00805f9b34fb"

# Android Klassen
if platform == 'android':
    BluetoothAdapter = autoclass("android.bluetooth.BluetoothAdapter")
    BluetoothProfile = autoclass("android.bluetooth.BluetoothProfile")
    BluetoothGattDescriptor = autoclass("android.bluetooth.BluetoothGattDescriptor")
    UUID = autoclass("java.util.UUID")
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    mActivity = PythonActivity.mActivity
    Context = autoclass('android.content.Context')

# =========================
# CALLBACKS
# =========================
# HINWEIS: ScanCallback und BluetoothGattCallback sind in Java abstrakte Klassen.
# Pyjnius kann diese oft nicht direkt implementieren. Wenn dies abstürzt,
# wird die Bibliothek "able" (Android Bluetooth Low Energy) benötigt.

class BLEScanCallback(PythonJavaClass):
    __javainterfaces__ = ["android/bluetooth/le/ScanCallback"]
    __javacontext__ = "app"

    def __init__(self, app):
        super().__init__()
        self.app = app

    @java_method("(ILandroid/bluetooth/le/ScanResult;)V")
    def onScanResult(self, callbackType, result):
        try:
            device = result.getDevice()
            name = device.getName()
            if name and name == DEVICE_NAME:
                print(f"Gerät gefunden: {name}")
                self.app.stop_scan()
                self.app.connect(device)
        except Exception as e:
            print(f"Error in onScanResult: {e}")

    @java_method("(I)V")
    def onScanFailed(self, errorCode):
        print(f"Scan failed with error: {errorCode}")

class GattCallback(PythonJavaClass):
    __javainterfaces__ = ["android/bluetooth/BluetoothGattCallback"]
    __javacontext__ = "app"

    def __init__(self, app):
        super().__init__()
        self.app = app

    @java_method("(Landroid/bluetooth/BluetoothGatt;II)V")
    def onConnectionStateChange(self, gatt, status, newState):
        if newState == 2: # STATE_CONNECTED
            Clock.schedule_once(lambda dt: self.app.set_status("Verbunden"))
            # Wichtig: Discover Services muss auf dem UI Thread oder verzögert gestartet werden
            gatt.discoverServices()
        elif newState == 0: # STATE_DISCONNECTED
            Clock.schedule_once(lambda dt: self.app.set_status("Getrennt"))

    @java_method("(Landroid/bluetooth/BluetoothGatt;I)V")
    def onServicesDiscovered(self, gatt, status):
        if status != 0: # GATT_SUCCESS
            return

        service = gatt.getService(UUID.fromString(SERVICE_UUID))
        if not service:
            print("Service nicht gefunden")
            return

        char = service.getCharacteristic(UUID.fromString(CHAR_UUID))
        if not char:
            print("Characteristic nicht gefunden")
            return

        # Notifications aktivieren (Lokal)
        gatt.setCharacteristicNotification(char, True)

        # Descriptor schreiben (Remote)
        descriptor = char.getDescriptor(UUID.fromString(CCCD_UUID))
        if descriptor:
            descriptor.setValue(BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE)
            gatt.writeDescriptor(descriptor)

    @java_method("(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)V")
    def onCharacteristicChanged(self, gatt, characteristic):
        raw_val = characteristic.getValue()
        if raw_val:
            # Pyjnius gibt signierte Bytes (-128 bis 127) zurück, Python braucht unsigned (0-255) oder direkten Cast
            # Hier vereinfacht:
            try:
                value = bytes(raw_val).decode("utf-8", "ignore")
                Clock.schedule_once(lambda dt: self.app.update_direction(value))
            except Exception as e:
                print(f"Error decoding: {e}")

# =========================
# KIVY APP
# =========================
class BLEApp(App):
    def build(self):
        self.layout = BoxLayout(orientation="vertical", padding=30, spacing=20)
        self.status_label = Label(text="Status: Init...", font_size=22)
        self.dir_label = Label(text="Richtung: --", font_size=36)
        self.btn = Button(text="Scan Starten", size_hint=(1, 0.2))
        self.btn.bind(on_press=self.start_scan_wrapper)

        self.layout.add_widget(self.status_label)
        self.layout.add_widget(self.dir_label)
        self.layout.add_widget(self.btn)

        self.scanner = None
        self.gatt = None
        self.scan_cb = None # Referenz behalten, damit GC sie nicht löscht

        # Permissions beim Start anfordern
        self.request_android_permissions()
        return self.layout

    def request_android_permissions(self):
        if platform != 'android':
            return

        from android.permissions import request_permissions, Permission
        import android.os.Build

        # API Version prüfen
        version = android.os.Build.VERSION.SDK_INT
        
        permissions = []
        if version >= 31: # Android 12+
            permissions = [
                Permission.BLUETOOTH_SCAN,
                Permission.BLUETOOTH_CONNECT,
                Permission.ACCESS_FINE_LOCATION 
            ]
        else: # Android < 12
            permissions = [
                Permission.ACCESS_FINE_LOCATION,
                Permission.ACCESS_COARSE_LOCATION
            ]
        
        request_permissions(permissions, self.permission_callback)

    def permission_callback(self, permissions, results):
        if all(results):
            self.set_status("Bereit zum Scannen")
        else:
            self.set_status("Keine Berechtigung!")

    def set_status(self, text):
        self.status_label.text = f"Status: {text}"

    def update_direction(self, value):
        self.dir_label.text = f"Richtung: {value}"

    def start_scan_wrapper(self, instance):
        if platform == 'android':
            self.start_scan()
        else:
            print("BLE funktioniert nur auf Android")

    def start_scan(self):
        self.set_status("Scanne...")
        adapter = BluetoothAdapter.getDefaultAdapter()
        if not adapter or not adapter.isEnabled():
            self.set_status("Bluetooth ist aus!")
            return

        self.scanner = adapter.getBluetoothLeScanner()
        self.scan_cb = BLEScanCallback(self)
        
        # Start Scan (benötigt Permissions)
        try:
            self.scanner.startScan(self.scan_cb)
        except Exception as e:
            self.set_status(f"Scan Error: {e}")

    def stop_scan(self):
        if self.scanner and self.scan_cb:
            self.scanner.stopScan(self.scan_cb)
            self.set_status("Scan gestoppt")

    def connect(self, device):
        self.set_status("Verbinde...")
        # autoConnect=False ist für BLE stabiler
        self.gatt = device.connectGatt(
            mActivity,
            False,
            GattCallback(self)
        )

if __name__ == "__main__":
    BLEApp().run()
