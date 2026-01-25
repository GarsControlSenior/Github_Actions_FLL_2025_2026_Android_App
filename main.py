import cv2
import numpy as np
import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Ellipse, Line
from kivy.utils import platform
from kivy.clock import Clock

# Android-spezifische Importe
if platform == 'android':
    from jnius import autoclass, cast
    from android.permissions import check_permission, request_permissions, Permission
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Intent = autoclass('android.content.Intent')
    MediaStore = autoclass('android.provider.MediaStore')
    Uri = autoclass('android.net.Uri')
    File = autoclass('java.io.File')
    Environment = autoclass('android.os.Environment')

class PointSelector(FloatLayout):
    """Widget zur interaktiven Auswahl der 4 Ecken auf dem Foto."""
    def __init__(self, image_path, callback, **kwargs):
        super().__init__(**kwargs)
        self.image_path = image_path
        self.callback = callback
        self.points = []
        
        # Das aufgenommene Bild anzeigen
        self.img_widget = Image(source=image_path, allow_stretch=True, keep_ratio=True)
        self.add_widget(self.img_widget)
        
        self.info_label = Label(
            text="Klicke die 4 Ecken des Fundes an\n(Reihenfolge: oben-links, oben-rechts, unten-rechts, unten-links)",
            size_hint=(1, 0.1), pos_hint={'top': 1},
            color=(1, 1, 1, 1)
        )
        self.add_widget(self.info_label)

    def on_touch_down(self, touch):
        if len(self.points) < 4:
            # Speichere die Klick-Position
            self.points.append(touch.pos)
            
            # Zeichne einen roten Punkt
            with self.canvas:
                Color(1, 0, 0, 1)
                Ellipse(pos=(touch.x - 15, touch.y - 15), size=(30, 30))
                if len(self.points) > 1:
                    Line(points=[p for pt in self.points for p in pt], width=2)

            if len(self.points) == 4:
                # Button zum Starten der Entzerrung einblenden
                btn = Button(text="Entzerrung berechnen", size_hint=(0.5, 0.1), 
                             pos_hint={'center_x': 0.5, 'y': 0.05})
                btn.bind(on_release=lambda x: self.callback(self.points, self.img_widget))
                self.add_widget(btn)

class MainApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical', padding=20)
        self.temp_image_path = os.path.join(self.user_data_dir, "temp_capture.jpg")
        
        self.btn = Button(
            text="Foto aufnehmen", 
            size_hint=(1, 0.2),
            background_color=(0.2, 0.6, 1, 1)
        )
        self.btn.bind(on_press=self.manage_camera_start)
        self.layout.add_widget(self.btn)
        
        self.status_label = Label(text="Warte auf Kamera...")
        self.layout.add_widget(self.status_label)
        
        return self.layout

    def manage_camera_start(self, instance):
        if platform == 'android':
            perms = [Permission.CAMERA, Permission.WRITE_EXTERNAL_STORAGE]
            request_permissions(perms, self.on_permissions_result)
        else:
            self.status_label.text = "Kamera-Sim: Suche 'test.jpg'..."
            if os.path.exists("test.jpg"):
                self.show_selection_ui("test.jpg")

    def on_permissions_result(self, permissions, grants):
        if all(grants):
            self.open_camera()

    def open_camera(self):
        activity = PythonActivity.mActivity
        intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        
        # Datei-Pfad für das Foto vorbereiten
        temp_file = File(self.temp_image_path)
        uri = Uri.fromFile(temp_file)
        intent.putExtra(MediaStore.EXTRA_OUTPUT, cast('android.os.Parcelable', uri))
        
        activity.startActivityForResult(intent, 101)
        # In einer echten App müsste man onActivityResult abfangen.
        # Hier nutzen wir einen einfachen Check-Button zur Demo:
        self.layout.clear_widgets()
        check_btn = Button(text="Bild geladen? Klick hier.")
        check_btn.bind(on_release=lambda x: self.show_selection_ui(self.temp_image_path))
        self.layout.add_widget(check_btn)

    def show_selection_ui(self, path):
        self.layout.clear_widgets()
        self.selector = PointSelector(image_path=path, callback=self.process_ortho)
        self.layout.add_widget(self.selector)

    def process_ortho(self, touch_points, img_widget):
        # 1. Bild mit OpenCV laden
        img = cv2.imread(img_widget.source)
        if img is None: return

        h_img, w_img, _ = img.shape

        # 2. Umrechnung Kivy-Touch -> Bild-Pixel
        # Kivy (0,0) ist unten-links, OpenCV (0,0) oben-links
        src_pts = []
        for (tx, ty) in touch_points:
            # Normalisieren auf Widget-Größe
            nx = (tx - img_widget.x) / img_widget.width
            ny = (ty - img_widget.y) / img_widget.height
            
            # Skalieren auf Bild-Pixel und Y invertieren
            px = nx * w_img
            py = (1 - ny) * h_img
            src_pts.append([px, py])

        src_pts = np.float32(src_pts)

        # 3. Ziel-Koordinaten definieren (Quadrat 1000x1000)
        side = 1000
        dst_pts = np.float32([[0, 0], [side, 0], [side, side], [0, side]])

        # 4. Homographie berechnen und anwenden
        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        ortho = cv2.warpPerspective(img, M, (side, side))

        # 5. Ergebnis speichern und anzeigen
        out_path = os.path.join(self.user_data_dir, "orthophoto.jpg")
        cv2.imwrite(out_path, ortho)
        
        self.layout.clear_widgets()
        self.layout.add_widget(Image(source=out_path))
        self.layout.add_widget(Label(text=f"Gespeichert in:\n{out_path}", size_hint_y=0.2))
        
        restart_btn = Button(text="Neu starten", size_hint_y=0.1)
        restart_btn.bind(on_release=lambda x: os._exit(0)) # Simpler Neustart
        self.layout.add_widget(restart_btn)

if __name__ == "__main__":
    MainApp().run()
