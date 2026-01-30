from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.graphics.texture import Texture
from kivy.clock import Clock

from jnius import autoclass, PythonJavaClass, java_method
from PIL import Image as PILImage, ImageDraw
import io

# Android Klassen
PythonActivity = autoclass('org.kivy.android.PythonActivity')
Intent = autoclass('android.content.Intent')
MediaStore = autoclass('android.provider.MediaStore')

class CameraResultListener(PythonJavaClass):
    __javainterfaces__ = ['org/kivy/android/PythonActivity$ActivityResultListener']

    def __init__(self, app):
        super().__init__()
        self.app = app

    @java_method('(IILandroid/content/Intent;)V')
    def onActivityResult(self, requestCode, resultCode, intent):
        if resultCode == -1 and intent is not None:
            extras = intent.getExtras()
            bitmap = extras.get("data")  # Thumbnail!

            self.app.process_bitmap(bitmap)

class MainApp(App):
    def build(self):
        self.layout = BoxLayout()
        self.image = Image()
        self.layout.add_widget(self.image)

        Clock.schedule_once(self.open_camera, 0)
        return self.layout

    def open_camera(self, dt):
        activity = PythonActivity.mActivity

        self.listener = CameraResultListener(self)
        activity.addActivityResultListener(self.listener)

        intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        activity.startActivityForResult(intent, 0)

    def process_bitmap(self, bitmap):
        # Bitmap → Bytes
        stream = autoclass('java.io.ByteArrayOutputStream')()
        bitmap.compress(
            autoclass('android.graphics.Bitmap$CompressFormat').JPEG,
            100,
            stream
        )
        byte_data = stream.toByteArray()

        # Pillow Bild
        img = PILImage.open(io.BytesIO(byte_data)).convert("RGB")
        draw = ImageDraw.Draw(img)

        # Roter Punkt oben rechts
        r = int(min(img.size) * 0.12)
        x = img.width - r - 10
        y = r + 10
        draw.ellipse((x-r, y-r, x+r, y+r), fill="red")

        # In Kivy anzeigen
        data = img.tobytes()
        texture = Texture.create(size=img.size)
        texture.blit_buffer(data, colorfmt='rgb', bufferfmt='ubyte')
        texture.flip_vertical()
        self.image.texture = texture

if __name__ == "__main__":
    MainApp().run()
