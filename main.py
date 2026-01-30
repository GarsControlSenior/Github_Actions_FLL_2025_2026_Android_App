from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from jnius import autoclass

class MainApp(App):
    def build(self):
        self.open_camera()
        return BoxLayout()

    def open_camera(self):
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Intent = autoclass('android.content.Intent')
        MediaStore = autoclass('android.provider.MediaStore')

        activity = PythonActivity.mActivity
        intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        activity.startActivity(intent)

if __name__ == "__main__":
    MainApp().run()
