import math
from os.path import join, exists
from PIL import Image as PILImage

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.utils import platform
from kivy.clock import mainthread
from kivy.graphics import Color, Ellipse, Line

# Android-spezifische Importe
if platform == 'android':
    from jnius import autoclass, cast
    from android.permissions import check_permission, request_permissions, Permission
    from android import activity

# --- DEIN TOUCH-IMAGE WIDGET ---
class TouchImage(Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.points = []

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and len(self.points) < 4:
            self.points.append((touch.x, touch.y))
            self.redraw_shapes()
            return True 
        return super().on_touch_down(touch)

    def redraw_shapes(self):
        self.canvas.after.clear()
        if not self.points:
            return
        with self.canvas.after:
            Color(1, 0, 0) # Rot für Punkte
            for x, y in self.points:
                Ellipse(pos=(x - 6, y - 6), size=(12, 12))

            if len(self.points) >= 2:
                cx = sum(p[0] for p in self.points) / len(self.points)
                cy = sum(p[1] for p in self.points) / len(self.points)
                def ang(p): return math.atan2(p[1] - cy, p[0] - cx)
                ordered = sorted(self.points, key=ang)
                pts = []
                for p in ordered: pts.extend([p[0], p[1]])

                Color(0, 1, 0) # Grün für Linien
                if len(ordered) >= 3:
                    Line(points=pts + pts[0:2], width=2)
                else:
                    Line(points=pts, width=2)

# --- DER NEUE PREVIEW SCREEN ---
class PreviewScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Das TouchImage aus deinem Code
        self.touch_img = TouchImage(allow_stretch=True, keep_ratio=True, size_hint_y=0.7)
        
        # Steuerung
        self.controls = BoxLayout(orientation='vertical', size_hint_y=0.3, spacing=5)
        self.btn_fix = Button(text="Korrektur anwenden", background_color=(0.2, 0.8, 0.2, 1))
        self.btn_fix.bind(on_press=self.apply_correction)
        
        self.btn_back = Button(text="Neues Foto")
        self.btn_back.bind(on_press=self.go_back)
        
        self.info_label = Label(text="Tippe 4 Punkte an", size_hint_y=0.3)
        
        self.controls.add_widget(self.btn_fix)
        self.controls.add_widget(self.btn_back)
        self.controls.add_widget(self.info_label)
        
        self.layout.add_widget(self.touch_img)
        self.layout.add_widget(self.controls)
        self.add_widget(self.layout)

    def go_back(self, instance):
        self.manager.current = 'camera_screen'

    def apply_correction(self, instance):
        # Hier ist deine PIL Logik integriert
        if len(self.touch_img.points) != 4:
            self.info_label.text = "Bitte genau 4 Punkte auswählen"
            return
        
        filename = self.touch_img.source
        if not filename or not exists(filename):
            return

        try:
            img = PILImage.open(filename)
            ratio_x = img.width / self.touch_img.width
            ratio_y = img.height / self.touch_img.height
            
            scaled_points = []
            for x_kivy, y_kivy in self.touch_img.points:
                x_rel = x_kivy - self.touch_img.x
                y_rel = y_kivy - self.touch_img.y
                scaled_points.append((x_rel * ratio_x, y_rel * ratio_y))

            xs = [p[0] for p in scaled_points]
            ys = [p[1] for p in scaled_points]
            
            left, right = int(min(xs)), int(max(xs))
            pil_top = img.height - int(max(ys))
            pil_bottom = img.height - int(min(ys))
            
            cropped = img.crop((left, pil_top, right, pil_bottom))
            corrected = cropped.resize((800, 1000)) # Etwas höhere Res für Preview
            
            # Speichern unter neuem Namen
            out_path = join(App.get_running_app().user_data_dir, "korrigiert.png")
            corrected.save(out_path)
            
            # Update View
            self.touch_img.source = out_path
            self.touch_img.reload()
            self.touch_img.points.clear()
            self.touch_img.canvas.after.clear()
            self.info_label.text = "Korrektur fertig!"
            
        except Exception as e:
            self.info_label.text = f"Fehler: {e}"

# --- MAIN APP ---
class MainApp(App):
    def build(self):
        self.sm = ScreenManager()
        
        # Camera Start Screen
        self.cam_screen = Screen(name='camera_screen')
        layout = BoxLayout(orientation='vertical', padding=50)
        self.btn_start = Button(text="Kamera öffnen", size_hint_y=0.2)
        self.btn_start.bind(on_press=self.manage_camera_start)
        layout.add_widget(Label(text="Beleg-Scanner", font_size='24sp'))
        layout.add_widget(self.btn_start)
        self.cam_screen.add_widget(layout)
        
        self.preview_screen = PreviewScreen(name='preview_screen')
        
        self.sm.add_widget(self.cam_screen)
        self.sm.add_widget(self.preview_screen)

        if platform == 'android':
            activity.bind(on_activity_result=self.on_result)
            self.photo_path = join(self.user_data_dir, "temp_photo.jpg")

        return self.sm

    def manage_camera_start(self, instance):
        if platform == 'android':
            request_permissions([Permission.CAMERA, Permission.WRITE_EXTERNAL_STORAGE], 
                                callback=self.on_perms)
        else:
            self.preview_screen.touch_img.source = "test.png" # Dummy für PC
            self.sm.current = 'preview_screen'

    def on_perms(self, permissions, grants):
        if all(grants): self.open_camera_android()

    def open_camera_android(self):
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Intent = autoclass('android.content.Intent')
        MediaStore = autoclass('android.provider.MediaStore')
        Uri = autoclass('android.net.Uri')
        File = autoclass('java.io.File')

        intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        file_obj = File(self.photo_path)
        # Für moderne Android-Versionen braucht man eigentlich einen FileProvider. 
        # Zur Vereinfachung hier der direkte Weg für den Intent-Result-Trigger:
        self.intent_uri = Uri.fromFile(file_obj)
        intent.putExtra(MediaStore.EXTRA_OUTPUT, self.intent_uri)
        
        PythonActivity.mActivity.startActivityForResult(intent, 101)

    @mainthread
    def on_result(self, requestCode, resultCode, intent):
        if requestCode == 101 and resultCode == -1:
            # Foto wurde gemacht!
            self.preview_screen.touch_img.source = self.photo_path
            self.preview_screen.touch_img.reload()
            self.sm.current = 'preview_screen'

if __name__ == "__main__":
    MainApp().run()
