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

# Plyer Import sicher machen
try:
    from plyer import camera, share
except ImportError:
    camera = None
    share = None
    print("Plyer nicht gefunden (PC Modus?)")

class ImageProcessor:
    def order_points(self, pts):
        rect = np.zeros((4, 2), dtype="float32")
        pts = np.array(pts)
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)] # TL
        rect[2] = pts[np.argmax(s)] # BR
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)] # TR
        rect[3] = pts[np.argmax(diff)] # BL
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
            print(f"Fehler bei Perspektive: {e}")
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
            Color(1, 0, 0, 0.8) # Rote Punkte für bessere Sichtbarkeit
            self.ellipse = Ellipse(pos=self.pos, size=self.size)
        self.bind(pos=lambda *x: setattr(self.ellipse, 'pos', self.pos))

    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            self.center = touch.pos
            self.parent.update_lines()
            return True

# --- HIER WAR DER FEHLER: MenuScreen braucht Widgets! ---
class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(40), spacing=dp(20))
        
        # Titel
        layout.add_widget(Label(text="Scanner App", font_size=dp(30), size_hint_y=0.2))
        
        # Info
        self.info_lbl = Label(text="Drücke Start um ein Foto zu machen", size_hint_y=0.6)
        layout.add_widget(self.info_lbl)
        
        # Kamera Button
        btn = Button(text="Kamera starten", size_hint_y=0.2, background_color=(0.2, 0.6, 1, 1))
        btn.bind(on_release=self.take_photo)
        layout.add_widget(btn)
        
        self.add_widget(layout)

    def take_photo(self, *args):
        filename = 'input.jpg'
        target = os.path.join(App.get_running_app().user_data_dir, filename)
        
        # Falls Datei schon existiert, löschen (verhindert Cache-Probleme)
        if os.path.exists(target):
            try: os.remove(target)
            except: pass

        if camera:
            try:
                # Plyer öffnet die native Kamera-App
                camera.take_picture(filename=target, on_complete=self.done)
            except Exception as e:
                self.info_lbl.text = f"Fehler: {e}"
        else:
            # PC Debug Modus: Simuliere ein Bild, falls keine Kamera da ist
            self.info_lbl.text = "Keine Kamera gefunden (PC Modus)"
            # Erstelle ein Dummy-Bild zum Testen
            dummy = np.zeros((1000, 800, 3), dtype=np.uint8)
            cv2.rectangle(dummy, (200, 200), (600, 800), (255, 255, 255), -1)
            cv2.imwrite(target, dummy)
            self.done(target)

    def done(self, path):
        # Verzögerung, damit die Datei sicher gespeichert ist
        Clock.schedule_once(lambda dt: self.next(path), 1.0)

    def next(self, path):
        if os.path.exists(path):
            self.manager.get_screen('editor').load(path)
            self.manager.current = 'editor'
        else:
            self.info_lbl.text = "Fehler: Bild wurde nicht gespeichert."

class EditorScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.proc = ImageProcessor()
        self.cv_img = None
        self.res_img = None
        
        root = BoxLayout(orientation='vertical')
        
        # Editor Bereich
        self.fl = FloatLayout()
        self.img = Image(allow_stretch=True, keep_ratio=True)
        self.fl.add_widget(self.img)
        
        self.corners = [DraggableCorner() for _ in range(4)]
        for c in self.corners: self.fl.add_widget(c)
        
        with self.fl.canvas.after:
            Color(0, 1, 0, 1)
            self.line = Line(width=dp(2), close=True)
            
        root.add_widget(self.fl)
        
        # Button Leiste
        btns = BoxLayout(size_hint_y=None, height=dp(60), padding=dp(5))
        
        btn_back = Button(text="Zurück")
        btn_back.bind(on_release=self.go_back)
        
        self.btn_main = Button(text="Zuschneiden")
        self.btn_main.bind(on_release=self.action)
        
        btns.add_widget(btn_back)
        btns.add_widget(self.btn_main)
        root.add_widget(btns)
        
        self.add_widget(root)

    def go_back(self, *args):
        self.manager.current = 'menu'

    def load(self, path):
        try:
            # Bild laden und drehen
            p = PILImage.open(path)
            p = ImageOps.exif_transpose(p)
            p.thumbnail((1024, 1024)) # WICHTIG: Kleiner machen für RAM
            
            self.cv_img = cv2.cvtColor(np.array(p), cv2.COLOR_RGB2BGR)
            self.img.texture = self.proc.cv2_to_texture(self.cv_img)
            
            self.reset_ui()
            # Kurz warten, bis das Layout steht, dann Punkte setzen
            Clock.schedule_once(self.init_pts, 0.5)
        except Exception as e:
            print(f"Fehler beim Laden: {e}")

    def init_pts(self, *args):
        norm_w, norm_h = self.img.norm_image_size
        # Wenn Bild noch nicht geladen, abbrechen oder neu versuchen
        if norm_w == 0: 
            Clock.schedule_once(self.init_pts, 0.2)
            return

        cx, cy = self.img.center
        w, h = norm_w, norm_h
        
        # Punkte etwas mittig anordnen
        pts = [
            (cx - w*0.3, cy + h*0.3), # TL
            (cx + w*0.3, cy + h*0.3), # TR
            (cx + w*0.3, cy - h*0.3), # BR
            (cx - w*0.3, cy - h*0.3)  # BL
        ]
        
        for i, p in enumerate(pts):
            self.corners[i].center = p
            self.corners[i].opacity = 1
        
        self.update_lines()

    def update_lines(self):
        self.line.points = [c for corner in self.corners for c in corner.center]

    def action(self, *args):
        if self.btn_main.text == "Zuschneiden":
            self.do_crop()
        else:
            self.do_share()

    def do_crop(self):
        if self.cv_img is None: return
        
        norm_w, norm_h = self.img.norm_image_size
        if norm_w == 0: return

        cx = self.img.center_x - norm_w / 2
        cy = self.img.center_y - norm_h / 2
        
        orig_h, orig_w = self.cv_img.shape[:2]
        
        pts = []
        for c in self.corners:
            # Umrechnen von Screen-Koordinaten in Bild-Koordinaten
            x_ratio = (c.center_x - cx) / norm_w
            y_ratio = 1.0 - (c.center_y - cy) / norm_h # Y ist in Kivy unten 0, in CV2 oben 0
            
            pts.append([x_ratio * orig_w, y_ratio * orig_h])
        
        res = self.proc.perspective_correct(self.cv_img, pts)
        
        if res is not None:
            self.res_img = res
            self.img.texture = self.proc.cv2_to_texture(self.res_img)
            self.btn_main.text = "Teilen"
            for c in self.corners: c.opacity = 0
            self.line.points = []

    def do_share(self):
        if self.res_img is None: return
        path = os.path.join(App.get_running_app().user_data_dir, 'scan_result.jpg')
        cv2.imwrite(path, self.res_img)
        if share:
            share.share_file(path)

    def reset_ui(self):
        self.btn_main.text = "Zuschneiden"
        for c in self.corners: c.opacity = 1

class MainApp(App):
    def build(self):
        # Berechtigungen für Android
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.CAMERA, 
                Permission.WRITE_EXTERNAL_STORAGE, 
                Permission.READ_EXTERNAL_STORAGE
            ])
            
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(EditorScreen(name='editor'))
        return sm

if __name__ == '__main__':
    MainApp().run()
