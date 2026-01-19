from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from jnius import autoclass
import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.camera import Camera
from kivy.uix.image import Image
from kivy.graphics import Color, Ellipse, Line
import math
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.clock import Clock # Neu: Für verzögerten Start
from os.path import join, exists
from PIL import Image as PILImage

# Neu: Imports für Android-Berechtigungen. Nutzt try-except für Desktop-Tests.
try:
    from android.permissions import request_permissions, Permission
except ImportError:
    request_permissions = None # Platzhalter für Desktop-Systeme

class MainApp(App):
    def build(self):
        self.open_camera()
        return BoxLayout()

    def open_camera(self):
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Intent = autoclass('android.content.Intent')
        MediaStore = autoclass('android.provider.MediaStore')

        activity = PythonActivity.mActivity
        intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        activity.startActivity(intent)

if __name__ == "__main__":
    MainApp().run()
