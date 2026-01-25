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

# Android-spezifische Korrekturen
if platform == 'android':
    from jnius import autoclass, cast
    from android.permissions import request_permissions, Permission
    from android import activity # Wichtig für Callbacks
    
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Intent = autoclass('android.content.Intent')
    MediaStore = autoclass('android.provider.MediaStore')
    File = autoclass('java.io.File')
    # FileProvider verhindert die FileUriExposedException
    FileProvider = autoclass('androidx.core.content.FileProvider')
    Context = autoclass('android.content.Context')

class PointSelector(FloatLayout):
    def __init__(self, image_path, callback, **kwargs):
        super().__init__(**kwargs)
        self.image_path = image_path
        self.callback = callback
        self.points = []
        
        self.img_widget = Image(source=image_path, allow_stretch=True, keep_ratio=True)
        self.add_widget(self.img_widget)
        
        self.info_label = Label(
            text="Tippe die 4 Ecken an\n(OL, OR, UR, UL)",
            size_hint=(1, 0.1), pos_hint={'top': 1},
            color=(1, 1, 1, 1)
        )
        self.add_widget(self.info_label)

    def on_touch_down(self, touch):
        if len(self.points) < 4:
            self.points.append(touch.pos)
            with self.canvas:
                Color(1, 0, 0, 1)
                Ellipse(pos=(touch.x - 15, touch.y - 15), size=(30, 30))
                if len(self.points) > 1:
                    Line(points=[p for pt in self.points for p in pt], width=2)

            if len(self.points) == 4:
                btn = Button(text="Entzerrung berechnen", size_hint=(0.5, 0.1), 
                             pos_hint={'center_x': 0.5, 'y': 0.05})
                btn.bind(on_release=lambda x: self.callback(self.points, self.img_widget))
                self.add_widget(btn)

class MainApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical', padding=20)
        # Pfad im internen App-Speicher (sicherer auf Android)
        self.temp_image_path = os.path.join(self.user_data_dir, "temp_capture.jpg")
        
        self.btn = Button(text="Foto aufnehmen", size_hint=(1, 0.2))
        self.btn.bind(on_press=self.start_process)
        self.layout.add_widget(self.btn)
        
        self.status_label = Label(text="Bereit.")
        self.layout.add_widget(self.status_label)
        
        # Activity Result Handler registrieren
        if platform == 'android':
            activity.bind(on_activity_result=self.on_activity_result)
            
        return self.layout

    def start_process(self, instance):
        if platform == 'android':
            request_permissions([Permission.CAMERA], self.on_permissions_result)
        else:
            self.status_label.text = "PC-Modus: Suche 'test.jpg'..."
            if os.path.exists("test.jpg"): self.show_selection_ui("test.jpg")

    def on_permissions_result(self, permissions, grants):
        if all(grants): self.open_camera()

    def open_camera(self):
        current_activity = PythonActivity.mActivity
        intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        
        temp_file = File(self.temp_image_path)
        # Ersetzt Uri.fromFile: Nutzt den FileProvider der App
        # WICHTIG: Die Authority muss in der buildozer.spec/Manifest passen!
        app_id = current_activity.getPackageName()
        uri = FileProvider.getUriForFile(
            current_activity,
            f"{app_id}.fileprovider",
            temp_file
        )
        
        parcelable_uri = cast('android.os.Parcelable', uri)
        intent.putExtra(MediaStore.EXTRA_OUTPUT, parcelable_uri)
        current_activity.startActivityForResult(intent, 101)

    def on_activity_result(self, request_code, result_code, data):
        if request_code == 101:
            # Wenn das Foto gemacht wurde (Result OK = -1)
            if os.path.exists(self.temp_image_path):
                Clock.schedule_once(lambda dt: self.show_selection_ui(self.temp_image_path))

    def show_selection_ui(self, path):
        self.layout.clear_widgets()
        self.selector = PointSelector(image_path=path, callback=self.process_ortho)
        self.layout.add_widget(self.selector)

    def process_ortho(self, touch_points, img_widget):
        img = cv2.imread(img_widget.source)
        if img is None: return

        h_img, w_img, _ = img.shape
        src_pts = []
        for (tx, ty) in touch_points:
            nx = (tx - img_widget.x) / img_widget.width
            ny = (ty - img_widget.y) / img_widget.height
            px = nx * w_img
            py = (1 - ny) * h_img
            src_pts.append([px, py])

        src_pts = np.float32(src_pts)
        side = 1000
        dst_pts = np.float32([[0, 0], [side, 0], [side, side], [0, side]])

        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        ortho = cv2.warpPerspective(img, M, (side, side))

        out_path = os.path.join(self.user_data_dir, "orthophoto.jpg")
        cv2.imwrite(out_path, ortho)
        
        self.layout.clear_widgets()
        self.layout.add_widget(Image(source=out_path))
        restart_btn = Button(text="Neues Bild", size_hint_y=0.1)
        restart_btn.bind(on_release=lambda x: self.build()) # Einfacher Reset
        self.layout.add_widget(restart_btn)

if __name__ == "__main__":
    MainApp().run()

if __name__ == "__main__":
    MainApp().run()

