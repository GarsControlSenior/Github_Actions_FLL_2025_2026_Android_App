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
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Ellipse
from kivy.graphics.texture import Texture
from kivy.utils import platform
from kivy.clock import Clock
from kivy.metrics import dp

# Plyer nur importieren, wenn nötig
try:
    from plyer import camera, share
except ImportError:
    camera = None
    share = None

class ImageProcessor:
    def order_points(self, pts):
        rect = np.zeros((4, 2), dtype="float32")
        pts = np.array(pts)
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)] # Top-Left
        rect[2] = pts[np.argmax(s)] # Bottom-Right
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)] # Top-Right
        rect[3] = pts[np.argmax(diff)] # Bottom-Left
        return rect

    def perspective_correct(self, img, corners):
        try:
            rect = self.order_points(corners)
            (tl, tr, br, bl) = rect
            widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
            widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
            maxWidth = max(int(widthA), int(widthB))
            heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
            heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
            maxHeight = max(int(heightA), int(heightB))
            dst = np.array([[0, 0], [maxWidth-1, 0], [maxWidth-1, maxHeight-1], [0, maxHeight-1]], dtype="float32")
            M = cv2.getPerspectiveTransform(rect, dst)
            return cv2.warpPerspective(img, M, (maxWidth, maxHeight))
        except Exception as e:
            print(f"Fehler Transformation: {e}")
            return None

    def cv2_to_texture(self, img):
        try:
            buf = cv2.flip(img, 0)
            buf = cv2.cvtColor(buf, cv2.COLOR_BGR2RGB)
            texture = Texture.create(size=(img.shape[1], img.shape[0]), colorfmt='rgb')
            texture.blit_buffer(buf.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
            return texture
        except: return None

class DraggableCorner(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(50), dp(50))
        with self.canvas:
            Color(1, 0, 0, 0.7)
            self.ellipse = Ellipse(pos=self.pos, size=self.size)
        self.bind(pos=lambda *x: setattr(self.ellipse, 'pos', self.pos))

    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            self.center = touch.pos
            self.parent.update_lines()
            return True

class MenuScreen(Screen):
    def take_photo(self):
        # Pfad sicherstellen
        path = os.path.join(App.get_running_app().user_data_dir, 'input.jpg')
        if camera:
            try:
                camera.take_picture(filename=path, on_complete=self.done)
            except Exception as e:
                print(f"Kamera Fehler: {e}")
                self.done(path) # Fallback
        else:
            self.done(path)

    def done(self, path):
        if os.path.exists(path):
            Clock.schedule_once(lambda dt: self.next(path), 0.5)

    def next(self, path):
        self.manager.get_screen('editor').load(path)
        self.manager.current = 'editor'

class EditorScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.proc = ImageProcessor()
        self.cv_img = None
        self.res_img = None
        
        layout = BoxLayout(orientation='vertical')
        self.fl = FloatLayout()
        self.img_display = Image(allow_stretch=True, keep_ratio=True)
        self.fl.add_widget(self.img_display)
        
        self.corners = [DraggableCorner() for _ in range(4)]
        for c in self.corners: self.fl.add_widget(c)
        
        with self.fl.canvas.after:
            Color(0, 1, 0, 1)
            self.line = Line(width=dp(1.5), close=True)
            
        layout.add_widget(self.fl)
        
        btns = BoxLayout(size_hint_y=None, height=dp(60), padding=dp(10))
        self.btn_main = Button(text="Zuschneiden", on_release=self.action)
        btns.add_widget(Button(text="Abbrechen", on_release=self.reset_to_menu))
        btns.add_widget(self.btn_main)
        layout.add_widget(btns)
        self.add_widget(layout)

    def load(self, path):
        try:
            p = PILImage.open(path)
            p = ImageOps.exif_transpose(p)
            p.thumbnail((1500, 1500)) # RAM Schutz: Bild verkleinern
            self.cv_img = cv2.cvtColor(np.array(p), cv2.COLOR_RGB2BGR)
            self.img_display.texture = self.proc.cv2_to_texture(self.cv_img)
            self.reset_ui()
            Clock.schedule_once(self.init_pts, 0.5)
        except Exception as e:
            print(f"Ladefehler: {e}")

    def init_pts(self, *args):
        # Sicherer Check der Bildgröße in der UI
        iw, ih = self.img_display.norm_image_size
        if iw <= 1: # Falls noch nicht gerendert, nochmal versuchen
            Clock.schedule_once(self.init_pts, 0.2)
            return
            
        cx, cy = self.img_display.center
        pts = [(cx-iw*0.3, cy+ih*0.3), (cx+iw*0.3, cy+ih*0.3), 
               (cx+iw*0.3, cy-ih*0.3), (cx-iw*0.3, cy-ih*0.3)]
        for i, p in enumerate(pts): self.corners[i].center = p
        self.update_lines()

    def update_lines(self):
        self.line.points = [p for c in self.corners for p in c.center]

    def action(self, *args):
        if self.btn_main.text == "Zuschneiden":
            self.do_crop()
        else:
            self.do_share()

    def do_crop(self):
        if self.cv_img is None: return
        
        iw, ih = self.img_display.norm_image_size
        if iw == 0 or ih == 0: return # Crash-Schutz: Division durch Null
        
        ix = self.img_display.center_x - iw/2
        iy = self.img_display.center_y - ih/2
        h_r, w_r = self.cv_img.shape[:2]
        
        pts = []
        for c in self.corners:
            # Umrechnung UI-Koordinate -> Bild-Pixel
            nx = (c.center_x - ix) / iw
            ny = 1 - (c.center_y - iy) / ih
            pts.append([nx * w_r, ny * h_r])
        
        self.res_img = self.proc.perspective_correct(self.cv_img, pts)
        if self.res_img is not None:
            self.img_display.texture = self.proc.cv2_to_texture(self.res_img)
            self.btn_main.text = "Teilen"
            for c in self.corners: c.opacity = 0
            self.line.points = []

    def do_share(self):
        if self.res_img is None: return
        path = os.path.join(App.get_running_app().user_data_dir, 'scan.jpg')
        cv2.imwrite(path, self.res_img)
        if share:
            try: share.share_file(path)
            except: pass

    def reset_ui(self):
        self.btn_main.text = "Zuschneiden"
        for c in self.corners: c.opacity = 1

    def reset_to_menu(self, *args):
        self.manager.current = 'menu'

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
