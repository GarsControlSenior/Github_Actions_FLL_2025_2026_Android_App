from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.graphics import Color, Ellipse, Line
from kivy.clock import Clock
from kivy.utils import platform

import math
import os
from PIL import Image as PILImage

# Android-spezifische Imports
if platform == "android":
    from android.permissions import request_permissions, Permission
    from android.activity import activity
    from jnius import autoclass

    Intent = autoclass('android.content.Intent')
    MediaStore = autoclass('android.provider.MediaStore')
    File = autoclass('java.io.File')
    Environment = autoclass('android.os.Environment')
    Uri = autoclass('android.net.Uri')

class TouchImage(Image):
    """Bild-Widget, das Klicks registriert und Linien zwischen 4 Punkten zieht."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.points = []

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and len(self.points) < 4:
            # Speichere die Klick-Position relativ zum Widget
            self.points.append(touch.pos)
            self.draw()
        return super().on_touch_down(touch)

    def draw(self):
        self.canvas.after.clear()
        with self.canvas.after:
            Color(0, 1, 0, 1)  # Grün
            for x, y in self.points:
                Ellipse(pos=(x - 10, y - 10), size=(20, 20))

            if len(self.points) >= 2:
                # Punkte für die Linie sortieren (Uhrzeigersinn)
                ordered = self.get_ordered_points()
                pts = []
                for p in ordered:
                    pts.extend(p)
                Line(points=pts + pts[:2], width=2)

    def get_ordered_points(self):
        if not self.points:
            return []
        # Schwerpunkt berechnen für die Sortierung
        cx = sum(p[0] for p in self.points) / len(self.points)
        cy = sum(p[1] for p in self.points) / len(self.points)
        # Sortierung im Uhrzeigersinn, beginnend oben links
        return sorted(self.points, key=lambda p: math.atan2(p[1] - cy, p[0] - cx), reverse=True)

    def clear_points(self):
        self.points = []
        self.canvas.after.clear()

class CameraApp(App):
    def build(self):
        self.root = BoxLayout(orientation="vertical")
        
        # UI Elemente
        self.info = Label(text="Warte auf Kamera...", size_hint_y=0.1)
        self.root.add_widget(self.info)

        self.image = TouchImage(allow_stretch=True, keep_ratio=False)
        self.root.add_widget(self.image)

        btns = BoxLayout(size_hint_y=0.15)
        
        btn_crop = Button(text="Entzerren (Ortho)")
        btn_crop.bind(on_press=self.orthorectify)
        btns.add_widget(btn_crop)

        btn_reset = Button(text="Reset Punkte")
        btn_reset.bind(on_press=lambda x: self.image.clear_points())
        btns.add_widget(btn_reset)

        btn_new = Button(text="Neues Foto")
        btn_new.bind(on_press=self.start_camera_intent)
        btns.add_widget(btn_new)

        self.root.add_widget(btns)

        # Pfad für das temporäre Foto
        if platform == "android":
            self.photo_path = os.path.join(
                Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_PICTURES).getAbsolutePath(), 
                "ortho_temp.jpg"
            )
            Clock.schedule_once(self.init_android, 0.5)
        else:
            self.photo_path = "test_photo.jpg"
            self.info.text = "PC-Modus: Lade test_photo.jpg falls vorhanden"

        return self.root

    def init_android(self, *args):
        request_permissions([Permission.CAMERA, Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE], self.on_permissions)

    def on_permissions(self, permissions, grants):
        if all(grants):
            self.info.text = "Bereit. Foto aufnehmen!"
        else:
            self.info.text = "Berechtigungen fehlen!"

    def start_camera_intent(self, *args):
        if platform == "android":
            file = File(self.photo_path)
            uri = Uri.fromFile(file)
            intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
            intent.putExtra(MediaStore.EXTRA_OUTPUT, uri)
            activity.bind(on_activity_result=self.on_result)
            activity.startActivityForResult(intent, 999)
        else:
            self.info.text = "Kamera-Intent nur auf Android."

    def on_result(self, requestCode, resultCode, intent):
        if requestCode == 999:
            Clock.schedule_once(lambda dt: self.load_image(), 0.5)

    def load_image(self):
        if os.path.exists(self.photo_path):
            self.image.source = self.photo_path
            self.image.reload()
            self.image.clear_points()
            self.info.text = "4 Ecken im Uhrzeigersinn markieren"

    def orthorectify(self, *args):
        pts = self.image.get_ordered_points()
        if len(pts) != 4:
            self.info.text = "Fehler: Bitte 4 Punkte setzen!"
            return

        try:
            img = PILImage.open(self.photo_path)
            img_w, img_h = img.size

            # Umrechnung: Kivy Widget-Koordinaten -> Bild-Pixel-Koordinaten
            # Kivy: (0,0) links unten | PIL: (0,0) links oben
            w_w = self.image.width
            w_h = self.image.height

            real_pts = []
            for px, py in pts:
                # Korrektur der relativen Position im Widget
                rel_x = (px - self.image.x) / w_w
                rel_y = 1.0 - ((py - self.image.y) / w_h) # Y-Achse spiegeln
                real_pts.append((rel_x * img_w, rel_y * img_h))

            # Ziel-Dimensionen berechnen (Durchschnittliche Kantenlängen)
            width = int((math.dist(real_pts[0], real_pts[1]) + math.dist(real_pts[3], real_pts[2])) / 2)
            height = int((math.dist(real_pts[0], real_pts[3]) + math.dist(real_pts[1], real_pts[2])) / 2)

            # Transformation (PIL QUAD: oben-links, unten-links, unten-right, oben-rechts)
            # Unsere get_ordered_points liefert sie meist in dieser Logik.
            ortho = img.transform(
                (width, height),
                PILImage.QUAD,
                data=(
                    real_pts[0][0], real_pts[0][1], # oben links
                    real_pts[3][0], real_pts[3][1], # unten links
                    real_pts[2][0], real_pts[2][1], # unten rechts
                    real_pts[1][0], real_pts[1][1]  # oben rechts
                ),
                resample=PILImage.BICUBIC
            )

            ortho.save(self.photo_path)
            self.load_image()
            self.info.text = "Orthofoto erstellt!"
        except Exception as e:
            self.info.text = f"Fehler: {str(e)}"

if __name__ == "__main__":
    CameraApp().run()
