from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.core.window import Window
from jnius import autoclass

try:
    from android.permissions import request_permissions, Permission
except ImportError:
    request_permissions = None
    Permission = None


# ───────────── Schwarzer Minimal-Button ─────────────
class BlackButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 1)
        self.color = (1, 1, 1, 1)
        self.border = (0, 0, 0, 0)


# ───────────── Willkommen (nur beim ersten Start) ─────────────
class WelcomeScreen(BoxLayout):
    def __init__(self, app, **kwargs):
        super().__init__(orientation="vertical", spacing=80, padding=80, **kwargs)
        self.app = app
        Window.clearcolor = (0, 0, 0, 1)

        label = Label(
            text="Herzlich Willkommen!\n\n"
                 "Vielen Dank, dass Sie diese App ausprobieren.\n"
                 "Liebe Grüße",
            font_size=64,
            color=(1, 1, 1, 1),
            halign="center"
        )
        label.bind(size=label.setter("text_size"))

        btn = BlackButton(
            text="Weiter",
            font_size=48,
            size_hint=(None, None),
            size=(500, 150)
        )
        btn.pos_hint = {"center_x": 0.5}
        btn.bind(on_press=self.next)

        self.add_widget(label)
        self.add_widget(btn)

    def next(self, instance):
        self.app.set_first_start_done()
        self.app.show_question()


# ───────────── Arduino Frage ─────────────
class QuestionScreen(BoxLayout):
    def __init__(self, app, **kwargs):
        super().__init__(orientation="vertical", padding=60, spacing=40, **kwargs)
        self.app = app
        Window.clearcolor = (0, 0, 0, 1)

        # Top bar
        top = BoxLayout(size_hint=(1, 0.15))
        top.add_widget(Label())
        help_btn = BlackButton(text="?", font_size=72, size_hint=(None, None), size=(120, 120))
        help_btn.bind(on_press=self.show_help)
        top.add_widget(help_btn)
        self.add_widget(top)

        # Frage
        label = Label(
            text="Möchten Sie die App\nmit dem Arduino durchführen?",
            font_size=72,
            color=(1, 1, 1, 1),
            halign="center",
            size_hint=(1, 0.4)
        )
        label.bind(size=label.setter("text_size"))
        self.add_widget(label)

        # Buttons
        row = BoxLayout(spacing=80, size_hint=(1, 0.25))
        btn_yes = BlackButton(text="Ja", font_size=56)
        btn_no = BlackButton(text="Nein", font_size=56)

        btn_yes.bind(on_press=lambda x: self.app.start_camera(True))
        btn_no.bind(on_press=lambda x: self.app.start_camera(False))

        row.add_widget(btn_yes)
        row.add_widget(btn_no)
        self.add_widget(row)

    def show_help(self, instance):
        popup = Popup(
            title="",
            content=Label(
                text="Bei Fragen können Sie uns\n"
                     "einfach eine E-Mail schicken.",
                font_size=44,
                halign="center"
            ),
            size_hint=(0.6, 0.3)
        )
        popup.open()


# ───────────── Nordrichtung Screen ─────────────
class NorthScreen(BoxLayout):
    def __init__(self, app, **kwargs):
        super().__init__(orientation="vertical", padding=60, spacing=40, **kwargs)
        self.app = app
        Window.clearcolor = (0, 0, 0, 1)

        # Top bar
        top = BoxLayout(size_hint=(1, 0.15))
        top.add_widget(Label())
        help_btn = BlackButton(text="?", font_size=72, size_hint=(None, None), size=(120, 120))
        help_btn.bind(on_press=self.show_help)
        top.add_widget(help_btn)
        self.add_widget(top)

        label = Label(
            text="Nordrichtung",
            font_size=80,
            color=(1, 1, 1, 1),
            size_hint=(1, 0.5)
        )
        self.add_widget(label)

        btn = BlackButton(
            text="Erneutes Foto machen",
            font_size=48,
            size_hint=(None, None),
            size=(600, 150)
        )
        btn.pos_hint = {"center_x": 0.5}
        btn.bind(on_press=lambda x: self.app.show_question())
        self.add_widget(btn)

    def show_help(self, instance):
        popup = Popup(
            title="",
            content=Label(
                text="Bei Fragen können Sie uns\n"
                     "einfach eine E-Mail schicken.",
                font_size=44,
                halign="center"
            ),
            size_hint=(0.6, 0.3)
        )
        popup.open()


# ───────────── App ─────────────
class MainApp(App):
    def build(self):
        self.root_box = BoxLayout()
        self.check_first_start()
        return self.root_box

    def check_first_start(self):
        prefs = autoclass("org.kivy.android.PythonActivity").mActivity \
            .getSharedPreferences("ArchälogiePrefs", 0)

        if prefs.getBoolean("first_start", True):
            self.root_box.add_widget(WelcomeScreen(self))
        else:
            self.show_question()

    def set_first_start_done(self):
        prefs = autoclass("org.kivy.android.PythonActivity").mActivity \
            .getSharedPreferences("ArchälogiePrefs", 0)
        prefs.edit().putBoolean("first_start", False).apply()

    def show_question(self):
        self.root_box.clear_widgets()
        self.root_box.add_widget(QuestionScreen(self))

    def start_camera(self, show_north):
        self.show_north = show_north
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

        self.root_box.clear_widgets()
        if self.show_north:
            self.root_box.add_widget(NorthScreen(self))
        else:
            self.show_question()


if __name__ == "__main__":
    MainApp().run()
