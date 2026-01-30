from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from jnius import autoclass

class MainApp(App):
    def build(self):
        # Leeres Layout (damit App stabil startet)
        self.layout = BoxLayout()

        # Kamera erst starten, wenn App wirklich läuft
        Clock.schedule_once(self.open_camera, 0)

        return self.layout

    def open_camera(self, dt):
        try:
            # === STANDARD ANDROID KAMERA (dein Original-Code) ===
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            MediaStore = autoclass('android.provider.MediaStore')

            activity = PythonActivity.mActivity
            intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)

            # WICHTIG: startActivity (nicht startActivityForResult)
            # → Kamera ist komplett unabhängig & stabil
            activity.startActivity(intent)

        except Exception as e:
            # Falls hier jemals ein Fehler ist → App bleibt offen
            print("Fehler beim Öffnen der Kamera:", e)

        # OPTIONAL: Nachbearbeitung vorbereiten
        Clock.schedule_once(self.safe_after_camera_code, 0)

    def safe_after_camera_code(self, dt):
        """
        HIER kommt später dein Code mit rotem Punkt rein.
        Alles ist absichtlich in try/except,
        damit die App NIEMALS abstürzt.
        """
        try:
            # === DEIN SPÄTERER CODE ===
            # z.B. Pillow, roter Punkt, etc.
            print("Nachbearbeitung bereit (hier später roter Punkt)")

        except Exception as e:
            print("Fehler im Nachbearbeitungs-Code:", e)


if __name__ == "__main__":
    MainApp().run()
