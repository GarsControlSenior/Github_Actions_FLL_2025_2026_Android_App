from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.camera import Camera
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.graphics import Color, Ellipse
from kivy.clock import Clock
import os

class CameraApp(App):

    def build(self):
        self.root = BoxLayout(orientation='vertical')

        # === KAMERA ===
        self.camera = Camera(play=True, resolution=(640, 480))
        self.root.add_widget(self.camera)

        # === ROTER PUNKT (Overlay) ===
        with self.camera.canvas.after:
            Color(1, 0, 0)
            self.red_dot = Ellipse(size=(80, 80))

        Clock.schedule_once(self.update_dot_position, 0)

        # === BUTTON ===
        btn = Button(text="Foto aufnehmen", size_hint_y=0.2)
        btn.bind(on_press=self.take_picture)
        self.root.add_widget(btn)

        return self.root

    def update_dot_position(self, dt):
        # oben rechts
        cam_w, cam_h = self.camera.size
        self.red_dot.pos = (
            self.camera.x + cam_w - 90,
            self.camera.y + cam_h - 90
        )

    def take_picture(self, instance):
        # Foto speichern
        path = os.path.join(self.user_data_dir, "foto.jpg")
        self.camera.export_to_png(path)

        # Kamera stoppen
        self.camera.play = False

        # Anzeige wechseln
        self.root.clear_widgets()
        img = Image(source=path, allow_stretch=True, keep_ratio=True)
        self.root.add_widget(img)

        back_btn = Button(text="Zurück zur Kamera", size_hint_y=0.2)
        back_btn.bind(on_press=self.restart_camera)
        self.root.add_widget(back_btn)

    def restart_camera(self, instance):
        self.root.clear_widgets()
        self.camera.play = True
        self.build()

if __name__ == "__main__":
    CameraApp().run()
