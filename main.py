from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from jnius import autoclass, PythonJavaClass, java_method

# Android Klassen
PythonActivity = autoclass('org.kivy.android.PythonActivity')
Intent = autoclass('android.content.Intent')
MediaStore = autoclass('android.provider.MediaStore')

# Listener nur um ZURÜCKKOMMEN zu erkennen
class CameraResultListener(PythonJavaClass):
    __javainterfaces__ = ['org/kivy/android/PythonActivity$ActivityResultListener']

    def __init__(self, app):
        super().__init__()
        self.app = app

    @java_method('(IILandroid/content/Intent;)V')
    def onActivityResult(self, requestCode, resultCode, intent):
        # Egal ob OK oder Abbrechen → blaue Fläche anzeigen
        self.app.show_blue_screen()

class MainApp(App):

    def build(self):
        self.root_layout = BoxLayout()
        Clock.schedule_once(self.open_camera, 0)
        return self.root_layout

    def open_camera(self, dt):
        try:
            activity = PythonActivity.mActivity

            # Listener registrieren
            self.listener = CameraResultListener(self)
            activity.addActivityResultListener(self.listener)

            # Standardkamera starten
            intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
            activity.startActivityForResult(intent, 0)

        except Exception as e:
            print("Fehler beim Öffnen der Kamera:", e)
            self.show_blue_screen()

    def show_blue_screen(self):
        # UI komplett ersetzen
        self.root_layout.clear_widgets()

        blue_layout = BoxLayout()
        with blue_layout.canvas.before:
            Color(0, 0, 0.6, 1)  # Dunkelblau
            self.bg = Rectangle(size=blue_layout.size, pos=blue_layout.pos)

        blue_layout.bind(size=self.update_bg, pos=self.update_bg)

        # Weißer Pfeil (Unicode)
        arrow = Label(
            text="➜",
            font_size="120sp",
            color=(1, 1, 1, 1)
        )

        blue_layout.add_widget(arrow)
        self.root_layout.add_widget(blue_layout)

    def update_bg(self, instance, value):
        self.bg.size = instance.size
        self.bg.pos = instance.pos


if __name__ == "__main__":
    MainApp().run()
