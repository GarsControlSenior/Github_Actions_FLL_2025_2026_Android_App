from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.utils import platform

# Android-spezifische Importe nur laden, wenn wir auf Android sind
if platform == 'android':
    from jnius import autoclass
    from android.permissions import check_permission, request_permissions, Permission

class MainApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical', padding=20)
        
        self.btn = Button(
            text="Kamera starten", 
            size_hint=(1, 0.2),
            background_color=(0.2, 0.6, 1, 1)
        )
        self.btn.bind(on_press=self.manage_camera_start)
        
        self.layout.add_widget(self.btn)
        return self.layout

    def manage_camera_start(self, instance):
        """Prüft Berechtigungen und entscheidet: Starten oder Fragen."""
        if platform == 'android':
            perms = [Permission.CAMERA]
            if all([check_permission(p) for p in perms]):
                self.open_camera()
            else:
                request_permissions(perms, callback=self.on_permissions_result)
        else:
            print("Kamera-Feature ist nur auf Android verfügbar.")

    def on_permissions_result(self, permissions, grants):
        """Reaktion auf die Antwort des Nutzers."""
        if all(grants):
            self.open_camera()
        else:
            self.show_permission_explanation()

    def show_permission_explanation(self):
        """Popup, falls der Nutzer 'Nicht zulassen' geklickt hat."""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        msg = Label(text="Kamera-Zugriff wurde verweigert.\n\n"
                         "Bitte erlaube den Zugriff, damit die\n"
                         "App Fotos aufnehmen kann.",
                    halign="center")
        
        btn_layout = BoxLayout(size_hint_y=0.4, spacing=10)
        retry_btn = Button(text="Nochmal")
        settings_btn = Button(text="Einstellungen")
        
        btn_layout.add_widget(retry_btn)
        btn_layout.add_widget(settings_btn)
        content.add_widget(msg)
        content.add_widget(btn_layout)

        popup = Popup(title="Berechtigung nötig", content=content, size_hint=(0.8, 0.5))
        
        retry_btn.bind(on_release=lambda x: (popup.dismiss(), self.manage_camera_start(None)))
        settings_btn.bind(on_release=lambda x: (popup.dismiss(), self.open_android_settings()))
        popup.open()

    def open_android_settings(self):
        """Öffnet die Android-App-Info, falls 'Nicht mehr fragen' gewählt wurde."""
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Intent = autoclass('android.content.Intent')
        Settings = autoclass('android.provider.Settings')
        Uri = autoclass('android.net.Uri')
        
        activity = PythonActivity.mActivity
        intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS)
        uri = Uri.fromParts("package", activity.getPackageName(), None)
        intent.setData(uri)
        activity.startActivity(intent)

    def open_camera(self):
        """Der eigentliche Kamera-Aufruf."""
        try:
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            MediaStore = autoclass('android.provider.MediaStore')

            activity = PythonActivity.mActivity
            intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
            
            # Startet die Kamera-App
            activity.startActivity(intent)
        except Exception as e:
            print(f"Fehler beim Kamera-Start: {e}")

if __name__ == "__main__":
    MainApp().run()
