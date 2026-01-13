from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.graphics import Color, Ellipse, Line
from kivy.clock import Clock

import math
import os
from PIL import Image as PILImage

# Android
from android.permissions import request_permissions, Permission
from android.activity import activity
from jnius import autoclass

# Android Klassen
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
            self.redraw()
        return super().on_touch_down(touch)

    def redraw(self):
        self.canvas.after.clear()
        if not self.points:
            return

        with self.canvas.after:
            Color(0, 1, 0)
            for x, y in self.points:
                Ellipse(pos=(x - 8, y - 8), size=(16, 16))

            if len(self.points) >= 2:
                cx = sum(p[0] for p in self.points) / len(self.points)
                cy = sum(p[1] for p in self.points) / len(self.points)

                def ang(p):
                    return math.atan2(p[1] - cy, p[0] - cx)

                ordered = sorted(self.points, key=ang)
                pts = []
                for p in ordered:
                    pts.extend(p)

                Line(points=pts + pts[:2], width=3)

    def sorted_points(self):
        if len(self.points) != 4:
            return None

        cx = sum(p[0] for p in self.points) / 4
        cy = sum(p[1] for p in self.points) / 4

        def ang(p):
            return math.atan2(p[1] - cy, p[0] - cx)

        return sorted(self.points, key=ang)


class CameraApp(App):

    def build(self):
        request_permissions(
            [Permission.CAMERA, Permission.WRITE_EXTERNAL_STORAGE],
            self.permission_callback
        )

        self.root = BoxLayout(orientation="vertical")

        self.info = Label(text="Kamera wird gestartet ...", size_hint_y=0.1)
        self.root.add_widget(self.info)

        self.image = TouchImage(allow_stretch=True, keep_ratio=False)
        self.root.add_widget(self.image)

        self.buttons = BoxLayout(size_hint_y=0.15)

        btn_crop = Button(text="Zuschneiden")
        btn_crop.bind(on_press=self.crop_image)
        self.buttons.add_widget(btn_crop)

        btn_reset = Button(text="Neues Foto")
        btn_reset.bind(on_press=self.open_camera)
        self.buttons.add_widget(btn_reset)

        self.root.add_widget(self.buttons)

        return self.root

    def permission_callback(self, permissions, grants):
        if all(grants):
            Clock.schedule_once(lambda dt: self.open_camera(), 0.5)
        else:
            self.info.text = "Kamera-Berechtigung verweigert"

    def open_camera(self, *args):
        self.photo_path = os.path.join(
            Environment.getExternalStoragePublicDirectory(
                Environment.DIRECTORY_PICTURES
            ).getAbsolutePath(),
            "kivy_camera_photo.jpg"
        )

        file = File(self.photo_path)
        uri = Uri.fromFile(file)

        intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        intent.putExtra(MediaStore.EXTRA_OUTPUT, uri)

        activity.startActivityForResult(intent, 123)
        activity.bind(on_activity_result=self.on_activity_result)

        self.info.text = "Foto aufnehmen ..."

    def on_activity_result(self, requestCode, resultCode, intent):
        if requestCode == 123 and os.path.exists(self.photo_path):
            self.image.source = self.photo_path
            self.image.reload()
            self.image.points = []
            self.image.redraw()
            self.info.text = "Bitte 4 Punkte auswählen"

    def crop_image(self, *args):
        pts = self.image.sorted_points()
        if not pts:
            self.info.text = "Bitte genau 4 Punkte setzen"
            return

        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]

        left, right = int(min(xs)), int(max(xs))
        top, bottom = int(min(ys)), int(max(ys))

        if right - left < 50 or bottom - top < 50:
            self.info.text = "Punkte zu nah"
            return

        img = PILImage.open(self.photo_path)
        cropped = img.crop((left, top, right, bottom))
        cropped.save(self.photo_path)

        self.image.source = self.photo_path
        self.image.reload()
        self.image.points = []
        self.image.redraw()

        self.info.text = "Fertig zugeschnitten"


CameraApp().run()
