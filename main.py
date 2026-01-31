from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window
from jnius import autoclass


class StartScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", spacing=30, padding=40, **kwargs)

        # Schwarzer Hintergrund
        Window.clearcolor = (0, 0, 0, 1)

        # Text
        question = Label(
            text="Möchten Sie die App mit dem Arduino durchführen?",
            color=(1, 1, 1, 1),
            font_size=24,
            halign="center",
            valign="middle"
        )
        question.bind(size=question.setter("text_size"))

        # Buttons
        btn_yes = Button(text="Ja", font_size=22, size_hint=(1, 0.25))
        btn_no = Button(text="Nein", font_size=22, size_hint=(1, 0.25))

        btn_yes.bind(on_press=self.open_camera)
        btn_no.bind(on_press=self.open_camera)

        self.add_widget(question)
        self.add_widget(btn_yes)
        self.add_widget(btn_no)

    def open_camera(self, instance):
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
