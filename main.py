from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.utils import platform
from jnius import autoclass, PythonJavaClass, java_method
import struct

# =========================
# MATCH MIT ARDUINO SKETCH
# =========================
DEVICE_NAME = "Arduino_GCS"
SERVICE_UUID = "0000180a-0000-1000-8000-00805f9b34fb" # 180A in Langform
CHAR_UUID    = "00002a57-0000-1000-8000-00805f9b34fb" # 2A57 in Langform
CCCD_UUID    = "00002902-0000-1000-8000-00805f9b34fb"

BluetoothAdapter = None
BluetoothDevice = None
BluetoothGattDescriptor = None
UUID = None
mActivity = None

class BLEScanCallback(PythonJavaClass):
    __javainterfaces__ = ["android/bluetooth/BluetoothAdapter$LeScanCallback"]
    def __init__(self, app):
        super().__init__()
        self.app = app

    @java_method("(Landroid/bluetooth/BluetoothDevice;I[B)V")
    def onLeScan(self, device, rssi, scanRecord):
        name = device.getName()
        if name and name == DEVICE_NAME:
            self.app.stop_scan()
            self.app.connect(device)

class GattCallback(PythonJavaClass):
    __javainterfaces__ = ["android/bluetooth/BluetoothGattCallback"]
    def __init__(self, app):
        super().__init__()
        self.app = app

    @java_method("(Landroid/bluetooth/BluetoothGatt;II)V")
    def onConnectionStateChange(self, gatt, status, newState):
        if newState == 2: # CONNECTED
            Clock.schedule_once(lambda dt: self.app.set_status("Verbunden"))
            Clock.schedule_once(lambda dt: gatt.discoverServices(), 1.0)
        else:
            Clock.schedule_once(lambda dt: self.app.set_status("Getrennt. Suche..."))
            Clock.schedule_once(lambda dt: self.app.start_scan(), 2.0)

    @java_method("(Landroid/bluetooth/BluetoothGatt;I)V")
    def onServicesDiscovered(self, gatt, status):
        s_obj = gatt.getService(UUID.fromString(SERVICE_UUID))
        if s_obj:
            char = s_obj.getCharacteristic(UUID.fromString(CHAR_UUID))
            if char:
                gatt.setCharacteristicNotification(char, True)
                desc = char.getDescriptor(UUID.fromString(CCCD_UUID))
                if desc:
                    desc.setValue(BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE)
                    gatt.writeDescriptor(desc)

    @java_method("(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)V")
    def onCharacteristicChanged(self, gatt, characteristic):
        data = characteristic.getValue() # Das sind 4 Bytes vom Arduino
        if data:
            # Konvertiert 4 Bytes (Little Endian) in einen Integer
            try:
                angle = struct.unpack('<I', bytes(data))[0]
                Clock.schedule_once(lambda dt: self.app.update_data(angle))
            except:
                pass

class BLEApp(App):
    def build(self):
        self.root = BoxLayout(orientation='vertical', padding=50, spacing=20)
        self.status_lbl = Label(text="Status: Startet...", font_size=20)
        self.angle_lbl = Label(text="0°", font_size=80, color=(0, 1, 0.5, 1))
        self.dir_lbl = Label(text="---", font_size=40)
        
        self.root.add_widget(self.status_lbl)
        self.root.add_widget(self.angle_lbl)
        self.root.add_widget(self.dir_lbl)
        return self.root

    def on_start(self):
        if platform == "android":
            self.setup_android()

    def setup_android(self):
        global BluetoothAdapter, BluetoothDevice, BluetoothGattDescriptor, UUID, mActivity
        BluetoothAdapter = autoclass("android.bluetooth.BluetoothAdapter")
        BluetoothDevice = autoclass("android.bluetooth.BluetoothDevice")
        BluetoothGattDescriptor = autoclass("android.bluetooth.BluetoothGattDescriptor")
        UUID = autoclass("java.util.UUID")
        mActivity = autoclass("org.kivy.android.PythonActivity").mActivity
        self.request_permissions()

    def request_permissions(self):
        from android.permissions import request_permissions, Permission
        request_permissions([Permission.ACCESS_FINE_LOCATION, Permission.BLUETOOTH_SCAN, Permission.BLUETOOTH_CONNECT], 
                           lambda p, r: self.start_scan())

    def start_scan(self, *args):
        adapter = BluetoothAdapter.getDefaultAdapter()
        if adapter and adapter.isEnabled():
            self.scan_cb = BLEScanCallback(self)
            adapter.startLeScan(self.scan_cb)
            self.set_status("Suche Arduino...")

    def stop_scan(self):
        adapter = BluetoothAdapter.getDefaultAdapter()
        if adapter: adapter.stopLeScan(self.scan_cb)

    def connect(self, device):
        self.set_status("Verbinde...")
        device.connectGatt(mActivity, False, GattCallback(self), 2)

    def set_status(self, txt): self.status_lbl.text = txt

    def update_data(self, angle):
        self.angle_lbl.text = f"{angle}°"
        # Richtung berechnen
        dirs = ["Nord", "Nordost", "Ost", "Suedost", "Sued", "Suedwest", "West", "Nordwest"]
        idx = int((angle + 22.5) / 45) % 8
        self.dir_lbl.text = dirs[idx]

if __name__ == "__main__":
    BLEApp().run()
