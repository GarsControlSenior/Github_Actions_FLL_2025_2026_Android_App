from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
import asyncio
from bleak import BleakClient, BleakScanner

# BLE Service & Characteristic UUIDs
SERVICE_UUID = "180A"
CHAR_UUID = "2A57"
DEVICE_NAME = "Arduino_GCS"

class BLEApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        self.status_label = Label(text="Status: Nicht verbunden", font_size=20)
        self.direction_label = Label(text="Richtung: --", font_size=30)
        
        self.connect_btn = Button(text="Verbinden", size_hint=(1, 0.2))
        self.connect_btn.bind(on_press=lambda x: asyncio.ensure_future(self.connect_ble()))
        
        self.layout.add_widget(self.status_label)
        self.layout.add_widget(self.direction_label)
        self.layout.add_widget(self.connect_btn)
        
        return self.layout

    async def connect_ble(self):
        self.status_label.text = "Status: Scanne nach Geräten..."
        devices = await BleakScanner.discover()
        target = None
        for d in devices:
            if d.name == DEVICE_NAME:
                target = d
                break
        
        if target is None:
            self.status_label.text = "Status: Gerät nicht gefunden"
            return
        
        self.status_label.text = f"Status: Verbinde mit {DEVICE_NAME}..."
        async with BleakClient(target) as client:
            if client.is_connected:
                self.status_label.text = f"Status: Verbunden mit {DEVICE_NAME}"
                while True:
                    try:
                        data = await client.read_gatt_char(CHAR_UUID)
                        # Arduino sendet String → decode von bytes
                        direction = data.decode('utf-8').strip()
                        self.direction_label.text = f"Richtung: {direction}"
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        self.status_label.text = f"Fehler: {str(e)}"
                        break

if __name__ == "__main__":
    BLEApp().run()
