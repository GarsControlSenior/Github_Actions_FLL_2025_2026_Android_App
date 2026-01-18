from kivy.app import App
from kivy.uix.boxlayout import BoxLayout

from jnius import autoclass
from android.storage import primary_external_storage_path

import os
from datetime import datetime


class MainApp(App):

    def build(self):
        self.open_camera()
        return BoxLayout()

    def open_camera(self):
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Intent = autoclass('android.content.Intent')
        MediaStore = autoclass('android.provider.MediaStore')
        File = autoclass('java.io.File')
        Uri = autoclass('android.net.Uri')

        activity = PythonActivity.mActivity

        # 📁 Bilder-Ordner
        pictures_dir = os.path.join(
            primary_external_storage_path(),
            "Pictures",
            "Forschung"
        )

        if not os.path.exists(pictures_dir):
            os.makedirs(pictures_dir)

        # 🕒 EINDEUTIGER DATEINAME
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"forschung_{timestamp}.jpg"

        file_path = os.path.join(pictures_dir, filename)
        photo_file = File(file_path)
        photo_uri = Uri.fromFile(photo_file)

        # 📷 Kamera-Intent
        intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        intent.putExtra(MediaStore.EXTRA_OUTPUT, photo_uri)

        activity.startActivity(intent)


if __name__ == "__main__":
    MainApp().run()
