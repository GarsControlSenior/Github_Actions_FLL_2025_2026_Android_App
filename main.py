import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.camera import Camera
from kivy.uix.image import Image
from kivy.graphics import Color, Ellipse, Line
import math
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.clock import Clock # Neu: Für verzögerten Start
from os.path import join, exists
from PIL import Image as PILImage

# Neu: Imports für Android-Berechtigungen. Nutzt try-except für Desktop-Tests.
try:
    from android.permissions import request_permissions, Permission
except ImportError:
    request_permissions = None # Platzhalter für Desktop-Systeme


class TouchImage(Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.points = []

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and len(self.points) < 4:
            self.points.append((touch.x, touch.y))
            self.redraw_shapes()
            return True

        return super().on_touch_down(touch)

    def redraw_shapes(self):
        self.canvas.after.clear()
        if not self.points:
            return

        with self.canvas.after:
            Color(1, 0, 0)
            for x, y in self.points:
                Ellipse(pos=(x - 6, y - 6), size=(12, 12))

            if len(self.points) >= 2:
                cx = sum(p[0] for p in self.points) / len(self.points)
                cy = sum(p[1] for p in self.points) / len(self.points)
                def ang(p):
                    return math.atan2(p[1] - cy, p[0] - cx)

                ordered = sorted(self.points, key=ang)
                pts = []
                for p in ordered:
                    pts.extend([p[0], p[1]])

                Color(0, 1, 0)
                if len(ordered) >= 3:
                    Line(points=pts + pts[0:2], width=2)
                else:
                    Line(points=pts, width=2)

class CameraApp(App):
    # --- NEUE METHODEN FÜR BERECHTIGUNGEN ---

    def check_and_request_permissions(self):
        """Überprüft und fordert die notwendigen Berechtigungen an."""
        
        if request_permissions: # Nur auf Android ausführen
            self.info.text = "Fordere Berechtigungen an..."
            
            # Die Liste der benötigten Berechtigungen (Kamera und Speicher)
            permissions_to_request = [
                Permission.CAMERA,
                Permission.WRITE_EXTERNAL_STORAGE
            ]
            
            # Die Abfrage starten. Das Ergebnis landet in 'self.permissions_callback'.
            request_permissions(permissions_to_request, self.permissions_callback)
        else:
            # Nicht auf Android (Desktop): Kamera kann direkt gestartet werden
            self.start_camera_if_allowed()

    def permissions_callback(self, permissions, granted):
        """Wird aufgerufen, nachdem der Benutzer auf die Berechtigungsanfrage reagiert hat."""
        
        # Prüfen, ob alle kritischen Berechtigungen erteilt wurden
        if all(granted):
            self.info.text = "Alle Berechtigungen erteilt. Kamera startet..."
            self.start_camera_if_allowed()
        else:
            self.info.text = "FEHLER: Berechtigungen verweigert. Kamera nicht verfügbar."
            # Hier könnten Sie eine Fehlermeldung anzeigen oder die App beenden

    def start_camera_if_allowed(self):
        """Startet die Kamera, wenn die Berechtigungen erteilt wurden oder auf dem Desktop."""
        # Wichtig: Wir müssen self.camera zur main_content hinzufügen, da es am Ende von build()
        # NICHT mehr hinzugefügt wird, sondern hier!
        if self.camera not in self.main_content.children:
             self.main_content.add_widget(self.camera)
        
        self.camera.play = True
        self.info.text = "Kamera läuft."
    
    # --- BESTEHENDE METHODEN ---

    def build(self):
        root = BoxLayout(orientation="vertical")
        
        # 1. Haupt-Widget: Enthält entweder die Kamera oder das Bild (nimmt 70% des Platzes ein)
        self.main_content = BoxLayout(orientation="vertical", size_hint_y=0.7)
        root.add_widget(self.main_content)
        
        # 2. Steuerungselemente (Buttons und Label, nehmen 30% des Platzes ein)
        self.controls = BoxLayout(orientation="vertical", size_hint_y=0.3)
        root.add_widget(self.controls)

        # Widgets initialisieren
        self.camera = Camera(play=False, resolution=(640, 480))
        self.image = TouchImage(allow_stretch=True, keep_ratio=True)
        self.filename = "" 

        # UI-Elemente zu Controls hinzufügen
        btn_photo = Button(text="Foto aufnehmen", size_hint_y=0.3)
        btn_photo.bind(on_press=self.take_photo)
        self.controls.add_widget(btn_photo)

        btn_fix = Button(text="Korrektur anwenden", size_hint_y=0.3)
        btn_fix.bind(on_press=self.correct_image)
        self.controls.add_widget(btn_fix)

        self.info = Label(text="Warte auf Berechtigung...", size_hint_y=0.4) # Angepasster Starttext
        self.controls.add_widget(self.info)
        
        # KEIN DIREKTER KAMERA-START MEHR HIER! Die Kamera wird erst nach der Berechtigungsprüfung gestartet.
        
        # Startet die Berechtigungsabfrage verzögert
        Clock.schedule_once(lambda dt: self.check_and_request_permissions(), 0.1)

        return root

    def take_photo(self, *args):
        # ... (Logik wie zuvor) ...
        try:
            app_data_path = App.get_running_app().user_data_dir
            self.filename = join(app_data_path, "foto.png")

        
            self.camera.export_to_png(self.filename)
            
            self.camera.play = False
            self.main_content.remove_widget(self.camera)

            self.image.source = self.filename
            self.image.reload()
            
            self.main_content.clear_widgets()
            self.main_content.add_widget(self.image)

            self.image.points.clear()
            self.image.canvas.after.clear()
            self.info.text = "4 Punkte antippen"
            
        except Exception as e:
            self.info.text = f"Fehler beim Foto: {e}"
            return

    def correct_image(self, *args):
        # ... (Logik wie zuvor) ...
        if len(self.image.points) != 4:
            self.info.text = "Bitte genau 4 Punkte auswählen"
            return
        
        if not self.filename or not exists(self.filename):
            self.info.text = "Fehler: Zuerst Foto aufnehmen!"
            return

        app_data_path = App.get_running_app().user_data_dir
        korrigiert_filename = join(app_data_path, "korrigiert.png")

        try:
            # 1. Bild öffnen
            img = PILImage.open(self.filename)
            
            # 2. Kivy-Koordinaten auf Widget-Dimensionen skalieren
            ratio_x = img.width / self.image.width
            ratio_y = img.height / self.image.height
            
            scaled_points = []
            for x_kivy, y_kivy in self.image.points:
                x_rel = x_kivy - self.image.x
                y_rel = y_kivy - self.image.y
                x_img = x_rel * ratio_x
                y_img = y_rel * ratio_y
                scaled_points.append((x_img, y_img))


            # 3. Bestimme die Bounding Box des Zuschneidebereichs (Min/Max der skalierten Punkte)
            xs = [p[0] for p in scaled_points]
            ys = [p[1] for p in scaled_points]

            left = int(min(xs))
            right = int(max(xs))
            top_kivy_pixel = int(max(ys))
            bottom_kivy_pixel = int(min(ys))

            # Konvertierung zu PIL (top, bottom)
            pil_top = img.height - top_kivy_pixel
            pil_bottom = img.height - bottom_kivy_pixel 
            
            # 4. Überprüfung des gültigen Zuschneidebereichs
            if left >= right or pil_top >= pil_bottom:
                 self.info.text = "Fehler bei Koordinaten: Ungültige Zuschneide-Box (Punkte zu nah oder falsch)."
                 return
            
            # 5. Zuschneiden (Bounding Box)
            cropped = img.crop((left, pil_top, right, pil_bottom))

            # 6. Neuskalierung/Entzerrung (einfache Skalierung als Platzhalter)
            corrected = cropped.resize((400, 600))

            # 7. Speichern und Anzeigen
            corrected.save(korrigiert_filename)

            self.image.source = korrigiert_filename
            self.image.reload()
            
            self.image.points.clear()
            self.image.canvas.after.clear()
            self.info.text = "Korrektur angewendet"
            
        except Exception as e:
            self.info.text = f"Fehler bei Korrektur: {e}"
            
CameraApp().run()
