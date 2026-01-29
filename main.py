import math
import os
from os.path import join, exists
from PIL import Image as PILImage

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.utils import platform
from kivy.clock import mainthread
from kivy.graphics import Color, Ellipse

# Android-spezifische Importe
if platform == 'android':
    from jnius import autoclass
    from android.permissions import request_permissions, Permission
    from android import activity
    from android.storage import primary_external_storage_path

class TouchImage(Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.points = []

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and len(self.points) < 4:
            # Speichere relative Koordinaten (0.0 bis 1.0) für Skalierungsunabhängigkeit
            rel_x = (touch.x - self.x) / self.width
            rel_y = (touch.y - self.y) / self.height
            self.points.append((rel_x, rel_y))
            self.redraw_shapes()
            return True 
        return super().on_touch_down(touch)

    def redraw_shapes(self):
        self.canvas.after.clear()
        if not self.points: return
        with self.canvas.after:
            Color(1, 0, 0) # Rote Punkte für die Markierung
            for rx, ry in self.points:
                px, py = rx * self.width + self.x, ry * self.height + self.y
                Ellipse(pos=(px - 10, py - 10), size=(20, 20))

class PreviewScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.touch_img = TouchImage(allow_stretch=True, keep_ratio=True, size_hint_y=0.7)
        
        self.controls = BoxLayout(orientation='vertical', size_hint_y=0.3, spacing=5)
        self.btn_fix = Button(text="Orthofoto erstellen", background_color=(0, 0.7, 0, 1))
        self.btn_fix.bind(on_press=self.apply_ortho)
        self.btn_back = Button(text="Neues Foto / Reset")
        self.btn_back.bind(on_press=self.reset_screen)
        self.info_label = Label(text="Markiere die 4 Ecken des Belegs", size_hint_y=0.2)
        
        self.controls.add_widget(self.btn_fix)
        self.controls.add_widget(self.btn_back)
        self.controls.add_widget(self.info_label)
        self.layout.add_widget(self.touch_img)
        self.layout.add_widget(self.controls)
        self.add_widget(self.layout)

    def reset_screen(self, instance):
        self.touch_img.points = []
        self.touch_img.canvas.after.clear()
        self.manager.current = 'camera_screen'

    def apply_ortho(self, instance):
        if len(self.touch_img.points) != 4:
            self.info_label.text = "Bitte 4 Punkte setzen!"
            return
        try:
            img = PILImage.open(self.touch_img.source)
            w, h = img.size
            # Koordinatenumrechnung: Kivy (Y=0 unten) zu PIL (Y=0 oben)
            pts = [(p[0]*w, h-(p[1]*h)) for p in self.touch_img.points]
            
            # Sortierung der Punkte: Oben-Links, Oben-Rechts, Unten-Rechts, Unten-Links
            pts.sort(key=lambda p: p[1])
            top = sorted(pts[:2], key=lambda p: p[0])
            bottom = sorted(pts[2:], key=lambda p: p[0], reverse=True)
            src_pts = top + bottom
            
            # Zielformat (z.B. 800x1100 Pixel)
            dst_w, dst_h = 800, 1100
            dst_pts = [(0, 0), (dst_w, 0), (dst_w, dst_h), (0, dst_h)]
            
            coeffs = self.find_coeffs(dst_pts, src_pts)
            ortho = img.transform((dst_w, dst_h), PILImage.PERSPECTIVE, coeffs, PILImage.BICUBIC)
            
            out_path = join(App.get_running_app().user_data_dir, "ortho_result.png")
            ortho.save(out_path)
            self.touch_img.source = out_path
            self.touch_img.reload()
            self.touch_img.points = []
            self.touch_img.canvas.after.clear()
            self.info_label.text = "Orthofoto erfolgreich erstellt!"
        except Exception as e:
            self.info_label.text = f"Fehler: {str(e)[:40]}"

    def find_coeffs(self, pa, pb):
        """Berechnet die Perspektiv-Koeffizienten ohne externe Bibliotheken."""
        matrix = []
        for p1, p2 in zip(pa, pb):
            matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0]*p1[0], -p2[0]*p1[1], p2[0]])
            matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1]*p1[0], -p2[1]*p1[1], p2[1]])
        for i in range(8):
            max_row = i
            for k in range(i + 1, 8):
                if abs(matrix[k][i]) > abs(matrix[max_row][i]): max_row = k
            matrix[i], matrix[max_row] = matrix[max_row], matrix[i]
            for k in range(i + 1, 8):
                c = -matrix[k][i] / matrix[i][i]
                for j in range(i, 9):
                    matrix[k][j] += c * matrix[i][j]
        res = [0] * 8
        for i in range(7, -1, -1):
            res[i] = matrix[i][8] / matrix[i][i]
            for k in range(i - 1, -1, -1):
                matrix[k][8] -= matrix[k][i] * res[i]
        return res

class MainApp(App):
    def build(self):
        self.sm = ScreenManager()
        self.cam_screen = Screen(name='camera_screen')
        layout = BoxLayout(orientation='vertical', padding=50)
        btn = Button(text="Kamera öffnen", size_hint_y=0.2, background_color=(0.2, 0.6, 1, 1))
        btn.bind(on_press=self.manage_camera_start)
        layout.add_widget(Label(text="Beleg-Scanner", font_size='24sp'))
        layout.add_widget(btn)
        self.cam_screen.add_widget(layout)
        
        self.preview_screen = PreviewScreen(name='preview_screen')
        self.sm.add_widget(self.cam_screen)
        self.sm.add_widget(self.preview_screen)
        
        if platform == 'android':
            activity.bind(on_activity_result=self.on_result)
            # Speichere das temporäre Foto im öffentlichen Download-Ordner
            self.photo_path = join(primary_external_storage_path(), "Download", "temp_scan_image.jpg")
        return self.sm

    def manage_camera_start(self, instance):
        if platform == 'android':
            request_permissions([Permission.CAMERA, Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE], 
                                callback=self.check_permissions)
        else:
            # Desktop-Simulationsmodus
            self.sm.current = 'preview_screen'

    def check_permissions(self, permissions, grants):
        if all(grants):
            self.open_camera_android()

    def open_camera_android(self):
        try:
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            MediaStore = autoclass('android.provider.MediaStore')
            Uri = autoclass('android.net.Uri')
            File = autoclass('java.io.File')
            StrictMode = autoclass('android.os.StrictMode')
            
            # Deaktiviert die FileUriExposedException für den Intent
            policy = StrictMode.VmPolicy.Builder().build()
            StrictMode.setVmPolicy(policy)
            
            intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
            photo_file = File(self.photo_path)
            uri = Uri.fromFile(photo_file)
            intent.putExtra(MediaStore.EXTRA_OUTPUT, uri)
            
            # Startet die System-Kamera-App
            PythonActivity.mActivity.startActivityForResult(intent, 101)
        except Exception as e:
            print(f"Kamera-Startfehler: {e}")

    @mainthread
    def on_result(self, requestCode, resultCode, intent):
        if requestCode == 101 and resultCode == -1: # -1 entspricht RESULT_OK
            self.preview_screen.touch_img.source = self.photo_path
            self.preview_screen.touch_img.reload()
            self.sm.current = 'preview_screen'

if __name__ == "__main__":
    MainApp().run()
