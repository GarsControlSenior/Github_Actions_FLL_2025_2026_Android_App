from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.camera import Camera
from kivy.uix.image import Image
from kivy.graphics import Color, Ellipse, Line
import math
from kivy.uix.label import Label
from PIL import Image as PILImage

# Imports für Android-Berechtigungen
try:
    from android.permissions import request_permissions, Permission
    PERMISSIONS = [Permission.CAMERA, Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE]
except ImportError:
    request_permissions = None
    PERMISSIONS = []

class TouchImage(Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.points = []

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and len(self.points) < 4:
            self.points.append(touch.pos)
            self.redraw_shapes()
        return super().on_touch_down(touch)

    def redraw_shapes(self):
        """Zeichne Punkte und automatisch sortierte Linien (Rechteck ohne Überschneidungen)"""
        self.canvas.after.clear()
        if not self.points:
            return

        with self.canvas.after:
            # Punkte zeichnen (grün)
            Color(0, 1, 0)
            for x, y in self.points:
                Ellipse(pos=(x - 8, y - 8), size=(16, 16))

            # Linien nur wenn mindestens 2 Punkte
            if len(self.points) >= 2:
                # Sortiere Punkte nach Winkel um Schwerpunkt (erzeugt Polygon ohne Überschneidungen)
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
                    # Polygon schließen (verbinde auch letzten mit ersten Punkt)
                    Line(points=pts + [pts[0], pts[1]], width=3)
                else:
                    Line(points=pts, width=3)

    def get_sorted_points(self):
        """Gibt Punkte sortiert zurück (für Zuschnitt)"""
        if len(self.points) != 4:
            return None
        
        cx = sum(p[0] for p in self.points) / 4
        cy = sum(p[1] for p in self.points) / 4

        def ang(p):
            return math.atan2(p[1] - cy, p[0] - cx)

        return sorted(self.points, key=ang)


class CameraApp(App):
    def build(self):
        # Berechtigungen beim Start anfordern
        if request_permissions:
            request_permissions(PERMISSIONS)

        # Root Layout
        self.root_layout = BoxLayout(orientation="vertical")

        # Info Label oben
        self.info = Label(text="Bitte mache ein Foto", size_hint_y=0.1, bold=True)
        self.root_layout.add_widget(self.info)

        # Kamera mit Rotation (90 Grad nach rechts = -90)
        self.camera = Camera(play=True, resolution=(640, 480))
        self.camera.rotation = -90  # 90 Grad nach rechts
        self.camera.size_hint_y = 0.7  # Kamera füllt 70% der Höhe
        self.root_layout.add_widget(self.camera)

        # Buttons
        self.btn_layout = BoxLayout(size_hint_y=0.2, spacing=5, padding=5)
        
        btn_photo = Button(text="Foto aufnehmen")
        btn_photo.bind(on_press=self.take_photo)
        self.btn_layout.add_widget(btn_photo)

        btn_correct = Button(text="Zuschnitt anwenden")
        btn_correct.bind(on_press=self.correct_image)
        self.btn_layout.add_widget(btn_correct)

        btn_reset = Button(text="Zurück")
        btn_reset.bind(on_press=self.reset)
        self.btn_layout.add_widget(btn_reset)

        self.root_layout.add_widget(self.btn_layout)

        # Bild-Widget (initial versteckt)
        self.image = TouchImage(allow_stretch=True, keep_ratio=False)
        self.image.size_hint_y = 0.7
        # Nicht hinzufügen, wird bei Bedarf angezeigt
        
        return self.root_layout

    def take_photo(self, *args):
        """Foto aufnehmen und Vollbild-Anzeige zeigen"""
        self.filename = "foto.png"
        try:
            self.camera.export_to_png(self.filename)
            
            # Verstecke Kamera und Buttons, zeige Bild
            self.root_layout.remove_widget(self.camera)
            self.root_layout.remove_widget(self.btn_layout)
            
            # Füge Bild hinzu
            self.image.source = self.filename
            self.image.reload()
            self.image.points = []
            self.image.redraw_shapes()
            self.root_layout.insert_widget(1, self.image)  # Nach Info Label
            
            self.info.text = "Bitte wählen Sie 4 Punkte aus"
        except Exception as e:
            self.info.text = f"Fehler beim Foto: {str(e)}"

    def correct_image(self, *args):
        """Einfaches Zuschneiden und Skalieren (ohne OpenCV)"""
        if len(self.image.points) != 4:
            self.info.text = f"Bitte genau 4 Punkte auswählen (aktuell: {len(self.image.points)})"
            return

        try:
            # Sortierte Punkte holen
            sorted_points = self.image.get_sorted_points()

            # Berechne Bounding Box
            xs = [p[0] for p in sorted_points]
            ys = [p[1] for p in sorted_points]
            left, right = int(min(xs)), int(max(xs))
            top, bottom = int(min(ys)), int(max(ys))

            # Bild laden und zuschneiden
            img = PILImage.open(self.filename)
            
            # Zuschneiden (je nach Bild-Rotation anpassen)
            width = right - left
            height = bottom - top
            
            if width < 50 or height < 50:
                self.info.text = "Punkte zu nah beieinander"
                return
            
            cropped = img.crop((left, top, right, bottom))

            # Skalieren (Standardgröße)
            corrected = cropped.resize((400, 600), PILImage.Resampling.LANCZOS)

            # Speichern und anzeigen
            corrected.save("korrigiert.png")

            self.image.source = "korrigiert.png"
            self.image.reload()
            self.image.points = []
            self.image.redraw_shapes()

            self.info.text = "Zuschnitt abgeschlossen!"
        except Exception as e:
            self.info.text = f"Fehler: {str(e)}"

    def reset(self, *args):
        """Zurück zum Kamera-View"""
        # Entferne Bild und Buttons
        if self.image.parent:
            self.root_layout.remove_widget(self.image)
        if self.btn_layout.parent:
            self.root_layout.remove_widget(self.btn_layout)
        
        # Zeige Kamera und Buttons wieder
        self.camera.play = True
        self.root_layout.insert_widget(1, self.camera)  # Nach Info Label
        self.root_layout.add_widget(self.btn_layout)
        
        self.image.source = ""
        self.image.points = []
        self.image.redraw_shapes()
        self.info.text = "Bitte mache ein Foto"


CameraApp().run()
