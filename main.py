import math
from os.path import join

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.utils import platform
from kivy.clock import mainthread

from PIL import Image as PILImage
from PIL import ImageDraw

# Android Imports
if platform == "android":
    from jnius import autoclass
    from android.permissions import request_permissions, Permission
    from android import activity


# -------------------------------------------------
# Vorschau-Screen
# -------------------------------------------------
class PreviewScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)

        self.img = Image(allow_stretch=True, keep_ratio=True)
        btn_back = Button(text="Neues Foto", size_hint_y=0.2)
        btn_back.bind(on_press=self.back)

        layout.add_widget(self.img)
        layout.add_widget(btn_back)
        self.add_widget(layout)

    def back(self, *args):
        self.manager.current = "camera"


# -------------------------------------------------
# App
# -------------------------------------------------
class ForschungApp(App):

    def build(self):
        self.sm = ScreenManager()

        # Kamera Screen
        cam_screen = Screen(name="camera")
        layout = BoxLayout(orientation="vertical", padding=40, spacing=20)

        title = Label(text="Forschung", font_size="24sp")
        btn_cam = Button(text="Foto aufnehmen", size_hint_y=0.25)
        btn_cam.bind(on_press=self.request_camera_permission)

        self.status = Label(text="Bereit")

        layout.add_widget(title)
        layout.add_widget(btn_cam)
        layout.add_widget(self.status)
        cam_screen.add_widget(layout)

        self.preview = PreviewScreen(name="preview")

        self.sm.add_widget(cam_screen)
        self.sm.add_widget(self.preview)

        if platform == "android":
            activity.bind(on_activity_result=self.on_activity_result)
            self.photo_uri = None

        return self.sm

    # -------------------------------------------------
    # Kamera Permission (NUR KAMERA)
    # -------------------------------------------------
    def request_camera_permission(self, *args):
        if platform != "android":
            return

        request_permissions(
            [Permission.CAMERA],
            self.on_permission_result
        )

    def on_permission_result(self, permissions, grants):
        if grants and grants[0]:
            self.open_camera()
        else:
            self.status.text = "Kamera-Berechtigung verweigert"

    # -------------------------------------------------
    # Native Android Kamera
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
        activity_inst.startActivityForResult(intent, 1001)

    @mainthread
    def on_activity_result(self, request_code, result_code, intent):
        if request_code == 1001 and result_code == -1:
            self.copy_to_local(self.photo_uri)

    # -------------------------------------------------
    # Bild lokal kopieren (App-interner Speicher)
    # -------------------------------------------------
    def copy_to_local(self, uri):
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        context = PythonActivity.mActivity
        resolver = context.getContentResolver()

        dest_path = join(self.user_data_dir, "photo.jpg")

        inp = resolver.openInputStream(uri)
        FileOutputStream = autoclass("java.io.FileOutputStream")
        out = FileOutputStream(dest_path)

        buffer = bytearray(4096)
        while True:
            r = inp.read(buffer)
            if r == -1:
                break
            out.write(buffer, 0, r)

        inp.close()
        out.close()

        # Demo-Nordrichtung (später Arduino BLE)
        heading = 0.0

        out_img = self.draw_north_arrow(dest_path, heading)

        self.preview.img.source = out_img
        self.preview.img.reload()
        self.sm.current = "preview"

    # -------------------------------------------------
    # Nordpfeil zeichnen
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

        out_path = join(self.user_data_dir, "photo_with_arrow.png")
        img.save(out_path)
        return out_path


if __name__ == "__main__":
    ForschungApp().run()
