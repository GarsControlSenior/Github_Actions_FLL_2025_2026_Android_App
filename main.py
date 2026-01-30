from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.graphics.texture import Texture
from jnius import autoclass, PythonJavaClass, java_method
from PIL import Image as PILImage, ImageDraw
import os

# Listener, um das Kameraergebnis abzufangen
PythonActivity = autoclass('org.kivy.android.PythonActivity')
Intent = autoclass('android.content.Intent')
MediaStore = autoclass('android.provider.MediaStore')
File = autoclass('java.io.File')
Environment = autoclass('android.os.Environment')
Uri = autoclass('android.net.Uri')

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
        self.take_photo()
        return self.layout

    def take_photo(self):
        activity = PythonActivity.mActivity

        # Speicherort für das Foto
        pictures_dir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_PICTURES).getAbsolutePath()
        self.photo_path = os.path.join(pictures_dir, "temp_photo.jpg")

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
        # Bild öffnen
        img = PILImage.open(path)
        draw = ImageDraw.Draw(img)

        # Großer roter Punkt oben rechts
        radius = 50
        x = img.width - radius - 10
        y = radius + 10
        draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill="red")

        # Bild speichern
        img.save(path)

        # Bild in Kivy anzeigen
        img_kivy = PILImage.open(path)
        img_data = img_kivy.tobytes()
        texture = Texture.create(size=img_kivy.size)
        texture.blit_buffer(img_data, colorfmt='rgb', bufferfmt='ubyte')
        texture.flip_vertical()
        self.image_widget.texture = texture

if __name__ == "__main__":
    MainApp().run()
