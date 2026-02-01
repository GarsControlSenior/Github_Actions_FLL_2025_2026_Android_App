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

# ───────────── Design ─────────────
DARK_BLUE_BG = (0.05, 0.2, 0.45, 1)


class DarkBlueButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = DARK_BLUE_BG
        self.color = (1, 1, 1, 1)
        self.border = (0, 0, 0, 0)


# ───────────── Willkommen Screen ─────────────
class WelcomeScreen(BoxLayout):
    def __init__(self, app):
        super().__init__(orientation="vertical", spacing=60)
        self.app = app
        Window.clearcolor = DARK_BLUE_BG

        label = Label(
            text="Herzlich Willkommen!\n\nVielen Dank, dass Sie diese App ausprobieren.\nLiebe Grüße",
            font_size=64,
            halign="center",
            color=(1, 1, 1, 1),
            size_hint=(1, 0.6),
            pos_hint={"center_y": 0.6}
        )
        label.bind(size=label.setter("text_size"))

        btn = DarkBlueButton(
            text="Weiter",
            font_size=48,
            size_hint=(None, None),
            size=(500, 150)
        )
        btn.pos_hint = {"center_x": 0.5}
        btn.bind(on_press=lambda x: self.app.show_question())

        self.add_widget(label)
        self.add_widget(btn)


# ───────────── Nordrichtung Screen ─────────────
class NorthScreen(BoxLayout):
    def __init__(self, app):
        super().__init__(orientation="vertical", spacing=60)
        self.app = app
        Window.clearcolor = DARK_BLUE_BG

        label = Label(
            text="Nordrichtung",
            font_size=80,
            color=(1, 1, 1, 1),
            size_hint=(1, 0.6),
            pos_hint={"center_y": 0.6},
            halign="center"
        )
        label.bind(size=label.setter("text_size"))

        btn = DarkBlueButton(
            text="Weiter",
            font_size=48,
            size_hint=(None, None),
            size=(400, 140)
        )
        btn.pos_hint = {"center_x": 0.5}
        btn.bind(on_press=lambda x: self.app.show_question())

        self.add_widget(label)
        self.add_widget(btn)


# ───────────── Arduino-Frage Screen ─────────────
class QuestionScreen(BoxLayout):
    def __init__(self, app):
        super().__init__(orientation="vertical", spacing=60)
        self.app = app
        Window.clearcolor = DARK_BLUE_BG

        # Hilfe oben rechts
        top = BoxLayout(size_hint=(1, None), height=120)
        top.add_widget(Label())
        help_btn = DarkBlueButton(
            text="?",
            font_size=72,
            size_hint=(None, None),
            size=(120, 120)
        )
        help_btn.bind(on_press=self.show_help)
        top.add_widget(help_btn)
        self.add_widget(top)

        label = Label(
            text="Möchten Sie die App\nmit dem Arduino durchführen?",
            font_size=72,
            halign="center",
            color=(1, 1, 1, 1),
            size_hint=(1, 0.6),
            pos_hint={"center_y": 0.6}
        )
        label.bind(size=label.setter("text_size"))
        self.add_widget(label)

        row = BoxLayout(spacing=80, size_hint=(1, None), height=160)
        btn_yes = DarkBlueButton(text="Ja", font_size=56)
        btn_no = DarkBlueButton(text="Nein", font_size=56)

        btn_yes.bind(on_press=lambda x: self.app.start_camera(True))
        btn_no.bind(on_press=lambda x: self.app.start_camera(False))

        row.add_widget(btn_yes)
        row.add_widget(btn_no)
        self.add_widget(row)

    def show_help(self, instance):
        Popup(
            title="",
            content=Label(
                text="Bei Fragen können Sie uns\n"
                     "einfach eine E-Mail schicken.",
                font_size=44,
                halign="center"
            ),
            size_hint=(0.6, 0.3)
        ).open()


# ───────────── Main App ─────────────
class MainApp(App):
    def build(self):
        self.root_box = BoxLayout()
        self.show_north_after_camera = False
        self.check_first_start()
        return self.root_box

    def check_first_start(self):
        prefs = autoclass("org.kivy.android.PythonActivity").mActivity \
            .getSharedPreferences("ArchaelogiePrefs", 0)

        if prefs.getBoolean("first_start", True):
            prefs.edit().putBoolean("first_start", False).apply()
            self.root_box.add_widget(WelcomeScreen(self))
        else:
            self.show_question()

    def show_question(self):
        self.root_box.clear_widgets()
        self.root_box.add_widget(QuestionScreen(self))

    def start_camera(self, was_yes):
        self.show_north_after_camera = was_yes

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

        intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        PythonActivity.mActivity.startActivity(intent)

        # Nach Rückkehr von Kamera
        if self.show_north_after_camera:
            self.root_box.clear_widgets()
            self.root_box.add_widget(NorthScreen(self))
        else:
            self.show_question()


if __name__ == "__main__":
    MainApp().run()
