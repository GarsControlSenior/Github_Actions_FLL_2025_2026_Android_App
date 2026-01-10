import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.camera import Camera
from kivy.uix.image import Image
from kivy.graphics import Color, Ellipse, Line
import math
from kivy.uix.label import Label
from kivy.core.window import Window # Hinzugefügt für bessere Kamera-Handhabung
from PIL import Image as PILImage

# Hinweis: Für die Bildverarbeitung wird die Pillow-Bibliothek benötigt (in spec korrigiert).

class TouchImage(Image):
    # Diese Klasse bleibt unverändert, da die Zeichenlogik funktioniert.
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.points = []

    def on_touch_down(self, touch):
        # Wir wollen nur auf den TouchImage-Bereich reagieren
        if self.collide_point(*touch.pos) and len(self.points) < 4:
            # Touch-Koordinaten relativ zum Widget
            x_rel = touch.x - self.x
            y_rel = touch.y - self.y
            self.points.append((touch.x, touch.y))
            self.redraw_shapes()
            return True # Wichtig: Signalisiert, dass der Touch verarbeitet wurde
        
        return super().on_touch_down(touch)

    def redraw_shapes(self):
        # Lösche vorherige Zeichnungen
        self.canvas.after.clear()
        if not self.points:
            return

        # Zeichnet die Punkte und das sortierte Polygon wie zuvor
        with self.canvas.after:
            # Punkte zeichnen
            Color(1, 0, 0)
            for x, y in self.points:
                Ellipse(pos=(x - 6, y - 6), size=(12, 12))

            # Linien in sinnvoller Reihenfolge zeichnen (nach Winkel um Schwerpunkt sortieren)
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
                    # Polygon schließen
                    Line(points=pts + pts[0:2], width=2)
                else:
                    Line(points=pts, width=2)

class CameraApp(App):
    def build(self):
        root = BoxLayout(orientation="vertical")
        
        # 1. Haupt-Widget: Enthält entweder die Kamera oder das Bild
        self.main_content = BoxLayout(orientation="vertical", size_hint_y=0.7)
        root.add_widget(self.main_content)
        
        # 2. Steuerungselemente (Buttons)
        self.controls = BoxLayout(orientation="vertical", size_hint_y=0.3)
        root.add_widget(self.controls)

        # A. Kamera-Vorschau initialisieren (später in main_content hinzugefügt)
        # play=False, bis wir wissen, dass alles geladen ist
        self.camera = Camera(play=False, resolution=(640, 480))
        
        # B. TouchImage initialisieren
        self.image = TouchImage(allow_stretch=True, keep_ratio=True)
        
        # UI-Elemente
        btn_photo = Button(text="Foto aufnehmen", size_hint_y=0.3)
        btn_photo.bind(on_press=self.take_photo)
        self.controls.add_widget(btn_photo)

        btn_fix = Button(text="Korrektur anwenden", size_hint_y=0.3)
        btn_fix.bind(on_press=self.correct_image)
        self.controls.add_widget(btn_fix)

        self.info = Label(text="Kamera wird gestartet...", size_hint_y=0.4)
        self.controls.add_widget(self.info)
        
        # Initial die Kamera hinzufügen und starten
        self.main_content.add_widget(self.camera)
        self.camera.play = True # Kamera jetzt starten

        return root

    def take_photo(self, *args):
        # 1. Dateinamen setzen und Foto aufnehmen
        self.filename = "foto.png"
        
        # HINWEIS: Manchmal muss man eine kurze Verzögerung einbauen,
        # um sicherzustellen, dass die Kamera bereit ist.
        try:
            self.camera.export_to_png(self.filename)
        except Exception as e:
            self.info.text = f"Fehler beim Speichern: {e}"
            return

        # 2. Kamera stoppen und entfernen
        self.camera.play = False
        self.main_content.remove_widget(self.camera)

        # 3. TouchImage mit dem aufgenommenen Bild hinzufügen
        self.image.source = self.filename
        self.image.reload()
        
        # 4. Neu setzen des Image Widgets
        self.main_content.clear_widgets() # Sicherstellen, dass alles entfernt ist
        self.main_content.add_widget(self.image)

        self.image.points.clear()
        self.image.canvas.after.clear()
        self.info.text = "4 Punkte antippen"

    def correct_image(self, *args):
        # HINWEIS: Hier ist der Ort für die Perspektivkorrektur-Logik,
        # die wir später besprochen haben. Im Moment ist die vereinfachte Logik aktiv.
        
        if len(self.image.points) != 4:
            self.info.text = "Bitte genau 4 Punkte auswählen"
            return
        
        # ... (Logik zur perspektivischen Korrektur hier einfügen) ...
        # Für den Test bleibt die Logik einfach:
        
        try:
            xs = [p[0] for p in self.image.points]
            ys = [p[1] for p in self.image.points]

            # Kivy-Koordinaten (unten-links) müssen zu PIL-Koordinaten (oben-links)
            left, right = int(min(xs)), int(max(xs))
            bottom_kivy, top_kivy = int(min(ys)), int(max(ys))
            
            img = PILImage.open(self.filename)
            
            # Y-Achse invertieren: (img.height - top_kivy) bis (img.height - bottom_kivy)
            cropped = img.crop((left, img.height - top_kivy, right, img.height - bottom_kivy))

            # leichte Entzerrung durch Neuskalierung
            corrected = cropped.resize((400, 600))

            corrected.save("korrigiert.png")

            self.image.source = "korrigiert.png"
            self.image.reload()

            self.image.points.clear()
            self.image.canvas.after.clear()
            self.info.text = "Korrektur angewendet"
            
        except Exception as e:
            self.info.text = f"Fehler bei Korrektur: {e}"
            
CameraApp().run()
