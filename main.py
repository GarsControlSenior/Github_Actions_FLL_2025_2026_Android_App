import math
from os.path import join

from kivy.app import App
from kivy.uix.image import Image
from kivy.utils import platform
from kivy.clock import mainthread

from PIL import Image as PILImage
from PIL import ImageDraw

# Android
if platform == "android":
    from jnius import autoclass
    from android.permissions import request_permissions, Permission
    from android import activity


class MainApp(App):

    def build(self):
        self.img = Image(allow_stretch=True, keep_ratio=True)

        if platform == "android":
            activity.bind(on_activity_result=self.on_activity_result)
            self.photo_uri = None
            self.request_camera_permission()

        return self.img

    # -------------------------------------------------
    # Kamera-Berechtigung
    # -------------------------------------------------
    def request_camera_permission(self):
        request_permissions([Permission.CAMERA], self.on_permission)

    def on_permission(self, permissions, grants):
        if grants and grants[0]:
            self.open_camera()

    # -------------------------------------------------
    # Kamera öffnen
    # -------------------------------------------------
    def open_camera(self):
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Intent = autoclass("android.content.Intent")
        MediaStore = autoclass("android.provider.MediaStore")
        ContentValues = autoclass("android.content.ContentValues")

        activity_inst = PythonActivity.mActivity
        resolver = activity_inst.getContentResolver()

        values = ContentValues()
        values.put(MediaStore.Images.Media.MIME_TYPE, "image/jpeg")

        self.photo_uri = resolver.insert(
            MediaStore.Images.Media.EXTERNAL_CONTENT_URI,
            values
        )

        intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        intent.putExtra(MediaStore.EXTRA_OUTPUT, self.photo_uri)
        activity_inst.startActivityForResult(intent, 1234)

    # -------------------------------------------------
    # Kamera-Ergebnis
    # -------------------------------------------------
    @mainthread
    def on_activity_result(self, request, result, intent):
        if request == 1234 and result == -1:
            self.copy_and_draw_arrow(self.photo_uri)

    # -------------------------------------------------
    # Bild kopieren + Nordpfeil zeichnen
    # -------------------------------------------------
    def copy_and_draw_arrow(self, uri):
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        context = PythonActivity.mActivity
        resolver = context.getContentResolver()

        dest = join(self.user_data_dir, "photo.jpg")

        inp = resolver.openInputStream(uri)
        FileOutputStream = autoclass("java.io.FileOutputStream")
        out = FileOutputStream(dest)

        buffer = bytearray(4096)
        while True:
            r = inp.read(buffer)
            if r == -1:
                break
            out.write(buffer, 0, r)

        inp.close()
        out.close()

        # DEMO: Norden = 0°
        out_img = self.draw_north_arrow(dest, heading=0.0)

        self.img.source = out_img
        self.img.reload()

    # -------------------------------------------------
    # Nordpfeil oben rechts
    # -------------------------------------------------
    def draw_north_arrow(self, path, heading):
        img = PILImage.open(path).convert("RGBA")
        draw = ImageDraw.Draw(img)

        w, h = img.size
        cx, cy = w - 120, 120
        length = 80

        angle = math.radians(-heading)
        x2 = cx + length * math.sin(angle)
        y2 = cy - length * math.cos(angle)

        draw.line((cx, cy, x2, y2),
                  fill=(255, 0, 0, 255),
                  width=6)

        out = join(self.user_data_dir, "photo_with_arrow.png")
        img.save(out)
        return out


if __name__ == "__main__":
    MainApp().run()
