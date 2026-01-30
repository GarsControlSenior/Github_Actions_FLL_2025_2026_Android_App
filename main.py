from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.utils import platform
from kivy.clock import mainthread
from os.path import join

if platform == "android":
    from jnius import autoclass
    from android.permissions import request_permissions, Permission
    from android import activity


class CameraApp(App):

    def build(self):
        self.layout = BoxLayout(orientation="vertical")
        self.label = Label(text="Warte auf Kamera …", size_hint_y=0.1)
        self.image = Image(allow_stretch=True, keep_ratio=True)

        self.layout.add_widget(self.label)
        self.layout.add_widget(self.image)

        if platform == "android":
            activity.bind(on_activity_result=self.on_activity_result)
            self.request_camera_permission()
        else:
            self.label.text = "Nur auf Android nutzbar"

        return self.layout

    # =====================
    # BERECHTIGUNG
    # =====================
    def request_camera_permission(self):
        request_permissions([Permission.CAMERA], self.on_permission_result)

    def on_permission_result(self, permissions, grants):
        if grants and grants[0]:
            self.open_camera()
        else:
            self.label.text = "Kamera-Berechtigung verweigert"

    # =====================
    # KAMERA ÖFFNEN
    # =====================
    def open_camera(self):
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Intent = autoclass("android.content.Intent")
        MediaStore = autoclass("android.provider.MediaStore")
        File = autoclass("java.io.File")
        Uri = autoclass("android.net.Uri")

        self.photo_path = join(self.user_data_dir, "photo.jpg")
        photo_file = File(self.photo_path)
        photo_uri = Uri.fromFile(photo_file)

        intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        intent.putExtra(MediaStore.EXTRA_OUTPUT, photo_uri)

        PythonActivity.mActivity.startActivityForResult(intent, 1)

    # =====================
    # FOTO ZURÜCK
    # =====================
    @mainthread
    def on_activity_result(self, request_code, result_code, intent):
        if request_code == 1 and result_code == -1:
            self.image.source = self.photo_path
            self.image.reload()
            self.label.text = "Foto aufgenommen"
        else:
            self.label.text = "Kein Foto aufgenommen"


if __name__ == "__main__":
    CameraApp().run()
