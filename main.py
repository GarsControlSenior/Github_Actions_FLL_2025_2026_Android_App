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
        super().__init__(orientation="vertical", padding=40, spacing=30, **kwargs)

        # Schwarzer Hintergrund
        Window.clearcolor = (0, 0, 0, 1)

        # ── Obere Leiste mit Fragezeichen ─────────────────
        top_bar = BoxLayout(orientation="horizontal", size_hint=(1, 0.15))

        top_bar.add_widget(Label())  # Platzhalter links

        help_btn = Button(
            text="?",
            font_size=28,
            size_hint=(None, None),
            size=(60, 60)
        )
        help_btn.bind(on_press=self.show_help)

        top_bar.add_widget(help_btn)
        self.add_widget(top_bar)

        # ── Große Frage ─────────────────
        question = Label(
            text="Möchten Sie die App mit dem Arduino durchführen?",
            color=(1, 1, 1, 1),
            font_size=42,
            halign="center",
            valign="middle",
            size_hint=(1, 0.45)
        )
        question.bind(size=question.setter("text_size"))
        self.add_widget(question)

        # ── Buttons nebeneinander ─────────────────
        button_row = BoxLayout(orientation="horizontal", spacing=30, size_hint=(1, 0.25))

        btn_yes = Button(text="Ja", font_size=26)
        btn_no = Button(text="Nein", font_size=26)

        btn_yes.bind(on_press=self.handle_click)
        btn_no.bind(on_press=self.handle_click)

        button_row.add_widget(btn_yes)
        button_row.add_widget(btn_no)

        self.add_widget(button_row)

    # ── Fragezeichen Popup ─────────────────
    def show_help(self, instance):
        content = Label(
            text="Bei Fragen können Sie uns einfach eine E-Mail schicken.",
            font_size=20,
            halign="center",
            valign="middle"
        )
        content.bind(size=content.setter("text_size"))

        popup = Popup(
            title="Hilfe",
            content=content,
            size_hint=(0.8, 0.4)
        )
        popup.open()

    # ── Klick auf Ja / Nein ─────────────────
    def handle_click(self, instance):
        if request_permissions:
            request_permissions([Permission.CAMERA], self.after_permission)
        else:
            self.open_camera()

    def after_permission(self, permissions, results):
        if all(results):
            self.open_camera()

    # ── Kamera öffnen ─────────────────
    def open_camera(self):
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Intent = autoclass('android.content.Intent')
        MediaStore = autoclass('android.provider.MediaStore')

        activity = PythonActivity.mActivity
        intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        activity.startActivity(intent)


class MainApp(App):
    def build(self):
        return StartScreen()


if __name__ == "__main__":
    MainApp().run()
