import os
import cv2
import numpy as np

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.properties import ListProperty
from kivy.graphics import Color, Ellipse


# ---------------------------------------------------
# Corner Handle Widget
# ---------------------------------------------------

class CornerWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size = (30, 30)

        with self.canvas:
            Color(1, 0, 0)
            self.circle = Ellipse(pos=self.pos, size=self.size)

        self.bind(pos=self.update_graphics)

    def update_graphics(self, *args):
        self.circle.pos = self.pos

    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            self.center = touch.pos
            return True
        return super().on_touch_move(touch)


# ---------------------------------------------------
# Main Perspective Screen
# ---------------------------------------------------

class PerspectiveScreen(FloatLayout):

    corners = ListProperty()

    def __init__(self, image_path, photos_dir, **kwargs):
        super().__init__(**kwargs)

        self.image_path = image_path
        self.photos_dir = photos_dir

        self.image_widget = Image(source=image_path,
                                  allow_stretch=True,
                                  keep_ratio=True)
        self.add_widget(self.image_widget)

        self.init_corners()

    # ---------------------------------------------------
    # Initial corner placement
    # ---------------------------------------------------

    def init_corners(self):
        margin = 100
        positions = [
            (margin, margin),
            (Window.width - margin, margin),
            (Window.width - margin, Window.height - margin),
            (margin, Window.height - margin),
        ]

        self.corners = []
        for pos in positions:
            c = CornerWidget()
            c.center = pos
            self.add_widget(c)
            self.corners.append(c)

    # ---------------------------------------------------
    # MAIN PERSPECTIVE FUNCTION
    # ---------------------------------------------------

    def apply_perspective(self, path):

        img = cv2.imread(path)
        if img is None:
            print("Image not found")
            return path

        h_real, w_real = img.shape[:2]

        # -----------------------------------
        # 1️⃣ Map screen coordinates to image
        # -----------------------------------
        mapped = []
        for c in self.corners:
            x = (c.center_x / Window.width) * w_real
            y = h_real - (c.center_y / Window.height) * h_real
            mapped.append([x, y])

        pts = np.array(mapped, dtype="float32")

        # -----------------------------------
        # 2️⃣ Sort points (TL, TR, BR, BL)
        # -----------------------------------
        rect = np.zeros((4, 2), dtype="float32")

        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]  # TL
        rect[2] = pts[np.argmax(s)]  # BR

        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]  # TR
        rect[3] = pts[np.argmax(diff)]  # BL

        (tl, tr, br, bl) = rect

        # -----------------------------------
        # 3️⃣ Calculate angle between top & left
        # -----------------------------------
        vec_top = tr - tl
        vec_left = bl - tl

        dot = np.dot(vec_top, vec_left)
        denom = np.linalg.norm(vec_top) * np.linalg.norm(vec_left)

        if denom == 0:
            return path

        angle = np.arccos(np.clip(dot / denom, -1.0, 1.0))
        angle_deg = np.degrees(angle)
        angle_rad = np.radians(angle_deg)

        print("Detected angle:", angle_deg)

        # -----------------------------------
        # 4️⃣ Depth ratio
        # -----------------------------------
        left_height = np.linalg.norm(bl - tl)
        right_height = np.linalg.norm(br - tr)

        depth_ratio = left_height / right_height if right_height != 0 else 1.0

        # -----------------------------------
        # 5️⃣ Compute target size
        # -----------------------------------
        width_top = np.linalg.norm(tr - tl)
        width_bottom = np.linalg.norm(br - bl)
        max_width = int(max(width_top, width_bottom))

        max_height = int(max(left_height, right_height))

        if max_width < 1 or max_height < 1:
            return path

        # -----------------------------------
        # 6️⃣ Rebuild geometry with same angle
        # -----------------------------------
        new_tl = [0, 0]
        new_tr = [max_width - 1, 0]

        new_bl_x = max_height * np.cos(angle_rad)
        new_bl_y = max_height * np.sin(angle_rad)

        new_bl = [new_bl_x, new_bl_y]

        new_br = [
            max_width - 1,
            new_bl_y / depth_ratio
        ]

        dst = np.array([new_tl, new_tr, new_br, new_bl], dtype="float32")

        # -----------------------------------
        # 7️⃣ Perspective transform
        # -----------------------------------
        M = cv2.getPerspectiveTransform(rect, dst)

        warped_height = int(max(new_bl_y, new_br[1]))
        warped_height = max(warped_height, 1)

        warped = cv2.warpPerspective(
            img,
            M,
            (max_width, warped_height)
        )

        # -----------------------------------
        # 8️⃣ Save result
        # -----------------------------------
        new_path = os.path.join(self.photos_dir, "warped_temp.png")
        cv2.imwrite(new_path, warped)

        print("Perspective corrected image saved.")

        return new_path


# ---------------------------------------------------
# Minimal App for Testing
# ---------------------------------------------------

class TestApp(App):
    def build(self):
        return PerspectiveScreen(
            image_path="test.jpg",
            photos_dir="."
        )


if __name__ == "__main__":
    TestApp().run()
