from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.core.window import Window
from jnius import autoclass

# Android Permissions
try:
    from android.permissions import request_permissions, Permission
except ImportError:
    request_permissions = None
    Permission = None


class StartScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", spacing=40, padding=50, **kwargs)

        Window.clearcolor = (0, 0, 0, 1)

        # ❗ Größere Schrift
        self.label = Label(
            text="Möchten Sie die App mit dem Arduino durchführen?",
            color=(1, 1, 1, 1),
            font_size=34,
            halign="center",
            valign="middle"
        )
        self.label.bind(size=self.label.setter("text_size"))

        btn_yes = Button(text="Ja", font_size=24, size_hint=(1, 0.25))
        btn_no = Button(text="Nein", font_size=24, size_hint=(1, 0.25))

        btn_yes.bind(on_press=self.handle_click)
        btn_no.bind(on_press=self.handle_click)

        self.add_widget(self.label)
        self.add_widget(btn_yes)
        self.add_widget(btn_no)

    def handle_click(self, instance):
        # 👉 IMMER erst Berechtigung anfragen
        if request_permissions:
            request_permissions(
                [Permission.CAMERA],
                self.after_permission
            )
        else:
            self.open_camera()

    def after_permission(self, permissions, results):
        if all(results):
            self.open_camera()

    def open_camera(self):
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Intent = autoclass('android.content.Intent')
        MediaStore = autoclass('android.provider.MediaStore')

        activity = PythonActivity.mActivity
        intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        activity.startActivity(intent)

        # Nach Kamera → Nachfrage anzeigen
        self.ask_save()

    def ask_save(self):
        box = BoxLayout(orientation="vertical", spacing=20, padding=20)

        label = Label(
            text="Möchten Sie das gemachte Foto speichern?",
            font_size=22
        )

        btn_yes = Button(text="Ja", font_size=20)
        btn_no = Button(text="Nein", font_size=20)

        box.add_widget(label)
        box.add_widget(btn_yes)
        box.add_widget(btn_no)

        popup = Popup(
            title="Foto speichern",
            content=box,
            size_hint=(0.8, 0.4)
        )

        btn_yes.bind(on_press=lambda x: popup.dismiss())
        btn_no.bind(on_press=lambda x: popup.dismiss())

        popup.open()


class MainApp(App):
    def build(self):
        return StartScreen()


if __name__ == "__main__":
    MainApp().run()
