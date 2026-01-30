from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics.texture import Texture

from jnius import autoclass, PythonJavaClass, java_method
from PIL import Image as PILImage, ImageDraw
import io

# Android Klassen
PythonActivity = autoclass('org.kivy.android.PythonActivity')
Intent = autoclass('android.content.Intent')
MediaStore = autoclass('android.provider.MediaStore')
Bitmap = autoclass('android.graphics.Bitmap')
CompressFormat = autoclass('android.graphics.Bitmap$CompressFormat')
ByteArrayOutputStream = autoclass('java.io.ByteArrayOutputStream')

class CameraListener(PythonJavaClass):
    __javainterfaces__ = ['org/kivy/android/PythonActivity$ActivityResultListener']

    def __init__(self, app):
        super().__init__()
        self.app = app

    @java_method('(IILandroid/content/Intent;)V')
    def onActivityResult(self, requestCode, resultCode, intent):
        try:
            if resultCode == -1 and intent:
                extras = intent.getExtras()
                bitmap = extras.get("data")  # Thumbnail
                self.app.process_image(bitmap)
        except Exception as e:
            print("Kamera-Fehler:", e)

class MainApp(App):

    def build(self):
        self.layout = BoxLayout()
        self.image = Image(allow_stretch=True, keep_ratio=True)
        self.layout.add_widget(self.image)

        Clock.schedule_once(self.open_camera, 0)
        return self.layout

    def open_camera(self, dt):
        try:
            activity = PythonActivity.mActivity
            self.listener = CameraListener(self)
            activity.addActivityResultListener(self.listener)

            intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
            activity.startActivityForResult(intent, 0)
        except Exception as e:
            print("Fehler beim Starten der Kamera:", e)

    def process_image(self, bitmap):
        try:
            stream = ByteArrayOutputStream()
            bitmap.compress(CompressFormat.JPEG, 100, stream)
            data = stream.toByteArray()

            img = PILImage.open(io.BytesIO(data)).convert("RGB")
            draw = ImageDraw.Draw(img)

            # 🔴 Roter Punkt oben rechts
            r = int(min(img.size) * 0.12)
            x = img.width - r - 10
            y = r + 10
            draw.ellipse((x-r, y-r, x+r, y+r), fill="red")

            # Anzeige in Kivy
            texture = Texture.create(size=img.size)
            texture.blit_buffer(img.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
            texture.flip_vertical()
            self.image.texture = texture

        except Exception as e:
            print("Bildverarbeitung fehlgeschlagen:", e)

if __name__ == "__main__":
    MainApp().run()
