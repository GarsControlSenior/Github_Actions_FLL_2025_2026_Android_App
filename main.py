from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.camera import Camera
from kivy.uix.image import Image
from kivy.graphics import Color, Ellipse, Line
import math
from kivy.uix.label import Label
from PIL import Image as PILImage
import cv2
import numpy as np

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
        """Gibt Punkte sortiert zurück (für Perspektivkorrektur)"""
        if len(self.points) != 4:
            return None
        
        cx = sum(p[0] for p in self.points) / 4
        cy = sum(p[1] for p in self.points) / 4

        def ang(p):
            return math.atan2(p[1] - cy, p[0] - cx)

        return sorted(self.points, key=ang)


class CameraApp(App):
    def build(self):
        root = BoxLayout(orientation="vertical")

        # Info Label oben
        self.info = Label(text="Bitte mache ein Foto", size_hint_y=0.1, bold=True)
        root.add_widget(self.info)

        # Kamera
        self.camera = Camera(play=True, resolution=(640, 480))
        root.add_widget(self.camera)

        # Buttons
        btn_layout = BoxLayout(size_hint_y=0.15, spacing=5, padding=5)
        
        btn_photo = Button(text="Foto aufnehmen")
        btn_photo.bind(on_press=self.take_photo)
        btn_layout.add_widget(btn_photo)

        btn_correct = Button(text="Entzerrung beginnen")
        btn_correct.bind(on_press=self.correct_image)
        btn_layout.add_widget(btn_correct)

        btn_reset = Button(text="Zurück")
        btn_reset.bind(on_press=self.reset)
        btn_layout.add_widget(btn_reset)

        root.add_widget(btn_layout)

        # Bild-Widget (für angeklickte Punkte)
        self.image = TouchImage(allow_stretch=True, keep_ratio=True)
        root.add_widget(self.image)

        return root

    def take_photo(self, *args):
        """Foto aufnehmen und anzeigen"""
        self.filename = "foto.png"
        try:
            self.camera.export_to_png(self.filename)
            self.image.source = self.filename
            self.image.reload()
            
            # Punkte zurücksetzen
            self.image.points = []
            self.image.redraw_shapes()
            
            self.info.text = "Bitte wählen Sie 4 Punkte aus"
        except Exception as e:
            self.info.text = f"Fehler beim Foto: {str(e)}"

    def correct_image(self, *args):
        """Perspektivkorrektur mit OpenCV"""
        if len(self.image.points) != 4:
            self.info.text = f"Bitte genau 4 Punkte auswählen (aktuell: {len(self.image.points)})"
            return

        try:
            # Sortierte Punkte holen (kein Überschneiden)
            sorted_points = self.image.get_sorted_points()
            src_points = np.array(sorted_points, dtype=np.float32)

            # Berechne Bounding Box für Zielgröße
            xs = [p[0] for p in sorted_points]
            ys = [p[1] for p in sorted_points]
            width = int(max(xs) - min(xs))
            height = int(max(ys) - min(ys))

            # Falls Dimensionen zu klein
            if width < 50 or height < 50:
                self.info.text = "Punkte zu nah beieinander"
                return

            # Zielrechteck (Draufsicht)
            dst_points = np.array([
                [0, 0],
                [width, 0],
                [width, height],
                [0, height]
            ], dtype=np.float32)

            # Perspektive-Transformationsmatrix berechnen
            matrix = cv2.getPerspectiveTransform(src_points, dst_points)

            # Bild laden und transformieren
            img_cv = cv2.imread(self.filename)
            if img_cv is None:
                self.info.text = "Fehler beim Laden des Fotos"
                return

            warped = cv2.warpPerspective(img_cv, matrix, (width, height))

            # Speichern und anzeigen
            cv2.imwrite("korrigiert.png", warped)

            self.image.source = "korrigiert.png"
            self.image.reload()
            self.image.points = []
            self.image.redraw_shapes()

            self.info.text = "Entzerrung abgeschlossen!"
        except Exception as e:
            self.info.text = f"Fehler: {str(e)}"

    def reset(self, *args):
        """Zurück zum Kamera-View"""
        self.camera.play = True
        self.image.source = ""
        self.image.points = []
        self.image.redraw_shapes()
        self.info.text = "Bitte mache ein Foto"


CameraApp().run()
