from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.utils import platform

from jnius import autoclass, PythonJavaClass, java_method

# =========================
# BLE CONFIG
# =========================
DEVICE_NAME = "Arduino_GCS"

SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
CHAR_UUID    = "abcdef01-1234-5678-1234-56789abcdef0"
CCCD_UUID    = "00002902-0000-1000-8000-00805f9b34fb"

# =========================
# ANDROID CLASSES
# =========================
if platform == "android":
    BluetoothAdapter = autoclass("android.bluetooth.BluetoothAdapter")
    BluetoothDevice  = autoclass("android.bluetooth.BluetoothDevice")
    BluetoothGattDescriptor = autoclass("android.bluetooth.BluetoothGattDescriptor")
    UUID = autoclass("java.util.UUID")

    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    mActivity = PythonActivity.mActivity

# =========================
# STABILER SCAN CALLBACK
# =========================
class BLEScanCallback(PythonJavaClass):
    __javainterfaces__ = [
        "android/bluetooth/BluetoothAdapter$LeScanCallback"
    ]
    __javacontext__ = "app"

    def __init__(self, app):
        super().__init__()
        self.app = app

    @java_method("(Landroid/bluetooth/BluetoothDevice;I[B)V")
    def onLeScan(self, device, rssi, scanRecord):
        name = device.getName()
        if name and name == DEVICE_NAME:
            print("✔ Gerät gefunden:", name)
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
        if newState == 2:  # STATE_CONNECTED
            Clock.schedule_once(
                lambda dt: self.app.set_status("Verbunden")
            )
            # minimal verzögern → stabiler
            Clock.schedule_once(
                lambda dt: gatt.discoverServices(), 0.2
            )
        else:
            Clock.schedule_once(
                lambda dt: self.app.set_status("Getrennt")
            )

    @java_method("(Landroid/bluetooth/BluetoothGatt;I)V")
    def onServicesDiscovered(self, gatt, status):
        service = gatt.getService(UUID.fromString(SERVICE_UUID))
        if not service:
            print("Service nicht gefunden")
            return

        char = service.getCharacteristic(UUID.fromString(CHAR_UUID))
        if not char:
            print("Characteristic nicht gefunden")
            return

        # Local
        gatt.setCharacteristicNotification(char, True)

        # Remote
        desc = char.getDescriptor(UUID.fromString(CCCD_UUID))
        if desc:
            desc.setValue(
                BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
            )
            gatt.writeDescriptor(desc)

    @java_method(
        "(Landroid/bluetooth/BluetoothGatt;"
        "Landroid/bluetooth/BluetoothGattCharacteristic;)V"
    )
    def onCharacteristicChanged(self, gatt, characteristic):
        data = characteristic.getValue()
        if data:
            value = list(data)[0]  # Arduino-freundlich
            Clock.schedule_once(
                lambda dt: self.app.update_value(value)
            )

# =========================
# KIVY APP
# =========================
class BLEApp(App):

    def build(self):
        root = BoxLayout(
            orientation="vertical",
            padding=30,
            spacing=20
        )

        self.status_lbl = Label(
            text="Status: Init",
            font_size=22
        )
        self.value_lbl = Label(
            text="Wert: --",
            font_size=36
        )

        btn = Button(
            text="Scan starten",
            size_hint=(1, 0.25)
        )
        btn.bind(on_press=self.start_scan)

        root.add_widget(self.status_lbl)
        root.add_widget(self.value_lbl)
        root.add_widget(btn)

        self.adapter = None
        self.scan_cb = None
        self.gatt = None

        self.request_permissions()
        return root

    # ---------------------
    # PERMISSIONS
    # ---------------------
    def request_permissions(self):
        if platform != "android":
            return

        from android.permissions import (
            request_permissions,
            Permission
        )
        from android.os import Build

        perms = [Permission.ACCESS_FINE_LOCATION]
        if Build.VERSION.SDK_INT >= 31:
            perms += [
                Permission.BLUETOOTH_SCAN,
                Permission.BLUETOOTH_CONNECT
            ]

        request_permissions(perms, self.permission_cb)

    def permission_cb(self, perms, results):
        if all(results):
            self.set_status("Bereit")
        else:
            self.set_status("Keine Berechtigung")

    # ---------------------
    # BLE
    # ---------------------
    def start_scan(self, *args):
        self.adapter = BluetoothAdapter.getDefaultAdapter()
        if not self.adapter or not self.adapter.isEnabled():
            self.set_status("Bluetooth aus")
            return

        self.scan_cb = BLEScanCallback(self)
        self.adapter.startLeScan(self.scan_cb)
        self.set_status("Scanne…")

    def stop_scan(self):
        if self.adapter and self.scan_cb:
            self.adapter.stopLeScan(self.scan_cb)

    def connect(self, device):
        self.set_status("Verbinde…")
        self.gatt = device.connectGatt(
            mActivity,
            False,
            GattCallback(self),
            BluetoothDevice.TRANSPORT_LE
        )

    # ---------------------
    # UI
    # ---------------------
    def set_status(self, txt):
        self.status_lbl.text = f"Status: {txt}"

    def update_value(self, val):
        self.value_lbl.text = f"Wert: {val}"

# =========================
if __name__ == "__main__":
    BLEApp().run()
