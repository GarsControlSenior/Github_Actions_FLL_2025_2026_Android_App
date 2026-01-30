from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics.texture import Texture

from jnius import autoclass, PythonJavaClass, java_method
from PIL import Image as PILImage, ImageDraw
import os

# Android-Klassen
PythonActivity = autoclass('org.kivy.android.PythonActivity')
Intent = autoclass('android.content.Intent')
MediaStore = autoclass('android.provider.MediaStore')
File = autoclass('java.io.File')
Uri = autoclass('android.net.Uri')
# interner Speicher
Environment = autoclass('android.os.Environment')

# Listener für Kameraergebnis
class ActivityResultListener(PythonJavaClass):
    __javainterfaces__ = ['org/kivy/android/PythonActivity$ActivityResultListener']

    def __init__(self, app):
        super().__init__()
        self.app = app

    @java_method('(IILandroid/content/Intent;)V')
    def onActivityResult(self, requestCode, resultCode, intent):
        if resultCode == -1:  # RESULT_OK
            self.app.add_red_dot(self.app.photo_path)

class MainApp(App):
    def build(self):
        self.layout = BoxLayout()
        self.image_widget = Image()
        self.layout.add_widget(self.image_widget)

        # Kamera 0.5 Sekunden verzögert starten, damit App vollständig lädt
        Clock.schedule_once(lambda dt: self.take_photo(), 0.5)
        return self.layout

    def take_photo(self):
        activity = PythonActivity.mActivity

        # Speicherort im internen App-Verzeichnis (kein Storage-Permission nötig)
        app_storage = activity.getFilesDir().getAbsolutePath()
        self.photo_path = os.path.join(app_storage, "temp_photo.jpg")

        # Datei-URI erstellen
        file_obj = File(self.photo_path)
        uri = Uri.fromFile(file_obj)

        # Kamera-Intent
        intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        intent.putExtra(MediaStore.EXTRA_OUTPUT, uri)

        # Listener registrieren
        self.listener = ActivityResultListener(self)
        PythonActivity.mActivity.addActivityResultListener(self.listener)

        # Kamera starten
        PythonActivity.mActivity.startActivityForResult(intent, 0)

    def add_red_dot(self, path):
        # Bild öffnen und in RGB konvertieren
        img = PILImage.open(path).convert('RGB')
        draw = ImageDraw.Draw(img)

        # Großer roter Punkt oben rechts
        radius = int(min(img.width, img.height) * 0.1)  # 10% der Bildgröße
        x = img.width - radius - 10
        y = radius + 10
        draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill="red")

        # Bild speichern
        img.save(path)

        # Bild in Kivy anzeigen
        img_kivy = PILImage.open(path).convert('RGB')
        img_data = img_kivy.tobytes()
        texture = Texture.create(size=img_kivy.size)
        texture.blit_buffer(img_data, colorfmt='rgb', bufferfmt='ubyte')
        texture.flip_vertical()
        self.image_widget.texture = texture
        self.image_widget.allow_stretch = True
        self.image_widget.keep_ratio = True

if __name__ == "__main__":
    MainApp().run()
