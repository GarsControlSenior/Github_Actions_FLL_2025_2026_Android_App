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

# Android-Imports NUR wenn Android
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
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.points = []

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and len(self.points) < 4:
            self.points.append(touch.pos)
            self.draw()
        return super().on_touch_down(touch)

    def draw(self):
        self.canvas.after.clear()
        with self.canvas.after:
            Color(0, 1, 0)
            for x, y in self.points:
                Ellipse(pos=(x - 8, y - 8), size=(16, 16))

            if len(self.points) >= 2:
                cx = sum(p[0] for p in self.points) / len(self.points)
                cy = sum(p[1] for p in self.points) / len(self.points)

                ordered = sorted(
                    self.points,
                    key=lambda p: math.atan2(p[1] - cy, p[0] - cx)
                )

                pts = []
                for p in ordered:
                    pts.extend(p)

                Line(points=pts + pts[:2], width=3)

    def get_points(self):
        if len(self.points) != 4:
            return None

        cx = sum(p[0] for p in self.points) / 4
        cy = sum(p[1] for p in self.points) / 4

        return sorted(
            self.points,
            key=lambda p: math.atan2(p[1] - cy, p[0] - cx)
        )


class CameraApp(App):

    def build(self):
        self.root = BoxLayout(orientation="vertical")

        self.info = Label(text="Starte Kamera …", size_hint_y=0.1)
        self.root.add_widget(self.info)

        self.image = TouchImage(allow_stretch=True, keep_ratio=False)
        self.root.add_widget(self.image)

        btns = BoxLayout(size_hint_y=0.15)

        btn_crop = Button(text="Zuschneiden")
        btn_crop.bind(on_press=self.crop)
        btns.add_widget(btn_crop)

        btn_new = Button(text="Neues Foto")
        btn_new.bind(on_press=self.start_camera)
        btns.add_widget(btn_new)

        self.root.add_widget(btns)

        # Kamera erst NACH App-Start öffnen
        Clock.schedule_once(self.init_android, 0.5)

        return self.root

    def init_android(self, *args):
        if platform != "android":
            self.info.text = "Nur auf Android verfügbar"
            return

        request_permissions(
            [Permission.CAMERA, Permission.WRITE_EXTERNAL_STORAGE],
            self.on_permissions
        )

    def on_permissions(self, permissions, grants):
        if all(grants):
            Clock.schedule_once(lambda dt: self.start_camera(), 0.5)
        else:
            self.info.text = "Kamera-Berechtigung verweigert"

    def start_camera(self, *args):
        self.photo_path = os.path.join(
            Environment.getExternalStoragePublicDirectory(
                Environment.DIRECTORY_PICTURES
            ).getAbsolutePath(),
            "kivy_photo.jpg"
        )

        file = File(self.photo_path)
        uri = Uri.fromFile(file)

        intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        intent.putExtra(MediaStore.EXTRA_OUTPUT, uri)

        activity.bind(on_activity_result=self.on_result)
        activity.startActivityForResult(intent, 999)

        self.info.text = "Foto aufnehmen"

    def on_result(self, requestCode, resultCode, intent):
        if requestCode == 999 and os.path.exists(self.photo_path):
            self.image.source = self.photo_path
            self.image.reload()
            self.image.points.clear()
            self.image.draw()
            self.info.text = "4 Punkte auswählen"

    def crop(self, *args):
        pts = self.image.get_points()
        if not pts:
            self.info.text = "Bitte 4 Punkte setzen"
            return

        xs, ys = zip(*pts)
        img = PILImage.open(self.photo_path)

        cropped = img.crop((min(xs), min(ys), max(xs), max(ys)))
        cropped.save(self.photo_path)

        self.image.source = self.photo_path
        self.image.reload()
        self.image.points.clear()
        self.image.draw()

        self.info.text = "Zugeschnitten"


CameraApp().run()
