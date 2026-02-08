from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.utils import platform
from jnius import autoclass, PythonJavaClass, java_method
import struct

# Standard UUIDs
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
            self.app.log(f"Gefunden: {name} ({device.getAddress()})")
            self.app.connect(device)

class GattCallback(PythonJavaClass):
    __javainterfaces__ = ["android/bluetooth/BluetoothGattCallback"]
    def __init__(self, app):
        super().__init__()
        self.app = app

    @java_method("(Landroid/bluetooth/BluetoothGatt;II)V")
    def onConnectionStateChange(self, gatt, status, newState):
        if newState == 2: # STATE_CONNECTED
            self.app.log("Verbunden! Suche Services...")
            Clock.schedule_once(lambda dt: gatt.discoverServices(), 1.0)
        elif newState == 0: # STATE_DISCONNECTED
            self.app.log("Verbindung getrennt.")

    @java_method("(Landroid/bluetooth/BluetoothGatt;I)V")
    def onServicesDiscovered(self, gatt, status):
        self.app.log(f"Services entdeckt (Status: {status})")
        services = gatt.getServices()
        
        for i in range(services.size()):
            s = services.get(i)
            s_uuid = s.getUuid().toString().lower()
            self.app.log(f"S: {s_uuid[4:8].upper()}")
            
            if "180a" in s_uuid:
                chars = s.getCharacteristics()
                for j in range(chars.size()):
                    c = chars.get(j)
                    c_uuid = c.getUuid().toString().lower()
                    self.app.log(f"  C: {c_uuid[4:8].upper()}")
                    
                    if "2a57" in c_uuid:
                        self.app.log("Aktiviere Notify...")
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
                angle = struct.unpack('<i', bytes(data))[0]
                Clock.schedule_once(lambda dt: self.app.update_data(angle))
            except: pass

class BLEApp(App):
    def build(self):
        self.root = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # UI Elemente
        self.angle_lbl = Label(text="0°", font_size=100, size_hint_y=0.3)
        self.status_btn = Button(text="Scan starten", size_hint_y=0.15, on_press=self.start_scan)
        
        # Log Fenster
        self.scroll = ScrollView(size_hint_y=0.55)
        self.log_lbl = Label(text="System bereit\n", size_hint_y=None, halign="left", valign="top")
        self.log_lbl.bind(texture_size=self.log_lbl.setter('size'))
        self.scroll.add_widget(self.log_lbl)
        
        self.root.add_widget(self.angle_lbl)
        self.root.add_widget(self.status_btn)
        self.root.add_widget(self.scroll)
        
        self.gatt = None
        self.device = None
        return self.root

    def log(self, txt):
        Clock.schedule_once(lambda dt: setattr(self.log_lbl, 'text', self.log_lbl.text + txt + "\n"))

    def on_start(self):
        if platform == "android":
            self.init_java()
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.ACCESS_FINE_LOCATION, Permission.BLUETOOTH_SCAN, Permission.BLUETOOTH_CONNECT], 
                               lambda p, r: self.log("Berechtigungen okay."))

    def init_java(self):
        global BluetoothAdapter, BluetoothDevice, BluetoothGattDescriptor, UUID, mActivity
        BluetoothAdapter = autoclass("android.bluetooth.BluetoothAdapter")
        BluetoothDevice = autoclass("android.bluetooth.BluetoothDevice")
        BluetoothGattDescriptor = autoclass("android.bluetooth.BluetoothGattDescriptor")
        UUID = autoclass("java.util.UUID")
        mActivity = autoclass("org.kivy.android.PythonActivity").mActivity

    def start_scan(self, *args):
        self.log("Scanne nach Arduino...")
        self.status_btn.text = "Suche..."
        self.scan_cb = BLEScanCallback(self)
        BluetoothAdapter.getDefaultAdapter().startLeScan(self.scan_cb)

    def stop_scan(self):
        adapter = BluetoothAdapter.getDefaultAdapter()
        if adapter and hasattr(self, 'scan_cb'):
            adapter.stopLeScan(self.scan_cb)

    def connect(self, device):
        self.device = device
        self.log("Stoppe Scan...")
        self.stop_scan()
        self.log("Verbinde (Delay 0.5s)...")
        self.status_btn.text = "Verbinde..."
        Clock.schedule_once(lambda dt: self._do_connect(), 0.5)

    def _do_connect(self):
        # TRANSPORT_LE (2) ist entscheidend für Stabilität
        self.gatt = self.device.connectGatt(mActivity, False, GattCallback(self), 2)

    def update_data(self, angle):
        self.angle_lbl.text = f"{angle}°"
        self.status_btn.text = "Verbunden"

if __name__ == "__main__":
    BLEApp().run()
