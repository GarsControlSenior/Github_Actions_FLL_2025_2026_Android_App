from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.utils import platform

# Wichtig: Jnius Importe auf Modulebene minimal halten
from jnius import autoclass, PythonJavaClass, java_method

# Globale Variablen für Java-Klassen (werden in on_start gefüllt)
BluetoothAdapter = None
BluetoothDevice = None
BluetoothGattDescriptor = None
UUID = None
mActivity = None

class BLEScanCallback(PythonJavaClass):
    __javainterfaces__ = ["android/bluetooth/BluetoothAdapter$LeScanCallback"]
    # Kein __javacontext__ hier, das verursacht oft Crashes!

    def __init__(self, app):
        super().__init__()
        self.app = app

    @java_method("(Landroid/bluetooth/BluetoothDevice;I[B)V")
    def onLeScan(self, device, rssi, scanRecord):
        try:
            name = device.getName()
            if name == "Arduino_GCS":
                self.app.stop_scan()
                self.app.connect(device)
        except:
            pass

class GattCallback(PythonJavaClass):
    __javainterfaces__ = ["android/bluetooth/BluetoothGattCallback"]

    def __init__(self, app):
        super().__init__()
        self.app = app

    @java_method("(Landroid/bluetooth/BluetoothGatt;II)V")
    def onConnectionStateChange(self, gatt, status, newState):
        if newState == 2: # CONNECTED
            Clock.schedule_once(lambda dt: self.app.set_status("Verbunden"))
            Clock.schedule_once(lambda dt: gatt.discoverServices(), 0.5)
        else:
            Clock.schedule_once(lambda dt: self.app.set_status("Getrennt"))

    @java_method("(Landroid/bluetooth/BluetoothGatt;I)V")
    def onServicesDiscovered(self, gatt, status):
        # Hier deine UUIDs einsetzen
        s_uuid = UUID.fromString("12345678-1234-5678-1234-56789abcdef0")
        c_uuid = UUID.fromString("abcdef01-1234-5678-1234-56789abcdef0")
        cccd   = UUID.fromString("00002902-0000-1000-8000-00805f9b34fb")
        
        service = gatt.getService(s_uuid)
        if service:
            char = service.getCharacteristic(c_uuid)
            if char:
                gatt.setCharacteristicNotification(char, True)
                desc = char.getDescriptor(cccd)
                if desc:
                    desc.setValue(BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE)
                    gatt.writeDescriptor(desc)

    @java_method("(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)V")
    def onCharacteristicChanged(self, gatt, characteristic):
        data = characteristic.getValue()
        if data:
            val = list(data)[0]
            Clock.schedule_once(lambda dt: self.app.update_value(val))

class BLEApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical', padding=20)
        self.status_lbl = Label(text="Status: Warte auf Android...")
        self.value_lbl = Label(text="-", font_size=50)
        self.btn = Button(text="SCAN", on_press=self.start_scan, size_hint_y=0.2)
        
        self.layout.add_widget(self.status_lbl)
        self.layout.add_widget(self.value_lbl)
        self.layout.add_widget(self.btn)
        return self.layout

    def on_start(self):
        # Erst hier, wenn die App läuft, Java-Klassen laden
        if platform == "android":
            self.init_android()
        else:
            self.set_status("Nicht auf Android")

    def init_android(self):
        global BluetoothAdapter, BluetoothDevice, BluetoothGattDescriptor, UUID, mActivity
        try:
            BluetoothAdapter = autoclass("android.bluetooth.BluetoothAdapter")
            BluetoothDevice = autoclass("android.bluetooth.BluetoothDevice")
            BluetoothGattDescriptor = autoclass("android.bluetooth.BluetoothGattDescriptor")
            UUID = autoclass("java.util.UUID")
            mActivity = autoclass("org.kivy.android.PythonActivity").mActivity
            self.request_perms()
        except Exception as e:
            self.set_status(f"Java Error: {str(e)}")

    def request_perms(self):
        from android.permissions import request_permissions, Permission
        from android.os import Build
        perms = [Permission.ACCESS_FINE_LOCATION]
        if Build.VERSION.SDK_INT >= 31:
            perms += [Permission.BLUETOOTH_SCAN, Permission.BLUETOOTH_CONNECT]
        request_permissions(perms, lambda p, r: self.set_status("Bereit" if all(r) else "Berechtigung fehlt"))

    def start_scan(self, *args):
        self.adapter = BluetoothAdapter.getDefaultAdapter()
        if self.adapter and self.adapter.isEnabled():
            self.scan_cb = BLEScanCallback(self)
            self.adapter.startLeScan(self.scan_cb)
            self.set_status("Scanne...")
        else:
            self.set_status("BT aus!")

    def stop_scan(self):
        if self.adapter: self.adapter.stopLeScan(self.scan_cb)

    def connect(self, device):
        self.set_status("Verbinde...")
        self.gatt = device.connectGatt(mActivity, False, GattCallback(self), 2)

    def set_status(self, txt): self.status_lbl.text = f"Status: {txt}"
    def update_value(self, val): self.value_lbl.text = str(val)

if __name__ == "__main__":
    BLEApp().run()
