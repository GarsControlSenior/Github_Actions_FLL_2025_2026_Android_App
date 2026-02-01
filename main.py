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

# ───────────── Design ─────────────
DARK_BLUE_BG = (0.02, 0.1, 0.3, 1)


class StartScreen(BoxLayout):
    def __init__(self, app):
        super().__init__(orientation="vertical", padding=40, spacing=30)
        self.app = app
        Window.clearcolor = DARK_BLUE_BG

        # ── Obere Leiste mit Fragezeichen ──
        top_bar = BoxLayout(orientation="horizontal", size_hint=(1, 0.15))
        top_bar.add_widget(Label())

        help_btn = Button(
            text="?",
            font_size=56,              # größer
            size_hint=(None, None),
            size=(120, 120),
            background_color=DARK_BLUE_BG,
            color=(1, 1, 1, 1)
        )
        help_btn.bind(on_press=self.show_help)
        top_bar.add_widget(help_btn)
        self.add_widget(top_bar)

        # ── Arduino-Frage (DOPPELT SO GROß) ──
        question = Label(
            text="Möchten Sie die App\nmit dem Arduino durchführen?",
            color=(1, 1, 1, 1),
            font_size=84,              # ⬅️ doppelt so groß
            halign="center",
            valign="middle",
            size_hint=(1, 0.45)
        )
        question.bind(size=question.setter("text_size"))
        self.add_widget(question)

        # ── Buttons ──
        button_row = BoxLayout(orientation="horizontal", spacing=40, size_hint=(1, 0.25))

        btn_yes = Button(
            text="Ja",
            font_size=48,
            background_color=DARK_BLUE_BG,
            color=(1, 1, 1, 1)
        )
        btn_no = Button(
            text="Nein",
            font_size=48,
            background_color=DARK_BLUE_BG,
            color=(1, 1, 1, 1)
        )

        btn_yes.bind(on_press=self.open_camera)
        btn_no.bind(on_press=self.open_camera)

        button_row.add_widget(btn_yes)
        button_row.add_widget(btn_no)
        self.add_widget(button_row)

    # ── Hilfe Popup ──
    def show_help(self, instance):
        content = Label(
            text="Bei Fragen können Sie uns\n"
                 "einfach eine E-Mail schicken.",
            font_size=36,              # größer
            halign="center",
            valign="middle"
        )
        content.bind(size=content.setter("text_size"))

        Popup(
            title="Hilfe",
            content=content,
            size_hint=(0.7, 0.35)
        ).open()

    # ── Kamera öffnen (KEIN Screenwechsel!) ──
    def open_camera(self, instance):
        if request_permissions:
            request_permissions([Permission.CAMERA], self.after_permission)
        else:
            self.start_camera()

    def after_permission(self, permissions, results):
        if all(results):
            self.start_camera()

    def start_camera(self):
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Intent = autoclass('android.content.Intent')
        MediaStore = autoclass('android.provider.MediaStore')

        activity = PythonActivity.mActivity
        intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        activity.startActivity(intent)


class MainApp(App):
    def build(self):
        self.root = StartScreen(self)
        return self.root

    # ⬅️ WICHTIG: Wird aufgerufen, wenn man von Kamera zurückkommt
    def on_resume(self):
        self.root.clear_widgets()
        self.root = StartScreen(self)
        self.root_window.add_widget(self.root)


if __name__ == "__main__":
    MainApp().run()
