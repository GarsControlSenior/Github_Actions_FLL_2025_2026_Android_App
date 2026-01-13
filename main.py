from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.camera import Camera
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.utils import platform

class CameraApp(App):

    def build(self):
        layout = BoxLayout(orientation="vertical")

        info = Label(
            text="Kamera Vorschau",
            size_hint_y=0.08
        )
        layout.add_widget(info)

        self.camera = Camera(
            play=False,
            resolution=(3840, 2160)  # 4K → maximale Vorschau
        )

        self.camera.allow_stretch = True
        self.camera.keep_ratio = False
        self.camera.size_hint_y = 0.92

        layout.add_widget(self.camera)

        Clock.schedule_once(self.start_camera, 0.5)

        return layout

    def start_camera(self, *args):
        self.camera.play = True


CameraApp().run()
