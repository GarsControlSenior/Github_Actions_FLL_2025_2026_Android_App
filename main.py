import os
from datetime import datetime

import cv2
import numpy as np
from PIL import Image as PILImage, ImageOps

import kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Ellipse
from kivy.graphics.texture import Texture
from kivy.utils import platform
from kivy.clock import Clock, mainthread
from kivy.core.window import Window

# Plyer für native Features
from plyer import camera, share

# --- Bildverarbeitungsklasse ---
class ImageProcessor:
    def order_points(self, pts):
        """Sortiert Punkte: oben-links, oben-rechts, unten-rechts, unten-links."""
        rect = np.zeros((4, 2), dtype="float32")
        pts = np.array(pts)
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        return rect

    def perspective_correct(self, img, corners):
        """Führt die perspektivische Entzerrung durch."""
        try:
            rect = self.order_points(corners)
            (tl, tr, br, bl) = rect

            widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
            widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
            maxWidth = max(int(widthA), int(widthB))

            heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
            heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
            maxHeight = max(int(heightA), int(heightB))

            if maxWidth <= 0 or maxHeight <= 0: return None

            dst = np.array([
                [0, 0], [maxWidth - 1, 0],
                [maxWidth - 1, maxHeight - 1], [0, maxHeight - 1]], dtype="float32")

            M = cv2.getPerspectiveTransform(rect, dst)
            return cv2.warpPerspective(img, M, (maxWidth, maxHeight))
        except Exception as e:
            print(f"Fehler bei Entzerrung: {e}")
            return None

    def cv2_to_texture(self, img):
        """Konvertiert OpenCV-Bild in Kivy-Textur."""
        try:
            buf = cv2.flip(img, 0)
            buf = cv2.cvtColor(buf, cv2.COLOR_BGR2RGB)
            texture = Texture.create(size=(img.shape[1], img.shape[0]), colorfmt='rgb')
            texture.blit_buffer(buf.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
            return texture
        except: return None

# --- UI: Ziehbare Eckpunkte ---
class DraggableCorner(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(60), dp(60)) 
        with self.canvas:
            Color(1, 0, 0, 0.7)
            self.ellipse = Ellipse(pos=self.pos, size=self.size)
        self.bind(pos=self.update_ellipse)

    def update_ellipse(self, *args):
        self.ellipse.pos = self.pos

    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            self.center = touch.pos
            if self.parent: self.parent.update_lines()
            return True
        return super().on_touch_move(touch)

# --- Screen 1: Startbildschirm ---
class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=50, spacing=20)
        layout.add_widget(Label(text="DocScan Ortographer", font_size='24sp', size_hint=(1, 0.6)))
        
        btn = Button(text="Kamera öffnen", size_hint=(1, 0.2), background_color=(0.1, 0.5, 0.8, 1))
        btn.bind(on_release=self.take_photo)
        layout.add_widget(btn)
        self.add_widget(layout)
        
        self.tmp_path = os.path.join(App.get_running_app().user_data_dir, 'capture.jpg')

    def take_photo(self, *args):
        try:
            camera.take_picture(filename=self.tmp_path, on_complete=self.on_complete)
        except Exception as e:
            # Fallback für PC-Tests
            print(f"Kamera-Fehler: {e}")
            if os.path.exists("test.jpg"): self.on_complete("test.jpg")

    def on_complete(self, path):
        if os.path.exists(path):
            Clock.schedule_once(lambda dt: self.switch_to_editor(path), 0)

    def switch_to_editor(self, path):
        self.manager.get_screen('editor').load_image(path)
        self.manager.current = 'editor'

# --- Screen 2: Editor ---
from kivy.metrics import dp

class EditorScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.processor = ImageProcessor()
        self.cv_image = None
        self.processed_image = None
        self.state = "crop" # crop oder share

        self.layout = FloatLayout()
        self.img_view = Image(pos_hint={'center_x': .5, 'center_y': .55}, allow_stretch=True, keep_ratio=True)
        self.layout.add_widget(self.img_view)

        # Interaktions-Overlay
        self.overlay = FloatLayout()
        self.layout.add_widget(self.overlay)
        self.corners = [DraggableCorner() for _ in range(4)]
        for c in self.corners: self.overlay.add_widget(c)
        
        with self.overlay.canvas.after:
            Color(0, 1, 0, 1)
            self.line = Line(width=dp(2))

        # Buttons
        footer = BoxLayout(size_hint=(1, 0.1), pos_hint={'bottom': 0}, padding=dp(5))
        self.btn_back = Button(text="Abbrechen")
        self.btn_back.bind(on_release=self.go_back)
        self.btn_main = Button(text="Zuschneiden", background_color=(0, 0.7, 0, 1))
        self.btn_main.bind(on_release=self.action)
        
        footer.add_widget(self.btn_back)
        footer.add_widget(self.btn_main)
        self.layout.add_widget(footer)
        self.add_widget(self.layout)

    def load_image(self, path):
        # RAM & EXIF Fix
        pil_img = PILImage.open(path)
        pil_img = ImageOps.exif_transpose(pil_img)
        
        # Skalierung zum Bearbeiten (max 1200px)
        pil_img.thumbnail((1200, 1200))
        
        self.cv_image = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        self.img_view.texture = self.processor.cv2_to_texture(self.cv_image)
        
        self.reset_ui()
        Clock.schedule_once(self.init_corners, 0.2)

    def init_corners(self, dt):
        w, h = self.img_view.norm_image_size
        cx, cy = self.img_view.center
        offset_w, offset_h = w * 0.35, h * 0.35
        self.corners[0].center = (cx - offset_w, cy + offset_h)
        self.corners[1].center = (cx + offset_w, cy + offset_h)
        self.corners[2].center = (cx + offset_w, cy - offset_h)
        self.corners[3].center = (cx - offset_w, cy - offset_h)
        self.update_lines()

    def update_lines(self, *args):
        pts = []
        for i in [0, 1, 2, 3, 0]:
            pts.extend([self.corners[i].center_x, self.corners[i].center_y])
        self.line.points = pts

    def action(self, *args):
        if self.state == "crop":
            self.do_crop()
        else:
            self.do_share()

    def do_crop(self):
        norm = self.img_view.norm_image_size
        img_x = self.img_view.center_x - norm[0]/2
        img_y = self.img_view.center_y - norm[1]/2
        h_real, w_real = self.cv_image.shape[:2]
        
        pts = []
        for c in self.corners:
            rx = (c.center_x - img_x) / norm[0]
            ry = 1.0 - ((c.center_y - img_y) / norm[1])
            pts.append([rx * w_real, ry * h_real])
            
        res = self.processor.perspective_correct(self.cv_image, pts)
        if res is not None:
            self.processed_image = res
            self.img_view.texture = self.processor.cv2_to_texture(res)
            self.state = "share"
            self.btn_main.text = "Bild teilen"
            self.btn_main.background_color = (0, 0.4, 0.9, 1)
            for c in self.corners: c.opacity = 0
            self.line.points = []

    def do_share(self):
        fname = f"Scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        fpath = os.path.join(App.get_running_app().user_data_dir, fname)
        
        # Speichern via Pillow (Qualität 95)
        rgb = cv2.cvtColor(self.processed_image, cv2.COLOR_BGR2RGB)
        PILImage.fromarray(rgb).save(fpath, "JPEG", quality=95)
        
        try:
            share.share_file(fpath)
        except:
            print("Teilen nicht möglich")

    def reset_ui(self):
        self.state = "crop"
        self.btn_main.text = "Zuschneiden"
        self.btn_main.background_color = (0, 0.7, 0, 1)
        for c in self.corners: c.opacity = 1

    def go_back(self, *args):
        self.manager.current = 'menu'

# --- App Container ---
class ScannerApp(App):
    def build(self):
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            from android import api_version
            # Dynamische Rechteprüfung für Android 13+
            perms = [Permission.CAMERA]
            if api_version >= 33:
                perms.append(Permission.READ_MEDIA_IMAGES)
            else:
                perms.append(Permission.READ_EXTERNAL_STORAGE)
            request_permissions(perms)

        sm = ScreenManager()
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(EditorScreen(name='editor'))
        return sm

    def on_pause(self): return True # Verhindert Absturz bei Kamera-Wechsel

if __name__ == '__main__':
    ScannerApp().run()
