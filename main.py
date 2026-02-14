import os
import cv2
import numpy as np
import math
import threading
from kivy.utils import platform
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.graphics import Color, Line
from kivy.properties import NumericProperty, ListProperty, StringProperty
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.snackbar import Snackbar
from plyer import accelerometer
from camera4kivy import Preview

# Java-Brücke für Galerie-Zugriff
if platform == 'android':
    from android.permissions import request_permissions, Permission
    from jnius import autoclass, cast

# UI Layout
KV = '''
<OrtographerScreen>:
    BoxLayout:
        orientation: 'vertical'
        md_bg_color: 0.05, 0.05, 0.05, 1

        RelativeLayout:
            id: container
            Preview:
                id: preview
                aspect_ratio: '16:9'
            
            Widget:
                id: overlay
                canvas:
                    Color:
                        rgba: 1, 0.8, 0, 0.8 # Gelbes Trapez
                    Line:
                        points: root.polygon_flat
                        width: dp(2)
                        close: True

        MDCard:
            orientation: "vertical"
            padding: "15dp"
            size_hint_y: None
            height: "230dp"
            radius: [25, 25, 0, 0]
            md_bg_color: 0.15, 0.15, 0.15, 1
            elevation: 4

            MDLabel:
                text: root.status_text
                halign: "center"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                font_style: "Button"

            MDBoxLayout:
                MDLabel: text: "Breite"; theme_text_color: "Hint"; size_hint_x: 0.2
                MDSlider:
                    id: w_slider
                    min: 10; max: 100; value: 65
                    on_value: root.update_polygon()
            
            MDBoxLayout:
                MDLabel: text: "Höhe"; theme_text_color: "Hint"; size_hint_x: 0.2
                MDSlider:
                    id: h_slider
                    min: 10; max: 100; value: 45
                    on_value: root.update_polygon()

            MDFillRoundFlatButton:
                text: "SCAN & SPEICHERN"
                pos_hint: {"center_x": .5}
                size_hint_x: 0.8
                on_release: root.safe_capture()
                disabled: root.is_processing == 1
'''

class OrtographerScreen(MDScreen):
    roll = NumericProperty(0)
    pitch = NumericProperty(0)
    polygon_flat = ListProperty([])
    status_text = StringProperty("Initialisiere...")
    is_processing = NumericProperty(0)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.current_pts = []
        # Low-Pass Filter Variablen (Zappel-Schutz)
        self.lp_roll = 0
        self.lp_pitch = 0
        self.alpha = 0.15 # Filter-Stärke (0.01 = sehr träge, 1.0 = kein Filter)
        
        Clock.schedule_once(self.setup)

    def setup(self, dt):
        if platform == 'android':
            request_permissions([Permission.CAMERA, Permission.WRITE_EXTERNAL_STORAGE])
        
        # Kamera verbinden
        self.ids.preview.connect_camera(enable_analyze_callback=False)
        # Sensoren alle 30ms abfragen
        Clock.schedule_interval(self.update_sensors, 1.0/30.0)

    def update_sensors(self, dt):
        """ Liest Sensoren und glättet die Werte (Zappel-Schutz) """
        try:
            acc = accelerometer.acceleration
            if acc and all(v is not None for v in acc):
                # Rohwerte berechnen
                raw_roll = math.degrees(math.atan2(acc[0], acc[2]))
                raw_pitch = math.degrees(math.atan2(-acc[1], math.sqrt(acc[0]**2 + acc[2]**2)))
                
                # Low-Pass Filter Formel: glatt = alpha * neu + (1-alpha) * alt
                self.lp_roll = self.alpha * raw_roll + (1 - self.alpha) * self.lp_roll
                self.lp_pitch = self.alpha * raw_pitch + (1 - self.alpha) * self.lp_pitch
                
                self.roll, self.pitch = self.lp_roll, self.lp_pitch
                self.status_text = f"Neigung: P {int(self.pitch)}° | R {int(self.roll)}°"
                self.update_polygon()
        except:
            self.status_text = "Keine Sensordaten verfügbar"

    def update_polygon(self):
        """ Berechnet das Trapez (logische Kopie deines Swift-Codes) """
        vw, vh = self.ids.container.size
        if vw < 10: return

        w_pc, h_pc = self.ids.w_slider.value / 100.0, self.ids.h_slider.value / 100.0
        cx, cy = vw / 2, vh / 2
        bw, bh = vw * w_pc, vh * h_pc

        p = max(-35, min(35, self.pitch)) / 35.0
        r = max(-35, min(35, self.roll)) / 35.0

        narrow = 0.35 * abs(p) * bw
        skew = r * (bw * 0.2)
        top_w = bw - (narrow if p >= 0 else 0)
        bot_w = bw - (0 if p >= 0 else narrow)

        # TL, TR, BR, BL
        self.current_pts = [
            (cx - skew/2 - top_w/2, cy + bh/2),
            (cx - skew/2 + top_w/2, cy + bh/2),
            (cx + skew/2 + bot_w/2, cy - bh/2),
            (cx + skew/2 - bot_w/2, cy - bh/2)
        ]
        
        flat = []
        for p_xy in self.current_pts: flat.extend([p_xy[0], p_xy[1]])
        self.polygon_flat = flat

    def safe_capture(self):
        if self.is_processing: return
        self.is_processing = 1
        self.status_text = "Verarbeite Bild..."
        # Screenshot-Funktion von camera4kivy
        self.ids.preview.capture_screenshot(self.process_thread_starter)

    def process_thread_starter(self, path):
        threading.Thread(target=self._run_cv_logic, args=(path,)).start()

    def _run_cv_logic(self, path):
        try:
            img = cv2.imread(path)
            if img is None: return

            # Koordinaten-Mapping View -> Bild-Pixel
            ih, iw = img.shape[:2]
            vw, vh = self.ids.container.size
            src_pts = []
            for (vx, vy) in self.current_pts:
                # Kivy Y (unten 0) -> OpenCV Y (oben 0)
                src_pts.append([(vx/vw)*iw, (1.0 - (vy/vh))*ih])
            
            src_pts = np.array(src_pts, dtype="float32")
            # Zielformat DIN A4 Proportionen
            dst_pts = np.array([[0,0], [1200,0], [1200,1600], [0,1600]], dtype="float32")
            
            M = cv2.getPerspectiveTransform(src_pts, dst_pts)
            warped = cv2.warpPerspective(img, M, (1200, 1600))
            
            # Speichername generieren
            final_name = f"Ortho_{int(Clock.get_time())}.jpg"
            out_path = os.path.join(os.path.dirname(path), final_name)
            cv2.imwrite(out_path, warped)

            # In Galerie speichern (Android MediaStore)
            if platform == 'android':
                self.android_save_to_gallery(out_path, final_name)

            self.notify(f"Gespeichert: {final_name}")
        except Exception as e:
            self.notify(f"Fehler: {str(e)}")
        finally:
            self.is_processing = 0
            if os.path.exists(path): os.remove(path)

    def android_save_to_gallery(self, file_path, name):
        """ Nutzt MediaStore, damit das Bild sofort in Fotos erscheint """
        try:
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            MediaStore = autoclass('android.provider.MediaStore')
            BitmapFactory = autoclass('android.graphics.BitmapFactory')
            context = PythonActivity.mActivity
            bitmap = BitmapFactory.decodeFile(file_path)
            MediaStore.Images.Media.insertImage(context.getContentResolver(), bitmap, name, "Ortographer")
        except: pass

    def notify(self, msg):
        Clock.schedule_once(lambda dt: Snackbar(text=msg).open(), 0)

class OrtographerApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Amber"
        return Builder.load_string(KV + "\nOrtographerScreen:")

    def on_pause(self):
        # WICHTIG: Kamera beim Minimieren stoppen, um Absturz zu verhindern
        try: self.root.ids.preview.disconnect_camera()
        except: pass
        return True

    def on_resume(self):
        # Kamera wieder starten
        try: self.root.ids.preview.connect_camera()
        except: pass

if __name__ == '__main__':
    OrtographerApp().run()
