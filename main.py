from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.utils import platform
from jnius import autoclass, PythonJavaClass, java_method
import struct

# UUIDs für Standard 16-bit Profile
CCCD_UUID = "00002902-0000-1000-8000-00805f9b34fb"

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
        if name == "Arduino_GCS":
            self.app.log(f"Gefunden: {name}")
            self.app.stop_scan()
            self.app.connect(device)

class GattCallback(PythonJavaClass):
    __javainterfaces__ = ["android/bluetooth/BluetoothGattCallback"]
    def __init__(self, app):
        super().__init__()
        self.app = app

    @java_method("(Landroid/bluetooth/BluetoothGatt;II)V")
    def onConnectionStateChange(self, gatt, status, newState):
        if newState == 2:
            self.app.log("Verbunden! Suche Services...")
            Clock.schedule_once(lambda dt: gatt.discoverServices(), 1.0)
        elif newState == 0:
            self.app.log("Getrennt.")

    @java_method("(Landroid/bluetooth/BluetoothGatt;I)V")
    def onServicesDiscovered(self, gatt, status):
        self.app.log(f"Services entdeckt (Status: {status})")
        services = gatt.getServices()
        
        for i in range(services.size()):
            s = services.get(i)
            s_uuid = s.getUuid().toString().lower()
            self.app.log(f"S: {s_uuid[4:8].upper()}") # Zeigt nur die Kurz-ID
            
            # Suche nach deinem Service (180A)
            if "180a" in s_uuid:
                chars = s.getCharacteristics()
                for j in range(chars.size()):
                    c = chars.get(j)
                    c_uuid = c.getUuid().toString().lower()
                    self.app.log(f"  C: {c_uuid[4:8].upper()}")
                    
                    if "2a57" in c_uuid:
                        self.app.log("Match! Aktiviere Notify...")
                        gatt.setCharacteristicNotification(c, True)
                        d = c.getDescriptor(UUID.fromString(CCCD_UUID))
                        if d:
                            d.setValue(BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE)
                            gatt.writeDescriptor(d)

    @java_method("(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)V")
    def onCharacteristicChanged(self, gatt, characteristic):
        data = characteristic.getValue()
        if data:
            try:
                # Arduino BLE sendet oft 4-byte Int (Little Endian)
                angle = struct.unpack('<i', bytes(data))[0]
                Clock.schedule_once(lambda dt: self.app.update_data(angle))
            except:
                pass

class BLEApp(App):
    def build(self):
        self.root = BoxLayout(orientation='vertical', padding=20)
        self.angle_lbl = Label(text="0°", font_size=100, size_hint_y=0.4)
        
        # Log Fenster
        self.scroll = ScrollView(size_hint_y=0.6)
        self.log_lbl = Label(text="Log gestartet...\n", size_hint_y=None, halign="left", valign="top")
        self.log_lbl.bind(texture_size=self.log_lbl.setter('size'))
        self.scroll.add_widget(self.log_lbl)
        
        self.root.add_widget(self.angle_lbl)
        self.root.add_widget(self.scroll)
        return self.root

    def log(self, txt):
        Clock.schedule_once(lambda dt: setattr(self.log_lbl, 'text', self.log_lbl.text + txt + "\n"))

    def on_start(self):
        if platform == "android":
            self.init_java()
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.ACCESS_FINE_LOCATION, Permission.BLUETOOTH_SCAN, Permission.BLUETOOTH_CONNECT], 
                               lambda p, r: self.start_scan())

    def init_java(self):
        global BluetoothAdapter, BluetoothDevice, BluetoothGattDescriptor, UUID, mActivity
        BluetoothAdapter = autoclass("android.bluetooth.BluetoothAdapter")
        BluetoothDevice = autoclass("android.bluetooth.BluetoothDevice")
        BluetoothGattDescriptor = autoclass("android.bluetooth.BluetoothGattDescriptor")
        UUID = autoclass("java.util.UUID")
        mActivity = autoclass("org.kivy.android.PythonActivity").mActivity

    def start_scan(self):
        self.log("Scan gestartet...")
        self.scan_cb = BLEScanCallback(self)
        BluetoothAdapter.getDefaultAdapter().startLeScan(self.scan_cb)

    def stop_scan(self):
        BluetoothAdapter.getDefaultAdapter().stopLeScan(self.scan_cb)

    def connect(self, device):
        device.connectGatt(mActivity, False, GattCallback(self), 2)

    def update_data(self, angle):
        self.angle_lbl.text = f"{angle}°"

if __name__ == "__main__":
    BLEApp().run()
