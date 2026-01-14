import cv2
import numpy as np
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.camera import Camera
from kivy.uix.button import Button
from kivy.graphics.texture import Texture
from kivy.utils import platform
from kivy.clock import Clock

# Falls wir auf Android sind, brauchen wir Berechtigungen
if platform == 'android':
    from android.permissions import request_permissions, Permission
    request_permissions([Permission.CAMERA, Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])

class OrthoCameraApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical')

        # 1. Kamera-Widget
        # index=0 ist meist die Rückkamera
        self.camera = Camera(play=True, resolution=(1280, 720))
        self.layout.add_widget(self.camera)

        # 2. Aufnahme-Button
        self.capture_button = Button(
            text="Orthofoto erstellen",
            size_hint=(1, 0.15),
            background_color=(0, 0.7, 1, 1)
        )
        self.capture_button.bind(on_press=self.process_image)
        self.layout.add_widget(self.capture_button)

        return self.layout

    def process_image(self, *args):
        # Hol dir das aktuelle Bild von der Kamera-Textur
        texture = self.camera.texture
        size = texture.size
        pixels = texture.pixels
        
        # Umwandlung von Kivy-Textur in OpenCV-Format (numpy array)
        frame = np.frombuffer(pixels, dtype=np.uint8)
        frame = frame.reshape(int(size[1]), int(size[0]), 4)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
        frame = cv2.flip(frame, 0) # Kivy Texturen sind oft vertikal gespiegelt

        # BILDVERARBEITUNG:
        # Wir versuchen das größte Rechteck (das Papier) zu finden
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blurred, 75, 200)

        contours, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

        screen_cnt = None
        for c in contours:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            if len(approx) == 4: # Wir haben 4 Ecken gefunden!
                screen_cnt = approx
                break

        if screen_cnt is not None:
            # Perspektivische Korrektur durchführen
            warped = self.four_point_transform(frame, screen_cnt.reshape(4, 2))
            
            # Ergebnis speichern
            filename = "orthofoto_result.jpg"
            cv2.imwrite(filename, warped)
            print(f"Erfolg! Bild gespeichert als {filename}")
            self.capture_button.text = "Gespeichert!"
            Clock.schedule_once(self.reset_button, 2)
        else:
            print("Kein Rechteck erkannt. Bitte Papier deutlicher zeigen.")
            self.capture_button.text = "Fehler: Kein Papier erkannt"
            Clock.schedule_once(self.reset_button, 2)

    def reset_button(self, dt):
        self.capture_button.text = "Orthofoto erstellen"

    def four_point_transform(self, image, pts):
        # Hilfsfunktion zur Entzerrung
        rect = self.order_points(pts)
        (tl, tr, br, bl) = rect

        # Breite und Höhe des neuen Bildes berechnen
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
            [0, maxHeight - 1]], dtype="float32")

        M = cv2.getPerspectiveTransform(rect, dst)
        return cv2.warpPerspective(image, M, (maxWidth, maxHeight))

    def order_points(self, pts):
        # Sortiert die Punkte: oben-links, oben-rechts, unten-rechts, unten-links
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        return rect

if __name__ == '__main__':
    OrthoCameraApp().run()
