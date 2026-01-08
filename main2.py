from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.camera import Camera
from kivy.uix.image import Image
from kivy.graphics import Color, Ellipse, Line
import math
from kivy.uix.label import Label
from PIL import Image as PILImage

# Hinweis: Für die Bildverarbeitung wird die Pillow-Bibliothek benötigt.

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
        # Lösche vorherige Zeichnungen und zeichne Punkte + geordnete Linien (Polygon)
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
        #return super().on_touch_down(touch)


class CameraApp(App):
    def build(self):
        root = BoxLayout(orientation="vertical")

        self.camera = Camera(play=True, resolution=(640, 480))
        root.add_widget(self.camera)

        btn_photo = Button(text="Foto aufnehmen", size_hint_y=0.15)
        btn_photo.bind(on_press=self.take_photo)
        root.add_widget(btn_photo)

        self.image = TouchImage(allow_stretch=True, keep_ratio=True)
        root.add_widget(self.image)

        btn_fix = Button(text="Korrektur anwenden", size_hint_y=0.15)
        btn_fix.bind(on_press=self.correct_image)
        root.add_widget(btn_fix)

        self.info = Label(text="Foto aufnehmen", size_hint_y=0.1)
        root.add_widget(self.info)

        return root

    def take_photo(self, *args):
        self.filename = "foto.png"
        self.camera.export_to_png(self.filename)

        self.image.source = self.filename
        self.image.reload()

        self.image.points.clear()
        self.image.canvas.after.clear()

        self.info.text = "4 Punkte antippen"

    def correct_image(self, *args):
        if len(self.image.points) != 4:
            self.info.text = "Bitte genau 4 Punkte auswählen"
            return

        # Touchpunkte → Bounding Box
        xs = [p[0] for p in self.image.points]
        ys = [p[1] for p in self.image.points]

        left, right = int(min(xs)), int(max(xs))
        bottom, top = int(min(ys)), int(max(ys))

        img = PILImage.open(self.filename)

        # Zuschneiden = echte Bildänderung
        cropped = img.crop((left, img.height - top, right, img.height - bottom))

        # leichte Entzerrung durch Neuskalierung
        corrected = cropped.resize((400, 600))

        corrected.save("korrigiert.png")

        self.image.source = "korrigiert.png"
        self.image.reload()

        self.info.text = "Korrektur angewendet"


CameraApp().run()