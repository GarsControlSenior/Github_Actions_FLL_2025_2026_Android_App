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
from os.path import join, exists # join und exists für Pfade hinzugefügt
from PIL import Image as PILImage

# Hinweis: Pillow (PIL) muss in buildozer.spec als Requirement enthalten sein.

class TouchImage(Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.points = []

    def on_touch_down(self, touch):
        # Nur reagieren, wenn der Touch auf dem Widget ist und weniger als 4 Punkte gesetzt sind
        if self.collide_point(*touch.pos) and len(self.points) < 4:
            self.points.append((touch.x, touch.y))
            self.redraw_shapes()
            return True 
        
        return super().on_touch_down(touch)

    def redraw_shapes(self):
        # Lösche vorherige Zeichnungen
        self.canvas.after.clear()
        if not self.points:
            return

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
        
        # 1. Haupt-Widget: Enthält entweder die Kamera oder das Bild (nimmt 70% des Platzes ein)
        self.main_content = BoxLayout(orientation="vertical", size_hint_y=0.7)
        root.add_widget(self.main_content)
        
        # 2. Steuerungselemente (Buttons und Label, nehmen 30% des Platzes ein)
        self.controls = BoxLayout(orientation="vertical", size_hint_y=0.3)
        root.add_widget(self.controls)

        # Widgets initialisieren
        self.camera = Camera(play=False, resolution=(640, 480))
        self.image = TouchImage(allow_stretch=True, keep_ratio=True)
        self.filename = "" # Initialisiere den Dateinamen

        # UI-Elemente zu Controls hinzufügen
        btn_photo = Button(text="Foto aufnehmen", size_hint_y=0.3)
        btn_photo.bind(on_press=self.take_photo)
        self.controls.add_widget(btn_photo)

        btn_fix = Button(text="Korrektur anwenden", size_hint_y=0.3)
        btn_fix.bind(on_press=self.correct_image)
        self.controls.add_widget(btn_fix)

        self.info = Label(text="Kamera wird gestartet...", size_hint_y=0.4)
        self.controls.add_widget(self.info)
        
        # Beim Start: Nur die Kamera anzeigen
        self.main_content.add_widget(self.camera)
        self.camera.play = True
        self.info.text = "Kamera läuft."

        return root

    def take_photo(self, *args):
        try:
            # Absoluten Pfad im privaten App-Speicher definieren
            app_data_path = App.get_running_app().user_data_dir 
            self.filename = join(app_data_path, "foto.png") 
            
            # Foto aufnehmen
            self.camera.export_to_png(self.filename)
            
            # Kamera stoppen und aus dem Layout entfernen
            self.camera.play = False
            self.main_content.remove_widget(self.camera)

            # TouchImage mit dem neuen Bild hinzufügen
            self.image.source = self.filename
            self.image.reload()
            
            self.main_content.clear_widgets() # Platzhalter leeren
            self.main_content.add_widget(self.image)

            self.image.points.clear()
            self.image.canvas.after.clear()
            self.info.text = "4 Punkte antippen"
            
        except Exception as e:
            self.info.text = f"Fehler beim Foto: {e}"
            return

    def correct_image(self, *args):
        if len(self.image.points) != 4:
            self.info.text = "Bitte genau 4 Punkte auswählen"
            return
        
        # Prüfen, ob das Foto existiert, bevor PIL es öffnet
        if not self.filename or not exists(self.filename):
            self.info.text = "Fehler: Zuerst Foto aufnehmen!"
            return

        app_data_path = App.get_running_app().user_data_dir
        korrigiert_filename = join(app_data_path, "korrigiert.png")

        try:
            # 1. Punkte-Koordinaten auslesen (Kivy-Koordinaten)
            xs = [p[0] for p in self.image.points]
            ys = [p[1] for p in self.image.points]

            # 2. PIL-Bild öffnen
            img = PILImage.open(self.filename)
            
            # 3. Zuschneiden (Bounding Box)
            # Kivy Y (unten-links) muss zu PIL Y (oben-links) konvertiert werden
            left, right = int(min(xs)), int(max(xs))
            top_kivy, bottom_kivy = int(max(ys)), int(min(ys)) # max/min vertauschen, da Kivy y-unten-links
            
            # Invertierung für PIL:
            # PIL crop erwartet (left, top, right, bottom) (top ist Y=0)
            cropped = img.crop((left, img.height - top_kivy, right, img.height - bottom_kivy))

            # 4. Neuskalierung/Entzerrung (hier: einfache Skalierung)
            corrected = cropped.resize((400, 600)) # HIER KÖNNTE SPÄTER DIE PERSPEKTIVKORREKTUR ERFOLGEN

            # 5. Speichern und Anzeigen
            corrected.save(korrigiert_filename)

            self.image.source = korrigiert_filename
            self.image.reload()
            
            self.image.points.clear()
            self.image.canvas.after.clear()
            self.info.text = "Korrektur angewendet"
            
        except Exception as e:
            self.info.text = f"Fehler bei Korrektur: {e}"
            
CameraApp().run()
