from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.graphics import Color, Line
from jnius import autoclass

# Android permissions
try:
    from android.permissions import request_permissions, Permission
except ImportError:
    request_permissions = None
    Permission = None


class WhiteFrameButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.color = (1, 1, 1, 1)
        with self.canvas.after:
            Color(1, 1, 1, 1)
            self.border = Line(rectangle=(self.x, self.y, self.width, self.height), width=2)
        self.bind(pos=self.update_border, size=self.update_border)

    def update_border(self, *args):
        self.border.rectangle = (self.x, self.y, self.width, self.height)


class StartScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", spacing=40, padding=60, **kwargs)
        Window.clearcolor = (0, 0, 0, 1)

        # ── Top bar mit Fragezeichen ──
        top = BoxLayout(size_hint=(1, 0.15))
        top.add_widget(Label())

        help_btn = WhiteFrameButton(
            text="?",
            font_size=80,
            size_hint=(None, None),
            size=(120, 120)
        )
        help_btn.bind(on_press=self.show_help)
        top.add_widget(help_btn)
        self.add_widget(top)

        # ── Große Frage ──
        question = Label(
            text="Möchten Sie die App\nmit dem Arduino durchführen?",
            font_size=72,
            color=(1, 1, 1, 1),
            halign="center",
            valign="middle",
            size_hint=(1, 0.35)
        )
        question.bind(size=question.setter("text_size"))
        self.add_widget(question)

        # ── Buttons mittig ──
        mid = BoxLayout(size_hint=(1, 0.25))
        buttons = BoxLayout(spacing=60, size_hint=(None, None), size=(800, 200))
        buttons.pos_hint = {"center_x": 0.5, "center_y": 0.5}

        btn_yes = WhiteFrameButton(text="Ja", font_size=56)
        btn_no = WhiteFrameButton(text="Nein", font_size=56)

        btn_yes.bind(on_press=self.start_camera)
        btn_no.bind(on_press=self.start_camera)

        buttons.add_widget(btn_yes)
        buttons.add_widget(btn_no)
        mid.add_widget(buttons)
        self.add_widget(mid)

    # ── Hilfe ──
    def show_help(self, instance):
        lbl = Label(
            text="Bei Fragen können Sie uns\n"
                 "einfach eine E-Mail schicken.",
            font_size=40,
            halign="center"
        )
        popup = Popup(title="Hilfe", content=lbl, size_hint=(0.85, 0.45))
        popup.open()

    # ── Kamera ──
    def start_camera(self, instance):
        if request_permissions:
            request_permissions([Permission.CAMERA], self.after_permission)
        else:
            self.open_camera()

    def after_permission(self, permissions, results):
        if all(results):
            self.open_camera()

    def open_camera(self):
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Intent = autoclass("android.content.Intent")
        MediaStore = autoclass("android.provider.MediaStore")

        activity = PythonActivity.mActivity
        intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        activity.startActivity(intent)

        self.ask_save()

    # ── Nach Foto: speichern? ──
    def ask_save(self):
        box = BoxLayout(orientation="vertical", spacing=30, padding=30)
        label = Label(
            text="Möchten Sie das Foto speichern?",
            font_size=44,
            halign="center"
        )

        btn_row = BoxLayout(spacing=40)
        btn_yes = WhiteFrameButton(text="Ja", font_size=40)
        btn_no = WhiteFrameButton(text="Nein", font_size=40)

        btn_yes.bind(on_press=self.choose_folder)
        btn_no.bind(on_press=lambda x: popup.dismiss())

        btn_row.add_widget(btn_yes)
        btn_row.add_widget(btn_no)

        box.add_widget(label)
        box.add_widget(btn_row)

        popup = Popup(title="", content=box, size_hint=(0.9, 0.45))
        popup.open()
        self.popup = popup

    # ── Ordner auswählen ──
    def choose_folder(self, instance):
        self.popup.dismiss()
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Intent = autoclass("android.content.Intent")

        activity = PythonActivity.mActivity
        intent = Intent(Intent.ACTION_OPEN_DOCUMENT_TREE)
        activity.startActivity(intent)


class MainApp(App):
    def build(self):
        return StartScreen()


if __name__ == "__main__":
    MainApp().run()
