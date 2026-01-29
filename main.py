import os
from os.path import join
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

# Android Importe
if platform == 'android':
    from jnius import autoclass, cast
    from android.permissions import request_permissions, Permission
    from android import activity

class TouchImage(Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.points = []

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and len(self.points) < 4:
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
                px, py = rx * self.width + self.x, ry * self.height + self.y
                Ellipse(pos=(px - 10, py - 10), size=(20, 20))

class PreviewScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.touch_img = TouchImage(allow_stretch=True, keep_ratio=True, size_hint_y=0.7)
        
        self.controls = BoxLayout(orientation='vertical', size_hint_y=0.3, spacing=5)
        self.btn_fix = Button(text="Scan entzerren", background_color=(0, 0.7, 0, 1))
        self.btn_fix.bind(on_press=self.apply_ortho)
        self.btn_back = Button(text="Neues Foto")
        self.btn_back.bind(on_press=self.reset_screen)
        self.info_label = Label(text="Markiere die 4 Ecken", size_hint_y=0.2)
        
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
            # Bild laden
            img = PILImage.open(self.touch_img.source)
            w, h = img.size
            pts = [(p[0]*w, h-(p[1]*h)) for p in self.touch_img.points]
            
            # Sortieren
            pts.sort(key=lambda p: p[1])
            top = sorted(pts[:2], key=lambda p: p[0])
            bottom = sorted(pts[2:], key=lambda p: p[0], reverse=True)
            src_pts = top + bottom
            
            dst_w, dst_h = 800, 1100
            dst_pts = [(0, 0), (dst_w, 0), (dst_w, dst_h), (0, dst_h)]
            
            coeffs = self.find_coeffs(dst_pts, src_pts)
            ortho = img.transform((dst_w, dst_h), PILImage.PERSPECTIVE, coeffs, PILImage.BICUBIC)
            
            out_path = join(App.get_running_app().user_data_dir, "scan_result.png")
            ortho.save(out_path)
            self.touch_img.source = out_path
            self.touch_img.reload()
            self.touch_img.points = []
            self.touch_img.canvas.after.clear()
            self.info_label.text = "Perfekt entzerrt!"
        except Exception as e:
            self.info_label.text = f"Fehler: {str(e)[:40]}"

    def find_coeffs(self, pa, pb):
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
        btn = Button(text="Native Kamera öffnen", size_hint_y=0.2, background_color=(0.2, 0.6, 1, 1))
        btn.bind(on_press=self.check_perms)
        self.status_lbl = Label(text="Bereit", size_hint_y=0.1)
        
        layout.add_widget(Label(text="Profi-Scanner", font_size='24sp'))
        layout.add_widget(btn)
        layout.add_widget(self.status_lbl)
        self.cam_screen.add_widget(layout)
        
        self.preview_screen = PreviewScreen(name='preview_screen')
        self.sm.add_widget(self.cam_screen)
        self.sm.add_widget(self.preview_screen)
        
        if platform == 'android':
            activity.bind(on_activity_result=self.on_result)
            self.uri_photo = None # Hier speichern wir die content:// URI

        return self.sm

    def check_perms(self, instance):
        if platform == 'android':
            # Frage alle nötigen Rechte ab
            perms = [Permission.CAMERA, Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE]
            # Für Android 13+ (SDK 33) gibt es Permission.READ_MEDIA_IMAGES (String: 'android.permission.READ_MEDIA_IMAGES')
            # Buildozer/Python-for-Android kennt das Enum evtl. noch nicht, daher als String sicherheitshalber:
            if autoclass('android.os.Build$VERSION').SDK_INT >= 33:
                perms.append('android.permission.READ_MEDIA_IMAGES')
                
            request_permissions(perms, self.on_perms)
        else:
            self.sm.current = 'preview_screen'

    def on_perms(self, permissions, grants):
        # Einfache Prüfung: Wenn Kamera erlaubt ist, versuchen wir es
        if grants:
            self.open_native_camera()
        else:
            self.status_lbl.text = "Berechtigung fehlt!"

    def open_native_camera(self):
        try:
            # Android Klassen
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            MediaStore = autoclass('android.provider.MediaStore')
            ContentValues = autoclass('android.content.ContentValues')
            
            # 1. ContentResolver holen
            activity_instance = PythonActivity.mActivity
            resolver = activity_instance.getContentResolver()
            
            # 2. Leeren Platz im Medienspeicher (Galerie) reservieren
            values = ContentValues()
            values.put(MediaStore.Images.Media.TITLE, "NewScan")
            values.put(MediaStore.Images.Media.DESCRIPTION, "From Kivy App")
            values.put(MediaStore.Images.Media.MIME_TYPE, "image/jpeg")
            
            # Wir nutzen EXTERNAL_CONTENT_URI - das funktioniert ohne FileProvider!
            self.uri_photo = resolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values)
            
            if not self.uri_photo:
                self.status_lbl.text = "Fehler: Konnte URI nicht erstellen"
                return

            # 3. Intent starten mit der sicheren URI
            intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
            intent.putExtra(MediaStore.EXTRA_OUTPUT, self.uri_photo)
            
            # Sicherstellen, dass eine Kamera-App da ist
            if intent.resolveActivity(activity_instance.getPackageManager()) is not None:
                activity_instance.startActivityForResult(intent, 999)
            else:
                self.status_lbl.text = "Keine Kamera-App gefunden!"
                
        except Exception as e:
            self.status_lbl.text = f"Startfehler: {e}"

    @mainthread
    def on_result(self, requestCode, resultCode, intent):
        # 999 ist unser Kamera-Request Code
        if requestCode == 999 and resultCode == -1: # -1 = RESULT_OK
            if self.uri_photo:
                self.copy_uri_to_local(self.uri_photo)
                
    def copy_uri_to_local(self, uri):
        """Kopiert das Bild vom Content-Speicher in den App-Speicher für Kivy"""
        try:
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            context = PythonActivity.mActivity
            resolver = context.getContentResolver()
            
            # Input Stream vom System öffnen
            inp_stream = resolver.openInputStream(uri)
            
            # Zieldatei im App-Ordner
            dest_path = join(self.user_data_dir, "temp_cam_photo.jpg")
            
            # Kopieren (Byte für Byte in Python ist langsam, aber OK für 1 Bild)
            # Effizienter: Java-Klassen nutzen, aber Python 'read' geht auch
            # Wir lesen alles in den RAM (Vorsicht bei riesigen Bildern, aber meist ok)
            # Besser: Chunks
            
            with open(dest_path, 'wb') as out_file:
                # Java InputStream lesen ist in Python via jnius tricky. 
                # Wir nutzen einen simplen Weg: Stream in Python File Object wrappen geht nicht direkt.
                # Wir lesen Blocks via jnius.
                
                buffer = bytearray(4096)
                while True:
                    read = inp_stream.read(buffer)
                    if read == -1: break
                    out_file.write(buffer[:read])
            
            inp_stream.close()
            
            # Bild in Kivy anzeigen
            self.preview_screen.touch_img.source = dest_path
            self.preview_screen.touch_img.reload()
            self.sm.current = 'preview_screen'
            
        except Exception as e:
            self.status_lbl.text = f"Ladefehler: {e}"

if __name__ == "__main__":
    MainApp().run()
