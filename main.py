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
from kivy.graphics import Color, Ellipse, Line

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
            # Speichere relative Koordinaten (0-1), um Skalierungsprobleme zu vermeiden
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
            Color(1, 0, 0)
            for rx, ry in self.points:
                # Zurückrechnen auf Pixel für die Anzeige
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
        
        self.info_label = Label(text="Tippe die 4 Ecken des Objekts an", size_hint_y=0.2)
        
        self.controls.add_widget(self.btn_fix)
        self.controls.add_widget(self.btn_back)
        self.controls.add_widget(self.info_label)
        self.layout.add_widget(self.touch_img)
        self.layout.add_widget(self.controls)
        self.add_widget(self.layout)

    def reset_screen(self, instance):
        self.touch_img.points = []
        self.touch_img.canvas.after.clear()
        if self.touch_img.source: self.touch_img.reload()
        self.manager.current = 'camera_screen'

    def apply_ortho(self, instance):
        if len(self.touch_img.points) != 4:
            self.info_label.text = "Bitte genau 4 Punkte setzen!"
            return

        try:
            img = PILImage.open(self.touch_img.source)
            w, h = img.size

            # 1. Punkte sortieren (Oben-Links, Oben-Rechts, Unten-Rechts, Unten-Links)
            # Kivy Y=0 ist unten, PIL Y=0 ist oben!
            pts = []
            for rx, ry in self.touch_img.points:
                pts.append((rx * w, h - (ry * h))) # Umrechnung auf PIL-Koordinaten

            # Einfache Sortierung nach Quadranten
            pts.sort(key=lambda p: p[1]) # Sortiere nach Y
            top = sorted(pts[:2], key=lambda p: p[0]) # Die zwei oberen nach X
            bottom = sorted(pts[2:], key=lambda p: p[0], reverse=True) # Die zwei unteren
            ordered_pts = top + bottom # Reihenfolge: TL, TR, BR, BL

            # 2. Ziel-Dimensionen (A4 Format Simulation)
            dst_w, dst_h = 800, 1100
            dst_pts = [0, 0, dst_w, 0, dst_w, dst_h, 0, dst_h]
            
            # 3. Perspektivische Transformation berechnen
            # Pillow braucht die Koeffizienten für die Quad-Transformation
            coeffs = self.find_coeffs(dst_pts, ordered_pts)
            
            ortho_img = img.transform((dst_w, dst_h), PILImage.PERSPECTIVE, coeffs, PILImage.BICUBIC)
            
            out_path = join(App.get_running_app().user_data_dir, "orthofoto.png")
            ortho_img.save(out_path)
            
            self.touch_img.source = out_path
            self.touch_img.reload()
            self.touch_img.points = []
            self.touch_img.canvas.after.clear()
            self.info_label.text = "Orthofoto erstellt!"

        except Exception as e:
            self.info_label.text = f"Fehler: {str(e)}"

    def find_coeffs(self, pa, pb):
        import numpy as np
        matrix = []
        for p1, p2 in zip(pa, pb):
            matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0]*p1[0], -p2[0]*p1[1]])
            matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1]*p1[0], -p2[1]*p1[1]])
        # Simpler Ersatz für Matrix-Inversion ohne große Libs
        # Da numpy oft nicht in Standard-Kivy-Builds ist, hier die Lösung via Pillow direkt:
        # Hinweis: find_coeffs ist mathematisch komplex. Pillow's transform nutzt:
        # (x, y) -> ((ax + by + c) / (gx + hy + 1), (dx + ey + f) / (gx + hy + 1))
        # Da numpy-Installation in Buildozer oft fehlschlägt, nutzen wir hier einen Trick:
        return self._solve_linear_matrix(pa, pb)

    def _solve_linear_matrix(self, dst_pts, src_pts):
        # Hilfsfunktion zur Berechnung der Koeffizienten für Pillow PERSPECTIVE
        import numpy as np # Nur wenn verfügbar, sonst schlägt es fehl.
        # Alternativ: Wir nutzen die interne Pillow Methode für Quads
        # Da die Matrix-Berechnung ohne Numpy schwer ist, hier die stabilste Form:
        matrix = []
        for i in range(4):
            matrix.append([dst_pts[i*2], dst_pts[i*2+1], 1, 0, 0, 0, -src_pts[i][0]*dst_pts[i*2], -src_pts[i][0]*dst_pts[i*2+1]])
            matrix.append([0, 0, 0, dst_pts[i*2], dst_pts[i*2+1], 1, -src_pts[i][1]*dst_pts[i*2], -src_pts[i][1]*dst_pts[i*2+1]])
        A = np.array(matrix, dtype=float)
        B = np.array(src_pts).reshape(8)
        res = np.linalg.solve(A, B)
        return res

class MainApp(App):
    def build(self):
        self.sm = ScreenManager()
        self.cam_screen = Screen(name='camera_screen')
        layout = BoxLayout(orientation='vertical', padding=50)
        btn = Button(text="Kamera öffnen", size_hint_y=0.2)
        btn.bind(on_press=self.manage_camera_start)
        layout.add_widget(Label(text="Beleg-Scanner", font_size='24sp'))
        layout.add_widget(btn)
        self.cam_screen.add_widget(layout)
        self.preview_screen = PreviewScreen(name='preview_screen')
        self.sm.add_widget(self.cam_screen)
        self.sm.add_widget(self.preview_screen)

        if platform == 'android':
            activity.bind(on_activity_result=self.on_result)
            # Speichere im öffentlichen Download Ordner, um Permissions-Probleme zu umgehen
            self.photo_path = join(primary_external_storage_path(), "Download", "scanner_temp.jpg")
        return self.sm

    def manage_camera_start(self, instance):
        if platform == 'android':
            request_permissions([Permission.CAMERA, Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE], callback=self.on_perms)
        else:
            self.preview_screen.touch_img.source = "test.png"
            self.sm.current = 'preview_screen'

    def on_perms(self, permissions, grants):
        if all(grants): self.open_camera_android()

    def open_camera_android(self):
        try:
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            MediaStore = autoclass('android.provider.MediaStore')
            Uri = autoclass('android.net.Uri')
            File = autoclass('java.io.File')
            StrictMode = autoclass('android.os.StrictMode')

            # Fix für FileUriExposedException
            policy = StrictMode.VmPolicy.Builder().build()
            StrictMode.setVmPolicy(policy)

            intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
            file_obj = File(self.photo_path)
            uri = Uri.fromFile(file_obj)
            intent.putExtra(MediaStore.EXTRA_OUTPUT, uri)
            PythonActivity.mActivity.startActivityForResult(intent, 101)
        except Exception as e:
            print(f"Fehler: {e}")

    @mainthread
    def on_result(self, requestCode, resultCode, intent):
        if requestCode == 101 and resultCode == -1:
            self.preview_screen.touch_img.source = self.photo_path
            self.preview_screen.touch_img.reload()
            self.sm.current = 'preview_screen'

if __name__ == "__main__":
    MainApp().run()
