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
DARK_BLUE_BG = (0.05, 0.2, 0.45, 1)


class DarkBlueButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = DARK_BLUE_BG
        self.color = (1, 1, 1, 1)
        self.border = (0, 0, 0, 0)


# ───────────── Willkommen / Arduino Frage Screen ─────────────
class StartScreen(BoxLayout):
    def __init__(self, app, show_welcome=True):
        super().__init__(orientation="vertical", spacing=20, padding=40)
        self.app = app
        self.show_welcome = show_welcome
        Window.clearcolor = DARK_BLUE_BG

        # Obere Leiste mit Fragezeichen
        top_bar = BoxLayout(orientation="horizontal", size_hint=(1, 0.15))
        top_bar.add_widget(Label())  # linker Platzhalter
        help_btn = DarkBlueButton(
            text="?",
            font_size=36,
            size_hint=(None, None),
            size=(80, 80)
        )
        help_btn.bind(on_press=self.show_help)
        top_bar.add_widget(help_btn)
        self.add_widget(top_bar)

        if self.show_welcome:
            # Willkommenstext
            welcome_label = Label(
                text="Herzlich Willkommen!\n\nVielen Dank, dass Sie diese App ausprobieren.\nLiebe Grüße",
                color=(1, 1, 1, 1),
                font_size=42,
                halign="center",
                valign="middle",
                size_hint=(1, 0.45)
            )
            welcome_label.bind(size=welcome_label.setter("text_size"))
            self.add_widget(welcome_label)

            # Weiter-Button zur Arduino-Frage
            btn_continue = DarkBlueButton(text="Weiter", font_size=32, size_hint=(None, None), size=(300, 120))
            btn_continue.pos_hint = {"center_x": 0.5}
            btn_continue.bind(on_press=lambda x: self.app.show_question_screen())
            self.add_widget(btn_continue)
        else:
            # Arduino-Frage direkt
            self.add_arduino_question()

    def add_arduino_question(self):
        question = Label(
            text="Möchten Sie die App\nmit dem Arduino durchführen?",
            color=(1, 1, 1, 1),
            font_size=42,
            halign="center",
            valign="middle",
            size_hint=(1, 0.45)
        )
        question.bind(size=question.setter("text_size"))
        self.add_widget(question)

        # Buttons nebeneinander
        button_row = BoxLayout(orientation="horizontal", spacing=30, size_hint=(1, 0.25))
        btn_yes = DarkBlueButton(text="Ja", font_size=32)
        btn_no = DarkBlueButton(text="Nein", font_size=32)
        btn_yes.bind(on_press=lambda x: self.app.start_camera(True))
        btn_no.bind(on_press=lambda x: self.app.start_camera(False))
        button_row.add_widget(btn_yes)
        button_row.add_widget(btn_no)
        self.add_widget(button_row)

    # Fragezeichen Popup
    def show_help(self, instance):
        content = Label(
            text="Bei Fragen können Sie uns einfach eine E-Mail schicken.",
            font_size=24,
            halign="center",
            valign="middle"
        )
        content.bind(size=content.setter("text_size"))

        popup = Popup(
            title="Hilfe",
            content=content,
            size_hint=(0.6, 0.3)
        )
        popup.open()


# ───────────── Main App ─────────────
class MainApp(App):
    def build(self):
        self.root_box = BoxLayout()
        Window.clearcolor = DARK_BLUE_BG

        # Prüfen, ob Willkommen anzeigen (nur beim ersten Start)
        self.show_welcome = True
        self.show_start_screen()
        return self.root_box

    def show_start_screen(self):
        self.root_box.clear_widgets()
        self.root_box.add_widget(StartScreen(self, show_welcome=self.show_welcome))

    def show_question_screen(self):
        self.show_welcome = False
        self.root_box.clear_widgets()
        self.root_box.add_widget(StartScreen(self, show_welcome=False))

    def start_camera(self, was_yes):
        # Egal JA oder NEIN, nach Kamera → zurück zur Arduino-Frage
        self.last_answer_was_yes = was_yes

        if request_permissions:
            request_permissions([Permission.CAMERA], self.after_permission)
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

        # Nach Rückkehr → immer zurück zur Arduino-Frage
        self.show_question_screen()


if __name__ == "__main__":
    MainApp().run()
