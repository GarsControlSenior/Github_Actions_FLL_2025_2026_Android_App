import os
import cv2
import numpy as np
from PIL import Image as PILImage, ImageOps

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
from kivy.clock import Clock
from kivy.metrics import dp

# Plyer für Kamera & Teilen sicher einbinden
try:
    from plyer import camera, share
except Exception:
    camera = None
    share = None

class ImageProcessor:
    """Verarbeitet die Bildtransformationen mit OpenCV."""
    
    def order_points(self, pts):
        rect = np.zeros((4, 2), dtype="float32")
        pts = np.array(pts)
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]  # Top-Left
        rect[2] = pts[np.argmax(s)]  # Bottom-Right
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)] # Top-Right
        rect[3] = pts[np.argmax(diff)] # Bottom-Left
        return rect

    def perspective_correct(self, img, corners):
        try:
            rect = self.order_points(corners)
            (tl, tr, br, bl) = rect
            
            # Berechnung der neuen Breite/Höhe
            widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
            widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
            maxWidth = max(int(widthA), int(widthB))
            
            heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
            heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
            maxHeight = max(int(heightA), int(heightB))
            
            dst = np.array([
                [0, 0],
                [maxWidth - 1, 0],
                [maxWidth - 1, maxHeight - 1],
                [0, maxHeight - 1]
            ], dtype="float32")
            
            M = cv2.getPerspectiveTransform(rect, dst)
            return cv2.warpPerspective(img, M, (maxWidth, maxHeight))
        except Exception:
            return None

    def cv2_to_texture(self, img):
        """Konvertiert OpenCV-Bild in Kivy-Textur."""
        try:
            buf = cv2.flip(img, 0)
            buf = cv2.cvtColor(buf, cv2.COLOR_BGR2RGB)
            texture = Texture.create(size=(img.shape[1], img.shape[0]), colorfmt='rgb')
            texture.blit_buffer(buf.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
            return texture
        except Exception:
            return None

class DraggableCorner(Widget):
    """Ein ziehbarer roter Punkt für die Eckenauswahl."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(50), dp(50))
        with self.canvas:
            Color(1, 0, 0, 0.8)
            self.ellipse = Ellipse(pos=self.pos, size=self.size)
        self.bind(pos=lambda *x: setattr(self.ellipse, 'pos', self.pos))

    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            self.center = touch.pos
            self.parent.update_lines()
            return True

class MenuScreen(Screen):
    """Startbildschirm der App."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20))
        
        layout.add_widget(Label(text="Beleg Scanner", font_size=dp(32), size_hint_y=0.2))
        
        self.status_lbl = Label(text="Bereit für Scan", size_hint_y=0.6)
        layout.add_widget(self.status_lbl)
        
        btn = Button(text="Kamera öffnen", size_hint_y=0.2, background_color=(0, 0.5, 1, 1))
        btn.bind(on_release=self.take_photo)
        layout.add_widget(btn)
        
        self.add_widget(layout)

    def take_photo(self, *args):
        path = os.path.join(App.get_running_app().user_data_dir, 'input.jpg')
        if platform == 'android' and camera:
            try:
                camera.take_picture(filename=path, on_complete=self.done)
            except Exception as e:
                self.status_lbl.text = f"Fehler: {str(e)}"
        else:
            # Fallback für PC-Tests: Erstellt ein weißes Rechteck
            dummy = np.zeros((1200, 800, 3), dtype=np.uint8)
            cv2.rectangle(dummy, (150, 150), (650, 1050), (255, 255, 255), -1)
            cv2.imwrite(path, dummy)
            self.done(path)

    def done(self, path):
        if os.path.exists(path):
            Clock.schedule_once(lambda dt: self.next(path), 0.5)

    def next(self, path):
        self.manager.get_screen('editor').load(path)
        self.manager.current = 'editor'

class EditorScreen(Screen):
    """Bildschirm zum Zuschneiden und Korrigieren."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.proc = ImageProcessor()
        self.cv_img = None
        self.res_img = None
        
        root = BoxLayout(orientation='vertical')
        
        # Arbeitsbereich
        self.fl = FloatLayout()
        self.img_widget = Image(allow_stretch=True, keep_ratio=True)
        self.fl.add_widget(self.img_widget)
        
        self.corners = [DraggableCorner() for _ in range(4)]
        for c in self.corners: self.fl.add_widget(c)
        
        with self.fl.canvas.after:
            Color(0, 1, 0, 1)
            self.line = Line(width=dp(2), close=True)
            
        root.add_widget(self.fl)
        
        # Buttons
        btns = BoxLayout(size_hint_y=None, height=dp(65), padding=dp(5), spacing=dp(5))
        self.btn_action = Button(text="Zuschneiden")
        self.btn_action.bind(on_release=self.action)
        
        btn_back = Button(text="Abbrechen")
        btn_back.bind(on_release=self.go_back)
        
        btns.add_widget(btn_back)
        btns.add_widget(self.btn_action)
        root.add_widget(btns)
        
        self.add_widget(root)

    def go_back(self, *args):
        self.manager.current = 'menu'

    def load(self, path):
        try:
            # RAM-Schutz: Bild direkt verkleinert laden
            p = PILImage.open(path)
            p = ImageOps.exif_transpose(p)
            p.thumbnail((1200, 1200)) 
            
            self.cv_img = cv2.cvtColor(np.array(p), cv2.COLOR_RGB2BGR)
            self.img_widget.texture = self.proc.cv2_to_texture(self.cv_img)
            
            self.reset_ui()
            Clock.schedule_once(self.init_pts, 0.5)
        except Exception:
            self.go_back()

    def init_pts(self, *args):
        # Berechnet die Position der Punkte relativ zum angezeigten Bild
        w, h = self.img_widget.norm_image_size
        if w <= 1: 
            Clock.schedule_once(self.init_pts, 0.2)
            return

        cx, cy = self.img_widget.center
        pts = [
            (cx - w*0.3, cy + h*0.3), (cx + w*0.3, cy + h*0.3),
            (cx + w*0.3, cy - h*0.3), (cx - w*0.3, cy - h*0.3)
        ]
        for i, p in enumerate(pts):
            self.corners[i].center = p
            self.corners[i].opacity = 1
        self.update_lines()

    def update_lines(self):
        self.line.points = [p for c in self.corners for p in c.center]

    def action(self, *args):
        if self.btn_action.text == "Zuschneiden":
            self.do_crop()
        else:
            self.do_share()

    def do_crop(self):
        if self.cv_img is None: return
        
        # Koordinatenumrechnung UI -> Bildpixel
        iw, ih = self.img_widget.norm_image_size
        ix = self.img_widget.center_x - iw/2
        iy = self.img_widget.center_y - ih/2
        h_orig, w_orig = self.cv_img.shape[:2]
        
        pts = []
        for c in self.corners:
            nx = (c.center_x - ix) / iw
            ny = 1.0 - (c.center_y - iy) / ih
            pts.append([nx * w_orig, ny * h_orig])
        
        res = self.proc.perspective_correct(self.cv_img, pts)
        if res is not None:
            self.res_img = res
            self.img_widget.texture = self.proc.cv2_to_texture(self.res_img)
            self.btn_action.text = "Teilen"
            for c in self.corners: c.opacity = 0
            self.line.points = []

    def do_share(self):
        if self.res_img is None: return
        path = os.path.join(App.get_running_app().user_data_dir, 'scan.jpg')
        cv2.imwrite(path, self.res_img)
        if share:
            try: share.share_file(path)
            except Exception: pass

    def reset_ui(self):
        self.btn_action.text = "Zuschneiden"
        for c in self.corners: c.opacity = 1

class MainApp(App):
    def build(self):
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.CAMERA, Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])
        
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(EditorScreen(name='editor'))
        return sm

if __name__ == '__main__':
    MainApp().run()
